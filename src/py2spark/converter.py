# py2spark.converter — nucleo de conversion Python (pandas) -> PySpark 3.
#
# Estrategia: parsear el codigo a AST, detectar los "nombres" que son DataFrames
# de pandas (por asignaciones desde pd.read_* o desde operaciones de otro df) y
# reescribir las construcciones idiomaticas de pandas a PySpark:
#
#   pd.read_csv("f.csv")            -> spark.read.option("header",True).option("inferSchema",True).csv("f.csv")
#   pd.read_parquet("f")           -> spark.read.parquet("f")
#   df[df["x"] > 0]                -> df.filter(F.col("x") > 0)
#   df["x"]                        -> F.col("x")            (dentro de expresiones)
#   df["y"] = expr                 -> df = df.withColumn("y", expr)
#   df.groupby("k").agg(...)       -> df.groupBy("k").agg(...)
#   df.merge(o, on="k", how=...)   -> df.join(o, on="k", how=...)
#   df.drop(columns=[...])         -> df.drop(...)
#   df.rename(columns={a:b})       -> df.withColumnRenamed(a,b)...
#   df.sort_values("x", asc=False) -> df.orderBy(F.col("x").desc())
#   df.head(n) / df.limit(n)       -> df.limit(n)
#   df.fillna(v) / dropna()        -> df.fillna(v) / df.dropna()
#   df.to_csv("o") / to_parquet    -> df.write...csv("o") / parquet("o")
#   len(df) / df.shape[0]          -> df.count()
#
# Lo no soportado (apply con lambda arbitraria, iterrows, loops sobre filas,
# numpy elementwise, etc.) se deja igual y se anota un TODO.

import ast
import re

from . import mllib as _mllib


# --------- utilidades de deteccion ---------

_PANDAS_READERS = {
    "read_csv": "csv",
    "read_parquet": "parquet",
    "read_json": "json",
    "read_table": "csv",
    "read_orc": "orc",
    # read_excel no tiene equivalente nativo en Spark; lo mapeamos a CSV como
    # aproximacion (Spark no lee .xlsx sin el conector com.crealytics.spark.excel).
    # Se avisa en warnings. Mejor una fuente detectable que dejar pd.read_excel crudo.
    "read_excel": "csv",
}

# Metodos que devuelven otro DataFrame (para propagar el "es df").
_DF_RETURNING = {
    "filter", "select", "where", "groupby", "groupBy", "agg", "merge", "join",
    "drop", "rename", "sort_values", "orderBy", "sort", "head", "limit",
    "fillna", "dropna", "withColumn", "withColumnRenamed", "distinct",
    "drop_duplicates", "assign", "copy", "reset_index", "tail", "sample",
    "union", "unionByName", "withColumnRenamed",
}

# Agregaciones pandas -> funciones F.
_AGG_MAP = {
    "sum": "sum", "mean": "avg", "avg": "avg", "min": "min", "max": "max",
    "count": "count", "std": "stddev", "var": "variance", "median": "percentile_approx",
    "nunique": "countDistinct", "first": "first", "last": "last",
}


# Modulos de ML cuyo entrenamiento NO se traduce 1:1 a Spark (se usa MLlib).
_ML_MODULES = ("sklearn", "xgboost", "lightgbm", "catboost", "tensorflow",
               "keras", "torch", "statsmodels")

# Nombres de clases/funciones ML tipicas (para detectar uso sin import explicito).
_ML_CALLABLES = {
    "train_test_split", "cross_val_score", "GridSearchCV", "StandardScaler",
    "MinMaxScaler", "LabelEncoder", "OneHotEncoder", "LogisticRegression",
    "LinearRegression", "RandomForestClassifier", "RandomForestRegressor",
    "GradientBoostingClassifier", "DecisionTreeClassifier", "KMeans", "SVC",
    "XGBClassifier", "XGBRegressor", "LGBMClassifier", "Pipeline",
}

# Cargadores de datasets de sklearn: NO tienen equivalente en Spark (los datos
# vienen de una fuente real: CSV/parquet/tabla). Los reconocemos para traducirlos
# a un spark.read con TODO, y NO dejarlos crudos (que daria NameError al borrar
# el import 'from sklearn.datasets import ...').
_ML_DATA_LOADERS = {
    "fetch_openml", "fetch_california_housing", "fetch_covtype", "fetch_20newsgroups",
    "load_iris", "load_digits", "load_wine", "load_breast_cancer", "load_diabetes",
    "load_boston", "load_linnerud", "make_classification", "make_regression",
    "make_blobs", "make_moons", "make_circles",
}

# Sugerencia de equivalente en Spark MLlib por clase sklearn.
_MLLIB_HINT = {
    "LogisticRegression": "pyspark.ml.classification.LogisticRegression",
    "LinearRegression": "pyspark.ml.regression.LinearRegression",
    "RandomForestClassifier": "pyspark.ml.classification.RandomForestClassifier",
    "RandomForestRegressor": "pyspark.ml.regression.RandomForestRegressor",
    "GradientBoostingClassifier": "pyspark.ml.classification.GBTClassifier",
    "DecisionTreeClassifier": "pyspark.ml.classification.DecisionTreeClassifier",
    "KMeans": "pyspark.ml.clustering.KMeans",
    "StandardScaler": "pyspark.ml.feature.StandardScaler (+ VectorAssembler)",
    "MinMaxScaler": "pyspark.ml.feature.MinMaxScaler (+ VectorAssembler)",
    "OneHotEncoder": "pyspark.ml.feature.StringIndexer + OneHotEncoder",
    "train_test_split": "df.randomSplit([0.8, 0.2], seed=42)",
    "get_dummies": "pyspark.ml.feature.StringIndexer + OneHotEncoder",
}


def _is_ml_module(mod):
    mod = (mod or "").split(".")[0]
    return mod in _ML_MODULES


def _names_in_target(tgt):
    """Nombres de variable simples de un target de asignacion.

    - Name           -> [id]
    - Tuple/List      -> nombres de sus elementos Name
    - Subscript (df[cols]) u otros -> [] (sin nombre simple)
    """
    if isinstance(tgt, ast.Name):
        return [tgt.id]
    if isinstance(tgt, (ast.Tuple, ast.List)):
        out = []
        for e in tgt.elts:
            if isinstance(e, ast.Name):
                out.append(e.id)
        return out
    return []


