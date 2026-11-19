"""Runtime de parametros Ab Initio para los jobs generados (Spark y Glue).

Este archivo es la UNICA fuente: sus funciones se importan en los tests y su texto
(desde el marcador BEGIN hasta el final) se incrusta tal cual en cada job generado
(ver `emit_params_runtime`). Por eso el bloque incrustado solo usa `os`, `re` y los
globales `PARAMS`/`spark`/`F` del job; no importa nada del proyecto.

Que resuelve:
  * ${NAME} y $NAME (incluso anidados: OUT='$DIR/$NAME') con PARAMS + os.environ,
    con limite de profundidad y deteccion de ciclos.
  * PDL $[...] con un mini-evaluador propio (if/else, is_blank, ==, !=, <, >, and, or,
    not, numeros, strings, referencias a parametros y unas pocas funciones string).
    NUNCA se usa eval/exec sobre el texto.
  * Spark SQL sustituye ${X} por '' por su cuenta (spark.sql.variable.substitute): se
    desactiva y las expresiones se expanden en Python antes de llegar al parser.
  * Filter by Expression con expresion vacia o *_FLAG == 0 -> pass-through (Ab Initio);
    BNX_STRICT_PARAMS=1 lo convierte en error claro.
"""

# >>> BEGIN BNX PARAMS RUNTIME
import os
import re
import shlex
import shutil
import subprocess
import sys
import datetime as _bnx_dtm
_BNX_MAX_DEPTH = 10
_BNX_RAW = {}
_BNX_DONE = {}
_BNX_WARNED = set()


def _bnx_warn(key, msg):
    if key not in _BNX_WARNED:
        _BNX_WARNED.add(key)
        print(msg)


def _bnx_lookup(name):
    """Valor crudo de un parametro: PARAMS (ya incluye env) y luego os.environ."""
    if name in _BNX_RAW:
        return _BNX_RAW[name]
    if name in os.environ:
        return os.environ[name]
    p = globals().get("PARAMS")
    if p is not None and not name.startswith("_") and hasattr(p, name):
        v = getattr(p, name)
        if isinstance(v, str):
            return v
    return None


class _BnxPdlUnsupported(Exception):
    pass


_PDL_TOK = re.compile(
    r"""\s*(?:
      (?P<num>\d+(?:\.\d+)?)
     |(?P<str>'(?:[^'\\]|\\.)*'|"(?:[^"\\]|\\.)*")
     |(?P<ref>\$\{\w+\}|\$[A-Za-z_]\w*)
     |(?P<id>[A-Za-z_]\w*)
     |(?P<op>==|!=|<=|>=|&&|\|\||<|>|\+|\(|\)|,|!)
    )""", re.X)


def _pdl_tokens(src):
    pos, out = 0, []
    src = src.strip()
    while pos < len(src):
        m = _PDL_TOK.match(src, pos)
        if not m or m.end() == pos:
            raise _BnxPdlUnsupported("token no soportado en %r" % src[pos:pos + 12])
        pos = m.end()
        kind = m.lastgroup
        out.append((kind, m.group(kind)))
    return out


def _pdl_num(v):
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


def _pdl_str(v):
    if isinstance(v, bool):
        return "1" if v else "0"
    if isinstance(v, float) and v == int(v):
        return str(int(v))
    if isinstance(v, _bnx_dtm.datetime):
        return v.strftime("%Y%m%d%H%M%S")
    return "" if v is None else str(v)


def _pdl_truth(v):
    if isinstance(v, bool):
        return v
    n = _pdl_num(v)
    if n is not None:
        return n != 0
    return str(v) != ""


_PDL_FMT = re.compile(r"YYYY|YY|MM|DD|HH24|HH|MI|SS")
_PDL_FMT_MAP = {"YYYY": "%Y", "YY": "%y", "MM": "%m", "DD": "%d", "HH24": "%H", "HH": "%H", "MI": "%M", "SS": "%S"}


def _pdl_fmt(dt, fmt):
    if not isinstance(dt, _bnx_dtm.datetime):
        raise _BnxPdlUnsupported("fecha no valida")
    return dt.strftime(_PDL_FMT.sub(lambda m: _PDL_FMT_MAP[m.group(0)], fmt.replace("%", "%%")))


def _pdl_substr(s, start, length):
    # sin los builtins que pisa `from pyspark.sql.functions import *` (maximo/minimo/etc.)
    i = int(float(start)) - 1
    i = i if i > 0 else 0
    return _pdl_str(s)[i:i + int(float(length))]


