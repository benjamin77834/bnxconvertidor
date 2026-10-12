# py2spark.sklearn_pipeline — reconocedor del patron sklearn
# Pipeline + ColumnTransformer y traductor a un pyspark.ml.Pipeline equivalente.
#
# Opera a nivel de MODULO (ve todos los statements), porque este patron NO se
# traduce linea-por-linea: un `model = Pipeline([... ColumnTransformer ...])`
# referencia sub-pipelines, listas de features y un clasificador definidos antes.
#
# Diseno defensivo: SOLO se activa si reconoce el patron COMPLETO con piezas
# soportadas (SimpleImputer / StandardScaler / OneHotEncoder / StringIndexer +
# un clasificador MLlib conocido). Si algo no encaja, devuelve None y el
# convertidor cae a su comportamiento normal (TODO honesto). Nunca genera un
# pipeline a medias.

import ast

from ._unparse import unparse as _unparse


# Clasificadores/regresores sklearn -> (clase MLlib, kind para imports).
_ESTIMATORS = {
    "RandomForestClassifier": ("RandomForestClassifier", "rf_clf"),
    "RandomForestRegressor": ("RandomForestRegressor", "rf_reg"),
    "LogisticRegression": ("LogisticRegression", "logreg"),
    "LinearRegression": ("LinearRegression", "linreg"),
    "DecisionTreeClassifier": ("DecisionTreeClassifier", "dtree"),
    "GradientBoostingClassifier": ("GBTClassifier", "gbt"),
}

# Mapeo de hiperparametros sklearn -> MLlib por clase.
_HYPERPARAMS = {
    "RandomForestClassifier": {
        "n_estimators": "numTrees", "max_depth": "maxDepth",
        "min_samples_leaf": "minInstancesPerNode", "random_state": "seed",
    },
    "RandomForestRegressor": {
        "n_estimators": "numTrees", "max_depth": "maxDepth",
        "min_samples_leaf": "minInstancesPerNode", "random_state": "seed",
    },
    "LogisticRegression": {"max_iter": "maxIter", "C": None},
    "LinearRegression": {},
    "DecisionTreeClassifier": {"max_depth": "maxDepth", "random_state": "seed"},
    "GradientBoostingClassifier": {
        "n_estimators": "maxIter", "max_depth": "maxDepth", "random_state": "seed",
    },
}

# Transformers soportados dentro de un sub-Pipeline de columna.
_IMPUTER = "SimpleImputer"
_SCALER = "StandardScaler"
_ONEHOT = "OneHotEncoder"
_INDEXER_ONLY = {"OrdinalEncoder", "LabelEncoder"}


def _call_name(node):
    if isinstance(node, ast.Call):
        f = node.func
        if isinstance(f, ast.Name):
            return f.id
        if isinstance(f, ast.Attribute):
            return f.attr
    return None


def _kw(call, name):
    for k in getattr(call, "keywords", []):
        if k.arg == name:
            return k.value
    return None


def _arg(call, idx):
    args = getattr(call, "args", [])
    return args[idx] if idx < len(args) else None


def _const_str(node):
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        return node.value
    return None


def _list_of_str(node):
    """Devuelve la lista de strings si node es ['a','b',...], o None."""
    if isinstance(node, ast.List):
        out = []
        for e in node.elts:
            s = _const_str(e)
            if s is None:
                return None
            out.append(s)
        return out
    return None


class _Scan:
    """Recolecta del modulo las piezas del patron sklearn."""

    def __init__(self):
        self.assigns = {}          # nombre -> nodo Call (valor asignado)
        self.feature_lists = {}    # nombre -> [cols]  (listas de str)
        self.df_feature_lists = {} # nombre -> col base de df[...] (no usado aun)
        self.label_col = None      # columna label inferida de y = df['col']
        self.read_csv_path = None  # ruta del pd.read_csv


