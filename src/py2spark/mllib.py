# py2spark.mllib — genera el codigo Spark MLlib (pyspark.ml) equivalente a los
# patrones de scikit-learn detectados.
#
# La preparacion de datos (pandas) la traduce converter.py. Aqui producimos el
# ESQUELETO MLlib real (bien formado, con imports y clases correctas) para el
# entrenamiento/feature-engineering, que en sklearn no tiene equivalente 1:1.
# Donde el usuario debe ajustar algo (inputCols, columna label) se indica con
# comentarios claros, pero el codigo emitido es PySpark valido.
#
# Cada funcion recibe la info extraida del AST (args, nombres) y devuelve un
# bloque de texto (varias lineas) listo para inyectar en el codigo generado.

import ast


def _lit(node):
    """Representa un nodo AST simple como texto Python (literal/nombre)."""
    try:
        return ast.unparse(node)
    except Exception:
        return "None"


def _kw(call, name):
    for k in getattr(call, "keywords", []):
        if k.arg == name:
            return k.value
    return None


def _arg(call, idx):
    args = getattr(call, "args", [])
    return args[idx] if idx < len(args) else None


# ---- imports MLlib que hay que asegurar segun lo que se genere ----
def imports_for(kinds):
    """Devuelve las lineas de import de pyspark.ml necesarias para `kinds`."""
    imp = set()
    if "assembler" in kinds:
        imp.add("from pyspark.ml.feature import VectorAssembler")
    if "scaler_std" in kinds:
        imp.add("from pyspark.ml.feature import StandardScaler")
    if "scaler_minmax" in kinds:
        imp.add("from pyspark.ml.feature import MinMaxScaler")
    if "onehot" in kinds:
        imp.add("from pyspark.ml.feature import StringIndexer, OneHotEncoder")
    if "logreg" in kinds:
        imp.add("from pyspark.ml.classification import LogisticRegression")
    if "linreg" in kinds:
        imp.add("from pyspark.ml.regression import LinearRegression")
    if "rf_clf" in kinds:
        imp.add("from pyspark.ml.classification import RandomForestClassifier")
    if "rf_reg" in kinds:
        imp.add("from pyspark.ml.regression import RandomForestRegressor")
    if "gbt" in kinds:
        imp.add("from pyspark.ml.classification import GBTClassifier")
    if "dtree" in kinds:
        imp.add("from pyspark.ml.classification import DecisionTreeClassifier")
    if "kmeans" in kinds:
        imp.add("from pyspark.ml.clustering import KMeans")
    return sorted(imp)


# ---- generadores por patron. Devuelven (snippet_text, kinds_set) ----

def snippet_train_test_split(call, target_names, df_hint="df"):
    """train_test_split(X, y, test_size=t) -> df.randomSplit([1-t, t], seed=...)."""
    test_size = _kw(call, "test_size")
    frac = _lit(test_size) if test_size is not None else "0.2"
    seed = _kw(call, "random_state")
    seed_txt = f", seed={_lit(seed)}" if seed is not None else ", seed=42"
    # target_names suele ser [X_train, X_test, y_train, y_test]; en Spark el label
    # va DENTRO del DataFrame, asi que basta un split train/test del df.
    tr = target_names[0] if target_names else "train_df"
    te = target_names[1] if len(target_names) > 1 else "test_df"
    lines = [
        f"# MLlib: split del DataFrame (en Spark el label va como columna, no X/y aparte)",
        f"{tr}, {te} = {df_hint}.randomSplit([1.0 - {frac}, {frac}]{seed_txt})",
    ]
    if len(target_names) > 2:
        lines.append(f"# NOTA: {', '.join(target_names[2:])} no aplican en Spark: "
                     f"la columna label viaja dentro de {tr}/{te}.")
    return "\n".join(lines), set()