_PDL_FUNCS = {
    "now1": lambda a: _bnx_dtm.datetime.now(),
    "now": lambda a: _bnx_dtm.datetime.now(),
    "datetime_add": lambda a: a[0] + _bnx_dtm.timedelta(days=int(float(a[1]))),
    "is_blank": lambda a: _pdl_str(a[0]).strip() == "",
    "is_defined": lambda a: _pdl_str(a[0]) != "",
    "string_length": lambda a: float(len(_pdl_str(a[0]))),
    "string_upcase": lambda a: _pdl_str(a[0]).upper(),
    "string_downcase": lambda a: _pdl_str(a[0]).lower(),
    "string_lrtrim": lambda a: _pdl_str(a[0]).strip(),
    "string_replace": lambda a: _pdl_str(a[0]).replace(_pdl_str(a[1]), _pdl_str(a[2])),
    "string_substring": lambda a: _pdl_substr(a[0], a[1], a[2]),
}


class _PdlParser:
    """Descenso recursivo sobre una lista de tokens; devuelve valores Python."""

    def __init__(self, toks, getter):
        self.t, self.i, self.get = toks, 0, getter

    def peek(self):
        return self.t[self.i] if self.i < len(self.t) else (None, None)

    def take(self):
        tok = self.peek()
        self.i += 1
        return tok

    def accept(self, kind, val):
        k, v = self.peek()
        if k == kind and v == val:
            self.i += 1
            return True
        return False

    def expect(self, kind, val):
        if not self.accept(kind, val):
            raise _BnxPdlUnsupported("se esperaba %r" % val)

    def parse(self):
        v = self.expr()
        if self.i != len(self.t):
            raise _BnxPdlUnsupported("sobran tokens")
        return v

    def expr(self):
        return self.p_or()

    def p_or(self):
        v = self.p_and()
        while self.accept("id", "or") or self.accept("op", "||"):
            r = self.p_and()
            v = _pdl_truth(v) or _pdl_truth(r)
        return v

    def p_and(self):
        v = self.p_not()
        while self.accept("id", "and") or self.accept("op", "&&"):
            r = self.p_not()
            v = _pdl_truth(v) and _pdl_truth(r)
        return v

    def p_not(self):
        if self.accept("id", "not") or self.accept("op", "!"):
            return not _pdl_truth(self.p_not())
        return self.p_cmp()

    def p_cmp(self):
        a = self.p_add()
        k, v = self.peek()
        if k == "op" and v in ("==", "!=", "<", ">", "<=", ">="):
            self.i += 1
            b = self.p_add()
            na, nb = _pdl_num(a), _pdl_num(b)
            x, y = (na, nb) if (na is not None and nb is not None) else (_pdl_str(a), _pdl_str(b))
            return {"==": x == y, "!=": x != y, "<": x < y, ">": x > y,
                    "<=": x <= y, ">=": x >= y}[v]
        return a

    def p_add(self):
        v = self.atom()
        while self.accept("op", "+"):
            r = self.atom()
            if isinstance(v, float) and isinstance(r, float):
                v = v + r
            else:
                v = _pdl_str(v) + _pdl_str(r)
        return v

    def atom(self):
        k, v = self.take()
        if k == "num":
            return float(v)
        if k == "str":
            return re.sub(r"\\(.)", r"\1", v[1:-1])
        if k == "ref":
            return self.get(v.strip("${}"))
        if k == "op" and v == "(":
            # cast de fecha de PDL: (datetime("FMT"))expr  /  (date("FMT"))expr
            t = self.t[self.i:self.i + 5]
            if (len(t) == 5 and t[0] == ("id", t[0][1]) and t[0][1] in ("datetime", "date")
                    and t[1] == ("op", "(") and t[2][0] == "str" and t[3] == ("op", ")") and t[4] == ("op", ")")):
                fmt = t[2][1][1:-1]
                self.i += 5
                return _pdl_fmt(self.atom(), fmt)
            r = self.expr()
            self.expect("op", ")")
            return r
        if k == "id" and v == "if":
            self.expect("op", "(")
            cond = self.expr()
            self.expect("op", ")")
            a = self.expr()
            if self.accept("id", "else"):
                b = self.expr()
            else:
                b = ""
            return a if _pdl_truth(cond) else b
        if k == "id":
            if self.accept("op", "("):
                args = []
                if not self.accept("op", ")"):
                    args.append(self.expr())
                    while self.accept("op", ","):
                        args.append(self.expr())
                    self.expect("op", ")")
                fn = _PDL_FUNCS.get(v)
                if fn is None:
                    raise _BnxPdlUnsupported("funcion %s" % v)
                try:
                    return fn(args)
                except (IndexError, ValueError):
                    raise _BnxPdlUnsupported("argumentos de %s" % v)
            return self.get(v)
        raise _BnxPdlUnsupported("expresion no soportada")


def _bnx_pdl_eval(src, getter):
    """Evalua el cuerpo de un $[...]. Lanza _BnxPdlUnsupported si no puede."""
    return _pdl_str(_PdlParser(_pdl_tokens(src), getter).parse())


