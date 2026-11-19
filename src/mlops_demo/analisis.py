# -*- coding: utf-8 -*-
"""Analisis estatico (AST) del codigo del banco: que columnas usa cada lectura y con que tipo/valores."""
import ast
import json
import os
import re

from . import sqlmini
from .estado import E

_IDENT = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")
_FECHA = re.compile(r"^\d{4}-\d{2}-\d{2}")
FN_COL = set("""col sum avg mean min max count countDistinct first last collect_list collect_set stddev
variance abs round floor ceil trim upper lower length year month dayofmonth to_date to_timestamp date_format
months_between datediff coalesce lag lead isnull sqrt log exp greatest least concat substring substr
regexp_replace last_day add_months date_add date_sub dayofweek weekofyear""".split())
FN_TODAS = {"months_between", "datediff", "coalesce", "greatest", "least", "concat"}
FN_NUM = set("sum avg mean stddev variance abs round floor ceil sqrt log exp greatest least".split())
FN_FECHA = set("""to_date to_timestamp date_format months_between datediff dayofmonth year month last_day
add_months date_add date_sub dayofweek weekofyear""".split())
M_COLS = set("""select groupBy groupby orderBy sort partitionBy drop dropDuplicates fillna pivot
sortWithinPartitions cube rollup""".split())
LEE = set("""parquet csv json orc load table read_csv read_parquet read_json read_excel parquet_to_df
hive_table_to_df json_to_df sql""".split())
TIPOS_NUM = ("int", "integer", "bigint", "long", "double", "float", "decimal", "short", "tinyint")


class Archivo(object):
    def __init__(self):
        self.cols = set()
        self.num = set()
        self.fecha = set()
        self.str = set()
        self.pool = {}        # col -> [literales] (de ==, isin)
        self.claves = set()   # columnas de join(on=...)
        self.lecturas = {}    # lineno -> set(cols)
        self.sqls = []
        self.attrs = set()
        self.llamados = set()   # id() de los Attribute que son el func de una Call
        self.bases_no = set()   # nombres importados / funciones / clases: sus atributos no son columnas

    def todas(self):
        return set(c for c in (self.cols | self.attrs) if c not in _NO_COL)


_OBJ_CONOCIDOS = set("""self cls kernel email log logger args kwargs settings config cfg reader writer spark
sqlContext sc F T W os sys re json time datetime math np pd xgb pickle traceback checks dateUtils""".split())
_BUILTINS = set(dir(__builtins__) if not isinstance(__builtins__, dict) else __builtins__.keys())
_NO_COL = set()
try:
    from pyspark.sql import DataFrame as _DF
    _NO_COL = set(dir(_DF))
except Exception:       # pyspark no instalado: analisis sin filtro de metodos
    pass
_NO_COL |= {"self", "kernel", "log", "spark", "settings", "reader", "writer", "T", "F", "col"}


def _nombre(f):
    if isinstance(f, ast.Attribute):
        return f.attr
    if isinstance(f, ast.Name):
        return f.id
    return ""


def _const_str(n):
    return n.value if isinstance(n, ast.Constant) and isinstance(n.value, str) else None


def _col_de(n):
    """Nombre de columna si n es F.col('x') / col('x') / df['x'] / df.x o una cadena sobre ellos."""
    while isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute):
        if n.func.attr in ("col", "column") and n.args:
            return _const_str(n.args[0])
        n = n.func.value
    if isinstance(n, ast.Call) and _nombre(n.func) in ("col", "column") and n.args:
        return _const_str(n.args[0])
    if isinstance(n, ast.Subscript):
        sl = n.slice.value if isinstance(n.slice, getattr(ast, "Index", ())) else n.slice
        return _const_str(sl)
    if isinstance(n, ast.Attribute) and isinstance(n.value, ast.Name) and not n.attr.startswith("_"):
        return n.attr
    return None


def _valor_const(n):
    if isinstance(n, ast.Constant) and isinstance(n.value, (int, float, str)) and not isinstance(n.value, bool):
        return n.value
    if isinstance(n, ast.UnaryOp) and isinstance(n.op, ast.USub) and isinstance(n.operand, ast.Constant):
        return -n.operand.value
    return None


