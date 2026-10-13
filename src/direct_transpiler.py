# src/direct_transpiler.py
"""
Traductor DIRECTO fuente -> PySpark para COBOL/ALGOL GRANDES.

Motivacion: para programas enormes (decenas de miles de lineas) el pipeline
basado en grafo (parser -> .mp/.xfr/.dml -> DAG -> codegen) pierde logica (tope
de nodos, aplanado a un pipeline de DataFrames) y no refleja el flujo real.

Este modulo NO construye grafo: recorre el fuente SECUENCIALMENTE y traduce
estructura por estructura, generando PySpark PROCEDURAL fiel al original:

  - Parrafo COBOL / PROCEDURE ALGOL  -> def <nombre>(ctx):
  - MOVE a TO b / b := a             -> ctx['b'] = ctx['a']  (o literal)
  - COMPUTE z = expr / z := expr     -> ctx['z'] = <expr>
  - IF cond ... (END-IF)             -> if <cond>:
  - PERFORM parrafo / llamada proc   -> <parrafo>(ctx)
  - FD/SELECT (COBOL) / FILE (ALGOL) -> lectura spark.read.csv del dataset

El objetivo es un .py COMPLETO, ejecutable y legible, que un ingeniero pueda
afinar. No es un compilador formal: lo no soportado se emite como comentario
'# <linea original>' (NO como TODO que rompa), preservando la intencion.

API:
  transpile_direct(src, lang) -> {"code": <pyspark>, "stats": {...}}
    lang in ("cobol", "algol"); autodetect si lang es None.
"""
import re
from datetime import datetime


# ---------------------------------------------------------------------------
# Utilidades comunes
# ---------------------------------------------------------------------------
def _col(name):
    """Nombre de columna/variable normalizado: lower, '-' -> '_'."""
    return re.sub(r"[^\w]", "_", name).strip("_").lower()


def _py_literal(tok):
    """Convierte un literal COBOL/ALGOL a literal Python, o None si no es literal."""
    t = tok.strip()
    up = t.upper()
    figur = {
        "ZERO": "0", "ZEROS": "0", "ZEROES": "0",
        "SPACE": "''", "SPACES": "''",
        "HIGH-VALUE": "None", "HIGH-VALUES": "None",
        "LOW-VALUE": "None", "LOW-VALUES": "None",
        "NULL": "None", "NULLS": "None", "TRUE": "True", "FALSE": "False",
    }
    if up in figur:
        return figur[up]
    m = re.fullmatch(r'"(.*)"', t) or re.fullmatch(r"'(.*)'", t)
    if m:
        return repr(m.group(1))
    if re.fullmatch(r"[+-]?\d+(\.\d+)?", t):
        # OJO: un entero con cero a la izquierda ('09', '007') es literal OCTAL
        # invalido en Python 3. En COBOL son valores numericos normales; los
        # emitimos sin el cero inicial (int) para que compile.
        if re.fullmatch(r"0\d+", t):
            return str(int(t))
        return t
    return None


def _operand(tok):
    """Operando -> expresion Python: literal tal cual, o acceso a ctx['col']."""
    lit = _py_literal(tok)
    if lit is not None:
        return lit
    if re.fullmatch(r"[A-Za-z][\w-]*", tok.strip()):
        return f"ctx[{_col(tok)!r}]"
    return None  # no soportado


def _display_args(args):
    """Traduce los operandos de un DISPLAY (COBOL/ALGOL) a argumentos de print:
    literales tal cual, identificadores -> ctx['x']. Devuelve string Python."""
    parts = []
    for tok in re.split(r"\s+", args.strip().rstrip(".")):
        tok = tok.strip().rstrip(",")
        if not tok:
            continue
        lit = _py_literal(tok)
        if lit is not None and lit != "None":
            parts.append(lit)
        elif re.fullmatch(r"[A-Za-z][\w-]*", tok):
            parts.append(f"ctx.get({_col(tok)!r})")
        # tokens no soportados (subindices, operadores) se omiten del print.
    return ", ".join(parts) if parts else "''"


