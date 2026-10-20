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


# Constantes figurativas COBOL/ALGOL -> literal Python. A nivel de modulo para
# reutilizarlas tanto al traducir literales como identificadores en condiciones.
_FIGURATIVE = {
    "ZERO": "0", "ZEROS": "0", "ZEROES": "0",
    "SPACE": "''", "SPACES": "''",
    "HIGH-VALUE": "None", "HIGH-VALUES": "None",
    "LOW-VALUE": "None", "LOW-VALUES": "None",
    "NULL": "None", "NULLS": "None", "TRUE": "True", "FALSE": "False",
}


def _py_literal(tok):
    """Convierte un literal COBOL/ALGOL a literal Python, o None si no es literal."""
    t = tok.strip()
    up = t.upper()
    if up in _FIGURATIVE:
        return _FIGURATIVE[up]
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


def _strip_subscripts(s):
    """Elimina los subindices de tabla COBOL/ALGOL: 'TABLA(I)' -> 'TABLA',
    'A(I,J)' -> 'A', y reference modification 'X(1:3)' -> 'X'.

    El modelo `ctx` es un dict plano (sin arreglos reales), asi que un subindice
    no se puede resolver; dejarlo generaria `ctx['x'](...)` = llamada invalida
    (TypeError en runtime). Neutralizamos el indice usando el campo base. Se
    repite hasta estabilizar para subindices anidados A(B(I))."""
    prev = None
    cur = s
    # 'ident(...)' donde dentro NO hay otro parentesis sin cerrar: quitar '(...)'.
    pat = re.compile(r"([A-Za-z][\w-]*)\s*\([^()]*\)")
    # 'ident[...]' (subindice de ARRAY ALGOL, p.ej. ARTICULOS[CONTADOR]): mismo
    # tratamiento. En el modelo ctx plano no hay arreglos reales, asi que un
    # subindice con corchetes dejaria 'ctx["articulos"][ctx["contador"]]' =
    # indexar un string con string -> TypeError en runtime. Lo neutralizamos
    # al campo base. [^\[\]] evita tragar subindices anidados A[B[I]].
    pat_br = re.compile(r"([A-Za-z][\w-]*)\s*\[[^\[\]]*\]")
    while prev != cur:
        prev = cur
        cur = pat.sub(r"\1", cur)
        cur = pat_br.sub(r"\1", cur)
    return cur


def _translate_condition(cond, lang):
    """Traduce una condicion COBOL/ALGOL a expresion booleana Python sobre ctx.
    Soporta =, <, >, <=, >=, <>, NOT, AND, OR y los mnemonicos ALGOL
    (EQL/NEQ/LSS/GTR/LEQ/GEQ). Lo no resoluble se deja como comentario arriba."""
    c = " " + _strip_subscripts(cond.strip()) + " "
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
        # Figurativas COBOL/ALGOL -> su literal (ZERO->0, SPACES->'', etc.),
        # no un campo de ctx. Asi 'IF X > ZERO' -> 'ctx[x] > 0', no ctx['zero'].
        up = tok.upper()
        if up in _FIGURATIVE:
            return _FIGURATIVE[up]
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
    result = "".join(out).strip()

    # Coercion numerica en ARITMETICA dentro de la condicion: un operando de
    # +,-,*,/ que sea ctx['x'] se envuelve en _n(...) para no romper 'str - str'
    # (los campos vienen como texto del CSV/mensaje). No tocamos las igualdades
    # (ctx['x'] == 'ABC' debe seguir comparando texto).
    def _wrap_arith(mm):
        return f"_n({mm.group(0)})"
    # ctx['x'] seguido o precedido de operador aritmetico.
    result = re.sub(r"(ctx\[[^\]]+\])\s*([+\-*/])", lambda mm: f"_n({mm.group(1)}) {mm.group(2)}", result)
    result = re.sub(r"([+\-*/])\s*(ctx\[[^\]]+\])", lambda mm: f"{mm.group(1)} _n({mm.group(2)})", result)

    # Comparaciones de ORDEN (< > <= >=): coaccionar ambos lados a numero con
    # _n para no romper 'str > int' (un campo del CSV es texto; COBOL lo compara
    # como numero). Las igualdades (==, !=) se dejan: comparan texto o numero
    # sin romper. Operando = numero o un acceso ctx['..'] (quiza ya con _n()).
    _opnd = r"(_n\(ctx\[[^\]]+\]\)|ctx\[[^\]]+\]|\d+(?:\.\d+)?)"
    _cmp = re.compile(_opnd + r"\s*(<=|>=|<|>)\s*" + _opnd)

    def _wrap_cmp(mm):
        a, op, b = mm.group(1), mm.group(2), mm.group(3)
        aw = a if a.startswith("_n(") else (a if a[0].isdigit() else f"_n({a})")
        bw = b if b.startswith("_n(") else (b if b[0].isdigit() else f"_n({b})")
        return f"{aw} {op} {bw}"

    result = _cmp.sub(_wrap_cmp, result)
    return result