def _agregar_expr(a, texto):
    try:
        for c in sqlmini.ids_expresion(texto):
            a.cols.add(c)
    except Exception:
        pass


def _ids(a, n):
    s = _const_str(n)
    if s is not None:
        if _IDENT.match(s):
            a.cols.add(s)
        elif len(s) < 400 and any(ch in s for ch in " (=<>"):
            _agregar_expr(a, s)
    elif isinstance(n, (ast.List, ast.Tuple, ast.Set)):
        for e in n.elts:
            _ids(a, e)
    elif isinstance(n, ast.Dict):
        for k in n.keys:
            if k is not None:
                _ids(a, k)


def _claves(a, n):
    s = _const_str(n)
    if s is not None and _IDENT.match(s):
        a.claves.add(s)
    elif isinstance(n, (ast.List, ast.Tuple)):
        for e in n.elts:
            _claves(a, e)


def _llamada(a, c):
    nm = _nombre(c.func)
    if nm in FN_COL and c.args:
        rango = c.args if nm in FN_TODAS else c.args[:1]
        for x in rango:
            s = _const_str(x)
            if s is not None and _IDENT.match(s):
                a.cols.add(s)
                if nm in FN_NUM:
                    a.num.add(s)
                if nm in FN_FECHA:
                    a.fecha.add(s)
    if nm in M_COLS:
        for x in c.args:
            _ids(a, x)
        for kw in c.keywords:
            if kw.arg == "subset":
                _ids(a, kw.value)
    if nm == "withColumnRenamed" and c.args:
        _ids(a, c.args[0])
    if nm in ("filter", "where", "selectExpr", "expr") and c.args:
        for x in c.args:
            s = _const_str(x)
            if s:
                _agregar_expr(a, s)
    if nm == "join":
        for kw in c.keywords:
            if kw.arg == "on":
                _ids(a, kw.value)
                _claves(a, kw.value)
        if len(c.args) > 1:
            _ids(a, c.args[1])
            _claves(a, c.args[1])
    if nm == "agg":
        for x in c.args:
            _ids(a, x)
    if nm == "isin":
        col = _col_de(c.func.value) if isinstance(c.func, ast.Attribute) else None
        vals = []
        for x in c.args:
            vals.extend(x.elts if isinstance(x, (ast.List, ast.Tuple, ast.Set)) else [x])
        vs = [_valor_const(v) for v in vals if _valor_const(v) is not None]
        if col and vs:
            a.pool.setdefault(col, []).extend(vs)
            a.cols.add(col)
    if nm in ("like", "rlike", "startswith", "endswith", "contains") and isinstance(c.func, ast.Attribute):
        col = _col_de(c.func.value)
        if col:
            a.str.add(col)
            a.cols.add(col)
    if nm == "cast" and isinstance(c.func, ast.Attribute) and c.args:
        col, t = _col_de(c.func.value), (_const_str(c.args[0]) or "").lower()
        if col:
            a.cols.add(col)
            if t.split("(")[0] in TIPOS_NUM:
                a.num.add(col)
            elif t in ("date", "timestamp"):
                a.fecha.add(col)


def _otros(a, n):
    if isinstance(n, ast.Compare):
        izq = _col_de(n.left)
        for op, der in zip(n.ops, n.comparators):
            v = _valor_const(der)
            col = izq or _col_de(der)
            if col:
                a.cols.add(col)
            if izq and v is not None:
                if isinstance(v, str):
                    (a.fecha if _FECHA.match(v) else a.str).add(izq)
                    if isinstance(op, (ast.Eq,)):
                        a.pool.setdefault(izq, []).append(v)
                else:
                    a.num.add(izq)
                    if isinstance(op, ast.Eq):
                        a.pool.setdefault(izq, []).append(v)
    elif isinstance(n, ast.BinOp) and isinstance(n.op, (ast.Add, ast.Sub, ast.Mult, ast.Div, ast.Mod)):
        for x in (n.left, n.right):
            col = _col_de(x)
            if col:
                a.cols.add(col)
                a.num.add(col)
    elif isinstance(n, ast.Subscript):
        col = _col_de(n)
        if col and _IDENT.match(col):
            a.cols.add(col)
        sl = n.slice.value if isinstance(n.slice, getattr(ast, "Index", ())) else n.slice
        if isinstance(sl, (ast.List, ast.Tuple)):
            _ids(a, sl)
    elif isinstance(n, ast.Attribute) and isinstance(n.value, ast.Name):
        base = n.value.id
        if id(n) not in a.llamados and base not in a.bases_no and base not in _OBJ_CONOCIDOS \
                and not n.attr.startswith("__") and n.attr not in _BUILTINS:
            a.attrs.add(n.attr)
    elif isinstance(n, (ast.Constant,)) and isinstance(n.value, str) and len(n.value) > 15:
        low = n.value.lstrip().lower()
        if (low.startswith("select") or low.startswith("with ")) and " from " in low.replace("\n", " "):
            a.sqls.append(n.value)