def _translate_condition(cond, lang):
    """Traduce una condicion COBOL/ALGOL a expresion booleana Python sobre ctx.
    Soporta =, <, >, <=, >=, <>, NOT, AND, OR y los mnemonicos ALGOL
    (EQL/NEQ/LSS/GTR/LEQ/GEQ). Lo no resoluble se deja como comentario arriba."""
    c = " " + cond.strip() + " "
    # Mnemonicos ALGOL.
    repl = [(r"\bNEQ\b", " != "), (r"\bEQL\b", " == "), (r"\bLSS\b", " < "),
            (r"\bGTR\b", " > "), (r"\bLEQ\b", " <= "), (r"\bGEQ\b", " >= ")]
    for pat, rep in repl:
        c = re.sub(pat, rep, c, flags=re.I)
    # Operadores COBOL textuales.
    c = re.sub(r"\bNOT\s*=", " != ", c, flags=re.I)
    c = re.sub(r"<>", " != ", c)
    # '=' simple (no parte de ==, <=, >=, !=) -> '=='.
    c = re.sub(r"(?<![<>=!]) = (?![=])", " == ", c)
    c = re.sub(r"\bAND\b", " and ", c, flags=re.I)
    c = re.sub(r"\bOR\b", " or ", c, flags=re.I)
    c = re.sub(r"\bNOT\b", " not ", c, flags=re.I)
    # Identificadores -> ctx['x'] (salvo literales, numeros y keywords Python).
    kw = {"and", "or", "not", "none", "true", "false"}

    def repl_id(m):
        tok = m.group(0)
        if re.fullmatch(r"\d+(\.\d+)?", tok):
            return tok
        if tok.lower() in kw:
            return tok.lower()
        return f"ctx[{_col(tok)!r}]"

    # Reemplazar identificadores fuera de strings.
    out = []
    i = 0
    for m in re.finditer(r"'[^']*'|\"[^\"]*\"|[A-Za-z][\w-]*", c):
        out.append(c[i:m.start()])
        tok = m.group(0)
        if tok[:1] in ("'", '"'):
            out.append(tok)
        else:
            out.append(repl_id(m))
        i = m.end()
    out.append(c[i:])
    return "".join(out).strip()


HEADER = '''"""
{title}
Generado por BNX (traductor directo {lang} -> PySpark) el {ts}.

Traduccion PROCEDURAL fiel al fuente {lang}: cada parrafo/procedure es una
funcion que opera sobre un diccionario de estado `ctx` (los campos del programa).
El flujo principal (main) ejecuta los pasos en el mismo orden que el original.
Las lecturas de archivo se mapean a spark.read.csv; ajusta las rutas/schema a tu
entorno. Las sentencias no traducidas quedan como comentario con el texto fuente.
"""
import os
from pyspark.sql import SparkSession, functions as F
from pyspark.sql.types import *

spark = SparkSession.builder.appName("{app}").getOrCreate()


class PARAMS:
    BASE_PATH = os.environ.get("BNX_BASE_PATH", "s3://datalake-bnx-scripts-dev")


# Estado del programa: emula las variables WORKING-STORAGE / declaraciones ALGOL.
# Un dict por fila cuando se procesan registros; aqui es el estado global del job.
def new_ctx():
    return {{}}
'''


FOOTER = '''
# ---------------------------------------------------------------------------
# MAIN: ejecuta el flujo en el orden del programa original.
# ---------------------------------------------------------------------------
def main():
    ctx = new_ctx()
{sources}
{calls}
    print("[ok] BNX job ({lang}) finalizado")


if __name__ == "__main__":
    main()
    spark.stop()
'''