def _bnx_pdl_end(text, start):
    """Indice del ']' que cierra el '$[' que empieza en `start` (o -1)."""
    depth, q, i = 0, None, start
    while i < len(text):
        c = text[i]
        if q:
            if c == "\\":
                i += 1
            elif c == q:
                q = None
        elif c in "'\"":
            q = c
        elif c == "[":
            depth += 1
        elif c == "]":
            depth -= 1
            if depth == 0:
                return i
        i += 1
    return -1


# ${X}, $\{X\} (llaves escapadas del GDE) y $X
_BNX_REF = re.compile(r"\$\\?\{([A-Za-z_]\w*)\\?\}|\$([A-Za-z_]\w*)")


def _bnx_value(name, depth, stack, empties):
    """Valor expandido de un parametro; None si no existe."""
    if name in _BNX_DONE:
        return _BNX_DONE[name]
    raw = _bnx_lookup(name)
    if raw is None:
        return None
    if name in stack:
        _bnx_warn(("cycle", name), "[!] Parametro con referencia circular: %s (se deja sin expandir)" % name)
        return raw
    val = _bnx_expand(raw, depth + 1, stack + (name,), None, name)
    if not stack:
        _BNX_DONE[name] = val
    return val


def _bnx_expand(text, _depth=0, _stack=(), empties=None, _owner=None):
    """Expande ${X}, $X y $[PDL] en `text`. `empties` (lista) recibe los nombres
    de parametros que quedaron vacios."""
    if not isinstance(text, str) or "$" not in text:
        return text
    if _depth > _BNX_MAX_DEPTH:
        _bnx_warn(("depth", text[:40]), "[!] Parametros anidados demasiado profundos: %s" % text[:60])
        return text
    out, i, n = [], 0, len(text)
    while i < n:
        j = text.find("$", i)
        if j < 0:
            out.append(text[i:])
            break
        out.append(text[i:j])
        if text.startswith("$[", j):
            end = _bnx_pdl_end(text, j + 1)
            if end < 0:
                out.append(text[j:])
                break
            body = text[j + 2:end]

            def _get(nm, _d=_depth, _s=_stack):
                v = _bnx_value(nm, _d, _s, None)
                return "" if v is None else v
            try:
                out.append(_bnx_pdl_eval(body, _get))
            except (_BnxPdlUnsupported, RecursionError):
                _bnx_warn(("pdl", _owner or body), "[!] PDL no resuelto: %s" % (_owner or body[:60]))
                out.append("")
            i = end + 1
            continue
        m = _BNX_REF.match(text, j)
        if not m:
            out.append("$")
            i = j + 1
            continue
        braced = m.group(1) is not None
        name = m.group(1) or m.group(2)
        v = _bnx_value(name, _depth, _stack, empties)
        if v is None:
            if name.startswith("AI_"):
                _bnx_warn(("ai", name), "[!] Variable de Ab Initio $%s sin valor; se deja tal cual "
                          "(definela como variable de entorno si es una ruta)" % name)
                out.append(m.group(0))
            elif braced:
                _bnx_warn(("undef", name), "[!] Parametro %s sin valor; se expande como vacio" % name)
                if empties is not None:
                    empties.append(name)
                out.append("")
            else:
                out.append(m.group(0))  # $x suelto (p.ej. regex): no es un parametro
        else:
            if v.strip() == "" and empties is not None:
                empties.append(name)
            out.append(v)
        i = m.end()
    return "".join(out)


def _bnx_raw_name(path, node):
    """Nombre estable (bajo <base>/raw/) del dataset de un Input File.
    `path` es la ruta del componente con referencias a parametros ($\\{X\\}, $X). Se expande;
    si queda vacia, 'NOT SET' o con variables sin valor (p.ej. $ECS_* del banco) se usa el
    nombre del nodo. Cada segmento se sanea (espacios y caracteres raros -> '_').
    El orquestador usa el MISMO algoritmo (src.codegen.params_runtime.resolve_raw_name)."""
    val = _bnx_expand(path) if "$" in (path or "") else (path or "")
    val = val.replace("\\", "/").strip()
    if val.upper() in ("", "NOT SET", "NOTSET") or "$" in val:
        _bnx_warn(("rawname", node, path),
                  "[!] Ruta de entrada de %s no resuelta (%s); se usa el nombre del nodo en raw/" % (node, val or path))
        val = node
    segs = [re.sub(r"[^\w.\-]+", "_", s).strip("_") for s in val.split("/") if s not in ("", ".", "..")]
    segs = [s for s in segs if s]
    return "/".join(segs) or re.sub(r"[^\w.\-]+", "_", node)


def _bnx_refs(text):
    """Nombres de parametros referenciados (${X} / $X) en un texto."""
    return [a or b for a, b in _BNX_REF.findall(text or "")]


def _bnx_resolve_params(P=None):
    """Resuelve en sitio todos los atributos str de PARAMS que contengan $ (en orden
    de dependencias, con deteccion de ciclos)."""
    P = P if P is not None else globals().get("PARAMS")
    _BNX_RAW.clear()
    _BNX_DONE.clear()
    for k, v in vars(P).items():
        if not k.startswith("_") and isinstance(v, str):
            _BNX_RAW[k] = v
    for k, v in list(_BNX_RAW.items()):
        if "$" in v:
            setattr(P, k, _bnx_value(k, 0, (), None))
    return P