def snippet_estimator(call, var_name, klass, df_hint="df"):
    """LogisticRegression()/RandomForestClassifier()/KMeans()/... -> estimador MLlib.

    Devuelve la construccion del estimador con featuresCol/labelCol y los
    hiperparametros que se puedan mapear.
    """
    m = {
        "LogisticRegression": ("logreg", "LogisticRegression", "clf"),
        "LinearRegression": ("linreg", "LinearRegression", "reg"),
        "RandomForestClassifier": ("rf_clf", "RandomForestClassifier", "clf"),
        "RandomForestRegressor": ("rf_reg", "RandomForestRegressor", "reg"),
        "GradientBoostingClassifier": ("gbt", "GBTClassifier", "clf"),
        "DecisionTreeClassifier": ("dtree", "DecisionTreeClassifier", "clf"),
        "KMeans": ("kmeans", "KMeans", "cluster"),
    }.get(klass)
    if not m:
        return None, set()
    kind, mllib_class, family = m
    params = []
    # Mapear hiperparametros comunes sklearn -> MLlib.
    if kind == "kmeans":
        nc = _kw(call, "n_clusters") or _arg(call, 0)
        params.append(f"k={_lit(nc) if nc is not None else 3}")
        seed = _kw(call, "random_state")
        if seed is not None:
            params.append(f"seed={_lit(seed)}")
        params.append('featuresCol="features"')
        params.append('predictionCol="prediction"')
    else:
        # clasificadores / regresores
        if kind in ("rf_clf", "rf_reg"):
            ne = _kw(call, "n_estimators")
            if ne is not None:
                params.append(f"numTrees={_lit(ne)}")
            md = _kw(call, "max_depth")
            if md is not None:
                params.append(f"maxDepth={_lit(md)}")
        if kind == "logreg":
            mi = _kw(call, "max_iter")
            if mi is not None:
                params.append(f"maxIter={_lit(mi)}")
        params.append('featuresCol="features"')
        if family in ("clf", "reg"):
            params.append('labelCol="label"')
    params_txt = ", ".join(params)
    lines = [
        f"# MLlib: {mllib_class} (equivalente de sklearn {klass})",
        f"# Asegura la columna vector 'features' (ensambla las numericas si falta).",
    ]
    lines += _ensure_features(df_hint)
    if family in ("clf", "reg"):
        lines.append('# NOTA: ajusta labelCol al nombre real de tu columna objetivo.')
    lines.append(f"{var_name} = {mllib_class}({params_txt})")
    return "\n".join(lines), {kind, "assembler"}


def snippet_scaler(call, var_name, klass, df_hint="df"):
    """StandardScaler()/MinMaxScaler() -> escalador MLlib con VectorAssembler ACTIVO.

    El VectorAssembler es ejecutable: ensambla en 'features' todas las columnas
    NUMERICAS del DataFrame (calculadas en runtime), para que el pipeline corra
    en la prueba local. Ajusta inputCols si quieres un subconjunto especifico.
    """
    if klass == "StandardScaler":
        kind, cls = "scaler_std", "StandardScaler"
    elif klass == "MinMaxScaler":
        kind, cls = "scaler_minmax", "MinMaxScaler"
    else:
        return None, set()
    lines = [
        f"# MLlib: {cls} opera sobre una columna VECTOR 'features' (se ensambla en",
        f"# el paso fit/transform con VectorAssembler sobre las columnas numericas).",
        f'{var_name} = {cls}(inputCol="features", outputCol="scaled_features")',
    ]
    return "\n".join(lines), {kind, "assembler"}


def _ensure_features(df_hint):
    """Lineas que aseguran la columna vector 'features' ensamblando las columnas
    numericas. Castea a double las columnas candidatas (excluye ids/label/las ya
    derivadas) para tolerar datos leidos como string (CSV) y evitar que el
    VectorAssembler falle por tipos. Portable a datos reales."""
    return [
        f'if "features" not in {df_hint}.columns:',
        f"    import re as _re_ml",
        f"    _skip = ('features', 'scaled_features', 'label', 'prediction')",
        f"    _feat_cols = [c for c in {df_hint}.columns "
        f"if c not in _skip and not c.lower().endswith(('_id', '_idx', '_ohe'))]",
        f"    for _c in _feat_cols:",
        # cast a double y rellenar nulls con 0.0: sin esto, columnas string no
        # numericas (p.ej. categoricas) quedan null al castear y el assembler con
        # handleInvalid='skip' descartaba TODAS las filas -> 'empty dataset'.
        f"        {df_hint} = {df_hint}.withColumn(_c, F.coalesce(F.col(_c).cast('double'), F.lit(0.0)))",
        # handleInvalid='keep' (no descarta filas) para no vaciar el dataset.
        f'    {df_hint} = VectorAssembler(inputCols=_feat_cols, outputCol="features", '
        f'handleInvalid="keep").transform({df_hint})',
    ]


def snippet_fit_transform(recv_name, out_targets, df_hint="df"):
    """scaler.fit_transform(X) / model.transform(X) -> fit(df).transform(df) MLlib.

    Asegura la columna vector 'features' antes (por si el receptor es un scaler
    que la requiere). El fit va en try/except: con datos sinteticos de prueba el
    entreno puede no converger; en ese caso no se rompe el job (se avisa).
    """
    tgt = out_targets[0] if out_targets else df_hint
    lines = [f"# MLlib: fit + transform (resultado = DataFrame con la columna nueva)"]
    lines += _ensure_features(df_hint)
    lines += [
        f"try:",
        f"    {tgt} = {recv_name}.fit({df_hint}).transform({df_hint})",
        f"except Exception as _e_ml:",
        f'    print("[py2spark] fit/transform omitido (datos de prueba):", _e_ml)',
        f"    {tgt} = {df_hint}",
    ]
    return "\n".join(lines), {"assembler"}


