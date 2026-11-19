"""Recursos de Spark y rendimiento del Framework MLOps v2 (src/bnx_sparkconf.py + plantillas de mlops_pkg).
Sin red y sin YARN: el spark-submit del cluster es un script falso que imprime sus argumentos."""
import importlib.util
import json
import os
import stat
import subprocess
import sys
import zipfile

import pytest

from src import bnx_sparkconf as bs
from src import mlops_pkg as mp

SPARK_JSON = {
    "default": {
        "spark.yarn.queue": "root.cognitive",
        "spark.dynamicAllocation.enabled": "true",
        "spark.dynamicAllocation.minExecutors": "0",
        "spark.dynamicAllocation.initialExecutors": "50",
        "spark.dynamicAllocation.maxExecutors": "300",
        "spark.executor.cores": "5",
        "spark.executor.memory": "50g",
        "spark.executor.memoryOverhead": "10g",
        "spark.driver.memory": "24g",
        "spark.sql.shuffle.partitions": "25",
    },
    "logging_level": "WARN",
    "spark_config": "default",
    "spark_queue_uat": "root.process_val_uat",
    "mi_modelo": {"spark_config": {"spark.yarn.queue": "root.cognitive", "spark.executor.memory": "32G",
                                   "spark.executor.instances": "64"}},
}


@pytest.fixture
def settings(tmp_path):
    d = tmp_path / "settings"
    d.mkdir()
    (d / "spark.json").write_text(json.dumps(SPARK_JSON))
    return str(d)


# ---------------------------------------------------------------- spark.json -> conf de lanzamiento
def test_spark_json_bloque_default_y_cola_uat(settings):
    conf, origen = bs.leer_spark_json(settings, "prod")
    assert conf["spark.yarn.queue"] == "root.cognitive"
    assert conf["spark.executor.memory"] == "50g" and conf["spark.executor.cores"] == "5"
    assert "logging_level" not in conf and "default" in origen
    assert bs.leer_spark_json(settings, "uat")[0]["spark.yarn.queue"] == "root.process_val_uat"


def test_spark_json_bloque_de_modelo(settings):
    conf, _ = bs.leer_spark_json(settings, "prod", modelo="mi_modelo")
    assert conf["spark.executor.instances"] == "64" and conf["spark.executor.memory"] == "32G"


def test_spark_json_inexistente(tmp_path):
    assert bs.leer_spark_json(str(tmp_path), "uat") == ({}, None)
    assert bs.leer_spark_json(None) == ({}, None)


def test_prioridad_defecto_cfg_sparkjson_env(settings):
    cfg = {"spark": {"conf": {"spark.sql.shuffle.partitions": "99", "spark.executor.memory": "1g",
                              "spark.master": "local[2]", "spark.app.x": True}}}
    # sin settings: manda el cfg sobre el defecto; spark.master nunca pasa
    conf, _ = bs.conf_cluster(None, None, cfg, environ={})
    assert conf["spark.sql.shuffle.partitions"] == "99"
    assert conf["spark.dynamicAllocation.enabled"] == "true" and conf["spark.app.x"] == "true"
    assert "spark.master" not in conf and "spark.yarn.queue" not in conf
    # con settings: manda el spark.json
    conf, origen = bs.conf_cluster(settings, "uat", cfg, environ={})
    assert conf["spark.sql.shuffle.partitions"] == "25" and conf["spark.executor.memory"] == "50g"
    assert origen["spark.yarn.queue"] == "spark.json"
    # BNX_DRIVER_MEMORY y BNX_SPARK_CONF mandan sobre todo
    conf, _ = bs.conf_cluster(settings, "uat", cfg, environ={
        "BNX_DRIVER_MEMORY": "8g", "BNX_SPARK_CONF": "spark.executor.memory=20g; spark.yarn.queue=root.x"})
    assert conf["spark.driver.memory"] == "8g" and conf["spark.executor.memory"] == "20g"
    assert conf["spark.yarn.queue"] == "root.x"


def test_dir_settings_busca_junto_al_config(settings, tmp_path):
    sub = tmp_path / "settings" / "m" / "x"
    sub.mkdir(parents=True)
    cfg = sub / "pivot.json"
    cfg.write_text("{}")
    assert bs.dir_settings(None, str(cfg), env={}) == settings
    assert bs.dir_settings("/a", str(cfg), env={"CONF_PATH": "/b"}) == "/a"
    assert bs.dir_settings(None, None, env={"CONF_PATH": "/b"}) == "/b"


# ---------------------------------------------------------------- demo vs real
def test_demo_vs_real():
    assert bs.es_demo(None, None, False)
    assert bs.es_demo("cfg.json", "s", True)          # --demo manda
    assert not bs.es_demo("cfg.json", None, False)
    assert not bs.es_demo(None, "bin/settings", False)
    assert bs.nucleos("local[3]") == 3 and bs.nucleos("local[*]") >= 1
    assert bs.shuffle_local(2) == 8 and bs.shuffle_local(10) == 20