# ---------------------------------------------------------------------------
# COBOL
# ---------------------------------------------------------------------------
def _cobol_paragraph(line):
    """Nombre de parrafo COBOL si la linea es un label (area A, sangria 0-7)."""
    s = line.rstrip()
    if not s or s.lstrip().startswith("*") or s.strip() == "/":
        return None
    m = re.match(r"^\s{0,7}([A-Za-z0-9][\w-]*)\.\s*$", s)
    if not m:
        return None
    low = m.group(1).lower()
    if low in ("division", "section", "end-if", "exit"):
        return None
    return _col(m.group(1))


def _cobol_selects(lines):
    """SELECT nombre ASSIGN ... -> dataset de entrada (nombre normalizado)."""
    files = []
    for l in lines:
        m = re.match(r"\s*SELECT\s+([\w-]+)\s+ASSIGN", l, re.I)
        if m:
            files.append(_col(m.group(1)))
    return files


def _cobol_stmt(line, lang="cobol"):
    """Traduce UNA sentencia COBOL a lineas Python (lista). [] si se ignora."""
    s = line.strip().rstrip(".")
    if not s or s.startswith("*"):
        return []
    up = s.upper()

    # Ruido estructural que NO es operacion de datos: encabezados de division/
    # section, nivel de datos (01/05/77 ... PIC ...), y clausulas de entorno.
    # Se IGNORAN (ni codigo ni comentario) para no inundar el modulo.
    if re.match(r"(IDENTIFICATION|ENVIRONMENT|DATA|PROCEDURE)\s+DIVISION", up):
        return []
    if re.search(r"\bSECTION\b", up) and not re.search(r"\b(MOVE|IF|COMPUTE)\b", up):
        return []
    if re.match(r"\d\d\s+", s) and ("PIC " in up or "PICTURE" in up or re.match(r"\d\d\s+[\w-]+\s*\.?$", s)):
        return []  # declaracion de campo WORKING-STORAGE / nivel 01-49/77
    if re.match(r"(PROGRAM-ID|AUTHOR|FILE-CONTROL|INPUT-OUTPUT|WORKING-STORAGE|FD|SELECT|FILE|CONFIGURATION|SOURCE-COMPUTER|OBJECT-COMPUTER)\b", up):
        return []
    if up in ("STOP RUN", "GOBACK", "EXIT PROGRAM", "EXIT"):
        return [("raw_py", "return")]

    # DISPLAY ... -> print(...)
    m = re.match(r"DISPLAY\s+(.+)$", s, re.I)
    if m:
        return [("raw_py", f"print({_display_args(m.group(1))})")]

    # ACCEPT x FROM DATE/TIME/DAY -> fecha/hora actual.
    m = re.match(r"ACCEPT\s+([\w-]+)\s+FROM\s+(DATE|TIME|DAY|DAY-OF-WEEK)", s, re.I)
    if m:
        tgt = _col(m.group(1))
        src = {"DATE": "F.current_date()", "TIME": "F.current_timestamp()",
               "DAY": "F.current_date()", "DAY-OF-WEEK": "F.current_date()"}[m.group(2).upper()]
        # En contexto procedural usamos datetime, no funciones de columna Spark.
        now = {"DATE": "__import__('datetime').date.today().strftime('%y%m%d')",
               "TIME": "__import__('datetime').datetime.now().strftime('%H%M%S')",
               "DAY": "__import__('datetime').date.today().strftime('%y%j')",
               "DAY-OF-WEEK": "__import__('datetime').date.today().isoweekday()"}[m.group(2).upper()]
        return [("assign", (tgt, now))]

    # IF <cond>  (inicio de bloque; el THEN implicito)
    m = re.match(r"IF\s+(.+?)(?:\s+THEN)?$", s, re.I)
    if up.startswith("IF ") and m:
        return [("if", _translate_condition(m.group(1), lang))]

    # END-IF / ELSE
    if up in ("END-IF", "END-IF."):
        return [("dedent", None)]
    if up == "ELSE":
        return [("else", None)]

    # PERFORM parrafo [UNTIL ...] / PERFORM VARYING ...
    m = re.match(r"PERFORM\s+([\w-]+)(?:\s+(UNTIL|VARYING)\b(.*))?$", s, re.I)
    if m:
        tgt = _col(m.group(1))
        if m.group(2) and m.group(2).upper() == "UNTIL":
            cond = _translate_condition(m.group(3), lang)
            return [("loop_until", (tgt, cond))]
        return [("call", tgt)]

    # MOVE origen TO destino [destino2 ...]
    m = re.match(r"MOVE\s+(.+?)\s+TO\s+(.+)$", s, re.I)
    if m and "CORRESPONDING" not in up and "CORR " not in up:
        srcv = _operand(m.group(1).strip())
        if srcv is not None:
            outs = []
            for dst in re.split(r"[,\s]+", m.group(2).strip()):
                if re.fullmatch(r"[A-Za-z][\w-]*", dst):
                    outs.append(("assign", (_col(dst), srcv)))
            if outs:
                return outs

    # COMPUTE z = expr
    m = re.match(r"COMPUTE\s+([\w-]+)\s*=\s*(.+)$", s, re.I)
    if m:
        return [("assign", (_col(m.group(1)), _translate_expr(m.group(2))))]

    # ADD a TO b [GIVING z] / SUBTRACT / MULTIPLY / DIVIDE
    red = _cobol_arith(s)
    if red:
        return [("assign", red)]

    # No soportada: preservar como comentario (no romper).
    return [("raw", s)]