# Accesos de pandas basados en el INDICE de fila / posicion. Spark no tiene
# indice de fila, asi que estos no son traducibles 1:1.
_PANDAS_INDEX_ATTRS = {"loc", "iloc", "ix", "at", "iat", "index", "values", "reset_index", "set_index"}

# Atributos de un Bunch de sklearn (fetch_openml/load_*): no existen en Spark.
_SKLEARN_BUNCH_ATTRS = {"data", "target", "feature_names", "target_names", "DESCR", "frame"}

# astype de pandas -> cast de Spark. Mapea el tipo Python/numpy/str al tipo Spark.
_ASTYPE_MAP = {
    "int": "int", "int32": "int", "int64": "bigint", "long": "bigint",
    "float": "double", "float32": "float", "float64": "double",
    "str": "string", "string": "string", "object": "string",
    "bool": "boolean", "boolean": "boolean",
    "int8": "tinyint", "int16": "smallint",
}


def _astype_to_spark(arg):
    """Devuelve el nombre de tipo Spark para el argumento de pandas .astype(...).
    Acepta int/float/str (Name), 'int64' (str const) o np.int64 (Attribute)."""
    name = None
    if isinstance(arg, ast.Name):
        name = arg.id
    elif isinstance(arg, ast.Constant) and isinstance(arg.value, str):
        name = arg.value
    elif isinstance(arg, ast.Attribute):
        name = arg.attr  # np.int64 -> 'int64'
    if name is None:
        return None
    return _ASTYPE_MAP.get(name, _ASTYPE_MAP.get(name.lower()))


def _uses_pandas_index(node):
    """True si el nodo AST usa un accesor de indice/posicion de pandas
    (.loc, .iloc, .at, .iat, .ix, .index, .values, set_index/reset_index)."""
    for sub in ast.walk(node):
        if isinstance(sub, ast.Attribute) and sub.attr in _PANDAS_INDEX_ATTRS:
            return sub.attr
    return None


def _sklearn_bunch_attr(node):
    """Si el nodo es <name>.data / .target / .feature_names / ... (atributo de un
    Bunch de sklearn), devuelve el atributo. Estos no existen en un DataFrame de
    Spark (los datos vienen de una fuente real)."""
    if isinstance(node, ast.Attribute) and node.attr in _SKLEARN_BUNCH_ATTRS \
            and isinstance(node.value, ast.Name):
        return node.attr
    return None


class _Warnings:
    def __init__(self):
        self.warnings = []
        self.unsupported = []

    def warn(self, msg):
        if msg not in self.warnings:
            self.warnings.append(msg)

    def unsup(self, msg):
        if msg not in self.unsupported:
            self.unsupported.append(msg)


def _is_str_const(node):
    return isinstance(node, ast.Constant) and isinstance(node.value, str)


def _kw(call, name):
    """Devuelve el nodo del keyword `name` de un ast.Call, o None."""
    for k in call.keywords:
        if k.arg == name:
            return k.value
    return None