def test_memoria_driver_local():
    assert bs.memoria_driver_local(None, {"BNX_DRIVER_MEMORY": "4g"}) == ("4g", "BNX_DRIVER_MEMORY")
    assert bs.memoria_driver_local({"spark": {"conf": {"spark.driver.memory": "6g"}}}, {})[0] == "6g"


# ---------------------------------------------------------------- Python en los workers
@pytest.mark.parametrize("linea,patron", [
    ("f = udf(lambda x: x, StringType())", "udf"),
    ("@F.udf(returnType=T.StringType())", "udf"),
    ("spark.udf.register('q', quita)", "udf"),
    ("@pandas_udf('double')", "pandas_udf"),
    ("df.groupBy('a').applyInPandas(fn, schema)", "applyInPandas/mapInPandas/mapInArrow"),
    ("df.mapInPandas(fn, schema)", "applyInPandas/mapInPandas/mapInArrow"),
    ("x = df.rdd.map(lambda r: r)", ".rdd"),
    ("rdd_x.flatMap(f)", "rdd.map/flatMap/foreach/mapPartitions"),
    ("df.foreachPartition(f)", "foreach/foreachPartition/mapPartitions/foreachBatch"),
    ("df.foreach(f)", "foreach/foreachPartition/mapPartitions/foreachBatch"),
    ("sc.parallelize([1, 2], 2)", "sparkContext.parallelize"),
    ("import pyspark.pandas as ps", "pandas_api/pyspark.pandas"),
    ("psdf = df.pandas_api()", "pandas_api/pyspark.pandas"),
    ("from xgboost.spark import SparkXGBClassifier", "xgboost.spark/SparkXGB"),
])
def test_detecta_python_en_workers(linea, patron):
    assert patron in [h["patron"] for h in bs.detectar_python_en_workers(linea + "\n")]


def test_no_marca_sql_dataframe_ni_pandas_local():
    code = ("import pandas as pd\n"
            "df = spark.sql('select 1')\n"
            "df = df.groupBy('a').agg(F.sum('b')).withColumn('c', F.when(F.col('a') > 1, 1))\n"
            "pdf = df.toPandas()\n"
            "pdf['x'] = pdf['a'].map(lambda v: v + 1)\n"
            "# df.rdd.map(f)  y udf(f) comentados\n"
            "out = [x for x in range(3)]\n")
    assert bs.detectar_python_en_workers(code) == []


def test_udf_con_sklearn_trae_nota_y_python2_no_rompe():
    h = bs.detectar_python_en_workers("import sklearn\nprint 'x'\nf = udf(g, T)\n")
    assert h and h[0]["linea"] == 3 and "sklearn" in h[0]["nota"]


def test_tabla_de_tiempos():
    t = bs.tabla_tiempos([{"etapa": "extract", "nombre": "a", "seg": 9.0, "particiones": 10, "archivos": 4, "estado": "OK"},
                          {"etapa": "aggregate", "nombre": "b", "seg": 1.0, "estado": "OK"}], "yarn", "application_1")
    assert "master=yarn" in t and "application_1" in t and "TOTAL" in t and "extract" in t
    assert "Lo mas lento: extract 'a'" in t and "90%" in t


# ---------------------------------------------------------------- paquete generado
def _convert(code):
    return {"ok": True, "code": "df_out = df  # CONVERTIDO", "warnings": [], "unsupported": []}


def _build(tmp_path, fuentes):
    out = tmp_path / "pkg.zip"
    _, _, report = mp.build_package_from_sources(fuentes, convert_fn=_convert, include_bank_libs=False,
                                                 out_path=str(out), py_target="py3.11")
    zipfile.ZipFile(out).extractall(tmp_path / "pkg")
    return str(tmp_path / "pkg" / "framework_mlops_v2_pkg"), report


FUENTES = [{"name": "a.py", "code": "import pandas as pd\ndf_out = df\n"},
           {"name": "u.py", "code": "from pyspark.sql.functions import udf\nf = udf(lambda x: x)\ndf_out = df\n"}]


def test_paquete_trae_helper_y_reporta_workers(tmp_path):
    pkg, report = _build(tmp_path, FUENTES)
    assert os.path.isfile(os.path.join(pkg, "bnx_sparkconf.py"))
    meta = [r for r in report if r.get("_meta")][0]
    assert any("u.py" in f or f.endswith("/u.py") for f in meta["workers_python"])
    assert "Python 3.11" in meta["workers_python_aviso"]
    notas = open(os.path.join(pkg, "NOTAS_EJECUCION.md"), encoding="utf-8").read()
    for frase in ("sin instalar en otros nodos", "BNX_ENVIAR_VENV", "toPandas", "local[*]", "spark.json"):
        assert frase in notas


def test_helper_del_paquete_es_python38():
    import ast
    ast.parse(open(bs.__file__, encoding="utf-8").read(), feature_version=(3, 8))