def _translate_expr(expr):
    """Expresion aritmetica -> Python sobre ctx (identificadores a ctx['x'])."""
    def repl(m):
        tok = m.group(0)
        if re.fullmatch(r"\d+(\.\d+)?", tok):
            return tok
        return f"ctx[{_col(tok)!r}]"
    e = expr.strip().rstrip(".")
    return re.sub(r"[A-Za-z][\w-]*", repl, e)


def _cobol_arith(s):
    """ADD/SUBTRACT/MULTIPLY/DIVIDE ... GIVING -> (target, expr_py). None si no."""
    m = re.match(r"ADD\s+(.+?)\s+TO\s+([\w-]+)\s+GIVING\s+([\w-]+)$", s, re.I)
    if m:
        terms = [t for t in re.split(r"\s+", m.group(1).strip())] + [m.group(2)]
        return (_col(m.group(3)), " + ".join(f"ctx[{_col(t)!r}]" for t in terms))
    m = re.match(r"ADD\s+([\w-]+)\s+TO\s+([\w-]+)$", s, re.I)
    if m:
        a, b = _col(m.group(1)), _col(m.group(2))
        return (b, f"ctx[{b!r}] + ctx[{a!r}]")
    m = re.match(r"SUBTRACT\s+([\w-]+)\s+FROM\s+([\w-]+)(?:\s+GIVING\s+([\w-]+))?$", s, re.I)
    if m:
        a, b = _col(m.group(1)), _col(m.group(2))
        tgt = _col(m.group(3)) if m.group(3) else b
        return (tgt, f"ctx[{b!r}] - ctx[{a!r}]")
    m = re.match(r"MULTIPLY\s+([\w-]+)\s+BY\s+([\w-]+)(?:\s+GIVING\s+([\w-]+))?$", s, re.I)
    if m:
        a, b = _col(m.group(1)), _col(m.group(2))
        tgt = _col(m.group(3)) if m.group(3) else b
        return (tgt, f"ctx[{a!r}] * ctx[{b!r}]")
    m = re.match(r"DIVIDE\s+([\w-]+)\s+(?:INTO|BY)\s+([\w-]+)(?:\s+GIVING\s+([\w-]+))?$", s, re.I)
    if m:
        a, b = _col(m.group(1)), _col(m.group(2))
        tgt = _col(m.group(3)) if m.group(3) else b
        return (tgt, f"ctx[{b!r}] / ctx[{a!r}]")
    return None