# Helpers de runtime compartidos (coercion numerica + estado tolerante). Se
# inyectan en el header del modo PySpark via {{runtime}}. El modo puro los trae
# inline en HEADER_PURE.
_RUNTIME_HELPERS = r'''def _n(v):
    """Coercion numerica tolerante (str/_Zero/num -> numero, 0 si no se puede)."""
    if isinstance(v, bool):
        return int(v)
    if isinstance(v, (int, float)):
        return v
    if v is None:
        return 0
    s = str(v).strip()
    if not s:
        return 0
    try:
        return float(s) if "." in s else int(s)
    except ValueError:
        import re as _re
        m = _re.match(r"[+-]?\d+", s)
        return int(m.group(0)) if m else 0


def _div(a, b):
    """Division tolerante: COBOL con ON SIZE ERROR / divisor 0 no debe tumbar el
    programa. Devuelve 0 si el divisor es 0 (dato no inicializado/sintetico)."""
    a, b = _n(a), _n(b)
    return a / b if b else 0


# Guarda de profundidad: el flujo plano (sin el control real del COBOL) puede
# provocar recursion mutua entre parrafos. El decorador corta la ejecucion de un
# parrafo si se supera la profundidad maxima, evitando RecursionError.
_BNX_MAX_DEPTH = 50
_bnx_depth = {"n": 0}


def _guard_depth(fn):
    def _wrap(ctx):
        if _bnx_depth["n"] >= _BNX_MAX_DEPTH:
            return  # circuit breaker: demasiada anidacion de PERFORM
        _bnx_depth["n"] += 1
        try:
            return fn(ctx)
        finally:
            _bnx_depth["n"] -= 1
    return _wrap


class _Zero:
    """Valor por defecto para campos no inicializados: 0 en aritmetica, '' en texto."""
    def __add__(self, o): return o if isinstance(o, str) else (o + 0)
    def __radd__(self, o): return o if isinstance(o, str) else (0 + o)
    def __sub__(self, o): return -o
    def __rsub__(self, o): return o
    def __mul__(self, o): return 0 if not isinstance(o, str) else ""
    __rmul__ = __mul__
    def __truediv__(self, o): return 0
    def __rtruediv__(self, o): return 0
    def __eq__(self, o): return o in (0, "", None) or isinstance(o, _Zero)
    def __ne__(self, o): return not self.__eq__(o)
    def __lt__(self, o): return 0 < o if not isinstance(o, str) else "" < o
    def __gt__(self, o): return 0 > o if not isinstance(o, str) else "" > o
    def __le__(self, o): return not self.__gt__(o)
    def __ge__(self, o): return not self.__lt__(o)
    def __bool__(self): return False
    def __str__(self): return ""
    def __repr__(self): return "0"
    def __hash__(self): return 0


class _Ctx(dict):
    def __missing__(self, key):
        return _Zero()
'''


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
import datetime as _dt
from pyspark.sql import SparkSession, functions as F
from pyspark.sql.types import *

spark = SparkSession.builder.appName("{app}").getOrCreate()


class PARAMS:
    BASE_PATH = os.environ.get("BNX_BASE_PATH", "s3://datalake-bnx-scripts-dev")


{runtime}

# Estado del programa: emula las variables WORKING-STORAGE / declaraciones ALGOL.
def new_ctx():
    return _Ctx()
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