def _bnx_strict():
    return os.environ.get("BNX_STRICT_PARAMS", "").strip().lower() in ("1", "true", "yes", "si")


def _bnx_param_error(empties, ctx, exc):
    names = ", ".join(sorted(set(empties)))
    return RuntimeError("Parametro %s vacio en %s; definelo en el pset o como variable de entorno "
                        "(la expresion resultante no es SQL valido: %s)" % (names, ctx, str(exc).splitlines()[0][:120]))


def _bnx_install_spark_shims():
    """Desactiva la sustitucion ${X} de Spark SQL y expande parametros Ab Initio en
    where/filter/selectExpr/expr/join antes de que lleguen al parser de Spark."""
    try:
        spark.conf.set("spark.sql.variable.substitute", "false")
    except Exception:
        pass
    from pyspark.sql import DataFrame

    def _x(v):
        if isinstance(v, str) and "$" in v:
            return _bnx_expand(v)
        if isinstance(v, (list, tuple)):
            return type(v)(_x(i) for i in v)
        return v

    def _x_key(v, ctx):
        """Como _x, pero una clave que queda vacia por un parametro vacio es un error claro."""
        if isinstance(v, str) and "$" in v:
            empties = []
            out = _bnx_expand(v, 0, (), empties)
            if empties and out.strip() == "":
                raise RuntimeError("Parametro %s vacio en %s(); definelo en el pset o como variable "
                                   "de entorno" % (", ".join(sorted(set(empties))), ctx))
            return out
        if isinstance(v, (list, tuple)):
            return type(v)(_x_key(i, ctx) for i in v)
        return v

    def _wrap_df(cls, name, sql):
        orig = getattr(cls, name, None)
        if orig is None or getattr(orig, "_bnx_wrapped", False):
            return

        def _m(self, *args, **kw):
            empties = []
            if sql:  # where/filter/selectExpr: texto SQL; recordar parametros vacios
                args = [_bnx_expand(a, 0, (), empties) if isinstance(a, str) and "$" in a else a
                        for a in args]
            else:    # nombres de columna / claves (groupBy("$KEY"), orderBy, drop...)
                args = [_x_key(a, name) for a in args]
                if isinstance(kw.get("on"), (str, list, tuple)):
                    kw["on"] = _x(kw["on"])
            try:
                return orig(self, *args, **kw)
            except Exception as e:
                if empties and "PARSE" in (type(e).__name__ + str(e)).upper():
                    raise _bnx_param_error(empties, "%s()" % name, e) from e
                raise
        _m.__name__ = name
        _m._bnx_wrapped = True
        setattr(cls, name, _m)

    # En Spark 4 el DataFrame real es una subclase (classic/connect) que redefine los
    # metodos: se parchean tambien en el tipo concreto de la sesion.
    for _cls in {DataFrame, type(spark.range(0))}:
        for _n in ("where", "filter", "selectExpr"):
            _wrap_df(_cls, _n, True)
        for _n in ("groupBy", "groupby", "orderBy", "sort", "drop", "select", "dropDuplicates",
                   "join", "withColumnRenamed"):
            _wrap_df(_cls, _n, False)

    def _wrap_io(cls, name):
        orig = getattr(cls, name)
        if getattr(orig, "_bnx_wrapped", False):
            return

        def _m(self, *args, **kw):
            def _x(v):
                if isinstance(v, str) and "$" in v:
                    return _bnx_expand(v)
                if isinstance(v, (list, tuple)):
                    return type(v)(_x(i) for i in v)
                return v
            args = [_x(a) for a in args[:1]] + list(args[1:])
            if isinstance(kw.get("path"), (str, list, tuple)):
                kw["path"] = _x(kw["path"])
            return orig(self, *args, **kw)
        _m.__name__ = name
        _m._bnx_wrapped = True
        setattr(cls, name, _m)

    from pyspark.sql.readwriter import DataFrameReader, DataFrameWriter
    for _c in {DataFrameReader, type(spark.read)}:
        for _n in ("parquet", "csv", "json", "orc", "text", "load"):
            _wrap_io(_c, _n)
    for _c in {DataFrameWriter, type(spark.range(0).write)}:
        for _n in ("parquet", "csv", "json", "orc", "text", "save"):
            _wrap_io(_c, _n)
    _orig_expr = F.expr

    def _expr(s):
        empties = []
        if isinstance(s, str) and "$" in s:
            s = _bnx_expand(s, 0, (), empties)
        try:
            return _orig_expr(s)
        except Exception as e:
            if empties and "PARSE" in (type(e).__name__ + str(e)).upper():
                raise _bnx_param_error(empties, "expr()", e) from e
            raise
    F.expr = _expr
    globals()["expr"] = _expr