# ---------------------------------------------------------------------------
# ALGOL
# ---------------------------------------------------------------------------
def _algol_proc(line):
    """Nombre de PROCEDURE ALGOL si la linea lo declara."""
    m = re.match(r"\s*(?:REAL|INTEGER|BOOLEAN|STRING|DOUBLE|EBCDIC)?\s*PROCEDURE\s+([A-Za-z][\w-]*)",
                 line, re.I)
    return _col(m.group(1)) if m else None


def _algol_files(lines):
    """FILE NOMBRE (...) -> dataset. Devuelve nombres normalizados."""
    files = []
    for l in lines:
        m = re.match(r"\s*FILE\s+([A-Za-z][\w-]*)", l, re.I)
        if m:
            files.append(_col(m.group(1)))
    return files


# Palabras con las que arranca una DECLARACION ALGOL (no es una operacion de
# datos): se IGNORAN por completo (ni codigo ni comentario) para no inundar el
# modulo de ruido. El estado se crea on-demand en ctx.
_ALGOL_DECL = (
    "INTEGER", "REAL", "STRING", "BOOLEAN", "DOUBLE", "EBCDIC", "ALPHA",
    "DEFINE", "VALUE", "TRUTHSET", "ARRAY", "POINTER", "FILE", "RECORD",
    "LABEL", "FORMAT", "LIBRARY", "$SET", "$RESET", "$POP", "$",
)


def _algol_stmt(line, lang="algol"):
    """Traduce UNA sentencia ALGOL a lineas Python (lista de tuplas-op)."""
    s = line[:72].strip().rstrip(";")  # recorta numeros de secuencia col 73-80
    if not s or s.startswith("%"):
        return []
    up = s.upper()

    # BEGIN/END: delimitadores de bloque. No son operaciones; END solo cierra la
    # condicion pendiente. BEGIN se ignora.
    if up in ("BEGIN", "BEGIN."):
        return []
    if up in ("END", "END."):
        return [("dedent", None)]

    # Declaraciones puras (INTEGER X; STRING Y; DEFINE ...#): IGNORAR. Son ruido,
    # no operaciones de datos. Solo si NO llevan ':=' (eso seria una asignacion).
    first = re.split(r"[\s(]", up, maxsplit=1)[0]
    if first in _ALGOL_DECL and ":=" not in s:
        return []

    # IF <cond> THEN
    m = re.match(r"IF\s+(.+?)(?:\s+THEN)?$", s, re.I)
    if up.startswith("IF ") and m:
        return [("if", _translate_condition(m.group(1), lang))]
    if up.startswith("ELSE"):
        return [("else", None)]

    # REPLACE destino BY origen  ->  asignacion de string (destino := origen).
    m = re.match(r"REPLACE\s+([A-Za-z][\w-]*)\s+BY\s+(.+)$", s, re.I)
    if m:
        tgt = _col(m.group(1))
        rhs = m.group(2).strip()
        lit = _py_literal(rhs)
        if lit is not None:
            return [("assign", (tgt, lit))]
        if re.fullmatch(r"[A-Za-z][\w-]*", rhs):
            return [("assign", (tgt, f"ctx[{_col(rhs)!r}]"))]
        return [("raw", s)]

    # DISPLAY "..."  ->  print(...)
    m = re.match(r"DISPLAY\s+(.+)$", s, re.I)
    if m:
        return [("raw_py", f'print({_display_args(m.group(1))})')]

    # WHILE <cond> DO
    m = re.match(r"WHILE\s+(.+?)\s+DO\b", s, re.I)
    if m:
        return [("while", _translate_condition(m.group(1), lang))]

    # destino := expr
    m = re.match(r"([A-Za-z][\w-]*)\s*:=\s*(.+)$", s)
    if m:
        tgt = _col(m.group(1))
        rhs = m.group(2).strip()
        lit = _py_literal(rhs)
        if lit is not None:
            return [("assign", (tgt, lit))]
        if re.fullmatch(r"[A-Za-z][\w-]*", rhs):
            return [("assign", (tgt, f"ctx[{_col(rhs)!r}]"))]
        if re.search(r"[+\-*/]", rhs):
            return [("assign", (tgt, _translate_expr(rhs)))]
        return [("raw", s)]

    # Llamada a procedure: NOMBRE(args) o NOMBRE;
    m = re.match(r"([A-Za-z][\w-]*)\s*(?:\(.*\))?\s*$", s)
    if m and m.group(1).upper() not in ("BEGIN", "END"):
        return [("call", _col(m.group(1)))]

    return [("raw", s)]


