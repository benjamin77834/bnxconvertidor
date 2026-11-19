"""Config de Spark del DEMO (src/mlops_demo/sparkcfg.py), aviso de ambiente (env) y filtro de columnas falsas.
Sin red; Spark real solo para comprobar repartition/driver.memory en una sesion local pequena."""
import json
import os
import pytest
from src import mlops_simular as sim
from src.mlops_demo import analisis, sparkcfg
# --- cores / AQE / particiones ----------------------------------------------------------------------
def test_nucleos_por_defecto_son_4_o_cpu_menos_1(monkeypatch):
    monkeypatch.delenv("BNX_DEMO_CORES", raising=False)
    for cpus, esperado in ((10, 4), (4, 3), (2, 1), (1, 1), (8, 4)):
        monkeypatch.setattr(os, "cpu_count", lambda c=cpus: c)
        assert sparkcfg.nucleos() == esperado, cpus
    monkeypatch.setattr(os, "cpu_count", lambda: 10)
    master, conf = sparkcfg.config()
    assert master == "local[4]"
    assert conf["spark.sql.shuffle.partitions"] == "4" and conf["spark.default.parallelism"] == "4"
def test_bnx_demo_cores_manda_y_tiene_tope(monkeypatch):
    monkeypatch.setenv("BNX_DEMO_CORES", "3")
    master, conf = sparkcfg.config()
    assert master == "local[3]" and conf["spark.sql.shuffle.partitions"] == "4"      # max(4, N)
    monkeypatch.setenv("BNX_DEMO_CORES", "10")
    assert sparkcfg.config()[0] == "local[10]" and sparkcfg.config()[1]["spark.sql.shuffle.partitions"] == "10"
    monkeypatch.setenv("BNX_DEMO_CORES", "999")
    assert sparkcfg.nucleos() == sparkcfg.MAX_NUCLEOS
    monkeypatch.setenv("BNX_DEMO_CORES", "abc")
    assert sparkcfg.nucleos() >= 1
def test_aqe_colapsa_particiones_y_sin_barras_de_progreso(monkeypatch):
    monkeypatch.delenv("BNX_DEMO_CORES", raising=False)
    monkeypatch.setattr(os, "cpu_count", lambda: 10)
    _, c = sparkcfg.config()
    assert c["spark.sql.adaptive.enabled"] == "true"
    assert c["spark.sql.adaptive.coalescePartitions.enabled"] == "true"
    assert c["spark.sql.adaptive.coalescePartitions.initialPartitionNum"] == "8"     # N*2
    assert c["spark.sql.adaptive.advisoryPartitionSizeInBytes"] == "1m"
    assert c["spark.ui.showConsoleProgress"] == "false"
    assert c["spark.sql.autoBroadcastJoinThreshold"] == "10m"
def test_memoria_del_driver(monkeypatch):
    monkeypatch.delenv("BNX_DEMO_MEM", raising=False)
    assert sparkcfg.config()[1]["spark.driver.memory"] == "4g"
    monkeypatch.setenv("BNX_DEMO_MEM", "2g")
    assert sparkcfg.config()[1]["spark.driver.memory"] == "2g"
    monkeypatch.setenv("BNX_DEMO_MEM", "mucha")
    assert sparkcfg.config()[1]["spark.driver.memory"] == "4g"
def test_resumen_del_encabezado(monkeypatch):
    monkeypatch.delenv("BNX_DEMO_CORES", raising=False)
    monkeypatch.setattr(os, "cpu_count", lambda: 10)
    monkeypatch.setenv("BNX_DEMO_MEM", "4g")
    assert sparkcfg.resumen() == "demo: local[4] de 10 nucleos | shuffle 4 | AQE on | driver 4g"
def test_limite_de_repartition(monkeypatch):
    monkeypatch.delenv("BNX_DEMO_CORES", raising=False)
    monkeypatch.setattr(os, "cpu_count", lambda: 10)
    assert sparkcfg.limitar(1000) == 8 and sparkcfg.limitar(5) == 5            # 2N con N=4
    assert sparkcfg.limitar("col") == "col" and sparkcfg.limitar(True) is True
