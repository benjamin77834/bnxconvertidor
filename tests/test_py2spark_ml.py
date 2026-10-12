# Tests del reconocimiento de patrones ML (sklearn) en py2spark.
# La preparacion de datos (pandas) se traduce; el modelo ML se CONVIERTE a codigo
# Spark MLlib (pyspark.ml) real (esqueleto). El codigo generado SIEMPRE compila.
import ast
import glob
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.py2spark import convert_code  # noqa: E402


def _conv(src):
    r = convert_code(src)
    ast.parse(r["code"])  # nunca debe romper
    return r


def test_train_test_split_to_randomsplit():
    r = _conv(
        "import pandas as pd\n"
        "from sklearn.model_selection import train_test_split\n"
        "df = pd.read_csv('d.csv')\n"
        "X_tr, X_te, y_tr, y_te = train_test_split(df, df, test_size=0.2)\n"
    )
    # se traduce a randomSplit (MLlib), no queda train_test_split ejecutable
    assert "randomSplit(" in r["code"]
    code_lines = [l for l in r["code"].splitlines() if not l.lstrip().startswith("#")]
    assert not any("train_test_split(" in l for l in code_lines)


def test_logistic_regression_generates_mllib():
    r = _conv(
        "import pandas as pd\n"
        "from sklearn.linear_model import LogisticRegression\n"
        "df = pd.read_csv('d.csv')\n"
        "m = LogisticRegression(max_iter=1000)\n"
        "m.fit(df, df)\n"
        "p = m.predict(df)\n"
    )
    # genera el estimador MLlib real con import y hiperparametro mapeado
    assert "from pyspark.ml.classification import LogisticRegression" in r["code"]
    assert "LogisticRegression(maxIter=1000" in r["code"]
    assert "featuresCol=\"features\"" in r["code"]
    # .fit y .predict -> fit()/transform() MLlib
    assert ".fit(" in r["code"] and ".transform(" in r["code"]


def test_kmeans_generates_mllib():
    r = _conv(
        "import pandas as pd\n"
        "from sklearn.cluster import KMeans\n"
        "df = pd.read_csv('d.csv')\n"
        "km = KMeans(n_clusters=5, random_state=0)\n"
        "df['seg'] = km.fit_predict(df)\n"
    )
    assert "from pyspark.ml.clustering import KMeans" in r["code"]
    assert "KMeans(k=5" in r["code"]
    assert "seed=0" in r["code"]


def test_standard_scaler_generates_mllib():
    r = _conv(
        "import pandas as pd\n"
        "from sklearn.preprocessing import StandardScaler\n"
        "df = pd.read_csv('d.csv')\n"
        "cols = ['a', 'b']\n"
        "scaler = StandardScaler()\n"
        "df[cols] = scaler.fit_transform(df[cols])\n"
    )
    assert "from pyspark.ml.feature import StandardScaler" in r["code"]
    assert "StandardScaler(inputCol=" in r["code"]
    assert "VectorAssembler" in r["code"]  # se menciona el ensamblado de features


def test_get_dummies_generates_mllib():
    r = _conv(
        "import pandas as pd\n"
        "df = pd.read_csv('d.csv')\n"
        "df = pd.get_dummies(df, columns=['seg'])\n"
    )
    assert "StringIndexer" in r["code"] and "OneHotEncoder" in r["code"]


def test_vectorassembler_import_present_when_estimator():
    r = _conv(
        "import pandas as pd\n"
        "from sklearn.ensemble import RandomForestClassifier\n"
        "df = pd.read_csv('d.csv')\n"
        "rf = RandomForestClassifier(n_estimators=100, max_depth=8)\n"
    )
    assert "from pyspark.ml.feature import VectorAssembler" in r["code"]
    assert "RandomForestClassifier(numTrees=100" in r["code"]
    assert "maxDepth=8" in r["code"]


def test_all_examples_compile():
    base = os.path.join(os.path.dirname(__file__), "..", "examples", "py2spark")
    files = sorted(glob.glob(os.path.join(base, "*.py")))
    assert files, "no se encontraron ejemplos"
    for f in files:
        r = convert_code(open(f, encoding="utf-8").read())
        assert r["ok"], f
        ast.parse(r["code"])  # debe compilar