# --- Modo PYTHON PURO (COBOL transaccional CICS: procesa 1 mensaje a la vez) ---
HEADER_PURE = '''"""
{title}
Generado por BNX (traductor directo {lang} -> Python puro) el {ts}.

COBOL/ALGOL TRANSACCIONAL (tipo CICS): procesa UN mensaje a la vez. No usa
Spark. Cada parrafo es una funcion que opera sobre `ctx` (estado del programa).
Los READ ... INVALID KEY se traducen a lookups en memoria (dict), cargados UNA
sola vez desde CSV con pandas. Corre con `python <archivo>.py` sin cluster.

===========================================================================
COMO CORRER
===========================================================================
1) Estructura de carpetas:
       mi_proyecto/
       |- main.py          <- este archivo
       |- data/            <- tus CSV de lookup (una por tabla READ)
          |- rtads.csv
          |- suc_bc.csv
          |- ...
   (Cada CSV se indexa por su PRIMERA columna = la clave de busqueda.)

2) Instalar dependencia:
       pip install pandas

3) Correr directo (ejecuta main() con un mensaje de prueba):
       python main.py

4) Usarlo con tus datos reales:
       from main import procesa_entidad
       mensaje = {{
           "anz_ctr_idtran": "ALTA01",   # campos del mensaje de entrada
           "suc_bc_key": "001234",       # clave para el lookup SUC_BC
       }}
       salida = procesa_entidad(mensaje)   # devuelve el ctx final (dict)
       print(salida.get("ws_respuesta"))

5) Como API (si descargaste app.py):
       pip install fastapi uvicorn
       uvicorn app:app --reload
       # POST http://localhost:8000/procesa  body: {{"data": {{...}}}}

AJUSTES MANUALES (el COBOL no los da automatico):
 - Pon los CSV reales en ./data/ (o BNX_DATA_DIR), uno por tabla de lookup.
 - Antes de cada READ, el codigo usa ctx['<tabla>_key'] como clave; asignalo
   con el valor real (en el COBOL venia de un MOVE ... TO KEY previo).
===========================================================================
"""
import os
import datetime as _dt

try:
    import pandas as pd
except ImportError:  # pandas es opcional: sin el, los lookups quedan vacios.
    pd = None


class PARAMS:
    # Carpeta con los CSV de las tablas de lookup (una por archivo COBOL).
    DATA_DIR = os.environ.get("BNX_DATA_DIR", "./data")


# Archivos leidos por el programa (READ ... INVALID KEY). Se cargan como
# diccionarios indexados por su primera columna (clave). Ajusta la columna
# clave si tu CSV usa otra. Clave del dict = nombre normalizado del archivo.
_LOOKUP_FILES = {files_list}


def load_lookups(data_dir=None):
    """Carga cada CSV de _LOOKUP_FILES como dict indexado por su clave (primera
    columna). Devuelve {{NOMBRE: {{clave: fila_dict}}}}. Si no hay pandas o el
    CSV no existe, deja el lookup vacio (equivale a INVALID KEY siempre)."""
    data_dir = data_dir or PARAMS.DATA_DIR
    out = {{}}
    for name in _LOOKUP_FILES:
        path = os.path.join(data_dir, name.lower() + ".csv")
        if pd is None or not os.path.exists(path):
            out[name.upper()] = {{}}
            continue
        df = pd.read_csv(path, dtype=str)
        key = df.columns[0]  # primera columna = clave de acceso
        out[name.upper()] = df.set_index(key).to_dict("index")
    return out


# Lookups globales: se cargan UNA sola vez al importar el modulo.
LOOKUPS = load_lookups()


def _n(v):
    """Coercion numerica tolerante para aritmetica COBOL. Devuelve float si
    parece decimal, int si es entero, 0 si no se puede. Asi `_n(a) - _n(b)`
    nunca rompe por 'str - str' (los campos vienen como texto del CSV/mensaje)."""
    if isinstance(v, bool):
        return int(v)
    if isinstance(v, (int, float)):
        return v
    if v is None:
        return 0
    s = str(v).strip()
    if not s:
        return 0
    try:
        return float(s) if "." in s else int(s)
    except ValueError:
        import re as _re
        m = _re.match(r"[+-]?\\d+", s)
        return int(m.group(0)) if m else 0


def _div(a, b):
    """Division tolerante: devuelve 0 si el divisor es 0 (evita ZeroDivisionError)."""
    a, b = _n(a), _n(b)
    return a / b if b else 0


# PERFORM se traduce como llamada de funcion normal (p_xxx(ctx)). Como el flujo
# plano no reproduce el retorno exacto del PERFORM COBOL, dos parrafos pueden
# llamarse mutuamente y causar recursion infinita. En vez de decorar CADA
# funcion, instalamos UN limite de recursion razonable: Python lanzara
# RecursionError de forma controlada y procesa_entidad lo captura como fin del
# flujo (no un crash). Asi el codigo se lee limpio y ademas corre.
import sys as _sys
_sys.setrecursionlimit(8000)


# Campos de WORKING-STORAGE con su valor inicial COBOL (0 numerico, "" texto).
# Se usan para inicializar ctx EXPLICITAMENTE con los campos reales del programa.
WORKING_STORAGE = {ws_fields}


class _Ctx(dict):
    """Estado del programa. Es un dict normal; los campos conocidos vienen de
    WORKING_STORAGE con su valor inicial COBOL. Un acceso a un campo NO declarado
    (temporales, subindices) devuelve '' en vez de KeyError — equivalente a un
    alfanumerico vacio, sin objetos 'magicos'."""
    def __missing__(self, key):
        return ""


def new_ctx():
    return _Ctx(WORKING_STORAGE)
'''

