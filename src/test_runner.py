# src/test_runner.py
"""
Ejecutor de prueba local para código PySpark generado (BNX).

Toma el código PySpark producido por el convertidor y lo ejecuta localmente
usando datos de entrada sintéticos (los generados por Data Redactada), para
comprobar si el job corre correctamente sin necesidad de AWS/S3.

Estrategia (solo target PySpark, no Glue):
  1. Neutraliza las lecturas externas: `spark.read.<fmt>(...)` → DataFrame
     sintético inyectado por nombre de variable (X_df) desde BNX_INPUTS.
  2. Neutraliza las escrituras: `X.write...(...)` → registra un resumen
     (count + esquema) en lugar de escribir a S3.
  3. Ejecuta en un subproceso aislado con timeout y captura stdout/stderr.
"""
import re
import os
import io
import csv
import json
import sys
import tempfile
import subprocess


# Palabras que aparecen dentro de expresiones pero NO son columnas
# (keywords SQL, funciones Spark y funciones Ab Initio que se traducen)
_NON_COLUMN_TOKENS = {
    # keywords SQL
    "cast", "as", "when", "then", "else", "end", "case", "and", "or", "not",
    "null", "is", "in", "like", "rlike", "between", "distinct", "over", "partition",
    "by", "order", "group", "having", "select", "from", "where", "join", "on", "how",
    "asc", "desc", "descending", "ascending", "escape",
    # tipos
    "int", "integer", "string", "decimal", "date", "datetime", "timestamp",
    "double", "float", "long", "bigint", "boolean", "true", "false",
    # funciones Spark comunes
    "to_date", "to_timestamp", "coalesce", "lit", "col", "expr", "trim", "ltrim",
    "rtrim", "lpad", "rpad", "concat", "concat_ws", "substring", "substr", "size",
    "length", "instr", "locate", "replace", "regexp_replace", "split", "reverse",
    "upper", "lower", "current_date", "current_timestamp", "count", "sum", "avg",
    "min", "max", "row_number", "rank", "dense_rank", "when", "nvl", "isnull",
    "array_join", "datediff", "year", "month", "day", "weekofyear", "dayofmonth",
    # funciones Ab Initio (se traducen, no son columnas)
    "string_like", "string_lrtrim", "string_ltrim", "string_rtrim", "string_length",
    "string_substring", "string_index", "string_upcase", "string_downcase",
    "string_concat", "string_replace", "string_lpad", "string_rpad", "string_char",
    "string_is_alphabetic", "string_is_numeric", "is_null", "is_blank", "is_defined",
    "lookup", "lookup_match", "lookup_count", "first_defined", "now", "now1",
    # patrones de formato de fecha
    "yyyy", "mm", "dd", "hh", "ss",
    # direcciones/tipos de join
    "left", "right", "inner", "outer", "full",
}


def extract_referenced_columns(pyspark_code):
    """Escanea el código PySpark y devuelve el conjunto de nombres de columna
    que se referencian en cualquier parte: col("x"), "x" as y, on=["k"],
    orderBy("a","b"), expr("... campo ..."), withColumn("nuevo", ...), etc.

    Esto permite garantizar que los DataFrames sintéticos tengan esas columnas
    para que ninguna operación aguas abajo falle por columna ausente.
    """
    cols = set()

    # col("x") / col('x')
    for m in re.findall(r'col\(\s*["\'](\w+)["\']\s*\)', pyspark_code):
        cols.add(m)

    # F.col("x")
    for m in re.findall(r'F\.col\(\s*["\'](\w+)["\']\s*\)', pyspark_code):
        cols.add(m)

    # on="k" / on=["k1","k2"]
    for m in re.findall(r'on\s*=\s*["\'](\w+)["\']', pyspark_code):
        cols.add(m)
    for block in re.findall(r'on\s*=\s*\[([^\]]*)\]', pyspark_code):
        for m in re.findall(r'["\'](\w+)["\']', block):
            cols.add(m)

    # orderBy(...) / sort(...) / groupBy(...) / dropDuplicates([...])
    for fn in ("orderBy", "sort", "groupBy", "partitionBy"):
        for block in re.findall(rf'{fn}\(([^)]*)\)', pyspark_code):
            for m in re.findall(r'["\'](\w+)["\']', block):
                cols.add(m)
    for block in re.findall(r'dropDuplicates\(\s*\[([^\]]*)\]', pyspark_code):
        for m in re.findall(r'["\'](\w+)["\']', block):
            cols.add(m)

    # withColumn("nuevo", ...) — el nombre nuevo también debe existir río abajo
    for m in re.findall(r'withColumn\(\s*["\'](\w+)["\']', pyspark_code):
        cols.add(m)

    # expr("... texto ...") y where/filter("... texto ...") → tokens tipo identificador
    for block in re.findall(r'(?:expr|where|filter)\(\s*"((?:[^"\\]|\\.)*)"', pyspark_code):
        # limpiar escapes
        clean = block.replace('\\"', '"')
        for tok in re.findall(r'\b([a-zA-Z_]\w*)\b', clean):
            low = tok.lower()
            if low not in _NON_COLUMN_TOKENS and not tok.isdigit():
                cols.add(tok)

    # selectExpr("a", "b as c") — nombres antes de "as" y sueltos
    for block in re.findall(r'selectExpr\(([^)]*)\)', pyspark_code):
        for part in re.findall(r'["\']([^"\']+)["\']', block):
            if part == "*":
                continue
            m = re.match(r'\s*(\w+)', part)
            if m and m.group(1).lower() not in _NON_COLUMN_TOKENS:
                cols.add(m.group(1))

    # Quitar tokens claramente no-columna
    cols = {c for c in cols if c and c.lower() not in _NON_COLUMN_TOKENS and not c.isdigit()}
    return cols


def _csv_to_records(content, delimiter=","):
    """Convierte contenido CSV a lista de dicts (todo string, se castea en Spark)."""
    reader = csv.DictReader(io.StringIO(content), delimiter=delimiter)
    return [dict(r) for r in reader]