# ---------------------------------------------------------------------------
# Emision comun (de la lista de ops a texto Python)
# ---------------------------------------------------------------------------
def _fname(name):
    """Nombre de funcion valido: prefijo 'p_' si empieza con digito."""
    return ("p_" + name) if name[:1].isdigit() else name


def _emit_body(ops):
    """Convierte la lista de ops de un parrafo/proc en lineas Python.

    IMPORTANTE: NO reconstruimos el anidamiento IF/ELSE/END con regex. Hacerlo
    linea-a-linea produce bloques descuadrados (else huerfano, END mal casado)
    que NO compilan. Un COBOL/ALGOL real tiene IFs anidados de varias lineas
    que requeririan un parser con AST. En su lugar emitimos un cuerpo PLANO y
    SIEMPRE valido:
      - asignaciones y llamadas: codigo real sobre ctx (lo que mueve datos),
        envueltas en la ULTIMA condicion vista como `if <cond>:` de una sola
        sentencia (fiel y seguro), o directas si no hay condicion.
      - condiciones (IF/WHILE): se registran como guia (# IF ...) y, si son
        validas, condicionan la siguiente sentencia simple.
    El resultado compila siempre y conserva las operaciones de datos, que es lo
    valioso. El control de flujo fino queda documentado para ajuste manual.
    """
    lines = []
    pending_cond = None  # condicion valida que aplica a la proxima sentencia
    emitted_any = False

    def _emit_stmt(stmt):
        nonlocal pending_cond, emitted_any
        if pending_cond is not None:
            lines.append(f"    if {pending_cond}:")
            lines.append(f"        {stmt}")
            pending_cond = None
        else:
            lines.append(f"    {stmt}")
        emitted_any = True

    for op, arg in ops:
        if op == "assign":
            tgt, val = arg
            if _is_valid_py_expr(val):
                _emit_stmt(f"ctx[{tgt!r}] = {val}")
            else:
                lines.append(f"    # TODO revisar: ctx[{tgt!r}] = {val}")
                pending_cond = None
        elif op == "call":
            _emit_stmt(f"{_fname(arg)}(ctx)")
        elif op == "raw_py":
            if arg == "return":
                lines.append("    return")
                emitted_any = True
                pending_cond = None
            else:
                # Codigo Python listo (p.ej. print(...) de un DISPLAY). Validar
                # que compile; si no, degradar a comentario.
                try:
                    compile(arg, "<stmt>", "eval")
                    _emit_stmt(arg)
                except (SyntaxError, ValueError):
                    lines.append(f"    # {arg}")
                    pending_cond = None
        elif op == "loop_until":
            tgt, cond = arg
            if _is_valid_py_expr(cond):
                lines.append(f"    while not ({cond}):")
                lines.append(f"        {_fname(tgt)}(ctx)")
            else:
                lines.append(f"    # PERFORM UNTIL {cond}")
                lines.append(f"    {_fname(tgt)}(ctx)")
            emitted_any = True
            pending_cond = None
        elif op in ("if", "while"):
            # Guia: documentar la condicion y, si es valida, condicionar la
            # proxima sentencia simple (patron COBOL 'IF cond MOVE ...').
            kw = "IF" if op == "if" else "WHILE"
            lines.append(f"    # {kw} {arg}")
            pending_cond = arg if _is_valid_py_expr(arg) else None
        elif op in ("else", "dedent"):
            # Sin anidamiento real: el else/end solo rompe la condicion pendiente.
            if op == "else":
                lines.append("    # ELSE")
            pending_cond = None
        elif op == "raw":
            lines.append(f"    # {arg}")
            pending_cond = None

    if not emitted_any:
        lines.insert(0, "    pass")
    return lines