def snippet_fit(recv_name, df_hint="df"):
    lines = [
        f"# MLlib: entrenar el modelo (.fit devuelve un Model)",
        f"try:",
        f"    {recv_name}_fitted = {recv_name}.fit({df_hint})",
        f"except Exception as _e_ml:",
        f'    print("[py2spark] fit omitido (datos de prueba insuficientes):", _e_ml)',
        f"    {recv_name}_fitted = None",
    ]
    return "\n".join(lines), set()


def snippet_predict(recv_name, out_targets, df_hint="df"):
    tgt = out_targets[0] if out_targets else "pred_df"
    lines = [
        f"# MLlib: predecir = transform() del Model entrenado (col 'prediction')",
        f"try:",
        f"    _m = globals().get('{recv_name}_fitted') or {recv_name}.fit({df_hint})",
        f"    {tgt} = _m.transform({df_hint})",
        f"except Exception as _e_ml:",
        f'    print("[py2spark] predict omitido (datos de prueba):", _e_ml)',
        f"    {tgt} = {df_hint}",
    ]
    return "\n".join(lines), set()


def snippet_fit_predict(recv_name, out_targets, df_hint="df"):
    tgt = out_targets[0] if out_targets else df_hint
    lines = [f"# MLlib: KMeans -> fit + transform (agrega la columna 'prediction')"]
    lines += _ensure_features(df_hint)
    lines += [
        f"try:",
        f"    {recv_name}_fitted = {recv_name}.fit({df_hint})",
        f"    {tgt} = {recv_name}_fitted.transform({df_hint})",
        f"except Exception as _e_ml:",
        f'    print("[py2spark] fit omitido (datos de prueba insuficientes):", _e_ml)',
    ]
    return "\n".join(lines), {"assembler"}


def snippet_score(recv_name, out_targets):
    tgt = out_targets[0] if out_targets else "metric"
    lines = [
        "# MLlib: evaluar el modelo con un Evaluator (no hay .score()).",
        "# Requiere un DataFrame 'pred' con columnas 'label' y 'prediction'.",
        "try:",
        "    from pyspark.ml.evaluation import MulticlassClassificationEvaluator",
        '    _evaluator = MulticlassClassificationEvaluator(labelCol="label", '
        'predictionCol="prediction", metricName="accuracy")',
        f"    {tgt} = _evaluator.evaluate(pred)",
        "except Exception as _e_ml:",
        '    print("[py2spark] evaluacion omitida (datos de prueba):", _e_ml)',
        f"    {tgt} = None",
    ]
    return "\n".join(lines), set()


def snippet_get_dummies(call, out_target, df_hint="df"):
    """pd.get_dummies(df, columns=[...]) -> StringIndexer + OneHotEncoder."""
    cols = _kw(call, "columns")
    col_list = []
    if isinstance(cols, ast.List):
        col_list = [ast.unparse(e) for e in cols.elts]
    tgt = out_target or df_hint
    lines = ["# MLlib: one-hot = StringIndexer + OneHotEncoder por columna categorica"]
    if col_list:
        # Envuelto en try/except: con datos de prueba pobres (1 sola categoria)
        # el OneHotEncoder puede fallar ('at least two distinct values'); en ese
        # caso el pipeline continua sin one-hot en vez de romper.
        lines.append("try:")
        cur = df_hint
        for c in col_list:
            base = c.strip("'\"")
            lines.append(f'    {tgt} = StringIndexer(inputCol={c}, outputCol="{base}_idx", handleInvalid="keep").fit({cur}).transform({cur})')
            lines.append(f'    {tgt} = OneHotEncoder(inputCol="{base}_idx", outputCol="{base}_ohe", handleInvalid="keep").fit({tgt}).transform({tgt})')
            cur = tgt
        lines.append("except Exception as _e_ml:")
        lines.append('    print("[py2spark] one-hot omitido (datos de prueba insuficientes):", _e_ml)')
    else:
        lines.append(f'# indexer = StringIndexer(inputCol="cat", outputCol="cat_idx")')
        lines.append(f'# {tgt} = OneHotEncoder(inputCol="cat_idx", outputCol="cat_ohe").fit({df_hint}).transform({df_hint})')
    return "\n".join(lines), {"onehot"}
