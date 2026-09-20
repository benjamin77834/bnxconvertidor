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
