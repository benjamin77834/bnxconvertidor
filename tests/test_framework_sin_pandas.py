"""El codigo que GENERA el framework (plantillas) y el CONVERTIDO no usan pandas/numpy/UDF.

pandas/numpy solo se permiten como ORACULO dentro de estos tests."""
import ast
import os
import re
import sys
import types
import zipfile

import pytest

from src import mlops_pkg as mp
from src.py2spark import convert_code

pyspark = pytest.importorskip("pyspark")

_RESIDUO = re.compile(r"toPandas|to_pandas|pandas_udf|applyInPandas|mapInPandas|pyspark\.pandas|pandas_api|"
                      r"(?<![\w.])udf\(|@udf|F\.udf|\bpd\.|\bnp\.")


def _imports(code):
    out = set()
    for n in ast.walk(ast.parse(code)):
        if isinstance(n, ast.Import):
            out |= {a.name.split(".")[0] for a in n.names}
        elif isinstance(n, ast.ImportFrom) and n.level == 0 and n.module:
            out.add(n.module.split(".")[0])
    return out


def _usos_pandas_ast(code):
    """Usos reales (AST, no cadenas/comentarios) de pandas/numpy/UDF en el codigo."""
    bad = []
    for n in ast.walk(ast.parse(code)):
        if isinstance(n, ast.Attribute) and n.attr in ("toPandas", "to_pandas", "pandas_api",
                                                       "applyInPandas", "mapInPandas", "udf", "pandas_udf"):
            bad.append(n.attr)
        if isinstance(n, ast.Name) and n.id in ("pd", "np", "pandas_udf", "udf"):
            bad.append(n.id)
    return bad


def _codigo_sin_comentarios(code):
    return "\n".join(l for l in code.splitlines() if not l.lstrip().startswith("#"))


def _paquete_completo(tmp_path):
    src = [{"name": "bin/jobs/rps/pivot/job.py", "code": "def run(kernel):\n    pass\n"},
           {"name": "bin/toolbox/kernel.py", "code": "class Kernel:\n    pass\n"},
           {"name": "job_1.py", "code": "import pandas as pd\ndf = pd.read_csv('a.csv')\ndf['x'] = df['a'] * 2\n"}]
    out = tmp_path / "p.zip"
    _, _, rep = mp.build_package_from_sources(
        src, convert_fn=convert_code, include_bank_libs=False, extra_steps=True, include_monitoring=True,
        out_path=str(out), py_target="py3.11")
    z = zipfile.ZipFile(out)
    base = "framework_mlops_v2_pkg/"
    return {n[len(base):]: z.read(n).decode("utf-8", "replace") for n in z.namelist()
            if n.startswith(base) and n.endswith(".py") and "/vendor/" not in n}, rep


def test_plantillas_generadas_no_importan_pandas_ni_numpy(tmp_path):
    files, rep = _paquete_completo(tmp_path)
    propias = {p: c for p, c in files.items()
               if p.startswith(("framework_mlops_v2/", "bnx_demo/")) or p in ("main.py", "check_env.py", "bnx_sparkconf.py", "setup.py")}
    assert propias
    for p, c in propias.items():
        if p.startswith("bnx_demo/fsrutas"):
            continue           # parche OPCIONAL de pandas.read_* para el DEMO del codigo del banco (try/except)
        assert not (_imports(c) & {"pandas", "numpy"}), p
        assert not _usos_pandas_ast(c), (p, _usos_pandas_ast(c))
    # el aggregate CONVERTIDO tampoco
    conv = files["framework_mlops_v2/aggregates/job_1.py"]
    assert "import pandas" not in _codigo_sin_comentarios(conv)
    meta = [r for r in rep if r.get("_meta")][0]
    assert "xgboost" in meta["pandas"]["texto"] or "ciencia" in meta["pandas"]["texto"]   # extra_steps => xgboost/sklearn


def test_ejemplos_convertidos_sin_residuos():
    for ex in mp.EXAMPLES:
        r = convert_code(ex["code"])
        assert r["ok"], ex["id"]
        cod = _codigo_sin_comentarios(r["code"])
        assert not _RESIDUO.search(cod), (ex["id"], _RESIDUO.search(cod), r["code"])
        assert "import pandas" not in cod and "import numpy" not in cod, ex["id"]
        assert not r["unsupported"], (ex["id"], r["unsupported"])


# ----------------------- monitoreo en Spark (oraculo numpy/pandas solo aqui) -----------------------
@pytest.fixture(scope="module")
def spark():
    from pyspark.sql import SparkSession
    s = (SparkSession.builder.master("local[1]").appName("mon").config("spark.ui.enabled", "false")
         .config("spark.driver.bindAddress", "127.0.0.1").getOrCreate())
    yield s