class PandasToSparkTransformer(ast.NodeTransformer):
    """Reescribe el AST de pandas a PySpark.

    Mantiene un conjunto `df_names` con los nombres de variable que son
    DataFrames (Spark tras la conversion). Se siembra con las asignaciones
    `x = pd.read_*` y se propaga cuando `x = <df>.<metodo_que_devuelve_df>()`.
    """

    def __init__(self, diag):
        self.diag = diag
        self.df_names = set()
        self.pandas_alias = {"pd", "pandas"}  # se ajusta al leer imports
        # Nombres importados de sklearn/ML (clases y funciones) para detectar su
        # uso mas abajo y marcarlo con TODO hacia Spark MLlib.
        self.ml_names = set()
        # Variables que son estimadores ML (x = LogisticRegression(...)) para
        # neutralizar sus .fit()/.predict()/.transform() posteriores.
        self.ml_vars = set()
        # Bloques MLlib generados: id_placeholder -> texto multi-linea. Se emiten
        # como un statement placeholder y se sustituyen tras ast.unparse.
        self.mllib_blocks = {}
        self.mllib_kinds = set()      # tipos de import MLlib a asegurar
        self._mllib_seq = 0
        # Nombre del ultimo DataFrame "principal" visto (para df_hint de MLlib).
        self.last_df = "df"
        # Variables "muertas": provienen de un statement no traducible que se
        # neutralizo a TODO (p.ej. y = adult.target). Cualquier statement que las
        # use tambien se neutraliza para no romper con NameError.
        self.dead_vars = set()

    # ---- imports: detectar alias de pandas, y neutralizar 'import pandas' ----
    def visit_Import(self, node):
        new_names = []
        for alias in node.names:
            if alias.name == "pandas":
                self.pandas_alias.add(alias.asname or "pandas")
                # se reemplaza por el import de pyspark (lo agrega el preambulo);
                # marcamos para omitir esta linea.
                continue
            if _is_ml_module(alias.name):
                self._note_ml_import(alias.asname or alias.name.split(".")[0])
                continue  # se omite el import de sklearn/ML
            new_names.append(alias)
        if not new_names:
            return None  # elimina 'import pandas as pd'
        node.names = new_names
        return node

    def visit_ImportFrom(self, node):
        if node.module == "pandas":
            return None  # 'from pandas import ...' -> se omite
        if node.module and _is_ml_module(node.module):
            # from sklearn.linear_model import LogisticRegression, ...
            for alias in node.names:
                self.ml_names.add(alias.asname or alias.name)
            self._note_ml_import(node.module)
            return None  # se omite el import; el uso se marca con TODO
        return node

    def _note_ml_import(self, mod):
        self.diag.warn(
            f"Libreria ML detectada ('{mod}'): se genero el esqueleto equivalente "
            f"en Spark MLlib (pyspark.ml). Revisa 'featuresCol'/'labelCol' y ensambla "
            f"las columnas de features con VectorAssembler antes de entrenar."
        )

    # ---- Subscript: df[...] ----
    def visit_Subscript(self, node):
        self.generic_visit(node)
        val = node.value
        sl = node.slice
        # df["col"]  -> F.col("col")   (solo si `val` es un df conocido)
        if self._is_df(val) and _is_str_const(sl):
            return self._f_col(sl.value)
        # df[["a","b"]] -> df.select("a","b")
        if self._is_df(val) and isinstance(sl, ast.List) and all(_is_str_const(e) for e in sl.elts):
            cols = [e.value for e in sl.elts]
            return ast.Call(
                func=ast.Attribute(value=val, attr="select", ctx=ast.Load()),
                args=[ast.Constant(c) for c in cols], keywords=[],
            )
        # df[<bool expr>] -> df.filter(<bool expr>)
        if self._is_df(val) and not _is_str_const(sl) and not isinstance(sl, ast.Slice):
            return ast.Call(
                func=ast.Attribute(value=val, attr="filter", ctx=ast.Load()),
                args=[sl], keywords=[],
            )
        return node

    # ---- Call: pd.read_*, df.metodo(...) ----
    def visit_Call(self, node):
        self.generic_visit(node)
        f = node.func

        # pd.read_csv(...) / pd.read_parquet(...)
        if isinstance(f, ast.Attribute) and isinstance(f.value, ast.Name) \
                and f.value.id in self.pandas_alias and f.attr in _PANDAS_READERS:
            if f.attr == "read_excel":
                self.diag.warn("pd.read_excel -> spark.read.csv (aproximado): Spark no lee "
                               ".xlsx sin conector; ajusta el formato/fuente real del archivo.")
            return self._read(node, _PANDAS_READERS[f.attr])

        # pd.DataFrame(...) -> spark.createDataFrame(...) (aprox)
        if isinstance(f, ast.Attribute) and isinstance(f.value, ast.Name) \
                and f.value.id in self.pandas_alias and f.attr == "DataFrame":
            self.diag.warn("pd.DataFrame(...) -> spark.createDataFrame(...): revisa el esquema/estructura de entrada.")
            return ast.Call(
                func=ast.Attribute(value=ast.Name("spark", ast.Load()), attr="createDataFrame", ctx=ast.Load()),
                args=node.args, keywords=node.keywords,
            )

        # df.metodo(...)
        if isinstance(f, ast.Attribute) and self._is_df(f.value):
            return self._df_method(node, f)

        # col.astype(tipo) -> col.cast('tipo_spark')   (sobre expresion de columna)
        if isinstance(f, ast.Attribute) and f.attr == "astype":
            arg = node.args[0] if node.args else (node.keywords[0].value if node.keywords else None)
            spark_type = _astype_to_spark(arg) if arg is not None else None
            if spark_type is not None:
                return ast.Call(
                    func=ast.Attribute(value=f.value, attr="cast", ctx=ast.Load()),
                    args=[ast.Constant(spark_type)], keywords=[],
                )
            self.diag.warn("astype(...) con tipo no reconocido: revisa el .cast() manualmente.")
            return ast.Call(
                func=ast.Attribute(value=f.value, attr="cast", ctx=ast.Load()),
                args=[arg] if arg is not None else [], keywords=[],
            )

        # Series.apply/map/applymap (sobre columnas F.col(...) o df["x"]): logica
        # elementwise no traducible directamente. Se marca aunque el receptor no
        # sea un df completo (p.ej. df["x"].apply(...)).
        if isinstance(f, ast.Attribute) and f.attr in ("apply", "applymap", "map"):
            recv_is_col = (
                isinstance(f.value, ast.Call) and isinstance(f.value.func, ast.Attribute)
                and f.value.func.attr == "col"
            )
            if recv_is_col:
                self.diag.unsup(
                    f".{f.attr}(...) sobre una columna (Series.{f.attr}) no es "
                    f"traducible directo: usa funciones de columna (F.*) o define "
                    f"una UDF: F.udf(...)."
                )
            return node

        # len(df) -> df.count()
        if isinstance(f, ast.Name) and f.id == "len" and len(node.args) == 1 and self._is_df(node.args[0]):
            return ast.Call(
                func=ast.Attribute(value=node.args[0], attr="count", ctx=ast.Load()),
                args=[], keywords=[],
            )
        return node

    # ---- Assign: x = pd.read_*  |  df["c"] = expr  |  x = <df>.metodo() ----
    def visit_Assign(self, node):
        # Si el valor usa una variable "muerta" (proveniente de un statement no
        # traducible), este statement tambien se neutraliza a TODO.
        dead = self._refs_dead_var(node.value)
        if dead is not None:
            try:
                orig = ast.unparse(node)
            except Exception:
                orig = "<statement>"
            self._kill_targets(node)
            return self._emit_comment([
                f"TODO py2spark: no traducible (depende de '{dead}', que no tiene",
                f"equivalente en Spark).",
                f"Original: {orig}",
            ])

        # --- Deteccion de ML (sklearn/xgboost/etc.): el entrenamiento no se
        # traduce 1:1. Neutralizamos el statement a una asignacion a None y
        # registramos un TODO con el equivalente MLlib, para que el resto del
        # codigo (preparacion pandas) siga compilando. Cubre p.ej.:
        #   X_tr, X_te, y_tr, y_te = train_test_split(...)
        #   model = LogisticRegression(...)
        #   df[cols] = scaler.fit_transform(...)   (el caso que rompia el unparse)
        ml_snippet = self._ml_snippet_for_assign(node)
        if ml_snippet is not None:
            # Registrar como estimador las variables asignadas (para resolver sus
            # .fit()/.predict()/.transform() posteriores como MLlib).
            for tgt in node.targets:
                for nm in _names_in_target(tgt):
                    self.ml_vars.add(nm)
            return self._emit_mllib(ml_snippet)

        # Atributos de un Bunch de sklearn: X = adult.data / y = adult.target ...
        # No existen en Spark. '.data' y '.frame' -> el DataFrame completo (util
        # para seguir el pipeline). '.target' y demas -> TODO honesto.
        bunch_attr = _sklearn_bunch_attr(node.value)
        if bunch_attr is not None:
            base = node.value.value  # el Name del Bunch (p.ej. 'adult')
            base_is_df = isinstance(base, ast.Name) and self._is_df(base)
            if bunch_attr in ("data", "frame") and base_is_df:
                self.diag.warn(
                    f"'.{bunch_attr}' (Bunch de sklearn) -> se usa el DataFrame "
                    f"completo. Selecciona/elimina la columna objetivo segun tu caso."
                )
                # x = adult  (marcar x como df)
                if len(node.targets) == 1 and isinstance(node.targets[0], ast.Name):
                    self.df_names.add(node.targets[0].id)
                    self.last_df = node.targets[0].id
                return ast.Assign(targets=node.targets, value=base)
            # .target / .feature_names / .DESCR / .target_names: sin equivalente.
            try:
                orig = ast.unparse(node)
            except Exception:
                orig = "<statement>"
            self.diag.unsup(
                f"'.{bunch_attr}' es un atributo del Bunch de sklearn (no existe en "
                f"Spark). En Spark la columna objetivo es una columna del DataFrame; "
                f"ajusta labelCol y selecciona la columna real."
            )
            self._kill_targets(node)
            return self._emit_comment([
                f"TODO py2spark: no traducible ('.{bunch_attr}' es atributo de sklearn.Bunch).",
                f"Original: {orig}",
            ])

        # Accesos por indice/posicion de pandas (.loc/.iloc/.index/...): Spark no
        # tiene indice de fila. En vez de emitir codigo que rompe (NameError /
        # AttributeError), neutralizamos el statement a un comentario TODO honesto.
        idx_attr = _uses_pandas_index(node.value)
        if idx_attr is not None:
            try:
                orig = ast.unparse(node)
            except Exception:
                orig = "<statement>"
            self.diag.unsup(
                f"'.{idx_attr}' usa el indice/posicion de fila de pandas, que no "
                f"existe en Spark. Revisa manualmente: en Spark 'X' e 'y' suelen "
                f"ser columnas del mismo DataFrame (no se alinean por indice)."
            )
            self._kill_targets(node)
            return self._emit_comment([
                f"TODO py2spark: no traducible ('.{idx_attr}' depende del indice de pandas).",
                f"Original: {orig}",
            ])

        # visitar primero el valor (transforma pd.read_*, etc.)
        node.value = self.visit(node.value)

        # df["c"] = expr   -> df = df.withColumn("c", expr)
        if len(node.targets) == 1 and isinstance(node.targets[0], ast.Subscript):
            tgt = node.targets[0]
            if self._is_df(tgt.value) and _is_str_const(tgt.slice):
                colname = tgt.slice.value
                df_expr = tgt.value
                new_val = ast.Call(
                    func=ast.Attribute(value=df_expr, attr="withColumn", ctx=ast.Load()),
                    args=[ast.Constant(colname), node.value], keywords=[],
                )
                # asignar de vuelta al mismo df (df = df.withColumn(...))
                if isinstance(df_expr, ast.Name):
                    return ast.Assign(targets=[ast.Name(df_expr.id, ast.Store())], value=new_val)
                return ast.Expr(value=new_val)

        # visitar los targets (por si hay subscripts df["x"] en el LHS de otra forma)
        node.targets = [self.visit(t) for t in node.targets]

        # marcar el target como df si el valor es un df (propagacion de tipo)
        if len(node.targets) == 1 and isinstance(node.targets[0], ast.Name):
            if self._value_is_df(node.value):
                self.df_names.add(node.targets[0].id)
                # recordar el ultimo df principal para usarlo como hint en MLlib
                self.last_df = node.targets[0].id
        # El target se reasigno con un valor traducible: "revive" (ya no es muerto).
        for tgt in node.targets:
            for nm in _names_in_target(tgt):
                self.dead_vars.discard(nm)
        return node

    # ---- Expr suelto: model.fit(...) / model.predict(...) sin asignacion ----
    def visit_Expr(self, node):
        snip = self._ml_snippet_for_expr(node.value, out_targets=[])
        if snip is not None:
            return self._emit_mllib(snip)
        dead = self._refs_dead_var(node.value)
        if dead is not None:
            try:
                orig = ast.unparse(node)
            except Exception:
                orig = "<statement>"
            return self._emit_comment([
                f"TODO py2spark: no traducible (depende de '{dead}', sin equivalente en Spark).",
                f"Original: {orig}",
            ])
        idx_attr = _uses_pandas_index(node.value)
        if idx_attr is not None:
            try:
                orig = ast.unparse(node)
            except Exception:
                orig = "<statement>"
            self.diag.unsup(
                f"'.{idx_attr}' usa el indice/posicion de fila de pandas, que no "
                f"existe en Spark. Revisa manualmente."
            )
            return self._emit_comment([
                f"TODO py2spark: no traducible ('.{idx_attr}' depende del indice de pandas).",
                f"Original: {orig}",
            ])
        self.generic_visit(node)
        return node

    # =====================================================================
    # MLlib: generar el codigo pyspark.ml equivalente (esqueleto) por patron
    # =====================================================================
    def _emit_mllib(self, snippet_text):
        """Registra un bloque MLlib y devuelve un statement placeholder que se
        sustituye por el texto real tras ast.unparse."""
        self._mllib_seq += 1
        pid = f"__PY2SPARK_MLLIB_{self._mllib_seq}__"
        self.mllib_blocks[pid] = snippet_text
        # Statement placeholder valido: `pid`  (un Name suelto). El post-proceso
        # reemplaza la linea completa por el bloque MLlib multi-linea.
        return ast.Expr(value=ast.Name(pid, ast.Load()))

    def _refs_dead_var(self, node):
        """Nombre de la primera variable 'muerta' referenciada en el nodo, o None."""
        if not self.dead_vars:
            return None
        for sub in ast.walk(node):
            if isinstance(sub, ast.Name) and sub.id in self.dead_vars \
                    and isinstance(sub.ctx, ast.Load):
                return sub.id
        return None

    def _kill_targets(self, node):
        """Marca los targets de una asignacion como variables muertas."""
        for tgt in getattr(node, "targets", []):
            for nm in _names_in_target(tgt):
                self.dead_vars.add(nm)

    def _emit_comment(self, lines):
        """Neutraliza un statement no traducible dejando comentarios en su lugar.

        Reusa el mecanismo de placeholders (mllib_blocks) para inyectar texto
        multi-linea preservando la indentacion. `lines` es una lista de strings
        (sin el '#'); cada una se emite como comentario."""
        self._mllib_seq += 1
        pid = f"__PY2SPARK_MLLIB_{self._mllib_seq}__"
        block = "\n".join(f"# {ln}" if ln else "#" for ln in lines)
        self.mllib_blocks[pid] = block
        return ast.Expr(value=ast.Name(pid, ast.Load()))

    def _ml_snippet_for_assign(self, node):
        """Si el assign es un patron ML, devuelve el texto MLlib equivalente."""
        value = node.value
        if not isinstance(value, ast.Call):
            return None
        func = value.func
        targets_names = []
        for tgt in node.targets:
            targets_names.extend(_names_in_target(tgt))
        # Target subscript df[cols] = ... -> el destino es el df base.
        out_target = targets_names[0] if targets_names else self.last_df
        called = func.id if isinstance(func, ast.Name) else (func.attr if isinstance(func, ast.Attribute) else None)

        # Cargador de datos sklearn: fetch_openml/load_iris/make_classification...
        # En Spark los datos vienen de una fuente real. Traducimos a spark.read
        # (placeholder) y marcamos los targets como DataFrame. Sin esto quedaba
        # 'X, y = fetch_openml(...)' crudo -> NameError (el import se elimino).
        if called in _ML_DATA_LOADERS or (called and called in self.ml_names
                                          and called.startswith(("fetch_", "load_", "make_"))):
            df_name = targets_names[0] if targets_names else "df"
            self.last_df = df_name
            self.df_names.add(df_name)
            self.diag.warn(
                f"'{called}(...)' es un cargador de datos de sklearn: en Spark los "
                f"datos vienen de una fuente real. Se reemplazo por spark.read.* "
                f"(ajusta la ruta/tabla). Si separabas X, y: la columna label viaja "
                f"dentro del DataFrame."
            )
            lines = [
                f"# Origen de datos: reemplaza sklearn.datasets.{called} por tu fuente real.",
                f'{df_name} = spark.read.option("header", True).option("inferSchema", True).csv("datos.csv")',
            ]
            # Si habia mas de un target (X, y), avisar que en Spark es un solo df.
            if len(targets_names) > 1:
                lines.append(f"# NOTA: {', '.join(targets_names[1:])} no aplican en Spark; "
                             f"la columna label es una columna mas de {df_name}.")
            return "\n".join(lines)

        # train_test_split(...)
        if called == "train_test_split" and (called in self.ml_names or called in _ML_CALLABLES):
            snip, kinds = _mllib.snippet_train_test_split(value, targets_names, self.last_df)
            self.mllib_kinds |= kinds
            self.diag.warn("train_test_split -> DataFrame.randomSplit (MLlib). Revisa la columna label.")
            return snip

        # Estimadores: var = LogisticRegression(...)/KMeans(...)/RandomForest...(...)
        if called in ("LogisticRegression", "LinearRegression", "RandomForestClassifier",
                      "RandomForestRegressor", "GradientBoostingClassifier",
                      "DecisionTreeClassifier", "KMeans") and \
                (called in self.ml_names or called in _ML_CALLABLES):
            snip, kinds = _mllib.snippet_estimator(value, out_target, called, self.last_df)
            if snip:
                self.mllib_kinds |= kinds
                return snip

        # Escaladores: var = StandardScaler()/MinMaxScaler()
        if called in ("StandardScaler", "MinMaxScaler") and \
                (called in self.ml_names or called in _ML_CALLABLES):
            snip, kinds = _mllib.snippet_scaler(value, out_target, called)
            if snip:
                self.mllib_kinds |= kinds
                return snip

        # pd.get_dummies(...)
        if isinstance(func, ast.Attribute) and func.attr == "get_dummies" \
                and isinstance(func.value, ast.Name) and func.value.id in self.pandas_alias:
            snip, kinds = _mllib.snippet_get_dummies(value, out_target, self.last_df)
            self.mllib_kinds |= kinds
            return snip

        # Metodos de estimador: X = scaler.fit_transform(...) / model.predict(...)
        if isinstance(func, ast.Attribute) and func.attr in (
                "fit", "fit_transform", "transform", "predict", "predict_proba",
                "fit_predict", "score"):
            recv = func.value.id if isinstance(func.value, ast.Name) else None
            if recv in self.ml_vars:
                return self._method_snippet(recv, func.attr, targets_names)
        return None

    def _ml_snippet_for_expr(self, value, out_targets):
        if not isinstance(value, ast.Call):
            return None
        func = value.func
        if isinstance(func, ast.Attribute) and func.attr in (
                "fit", "fit_transform", "transform", "predict", "predict_proba",
                "fit_predict", "score"):
            recv = func.value.id if isinstance(func.value, ast.Name) else None
            if recv in self.ml_vars:
                return self._method_snippet(recv, func.attr, out_targets)
        return None

    def _method_snippet(self, recv, attr, out_targets):
        if attr in ("fit_transform", "transform"):
            snip, k = _mllib.snippet_fit_transform(recv, out_targets, self.last_df)
        elif attr == "fit":
            snip, k = _mllib.snippet_fit(recv, self.last_df)
        elif attr in ("predict", "predict_proba"):
            snip, k = _mllib.snippet_predict(recv, out_targets, self.last_df)
        elif attr == "fit_predict":
            snip, k = _mllib.snippet_fit_predict(recv, out_targets, self.last_df)
        elif attr == "score":
            snip, k = _mllib.snippet_score(recv, out_targets)
        else:
            return None
        self.mllib_kinds |= k
        return snip

    def _ml_expr_info(self, value):
        """Si `value` es una expresion ML no traducible, devuelve el mensaje TODO
        (con sugerencia MLlib). Si no, devuelve None."""
        if not isinstance(value, ast.Call):
            return None
        func = value.func
        # Nombre de la funcion/clase llamada.
        called = None
        recv_name = None
        if isinstance(func, ast.Name):
            called = func.id
        elif isinstance(func, ast.Attribute):
            called = func.attr
            if isinstance(func.value, ast.Name):
                recv_name = func.value.id

        # 1) Llamada directa a una clase/funcion ML importada o conocida.
        if called and (called in self.ml_names or called in _ML_CALLABLES):
            hint = _MLLIB_HINT.get(called)
            extra = f" Equivalente Spark: {hint}." if hint else ""
            return (f"'{called}(...)' es scikit-learn/ML: no se traduce a Spark 1:1."
                    f"{extra} Usa pyspark.ml (VectorAssembler + estimador).")

        # 2) Metodo de un estimador ML: model.fit(...)/predict(...)/transform(...).
        if isinstance(func, ast.Attribute) and func.attr in (
                "fit", "predict", "predict_proba", "fit_transform", "fit_predict",
                "transform", "score"):
            if recv_name in self.ml_vars:
                return (f"'{recv_name}.{func.attr}(...)' opera sobre un modelo ML de "
                        f"scikit-learn: en Spark usa el estimador de pyspark.ml "
                        f"(.fit() devuelve un Model; .transform() para predecir).")
        # 3) pd.get_dummies(...) -> one-hot: MLlib usa StringIndexer+OneHotEncoder.
        if isinstance(func, ast.Attribute) and func.attr == "get_dummies" \
                and isinstance(func.value, ast.Name) and func.value.id in self.pandas_alias:
            return ("pd.get_dummies(...) (one-hot) no tiene equivalente directo en "
                    "Spark: usa pyspark.ml.feature.StringIndexer + OneHotEncoder.")
        return None

    # =====================================================================
    # helpers de reescritura
    # =====================================================================
    def _is_df(self, node):
        """True si el nodo evalua (heuristicamente) a un DataFrame Spark."""
        if isinstance(node, ast.Name):
            return node.id in self.df_names
        # <df>.metodo_que_devuelve_df(...)  -> tambien es df
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute):
            if node.func.attr in _DF_RETURNING and self._is_df(node.func.value):
                return True
        # <df>[...]  (slice de columnas / filtro) sigue siendo df en algunos casos
        return False

    def _value_is_df(self, value):
        # spark.read... (aunque haya .option(...).option(...) intermedios) o
        # spark.createDataFrame(...). Recorremos la cadena bajando por .value,
        # atravesando tanto Attribute como Call, hasta encontrar la raiz Name.
        cur = value
        seen_read = False
        while isinstance(cur, (ast.Attribute, ast.Call)):
            if isinstance(cur, ast.Attribute):
                if cur.attr == "read":
                    seen_read = True
                cur = cur.value
            else:  # ast.Call -> bajar por el func
                cur = cur.func
        if isinstance(cur, ast.Name) and cur.id == "spark" and seen_read:
            return True
        # spark.createDataFrame(...)
        if isinstance(value, ast.Call) and isinstance(value.func, ast.Attribute) \
                and value.func.attr == "createDataFrame" \
                and isinstance(value.func.value, ast.Name) and value.func.value.id == "spark":
            return True
        # <df>.<metodo que devuelve df>(...)
        if isinstance(value, ast.Call) and isinstance(value.func, ast.Attribute) \
                and value.func.attr in _DF_RETURNING and self._is_df(value.func.value):
            return True
        if self._is_df(value):
            return True
        return False

    def _f_col(self, name):
        # F.col("name")
        return ast.Call(
            func=ast.Attribute(value=ast.Name("F", ast.Load()), attr="col", ctx=ast.Load()),
            args=[ast.Constant(name)], keywords=[],
        )

    def _read(self, node, fmt):
        # spark.read[.option(header,inferSchema)].<fmt>(path)
        path_arg = node.args[0] if node.args else _kw(node, "filepath_or_buffer") or _kw(node, "path")
        reader = ast.Attribute(value=ast.Name("spark", ast.Load()), attr="read", ctx=ast.Load())
        if fmt == "csv":
            # .option("header", True).option("inferSchema", True)
            reader = ast.Call(
                func=ast.Attribute(value=reader, attr="option", ctx=ast.Load()),
                args=[ast.Constant("header"), ast.Constant(True)], keywords=[],
            )
            reader = ast.Call(
                func=ast.Attribute(value=reader, attr="option", ctx=ast.Load()),
                args=[ast.Constant("inferSchema"), ast.Constant(True)], keywords=[],
            )
            # sep=... -> .option("sep", ...)
            sep = _kw(node, "sep") or _kw(node, "delimiter")
            if sep is not None:
                reader = ast.Call(
                    func=ast.Attribute(value=reader, attr="option", ctx=ast.Load()),
                    args=[ast.Constant("sep"), sep], keywords=[],
                )
        call = ast.Call(
            func=ast.Attribute(value=reader, attr=fmt, ctx=ast.Load()),
            args=[path_arg] if path_arg else [], keywords=[],
        )
        return call

    def _df_method(self, node, f):
        """Reescribe <df>.<metodo>(...)."""
        m = f.attr
        recv = f.value

        # merge -> join
        if m == "merge":
            other = node.args[0] if node.args else None
            on = _kw(node, "on")
            left_on = _kw(node, "left_on")
            how = _kw(node, "how")
            kws = []
            if on is not None:
                kws.append(ast.keyword(arg="on", value=on))
            elif left_on is not None:
                # left_on/right_on con nombres iguales -> on; si difieren, TODO.
                right_on = _kw(node, "right_on")
                if right_on is not None and ast.dump(left_on) == ast.dump(right_on):
                    kws.append(ast.keyword(arg="on", value=left_on))
                else:
                    self.diag.unsup("merge con left_on!=right_on: usa condicion explicita df1.k1==df2.k2 (revisar).")
                    if left_on is not None:
                        kws.append(ast.keyword(arg="on", value=left_on))
            howval = how.value if _is_str_const(how) else "inner"
            kws.append(ast.keyword(arg="how", value=ast.Constant(howval)))
            return ast.Call(
                func=ast.Attribute(value=recv, attr="join", ctx=ast.Load()),
                args=[other] if other else [], keywords=kws,
            )

        # groupby -> groupBy
        if m == "groupby":
            return ast.Call(
                func=ast.Attribute(value=recv, attr="groupBy", ctx=ast.Load()),
                args=node.args, keywords=[k for k in node.keywords if k.arg not in ("as_index", "sort")],
            )

        # sort_values -> orderBy (respeta ascending)
        if m == "sort_values":
            by = node.args[0] if node.args else _kw(node, "by")
            asc = _kw(node, "ascending")
            cols = []
            names = []
            if _is_str_const(by):
                names = [by.value]
            elif isinstance(by, ast.List):
                names = [e.value for e in by.elts if _is_str_const(e)]
            descending = (isinstance(asc, ast.Constant) and asc.value is False)
            for nm in names:
                c = self._f_col(nm)
                if descending:
                    c = ast.Call(func=ast.Attribute(value=c, attr="desc", ctx=ast.Load()), args=[], keywords=[])
                cols.append(c)
            if not cols and by is not None:
                cols = [by]
            return ast.Call(
                func=ast.Attribute(value=recv, attr="orderBy", ctx=ast.Load()),
                args=cols, keywords=[],
            )

        # head(n) / tail(n) -> limit(n)
        if m in ("head", "tail"):
            n = node.args[0] if node.args else ast.Constant(5)
            if m == "tail":
                self.diag.warn("df.tail(n): Spark no garantiza orden; se traduce como limit(n).")
            return ast.Call(
                func=ast.Attribute(value=recv, attr="limit", ctx=ast.Load()),
                args=[n], keywords=[],
            )

        # rename(columns={a:b, ...}) -> withColumnRenamed encadenado
        if m == "rename":
            cols = _kw(node, "columns")
            if isinstance(cols, ast.Dict):
                cur = recv
                for kk, vv in zip(cols.keys, cols.values):
                    cur = ast.Call(
                        func=ast.Attribute(value=cur, attr="withColumnRenamed", ctx=ast.Load()),
                        args=[kk, vv], keywords=[],
                    )
                return cur
            self.diag.unsup("rename sin columns={...} literal: revisar manualmente.")
            return node

        # drop(columns=[...]) o drop([...], axis=1) -> drop(*cols)
        if m == "drop":
            cols = _kw(node, "columns")
            args = []
            if isinstance(cols, ast.List):
                args = list(cols.elts)
            elif node.args and isinstance(node.args[0], ast.List):
                args = list(node.args[0].elts)
            elif node.args:
                args = [node.args[0]]
            return ast.Call(
                func=ast.Attribute(value=recv, attr="drop", ctx=ast.Load()),
                args=args, keywords=[],
            )

        # drop_duplicates -> dropDuplicates
        if m == "drop_duplicates":
            subset = _kw(node, "subset") or (node.args[0] if node.args else None)
            args = []
            if isinstance(subset, ast.List):
                args = [subset]
            return ast.Call(
                func=ast.Attribute(value=recv, attr="dropDuplicates", ctx=ast.Load()),
                args=args, keywords=[],
            )

        # to_csv / to_parquet -> write
        if m in ("to_csv", "to_parquet", "to_json", "to_orc"):
            fmt = m.replace("to_", "")
            path = node.args[0] if node.args else _kw(node, "path_or_buf") or _kw(node, "path")
            writer = ast.Attribute(value=recv, attr="write", ctx=ast.Load())
            writer = ast.Call(
                func=ast.Attribute(value=writer, attr="mode", ctx=ast.Load()),
                args=[ast.Constant("overwrite")], keywords=[],
            )
            if fmt == "csv":
                writer = ast.Call(
                    func=ast.Attribute(value=writer, attr="option", ctx=ast.Load()),
                    args=[ast.Constant("header"), ast.Constant(True)], keywords=[],
                )
            return ast.Call(
                func=ast.Attribute(value=writer, attr=fmt, ctx=ast.Load()),
                args=[path] if path else [], keywords=[],
            )

        # sample: pandas df.sample(n=..., frac=..., random_state=...) ->
        #   Spark df.sample(withReplacement, fraction, seed)
        # OJO: pandas 'n' es NUMERO de filas; Spark solo acepta 'fraction'.
        if m == "sample":
            frac = _kw(node, "frac")
            n = _kw(node, "n")
            if n is None and node.args and not _kw(node, "frac"):
                # primer posicional en pandas es 'n' (numero de filas)
                n = node.args[0]
            rs = _kw(node, "random_state") or _kw(node, "seed")
            replace = _kw(node, "replace")

            kws = []
            if replace is not None:
                kws.append(ast.keyword(arg="withReplacement", value=replace))

            if frac is not None:
                kws.append(ast.keyword(arg="fraction", value=frac))
                if rs is not None:
                    kws.append(ast.keyword(arg="seed", value=rs))
                return ast.Call(
                    func=ast.Attribute(value=recv, attr="sample", ctx=ast.Load()),
                    args=[], keywords=kws,
                )

            if n is not None:
                # Spark no toma numero de filas: tomamos una fraccion segura (1.0)
                # con el mismo seed y luego .limit(n) para obtener n filas.
                self.diag.warn(
                    "df.sample(n): Spark.sample usa fraccion, no numero de filas. "
                    "Se traduce a .sample(fraction=1.0, seed=...).limit(n)."
                )
                kws.append(ast.keyword(arg="fraction", value=ast.Constant(1.0)))
                if rs is not None:
                    kws.append(ast.keyword(arg="seed", value=rs))
                sampled = ast.Call(
                    func=ast.Attribute(value=recv, attr="sample", ctx=ast.Load()),
                    args=[], keywords=kws,
                )
                return ast.Call(
                    func=ast.Attribute(value=sampled, attr="limit", ctx=ast.Load()),
                    args=[n], keywords=[],
                )

            # sin n ni frac: traducir random_state->seed si existe
            if rs is not None:
                kws.append(ast.keyword(arg="seed", value=rs))
            return ast.Call(
                func=ast.Attribute(value=recv, attr="sample", ctx=ast.Load()),
                args=[], keywords=kws,
            )

        # fillna / dropna / distinct: mismos nombres en Spark (fillna, dropna, distinct)
        if m in ("fillna", "dropna", "distinct"):
            return node

        # agg: pandas .agg({"col":"sum"}) -> F.sum("col").alias("col")
        if m == "agg":
            return self._agg(node, recv)

        # apply / applymap / map / iterrows / itertuples: NO traducible fielmente
        if m in ("apply", "applymap", "map", "iterrows", "itertuples", "transform", "pipe"):
            self.diag.unsup(f"df.{m}(...) no es traducible automaticamente a Spark "
                            f"(logica fila-a-fila). Reescribe con funciones de columna "
                            f"(F.*) o una UDF de Spark.")
            return node

        # metodos que ya existen en Spark con el mismo nombre: dejar igual.
        return node

    def _agg(self, node, recv):
        """Traduce .agg(...) de pandas a .agg(F.<fun>('col').alias('col'), ...)."""
        # .agg({"col": "sum", ...})
        if node.args and isinstance(node.args[0], ast.Dict):
            d = node.args[0]
            items = []
            for kk, vv in zip(d.keys, d.values):
                if _is_str_const(kk) and _is_str_const(vv):
                    fun = _AGG_MAP.get(vv.value, vv.value)
                    call = ast.Call(
                        func=ast.Attribute(value=ast.Name("F", ast.Load()), attr=fun, ctx=ast.Load()),
                        args=[ast.Constant(kk.value)], keywords=[],
                    )
                    call = ast.Call(
                        func=ast.Attribute(value=call, attr="alias", ctx=ast.Load()),
                        args=[ast.Constant(kk.value)], keywords=[],
                    )
                    items.append(call)
                else:
                    self.diag.warn("agg con clave/valor no literal: revisar.")
            return ast.Call(
                func=ast.Attribute(value=recv, attr="agg", ctx=ast.Load()),
                args=items, keywords=[],
            )
        # .agg("sum") o .agg(["sum","mean"]) sobre un groupby: aproximacion
        self.diag.warn("agg(...) con forma no-dict: revisar la traduccion de agregaciones.")
        return node