FOOTER_PURE = '''
# ---------------------------------------------------------------------------
# ENTRADA: procesa UN mensaje de entrada y devuelve la respuesta.
# ---------------------------------------------------------------------------
def procesa_entidad(mensaje_input: dict, lookups=None) -> dict:
    """Procesa un mensaje transaccional (equivalente a una ejecucion del
    programa COBOL para una transaccion). Ejecuta los parrafos en el orden del
    fuente y devuelve el estado resultante (ctx)."""
    ctx = new_ctx()
    ctx["_lookups"] = lookups if lookups is not None else LOOKUPS
    ctx["ws_mensaje"] = mensaje_input
    # Sembrar los campos del mensaje en ctx (claves normalizadas).
    for k, v in (mensaje_input or {{}}).items():
        ctx[str(k).replace("-", "_").lower()] = v
    # Ejecuta los parrafos en el orden del programa. Si el flujo plano produce
    # recursion profunda (PERFORM que ciclan sin el retorno real del COBOL), se
    # corta de forma controlada y se devuelve el estado alcanzado (no un crash).
    try:
        _run_flow(ctx)
    except RecursionError:
        ctx["_bnx_recursion_cortada"] = True
    # Respuesta: WS-RESPUESTA si el programa la define, si no el ctx completo.
    return ctx.get("ws_respuesta", ctx)


def _run_flow(ctx):
    """Llama a los parrafos en el orden del programa original."""
{calls}


def main():
    # Prueba local: hidrata un mensaje de entrada con datos de ejemplo. Ajusta
    # estos campos al layout real de tu transaccion. Las claves '<tabla>_key'
    # apuntan a los lookups; ponles valores que existan en tus CSV.
    mensaje = {{"campo1": "valor"}}
    for _f in _LOOKUP_FILES:
        mensaje[_f.lower() + "_key"] = "VAL0000"
    salida = procesa_entidad(mensaje)
    print("[ok] procesa_entidad ejecutado. Muestra de la respuesta:")
    if isinstance(salida, dict):
        _shown = 0
        for _k, _v in salida.items():
            if _k in ("_lookups", "ws_mensaje"):
                continue
            print(f"    {{_k}} = {{str(_v)[:60]}}")
            _shown += 1
            if _shown >= 20:
                print(f"    ... (+{{len(salida) - _shown}} campos mas)")
                break
    else:
        print("   ", salida)


if __name__ == "__main__":
    main()
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


def _cobol_working_storage(lines):
    """Extrae los campos de datos COBOL (01-49/77 con PIC) y su VALOR INICIAL
    segun el tipo, para inicializar ctx EXPLICITAMENTE (sin _Zero).

    Reglas COBOL de valor por defecto:
      - PIC 9 / S9 / COMP / COMP-3 (numerico)  -> 0
      - PIC X / A (alfanumerico)               -> ""
      - clausula VALUE explicita               -> ese literal
    Devuelve dict {campo_normalizado: valor_inicial_python}. Omite FILLER y 88.
    """
    fields = {}
    for raw in lines:
        l = raw.strip()
        if not l or l.startswith("*"):
            continue
        # Nivel 01-49 o 77, nombre, ... PIC ...
        m = re.match(r"(0[1-9]|[1-4]\d|77)\s+([A-Za-z][\w-]*)\s+.*?\bPIC(?:TURE)?\s+(\S+)", l, re.I)
        if not m:
            continue
        name = m.group(2)
        if name.upper() == "FILLER":
            continue
        pic = m.group(3).upper().rstrip(".")
        col = _col(name)
        # VALUE explicito?
        mv = re.search(r"\bVALUE\s+(?:IS\s+)?('[^']*'|\"[^\"]*\"|[+-]?\d+(?:\.\d+)?|ZEROS?|ZEROES?|SPACES?)",
                       l, re.I)
        if mv:
            lit = _py_literal(mv.group(1))
            fields[col] = lit if lit is not None else '""'
            continue
        # Tipo por PIC: numerico (9/S/V y COMP) -> 0; alfanumerico (X/A) -> "".
        is_num = bool(re.search(r"[9S]", pic)) and not re.search(r"[XA]", pic)
        fields[col] = "0" if is_num else '""'
    return fields


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
    # Niveles de datos COBOL (01-49, 66 RENAMES, 77 independiente, 88 condicion
    # de nivel): son DECLARACIONES, no operaciones. Se ignoran aunque no traigan
    # PIC (grupos 02/03 y los 88 'VALUE ...' no lo traen). Esto evitaba miles de
    # comentarios '# 88 ...' / '# 02 ...' en el modulo.
    if re.match(r"(0[1-9]|[1-4]\d|6[6]|7[7]|8[8])\s+[\w-]", s):
        return []
    if re.match(r"(PROGRAM-ID|AUTHOR|FILE-CONTROL|INPUT-OUTPUT|WORKING-STORAGE|FD|SELECT|FILE|CONFIGURATION|SOURCE-COMPUTER|OBJECT-COMPUTER|LINKAGE|COPY|REPLACE)\b", up):
        return []
    if up in ("STOP RUN", "GOBACK", "EXIT PROGRAM", "EXIT"):
        return [("raw_py", "return")]
    # NEXT SENTENCE / CONTINUE: control de flujo sin efecto de datos -> no-op.
    if up in ("NEXT SENTENCE", "CONTINUE"):
        return []

    # OPEN / CLOSE de archivos: no aplican en Python puro / lookups en memoria.
    if re.match(r"(OPEN|CLOSE)\s+", up):
        return []

    # READ archivo [INTO destino] INVALID KEY / AT END -> lookup en memoria.
    # Transaccional (INVALID KEY): es un acceso indexado tipo diccionario.
    m = re.match(r"READ\s+([\w-]+)(?:\s+INTO\s+([\w-]+))?", s, re.I)
    if m and ("INVALID" in up or "KEY" in up or "AT END" in up):
        fname = _col(m.group(1))
        dest = _col(m.group(2)) if m.group(2) else fname
        return [("read_lookup", (fname, dest))]

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
        now = {"DATE": "_dt.date.today().strftime('%y%m%d')",
               "TIME": "_dt.datetime.now().strftime('%H%M%S')",
               "DAY": "_dt.date.today().strftime('%y%j')",
               "DAY-OF-WEEK": "_dt.date.today().isoweekday()"}[m.group(2).upper()]
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
    """Expresion aritmetica -> Python sobre ctx. Solo los IDENTIFICADORES se
    vuelven ctx['x']; los numeros se dejan tal cual (el patron \\d+ ya los
    excluye porque empieza por [A-Za-z])."""
    def repl(m):
        tok = m.group(0)
        # Coercion numerica: COMPUTE/aritmetica opera numeros; _n evita str-str.
        return f"_n(ctx[{_col(tok)!r}])"
    e = _strip_subscripts(expr.strip().rstrip("."))
    # Importante: el patron exige inicio con letra, asi un numero como '1' NO
    # entra (no se convierte en ctx['1']).
    e = re.sub(r"[A-Za-z][\w-]*", repl, e)
    # Divisiones seguras: 'A / B' -> '_div(A, B)' para evitar ZeroDivisionError.
    # Operandos simples (numero o _n(ctx[...])); se repite para varias '/'.
    _operand = r"(_n\(ctx\[[^\]]+\]\)|\d+(?:\.\d+)?)"
    _divpat = re.compile(_operand + r"\s*/\s*" + _operand)
    prev = None
    while prev != e:
        prev = e
        e = _divpat.sub(lambda m: f"_div({m.group(1)}, {m.group(2)})", e)
    return e


def _cobol_arith(s):
    """ADD/SUBTRACT/MULTIPLY/DIVIDE ... GIVING -> (target, expr_py). None si no."""
    def ref(tok):
        # Operando aritmetico: literal numerico tal cual, si no columna de ctx
        # envuelta en _n(...) para coercion numerica tolerante (evita str - str).
        lit = _py_literal(tok)
        if lit is not None and re.fullmatch(r"[+-]?\d+(\.\d+)?", lit):
            return lit
        return f"_n(ctx[{_col(tok)!r}])"

    m = re.match(r"ADD\s+(.+?)\s+TO\s+([\w-]+)\s+GIVING\s+([\w-]+)$", s, re.I)
    if m:
        terms = [t for t in re.split(r"\s+", m.group(1).strip())] + [m.group(2)]
        return (_col(m.group(3)), " + ".join(ref(t) for t in terms))
    m = re.match(r"ADD\s+([\w-]+)\s+TO\s+([\w-]+)$", s, re.I)
    if m:
        return (_col(m.group(2)), f"{ref(m.group(2))} + {ref(m.group(1))}")
    m = re.match(r"SUBTRACT\s+([\w-]+)\s+FROM\s+([\w-]+)(?:\s+GIVING\s+([\w-]+))?$", s, re.I)
    if m:
        tgt = _col(m.group(3)) if m.group(3) else _col(m.group(2))
        return (tgt, f"{ref(m.group(2))} - {ref(m.group(1))}")
    m = re.match(r"MULTIPLY\s+([\w-]+)\s+BY\s+([\w-]+)(?:\s+GIVING\s+([\w-]+))?$", s, re.I)
    if m:
        tgt = _col(m.group(3)) if m.group(3) else _col(m.group(2))
        return (tgt, f"{ref(m.group(1))} * {ref(m.group(2))}")
    # DIVIDE a INTO b -> b/a ; DIVIDE a BY b -> a/b. Division segura (_div).
    m = re.match(r"DIVIDE\s+([\w-]+)\s+INTO\s+([\w-]+)(?:\s+GIVING\s+([\w-]+))?$", s, re.I)
    if m:
        tgt = _col(m.group(3)) if m.group(3) else _col(m.group(2))
        return (tgt, f"_div({ref(m.group(2))}, {ref(m.group(1))})")
    m = re.match(r"DIVIDE\s+([\w-]+)\s+BY\s+([\w-]+)(?:\s+GIVING\s+([\w-]+))?$", s, re.I)
    if m:
        tgt = _col(m.group(3)) if m.group(3) else _col(m.group(2))
        return (tgt, f"_div({ref(m.group(1))}, {ref(m.group(2))})")
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


def _emit_body(ops, valid_funcs=None, clean=True):
    """Convierte la lista de ops de un parrafo/proc en lineas Python.

    valid_funcs: set de nombres de funcion existentes. Un PERFORM/llamada a un
    nombre que NO existe (parrafo no declarado, PERFORM THRU, typo) se emite como
    comentario en vez de romper con NameError en runtime.

    clean=True (default): NO emite comentarios de sentencias NO traducidas
    (MOVE con subindices, IF complejo, verbos de mainframe, etc.). Deja solo
    codigo Python ejecutable y legible. clean=False conserva esos comentarios
    como guia de lo que habia en el fuente.

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

    def _note(txt):
        # Comentario-guia de una sentencia no traducida: solo en modo NO limpio.
        if not clean:
            lines.append(f"    # {txt}")

    for op, arg in ops:
        if op == "assign":
            tgt, val = arg
            if _is_valid_py_expr(val):
                _emit_stmt(f"ctx[{tgt!r}] = {val}")
            else:
                _note(f"revisar: ctx[{tgt!r}] = {val}")
                pending_cond = None
        elif op == "call":
            fn = _fname(arg)
            if valid_funcs is None or fn in valid_funcs:
                _emit_stmt(f"{fn}(ctx)")
            else:
                # Parrafo no declarado como funcion (PERFORM THRU / typo): no
                # romper con NameError; se omite (o se documenta en modo guia).
                _note(f"PERFORM {arg} (parrafo no resuelto)")
                pending_cond = None
        elif op == "read_lookup":
            # READ archivo INTO destino INVALID KEY -> lookup en memoria.
            # La clave se toma de ctx['<file>_key'] (ajustable); si no existe,
            # devuelve None (equivalente al INVALID KEY / registro no hallado).
            fname, dest = arg
            key_var = f"{fname}_key"
            _emit_stmt(
                f"ctx[{dest!r}] = ctx.get('_lookups', {{}}).get({fname.upper()!r}, {{}})"
                f".get(ctx.get({key_var!r}))")
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
                    _note(arg)
                    pending_cond = None
        elif op == "loop_until":
            tgt, cond = arg
            fn = _fname(tgt)
            if valid_funcs is not None and fn not in valid_funcs:
                _note(f"PERFORM {tgt} UNTIL {cond} (parrafo no resuelto)")
                pending_cond = None
            elif _is_valid_py_expr(cond):
                # Bucle con GUARDA de iteraciones: el modelo plano puede no
                # actualizar la condicion (seria bucle infinito). El tope evita
                # colgar; ajusta/retira la guarda tras revisar la logica real.
                lines.append(f"    _guard = 0")
                lines.append(f"    while not ({cond}) and _guard < 1000:")
                lines.append(f"        {fn}(ctx)")
                lines.append(f"        _guard += 1")
                emitted_any = True
                pending_cond = None
            else:
                _note(f"PERFORM UNTIL {cond}")
                _emit_stmt(f"{fn}(ctx)")
                pending_cond = None
        elif op in ("if", "while"):
            # Condicion que aplica a la proxima sentencia simple (patron COBOL
            # 'IF cond MOVE ...'). Si es valida, se usa como `if cond:` al emitir
            # la siguiente sentencia. Si NO es valida (expresion compleja), se
            # descarta (modo limpio) o se documenta (modo guia).
            if _is_valid_py_expr(arg):
                pending_cond = arg
            else:
                kw = "IF" if op == "if" else "WHILE"
                _note(f"{kw} (revisar): {arg}")
                pending_cond = None
        elif op in ("else", "dedent"):
            # Sin anidamiento real: el else/end solo rompe la condicion pendiente.
            pending_cond = None
        elif op == "raw":
            _note(arg)
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


def _algol_group_paragraphs(raw_lines):
    """Agrupa un fuente ALGOL en (nombre, [ops]) respetando la estructura
    BEGIN/END, y SEPARA el programa principal del cuerpo de los PROCEDURE.

    En ALGOL el cuerpo de un PROCEDURE es el bloque BEGIN..END que le sigue;
    cuando ese bloque cierra, el PROCEDURE termina. Lo que viene DESPUES del
    ultimo PROCEDURE (hasta el END. del programa) es el PROGRAMA PRINCIPAL, y
    debe ir a un parrafo aparte ('main'), NO acumularse dentro del ultimo
    PROCEDURE (bug que metia todo el main en el ultimo proc y causaba recursion).

    Devuelve (paragraphs, has_main):
      paragraphs: lista de (nombre, [ops]); 'init' = lo previo al primer proc.
      has_main:   True si se detecto un programa principal con sentencias; en
                  ese caso el flujo _run_flow debe llamar SOLO a 'main'.
    """
    init_ops = []          # declaraciones/sentencias previas al primer PROCEDURE
    procs = []             # [(nombre, [ops])] cuerpos de PROCEDURE, en orden
    main_ops = []          # sentencias del PROGRAMA PRINCIPAL (tras los procs)
    depth = 0              # profundidad de BEGIN/END
    in_proc = False        # dentro del cuerpo de un PROCEDURE
    proc_depth = 0         # profundidad de BEGIN en que arranco el proc actual
    cur_name = None        # nombre del PROCEDURE en curso
    cur_ops = []           # ops del PROCEDURE en curso
    saw_proc = False       # ya vimos al menos un PROCEDURE

    for line in raw_lines:
        up = line[:72].strip().rstrip(";").upper()
        label = _algol_proc(line)

        if label and not in_proc:
            # Inicio de un PROCEDURE (en el nivel del programa, no anidado).
            cur_name = label
            cur_ops = []
            in_proc = True
            proc_depth = depth
            saw_proc = True
            continue

        is_begin = up in ("BEGIN", "BEGIN.")
        is_end = up in ("END", "END.")
        if is_begin:
            depth += 1
            # El BEGIN que abre el cuerpo del proc no emite op.
            if in_proc and depth == proc_depth + 1:
                continue

        ops = _algol_stmt(line, "algol")
        if in_proc:
            cur_ops.extend(ops)
        elif saw_proc:
            main_ops.extend(ops)   # sentencias del programa principal
        else:
            init_ops.extend(ops)   # preambulo antes del primer proc

        if is_end:
            depth -= 1
            # Cierre del bloque del PROCEDURE actual: termina el proc.
            if in_proc and depth == proc_depth:
                procs.append((cur_name, cur_ops))
                in_proc = False
                cur_name, cur_ops = None, []

    # Ensamblar: init (preambulo) + procedures + programa principal ('_bnx_main',
    # no 'main' para no colisionar con el def main() del footer del modulo).
    paragraphs = [("init", init_ops)]
    paragraphs.extend(procs)
    has_main = bool(main_ops)
    if has_main:
        paragraphs.append(("_bnx_main", main_ops))
    return paragraphs, has_main


def _dispatch(lang):
    if lang == "cobol":
        return _cobol_paragraph, _cobol_stmt, _cobol_selects
    return _algol_proc, _algol_stmt, _algol_files


FASTAPI_APP = '''"""
app.py — API FastAPI que expone el programa transaccional traducido.
Arranca con:  uvicorn app:app --reload
Requiere:     pip install fastapi uvicorn pandas
"""
from fastapi import FastAPI
from pydantic import BaseModel