def _lecturas(a, tree):
    """Asocia cada llamada de lectura a las columnas de su cadena y a las que se usan sobre su variable."""
    for fn in [x for x in ast.walk(tree) if isinstance(x, (ast.FunctionDef, ast.AsyncFunctionDef))] + [tree]:
        for st in ast.walk(fn):
            if not isinstance(st, (ast.Assign, ast.AnnAssign)):
                continue
            val = st.value
            if val is None:
                continue
            lecturas = [c for c in ast.walk(val) if isinstance(c, ast.Call) and _nombre(c.func) in LEE]
            if not lecturas:
                continue
            tg = st.targets[0] if isinstance(st, ast.Assign) else st.target
            var = tg.id if isinstance(tg, ast.Name) else (tg.attr if isinstance(tg, ast.Attribute) else None)
            sub = Archivo()
            for c in ast.walk(val):
                if isinstance(c, ast.Call):
                    _llamada(sub, c)
                _otros(sub, c)
            if var:
                for c in ast.walk(fn):
                    base = None
                    if isinstance(c, (ast.Subscript, ast.Attribute)) and isinstance(c.value, ast.Name):
                        base = c.value.id
                    elif isinstance(c, ast.Call) and isinstance(c.func, ast.Attribute):
                        b = c.func.value
                        while isinstance(b, (ast.Call, ast.Attribute)):
                            b = b.func.value if isinstance(b, ast.Call) and isinstance(b.func, ast.Attribute) \
                                else (b.value if isinstance(b, ast.Attribute) else None)
                            if b is None:
                                break
                        base = b.id if isinstance(b, ast.Name) else None
                    if base == var:
                        for x in ast.walk(c):
                            if isinstance(x, ast.Call):
                                _llamada(sub, x)
                            _otros(sub, x)
            cols = sub.todas()
            for c in lecturas:
                a.lecturas[c.lineno] = set(cols)


_CACHE = {}


def analizar_archivo(ruta):
    ruta = os.path.abspath(ruta)
    if ruta in _CACHE:
        return _CACHE[ruta]
    a = Archivo()
    try:
        with open(ruta, encoding="utf-8", errors="replace") as fh:
            tree = ast.parse(fh.read())
        # atributos que NO son columnas (df.col): llamadas (obj.metodo(...)), modulos/clases importados,
        # objetos conocidos (self, kernel, email...) y variables que se asignan desde una llamada a clase.
        for n in ast.walk(tree):
            if isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute):
                a.llamados.add(id(n.func))
            elif isinstance(n, ast.Import):
                a.bases_no.update((x.asname or x.name).split(".")[0] for x in n.names)
            elif isinstance(n, ast.ImportFrom):
                a.bases_no.update(x.asname or x.name for x in n.names)
            elif isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                a.bases_no.add(n.name)
                if not isinstance(n, ast.ClassDef):
                    a.bases_no.update(x.arg for x in n.args.args if x.arg in _OBJ_CONOCIDOS)
        for n in ast.walk(tree):
            if isinstance(n, ast.Call):
                _llamada(a, n)
            _otros(a, n)
        _lecturas(a, tree)
    except (OSError, SyntaxError, ValueError, RecursionError):
        pass
    _CACHE[ruta] = a
    return a