def _bnx_filter_split(df, cond, name):
    """Filter by Expression con semantica Ab Initio: devuelve (salida, reject).
    Parametro vacio o *_FLAG == 0 -> componente deshabilitado: pass-through."""
    empties = []
    txt = _bnx_expand(cond, 0, (), empties)
    refs = _bnx_refs(cond)
    flag_off = []
    for r in refs:
        fv = _bnx_lookup(r + "_FLAG")
        if fv is not None:
            fv = _bnx_value(r + "_FLAG", 0, (), None)
            if fv is not None and fv.strip() in ("", "0", "false", "False"):
                flag_off.append(r + "_FLAG=" + fv.strip())
    if empties or flag_off:
        why = ", ".join(sorted(set(empties))) + " vacio" if empties else ", ".join(flag_off)
        pname = (sorted(set(empties)) or [flag_off[0].split("=")[0]])[0]
        if _bnx_strict():
            raise RuntimeError("Parametro %s vacio en %s; definelo en el pset o como variable de entorno" % (pname, name))
        print("[~] %s deshabilitado: %s (pass-through como Ab Initio)" % (name, why))
        return df, df.limit(0)
    try:
        return df.where(txt), df.where("NOT (%s)" % txt)
    except Exception as e:
        # "(<expr>) <> 0": en Ab Initio <expr> da 0/1; si el usuario da una condicion
        # booleana ("amount > 0") Spark (ANSI) rechaza BOOLEAN <> INT: usarla directo.
        m = re.fullmatch(r"\s*\((.*)\)\s*<>\s*0\s*", txt, re.S)
        if m and ("DATATYPE_MISMATCH" in str(e) or "FILTER_NOT_BOOLEAN" in str(e)):
            inner = m.group(1)
            return df.where(inner), df.where("NOT (%s)" % inner)
        raise
# ---------------------------------------------------------------------------
# Run_Program de Ab Initio: seguro (sin shell) y OPCIONAL.
#   * El comando llega como LISTA de tokens de la plantilla (shlex ANTES de sustituir
#     parametros); cada token se expande por separado: el valor de un parametro nunca
#     puede partirse en varios argumentos ni introducir ; | && > etc. (no hay shell).
#   * mv/cp/rm/mkdir/touch/cat/echo/gzip/gunzip se hacen en Python (portables).
#   * ksh/sh/bash/zsh script -> subprocess con el interprete si existe (en Windows, bash
#     de Git/WSL; si no hay, se omite con aviso).
#   * Por defecto NO se ejecuta nada: BNX_RUN_PROGRAMS=1 (o --run-programs) lo activa.
#   * Con variables sin resolver ($VAR) o vacias NO se ejecuta y se reporta.
#   * Codigo de retorno != 0 -> aviso y sigue, salvo BNX_RUN_PROGRAMS_ESTRICTO=1.
# ---------------------------------------------------------------------------
_BNX_RP_OPS = (";", "&&", "||")
_BNX_RP_UNRES = re.compile(r"\$\{?[A-Za-z_]")
_BNX_RP_SHELLS = ("ksh", "sh", "bash", "zsh")
def _bnx_rp_tokenize(cmd):
    """Tokens de un comando (comillas respetadas; ; && || | > >> < & salen como tokens
    aparte). Lanza ValueError si las comillas no cierran."""
    lex = shlex.shlex(cmd, posix=True, punctuation_chars=True)
    lex.whitespace_split = True
    return list(lex)
def _bnx_rp_flag(name):
    return os.environ.get(name, "").strip().lower() in ("1", "true", "yes", "si")
def _bnx_rp_on():
    return _bnx_rp_flag("BNX_RUN_PROGRAMS") or "--run-programs" in sys.argv[1:]
def _bnx_rp_find_shell(name, nt=None, which=None, exists=None):
    """Ruta del interprete para `name` (ksh/sh/bash/zsh) o None. En POSIX, si falta ksh/zsh
    se usa bash y luego sh (los scripts ksh sencillos corren igual). En Windows solo bash
    (Git for Windows o WSL)."""
    nt = (os.name == "nt") if nt is None else nt
    which = which or shutil.which
    exists = exists or os.path.isfile
    if nt:
        p = which("bash")
        if p:
            return p
        for base in (os.environ.get("ProgramFiles"), os.environ.get("ProgramFiles(x86)"),
                     os.environ.get("LOCALAPPDATA")):
            if base:
                for rel in ("Git\\bin\\bash.exe", "Programs\\Git\\bin\\bash.exe"):
                    c = os.path.join(base, rel)
                    if exists(c):
                        return c
        return None
    for cand in (name, "bash", "sh"):
        p = which(cand)
        if p:
            return p
    return None
