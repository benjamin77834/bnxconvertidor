# py2spark.schema — inferencia de esquema de ENTRADA desde codigo PySpark.
#
# Data Redactada (datagen) sabe generar datos sinteticos a partir de un esquema
# {columns:[{name,type,pii}]}. Para un job PySpark que NO viene de un grafo .mp,
# aqui inferimos ese esquema analizando el codigo: por cada fuente de lectura
# (una variable asignada desde spark.read.*), detectamos las columnas que el job
# referencia y un tipo aproximado por como se usan (comparaciones numericas,
# aritmetica, casts). El resultado alimenta el modo "manual" de /datagen.
#
# No pretende ser exacto: el harness de prueba rellena columnas faltantes con
# null y castea segun el propio codigo. La meta es que la ejecucion local tenga
# datos con las columnas correctas y tipos razonables para no dar 0 filas.

import ast
import re


# Palabras que NO son columnas (funciones/keywords SQL y de PySpark).
_NON_COLUMN = {
    "and", "or", "not", "is", "null", "true", "false", "in", "like", "rlike",
    "between", "case", "when", "then", "else", "end", "as", "asc", "desc",
    "cast", "int", "bigint", "double", "float", "string", "decimal", "date",
    "timestamp", "boolean", "coalesce", "sum", "avg", "min", "max", "count",
    "col", "lit", "expr", "when", "F", "select", "distinct",
}


def _numeric_hint(col, code):
    """True si la columna se compara/opera aritmeticamente (=> numerica)."""
    patterns = [
        rf"col\(['\"]{re.escape(col)}['\"]\)\s*[<>]=?",       # F.col('x') > ...
        rf"col\(['\"]{re.escape(col)}['\"]\)\s*[-+*/]",       # F.col('x') - ...
        rf"[-+*/]\s*F?\.?col\(['\"]{re.escape(col)}['\"]\)",  # ... - F.col('x')
        rf"sum\(['\"]{re.escape(col)}['\"]\)",                # F.sum('x')
        rf"avg\(['\"]{re.escape(col)}['\"]\)",
    ]
    return any(re.search(p, code) for p in patterns)


def _detect_pii(name):
    """Heuristica simple de PII por nombre de columna (es/en)."""
    n = name.lower()
    keys = ("nombre", "name", "apellido", "email", "correo", "telefono", "phone",
            "rfc", "curp", "ssn", "dni", "cuenta", "account", "tarjeta", "card",
            "direccion", "address", "cliente", "customer", "cvv", "password", "clabe")
    return any(k in n for k in keys)


def _read_var_names(tree):
    """Nombres de variables asignadas desde una LECTURA de Spark.

    Reconoce las formas comunes que producen un DataFrame de entrada:
      X = spark.read.<fmt>(...)              (con .option(...) intermedios)
      X = spark.read.format(...).load(...)
      X = spark.table("t") / spark.sql("...")
      X = spark.createDataFrame(...)         (datos ya embebidos: tambien es fuente)
    """
    names = []
    for node in ast.walk(tree):
        if not (isinstance(node, ast.Assign) and len(node.targets) == 1
                and isinstance(node.targets[0], ast.Name)):
            continue
        val = node.value
        cur = val
        seen_read = False
        direct_reader = False   # spark.table / spark.sql / spark.createDataFrame
        while isinstance(cur, (ast.Attribute, ast.Call)):
            if isinstance(cur, ast.Attribute):
                if cur.attr == "read":
                    seen_read = True
                if cur.attr in ("table", "sql", "createDataFrame") \
                        and isinstance(cur.value, ast.Name) and cur.value.id == "spark":
                    direct_reader = True
                cur = cur.value
            else:
                cur = cur.func
        root_is_spark = isinstance(cur, ast.Name) and cur.id == "spark"
        if root_is_spark and (seen_read or direct_reader):
            names.append(node.targets[0].id)
    return names


def _referenced_columns(code):
    """Todas las columnas referenciadas en el codigo (por nombre)."""
    cols = set()
    for m in re.findall(r'(?:F\.)?col\(\s*["\'](\w+)["\']\s*\)', code):
        cols.add(m)
    for m in re.findall(r'withColumn\(\s*["\'](\w+)["\']', code):
        cols.add(m)
    for m in re.findall(r'(?:alias|withColumnRenamed)\(\s*["\'](\w+)["\']', code):
        cols.add(m)
    for fn in ("groupBy", "orderBy", "sort", "select", "selectExpr", "drop", "dropDuplicates"):
        for block in re.findall(rf'\.{fn}\(([^)]*)\)', code):
            for m in re.findall(r'["\'](\w+)["\']', block):
                cols.add(m)
    for block in re.findall(r'on\s*=\s*\[([^\]]*)\]', code):
        for m in re.findall(r'["\'](\w+)["\']', block):
            cols.add(m)
    for m in re.findall(r'on\s*=\s*["\'](\w+)["\']', code):
        cols.add(m)
    # agregaciones F.sum('x') etc.
    for m in re.findall(r'(?:sum|avg|min|max|count|stddev|variance)\(\s*["\'](\w+)["\']', code):
        cols.add(m)

    # Columnas de ENTRADA usadas por el MLlib generado: StringIndexer/Scaler/etc.
    # con inputCol="x" y VectorAssembler(inputCols=[...]). OJO: excluimos las
    # columnas DERIVADAS por el pipeline (las que aparecen como outputCol, mas
    # 'features'/'scaled_features' y sufijos _idx/_ohe/_scaled), que NO existen
    # en el dataset de entrada.
    derived = set()
    for m in re.findall(r'outputCol\s*=\s*["\'](\w+)["\']', code):
        derived.add(m)
    for m in re.findall(r'inputCol\s*=\s*["\'](\w+)["\']', code):
        cols.add(m)
    for block in re.findall(r'inputCols\s*=\s*\[([^\]]*)\]', code):
        for m in re.findall(r'["\'](\w+)["\']', block):
            cols.add(m)
    # descartar derivadas y sufijos tipicos de features/salidas de MLlib. Las
    # columnas de SALIDA del pipeline (prediction/probability/rawPrediction/
    # label_indexed) NO existen en el dataset de entrada; si las dejaramos, los
    # datos sinteticos tendrian solo derivadas y el job no tendria features.
    _ml_out = ("features", "scaled_features", "raw_features", "prediction",
               "probability", "rawprediction", "label_indexed")
    def _is_derived(c):
        lc = c.lower()
        return (c in derived or lc in _ml_out
                or lc.endswith(("_idx", "_ohe", "_scaled", "_vec", "_features")))
    return {c for c in cols
            if c.lower() not in _NON_COLUMN and not c.isdigit() and not _is_derived(c)}