def columnas_lectura(ruta, lineno):
    """Columnas de una lectura (por variable si se pudo asociar) o la union de las del archivo."""
    a = analizar_archivo(ruta)
    if lineno in a.lecturas and a.lecturas[lineno]:
        return sorted(a.lecturas[lineno])
    return sorted(a.todas())


def usos_columna(col):
    """Pistas de tipo/valores de una columna acumuladas en todo el codigo del banco analizado."""
    low = col.lower()
    out = {"num": False, "fecha": False, "str": False, "clave": False, "pool": []}
    for a in _CACHE.values():
        for k, dst in (("num", a.num), ("fecha", a.fecha), ("str", a.str), ("clave", a.claves)):
            if any(x.lower() == low for x in dst):
                out[k] = True
        for c, vs in a.pool.items():
            if c.lower() == low:
                for v in vs:
                    if v not in out["pool"]:
                        out["pool"].append(v)
    return out


def precargar(dirs):
    for d in dirs or []:
        for r, _ds, fs in os.walk(d):
            if any(p in r for p in ("__pycache__", ".git")):
                continue
            for f in fs:
                if f.endswith(".py"):
                    analizar_archivo(os.path.join(r, f))


def registro_settings(settings_dir):
    """tabla(lower) -> columnas, de los settings (tables_info: database/table/columns, extract: libname/...)
    y de los SQL (queries) que viajan en los JSON."""
    reg = {}

    def _add(tabla, cols):
        t = tabla.lower()
        lst = reg.setdefault(t, [])
        for c in cols:
            if c and c not in lst:
                lst.append(c)

    def _walk(o):
        if isinstance(o, dict):
            if isinstance(o.get("table"), str) and isinstance(o.get("columns"), list):
                db = o.get("database") or o.get("db") or ""
                cs = []
                for x in o["columns"]:
                    if isinstance(x, str):
                        cs.extend(sqlmini.ids_expresion(x.replace("{}", "x")))
                _add((db + "." if db else "") + o["table"], cs)
            ln, tn, sv = o.get("libname"), o.get("table_name"), o.get("select_variables")
            if isinstance(ln, list) and isinstance(tn, list) and isinstance(sv, list):
                for l, t, s in zip(ln, tn, sv):
                    cs = []
                    for p in sqlmini.separar_select(s or ""):
                        cs.extend(sqlmini.ids_expresion(p))
                    _add("%s.%s" % (l, t), cs)
            for v in o.values():
                _walk(v)
        elif isinstance(o, list):
            for v in o:
                _walk(v)
        elif isinstance(o, str):
            low = o.lstrip().lower()
            if (low.startswith("select") or low.startswith("with ")) and " from " in low.replace("\n", " "):
                try:
                    info = sqlmini.analizar(o.replace("{}", "'x'"))
                    for t, cs in info["cols"].items():
                        _add(t, cs)
                except Exception:
                    pass
    if settings_dir and os.path.isdir(settings_dir):
        for r, _d, fs in os.walk(settings_dir):
            for f in fs:
                if f.endswith(".json"):
                    try:
                        with open(os.path.join(r, f), encoding="utf-8") as fh:
                            _walk(json.load(fh))
                    except (OSError, ValueError):
                        pass
    return reg


def features_de_settings(settings_dir):
    """{fuente: [variables]} de la clave 'dqc_sources' de los settings (lista de variables del modelo)."""
    out = {}

    def _walk(o):
        if isinstance(o, dict):
            d = o.get("dqc_sources")
            if isinstance(d, dict):
                for k, v in d.items():
                    if isinstance(v, list) and all(isinstance(x, str) for x in v):
                        out.setdefault(k, [])
                        out[k].extend(x for x in v if x not in out[k])
            for v in o.values():
                _walk(v)
        elif isinstance(o, list):
            for v in o:
                _walk(v)
    if settings_dir and os.path.isdir(settings_dir):
        for r, _d, fs in os.walk(settings_dir):
            for f in fs:
                if f.endswith(".json"):
                    try:
                        with open(os.path.join(r, f), encoding="utf-8") as fh:
                            _walk(json.load(fh))
                    except (OSError, ValueError):
                        pass
    return out