def _scan_module(tree):
    sc = _Scan()
    for node in tree.body:
        if not isinstance(node, ast.Assign) or len(node.targets) != 1:
            continue
        tgt = node.targets[0]
        if not isinstance(tgt, ast.Name):
            continue
        name = tgt.id
        val = node.value

        # listas de features: numeric_features = ['a','b']
        lst = _list_of_str(val)
        if lst is not None:
            sc.feature_lists[name] = lst
            continue

        # label: y = df['churn']  (Subscript con string)
        if isinstance(val, ast.Subscript):
            sub = val.slice
            # py3.9+: slice es el nodo directo
            col = _const_str(sub)
            if col is not None:
                sc.label_col = sc.label_col or col
            continue

        # pd.read_csv("clientes.csv")
        if _call_name(val) == "read_csv":
            p = _arg(val, 0)
            s = _const_str(p)
            if s:
                sc.read_csv_path = s
            continue

        # llamadas (Pipeline/ColumnTransformer/estimadores/transformers)
        if isinstance(val, ast.Call):
            sc.assigns[name] = val
    return sc


def _parse_sub_pipeline(call, sc):
    """Un sklearn Pipeline(steps=[(nombre, Transformer()), ...]) de UNA columna.
    Devuelve lista de pasos normalizados [{'kind','params'}] o None si trae algo
    no soportado."""
    steps = _arg(call, 0)
    if steps is None:
        steps = _kw(call, "steps")
    if not isinstance(steps, ast.List):
        return None
    out = []
    for item in steps.elts:
        if not isinstance(item, ast.Tuple) or len(item.elts) != 2:
            return None
        tcall = item.elts[1]
        tname = _call_name(tcall)
        if tname == _IMPUTER:
            strat = _kw(tcall, "strategy")
            out.append({"kind": "imputer", "strategy": _const_str(strat) or "mean"})
        elif tname == _SCALER:
            out.append({"kind": "scaler"})
        elif tname == _ONEHOT:
            out.append({"kind": "onehot"})
        else:
            return None  # transformer no soportado -> abortar reconocimiento
    return out


def _resolve_transformer(ref, sc):
    """Resuelve un transformer referenciado por nombre o inline a sus pasos."""
    if isinstance(ref, ast.Name):
        call = sc.assigns.get(ref.id)
        if call is None:
            return None
        return _parse_sub_pipeline(call, sc)
    if isinstance(ref, ast.Call) and _call_name(ref) == "Pipeline":
        return _parse_sub_pipeline(ref, sc)
    return None


def _find_final_pipeline(sc):
    """Busca el `model = Pipeline([... , ('clf', <Estimator>())])` final.
    Devuelve (var_name, preprocessor_ref, estimator_call) o None."""
    for name, call in sc.assigns.items():
        if _call_name(call) != "Pipeline":
            continue
        steps = _arg(call, 0) or _kw(call, "steps")
        if not isinstance(steps, ast.List):
            continue
        pre_ref = None
        est_call = None
        ok = True
        for item in steps.elts:
            if not isinstance(item, ast.Tuple) or len(item.elts) != 2:
                ok = False
                break
            comp = item.elts[1]
            cn = _call_name(comp)
            if cn == "ColumnTransformer" or (isinstance(comp, ast.Name) and _call_name(sc.assigns.get(comp.id)) == "ColumnTransformer"):
                pre_ref = comp
            elif cn in _ESTIMATORS:
                est_call = comp
            elif isinstance(comp, ast.Name) and comp.id in sc.assigns and _call_name(sc.assigns[comp.id]) == "ColumnTransformer":
                pre_ref = comp
            else:
                # paso desconocido en el pipeline final -> no reconocer
                ok = False
                break
        if ok and est_call is not None:
            return name, pre_ref, est_call
    return None


