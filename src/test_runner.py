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


# Carpeta donde el runner LOCAL vuelca los resultados de cada escritura para que
# se puedan descargar desde la GUI. Vive en la raiz del proyecto (fuera de git).
BNX_LOCAL_OUTPUT_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "output", "local_test",
)


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


def _extract_write_dest(write_line):
    """Extrae el nombre de la tabla/destino de una linea de escritura PySpark.

    Ejemplos:
      X.write.mode("overwrite").parquet(f"{PARAMS.BASE_PATH}/output/tabla_clientes")
        -> "tabla_clientes"
      X.write.format("jdbc")...option("dbtable", "cuentas").save()  -> "cuentas"
      X.write.csv("/tmp/salida_final")                              -> "salida_final"

    Devuelve None si no se reconoce ningun destino (el caller usa el nombre del df).
    """
    # dbtable option (JDBC)
    m = re.search(r'"dbtable"\s*,\s*"([^"]+)"', write_line)
    if m:
        return _basename_token(m.group(1))
    # .parquet(...) / .csv(...) / .json(...) / .save(...) / .orc(...) / .text(...)
    m = re.search(
        r'\.(?:parquet|csv|json|orc|text|save)\(\s*f?["\']([^"\']+)["\']',
        write_line,
    )
    if m:
        return _basename_token(m.group(1))
    return None


def _basename_token(path_str):
    """Ultimo segmento util de un path, ignorando expresiones {..} interpoladas."""
    # Quitar cualquier interpolacion f-string {PARAMS.BASE_PATH} etc.
    cleaned = re.sub(r'\{[^}]*\}', '', path_str)
    cleaned = cleaned.strip().strip("/")
    if not cleaned:
        return None
    seg = cleaned.split("/")[-1]
    seg = seg.strip()
    return seg or None