def _detect_pandas(source):
    """True si el codigo importa/usa pandas (para decidir si convertir)."""
    return bool(re.search(r'\bimport\s+pandas\b|\bfrom\s+pandas\b|\bpd\.', source))


_PREAMBLE = '''\
# Generado por py2spark — Python (pandas) -> PySpark 3
# Revisa los comentarios "# TODO py2spark:" donde la traduccion no es 1:1.
from pyspark.sql import SparkSession
from pyspark.sql import functions as F

spark = SparkSession.builder.appName("py2spark_job").getOrCreate()
'''


def convert_code(source, add_preamble=True):
    """Convierte codigo Python (pandas) a PySpark 3.

    Devuelve dict: {ok, code, warnings, unsupported}.
    - ok: False si el codigo de entrada no es Python valido (no se toca).
    - code: PySpark generado (o el original si no se detecto pandas).
    - warnings: notas de traduccion no exacta.
    - unsupported: construcciones que requieren intervencion manual.
    """
    diag = _Warnings()
    try:
        tree = ast.parse(source)
    except SyntaxError as e:
        return {
            "ok": False,
            "code": source,
            "warnings": [],
            "unsupported": [f"El codigo de entrada no es Python valido: {e}"],
        }

    used_pandas = _detect_pandas(source)
    transformer = PandasToSparkTransformer(diag)
    new_tree = transformer.visit(tree)
    ast.fix_missing_locations(new_tree)

    try:
        body_code = ast.unparse(new_tree)
    except Exception as e:  # pragma: no cover - unparse muy raro que falle
        return {
            "ok": False,
            "code": source,
            "warnings": diag.warnings,
            "unsupported": diag.unsupported + [f"No se pudo regenerar el codigo: {e}"],
        }

    # Sustituir los placeholders MLlib por sus bloques de codigo reales,
    # respetando la indentacion de la linea donde aparece el placeholder.
    if transformer.mllib_blocks:
        body_code = _expand_mllib_placeholders(body_code, transformer.mllib_blocks)

    used_ml = bool(transformer.mllib_blocks)

    # Si el MLlib generado referencia un DataFrame (df_hint) que nunca se define
    # en el codigo (p.ej. el entrenamiento partia de arrays numpy, sin pd.read_*),
    # inyectamos una fuente placeholder para ese df. Sin esto el job rompe con
    # NameError y Data Redactada no detecta ninguna fuente (schema vacio).
    if used_ml:
        body_code = _ensure_mllib_source(body_code, transformer)
    if not used_pandas and not used_ml:
        diag.warn("No se detecto uso de pandas; el codigo se dejo casi intacto. "
                  "py2spark hoy traduce principalmente pandas->PySpark.")

    code = body_code
    if add_preamble and (used_pandas or used_ml):
        preamble = _PREAMBLE
        # Imports de pyspark.ml necesarios para los bloques MLlib generados.
        ml_imports = _mllib.imports_for(transformer.mllib_kinds)
        if ml_imports:
            preamble = preamble + "\n" + "\n".join(ml_imports) + "\n"
        code = preamble + "\n" + body_code

    # Inyectar comentarios TODO por cada 'unsupported' al inicio, para que queden
    # visibles en el archivo generado.
    if diag.unsupported:
        todo_block = "\n".join(f"# TODO py2spark: {u}" for u in diag.unsupported)
        code = todo_block + "\n" + code

    return {
        "ok": True,
        "code": code,
        "warnings": diag.warnings,
        "unsupported": diag.unsupported,
    }