def _bnx_rp_split_ops(argv):
    """[(operador_previo, tokens)] cortando por ; && || (solo tokens de la PLANTILLA)."""
    out, cur, op = [], [], ";"
    for t in argv:
        if t in _BNX_RP_OPS:
            if cur:
                out.append((op, cur))
            cur, op = [], t
        else:
            cur.append(t)
    if cur:
        out.append((op, cur))
    return out
def _bnx_rp_nul(path):
    return os.devnull if path == "/dev/null" else path
def _bnx_rp_exec(cmd, plantilla, nombre, extra_env=None):
    """Ejecuta UN comando simple (tokens ya expandidos). Devuelve el codigo de retorno."""
    args, redir_out, redir_err, redir_in, err_to_out = [], None, None, None, False
    i = 0
    while i < len(cmd):
        t = cmd[i]
        if t in (">", ">>") and i + 1 < len(cmd):
            redir_out = (_bnx_rp_nul(cmd[i + 1]), "a" if t == ">>" else "w")
            i += 2
        elif t == "2" and i + 2 < len(cmd) and cmd[i + 1] in (">", ">>"):
            redir_err = (_bnx_rp_nul(cmd[i + 2]), "a" if cmd[i + 1] == ">>" else "w")
            i += 3
        elif t == "2" and i + 2 < len(cmd) and cmd[i + 1] == ">&" and cmd[i + 2] == "1":
            err_to_out = True
            i += 3
        elif t == "<" and i + 1 < len(cmd):
            redir_in = _bnx_rp_nul(cmd[i + 1])
            i += 2
        elif t in ("|", "&", ">", ">>", "<", ">&", "|&", "&>"):
            print("[!] Run_Program %s: operador de shell '%s' no soportado (no se usa shell); "
                  "no se ejecuta" % (nombre, t))
            return 1
        else:
            args.append(t)
            i += 1
    if not args:
        return 0
    name = os.path.basename(args[0]).lower()
    if name.endswith(".exe"):
        name = name[:-4]
    rest = args[1:]
    opts = [a for a in rest if a.startswith("-") and len(a) > 1]
    pos = [a for a in rest if not (a.startswith("-") and len(a) > 1)]
    out = open(redir_out[0], redir_out[1]) if redir_out else None
    try:
        def _say(txt):
            (out or sys.stdout).write(txt)
        if name == "mv":
            if len(pos) < 2:
                print("[!] mv: faltan argumentos")
                return 1
            dst, rc = pos[-1], 0
            if len(pos) > 2 and not os.path.isdir(dst):
                print("[!] mv: el destino no es un directorio: %s" % dst)
                return 1
            for src in pos[:-1]:
                try:
                    if not os.path.lexists(src):
                        print("[!] mv: no existe: %s" % src)
                        rc = 1
                        continue
                    shutil.move(src, dst)
                    print("[ok] mv %s -> %s" % (src, dst))
                except (OSError, shutil.Error) as e:
                    print("[!] mv %s -> %s: %s" % (src, dst, e))
                    rc = 1
            return rc
        if name == "cp":
            rec = any(o in ("-r", "-R", "-a", "--recursive") or (not o.startswith("--") and ("r" in o or "R" in o or "a" in o))
                      for o in opts)
            if len(pos) < 2:
                print("[!] cp: faltan argumentos")
                return 1
            dst, rc = pos[-1], 0
            if len(pos) > 2 and not os.path.isdir(dst):
                print("[!] cp: el destino no es un directorio: %s" % dst)
                return 1
            for src in pos[:-1]:
                try:
                    if os.path.isdir(src):
                        if not rec:
                            print("[!] cp: %s es un directorio (usa -r)" % src)
                            rc = 1
                            continue
                        shutil.copytree(src, os.path.join(dst, os.path.basename(src.rstrip("/\\")))
                                        if os.path.isdir(dst) else dst, dirs_exist_ok=True)
                    else:
                        shutil.copy2(src, dst)
                    print("[ok] cp %s -> %s" % (src, dst))
                except (OSError, shutil.Error) as e:
                    print("[!] cp %s -> %s: %s" % (src, dst, e))
                    rc = 1
            return rc
        if name == "rm":
            rec = any(not o.startswith("--") and ("r" in o or "R" in o) for o in opts) or "--recursive" in opts
            force = any(not o.startswith("--") and "f" in o for o in opts) or "--force" in opts
            rc = 0
            home = os.path.realpath(os.path.expanduser("~"))
            for target in pos:
                real = os.path.realpath(target)
                if not target.strip() or real in (home, os.path.realpath(os.sep), os.path.splitdrive(real)[0] + os.sep):
                    print("[!] rm: se rechaza borrar %r" % target)
                    rc = 1
                    continue
                try:
                    if os.path.isdir(target) and not os.path.islink(target):
                        if not rec:
                            print("[!] rm: %s es un directorio (usa -r)" % target)
                            rc = 1
                            continue
                        shutil.rmtree(target)
                    elif os.path.lexists(target):
                        os.remove(target)
                    elif not force:
                        print("[!] rm: no existe: %s" % target)
                        rc = 1
                        continue
                    print("[ok] rm %s" % target)
                except OSError as e:
                    print("[!] rm %s: %s" % (target, e))
                    rc = 1
            return rc
        if name == "mkdir":
            rc = 0
            for d in [p for p in pos if p]:
                try:
                    if "-p" in opts:
                        os.makedirs(d, exist_ok=True)
                    else:
                        os.mkdir(d)
                    print("[ok] mkdir %s" % d)
                except OSError as e:
                    print("[!] mkdir %s: %s" % (d, e))
                    rc = 1
            return rc
        if name == "touch":
            rc = 0
            for f_ in pos:
                try:
                    with open(f_, "a"):
                        os.utime(f_, None)
                except OSError as e:
                    print("[!] touch %s: %s" % (f_, e))
                    rc = 1
            return rc
        if name == "cat":
            rc = 0
            srcs = pos or ([redir_in] if redir_in else [])
            if not srcs:
                print("[!] cat sin archivos (leeria stdin): no se ejecuta")
                return 1
            for f_ in srcs:
                try:
                    with open(f_, "r", errors="replace") as fh:
                        _say(fh.read())
                except OSError as e:
                    print("[!] cat %s: %s" % (f_, e))
                    rc = 1
            return rc
        if name == "echo":
            _say(" ".join(pos) + ("" if "-n" in opts else "\n"))
            return 0
        if name in ("gzip", "gunzip"):
            import gzip as _gz
            dec = name == "gunzip" or any(o in ("-d", "--decompress") for o in opts)
            keep = any(o in ("-k", "--keep") for o in opts)
            rc = 0
            for f_ in pos:
                try:
                    if dec:
                        dst = f_[:-3] if f_.lower().endswith(".gz") else f_ + ".out"
                        with _gz.open(f_, "rb") as a, open(dst, "wb") as b:
                            shutil.copyfileobj(a, b)
                    else:
                        dst = f_ + ".gz"
                        with open(f_, "rb") as a, _gz.open(dst, "wb") as b:
                            shutil.copyfileobj(a, b)
                    if not keep:
                        os.remove(f_)
                    print("[ok] %s %s -> %s" % (name, f_, dst))
                except (OSError, EOFError) as e:
                    print("[!] %s %s: %s" % (name, f_, e))
                    rc = 1
            return rc
        # --- interpretes de scripts ---
        env = dict(os.environ)
        for k, v in list(_BNX_RAW.items()):
            if k not in env:
                done = _bnx_value(k, 0, (), None)
                if isinstance(done, str) and done != "" and "$" not in done:
                    env[k] = done
        env.update(extra_env or {})
        if name in _BNX_RP_SHELLS:
            if "-c" in rest:
                # el texto de -c lo interpreta el shell: solo se acepta si -c y su texto son
                # literales de la plantilla (sin parametros)
                k = plantilla.index("-c") if "-c" in plantilla else -1
                if k < 0 or any("$" in t for t in plantilla[k + 1:k + 2]):
                    print("[!] Run_Program %s: '%s -c' con parametros no se ejecuta (evita inyeccion de "
                          "comandos); usa un script" % (nombre, name))
                    return 1
            sh = _bnx_rp_find_shell(name)
            if not sh:
                print("[!] Run_Program %s omitido: no hay interprete %s%s" % (
                    nombre, name, " (en Windows instala Git Bash o WSL)" if os.name == "nt" else ""))
                return 0
            script = next((a for a in rest if not a.startswith("-")), None)
            if script and "-c" not in rest and not os.path.isfile(script):
                print("[!] Run_Program %s: no existe el script %s" % (nombre, script))
                return 127
            argv2 = [sh] + rest
        else:
            exe = args[0] if os.sep in args[0] or "/" in args[0] else shutil.which(args[0])
            if not exe or not os.path.exists(exe):
                print("[!] Run_Program %s: comando no encontrado: %s" % (nombre, args[0]))
                return 127
            argv2 = [exe] + rest
        kw = {"env": env}
        fh_in = open(redir_in) if redir_in else None
        fh_err = open(redir_err[0], redir_err[1]) if redir_err else None
        try:
            if fh_in:
                kw["stdin"] = fh_in
            if out is not None:
                kw["stdout"] = out
            if fh_err:
                kw["stderr"] = fh_err
            elif err_to_out:
                kw["stderr"] = subprocess.STDOUT
            sys.stdout.flush()
            return subprocess.run(argv2, shell=False, **kw).returncode
        except OSError as e:
            print("[!] Run_Program %s: %s" % (nombre, e))
            return 126
        finally:
            for h in (fh_in, fh_err):
                if h:
                    h.close()
    finally:
        if out is not None:
            out.close()