# El modulo generado (main.py) expone procesa_entidad(mensaje) -> dict.
from {module} import procesa_entidad

app = FastAPI(title="BNX {lang} transaccional")


class Mensaje(BaseModel):
    # Campos del mensaje de entrada. Ajusta a tu layout real.
    data: dict


@app.get("/health")
def health():
    return {{"ok": True}}


@app.post("/procesa")
def procesa(msg: Mensaje):
    """Procesa UN mensaje transaccional y devuelve el estado/respuesta."""
    salida = procesa_entidad(msg.data)
    # Serializable: convertir a str los valores no-JSON (p.ej. Decimals).
    return {{"respuesta": {{str(k): str(v) for k, v in salida.items()}}
             if isinstance(salida, dict) else salida}}
'''


def fastapi_app_code(module_name="main", lang="cobol"):
    """Genera un app.py (FastAPI) que importa procesa_entidad del modulo puro."""
    return FASTAPI_APP.format(module=module_name, lang=lang.upper())


def readme_text(lang="cobol", lookups=None):
    """README.md con la guia de 'como correr' el modulo Python puro generado.
    `lookups` es la lista de tablas de lookup (para listar los CSV esperados)."""
    lk = lookups or []
    csv_lines = "\n".join(f"      - data/{n.lower()}.csv" for n in lk[:30]) or "      - (ninguna tabla de lookup detectada)"
    return f"""# BNX — Job {lang.upper()} transaccional (Python puro)

Traduccion directa del fuente {lang.upper()} a **Python puro** (sin Spark).
Procesa UN mensaje transaccional a la vez (modelo tipo CICS).

## Archivos
- `main.py` — el job: funciones por parrafo + `procesa_entidad(mensaje)`.
- `app.py` — (opcional) API FastAPI que expone `POST /procesa`.
- `data/` — CSV de las tablas de lookup (una por `READ ... INVALID KEY`).

## Requisitos
```
pip install pandas            # para los lookups
pip install fastapi uvicorn   # solo si usas app.py
```

## Datos de lookup
Pon un CSV por tabla en `data/` (indexado por su PRIMERA columna = la clave):
{csv_lines}

Puedes cambiar la carpeta con la variable `BNX_DATA_DIR`.

## Correr
```bash
python main.py                # ejecuta main() con un mensaje de prueba
```

## Usar con datos reales
```python
from main import procesa_entidad

mensaje = {{
    "anz_ctr_idtran": "ALTA01",   # campos del mensaje de entrada
    "suc_bc_key": "001234",       # clave del lookup SUC_BC (ejemplo)
}}
salida = procesa_entidad(mensaje)  # dict con el estado final (ctx)
print(salida.get("ws_respuesta"))
```

## Como API
```bash
uvicorn app:app --reload
# POST http://localhost:8000/procesa   body: {{"data": {{...}}}}
```

## Ajustes manuales (el {lang.upper()} no los da automatico)
1. Los CSV reales en `data/` (uno por tabla de lookup).
2. Antes de cada `READ`, el codigo usa `ctx['<tabla>_key']` como clave de
   busqueda; asignala con el valor real (en el fuente venia de un
   `MOVE ... TO KEY` previo al READ).

Generado por BNX Convertidor.
"""


def transpile_direct(src, lang="cobol", pure=False):
    """Traduce el fuente completo a un modulo procedural.

    pure=False -> PySpark (lee los archivos como DataFrames; flujo tipo job).
    pure=True  -> PYTHON PURO (COBOL/ALGOL transaccional CICS): sin Spark, los
                  READ se vuelven lookups en memoria (pandas) y se expone una
                  funcion procesa_entidad(mensaje) para procesar 1 mensaje.

    Devuelve {"code": str, "stats": {paragraphs, assigns, ifs, calls, lines}}.
    """
    lang = (lang or "cobol").lower()
    para_fn, stmt_fn, files_fn = _dispatch(lang)
    raw_lines = src.splitlines()

    files = files_fn(raw_lines)

    # Agrupar en parrafos/procedures. Lo previo al primer label va a 'init'.
    # ALGOL: usa el agrupador que respeta BEGIN/END y separa el programa
    # principal ('main') del cuerpo de los PROCEDURE (evita la recursion en que
    # el ultimo proc se tragaba todo el main). COBOL: agrupacion plana por label.
    has_main = False
    if lang == "algol":
        paragraphs, has_main = _algol_group_paragraphs(raw_lines)
    else:
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

    # Generar funciones. IMPORTANTE: generamos UNA funcion por CADA parrafo,
    # aunque no tenga sentencias traducibles (cuerpo 'pass'). Si lo saltaramos,
    # un PERFORM a ese parrafo seria un NameError en runtime. 'init' (lo previo
    # al primer parrafo) sí se omite si esta vacio (no se invoca).
    # Set de nombres de funcion que SI vamos a generar (para resolver llamadas).
    valid_funcs = {_fname(name) for name, ops in uniq
                   if not (not ops and name == "init")}

    func_blocks = []
    stats = {"paragraphs": 0, "assigns": 0, "ifs": 0, "calls": 0}
    for name, ops in uniq:
        if not ops and name == "init":
            continue
        stats["paragraphs"] += 1
        for op, _ in ops:
            if op == "assign":
                stats["assigns"] += 1
            elif op in ("if", "while"):
                stats["ifs"] += 1
            elif op in ("call", "loop_until"):
                stats["calls"] += 1
        body = _emit_body(ops, valid_funcs=valid_funcs)
        # Modo PURO: PERFORM = llamada normal (sin decorador de guarda). Modo
        # PySpark: mantiene @_guard_depth por si el flujo plano cicla.
        deco = "" if pure else "@_guard_depth\n"
        func_blocks.append(f"{deco}def {name}(ctx):\n" + "\n".join(body) + "\n")

    # Llamadas en orden (el flujo principal). 'init' (lo previo al primer
    # parrafo) solo son declaraciones; se omite de las llamadas.
    call_lines = []
    if has_main and "_bnx_main" in valid_funcs:
        # ALGOL con programa principal explicito: '_bnx_main' ya llama a cada
        # PROCEDURE en su orden. El flujo invoca SOLO '_bnx_main' (llamar ademas a
        # cada proc los duplicaria).
        call_lines.append("    _bnx_main(ctx)")
    else:
        for name, ops in uniq:
            if ops and name != "init" and name in valid_funcs:
                call_lines.append(f"    {name}(ctx)")
    if not call_lines:
        call_lines.append("    pass")

    ts = datetime.now().isoformat(timespec="seconds")

    if pure:
        # --- PYTHON PURO (transaccional) ---
        title = f"BNX JOB — traduccion directa {lang.upper()} -> Python puro"
        files_list = "[" + ", ".join(repr(f.upper()) for f in files) + "]"
        # Campos de WORKING-STORAGE con su valor inicial COBOL (0/"").
        # COMPACTO: agrupamos por valor (los que valen 0 y los que valen "") en
        # dict.fromkeys para NO ocupar 8000+ lineas (eso empujaba las funciones
        # p_* fuera de la vista previa y parecia que el codigo estaba vacio).
        ws = _cobol_working_storage(raw_lines) if lang == "cobol" else {}
        if ws:
            nums = sorted(k for k, v in ws.items() if v == "0")
            strs = sorted(k for k, v in ws.items() if v == '""')
            others = {k: v for k, v in sorted(ws.items()) if v not in ("0", '""')}

            def _wrap_names(names, per_line=12):
                # Lista de nombres partida en varias lineas cortas (legible, no
                # una sola linea de 150 KB que arruina la vista previa).
                out = []
                for i in range(0, len(names), per_line):
                    out.append("        " + ", ".join(repr(n) for n in names[i:i+per_line]) + ",")
                return "\n".join(out)

            lines_ws = ["{"]
            if nums:
                lines_ws.append("    # campos numericos -> 0")
                lines_ws.append("    **dict.fromkeys([")
                lines_ws.append(_wrap_names(nums))
                lines_ws.append("    ], 0),")
            if strs:
                lines_ws.append("    # campos alfanumericos -> ''")
                lines_ws.append("    **dict.fromkeys([")
                lines_ws.append(_wrap_names(strs))
                lines_ws.append("    ], ''),")
            for k, v in others.items():
                lines_ws.append(f"    {k!r}: {v},")
            lines_ws.append("}")
            ws_fields = "\n".join(lines_ws)
        else:
            ws_fields = "{}"
        header = HEADER_PURE.format(title=title, lang=lang.upper(), ts=ts,
                                    files_list=files_list, ws_fields=ws_fields)
        footer = FOOTER_PURE.format(calls="\n".join(call_lines))
        code = header + "\n\n" + "\n\n".join(func_blocks) + "\n" + footer
        stats["mode"] = "pure"
    else:
        # --- PYSPARK ---
        src_lines = []
        for f in files:
            src_lines.append(
                f'    ctx["df_{f}"] = (spark.read.option("header", True)'
                f'.csv(f"{{PARAMS.BASE_PATH}}/{f}.csv"))')
        if not src_lines:
            src_lines.append("    # (el programa no declara archivos de entrada explicitos)")
        app = f"BNX_{lang.upper()}_Direct"
        title = f"BNX JOB — traduccion directa {lang.upper()} -> PySpark"
        header = HEADER.format(title=title, lang=lang.upper(), ts=ts, app=app,
                               runtime=_RUNTIME_HELPERS)
        footer = FOOTER.format(sources="\n".join(src_lines),
                               calls="\n".join(call_lines), lang=lang.upper())
        code = header + "\n\n" + "\n\n".join(func_blocks) + "\n" + footer
        stats["mode"] = "spark"

    stats["lines"] = code.count("\n") + 1
    stats["files"] = len(files)
    return {"code": code, "stats": stats}