def _modulo(codigo, nombre):
    m = types.ModuleType(nombre)
    exec(codigo, m.__dict__)
    return m


def test_psi_y_dqc_en_spark_igual_al_oraculo_numpy(spark):
    np = pytest.importorskip("numpy")
    mon = _modulo(mp._MONITORING, "monitor_metrics_t").MonitorMetrics()
    datos = ["a"] * 60 + ["b"] * 30 + ["c"] * 10
    dev = {"a": 0.5, "b": 0.3, "c": 0.2}
    df = spark.createDataFrame([(x,) for x in datos], ["bin"])
    rc = np.array([0.6, 0.3, 0.1])
    rd = np.array([0.5, 0.3, 0.2])
    esperado = round(float(np.sum((rc - rd) * np.log(rc / rd))), 6)
    assert mon.psi(df, "bin", dev) == pytest.approx(esperado, abs=1e-6)
    # bin ausente en la poblacion actual -> epsilon (como antes)
    df2 = spark.createDataFrame([("a",)] * 10, ["bin"])
    e2 = float(np.sum((np.array([1.0, 1e-6, 1e-6]) - np.array([0.5, 0.3, 0.2]))
                      * np.log(np.array([1.0, 1e-6, 1e-6]) / np.array([0.5, 0.3, 0.2]))))
    assert mon.psi(df2, "bin", dev) == pytest.approx(round(e2, 6), abs=1e-5)
    # dqc: una sola pasada para todas las columnas
    d = spark.createDataFrame([(1, 10.0), (2, None), (None, 30.0), (4, 40.0)], "x int, y double")
    rep = mon.dqc(d, ["x", "y"])
    assert rep["x"]["null_pct"] == 25.0 and rep["y"]["null_pct"] == 25.0
    assert rep["x"]["n"] == 3 and rep["y"]["max"] == 40.0
    assert rep["y"]["mean"] == pytest.approx(float(np.mean([10.0, 30.0, 40.0])))
    assert rep["x"]["std"] == pytest.approx(float(np.std([1, 2, 4], ddof=1)))
    q = mon.quantile_bins(spark.createDataFrame([(float(i),) for i in range(101)], ["v"]), "v", 4)
    assert len(q) == 3 and q[1] == pytest.approx(50.0, abs=2)


def test_monitoreo_no_junta_filas_al_driver():
    src = mp._MONITORING
    assert ".collect()" not in src and "toPandas" not in src and "import math" not in src


# ----------------------- scoring xgboost: driver, solo features, sin pandas -----------------------
def test_scorer_xgboost_en_el_driver_sin_pandas(spark, monkeypatch):
    fake = types.ModuleType("xgboost")
    visto = {}

    class DMatrix(object):
        def __init__(self, data, feature_names=None):
            visto["data"], visto["names"] = data, feature_names

    class Booster(object):
        def load_model(self, p):
            visto["model"] = p

        def predict(self, dm):
            return [sum(f for f in fila if f == f) for fila in dm_data(dm)]

    def dm_data(dm):
        return visto["data"]
    fake.DMatrix, fake.Booster = DMatrix, Booster
    monkeypatch.setitem(sys.modules, "xgboost", fake)
    sc = _modulo(mp._SCORING, "scorer_t").Scorer("m.xgb")
    df = spark.createDataFrame([(1, 1.0, 2.0), (2, 3.0, None)], "id int, a double, b double")
    out = sc.score(df, ["a", "b"], out_col="s")
    filas = {r["id"]: r["s"] for r in out.collect()}
    assert filas == {1: 3.0, 2: 3.0}              # None -> NaN -> ignorado por el fake
    assert visto["names"] == ["a", "b"] and "_bnx_rid" not in out.columns
    with pytest.raises(ValueError, match="mas de 1 filas"):
        sc.score(df, ["a", "b"], max_rows=1)
    assert "pandas" not in _imports(mp._SCORING) and "toPandas" not in mp._SCORING


def test_pnl_template_sin_pandas():
    assert "pandas" not in _imports(mp._PNL.split('"""', 2)[2])
    ns = {}
    # _build_query en Python puro (sin BaseAggregate real)
    cuerpo = mp._PNL.split("class PnlAggregate(BaseAggregate):")[1].split("    def _aggregate_df")[0]
    exec("class BaseAggregate: pass\nclass P(BaseAggregate):" + cuerpo, ns)
    q = ns["P"]()._build_query({"variable": ["a", "", "zz"], "agg": ["sum", "max", "min"]}, ["k"], ["a", "k"])
    assert q == "SELECT k,sum(a) as a FROM tempPnl GROUP BY k"