def test_pure_pandas_example_no_mllib():
    # Los ejemplos de pandas puro (01, 05) NO deben generar codigo MLlib.
    base = os.path.join(os.path.dirname(__file__), "..", "examples", "py2spark")
    for name in ("01_feature_prep.py", "05_etl_join_agg.py"):
        f = os.path.join(base, name)
        if not os.path.exists(f):
            continue
        r = convert_code(open(f, encoding="utf-8").read())
        assert "pyspark.ml" not in r["code"], name


def test_xgboost_neutralized():
    # xgb.XGBClassifier(...) no tiene equivalente MLlib: TODO honesto, no NameError.
    import ast as _ast
    from src.py2spark import convert_code
    r = convert_code(
        'import pandas as pd\n'
        'import xgboost as xgb\n'
        'df = pd.read_csv("f.csv")\n'
        'model = xgb.XGBClassifier(n_estimators=100)\n'
        'model.fit(df)\n'
    )
    assert r["ok"]
    _ast.parse(r["code"])  # Python valido
    code_lines = [ln for ln in r["code"].splitlines()
                  if ln.strip() and not ln.lstrip().startswith("#")]
    # la construccion cruda de xgb NO queda como codigo ejecutable
    assert not any("xgb.XGBClassifier" in ln for ln in code_lines)
    assert "TODO py2spark" in r["code"]


def test_lightgbm_neutralized():
    import ast as _ast
    from src.py2spark import convert_code
    r = convert_code(
        'import pandas as pd\n'
        'import lightgbm as lgb\n'
        'df = pd.read_csv("f.csv")\n'
        'm = lgb.LGBMClassifier(n_estimators=200)\n'
    )
    assert r["ok"]
    _ast.parse(r["code"])
    code_lines = [ln for ln in r["code"].splitlines()
                  if ln.strip() and not ln.lstrip().startswith("#")]
    assert not any("lgb.LGBMClassifier" in ln for ln in code_lines)
    assert "TODO py2spark" in r["code"]


def test_stacking_classifier_neutralized():
    import ast as _ast
    from src.py2spark import convert_code
    r = convert_code(
        'import pandas as pd\n'
        'from sklearn.ensemble import StackingClassifier\n'
        'from sklearn.linear_model import LogisticRegression\n'
        'df = pd.read_csv("f.csv")\n'
        'st = StackingClassifier(estimators=[], final_estimator=LogisticRegression())\n'
    )
    assert r["ok"]
    _ast.parse(r["code"])
    assert "TODO py2spark" in r["code"]


def test_rf_label_string_and_evaluators():
    # RandomForest + CSV: label string -> StringIndexer; split train/test;
    # accuracy_score/classification_report -> Evaluators de Spark.
    from src.py2spark import convert_code
    r = convert_code(
        "import pandas as pd\n"
        "from sklearn.ensemble import RandomForestClassifier\n"
        "from sklearn.metrics import accuracy_score, classification_report\n"
        "df = pd.read_csv('datos.csv')\n"
        "modelo = RandomForestClassifier(n_estimators=100)\n"
        "modelo.fit(df)\n"
        "y_pred = modelo.predict(df)\n"
        "acc = accuracy_score(df, y_pred)\n"
        "print(classification_report(df, y_pred))\n"
    )
    code = r["code"]
    # 1. label string -> StringIndexer(outputCol='label_indexed')
    assert "StringIndexer" in code and "label_indexed" in code
    # 2. labelCol dinamico (_label_col), no hardcode 'label'
    assert "labelCol=_label_col" in code
    # 3. split train/test 80/20 seed 42 + fit sobre train_df
    assert "randomSplit([0.8, 0.2], seed=42)" in code
    assert "modelo.fit(_train)" in code
    # 4. guard de features vacias
    assert "no hay columnas de features" in code
    # 5. Evaluators (no sklearn)
    assert "MulticlassClassificationEvaluator" in code
    assert 'metricName="accuracy"' in code
    assert "weightedPrecision" in code and "weightedRecall" in code
    assert "accuracy_score" not in "\n".join(
        ln for ln in code.splitlines() if not ln.lstrip().startswith("#"))