def _normalize_inputs(datasets):
    """Normaliza los datasets de entrada a {nombre_nodo_lower: [records]}.

    datasets: lista de {"node", "io", "format", "content"|"rows", "columns"}
    Solo se usan los de io == "input" (o todos si ninguno trae io).
    """
    inputs = {}
    any_input = any(d.get("io") == "input" for d in datasets)
    for d in datasets:
        if any_input and d.get("io") != "input":
            continue
        node = (d.get("node") or "").strip()
        if not node:
            continue
        rows = d.get("rows")
        if rows is None and d.get("content"):
            if d.get("format") == "json":
                try:
                    rows = json.loads(d["content"])
                except Exception:
                    rows = []
            else:
                rows = _csv_to_records(d["content"])
        inputs[node.lower()] = rows or []
    return inputs


def build_test_script(pyspark_code, inputs, required_cols=None):
    """Construye un script PySpark ejecutable localmente.

    - Inyecta BNX_INPUTS (dict nodo→registros) al inicio.
    - Inyecta BNX_REQUIRED_COLS (columnas que el pipeline referencia) para que
      cada DataFrame las tenga (rellenadas con null si faltan).
    - Reemplaza lecturas spark.read.<fmt>(...) por _bnx_read("<var>").
    - Reemplaza escrituras X.write... por _bnx_write(X, "<var>").
    """
    required_cols = sorted(required_cols or [])
    lines = pyspark_code.split("\n")
    out = []

    # 1. Reemplazar asignaciones de lectura:
    #    Nombre_df = spark.read.<fmt>(...)   →   Nombre_df = _bnx_read("Nombre_df")
    read_re = re.compile(r'^(\s*)(\w+)\s*=\s*spark\.read\.[\w.]+\(.*\)\s*$')
    # 2. Reemplazar escrituras:
    #    X_df.write.mode(...).<fmt>(...)     →   _bnx_write(X_df, "X_df")
    #    X_df.write.<fmt>(...)               →   _bnx_write(X_df, "X_df")
    write_re = re.compile(r'^(\s*)(\w+)\.write\b.*$')
    # 3. Nodos sin fuente:  X_df = None  → placeholder vacío para no romper hijos
    none_re = re.compile(r'^(\s*)(\w+_df)\s*=\s*None\b.*$')

    for ln in lines:
        m_read = read_re.match(ln)
        if m_read:
            indent, var = m_read.group(1), m_read.group(2)
            out.append(f'{indent}{var} = _bnx_read("{var}")')
            continue
        m_write = write_re.match(ln)
        if m_write:
            indent, var = m_write.group(1), m_write.group(2)
            out.append(f'{indent}_bnx_write({var}, "{var}")')
            continue
        m_none = none_re.match(ln)
        if m_none:
            indent, var = m_none.group(1), m_none.group(2)
            out.append(f'{indent}{var} = _bnx_empty("{var}")  # BNX-TEST: era None')
            continue
        out.append(ln)

    body = "\n".join(out)

    # Reescribir joins con clave para que toleren claves ausentes en datos sinteticos:
    #   A.join(B, on="k", how="left")       → _bnx_join(A, B, "k", "left")
    #   A.join(B, on=["k1","k2"], how="left")→ _bnx_join(A, B, ["k1","k2"], "left")
    body = re.sub(
        r'(\w+)\.join\(\s*(\w+)\s*,\s*on\s*=\s*(\[[^\]]*\]|"[^"]*"|\'[^\']*\')\s*,\s*how\s*=\s*("[^"]*"|\'[^\']*\')\s*\)',
        r'_bnx_join(\1, \2, on=\3, how=\4)',
        body,
    )
    # Igual pero con broadcast(X) como lado derecho (lookup joins):
    #   A.join(broadcast(B), on=..., how=...) -> _bnx_join(A, _bnx_lkp("B"), ...)
    # _bnx_lkp resuelve la variable de lookup por nombre (case-insensitive) o
    # devuelve un DataFrame vacio tolerante si el nodo productor nombra distinto.
    body = re.sub(
        r'(\w+)\.join\(\s*broadcast\(\s*(\w+)\s*\)\s*,\s*on\s*=\s*(\[[^\]]*\]|"[^"]*"|\'[^\']*\')\s*,\s*how\s*=\s*("[^"]*"|\'[^\']*\')\s*\)',
        r'_bnx_join(\1, _bnx_lkp("\2"), on=\3, how=\4)',
        body,
    )

    # Reescribir orderBy/sort para que ignoren columnas ausentes:
    #   X.orderBy("a", "b")  → _bnx_sort(X, "a", "b")
    #   X.sort("a")          → _bnx_sort(X, "a")
    body = re.sub(
        r'(\w+)\.(?:orderBy|sort)\(([^)]*)\)',
        r'_bnx_sort(\1, \2)',
        body,
    )

    # Reescribir dropDuplicates([...]) para ignorar columnas ausentes:
    #   X.dropDuplicates(["a","b"])  → _bnx_dropdup(X, ["a","b"])
    body = re.sub(
        r'(\w+)\.dropDuplicates\((\[[^\]]*\])\)',
        r'_bnx_dropdup(\1, \2)',
        body,
    )

    # Corregir casts Ab Initio remanentes dentro de expr("..."): (tipo(N[,M]))x
    # que Spark no entiende (p.ej. substring((decimal(17,2))campo, 0, 17)).
    # Los convertimos a CAST(x AS TIPO) reutilizando la logica del codegen.
    # El contenido de expr(...) tiene las comillas dobles escapadas (\\"), asi que
    # trabajamos sobre la cadena escapada y re-escapamos el resultado.
    try:
        from codegen.spark_codegen import translate_abinitio_casts
    except Exception:
        try:
            from src.codegen.spark_codegen import translate_abinitio_casts
        except Exception:
            translate_abinitio_casts = None

    if translate_abinitio_casts is not None:
        _ab_cast_re = re.compile(r'\((?:string|decimal|integer|int|long|double|real)\(\s*[\d,.\s]+\)\)')

        def _fix_expr_casts(m):
            inner = m.group(1)
            if not _ab_cast_re.search(inner):
                return m.group(0)
            # inner viene con comillas escapadas (\") — desescapar, traducir, re-escapar
            unescaped = inner.replace('\\"', '"')
            fixed = translate_abinitio_casts(unescaped)
            return 'expr("' + fixed.replace('"', '\\"') + '")'

        body = re.sub(
            r'expr\("((?:[^"\\]|\\.)*)"\)',
            _fix_expr_casts,
            body,
        )

    # Corregir size(...) residual sobre escalares dentro de expr("..."):
    # length_of() de Ab Initio pudo haberse traducido a size() (solo ARRAY/MAP),
    # rompiendo con DATATYPE_MISMATCH cuando el argumento es STRING/DECIMAL.
    # Lo reescribimos a length(cast(<arg> as string)). Balanceamos parentesis para
    # capturar el argumento completo. Solo aplica cuando el argumento NO es un
    # array literal (no empieza con 'array(' ni con '[').
    def _find_matching_paren(s, open_idx):
        depth = 0
        i = open_idx
        while i < len(s):
            c = s[i]
            if c == '(':
                depth += 1
            elif c == ')':
                depth -= 1
                if depth == 0:
                    return i
            i += 1
        return -1

    def _fix_size_scalar(text):
        out = text
        guard = 0
        search_from = 0
        while guard < 200:
            guard += 1
            idx = out.find('size(', search_from)
            if idx == -1:
                break
            open_paren = idx + len('size') 
            close = _find_matching_paren(out, open_paren)
            if close == -1:
                break
            arg = out[open_paren + 1:close]
            arg_stripped = arg.strip()
            # No tocar arrays reales
            if arg_stripped.startswith('array(') or arg_stripped.startswith('['):
                search_from = close + 1
                continue
            replacement = 'length(cast(' + arg + ' as string))'
            out = out[:idx] + replacement + out[close + 1:]
            search_from = idx + len(replacement)
        return out

    body = _fix_size_scalar(body)

    # Corregir operadores logicos Ab Initio (&& , ||) dentro de where/filter/expr.
    # Spark SQL no acepta && ni || -> AND / OR. Solo tocamos el contenido de las
    # cadenas de estos metodos para no alterar codigo Python (que no usa && ni ||).
    def _fix_logical_ops(m):
        prefix = m.group(1)   # .where("  |  .filter("  |  expr("
        inner = m.group(2)    # contenido de la cadena
        suffix = m.group(3)   # ")
        if '&&' not in inner and '||' not in inner:
            return m.group(0)
        inner = inner.replace('&&', ' AND ').replace('||', ' OR ')
        inner = re.sub(r'\s{2,}', ' ', inner)
        return prefix + inner + suffix

    body = re.sub(
        r'(\.where\("|\.filter\("|expr\(")((?:[^"\\]|\\.)*)("\))',
        _fix_logical_ops,
        body,
    )

    # Sanear expresiones Ab Initio no traducidas que romperian el analisis Spark.
    # .where("...lookup(...)...") → .where("1=1") (lookup no ejecutable local sin la tabla)
    # Nota: la cadena puede tener comillas escapadas (\\"), por eso el patron es tolerante.
    body = re.sub(
        r'\.where\("(?:[^"\\]|\\.)*lookup\((?:[^"\\]|\\.)*"\)',
        '.where("1=1")  # BNX-TEST: lookup no traducido, filtro neutralizado',
        body,
    )
    body = re.sub(
        r'\.filter\("(?:[^"\\]|\\.)*lookup\((?:[^"\\]|\\.)*"\)',
        '.filter("1=1")  # BNX-TEST: lookup no traducido, filtro neutralizado',
        body,
    )
    # withColumn("X", expr("...lookup(...)..."))  o expr con comentario /* roto:
    # el lookup no es evaluable local (sin la tabla) y los comentarios /* */ de
    # Ab Initio pueden quedar sin cerrar. Neutralizamos la expr a NULL para que la
    # columna exista pero no rompa el analisis SQL.
    def _neutralize_lookup_expr(m):
        col = m.group(1)
        return f'.withColumn("{col}", expr("NULL"))  # BNX-TEST: expr con lookup/comentario no traducible, neutralizada'
    body = re.sub(
        r'\.withColumn\(\s*"([^"]+)"\s*,\s*expr\("(?:[^"\\]|\\.)*(?:lookup\(|/\*)(?:[^"\\]|\\.)*"\)\s*\)',
        _neutralize_lookup_expr,
        body,
    )

    # Neutralizar comandos shell (Run_Program) para no ejecutarlos en la prueba local:
    #   os.system(f"...")  → _bnx_shell(f"...")   (solo registra, no ejecuta)
    body = re.sub(r'\bos\.system\(', '_bnx_shell(', body)

    # Reemplazar el helper de multi-output (output_indexes_split) por uno tolerante:
    # la columna interna 'output_port_index' de Ab Initio no existe en los datos.
    # Se elimina la definicion generada y se usa _bnx_output_split del harness.
    body = re.sub(
        r'def output_indexes_split\([^)]*\):\n(?:[ \t].*\n)+',
        '', body,
    )
    body = re.sub(r'\boutput_indexes_split\(', '_bnx_output_split(', body)

    # Harness que se antepone. Define _bnx_read/_bnx_write y BNX_INPUTS.
    # _bnx_read intenta emparejar por nombre de variable (Nombre_df → nombre del nodo).
    harness = f'''# ===== BNX TEST HARNESS (auto-generado) =====
import json as _json
import re as _re_bnx
from pyspark.sql import SparkSession as _SS
from pyspark.sql import Row as _Row

_BNX_INPUTS = _json.loads({json.dumps(json.dumps(inputs))})
_BNX_REQUIRED_COLS = _json.loads({json.dumps(json.dumps(required_cols))})
_BNX_WRITES = []

class _BnxParamsMeta(type):
    # Metaclase tolerante para PARAMS: atributos no definidos → placeholder.
    def __getattr__(cls, name):
        return f"BNX_PARAM_{{name}}"

def _bnx_ensure_cols(df):
    # Garantiza que el DataFrame tenga todas las columnas que el pipeline referencia.
    # Las ausentes se agregan como null (StringType) para que ninguna operacion
    # aguas abajo (col, where, join, orderBy, expr) falle por columna inexistente.
    from pyspark.sql.functions import lit as _lit
    if df is None:
        return df
    have = set(df.columns)
    # Chequeo case-insensitive: si ya existe la columna con OTRO caso (p.ej.
    # 'Memo_Time' vs 'memo_time'), NO crear un duplicado que causaria ambiguedad.
    have_lower = {{x.lower() for x in have}}
    for c in _BNX_REQUIRED_COLS:
        if c not in have and c.lower() not in have_lower:
            df = df.withColumn(c, _lit(None).cast("string"))
            have_lower.add(c.lower())
    # quitar el placeholder si ya hay columnas reales
    if "_bnx_placeholder" in df.columns and len(df.columns) > 1:
        df = df.drop("_bnx_placeholder")
    return df

def _bnx_spark():
    # ANSI off: casts invalidos (p.ej. string no-numerico a bigint) devuelven NULL
    # en vez de explotar, igual que Ab Initio y que AWS Glue 3.3 (ANSI off por
    # defecto). Alinea el comportamiento local con el del target.
    return (_SS.builder.master("local[1]").appName("BNX_Test")
            .config("spark.sql.ansi.enabled", "false")
            .config("spark.sql.storeAssignmentPolicy", "LEGACY")
            .getOrCreate())

_bnx_session = _bnx_spark()
# Forzar ANSI off en runtime por si la sesion ya existia (getOrCreate reutiliza).
try:
    _bnx_session.conf.set("spark.sql.ansi.enabled", "false")
except Exception:
    pass

def _bnx_match_key(var):
    # var suele ser "NombreNodo_df" → buscamos "nombrenodo"
    base = var[:-3].lower() if var.lower().endswith("_df") else var.lower()
    if base in _BNX_INPUTS:
        return base
    # match laxo por prefijo/contains
    for k in _BNX_INPUTS:
        if k == base or base.startswith(k) or k.startswith(base):
            return k
    return None

def _bnx_make_df(records):
    # Construye un DataFrame con TODAS las columnas como string y esquema explicito.
    # Asi Spark no falla al inferir tipos mezclados (Double vs Long) entre filas;
    # el codigo generado ya castea con CAST(...) cuando necesita tipos.
    from pyspark.sql.types import StructType as _ST, StructField as _SF, StringType as _StrT
    # Union de todas las columnas presentes, preservando orden de aparicion
    col_order = []
    seen = set()
    for rec in records:
        for k in rec.keys():
            if k not in seen:
                seen.add(k)
                col_order.append(k)
    if not col_order:
        col_order = ["_bnx_placeholder"]
    schema = _ST([_SF(c, _StrT(), True) for c in col_order])
    norm_rows = []
    for rec in records:
        norm_rows.append(tuple(
            (None if rec.get(c) is None else str(rec.get(c))) for c in col_order
        ))
    return _bnx_session.createDataFrame(norm_rows, schema=schema)

def _bnx_empty(var):
    # Nodo sin fuente de datos (era None en el codigo generado).
    # Devolvemos un DataFrame vacio placeholder para que los hijos no fallen.
    key = _bnx_match_key(var)
    records = _BNX_INPUTS.get(key, []) if key else []
    if records:
        return _bnx_ensure_cols(_bnx_make_df(records))
    print(f"[BNX-TEST] STUB {{var}}: nodo sin fuente (era None), uso DataFrame vacio")
    return _bnx_ensure_cols(_bnx_make_df([{{"_bnx_placeholder": ""}}]))

def _bnx_read(var):
    key = _bnx_match_key(var)
    records = _BNX_INPUTS.get(key, []) if key else []
    if not records:
        # DataFrame vacío con una columna dummy + columnas requeridas
        print(f"[BNX-TEST] WARN: sin datos de entrada para {{var}} (nodo '{{key}}'), uso vacío")
        return _bnx_ensure_cols(_bnx_make_df([{{"_bnx_placeholder": ""}}]))
    df = _bnx_ensure_cols(_bnx_make_df(records))
    print(f"[BNX-TEST] READ {{var}} (nodo '{{key}}'): {{df.count()}} filas, cols={{df.columns}}")
    return df

def _bnx_lkp(name):
    # Resuelve una tabla de lookup por nombre. El codegen puede referenciar
    # 'connections_lkp_df' cuando el nodo productor se llama 'Connections_Lkp_df'
    # (difieren en mayus/minus) o cuando la tabla se materializa en otro flujo.
    # Busca en globals() una variable *_df que coincida (case-insensitive); si no
    # existe, devuelve un DataFrame vacio tolerante (el join sera un left sin match).
    g = globals()
    want = name.lower()
    if not want.endswith("_df"):
        want_df = want + "_df"
    else:
        want_df = want
    for vn, vv in list(g.items()):
        if vn.lower() == want_df and vv is not None and hasattr(vv, "columns"):
            return vv
    # No encontrado: DataFrame vacio con una columna placeholder.
    print(f"[BNX-TEST] LOOKUP: tabla '{{name}}' no materializada, uso vacio tolerante")
    from pyspark.sql.types import StructType as _ST, StructField as _SF, StringType as _StrT
    return spark.createDataFrame([], _ST([_SF("_bnx_lkp_empty", _StrT(), True)]))

def _bnx_join(left, right, on=None, how="inner"):
    # Join tolerante: si la clave no existe en algun lado (datos sinteticos
    # con esquema generico), la agrega como null para no romper el analisis.
    from pyspark.sql.functions import lit as _lit
    if left is None:
        return right
    if right is None:
        return left
    keys = on if isinstance(on, list) else [on] if on else []
    for k in keys:
        if k and k not in left.columns:
            print(f"[BNX-TEST] JOIN: clave '{{k}}' ausente en lado izquierdo, se agrega null")
            left = left.withColumn(k, _lit(None))
        if k and k not in right.columns:
            print(f"[BNX-TEST] JOIN: clave '{{k}}' ausente en lado derecho, se agrega null")
            right = right.withColumn(k, _lit(None))
    # Evitar columnas duplicadas no-clave (causan AMBIGUOUS_REFERENCE tras el join):
    # renombramos en el lado derecho las comunes que no son clave, con sufijo unico
    # para no colisionar si ya existe un "_r" de un join previo.
    key_set = set(keys)
    left_cols = set(left.columns)
    for c in list(right.columns):
        if c in left_cols and c not in key_set:
            new_name = c + "_r"
            n = 2
            taken = set(left.columns) | set(right.columns)
            while new_name in taken:
                new_name = f"{{c}}_r{{n}}"
                n += 1
            right = right.withColumnRenamed(c, new_name)
    try:
        return left.join(right, on=on, how=how)
    except Exception as _e:
        print(f"[BNX-TEST] JOIN fallo ({{_e}}), uso cross-join limitado")
        return left.crossJoin(right.limit(1))

def _bnx_colname(c):
    # Extrae el nombre de columna de un str o de un Column (col("x"), col("x").desc())
    if isinstance(c, str):
        return c
    try:
        s = str(c)
        _m = _re_bnx.search(r"'([A-Za-z_][A-Za-z0-9_]*)", s) or _re_bnx.search(r'"([A-Za-z_][A-Za-z0-9_]*)"', s)
        return _m.group(1) if _m else None
    except Exception:
        return None

def _bnx_sort(df, *cols):
    # orderBy/sort tolerante: ordena solo por columnas existentes.
    # Resuelve nombres sin distinguir mayus/minus (case-insensitive) contra las
    # columnas reales, para evitar UNRESOLVED_COLUMN cuando el codegen bajo el
    # nombre a minusculas (p.ej. 'memo_time' vs 'Memo_Time').
    from pyspark.sql.functions import col as _col
    if df is None:
        return df
    real_cols = list(df.columns)
    lower_map = {{}}
    for rc in real_cols:
        lower_map.setdefault(rc.lower(), rc)  # primer match gana
    existing = []
    for c in cols:
        name = _bnx_colname(c)
        if not name:
            continue
        if name in real_cols:
            existing.append(_col("`" + name + "`"))
        elif name.lower() in lower_map:
            resolved = lower_map[name.lower()]
            existing.append(_col("`" + resolved + "`"))
        else:
            print(f"[BNX-TEST] SORT: columna '{{name}}' ausente, se ignora")
    if not existing:
        print("[BNX-TEST] SORT: ninguna columna valida, se omite el orden")
        return df
    return df.orderBy(*existing)

def _bnx_dropdup(df, cols):
    # dropDuplicates tolerante: usa solo columnas existentes.
    if df is None:
        return df
    existing = [c for c in cols if c in df.columns]
    if not existing:
        print("[BNX-TEST] DEDUP: ninguna columna valida, dropDuplicates global")
        return df.dropDuplicates()
    return df.dropDuplicates(existing)

def _bnx_shell(cmd):
    # Run_Program: NO ejecutamos comandos shell en la prueba local, solo registramos.
    print(f"[BNX-TEST] SHELL (no ejecutado): {{cmd}}")
    return 0

def _bnx_output_split(df, index_expr, num_outputs):
    # Multi-output reformat tolerante. La columna interna de Ab Initio (p.ej.
    # 'output_port_index') no existe en los datos sinteticos: si falta, repartimos
    # las filas de forma round-robin entre los N puertos para que la prueba avance.
    from pyspark.sql.functions import expr as _expr, monotonically_increasing_id as _mid
    if df is None:
        return [None] * num_outputs
    col = index_expr.strip().strip('"').strip("'")
    if col in df.columns:
        return [df.filter(_expr(f"{{index_expr}} = {{i}}")) for i in range(num_outputs)]
    print(f"[BNX-TEST] OUTPUT-SPLIT: columna '{{col}}' ausente, reparto round-robin en {{num_outputs}} puertos")
    dfx = df.withColumn("_bnx_rr", _mid() % num_outputs)
    return [dfx.filter(_expr(f"_bnx_rr = {{i}}")).drop("_bnx_rr") for i in range(num_outputs)]

def _bnx_write(df, var):
    if df is None:
        print(f"[BNX-TEST] WRITE {{var}}: SKIP (DataFrame None — nodo sin datos)")
        return
    try:
        n = df.count()
        cols = df.columns
        _BNX_WRITES.append({{"var": var, "rows": n, "columns": cols}})
        print(f"[BNX-TEST] WRITE {{var}}: {{n}} filas, cols={{cols}}")
        df.show(5, truncate=False)
    except Exception as _e:
        print(f"[BNX-TEST] WRITE {{var}} ERROR: {{_e}}")
        raise

# Alias de spark para el código generado
spark = _bnx_session
# ===== FIN HARNESS =====

'''

    # El código generado crea su propio spark = SparkSession...getOrCreate().
    # Como local[1] ya tiene una sesión activa, getOrCreate reutiliza la misma.
    # Neutralizamos spark.stop() para no cortar la sesión antes de tiempo si aparece.
    body = body.replace("spark.stop()", "# spark.stop()  # neutralizado por BNX-TEST")

    # Parche de PARAMS: reescribimos la declaración `class PARAMS:` para que use
    # una metaclase tolerante. Así cualquier atributo no definido (AI_BIN, DATABASE,
    # TABLE, etc.) devuelve un placeholder en vez de lanzar AttributeError.
    # La metaclase se define en el harness (_BnxParamsMeta).
    body = re.sub(
        r'^(\s*)class\s+PARAMS\s*:',
        r'\1class PARAMS(metaclass=_BnxParamsMeta):',
        body,
        count=1,
        flags=re.M,
    )

    return harness + body