def _column_transformer_spec(ref, sc):
    """Resuelve un ColumnTransformer a [{role, cols, steps}]."""
    call = ref
    if isinstance(ref, ast.Name):
        call = sc.assigns.get(ref.id)
    if call is None or _call_name(call) != "ColumnTransformer":
        return None
    transformers = _arg(call, 0) or _kw(call, "transformers")
    if not isinstance(transformers, ast.List):
        return None
    spec = []
    for item in transformers.elts:
        if not isinstance(item, ast.Tuple) or len(item.elts) != 3:
            return None
        role = _const_str(item.elts[0]) or "col"
        tref = item.elts[1]
        cols_ref = item.elts[2]
        steps = _resolve_transformer(tref, sc)
        if steps is None:
            return None
        # columnas: nombre de lista registrada o lista inline de str
        cols = None
        if isinstance(cols_ref, ast.Name):
            cols = sc.feature_lists.get(cols_ref.id)
        else:
            cols = _list_of_str(cols_ref)
        if cols is None:
            return None
        spec.append({"role": role, "cols": cols, "steps": steps})
    return spec


def _lit(node):
    try:
        return _unparse(node)
    except Exception:
        return "None"


def detect_and_build(tree):
    """Punto de entrada. Si el modulo contiene el patron sklearn Pipeline +
    ColumnTransformer soportado, devuelve dict:
      {code, kinds, csv_path, label_col}
    con `code` = bloque pyspark.ml completo. Si no, devuelve None (el convertidor
    sigue su camino normal)."""
    sc = _scan_module(tree)
    final = _find_final_pipeline(sc)
    if not final:
        return None
    model_var, pre_ref, est_call = final
    if pre_ref is None:
        return None
    spec = _column_transformer_spec(pre_ref, sc)
    if not spec:
        return None

    est_name = _call_name(est_call)
    mllib_class, est_kind = _ESTIMATORS[est_name]

    # --- construir el bloque de codigo ---
    kinds = {"assembler", "evaluator", est_kind}
    numeric_imputed = []
    stages_pre = []   # stages antes de indexers/encoders
    indexers = []
    encoders = []
    cat_ohe_cols = []
    scaled_cols = []
    lines = []
    L = lines.append

    L("# sklearn Pipeline + ColumnTransformer -> pyspark.ml.Pipeline (equivalente).")
    L("# ColumnTransformer no existe en Spark: se aplana en una lista de stages.")

    label_col = sc.label_col or "label"
    L(f'label_col = "{label_col}"')
    L('label_indexer = StringIndexer(inputCol=label_col, outputCol="label", handleInvalid="keep")')
    kinds.add("onehot")  # StringIndexer vive en el import de onehot

    fillna_cols = []  # columnas categoricas con imputer most_frequent

    for part in spec:
        role = part["role"]
        cols = part["cols"]
        steps = part["steps"]
        has_imputer = next((s for s in steps if s["kind"] == "imputer"), None)
        has_scaler = any(s["kind"] == "scaler" for s in steps)
        has_onehot = any(s["kind"] == "onehot" for s in steps)

        if has_scaler or (has_imputer and has_imputer.get("strategy") in ("mean", "median") and not has_onehot):
            # rama NUMERICA
            cols_lit = "[" + ", ".join(repr(c) for c in cols) + "]"
            imp_out = [f"{c}_imp" for c in cols]
            imp_out_lit = "[" + ", ".join(repr(c) for c in imp_out) + "]"
            strat = (has_imputer or {}).get("strategy", "median") if has_imputer else "median"
            if strat not in ("mean", "median"):
                strat = "median"
            if has_imputer:
                L(f'imputer_{role} = Imputer(strategy="{strat}", inputCols={cols_lit}, outputCols={imp_out_lit})')
                assembler_in = imp_out
                kinds.add("imputer")
            else:
                assembler_in = cols
            asm_in_lit = "[" + ", ".join(repr(c) for c in assembler_in) + "]"
            L(f'assembler_{role}_num = VectorAssembler(inputCols={asm_in_lit}, outputCol="{role}_vec", handleInvalid="keep")')
            if has_scaler:
                L(f'scaler_{role} = StandardScaler(inputCol="{role}_vec", outputCol="{role}_scaled", withMean=True, withStd=True)')
                scaled_cols.append(f"{role}_scaled")
                kinds.add("scaler_std")
            else:
                scaled_cols.append(f"{role}_vec")
            if has_imputer:
                stages_pre.append(f"imputer_{role}")
            stages_pre.append(f"assembler_{role}_num")
            if has_scaler:
                stages_pre.append(f"scaler_{role}")
        elif has_onehot:
            # rama CATEGORICA
            if has_imputer and has_imputer.get("strategy") == "most_frequent":
                fillna_cols.extend(cols)
            for c in cols:
                indexers.append((c, f"{c}_idx"))
                encoders.append((f"{c}_idx", f"{c}_ohe"))
                cat_ohe_cols.append(f"{c}_ohe")
        else:
            # rama no clasificable -> abortar (defensivo)
            return None

    # fillna de categoricas (SimpleImputer most_frequent -> 'desconocido')
    if fillna_cols:
        fc = "[" + ", ".join(repr(c) for c in fillna_cols) + "]"
        L(f"# SimpleImputer(most_frequent) -> fillna('desconocido') + StringIndexer(handleInvalid='keep')")
        L(f'df = df.fillna("desconocido", subset={fc})')

    # indexers / encoders categoricos
    if indexers:
        idx_items = ", ".join(
            f'StringIndexer(inputCol={inp!r}, outputCol={out!r}, handleInvalid="keep")'
            for inp, out in indexers
        )
        L(f"indexers = [{idx_items}]")
        enc_items = ", ".join(
            f'OneHotEncoder(inputCol={inp!r}, outputCol={out!r}, handleInvalid="keep")'
            for inp, out in encoders
        )
        L(f"encoders = [{enc_items}]")

    # assembler final: numericas escaladas + one-hot categoricas
    final_inputs = scaled_cols + cat_ohe_cols
    fin_lit = "[" + ", ".join(repr(c) for c in final_inputs) + "]"
    L(f'assembler_final = VectorAssembler(inputCols={fin_lit}, outputCol="features", handleInvalid="keep")')

    # estimador con hiperparametros mapeados
    hp_map = _HYPERPARAMS.get(est_name, {})
    params = ['labelCol="label"', 'featuresCol="features"']
    for kw in getattr(est_call, "keywords", []):
        if kw.arg in hp_map and hp_map[kw.arg]:
            params.append(f"{hp_map[kw.arg]}={_lit(kw.value)}")
    L(f'{model_var}_rf = {mllib_class}({", ".join(params)})')

    # pipeline final
    pre_stages = "[label_indexer" + ("" if not stages_pre else ", " + ", ".join(stages_pre)) + "]"
    mid = " + indexers + encoders" if indexers else ""
    L(f"{model_var} = Pipeline(stages={pre_stages}{mid} + [assembler_final, {model_var}_rf])")

    # split + fit + evaluacion + guardado
    L("train_df, test_df = df.randomSplit([0.8, 0.2], seed=42)")
    L(f"{model_var}_fitted = {model_var}.fit(train_df)")
    L(f"_bnx_pred = {model_var}_fitted.transform(test_df)")
    L('for _mn in ("accuracy", "f1", "weightedPrecision", "weightedRecall"):')
    L('    _ev = MulticlassClassificationEvaluator(labelCol="label", predictionCol="prediction", metricName=_mn)')
    L('    print(f"{_mn}: {_ev.evaluate(_bnx_pred):.4f}")')
    L('_bnx_pred.select("label", "prediction", "probability").show(10, truncate=False)')
    L(f'{model_var}_fitted.write().overwrite().save("modelo_{model_var}")')
    L(f'print("[ok] modelo guardado en: modelo_{model_var}")')

    # kinds -> necesitamos Pipeline importado tambien
    kinds.add("pipeline")
    return {
        "code": "\n".join(lines),
        "kinds": kinds,
        "csv_path": sc.read_csv_path,
        "label_col": label_col,
    }