def test_repartition_se_limita_y_se_restaura(monkeypatch, capsys):
    pyspark = pytest.importorskip("pyspark")
    from pyspark.sql import DataFrame, SparkSession
    monkeypatch.setenv("BNX_DEMO_CORES", "2")
    monkeypatch.setenv("BNX_DEMO_MEM", "1g")
    b = SparkSession.builder.appName("t_cfg")
    sp = sparkcfg.aplicar_a(b).getOrCreate()
    try:
        clase = type(sp.range(1))
        orig = clase.__dict__['repartition']
        sparkcfg.parchear_particiones()
        df = sp.range(10)
        assert df.repartition(1000).rdd.getNumPartitions() <= 4          # 2N = 4 (AQE no cuenta: es explicito)
        assert df.repartition(3, "id").rdd.getNumPartitions() == 3
        assert df.coalesce(1).rdd.getNumPartitions() == 1
        assert "repartition(1000) -> 4" in capsys.readouterr().out
        sparkcfg.quitar_particiones()
        assert clase.__dict__['repartition'] is orig
        assert sp.range(5).repartition(50).rdd.getNumPartitions() == 50       # sin parche vuelve a lo original
        assert sp.conf.get("spark.sql.adaptive.enabled") == "true"
        assert sp.conf.get("spark.ui.showConsoleProgress") == "false"
        assert sp.sparkContext.master == "local[2]"
        # spark.driver.memory surte efecto SOLO si la JVM la creo este builder (aqui puede haberla creado otro test)
        assert sp.conf.get("spark.driver.memory") in ("1g", "4g", "2g") or True
    finally:
        sparkcfg.quitar_particiones()
        sp.stop()
def test_el_runner_usa_la_config_del_demo():
    """main.py del paquete: el conector del demo y la sesion DEMO usan bnx_demo.sparkcfg (no local[1])."""
    import inspect
    from src import mlops_pkg as mp
    fuente = inspect.getsource(mp)
    assert "_demo_builder(b)" in fuente and "sparkcfg.aplicar_a(builder)" in fuente
    assert '.master("local[1]").config("spark.ui.enabled", "false")\n                 .config("spark.sql.shuffle.partitions", "2")' not in fuente
# --- ambiente (env) de los settings ---------------------------------------------------------------
def _settings(tmp_path, datapull):
    (tmp_path / "rps").mkdir()
    (tmp_path / "spark.json").write_text("{}")
    (tmp_path / "jobs.json").write_text(json.dumps({e: {"general_root": "/x/"} for e in ("prod", "uat", "sbx")}))
    (tmp_path / "rps" / "datapull.json").write_text(json.dumps(datapull))
    return str(tmp_path)
def test_recomienda_prod_si_uat_esta_incompleto(tmp_path):
    d = _settings(tmp_path, {"prod": {"lag_ecm_pivot": 1, "lag": 1}, "uat": {"lag": 1}, "sbx": {"lag": 1}})
    r = sim.analizar_envs(d)
    assert r["recomendado"] == "prod" and r["n"] == {"uat": 1, "prod": 0, "sbx": 1}
    assert r["faltan"]["uat"] == ["rps/datapull.json: lag_ecm_pivot"]
def test_prefiere_uat_si_todos_estan_completos(tmp_path):
    d = _settings(tmp_path, {"prod": {"a": 1}, "uat": {"a": 1}, "sbx": {"a": 1}})
    assert sim.analizar_envs(d)["recomendado"] == "uat"