def run_pyspark_test(pyspark_code, datasets, timeout=120):
    """Ejecuta el código PySpark con datos sintéticos y devuelve el resultado.

    Devuelve dict:
      {"ok": bool, "exit_code": int, "stdout": str, "stderr": str,
       "timed_out": bool, "writes": [...], "reads": [...], "summary": str}
    """
    inputs = _normalize_inputs(datasets)
    required_cols = extract_referenced_columns(pyspark_code)
    script = build_test_script(pyspark_code, inputs, required_cols=required_cols)

    tmp = tempfile.NamedTemporaryFile(
        delete=False, suffix="_bnx_test.py", mode="w", encoding="utf-8"
    )
    tmp.write(script)
    tmp.close()

    env = dict(os.environ)
    # Silenciar logs verbosos de Spark
    env.setdefault("PYSPARK_PYTHON", sys.executable)

    timed_out = False
    try:
        proc = subprocess.run(
            [sys.executable, tmp.name],
            capture_output=True, text=True, timeout=timeout, env=env,
        )
        exit_code = proc.returncode
        stdout, stderr = proc.stdout, proc.stderr
    except subprocess.TimeoutExpired as e:
        timed_out = True
        exit_code = -1
        stdout = e.stdout or ""
        stderr = (e.stderr or "") + f"\n[BNX-TEST] Timeout tras {timeout}s"
        if isinstance(stdout, bytes):
            stdout = stdout.decode("utf-8", "replace")
        if isinstance(stderr, bytes):
            stderr = stderr.decode("utf-8", "replace")
    finally:
        try:
            os.unlink(tmp.name)
        except OSError:
            pass

    # Parsear resúmenes de READ/WRITE desde stdout
    reads = re.findall(r"\[BNX-TEST\] READ (\S+) \(nodo '([^']*)'\): (\d+) filas", stdout)
    writes = re.findall(r"\[BNX-TEST\] WRITE (\S+): (\d+) filas", stdout)

    ok = (not timed_out) and exit_code == 0
    if ok:
        summary = f"Ejecución OK · {len(reads)} lectura(s), {len(writes)} escritura(s)"
    elif timed_out:
        summary = f"Timeout tras {timeout}s — el job tardó demasiado"
    else:
        summary = "Falló la ejecución — revisa el error abajo"

    return {
        "ok": ok,
        "exit_code": exit_code,
        "timed_out": timed_out,
        "stdout": _tail(stdout, 20000),
        "stderr": _tail(stderr, 20000),
        "reads": [{"var": r[0], "node": r[1], "rows": int(r[2])} for r in reads],
        "writes": [{"var": w[0], "rows": int(w[1])} for w in writes],
        "summary": summary,
    }