def _bnx_run_program(argv, nombre="Run_Program", extra_env=None):
    """Ejecuta (o, por defecto, omite) el comando de un Run_Program. `argv`: lista de tokens
    de la plantilla con $VAR/${VAR} (o un str, que se separa con shlex). Devuelve el codigo de
    retorno, o None si se omitio / no se ejecuto."""
    if isinstance(argv, str):
        try:
            argv = _bnx_rp_tokenize(argv)
        except ValueError as e:
            print("[!] Run_Program %s: comando no interpretable (%s); omitido" % (nombre, e))
            return None
    argv = list(argv or [])
    if not argv:
        return None
    segs = _bnx_rp_split_ops(argv)
    empties = []
    expandidos = []
    for op, cmd in segs:
        expandidos.append((op, cmd, [_bnx_expand(t, 0, (), empties) for t in cmd]))
    texto = " ".join(" ".join(shlex.quote(t) for t in ex) if i == 0 else op + " " + " ".join(shlex.quote(t) for t in ex)
                     for i, (op, _c, ex) in enumerate(expandidos))
    if not _bnx_rp_on():
        print("[~] Run_Program %s omitido (activa BNX_RUN_PROGRAMS=1): %s" % (nombre, texto))
        return None
    sin = sorted(set(empties) | set(m.group(0)[1:].strip("{") for ex in expandidos for t in ex[2]
                                    for m in re.finditer(r"\$\{?[A-Za-z_]\w*", t)))
    if sin:
        print("[!] Run_Program %s NO se ejecuta: variables sin resolver o vacias (%s): %s. "
              "Definelas como variable de entorno o en el pset." % (nombre, ", ".join("$" + v for v in sin), texto))
        return None
    rc = 0
    for op, plant, ex in expandidos:
        if op == "&&" and rc != 0:
            continue
        if op == "||" and rc == 0:
            continue
        rc = _bnx_rp_exec(ex, plant, nombre, extra_env)
    if rc != 0:
        msg = "[!] Run_Program %s termino con codigo %s: %s" % (nombre, rc, texto)
        if _bnx_rp_flag("BNX_RUN_PROGRAMS_ESTRICTO"):
            raise RuntimeError(msg)
        print(msg + " (continua; BNX_RUN_PROGRAMS_ESTRICTO=1 aborta)")
    return rc