def test_run_sh_sintaxis_y_conf_en_cluster(tmp_path, settings):
    pkg, _ = _build(tmp_path, FUENTES)
    assert subprocess.run(["bash", "-n", os.path.join(pkg, "run.sh")]).returncode == 0
    # .venv falso + spark-submit falso
    vb = os.path.join(pkg, ".venv", "bin")
    os.makedirs(vb)
    open(os.path.join(vb, "python"), "w").write('#!/bin/bash\nexec "%s" "$@"\n' % sys.executable)
    os.chmod(os.path.join(vb, "python"), 0o755)
    open(os.path.join(vb, "activate"), "w").write('export PATH="$PWD/.venv/bin:$PATH"\n')
    fake = tmp_path / "fake-submit"
    fake.write_text('#!/bin/bash\nfor a in "$@"; do echo "ARG:$a"; done\n')
    fake.chmod(fake.stat().st_mode | stat.S_IEXEC)
    env = {k: v for k, v in os.environ.items() if not k.startswith(("BNX_", "SPARK_", "CONF_PATH"))}
    env.update(BNX_SPARK="cluster", BNX_SPARK_SUBMIT=str(fake), HADOOP_CONF_DIR="/x", BNX_SPARK_CONF="spark.executor.memory=20g")
    r = subprocess.run(["bash", "run.sh", "--settings", settings, "--env", "uat", "--extract-only"],
                       cwd=pkg, env=env, capture_output=True, text=True, timeout=120)
    args = [l[4:] for l in r.stdout.splitlines() if l.startswith("ARG:")]
    assert args[:4] == ["--master", "yarn", "--deploy-mode", "client"], r.stdout + r.stderr
    confs = [args[i + 1] for i, a in enumerate(args) if a == "--conf"]
    assert "spark.yarn.queue=root.process_val_uat" in confs
    assert "spark.dynamicAllocation.maxExecutors=300" in confs and "spark.executor.cores=5" in confs
    assert "spark.executor.memory=20g" in confs and "spark.executor.memory=50g" not in confs
    assert "spark.io.compression.codec=lz4" in confs
    assert "--archives" not in args          # BNX_ENVIAR_VENV apagado por defecto
    assert "main.py" in args and args[-1] == "--extract-only"
    assert "[spark-conf]" in r.stdout


# ---------------------------------------------------------------- extraccion sin relectura
def _cargar_main(pkg):
    pytest.importorskip("pyspark")
    sys.path.insert(0, pkg)
    try:
        spec = importlib.util.spec_from_file_location("bnx_main_t", os.path.join(pkg, "main.py"))
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        return mod
    finally:
        sys.path.remove(pkg)


class _DF:
    def __init__(self):
        self.write = self
    def mode(self, m):
        return self
    def parquet(self, p):
        self.dest = p


class _Spark:
    def __init__(self):
        self.reads, self.pre = 0, 0
        class _R:
            def __init__(s, o):
                s.o = o
            def parquet(s, p):
                s.o.reads += 1
                class _C:
                    def count(_):
                        return 42
                return _C()
        self.read = _R(self)
        class _SC:
            master, applicationId = "local[*]", "app-1"
        self.sparkContext = _SC()
    def sql(self, q):
        return _DF()


def test_extract_no_relee_y_registra_tiempos(tmp_path, monkeypatch):
    pkg, _ = _build(tmp_path, FUENTES)
    m = _cargar_main(pkg)
    monkeypatch.setattr(m, "_fs_parquet_files", lambda spark, p: 3)
    monkeypatch.setattr(m, "_fs_uri", lambda spark, p: p)
    llamadas = []
    monkeypatch.setattr(m, "_preflight", lambda spark, chk: llamadas.append(1))
    src = {"a": {"table_name": "a", "query": "select 1", "_check": {"db": "d", "table": "t", "columns": []}}}
    monkeypatch.delenv("BNX_CONTAR_FILAS", raising=False)
    monkeypatch.delenv("BNX_PREFLIGHT", raising=False)
    sp = _Spark()
    assert m._extract_sources(sp, ["a"], src, str(tmp_path / "prev"), str(tmp_path)) == []
    assert sp.reads == 0 and llamadas == [1]
    ex = [t for t in m._TIEMPOS if t["etapa"] == "extract"][0]
    assert ex["archivos"] == 3 and ex["filas"] is None and ex["estado"] == "OK"
    # con BNX_CONTAR_FILAS=1: UNA pasada; con BNX_PREFLIGHT=0 no hay preflight
    monkeypatch.setenv("BNX_CONTAR_FILAS", "1")
    monkeypatch.setenv("BNX_PREFLIGHT", "0")
    sp = _Spark()
    m._extract_sources(sp, ["a"], src, str(tmp_path / "prev"), str(tmp_path))
    assert sp.reads == 1 and llamadas == [1]
    assert [t for t in m._TIEMPOS if t["etapa"] == "extract"][-1]["filas"] == 42