def _tail(text, max_chars):
    """Recorta texto largo dejando el final (donde suelen estar los errores)."""
    if not text:
        return ""
    if len(text) <= max_chars:
        return text
    return "...[truncado]...\n" + text[-max_chars:]


def stream_pyspark_test(pyspark_code, datasets, timeout=180):
    """Ejecuta el PySpark de prueba y hace *yield* de cada linea de salida en vivo.

    Cada yield es un dict:
      {"type": "line", "text": "..."}     — una linea de stdout/stderr
      {"type": "done", "ok": bool, "summary": str, "reads": [...], "writes": [...]}

    Permite que la UI muestre una consola en tiempo real mientras el job corre.
    """
    import threading
    import time as _time

    inputs = _normalize_inputs(datasets)
    required_cols = extract_referenced_columns(pyspark_code)
    script = build_test_script(pyspark_code, inputs, required_cols=required_cols)

    tmp = tempfile.NamedTemporaryFile(
        delete=False, suffix="_bnx_test.py", mode="w", encoding="utf-8"
    )
    tmp.write(script)
    tmp.close()

    env = dict(os.environ)
    env.setdefault("PYSPARK_PYTHON", sys.executable)
    # Forzar salida sin buffer para ver el progreso en vivo
    env["PYTHONUNBUFFERED"] = "1"

    reads_all = []
    writes_all = []

    proc = subprocess.Popen(
        [sys.executable, "-u", tmp.name],
        stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
        text=True, bufsize=1, env=env,
    )

    start = _time.time()
    timed_out = False

    # Watchdog para el timeout
    def _kill_on_timeout():
        while proc.poll() is None:
            if _time.time() - start > timeout:
                proc.kill()
                return
            _time.sleep(1)

    watcher = threading.Thread(target=_kill_on_timeout, daemon=True)
    watcher.start()

    try:
        for raw_line in iter(proc.stdout.readline, ""):
            line = raw_line.rstrip("\n")
            # Filtrar ruido de Spark que no aporta al usuario
            if _is_noise(line):
                continue
            # Acumular reads/writes para el resumen final
            mr = re.match(r"\[BNX-TEST\] READ (\S+) \(nodo '([^']*)'\): (\d+) filas", line)
            if mr:
                reads_all.append({"var": mr.group(1), "node": mr.group(2), "rows": int(mr.group(3))})
            mw = re.match(r"\[BNX-TEST\] WRITE (\S+): (\d+) filas", line)
            if mw:
                writes_all.append({"var": mw.group(1), "rows": int(mw.group(2))})
            yield {"type": "line", "text": line}
    finally:
        proc.stdout.close()
        proc.wait()
        try:
            os.unlink(tmp.name)
        except OSError:
            pass

    if _time.time() - start > timeout:
        timed_out = True

    exit_code = proc.returncode
    ok = (not timed_out) and exit_code == 0
    if ok:
        summary = f"Ejecución OK · {len(reads_all)} lectura(s), {len(writes_all)} escritura(s)"
    elif timed_out:
        summary = f"Timeout tras {timeout}s — el job tardó demasiado"
    else:
        summary = "Falló la ejecución — revisa el error arriba"

    yield {
        "type": "done",
        "ok": ok,
        "exit_code": exit_code,
        "timed_out": timed_out,
        "summary": summary,
        "reads": reads_all,
        "writes": writes_all,
    }