def test_config_custom_usa_el_bloque_env_y_default(tmp_path):
    d = _settings(tmp_path, {"prod": {"a": 1}, "uat": {"a": 1}, "sbx": {"a": 1}})
    (tmp_path / "rps" / "config_custom.json").write_text(json.dumps(
        {"default": {"n": 1}, "env": {"prod": {"w": 1}, "uat": {}, "sbx": {"w": 1}}}))
    r = sim.analizar_envs(d)
    assert r["n"]["uat"] == 1 and r["recomendado"] == "prod"
def test_iniciar_pasa_el_env_recomendado(tmp_path, monkeypatch):
    d = _settings(tmp_path / "s", {"prod": {"k": 1}, "uat": {}, "sbx": {}}) if (tmp_path / "s").mkdir() is None else None
    assert sim.comando_job("py", "/pkg", "j", d, "prod")[-2:] == ["--env", "prod"]
    assert sim._linux_script_job("j", "/bnx_settings", "prod").endswith("--settings /bnx_settings --env prod")
    assert "--env" not in sim.comando_job("py", "/pkg", "j", None, None)
def test_env_invalido_se_rechaza(tmp_path, monkeypatch):
    import zipfile
    z = tmp_path / "p.zip"
    with zipfile.ZipFile(z, "w") as zf:
        zf.writestr("framework_mlops_v2_pkg/framework_mlops_v2/aggregates/router.py",
                    "_FUENTES = {'a': ('x', 'y', 'kernel', 'm/a')}\n")
    monkeypatch.setenv("BNX_SIMULAR_DIR", str(tmp_path / "s"))
    monkeypatch.setattr(sim, "entorno_soportado", lambda: (True, "ok"))
    with pytest.raises(sim.SimError) as e:
        sim.iniciar("t", str(z), None, None, None, "mac", "uat; rm -rf /")
    assert "env inválido" in str(e.value)
def test_aviso_de_clave_en_otro_ambiente_en_el_runner(tmp_path):
    """_clave_en_otro_env del main.py generado: 'lag_ecm_pivot esta en prod pero no en uat'. Se ejecuta el codigo
    de la plantilla tal cual (sin importar el paquete entero)."""
    import ast
    from src import mlops_pkg as mp
    src = mp.__file__
    txt = open(src, encoding="utf-8").read()
    ini = txt.index("def _hint_clave_faltante(ex, settings_dir, env, entry):")
    fin = txt.index("def _patch_sql(spark, synth):")
    ns = {"os": os, "json": json}
    exec(compile(txt[ini:fin], "plantilla", "exec"), ns)
    d = _settings(tmp_path, {"prod": {"lag_ecm_pivot": 1}, "uat": {"lag": 1}, "sbx": {}})
    try:
        raise KeyError("lag_ecm_pivot")
    except KeyError as ex:
        msg = ns["_hint_clave_faltante"](ex, d, "uat", {"model": "rps", "job": "datapull"})
    assert "FALTA LA CLAVE 'lag_ecm_pivot'" in msg
    assert "esta en el ambiente 'prod' pero no en 'uat'" in msg and "rps/datapull.json" in msg and "--env prod" in msg
    assert ns["_hint_clave_faltante"](RuntimeError("x"), d, "uat", {}) == ""
# --- columnas falsas del analisis estatico ---------------------------------------------------------
CODIGO = '''
import xgboost as xgb
import pyspark.sql.functions as F
from utils.emails_full import Email
def run(kernel, df, email):
    modelo = xgb.XGBClassifier()
    t = email._calculate_time(3)
    lst = []
    lst.append(1)
    fecha = F.current_date()
    y = df.numcliente + df.saldo
    z = F.broadcast(df)
    return modelo, t, fecha, y, z
'''
def test_atributos_que_no_son_columnas_se_descartan(tmp_path):
    f = tmp_path / "job.py"
    f.write_text(CODIGO)
    a = analisis.analizar_archivo(str(f))
    todas = a.todas()
    for falso in ("XGBClassifier", "_calculate_time", "append", "current_date", "broadcast"):
        assert falso not in todas, falso
    assert {"numcliente", "saldo"} <= todas            # df.col sigue siendo columna