# ---------------------------------------------------------------------------
# sklearn Pipeline + ColumnTransformer -> pyspark.ml.Pipeline (reconocedor).
# El patron COMPLETO soportado (SimpleImputer/StandardScaler/OneHotEncoder +
# clasificador) se traduce a un pipeline MLlib runnable, SIN TODO. Si el patron
# trae algo no soportado, degrada a TODO honesto (no genera basura).
# ---------------------------------------------------------------------------
_SK_PIPELINE_SRC = (
    "import pandas as pd\n"
    "from sklearn.compose import ColumnTransformer\n"
    "from sklearn.pipeline import Pipeline\n"
    "from sklearn.impute import SimpleImputer\n"
    "from sklearn.preprocessing import StandardScaler, OneHotEncoder\n"
    "from sklearn.ensemble import RandomForestClassifier\n"
    "from sklearn.model_selection import train_test_split\n"
    "from sklearn.metrics import classification_report\n"
    "df = pd.read_csv('clientes.csv')\n"
    "numeric_features = ['edad', 'ingreso']\n"
    "categorical_features = ['plan', 'region']\n"
    "X = df[numeric_features + categorical_features]\n"
    "y = df['churn']\n"
    "numeric_transformer = Pipeline(steps=[('imputer', SimpleImputer(strategy='median')), ('scaler', StandardScaler())])\n"
    "categorical_transformer = Pipeline(steps=[('imputer', SimpleImputer(strategy='most_frequent')), ('onehot', OneHotEncoder(handle_unknown='ignore'))])\n"
    "preprocessor = ColumnTransformer(transformers=[('num', numeric_transformer, numeric_features), ('cat', categorical_transformer, categorical_features)])\n"
    "model = Pipeline(steps=[('preprocessor', preprocessor), ('classifier', RandomForestClassifier(n_estimators=150, max_depth=12, min_samples_leaf=5, random_state=42, n_jobs=-1))])\n"
    "X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)\n"
    "model.fit(X_train, y_train)\n"
    "print(classification_report(y_test, model.predict(X_test)))\n"
)


def test_sklearn_pipeline_columntransformer_to_mllib():
    r = _conv(_SK_PIPELINE_SRC)
    code = r["code"]
    # sin construcciones sin soportar (cero TODO reales). Nota: el preambulo
    # contiene la frase "# TODO py2spark:" como instruccion; eso NO es un TODO
    # real. Verificamos que no haya LINEAS de TODO real emitidas.
    assert r["unsupported"] == []
    _real_todos = [l for l in code.splitlines() if l.lstrip().startswith("# TODO py2spark:")]
    assert _real_todos == []
    # el pipeline MLlib esta completo
    assert "pyspark.ml import Pipeline" in code
    assert "Imputer(strategy=\"median\"" in code
    assert "StandardScaler(" in code
    assert "StringIndexer(" in code and "OneHotEncoder(" in code
    assert "VectorAssembler(" in code and 'outputCol="features"' in code
    assert "RandomForestClassifier(" in code and "numTrees=150" in code
    assert "maxDepth=12" in code and "minInstancesPerNode=5" in code
    assert "Pipeline(stages=[" in code
    # las columnas numericas se castean a double ANTES del Imputer (Spark exige
    # tipo numerico; si el CSV trae vacios se infieren string -> IllegalArgument).
    assert 'F.col(\'edad\').cast("double")' in code
    assert 'F.col(\'ingreso\').cast("double")' in code
    assert ".fit(train_df)" in code and ".transform(test_df)" in code
    assert "MulticlassClassificationEvaluator(" in code
    assert ".write().overwrite().save(" in code
    # label inferido de y = df['churn']
    assert 'label_col = "churn"' in code
    # no quedan residuos de la version pandas/sklearn
    for ln in code.splitlines():
        s = ln.strip()
        if s.startswith("#"):
            continue
        assert "df.filter(" not in s
        assert "train_test_split(" not in s
        assert not s.startswith("X =") and not s.startswith("y =")


def test_sklearn_pipeline_unsupported_transformer_degrades_to_todo():
    # Pipeline con un transformer NO soportado (PCA): NO debe fingir equivalencia,
    # debe degradar a TODO honesto.
    r = _conv(
        "import pandas as pd\n"
        "from sklearn.pipeline import Pipeline\n"
        "from sklearn.decomposition import PCA\n"
        "from sklearn.ensemble import RandomForestClassifier\n"
        "df = pd.read_csv('d.csv')\n"
        "model = Pipeline(steps=[('pca', PCA(n_components=3)), ('clf', RandomForestClassifier())])\n"
    )
    assert r["unsupported"]  # hay al menos un TODO
    assert "TODO py2spark:" in r["code"]
    # no debe haber inventado un pipeline MLlib
    assert "Pipeline(stages=[" not in r["code"]