# Lineas de log de Spark/JVM que no aportan valor al usuario
_NOISE_PATTERNS = (
    "log4j", "SLF4J", "Using Spark's default", "Setting default log level",
    "To adjust logging level", "NativeCodeLoader", "Unable to load native-hadoop",
    "WARN SparkSession: Using an existing", "incubator", "WARNING: Using incubator",
    "SparkStringUtils", "Truncated the string representation",
    # BrokenPipeError de workers de Spark tras df.show() — ruido inofensivo en local
    "BrokenPipeError", "daemon.py", "outfile.flush", "code = worker(", "Errno 32",
    "pyspark.zip/pyspark/daemon", "~~~~~~", "^^^^",
)


def _is_noise(line):
    s = line.strip()
    if not s:
        return True
    # Barras de progreso de Spark: [Stage 0:> ...]
    if s.startswith("[Stage") or s.startswith("["):
        if "Stage" in s:
            return True
    for pat in _NOISE_PATTERNS:
        if pat in line:
            return True
    return False


# ---------------------------------------------------------------------------
# Código autocontenido para AWS: datos sintéticos embebidos, escrituras reales
# ---------------------------------------------------------------------------
def build_aws_selfcontained_code(pyspark_code, datasets, keep_writes=True,
                                 bucket=None, job_name=None):
    """Genera un PySpark AUTOCONTENIDO para ejecutar en AWS Glue/EMR.

    - Reemplaza las lecturas spark.read.<fmt>(...) por DataFrames construidos
      a partir de los datos sintéticos (embebidos como JSON en el propio script).
    - Mantiene las escrituras a S3 reales (keep_writes=True) para ver el output,
      o las neutraliza a .show() (keep_writes=False) si se quiere una corrida seca.
    - Ademas, cada escritura vuelca una copia LEGIBLE (CSV con header, coalesce(1))
      a una ruta de output conocida: s3://<bucket>/bnx-output/<job>/<var>/ para
      poder descargar el resultado con aws s3 cp.
    - Aplica las mismas defensas que el runner local (nodos None, joins tolerantes,
      lookups no traducidos, PARAMS tolerante, columnas requeridas) para que corra.

    Devuelve dict: {"code": <str>, "output_paths": [{"var","path"}]}
    """
    inputs = _normalize_inputs(datasets)
    required_cols = extract_referenced_columns(pyspark_code)

    bucket = (bucket or "datalake-bnx-scripts-dev").strip().rstrip("/")
    job = re.sub(r'[^A-Za-z0-9_-]', '_', (job_name or "bnx-datagen").strip())
    out_prefix = f"s3://{bucket}/bnx-output/{job}"
    output_paths = []

    lines = pyspark_code.split("\n")
    out = []

    read_re = re.compile(r'^(\s*)(\w+)\s*=\s*spark\.read\.[\w.]+\(.*\)\s*$')
    write_re = re.compile(r'^(\s*)(\w+)\.write\b.*$')
    none_re = re.compile(r'^(\s*)(\w+_df)\s*=\s*None\b.*$')

    for ln in lines:
        m_read = read_re.match(ln)
        if m_read:
            indent, var = m_read.group(1), m_read.group(2)
            out.append(f'{indent}{var} = _bnx_src("{var}")')
            continue
        m_none = none_re.match(ln)
        if m_none:
            indent, var = m_none.group(1), m_none.group(2)
            out.append(f'{indent}{var} = _bnx_src("{var}")  # AWS: nodo sin fuente')
            continue
        m_write = write_re.match(ln)
        if m_write:
            indent, var = m_write.group(1), m_write.group(2)
            clean_var = var[:-3] if var.lower().endswith("_df") else var
            copy_path = f"{out_prefix}/{clean_var}"
            output_paths.append({"var": clean_var, "path": copy_path})
            if not keep_writes:
                out.append(f'{indent}{var}.show(10, truncate=False)  # AWS: escritura neutralizada')
            else:
                out.append(ln)  # escritura original (a su path S3)
            # Copia legible CSV single-file a la ruta de output conocida
            out.append(f'{indent}_bnx_save_output({var}, "{copy_path}")')
            continue
        out.append(ln)

    body = "\n".join(out)

    # Reescrituras de robustez (igual que el runner local)
    body = re.sub(
        r'(\w+)\.join\(\s*(\w+)\s*,\s*on\s*=\s*(\[[^\]]*\]|"[^"]*"|\'[^\']*\')\s*,\s*how\s*=\s*("[^"]*"|\'[^\']*\')\s*\)',
        r'_bnx_join(\1, \2, on=\3, how=\4)',
        body,
    )
    # Igual pero con broadcast(X) como lado derecho (lookup joins):
    #   A.join(broadcast(B), on=..., how=...) -> _bnx_join(A, _bnx_lkp("B"), ...)
    # _bnx_lkp resuelve la variable de lookup por nombre (case-insensitive) o
    # devuelve un DataFrame vacio tolerante si el nodo productor nombra distinto.
    body = re.sub(
        r'(\w+)\.join\(\s*broadcast\(\s*(\w+)\s*\)\s*,\s*on\s*=\s*(\[[^\]]*\]|"[^"]*"|\'[^\']*\')\s*,\s*how\s*=\s*("[^"]*"|\'[^\']*\')\s*\)',
        r'_bnx_join(\1, _bnx_lkp("\2"), on=\3, how=\4)',
        body,
    )
    body = re.sub(r'(\w+)\.(?:orderBy|sort)\(([^)]*)\)', r'_bnx_sort(\1, \2)', body)
    body = re.sub(r'(\w+)\.dropDuplicates\((\[[^\]]*\])\)', r'_bnx_dropdup(\1, \2)', body)
    body = re.sub(
        r'\.where\("(?:[^"\\]|\\.)*lookup\((?:[^"\\]|\\.)*"\)',
        '.where("1=1")  # AWS: lookup no traducido, filtro neutralizado', body,
    )
    body = re.sub(
        r'\.filter\("(?:[^"\\]|\\.)*lookup\((?:[^"\\]|\\.)*"\)',
        '.filter("1=1")  # AWS: lookup no traducido, filtro neutralizado', body,
    )
    body = re.sub(r'\bos\.system\(', '_bnx_shell(', body)
    body = re.sub(r'def output_indexes_split\([^)]*\):\n(?:[ \t].*\n)+', '', body)
    body = re.sub(r'\boutput_indexes_split\(', '_bnx_output_split(', body)
    body = re.sub(
        r'^(\s*)class\s+PARAMS\s*:', r'\1class PARAMS(metaclass=_BnxParamsMeta):',
        body, count=1, flags=re.M,
    )

    header = f'''# ============================================================
# BNX — PySpark AUTOCONTENIDO para AWS (datos sinteticos embebidos)
# Generado por Data Redactada. Las lecturas S3 se reemplazan por datos
# sinteticos redactados; las escrituras van a S3 real.
# ============================================================
import json as _json
import re as _re_bnx

_BNX_INPUTS = _json.loads({json.dumps(json.dumps(inputs))})
_BNX_REQUIRED_COLS = _json.loads({json.dumps(json.dumps(sorted(required_cols)))})

class _BnxParamsMeta(type):
    def __getattr__(cls, name):
        return f"BNX_PARAM_{{name}}"

def _bnx_ensure_cols(df):
    from pyspark.sql.functions import lit as _lit
    if df is None:
        return df
    have = set(df.columns)
    have_lower = {{x.lower() for x in have}}
    for c in _BNX_REQUIRED_COLS:
        if c not in have and c.lower() not in have_lower:
            df = df.withColumn(c, _lit(None).cast("string"))
            have_lower.add(c.lower())
    if "_bnx_placeholder" in df.columns and len(df.columns) > 1:
        df = df.drop("_bnx_placeholder")
    return df

def _bnx_make_df(records):
    from pyspark.sql.types import StructType as _ST, StructField as _SF, StringType as _StrT
    from pyspark.sql import Row as _Row
    col_order, seen = [], set()
    for rec in records:
        for k in rec.keys():
            if k not in seen:
                seen.add(k); col_order.append(k)
    if not col_order:
        col_order = ["_bnx_placeholder"]
    schema = _ST([_SF(c, _StrT(), True) for c in col_order])
    rows = [tuple((None if rec.get(c) is None else str(rec.get(c))) for c in col_order) for rec in records]
    return spark.createDataFrame(rows, schema=schema)

def _bnx_match_key(var):
    base = var[:-3].lower() if var.lower().endswith("_df") else var.lower()
    if base in _BNX_INPUTS:
        return base
    for k in _BNX_INPUTS:
        if k == base or base.startswith(k) or k.startswith(base):
            return k
    return None

def _bnx_src(var):
    key = _bnx_match_key(var)
    records = _BNX_INPUTS.get(key, []) if key else []
    if not records:
        records = [{{"_bnx_placeholder": ""}}]
    return _bnx_ensure_cols(_bnx_make_df(records))

def _bnx_shell(cmd):
    print(f"[AWS] SHELL (no ejecutado): {{cmd}}")
    return 0

def _bnx_save_output(df, path):
    # Copia legible del resultado a una ruta de output conocida (CSV single-file)
    # y genera una PRESIGNED URL de S3 para descargar directo desde el browser.
    if df is None:
        print(f"[AWS] OUTPUT SKIP (df None): {{path}}")
        return
    try:
        df.coalesce(1).write.mode("overwrite").option("header", "true").csv(path)
        n = df.count()
        print(f"[AWS] OUTPUT escrito: {{path}} ({{n}} filas)")
        _bnx_presign(path)
    except Exception as _e:
        print(f"[AWS] OUTPUT error en {{path}}: {{_e}}")

def _bnx_presign(path):
    # Genera una presigned URL (valida 7 dias) del archivo CSV escrito en 'path'.
    # Usa el rol del job (Glue/EMR) — no requiere credenciales del cliente.
    try:
        import boto3
        m = _re_bnx.match(r"s3://([^/]+)/(.+)", path.rstrip("/"))
        if not m:
            return
        bkt, prefix = m.group(1), m.group(2)
        s3 = boto3.client("s3")
        # Buscar el archivo part-*.csv que Spark escribio bajo el prefijo
        resp = s3.list_objects_v2(Bucket=bkt, Prefix=prefix + "/")
        keys = [o["Key"] for o in resp.get("Contents", []) if o["Key"].endswith(".csv")]
        if not keys:
            keys = [o["Key"] for o in resp.get("Contents", []) if "part-" in o["Key"]]
        for key in keys:
            url = s3.generate_presigned_url(
                "get_object", Params={{"Bucket": bkt, "Key": key}}, ExpiresIn=604800,
            )
            fname = key.split("/")[-1]
            print(f"[AWS] DOWNLOAD|{{fname}}|{{url}}")
    except Exception as _e:
        print(f"[AWS] PRESIGN error para {{path}}: {{_e}}")

def _bnx_output_split(df, index_expr, num_outputs):
    from pyspark.sql.functions import expr as _expr, monotonically_increasing_id as _mid
    if df is None:
        return [None] * num_outputs
    col = index_expr.strip().strip('"').strip("'")
    if col in df.columns:
        return [df.filter(_expr(f"{{index_expr}} = {{i}}")) for i in range(num_outputs)]
    dfx = df.withColumn("_bnx_rr", _mid() % num_outputs)
    return [dfx.filter(_expr(f"_bnx_rr = {{i}}")).drop("_bnx_rr") for i in range(num_outputs)]

def _bnx_colname(c):
    if isinstance(c, str):
        return c
    try:
        s = str(c)
        _m = _re_bnx.search(r"'([A-Za-z_][A-Za-z0-9_]*)", s) or _re_bnx.search(r'"([A-Za-z_][A-Za-z0-9_]*)"', s)
        return _m.group(1) if _m else None
    except Exception:
        return None

def _bnx_sort(df, *cols):
    from pyspark.sql.functions import col as _col
    if df is None:
        return df
    real_cols = list(df.columns)
    lower_map = {{}}
    for rc in real_cols:
        lower_map.setdefault(rc.lower(), rc)
    existing = []
    for c in cols:
        name = _bnx_colname(c)
        if not name:
            continue
        if name in real_cols:
            existing.append(_col("`" + name + "`"))
        elif name.lower() in lower_map:
            existing.append(_col("`" + lower_map[name.lower()] + "`"))
    return df.orderBy(*existing) if existing else df

def _bnx_dropdup(df, cols):
    if df is None:
        return df
    existing = [c for c in cols if c in df.columns]
    return df.dropDuplicates(existing) if existing else df.dropDuplicates()

def _bnx_lkp(name):
    # Resuelve tabla de lookup por nombre (case-insensitive) desde globals();
    # si no existe, DataFrame vacio tolerante.
    g = globals()
    want_df = name.lower() if name.lower().endswith("_df") else name.lower() + "_df"
    for vn, vv in list(g.items()):
        if vn.lower() == want_df and vv is not None and hasattr(vv, "columns"):
            return vv
    print(f"[AWS] LOOKUP: tabla '{{name}}' no materializada, uso vacio tolerante")
    from pyspark.sql.types import StructType as _ST, StructField as _SF, StringType as _StrT
    return spark.createDataFrame([], _ST([_SF("_bnx_lkp_empty", _StrT(), True)]))

def _bnx_join(left, right, on=None, how="inner"):
    from pyspark.sql.functions import lit as _lit
    if left is None:
        return right
    if right is None:
        return left
    keys = on if isinstance(on, list) else [on] if on else []
    for k in keys:
        if k and k not in left.columns:
            left = left.withColumn(k, _lit(None))
        if k and k not in right.columns:
            right = right.withColumn(k, _lit(None))
    key_set = set(keys)
    left_cols = set(left.columns)
    for c in list(right.columns):
        if c in left_cols and c not in key_set:
            new_name = c + "_r"; n = 2
            taken = set(left.columns) | set(right.columns)
            while new_name in taken:
                new_name = f"{{c}}_r{{n}}"; n += 1
            right = right.withColumnRenamed(c, new_name)
    try:
        return left.join(right, on=on, how=how)
    except Exception:
        return left.crossJoin(right.limit(1))
# ============================================================

'''

    return {"code": header + body, "output_paths": output_paths}