def _ensure_mllib_source(body_code, transformer):
    """Garantiza que el DataFrame usado por el MLlib exista.

    El MLlib usa `transformer.last_df` como df_hint. Si ese nombre nunca se
    asigna en el codigo (porque el original partia de arrays numpy / datos en
    memoria y no de un pd.read_*), inyectamos una fuente placeholder para que el
    job ejecute y Data Redactada infiera un esquema."""
    df_hint = getattr(transformer, "last_df", "df") or "df"
    try:
        tree = ast.parse(body_code)
    except SyntaxError:
        return body_code

    # Buscamos una definicion INICIAL valida de df_hint: una asignacion a nivel
    # de modulo (no dentro de if/for/try) cuyo valor NO dependa del propio
    # df_hint. Las reasignaciones como `df = df.withColumn(...)` dentro del bloque
    # MLlib NO cuentan como definicion (df aun no existe ahi).
    def _value_uses(node, name):
        return any(isinstance(s, ast.Name) and s.id == name for s in ast.walk(node))

    defined = False
    for stmt in tree.body:  # solo statements top-level
        if isinstance(stmt, ast.Assign):
            names = []
            for tgt in stmt.targets:
                names.extend(_names_in_target(tgt))
            if df_hint in names and not _value_uses(stmt.value, df_hint):
                defined = True
                break

    if defined:
        return body_code  # ya se define en el codigo

    reader = (
        f"# Origen de datos: define aqui tu fuente real (el codigo original no\n"
        f"# leia de un archivo/tabla; usaba datos en memoria).\n"
        f'{df_hint} = spark.read.option("header", True).option("inferSchema", True).csv("datos.csv")'
    )
    transformer.df_names.add(df_hint)
    transformer.diag.warn(
        f"El entrenamiento MLlib usa '{df_hint}' pero el codigo no leia de una "
        f"fuente real (datos en memoria/numpy). Se inyecto un spark.read.* "
        f"placeholder: ajusta la ruta/tabla."
    )
    return reader + "\n" + body_code


def _expand_mllib_placeholders(body_code, blocks):
    """Reemplaza cada linea con un placeholder __PY2SPARK_MLLIB_N__ por su bloque
    de texto MLlib, preservando la indentacion de la linea."""
    out_lines = []
    for line in body_code.splitlines():
        stripped = line.strip()
        if stripped in blocks:
            indent = line[:len(line) - len(line.lstrip())]
            block = blocks[stripped]
            for bl in block.splitlines():
                out_lines.append(indent + bl if bl else bl)
        else:
            out_lines.append(line)
    return "\n".join(out_lines)


def convert_file(path, add_preamble=True):
    """Convierte un archivo .py y devuelve el mismo dict que convert_code."""
    with open(path, "r", encoding="utf-8", errors="replace") as f:
        src = f.read()
    return convert_code(src, add_preamble=add_preamble)