# <<< END BNX PARAMS RUNTIME


def runtime_source():
    """Texto del runtime a incrustar en un job generado."""
    path = os.path.abspath(__file__)
    with open(path, "r", encoding="utf-8") as fh:
        txt = fh.read()
    a = txt.index("# >>> BEGIN BNX PARAMS RUNTIME")
    b = txt.index("# <<< END BNX PARAMS RUNTIME")
    return txt[a:b] + "\n"


_SIMPLE_PARAM_PATH = re.compile(r"^[\w${}./\- ]+$")


def raw_path_fragment(path, node):
    """Fragmento f-string para la ruta de un Input File bajo raw/ cuando la ruta tiene
    referencias a parametros ($X / ${X}); None si no (el codegen usa su camino clasico)."""
    if not path:
        return None
    p = path.replace("\\{", "{").replace("\\}", "}").replace("\\$", "$")
    if "$" not in p or "$[" in p or not _SIMPLE_PARAM_PATH.match(p):
        return None
    n = node.replace("\\", "").replace("'", "")
    return "{_bnx_raw_name('%s', '%s')}" % (p, n)


def resolve_raw_name(path, node, defaults=None, env=None):
    """Mismo calculo que `_bnx_raw_name` del job, fuera del job (generador de datos,
    preflight). `defaults`: valores por defecto de la clase PARAMS del job; el entorno
    (os.environ y `env`) tiene prioridad, como en el job. Devuelve (nombre, avisos)."""
    g = globals()
    saved = (dict(_BNX_RAW), dict(_BNX_DONE), g["_bnx_warn"], g.get("PARAMS"))
    avisos = []
    try:
        _BNX_RAW.clear()
        _BNX_DONE.clear()
        for k, v in (defaults or {}).items():
            _BNX_RAW[k] = os.environ.get(k, v)
        for k, v in (env or {}).items():
            _BNX_RAW[str(k)] = str(v)
        g["_bnx_warn"] = lambda key, msg: avisos.append(msg)
        g.pop("PARAMS", None)
        return _bnx_raw_name(path, node), avisos
    finally:
        _BNX_RAW.clear()
        _BNX_RAW.update(saved[0])
        _BNX_DONE.clear()
        _BNX_DONE.update(saved[1])
        g["_bnx_warn"] = saved[2]
        if saved[3] is not None:
            g["PARAMS"] = saved[3]


def emit_params_runtime(f):
    """Escribe el runtime y su activacion en el job (tras definir `class PARAMS`)."""
    f.write("# =========================\n# PARAMETROS AB INITIO (runtime)\n# =========================\n")
    f.write(runtime_source())
    f.write("\n_bnx_resolve_params(PARAMS)\n_bnx_install_spark_shims()\n\n")