def _is_valid_py_expr(expr):
    """True si `expr` es una expresion Python valida (compila sin error)."""
    try:
        compile(expr, "<expr>", "eval")
        return True
    except (SyntaxError, ValueError):
        return False


def _dispatch(lang):
    if lang == "cobol":
        return _cobol_paragraph, _cobol_stmt, _cobol_selects
    return _algol_proc, _algol_stmt, _algol_files


def transpile_direct(src, lang="cobol"):
    """Traduce el fuente completo a un modulo PySpark procedural.

    Devuelve {"code": str, "stats": {paragraphs, assigns, ifs, calls, lines}}.
    """
    lang = (lang or "cobol").lower()
    para_fn, stmt_fn, files_fn = _dispatch(lang)
    raw_lines = src.splitlines()

    files = files_fn(raw_lines)

    # Agrupar en parrafos/procedures. Lo previo al primer label va a 'init'.
    paragraphs = []  # (nombre, [ops])
    current = "init"
    cur_ops = []
    for line in raw_lines:
        label = para_fn(line)
        if label:
            paragraphs.append((current, cur_ops))
            current = label
            cur_ops = []
            continue
        cur_ops.extend(stmt_fn(line, lang))
    paragraphs.append((current, cur_ops))

    # Dedup de nombres (COBOL/ALGOL pueden repetir labels raramente): sufijo _N.
    # Prefijo 'p_' si empieza con digito (no es identificador Python valido).
    seen = {}
    uniq = []
    for name, ops in paragraphs:
        if name[:1].isdigit():
            name = "p_" + name
        n = name
        if n in seen:
            seen[n] += 1
            n = f"{name}_{seen[name]}"
        else:
            seen[n] = 0
        uniq.append((n, ops))

    # Generar funciones.
    func_blocks = []
    stats = {"paragraphs": 0, "assigns": 0, "ifs": 0, "calls": 0}
    for name, ops in uniq:
        if not ops:
            continue
        stats["paragraphs"] += 1
        for op, _ in ops:
            if op == "assign":
                stats["assigns"] += 1
            elif op in ("if", "while"):
                stats["ifs"] += 1
            elif op in ("call", "loop_until"):
                stats["calls"] += 1
        body = _emit_body(ops)
        func_blocks.append(f"def {name}(ctx):\n" + "\n".join(body) + "\n")

    # Lecturas de archivos de entrada (datasets).
    src_lines = []
    for f in files:
        src_lines.append(
            f'    ctx["df_{f}"] = (spark.read.option("header", True)'
            f'.csv(f"{{PARAMS.BASE_PATH}}/{f}.csv"))')
    if not src_lines:
        src_lines.append("    # (el programa no declara archivos de entrada explicitos)")

    # Llamadas en orden (el flujo principal).
    call_lines = []
    for name, ops in uniq:
        if ops and name != "init":
            call_lines.append(f"    {name}(ctx)")
    if not call_lines:
        call_lines.append("    pass")

    app = f"BNX_{lang.upper()}_Direct"
    title = f"BNX JOB — traduccion directa {lang.upper()} -> PySpark"
    header = HEADER.format(title=title, lang=lang.upper(),
                           ts=datetime.now().isoformat(timespec="seconds"), app=app)
    footer = FOOTER.format(sources="\n".join(src_lines),
                           calls="\n".join(call_lines), lang=lang.upper())
    code = header + "\n\n" + "\n\n".join(func_blocks) + "\n" + footer
    stats["lines"] = code.count("\n") + 1
    stats["files"] = len(files)
    return {"code": code, "stats": stats}