def infer_input_schema(code, n_default_cols=3):
    """Infiere el esquema de ENTRADA desde codigo PySpark.

    Devuelve una lista de datasets-esquema (uno por fuente de lectura):
      [{"node": "<var_sin _df>", "node_type": "SOURCE", "io": "input",
        "columns": [{"name","type","pii"}]}]

    Estrategia: recolecta TODAS las columnas referenciadas y las asigna a CADA
    fuente de lectura (el harness ignora columnas de mas y rellena las que falten
    con null). El tipo se infiere por uso (numerico si hay comparacion/aritmetica
    /agregacion; string en otro caso).
    """
    try:
        tree = ast.parse(code)
    except SyntaxError:
        return []

    read_vars = _read_var_names(tree)
    all_cols = _referenced_columns(code)

    # ¿Es un job MLlib supervisado (clasificacion/regresion)? Si lo es y solo se
    # detecto 'label' (u otra columna objetivo), el dataset NO tendria columnas de
    # features y el VectorAssembler fallaria. Anadimos features numericas
    # sinteticas para que el modelo tenga con que entrenar.
    _is_supervised_ml = bool(re.search(
        r'labelCol|RandomForestClassifier|LogisticRegression|GBTClassifier|'
        r'DecisionTreeClassifier|LinearRegression|RandomForestRegressor|'
        r'MulticlassClassificationEvaluator', code))
    _label_like = {"label", "label_indexed", "churn", "target", "y"}

    def _mk_cols():
        out = []
        for c in sorted(all_cols):
            ctype = "decimal" if _numeric_hint(c, code) else "string"
            out.append({"name": c, "type": ctype, "pii": _detect_pii(c)})
        # Job ML supervisado sin features reales (solo label/derivadas): anadir
        # 3 columnas de features numericas sinteticas para que el modelo entrene.
        if _is_supervised_ml:
            _non_label = [c for c in all_cols if c.lower() not in _label_like]
            if not _non_label:
                for i in range(3):
                    out.append({"name": f"feature{i+1}", "type": "decimal", "pii": False})
        # si no se detecto ninguna columna, poner unas genericas para no dar vacio
        if not out:
            out = [{"name": f"col{i+1}", "type": "string", "pii": False}
                   for i in range(n_default_cols)]
        return out

    datasets = []
    seen = set()
    for var in read_vars:
        node = var[:-3] if var.lower().endswith("_df") else var
        key = node.lower()
        if key in seen:
            continue
        seen.add(key)
        datasets.append({
            "node": node,
            "node_type": "SOURCE",
            "io": "input",
            "columns": _mk_cols(),
        })

    # FALLBACK: no se detecto ninguna fuente de lectura (spark.read.*), pero el
    # codigo SI referencia columnas. En vez de dejar 0 datasets (y bloquear Data
    # Redactada), generamos un dataset generico 'input' con esas columnas. El
    # harness empareja por nombre de variable; si no empata exacto, igual provee
    # datos con las columnas correctas para que el job pueda ejecutar.
    if not datasets and all_cols:
        datasets.append({
            "node": "input",
            "node_type": "SOURCE",
            "io": "input",
            "columns": _mk_cols(),
        })

    # RED DE SEGURIDAD (regex): si el AST no capturo la fuente pero el texto tiene
    # una asignacion 'X = spark.read...' / spark.table / spark.sql, la tomamos por
    # regex. Cubre variaciones de formato que el walk del AST pudo no reconocer.
    if not datasets:
        for m in re.finditer(r'(\w+)\s*=\s*spark\s*\.\s*(?:read\b|table\s*\(|sql\s*\(|createDataFrame\s*\()', code):
            var = m.group(1)
            node = var[:-3] if var.lower().endswith("_df") else var
            if node.lower() in seen:
                continue
            seen.add(node.lower())
            datasets.append({
                "node": node, "node_type": "SOURCE", "io": "input",
                "columns": _mk_cols(),
            })

    # ULTIMO RECURSO: es un job PySpark generado por py2spark (tiene el marcador o
    # SparkSession) pero no se detecto ninguna fuente. En vez de bloquear Data
    # Redactada, generamos un dataset generico para que el job pueda ejecutar.
    if not datasets and ("py2spark" in code or "SparkSession" in code):
        datasets.append({
            "node": "input", "node_type": "SOURCE", "io": "input",
            "columns": _mk_cols(),
        })
    return datasets