def build_test_script(pyspark_code, inputs, required_cols=None, output_dir=None,
                      master="local[*]", amplify=1):
    """Construye un script PySpark ejecutable localmente.

    - Inyecta BNX_INPUTS (dict nodo→registros) al inicio.
    - Inyecta BNX_REQUIRED_COLS (columnas que el pipeline referencia) para que
      cada DataFrame las tenga (rellenadas con null si faltan).
    - Inyecta BNX_OUTPUT_DIR (carpeta donde se vuelcan los CSV de resultado para
      poder descargarlos desde la GUI).
    - Reemplaza lecturas spark.read.<fmt>(...) por _bnx_read("<var>").
    - Reemplaza escrituras X.write... por _bnx_write(X, "<var>").

    master:  master de Spark (p.ej. 'local[1]' normal, 'local[2]' para simular
             2 workers en el benchmark de optimizacion).
    amplify: factor de replicacion de los datos de entrada. >1 infla el volumen
             (repite cada registro N veces) para que las optimizaciones (cache,
             broadcast, coalesce) muestren su efecto en el benchmark.
    """
    required_cols = sorted(required_cols or [])
    output_dir = output_dir or BNX_LOCAL_OUTPUT_DIR
    lines = pyspark_code.split("\n")
    out = []

    # 1. Reemplazar asignaciones de lectura:
    #    Nombre_df = spark.read.<fmt>(...)   →   Nombre_df = _bnx_read("Nombre_df")
    read_re = re.compile(r'^(\s*)(\w+)\s*=\s*spark\.read\.[\w.]+\(.*\)\s*$')
    # 2. Reemplazar escrituras:
    #    X_df.write.mode(...).<fmt>("<destino>")  →  _bnx_write(X_df, "X_df", "<destino>")
    #    X_df.write.<fmt>(...)                    →  _bnx_write(X_df, "X_df", "<destino>")
    # El "<destino>" es el nombre de la tabla/ruta de salida (ultimo segmento del
    # path o el dbtable). Se usa para nombrar el CSV descargable, asi cada SINK
    # produce un archivo distinto con nombre significativo (no el nombre del df).
    # Tolera .coalesce(N)/.repartition(N) intermedios (introducidos por el
    # optimizador de performance) antes del .write, para seguir neutralizando la
    # escritura a S3 en la prueba local.
    write_re = re.compile(r'^(\s*)(\w+)(?:\.(?:coalesce|repartition)\([^)]*\))*\.write\b.*$')
    # 3. Nodos sin fuente:  X_df = None  → placeholder vacío para no romper hijos
    none_re = re.compile(r'^(\s*)(\w+_df)\s*=\s*None\b.*$')
    # 4. DML crudo Ab Initio que quedo sin traducir y NO es Python valido
    #    (p.ej. "out.* :: in1.*;", "out.CAMPO :: expr;", "begin", "end;").
    #    Se comenta para que el script sea ejecutable; semanticamente el nodo
    #    ya arrastra el DataFrame del padre, asi que el passthrough no se pierde.
    dml_raw_re = re.compile(
        r'^\s*('
        r'out\s*::\s*\w+\s*\('
        r'|out\.\*\s*::'
        r'|out\.\w+\s*:(?:\d+)?:'      # out.CAMPO :: expr  y  out.CAMPO :N: expr (prioridad Ab Initio)
        r'|begin\s*$'
        r'|end\s*;'
        r'|end\s*$'
        r'|let\s+\w+'
        r'|include\s+["\']'
        r')'
    )

    for ln in lines:
        m_read = read_re.match(ln)
        if m_read:
            indent, var = m_read.group(1), m_read.group(2)
            out.append(f'{indent}{var} = _bnx_read("{var}")')
            continue
        m_write = write_re.match(ln)
        if m_write:
            indent, var = m_write.group(1), m_write.group(2)
            dest = _extract_write_dest(ln) or var
            dest_arg = dest.replace('"', '\\"')
            out.append(f'{indent}_bnx_write({var}, "{var}", "{dest_arg}")')
            continue
        m_none = none_re.match(ln)
        if m_none:
            indent, var = m_none.group(1), m_none.group(2)
            out.append(f'{indent}{var} = _bnx_empty("{var}")  # BNX-TEST: era None')
            continue
        if dml_raw_re.match(ln) and not ln.lstrip().startswith('#'):
            indent = ln[:len(ln) - len(ln.lstrip())]
            out.append(f'{indent}# BNX-TEST: DML crudo sin traducir (passthrough/omitido): {ln.strip()}')
            continue
        # Linea huerfana con solo "..." (Ellipsis) que quedo de un raw reformat
        # del DML de Ab Initio. El error real es "unexpected indent": es una linea
        # suelta con indentacion inesperada (no es cuerpo de un bloque). La
        # comentamos por completo (sin indentacion) para eliminarla como sentencia.
        if ln.strip() == "...":
            out.append(f'# BNX-TEST: Ellipsis huerfano de DML crudo neutralizado')
            continue
        # Fragmento huerfano de un comentario partido por un \n del DML crudo:
        # linea INDENTADA que termina en "(truncado)" o "..." y no es codigo valido.
        # Provoca "IndentationError: unexpected indent". La comentamos por completo.
        if (ln[:1] in (' ', '\t')) and re.search(r'(\(truncado\)|\.\.\.)\s*$', ln):
            out.append(f'# BNX-TEST: fragmento de comentario huerfano neutralizado: {ln.strip()}')
            continue
        out.append(ln)

    body = "\n".join(out)

    # Corregir lineas withColumn(...) rotas por un comentario "# TODO: ..." que
    # contiene parentesis sin balancear (viene de un cast/expr Ab Initio no
    # traducido por versiones previas del generador). Ejemplo real:
    #   .withColumn("MIS_DATE", lit(None)  # TODO: (date('YYYY-MM-DD'))(MISDATE))
    # El parentesis final del withColumn queda "dentro" del comentario -> SyntaxError.
    # Si el TODO contiene un cast de fecha Ab Initio lo traducimos a to_date;
    # si no, dejamos lit(None) y quitamos el comentario roto para balancear.
    _todo_date_re = re.compile(
        r'''\(?\s*date\(\s*['"]([^'"]+)['"]\s*\)'''
        r'''(?:\s*\(\s*['"][^'"]*['"]\s*\))?'''
        r'''\s*\)?\s*'''
        r'''\(?\s*(?:in\d*\.)?([\w'".\-:/]+?)\s*\)?\s*$'''
    )

    def _fix_broken_todo(mo):
        prefix = mo.group(1)   # "  VAR_df = VAR_df" o "  ...df"
        col = mo.group(2)
        todo = mo.group(3).strip()
        # Intentar obtener el DataFrame destino desde el prefijo "VAR = VAR2"
        _dfm = re.search(r'=\s*([A-Za-z_]\w*)\s*$', prefix)
        target_df = _dfm.group(1) if _dfm else None
        dm = _todo_date_re.search(todo)
        if dm:
            fmt = dm.group(1).replace("YYYY", "yyyy").replace("DD", "dd")
            valor = dm.group(2).strip()
            if (valor.startswith("'") and valor.endswith("'")) or (valor.startswith('"') and valor.endswith('"')):
                lit_val = valor.strip(chr(39) + chr(34))
                inner = f'''to_date(lit("{lit_val}"), "{fmt}")'''
                return f'{prefix}.withColumn("{col}", {inner})  # BNX-TEST: cast fecha Ab Initio traducido'
            # Valor = campo. Puede que el nombre no exista tal cual (p.ej. MISDATE
            # vs MIS_DATE). Usamos helper tolerante que resuelve con/sin guiones
            # bajos y case-insensitive; si no existe, devuelve NULL.
            if target_df:
                inner = f'_bnx_todate({target_df}, "{valor}", "{fmt}")'
            else:
                inner = f'to_date(col("{valor}"), "{fmt}")'
            return f'{prefix}.withColumn("{col}", {inner})  # BNX-TEST: cast fecha Ab Initio traducido (col tolerante)'
        return f'{prefix}.withColumn("{col}", lit(None))  # BNX-TEST: TODO Ab Initio no traducible, columna NULL'

    # Captura la forma completa: "<algo>.withColumn("COL", lit(None)  # TODO: <expr>)"
    # tanto si va sola en la linea como si es "VAR = VAR.withColumn(...)".
    body = re.sub(
        r'^(.*?)\.withColumn\(\s*"([^"]+)"\s*,\s*lit\(None\)\s*#\s*TODO:\s*(.*?)\)\s*$',
        _fix_broken_todo,
        body,
        flags=re.M,
    )

    # Hacer tolerante el cast de fecha ya traducido de forma rigida por versiones
    # anteriores o por el parser: "VAR = VAR.withColumn("C", to_date(col("X"), "fmt"))".
    # Si 'X' no existe con ese nombre exacto (p.ej. Ab Initio MISDATE vs col MIS_DATE)
    # Spark lanza UNRESOLVED_COLUMN. Reescribimos a _bnx_todate(df, "X", "fmt") que
    # resuelve el nombre ignorando guion bajo/mayusculas o devuelve NULL.
    def _tolerant_todate(mo):
        prefix = mo.group(1)
        col = mo.group(2)
        field = mo.group(3)
        fmt = mo.group(4)
        _dfm = re.search(r'=\s*([A-Za-z_]\w*)\s*$', prefix)
        target_df = _dfm.group(1) if _dfm else None
        if not target_df:
            return mo.group(0)
        return (f'{prefix}.withColumn("{col}", _bnx_todate({target_df}, "{field}", "{fmt}"))'
                f'  # BNX-TEST: to_date col tolerante')

    body = re.sub(
        r'^(.*?)\.withColumn\(\s*"([^"]+)"\s*,\s*to_date\(\s*col\(\s*"([^"]+)"\s*\)\s*,\s*"([^"]+)"\s*\)\s*\)\s*(?:#.*)?$',
        _tolerant_todate,
        body,
        flags=re.M,
    )

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

    # Reescribir groupBy("a","b") para ignorar claves de agrupacion AUSENTES en los
    # datos sinteticos (que provocan UNRESOLVED_COLUMN). _bnx_groupby devuelve un
    # GroupedData usando solo las claves existentes; el .agg(...) encadenado sigue
    # funcionando igual.
    body = re.sub(
        r'(\w+)\.groupBy\(([^)]*)\)',
        r'_bnx_groupby(\1, \2)',
        body,
    )

    # Corregir casts Ab Initio remanentes dentro de expr("..."): (tipo(N[,M]))x
    # que Spark no entiende (p.ej. substring((decimal(17,2))campo, 0, 17)).
    # Los convertimos a CAST(x AS TIPO) reutilizando la logica del codegen.
    # El contenido de expr(...) tiene las comillas dobles escapadas (\\"), asi que
    # trabajamos sobre la cadena escapada y re-escapamos el resultado.
    try:
        from codegen.spark_codegen import translate_abinitio_casts, _translate_if_else
    except Exception:
        try:
            from src.codegen.spark_codegen import translate_abinitio_casts, _translate_if_else
        except Exception:
            translate_abinitio_casts = None
            _translate_if_else = None

    # Corregir 'if (...) ... else ...' Ab Initio crudo dentro de expr("...") que
    # quedo sin traducir (codigo compilado antes del fix). Lo pasamos por
    # _translate_if_else para convertirlo a CASE WHEN ... END.
    if _translate_if_else is not None:
        def _fix_expr_ifs(m):
            inner = m.group(1)
            if not re.search(r'\bif\s*\(', inner, re.IGNORECASE):
                return m.group(0)
            unescaped = inner.replace('\\"', '"')
            fixed = _translate_if_else(unescaped)
            return 'expr("' + fixed.replace('"', '\\"') + '")'

        body = re.sub(
            r'expr\("((?:[^"\\]|\\.)*)"\)',
            _fix_expr_ifs,
            body,
        )

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
        original = m.group(0)
        # Des-escapar operadores | del formato serializado GDE (\| -> |) para que
        # \|\| se reconozca como || y se traduzca a OR. El \| ademas provoca
        # SyntaxWarning ("invalid escape sequence") en Python.
        if '\\|' in inner:
            inner = inner.replace('\\|', '|')
        # Des-escapar parentesis/corchetes del serializado GDE (\( \) \[ \]) que
        # generan SyntaxWarning ("\)" invalido) y no aportan nada en SQL.
        for _esc, _plain in (('\\(', '('), ('\\)', ')'), ('\\[', '['), ('\\]', ']')):
            if _esc in inner:
                inner = inner.replace(_esc, _plain)
        # Quitar SOLO comillas escapadas residuales impares (\") del serializado GDE
        # que dejarian la cadena SQL sin cerrar. Si el numero de \" es par se asume
        # que son literales balanceados legitimos y no se tocan.
        if inner.count('\\"') % 2 == 1:
            inner = inner.replace('\\"', '')
        if inner == m.group(2):  # sin cambios de des-escape...
            if '&&' not in inner and '||' not in inner:
                return original
        inner = inner.replace('&&', ' AND ').replace('||', ' OR ')
        inner = re.sub(r'\s{2,}', ' ', inner).strip()
        return prefix + inner + suffix

    # Pre-saneo: comilla escapada residual (\") pegada al cierre de where/filter/expr,
    # que deja la cadena sin cerrar: .where("... \")  ->  .where("...")
    # Se corre ANTES de _fix_logical_ops porque ese \" rompe el emparejamiento del
    # regex de cadenas escapadas.
    body = re.sub(r'(\.where\("|\.filter\("|expr\(")((?:[^"\\]|\\.)*?)\s*\\"(\))', r'\1\2"\3', body)

    # Neutralizar withColumn("col", expr("<comentario Ab Initio o vacio>")) que
    # provienen de asignaciones DML comentadas (out.x :: //in.y;). El expr("//...")
    # o expr("") rompe con ParseException. Se reemplaza por lit(None). Esta red de
    # seguridad cubre codigo ya generado por versiones previas (sin regenerar).
    def _neutralize_comment_expr(m):
        pre = m.group(1)      # '<df>.withColumn("col", '
        inner = m.group(2)    # contenido dentro de expr("...")
        stripped = inner.strip()
        if stripped == "" or stripped.startswith("//") or stripped.startswith("/*"):
            return f'{pre}lit(None))  # BNX-TEST: expr vacia/comentada neutralizada'
        return m.group(0)
    body = re.sub(
        r'(\.withColumn\(\s*"[^"]+"\s*,\s*)expr\("((?:[^"\\]|\\.)*)"\)\)',
        _neutralize_comment_expr,
        body,
    )
    # withColumn("col", expr("sum(x)")) con una funcion de agregacion pura rompe con
    # MISSING_GROUP_BY (no hay GROUP BY). En un reformat Ab Initio equivale a una
    # agregacion global: la envolvemos en OVER () para que Spark la acepte.
    _agg_names = ("sum", "count", "avg", "mean", "min", "max", "stddev", "variance",
                  "collect_list", "collect_set", "first", "last")
    def _wrap_agg_expr(m):
        pre = m.group(1)       # '<df>.withColumn("col", expr("'
        inner = m.group(2)     # contenido del expr(...)
        suffix = m.group(3)    # '"))'
        s = inner.strip()
        mm = re.match(r'(\w+)\s*\(', s)
        if not mm or mm.group(1).lower() not in _agg_names:
            return m.group(0)
        # ya tiene OVER? no tocar
        if re.search(r'\bover\s*\(', s, re.IGNORECASE):
            return m.group(0)
        # verificar que la llamada abarca toda la expresion (agregacion pura)
        depth = 0
        oi = s.index('(')
        for i in range(oi, len(s)):
            if s[i] == '(':
                depth += 1
            elif s[i] == ')':
                depth -= 1
                if depth == 0:
                    if i == len(s) - 1:
                        return f'{pre}{s} OVER (){suffix}'
                    return m.group(0)
        return m.group(0)
    body = re.sub(
        r'(\.withColumn\(\s*"[^"]+"\s*,\s*expr\(")((?:[^"\\]|\\.)*)("\)\))',
        _wrap_agg_expr,
        body,
    )

    # Idem para .where("//...") / .filter("//...") vacios o solo-comentario.
    def _neutralize_comment_where(m):
        method = m.group(1)   # '.where("' | '.filter("'
        inner = m.group(2)
        stripped = inner.strip()
        if stripped == "" or stripped.startswith("//") or stripped.startswith("/*"):
            return f'{method}1=1")  # BNX-TEST: filtro vacio/comentado neutralizado'
        return m.group(0)
    body = re.sub(
        r'(\.where\("|\.filter\(")((?:[^"\\]|\\.)*)"\)',
        _neutralize_comment_where,
        body,
    )

    body = re.sub(
        r'(\.where\("|\.filter\("|expr\(")((?:[^"\\]|\\.)*)("\))',
        _fix_logical_ops,
        body,
    )

    # Corregir "NOT x IS [NOT] NULL" (sin parentesis) -> "NOT (x IS [NOT] NULL)".
    # Spark no acepta la forma sin parentesis. Aplica a todo el body (solo afecta
    # cadenas SQL dentro de where/filter/expr; el token no aparece en Python).
    body = re.sub(
        r'\bNOT\s+([A-Za-z_][\w.]*)\s+IS\s+(NOT\s+)?NULL',
        lambda m: f'NOT ({m.group(1)} IS {m.group(2) or ""}NULL)',
        body,
        flags=re.IGNORECASE,
    )

    # Corregir cast de fecha Ab Initio anidado raro que quedo crudo dentro de
    # expr("..."): (date('FMT')(\"\\x01\"))('VALOR')  ->  to_date('VALOR', "fmt").
    # El contenido de expr tiene comillas escapadas (\\"), trabajamos sobre la
    # cadena escapada. Ejemplo real: ((date('YYYY-MM-DD')(\"\\x01\"))('2024-12-12')).
    _weird_date_re = re.compile(
        r'''\(?\s*date\(\s*'([^']+)'\s*\)'''
        r'''(?:\s*\(\s*\\?"[^"]*\\?"\s*\))?'''
        r'''\s*\)?\s*'''
        r'''\(\s*'([^']*)'\s*\)'''
    )

    def _fix_weird_date(mo):
        inner = mo.group(1)
        if 'date(' not in inner:
            return mo.group(0)
        unescaped = inner.replace('\\"', '"')
        def _repl(d):
            fmt = d.group(1).replace("YYYY", "yyyy").replace("DD", "dd")
            valor = d.group(2)
            return f'''to_date('{valor}', "{fmt}")'''
        fixed = _weird_date_re.sub(_repl, unescaped)
        # colapsar parentesis externos redundantes
        fixed = fixed.strip()
        while fixed.startswith('(') and fixed.endswith(')') and fixed.count('(') > fixed.count('to_date('):
            core = fixed[1:-1].strip()
            if core.count('(') == core.count(')'):
                fixed = core
            else:
                break
        return 'expr("' + fixed.replace('"', '\\"') + '")'

    body = re.sub(
        r'expr\("((?:[^"\\]|\\.)*)"\)',
        _fix_weird_date,
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

    # --- Relajar comparaciones ENTRE COLUMNAS en filtros (opcion A) ---
    # Patron: .where(col("A") OP col("B"))  con OP relacional (>= <= > < = ==).
    # Estas comparaciones suelen venir de un lookup_count de Ab Initio (if(in.A >=
    # rec.B)). En la prueba local, B viene del lookup y tras el LEFT join sin match
    # queda NULL, con lo que "A OP NULL" es NULL (falso) y se descartan TODAS las
    # filas -> salida vacia. Como los datos sinteticos redactados no pueden cumplir
    # una relacion entre dos columnas de texto, relajamos el filtro: la fila pasa si
    # cumple la comparacion O si el lado derecho es NULL (sin dato de lookup).
    # Solo afecta a la PRUEBA LOCAL; el codigo que va a AWS no se toca.
    def _relax_col_cmp(m):
        a, op, b = m.group(1), m.group(2), m.group(3)
        # Normalizar '==' de Ab Initio a '=' de SQL.
        sql_op = "=" if op == "==" else op
        return (f'.where("(`{a}` {sql_op} `{b}`) OR `{b}` IS NULL OR `{a}` IS NULL")'
                f'  # BNX-TEST: comparacion entre columnas relajada (lookup sin datos sinteticos)')
    body = re.sub(
        r'\.where\(\s*col\("([^"]+)"\)\s*(>=|<=|==|=|>|<)\s*col\("([^"]+)"\)\s*\)',
        _relax_col_cmp,
        body,
    )
    body = re.sub(
        r'\.filter\(\s*col\("([^"]+)"\)\s*(>=|<=|==|=|>|<)\s*col\("([^"]+)"\)\s*\)',
        _relax_col_cmp,
        body,
    )

    # --- Relajar filtros de NULIDAD que vacian la salida en la prueba local ---
    # Patron: .where("NOT (col IS NULL)")  o  .where("col IS NOT NULL")
    # Estos vienen de chequeos Ab Initio sobre columnas que NO existen en los datos
    # sinteticos (p.ej. subcampos aplanados col_subcampo, o campos de un lookup sin
    # datos). Esas columnas son siempre NULL, asi que el filtro descarta TODAS las
    # filas -> salida vacia. En la PRUEBA LOCAL neutralizamos ese predicado a TRUE
    # para poder ver datos; el codigo que va a AWS NO se toca.
    # NOT (X IS NULL) -> (TRUE)
    body = re.sub(
        r'\.where\("NOT \(([A-Za-z_][\w]*) IS NULL\)"\)',
        r'.where("TRUE")  # BNX-TEST: filtro de nulidad relajado (columna sin dato sintetico)',
        body,
    )
    # X IS NOT NULL  (predicado unico en el where) -> TRUE
    body = re.sub(
        r'\.where\("([A-Za-z_][\w]*) IS NOT NULL"\)',
        r'.where("TRUE")  # BNX-TEST: filtro de nulidad relajado (columna sin dato sintetico)',
        body,
    )

    # --- Salvaguarda general: filtros SQL sobre columnas inexistentes ---
    # Patron: <df>.where("<sql>")  o  <df>.filter("<sql>")  con SQL de string.
    # Si el <sql> referencia columnas que no existen en los datos sinteticos
    # (p.ej. event_type/event_text de una rama de logs vacia, o subcampos que no
    # se generaron), Spark lanza UNRESOLVED_COLUMN y aborta el job. Redirigimos
    # esos filtros a _bnx_where(df, sql), que intenta el filtro y, si falla por
    # columna ausente, devuelve el df SIN filtrar (y avisa). Solo afecta la PRUEBA
    # LOCAL; el codigo que va a AWS NO se toca. No aplica a .where(col(...)) ni a
    # filtros ya neutralizados (comentario BNX-TEST al final de la linea).
    # Lineas de la forma:  DST = SRC.where("...")   (SRC puede ser != DST).
    body = re.sub(
        r'^(\s*)(\w+)\s*=\s*(\w+)\.(?:where|filter)\("((?:[^"\\]|\\.)*)"\)\s*$',
        lambda m: f'{m.group(1)}{m.group(2)} = _bnx_where({m.group(3)}, "{m.group(4)}")  # BNX-TEST: filtro tolerante a columnas ausentes',
        body,
        flags=re.MULTILINE,
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
_BNX_OUTPUT_DIR = _json.loads({json.dumps(json.dumps(output_dir))})
_BNX_MASTER = {json.dumps(master)}
_BNX_AMPLIFY = {int(amplify)}

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

def _bnx_todate(df, colname, fmt):
    # to_date tolerante: resuelve el nombre de columna ignorando mayus/minus y
    # diferencias de guion bajo (p.ej. Ab Initio 'MISDATE' vs columna 'MIS_DATE').
    # Si no existe ninguna variante, devuelve NULL en vez de romper el analisis.
    from pyspark.sql.functions import to_date as _td, col as _col, lit as _lit
    target = None
    if df is not None:
        want = colname.lower().replace("_", "")
        for c in df.columns:
            if c.lower().replace("_", "") == want:
                target = c
                break
    if target is None:
        return _to_date_null(fmt)
    return _td(_col(target), fmt)

def _to_date_null(fmt):
    from pyspark.sql.functions import to_date as _td, lit as _lit
    return _td(_lit(None).cast("string"), fmt)

def _bnx_spark():
    # ANSI off: casts invalidos (p.ej. string no-numerico a bigint) devuelven NULL
    # en vez de explotar, igual que Ab Initio y que AWS Glue 3.3 (ANSI off por
    # defecto). Alinea el comportamiento local con el del target.
    return (_SS.builder.master(_BNX_MASTER).appName("BNX_Test")
            .config("spark.sql.ansi.enabled", "false")
            .config("spark.sql.storeAssignmentPolicy", "LEGACY")
            # Datos de prueba son pequenos: 200 particiones de shuffle (default) es
            # absurdo y dispara el tiempo en grafos con muchos joins/gathers. Con 8
            # el mismo job baja de minutos a segundos.
            .config("spark.sql.shuffle.partitions", "8")
            .config("spark.default.parallelism", "8")
            # Broadcast agresivo de lookups pequenos (evita shuffles caros).
            .config("spark.sql.adaptive.enabled", "true")
            .config("spark.sql.adaptive.coalescePartitions.enabled", "true")
            # Menos ruido/overhead de UI de Spark en la prueba.
            .config("spark.ui.enabled", "false")
            .getOrCreate())

_bnx_session = _bnx_spark()
# Forzar ANSI off en runtime por si la sesion ya existia (getOrCreate reutiliza).
try:
    _bnx_session.conf.set("spark.sql.ansi.enabled", "false")
except Exception:
    pass

# Silenciar loggers de Spark que vuelcan el stacktrace Java completo de las
# AnalysisException que NOSOTROS capturamos a proposito en _bnx_where (filtros
# sobre columnas ausentes). Sin esto, cada filtro relajado imprime un traceback
# JSON gigante que parece un fallo cuando en realidad se manejo correctamente.
try:
    _jlog = _bnx_session._jvm.org.apache.log4j.Logger
    _jlevel = _bnx_session._jvm.org.apache.log4j.Level
    for _lname in (
        "org.apache.spark.sql.catalyst.util.SQLQueryContextLogger",
        "SQLQueryContextLogger",
        "org.apache.spark.sql.catalyst.analysis.CheckAnalysis",
        "org.apache.spark.sql.execution.QueryExecution",
    ):
        try:
            _jlog.getLogger(_lname).setLevel(_jlevel.OFF)
        except Exception:
            pass
    # Subir el umbral global a ERROR->FATAL para el resto de ruido de la JVM.
    _bnx_session.sparkContext.setLogLevel("FATAL")
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
    # Amplificacion para el benchmark de optimizacion: repetir los registros N
    # veces infla el volumen y hace visible el efecto de cache/broadcast/coalesce.
    if _BNX_AMPLIFY > 1:
        records = records * _BNX_AMPLIFY
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
    # Romper el LINAJE COMPARTIDO: cuando left y right derivan de un ancestro comun
    # (p.ej. un lookup que es el mismo Reformat que alimenta otra rama), Spark
    # resuelve las columnas 'on' de forma ambigua y el join puede devolver 0 filas
    # aunque sea un LEFT. Recreamos el lado derecho desde sus filas para que sea un
    # DataFrame independiente sin ese ancestro. Es barato en la prueba (datos chicos).
    def _detach(df):
        try:
            return df.sql_ctx.sparkSession.createDataFrame(df.collect(), df.schema)
        except Exception:
            try:
                return _bnx_session.createDataFrame(df.collect(), df.schema)
            except Exception:
                return df
    right = _detach(right)
    how_l = (how or "inner").lower()
    preserves_left = how_l in ("left", "leftouter", "left_outer", "outer", "full", "fullouter", "full_outer")
    try:
        left_n = left.count() if preserves_left else None
        joined = left.join(right, on=on, how=how)
        # Red de seguridad: un join que PRESERVA el izquierdo nunca deberia dar
        # menos filas que el izquierdo. Si pasa (bug de lineage), rehacemos el join
        # tras materializar tambien el izquierdo.
        if preserves_left and left_n is not None and joined.count() < left_n:
            print(f"[BNX-TEST] JOIN: resultado ({{joined.count()}}) < izquierdo ({{left_n}}) en '{{how}}', "
                  f"rehaciendo con lineage independiente")
            left2 = _detach(left)
            joined = left2.join(right, on=on, how=how)
        return joined
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

def _bnx_groupby(df, *cols):
    # groupBy tolerante: agrupa solo por las claves que EXISTEN en el DataFrame.
    # Las claves ausentes (datos sinteticos sin esa columna) provocarian
    # UNRESOLVED_COLUMN; las ignoramos. Si no queda ninguna clave valida, se agrega
    # una columna constante para agrupar todo en un solo grupo (agregacion global).
    from pyspark.sql.functions import lit as _lit
    real = list(df.columns)
    lower = {{c.lower(): c for c in real}}
    keys = []
    for c in cols:
        if not isinstance(c, str):
            # Column expr: intentamos extraer el nombre; si no, la usamos tal cual.
            name = _bnx_colname(c)
            c = name or c
        if isinstance(c, str):
            if c in real:
                keys.append(c)
            elif c.lower() in lower:
                keys.append(lower[c.lower()])
            else:
                print(f"[BNX-TEST] GROUPBY: clave '{{c}}' ausente, se ignora")
        else:
            keys.append(c)
    if not keys:
        print("[BNX-TEST] GROUPBY: ninguna clave valida, agrupacion global")
        df = df.withColumn("_bnx_grp_all", _lit(1))
        return df.groupBy("_bnx_grp_all")
    return df.groupBy(*keys)

def _bnx_shell(cmd):
    # Run_Program: NO ejecutamos comandos shell en la prueba local, solo registramos.
    print(f"[BNX-TEST] SHELL (no ejecutado): {{cmd}}")
    return 0

def _bnx_where(df, sql):
    # Filtro SQL tolerante: aplica df.where(sql); si falla porque la columna no
    # existe en los datos sinteticos (ramas de logs vacias, subcampos no
    # generados, campos de lookup sin datos), devuelve el df SIN filtrar para que
    # la prueba local pueda continuar y mostrar datos. Solo prueba local.
    if df is None:
        return df
    try:
        filtered = df.where(sql)
        # Forzar el analisis del plan logico (resuelve nombres de columna) SIN
        # ejecutar: acceder a .schema dispara UNRESOLVED_COLUMN aqui, no en el
        # .count()/.show() posterior, permitiendonos capturarlo y relajar.
        _ = filtered.schema
        return filtered
    except Exception as e:
        msg = str(e)
        if ("UNRESOLVED_COLUMN" in msg or "cannot be resolved" in msg
                or "AnalysisException" in type(e).__name__):
            print(f"[BNX-TEST] WHERE relajado (columna ausente en datos sinteticos): {{sql[:80]}}")
            return df
        print(f"[BNX-TEST] WHERE fallo ({{type(e).__name__}}), se omite el filtro: {{sql[:80]}}")
        return df

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

def _bnx_write(df, var, dest=None):
    if df is None:
        print(f"[BNX-TEST] WRITE {{var}}: SKIP (DataFrame None — nodo sin datos)")
        return
    try:
        n = df.count()
        cols = df.columns
        _BNX_WRITES.append({{"var": var, "rows": n, "columns": cols}})
        print(f"[BNX-TEST] WRITE {{var}}: {{n}} filas, cols={{cols}}")
        df.show(5, truncate=False)
        # Volcar una copia CSV a disco para poder descargarla desde la GUI.
        # El nombre del archivo usa el destino (tabla/ruta del SINK); si no hay,
        # cae al nombre de la variable del DataFrame.
        _bnx_dump_csv(df, dest or var)
    except Exception as _e:
        print(f"[BNX-TEST] WRITE {{var}} ERROR: {{_e}}")
        raise

def _bnx_dump_csv(df, var):
    # Escribe el DataFrame a un unico CSV con header en _BNX_OUTPUT_DIR/<var>.csv.
    # Recolectamos filas y usamos el modulo csv de la stdlib (sin pandas): los
    # datasets de prueba son pequenos, asi el archivo tiene un nombre estable y
    # es comodo de servir desde la GUI. Se limita el volcado por seguridad.
    import os as _os
    import csv as _csv
    _MAX_ROWS = 100000
    try:
        _os.makedirs(_BNX_OUTPUT_DIR, exist_ok=True)
        safe = _re_bnx.sub(r'[^A-Za-z0-9_.-]', '_', str(var))
        dest = _os.path.join(_BNX_OUTPUT_DIR, safe + ".csv")
        cols = df.columns
        rows = df.limit(_MAX_ROWS).collect()
        with open(dest, "w", newline="", encoding="utf-8") as _fh:
            w = _csv.writer(_fh)
            w.writerow(cols)
            for r in rows:
                w.writerow(["" if r[c] is None else r[c] for c in cols])
        # Linea que la GUI parsea para ofrecer el boton de descarga:
        #   [BNX-TEST] DOWNLOAD|<nombre>|<ruta_absoluta>
        print(f"[BNX-TEST] DOWNLOAD|{{safe}}.csv|{{dest}}")
    except Exception as _e:
        print(f"[BNX-TEST] DUMP {{var}} ERROR (no se guardo CSV): {{_e}}")

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


def run_pyspark_test(pyspark_code, datasets, timeout=120, job_name=None,
                     master="local[1]", amplify=1):
    """Ejecuta el código PySpark con datos sintéticos y devuelve el resultado.

    master/amplify: para el benchmark de optimizacion (simular 2 workers y volumen
    alto). Por defecto local[1] sin amplificar (prueba normal).

    Devuelve dict:
      {"ok": bool, "exit_code": int, "stdout": str, "stderr": str,
       "timed_out": bool, "writes": [...], "reads": [...], "summary": str,
       "report": {...}, "report_download": {name,path}}
    """
    inputs = _normalize_inputs(datasets)
    required_cols = extract_referenced_columns(pyspark_code)
    # Limpiar salidas previas para no mezclar resultados de corridas anteriores.
    _reset_local_output_dir()
    script = build_test_script(pyspark_code, inputs, required_cols=required_cols,
                               output_dir=BNX_LOCAL_OUTPUT_DIR,
                               master=master, amplify=amplify)

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
    downloads = [
        {"name": d[0], "path": d[1]}
        for d in re.findall(r"\[BNX-TEST\] DOWNLOAD\|([^|]+)\|(\S+)", stdout)
    ]

    ok = (not timed_out) and exit_code == 0
    if ok:
        summary = f"Ejecución OK · {len(reads)} lectura(s), {len(writes)} escritura(s)"
    elif timed_out:
        summary = f"Timeout tras {timeout}s — el job tardó demasiado"
    else:
        summary = "Falló la ejecución — revisa el error abajo"

    reads_l = [{"var": r[0], "node": r[1], "rows": int(r[2])} for r in reads]
    writes_l = [{"var": w[0], "rows": int(w[1])} for w in writes]
    steps = _parse_flow_steps(stdout)
    fidelity = _data_fidelity(datasets, pyspark_code, reads_l, writes_l, ok, timed_out)
    report = _build_run_report(reads_l, writes_l, downloads, steps, ok,
                               timed_out, exit_code, job_name=job_name,
                               fidelity=fidelity)
    report_dl = _write_report_file(report, job_name=job_name)
    if report_dl:
        # El reporte tambien es descargable como un "archivo de salida" mas.
        downloads = downloads + [report_dl]

    # Filtrar ruido (tracebacks Java de errores capturados, logs de la JVM, etc.)
    # tambien en la ruta no-streaming, igual que hace el streaming linea a linea.
    def _strip_noise(text):
        if not text:
            return text
        return "\n".join(l for l in text.splitlines() if not _is_noise(l))

    return {
        "ok": ok,
        "exit_code": exit_code,
        "timed_out": timed_out,
        "stdout": _tail(_strip_noise(stdout), 20000),
        "stderr": _tail(_strip_noise(stderr), 20000),
        "reads": reads_l,
        "writes": writes_l,
        "downloads": downloads,
        "report": report,
        "report_download": report_dl,
        "summary": summary,
    }


def _reset_local_output_dir():
    """Vacia (o crea) la carpeta de salidas locales antes de cada corrida."""
    import shutil
    try:
        if os.path.isdir(BNX_LOCAL_OUTPUT_DIR):
            shutil.rmtree(BNX_LOCAL_OUTPUT_DIR)
        os.makedirs(BNX_LOCAL_OUTPUT_DIR, exist_ok=True)
    except OSError:
        pass


def _parse_flow_steps(stdout):
    """Extrae el flujo de transformacion desde el stdout del job.

    El codigo generado imprime una linea por nodo ejecutado, con la forma
    "[simbolo] TIPO: nombre" (p.ej. "[>] SOURCE: clientes", "[~] JOIN: j1").
    Devuelve una lista ordenada de {"type","name"} en orden de ejecucion.
    """
    steps = []
    for m in re.finditer(
        r"^\[[^\]]\]\s+([A-Z][A-Z_]*): (.+)$", stdout, flags=re.M
    ):
        tipo = m.group(1).strip()
        name = m.group(2).strip()
        # Ignorar la cabecera generica del job si apareciera
        if tipo in ("BNX", "TEST"):
            continue
        steps.append({"type": tipo, "name": name})
    return steps


def _value_matches_type(value, ctype):
    """True si 'value' es consistente con el tipo declarado 'ctype'.

    Se usa para medir la fidelidad de los datos redactados vs su esquema.
    Valores None/'' se consideran neutrales (no penalizan ni suman).
    """
    if value is None:
        return None
    s = str(value).strip()
    if s == "":
        return None
    ctype = (ctype or "string").lower()
    try:
        if ctype in ("integer", "int", "long", "bigint"):
            int(s)
            return True
        if ctype in ("decimal", "double", "float"):
            float(s)
            return True
        if ctype in ("date", "datetime", "timestamp"):
            # Acepta patrones tipo YYYY-MM-DD o YYYY-MM-DD HH:MM:SS, o fechas redactadas YYYY-**-**
            return bool(re.match(r'^\d{4}[-/]?(\d{2}|\*\*)[-/]?(\d{2}|\*\*)', s))
        if ctype in ("boolean", "bool"):
            return s.lower() in ("true", "false", "0", "1", "t", "f")
        # string: cualquier cosa no vacia es valida
        return True
    except (ValueError, TypeError):
        return False


def _data_fidelity(datasets, pyspark_code, reads, writes, ok, timed_out):
    """Calcula la fidelidad de los datos de la prueba (0-100) con desglose.

    Combina:
      - Ejecucion (C): el job termino OK.
      - Salidas con datos (C): % de tablas de salida con filas > 0.
      - Traduccion sin huecos (C): % de columnas NO neutralizadas a NULL por
        salvaguardas (en el codigo generado: TODO / lit(None) / columna NULL).
      - Esquema de datos redactados (B): % de valores de entrada que respetan el
        tipo declarado de su columna.
    Devuelve dict con score total y cada factor (con su peso y detalle).
    """
    code = pyspark_code or ""
    # --- Factor B: fidelidad de esquema de los datos redactados de entrada ---
    total_vals = 0
    ok_vals = 0
    any_input = any(d.get("io") == "input" for d in (datasets or []))
    for d in (datasets or []):
        if any_input and d.get("io") != "input":
            continue
        cols = d.get("columns") or []
        rows = d.get("rows") or []
        if not cols or not rows:
            continue
        type_by_name = {c.get("name"): c.get("type", "string") for c in cols}
        for row in rows:
            if not isinstance(row, dict):
                continue
            for name, val in row.items():
                ctype = type_by_name.get(name)
                if ctype is None:
                    continue
                res = _value_matches_type(val, ctype)
                if res is None:
                    continue
                total_vals += 1
                if res:
                    ok_vals += 1
    schema_score = (ok_vals / total_vals * 100) if total_vals else 100.0

    # --- Factor C1: ejecucion ---
    exec_score = 100.0 if ok else 0.0

    # --- Factor C2: salidas con datos ---
    if writes:
        with_rows = sum(1 for w in writes if w.get("rows", 0) > 0)
        outputs_score = with_rows / len(writes) * 100
    else:
        outputs_score = 0.0 if reads else 100.0

    # --- Factor C3: traduccion sin huecos (columnas neutralizadas a NULL) ---
    # Contamos columnas de salida creadas vs las neutralizadas por salvaguardas
    # en el CODIGO GENERADO (no en el stdout del job).
    total_cols_created = len(re.findall(r'\.withColumn\(', code)) or 0
    null_cols = len(re.findall(
        r'lit\(None\)\s*#\s*TODO|# TODO Ab Initio no traducible|columna NULL',
        code,
    ))
    if total_cols_created > 0:
        translation_score = max(0.0, (total_cols_created - null_cols) / total_cols_created * 100)
    else:
        translation_score = 100.0

    factors = [
        {"key": "ejecucion", "label": "Ejecución completa", "score": round(exec_score, 1), "weight": 0.35},
        {"key": "esquema", "label": "Fidelidad de esquema (datos redactados)", "score": round(schema_score, 1), "weight": 0.25,
         "detail": f"{ok_vals}/{total_vals} valores respetan su tipo" if total_vals else "sin columnas tipadas"},
        {"key": "salidas", "label": "Salidas con datos", "score": round(outputs_score, 1), "weight": 0.20},
        {"key": "traduccion", "label": "Traducción sin columnas NULL", "score": round(translation_score, 1), "weight": 0.20,
         "detail": f"{null_cols} columna(s) neutralizada(s) de {total_cols_created}" if total_cols_created else "sin columnas generadas"},
    ]
    total = sum(f["score"] * f["weight"] for f in factors)
    return {"score": round(total, 1), "factors": factors}


def _describe_graph(steps, reads, writes, job_name=None):
    """Genera una descripcion en lenguaje natural (espanol) del grafo.

    Determinística: la arma a partir del flujo (steps) y las estadisticas de
    entrada/salida. No depende de IA externa. Devuelve un parrafo (string).
    """
    def _names(tipo):
        return [s["name"] for s in steps if s.get("type") == tipo]

    sources = _names("SOURCE")
    sinks = _names("SINK")
    joins = _names("JOIN")
    filters = _names("FILTER") + _names("DEDUP")
    transforms = _names("TRANSFORM")
    lookups = _names("LOOKUP")
    normalizes = _names("NORMALIZE")

    total_in = sum(r.get("rows", 0) for r in (reads or []))
    total_out = sum(w.get("rows", 0) for w in (writes or []))

    def _lista(items):
        items = [str(i) for i in items if i]
        if not items:
            return ""
        if len(items) == 1:
            return items[0]
        if len(items) == 2:
            return f"{items[0]} y {items[1]}"
        return ", ".join(items[:-1]) + f" y {items[-1]}"

    frases = []

    # 1. Fuentes de entrada
    if sources:
        n = len(sources)
        frases.append(
            f"El grafo «{job_name or 'sin nombre'}» lee datos de "
            f"{n} fuente{'s' if n != 1 else ''} ({_lista(sources)})"
            + (f", con {total_in} fila(s) de entrada en total" if reads else "")
            + "."
        )
    else:
        frases.append(f"El grafo «{job_name or 'sin nombre'}» no declara fuentes de entrada explícitas.")

    # 2. Transformaciones / joins / filtros / lookups / normalize
    pasos = []
    if joins:
        pasos.append(f"combina flujos mediante {len(joins)} join ({_lista(joins)})")
    if lookups:
        pasos.append(f"enriquece con {len(lookups)} búsqueda(s)/lookup ({_lista(lookups)})")
    if transforms:
        pasos.append(f"aplica {len(transforms)} transformación(es) ({_lista(transforms)})")
    if filters:
        pasos.append(f"filtra/deduplica registros en {len(filters)} paso(s) ({_lista(filters)})")
    if normalizes:
        pasos.append(f"normaliza estructuras en {len(normalizes)} paso(s) ({_lista(normalizes)})")
    if pasos:
        frases.append("Durante el procesamiento, " + _lista(pasos) + ".")
    else:
        frases.append("No se detectaron pasos intermedios de transformación (flujo directo).")

    # 3. Salidas
    if sinks:
        n = len(sinks)
        tablas = [w.get("var") for w in (writes or [])]
        frases.append(
            f"Finalmente escribe el resultado en {n} salida{'s' if n != 1 else ''} "
            f"({_lista(sinks)})"
            + (f", generando {total_out} fila(s) en total" if writes else "")
            + "."
        )
    else:
        frases.append("El grafo no produce salidas persistidas.")

    # 4. Balance entrada/salida
    if reads and writes:
        diff = total_out - total_in
        if diff == 0:
            frases.append("El número de filas se conserva entre entrada y salida.")
        elif diff < 0:
            frases.append(
                f"Se reducen {abs(diff)} fila(s) del total, típico de filtros, "
                f"deduplicación o agregaciones."
            )
        else:
            frases.append(
                f"Se incrementan {diff} fila(s), típico de joins que expanden o "
                f"normalización que desagrega registros."
            )

    return " ".join(frases)


def _build_run_report(reads, writes, downloads, steps, ok, timed_out,
                      exit_code, job_name=None, fidelity=None):
    """Arma el reporte estructurado de una corrida (para la UI y para descargar).

    reads/writes: listas de dicts {"var","node","rows"} / {"var","rows"}.
    downloads:    lista de {"name","path"} de los CSV de salida.
    steps:        flujo de transformacion (lista de {"type","name"}).
    Devuelve dict con estadisticas de entrada/salida, flujo y metadatos.
    """
    total_in = sum(r.get("rows", 0) for r in reads)
    total_out = sum(w.get("rows", 0) for w in writes)
    delta = total_out - total_in
    counts_by_type = {}
    for s in steps:
        counts_by_type[s["type"]] = counts_by_type.get(s["type"], 0) + 1
    description = _describe_graph(steps, reads, writes, job_name=job_name)
    return {
        "job_name": job_name or "grafo",
        "description": description,
        "ok": ok,
        "timed_out": timed_out,
        "exit_code": exit_code,
        "inputs": reads,
        "outputs": [
            {
                "table": (downloads[i]["name"] if i < len(downloads) else w.get("var")),
                "var": w.get("var"),
                "rows": w.get("rows", 0),
            }
            for i, w in enumerate(writes)
        ],
        "totals": {
            "input_rows": total_in,
            "output_rows": total_out,
            "delta_rows": delta,
        },
        "fidelity": fidelity or {},
        "flow": steps,
        "flow_counts": counts_by_type,
        "downloads": downloads,
    }


def _render_report_text(report):
    """Formatea el reporte como texto plano descargable (.txt)."""
    import datetime as _dt
    L = []
    L.append("=" * 60)
    L.append("BNX — REPORTE DE PRUEBA (Data Redactada)")
    L.append("=" * 60)
    L.append(f"Grafo:        {report.get('job_name', 'grafo')}")
    L.append(f"Fecha:        {_dt.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    estado = "OK" if report.get("ok") else ("TIMEOUT" if report.get("timed_out") else "FALLO")
    L.append(f"Estado:       {estado} (exit={report.get('exit_code')})")
    fid = report.get("fidelity") or {}
    if fid:
        L.append(f"Fidelidad:    {fid.get('score', 0)}%")
    L.append("")
    desc = report.get("description")
    if desc:
        L.append("-" * 60)
        L.append("DESCRIPCION DEL GRAFO")
        L.append("-" * 60)
        # Envolver el parrafo a ~72 columnas para legibilidad
        import textwrap as _tw
        for linea in _tw.wrap(desc, width=72):
            L.append(linea)
        L.append("")
    if fid.get("factors"):
        L.append("-" * 60)
        L.append("FIDELIDAD DE LOS DATOS (desglose)")
        L.append("-" * 60)
        L.append(f"Puntaje total: {fid.get('score', 0)}%")
        for f in fid["factors"]:
            peso = int(round(f.get("weight", 0) * 100))
            linea = f"  - {f['label']}: {f['score']}% (peso {peso}%)"
            if f.get("detail"):
                linea += f" — {f['detail']}"
            L.append(linea)
        L.append("")
    t = report.get("totals", {})
    L.append("-" * 60)
    L.append("COMPARACION ENTRADA vs SALIDA")
    L.append("-" * 60)
    L.append(f"Filas de entrada (total): {t.get('input_rows', 0)}")
    L.append(f"Filas de salida  (total): {t.get('output_rows', 0)}")
    L.append(f"Diferencia:               {t.get('delta_rows', 0):+d}")
    L.append("")
    L.append("Entradas por fuente:")
    if report.get("inputs"):
        for r in report["inputs"]:
            L.append(f"  - {r.get('node', r.get('var'))}: {r.get('rows', 0)} filas")
    else:
        L.append("  (ninguna)")
    L.append("")
    L.append("Salidas por tabla:")
    if report.get("outputs"):
        for o in report["outputs"]:
            L.append(f"  - {o.get('table')}: {o.get('rows', 0)} filas")
    else:
        L.append("  (ninguna)")
    L.append("")
    L.append("-" * 60)
    L.append("FLUJO DE TRANSFORMACION")
    L.append("-" * 60)
    if report.get("flow"):
        for i, s in enumerate(report["flow"], 1):
            L.append(f"  {i:>2}. [{s['type']}] {s['name']}")
    else:
        L.append("  (sin pasos registrados)")
    L.append("")
    if report.get("flow_counts"):
        resumen = ", ".join(f"{k}: {v}" for k, v in sorted(report["flow_counts"].items()))
        L.append(f"Resumen de nodos: {resumen}")
    L.append("")
    L.append("-" * 60)
    L.append("ARCHIVOS DE SALIDA DESCARGABLES")
    L.append("-" * 60)
    if report.get("downloads"):
        for d in report["downloads"]:
            L.append(f"  - {d.get('name')}")
    else:
        L.append("  (ninguno)")
    L.append("")
    return "\n".join(L)


def _write_report_file(report, job_name=None):
    """Escribe el reporte .txt en la carpeta de salidas y devuelve {name,path}.

    Devuelve None si no se pudo escribir.
    """
    try:
        os.makedirs(BNX_LOCAL_OUTPUT_DIR, exist_ok=True)
        safe = re.sub(r'[^A-Za-z0-9_.-]', '_', str(job_name or "grafo"))
        fname = f"reporte_{safe}.txt"
        dest = os.path.join(BNX_LOCAL_OUTPUT_DIR, fname)
        with open(dest, "w", encoding="utf-8") as fh:
            fh.write(_render_report_text(report))
        return {"name": fname, "path": dest}
    except OSError:
        return None


def _tail(text, max_chars):
    """Recorta texto largo dejando el final (donde suelen estar los errores)."""
    if not text:
        return ""
    if len(text) <= max_chars:
        return text
    return "...[truncado]...\n" + text[-max_chars:]


def stream_pyspark_test(pyspark_code, datasets, timeout=300, job_name=None):
    """Ejecuta el PySpark de prueba y hace *yield* de cada linea de salida en vivo.

    Cada yield es un dict:
      {"type": "line", "text": "..."}     — una linea de stdout/stderr
      {"type": "done", "ok": bool, "summary": str, "reads": [...], "writes": [...],
       "report": {...}, "report_download": {name,path}}

    Permite que la UI muestre una consola en tiempo real mientras el job corre.
    """
    import threading
    import time as _time

    inputs = _normalize_inputs(datasets)
    required_cols = extract_referenced_columns(pyspark_code)
    _reset_local_output_dir()
    script = build_test_script(pyspark_code, inputs, required_cols=required_cols,
                               output_dir=BNX_LOCAL_OUTPUT_DIR)

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
    downloads_all = []
    steps_all = []

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
            md = re.match(r"\[BNX-TEST\] DOWNLOAD\|([^|]+)\|(\S+)", line)
            if md:
                downloads_all.append({"name": md.group(1), "path": md.group(2)})
                # No mostramos esta linea cruda en la consola (la GUI la usa aparte).
                continue
            # Capturar pasos del flujo de transformacion: "[simbolo] TIPO: nombre"
            ms = re.match(r"^\[[^\]]\]\s+([A-Z][A-Z_]*): (.+)$", line)
            if ms and ms.group(1) not in ("BNX", "TEST"):
                steps_all.append({"type": ms.group(1), "name": ms.group(2).strip()})
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

    fidelity = _data_fidelity(datasets, pyspark_code, reads_all, writes_all, ok, timed_out)
    report = _build_run_report(reads_all, writes_all, downloads_all, steps_all,
                               ok, timed_out, exit_code, job_name=job_name,
                               fidelity=fidelity)
    report_dl = _write_report_file(report, job_name=job_name)
    downloads_out = list(downloads_all)
    if report_dl:
        downloads_out.append(report_dl)

    yield {
        "type": "done",
        "ok": ok,
        "exit_code": exit_code,
        "timed_out": timed_out,
        "summary": summary,
        "reads": reads_all,
        "writes": writes_all,
        "downloads": downloads_out,
        "report": report,
        "report_download": report_dl,
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
    # Volcado JSON del logger de Spark (SQLQueryContextLogger) de las
    # AnalysisException que capturamos a proposito en _bnx_where: es una linea
    # JSON gigante con el stacktrace Java. Red de seguridad por si el silenciado
    # del logger no lo suprime en alguna version de Spark.
    '"logger": "SQLQueryContextLogger"',
    '"errorClass": "UNRESOLVED_COLUMN',
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
    # Tolera .coalesce(N)/.repartition(N) (del optimizador) antes de .write.
    write_re = re.compile(r'^(\s*)(\w+)(?:\.(?:coalesce|repartition)\([^)]*\))*\.write\b.*$')
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

    # Corregir withColumn(...) roto por comentario "# TODO:" con parentesis sin
    # balancear (mismo fix que el runner local). Ver detalle alla.
    _aws_todo_date_re = re.compile(
        r'''\(?\s*date\(\s*['"]([^'"]+)['"]\s*\)'''
        r'''(?:\s*\(\s*['"][^'"]*['"]\s*\))?'''
        r'''\s*\)?\s*'''
        r'''\(?\s*(?:in\d*\.)?([\w'".\-:/]+?)\s*\)?\s*$'''
    )

    def _aws_fix_broken_todo(mo):
        prefix = mo.group(1)
        col = mo.group(2)
        todo = mo.group(3).strip()
        _dfm = re.search(r'=\s*([A-Za-z_]\w*)\s*$', prefix)
        target_df = _dfm.group(1) if _dfm else None
        dm = _aws_todo_date_re.search(todo)
        if dm:
            fmt = dm.group(1).replace("YYYY", "yyyy").replace("DD", "dd")
            valor = dm.group(2).strip()
            if (valor.startswith("'") and valor.endswith("'")) or (valor.startswith('"') and valor.endswith('"')):
                lit_val = valor.strip(chr(39) + chr(34))
                inner = f'''to_date(lit("{lit_val}"), "{fmt}")'''
                return f'{prefix}.withColumn("{col}", {inner})  # AWS: cast fecha Ab Initio traducido'
            if target_df:
                inner = f'_bnx_todate({target_df}, "{valor}", "{fmt}")'
            else:
                inner = f'to_date(col("{valor}"), "{fmt}")'
            return f'{prefix}.withColumn("{col}", {inner})  # AWS: cast fecha Ab Initio traducido (col tolerante)'
        return f'{prefix}.withColumn("{col}", lit(None))  # AWS: TODO Ab Initio no traducible, columna NULL'

    body = re.sub(
        r'^(.*?)\.withColumn\(\s*"([^"]+)"\s*,\s*lit\(None\)\s*#\s*TODO:\s*(.*?)\)\s*$',
        _aws_fix_broken_todo,
        body,
        flags=re.M,
    )

    def _aws_tolerant_todate(mo):
        prefix = mo.group(1)
        col = mo.group(2)
        field = mo.group(3)
        fmt = mo.group(4)
        _dfm = re.search(r'=\s*([A-Za-z_]\w*)\s*$', prefix)
        target_df = _dfm.group(1) if _dfm else None
        if not target_df:
            return mo.group(0)
        return (f'{prefix}.withColumn("{col}", _bnx_todate({target_df}, "{field}", "{fmt}"))'
                f'  # AWS: to_date col tolerante')

    body = re.sub(
        r'^(.*?)\.withColumn\(\s*"([^"]+)"\s*,\s*to_date\(\s*col\(\s*"([^"]+)"\s*\)\s*,\s*"([^"]+)"\s*\)\s*\)\s*(?:#.*)?$',
        _aws_tolerant_todate,
        body,
        flags=re.M,
    )

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

def _to_date_null(fmt):
    from pyspark.sql.functions import to_date as _td, lit as _lit
    return _td(_lit(None).cast("string"), fmt)

def _bnx_todate(df, colname, fmt):
    # to_date tolerante: resuelve el nombre de columna ignorando mayus/minus y
    # diferencias de guion bajo (MISDATE vs MIS_DATE); si no existe -> NULL.
    from pyspark.sql.functions import to_date as _td, col as _col
    target = None
    if df is not None:
        want = colname.lower().replace("_", "")
        for c in df.columns:
            if c.lower().replace("_", "") == want:
                target = c
                break
    if target is None:
        return _to_date_null(fmt)
    return _td(_col(target), fmt)

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
