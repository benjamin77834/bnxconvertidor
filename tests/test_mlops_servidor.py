"""Framework MLOps v2 en el servidor del banco: DEMO vs REAL, busqueda de settings, run.sh de cluster
(verificacion previa de imports, python del driver, conf dir del cluster sin reemplazar), alias
job_3 y check_env --driver. Sin red; Spark FALSO (script que imprime argv/env)."""
import ast
import json
import os
import shutil
import stat
import subprocess
import sys

import pytest

from src import bnx_sparkconf as bs
from src import mlops_pkg as mp

import test_mlops_kernel as tk   # noqa: E402  (fuentes falsas del banco; tests/ va en sys.path)

pytest.importorskip("pandas")
pytest.importorskip("pyspark")


# ---------------------------------------------------------------- funciones puras
def test_modo_ejecucion_demo_solo_explicito_o_sin_nada():
    assert bs.modo_ejecucion() == (True, "sin --config ni --settings (ni --env/--cohort/--fid)")
    assert bs.modo_ejecucion(demo_flag=True, config="c.json")[0] is True
    for kw in ({"config": "pivot.json"}, {"settings": "s"}, {"env": "uat"}, {"cohort": "201406"},
               {"fid": "x"}, {"conf_path": "/c"}):
        demo, motivo = bs.modo_ejecucion(**kw)
        assert demo is False and "se indico" in motivo
    assert not bs.es_demo(None, None, False, env="uat") and bs.es_demo(None, None, True, env="uat")


def test_buscar_settings_orden_y_candidatos(tmp_path):
    base = tmp_path / "pkg"
    (base / "bank_src" / "settings").mkdir(parents=True)
    (base / "bank_src" / "settings" / "spark.json").write_text("{}")
    cfg_dir = tmp_path / "bin" / "settings" / "RPS"
    cfg_dir.mkdir(parents=True)
    (tmp_path / "bin" / "settings" / "spark.json").write_text("{}")
    cfg = cfg_dir / "pivot.json"
    cfg.write_text("{}")
    cwd = str(tmp_path / "vacio")
    os.makedirs(cwd)
    # explicito manda, CONF_PATH despues
    assert bs.buscar_settings("/x", str(cfg), {}, [str(base)], cwd)[:2] == ("/x", "--settings")
    assert bs.buscar_settings(None, str(cfg), {"CONF_PATH": "/c"}, [str(base)], cwd)[:2] == ("/c", "$CONF_PATH")
    # bank_src/settings del paquete antes que la carpeta del --config
    d, motivo, _ = bs.buscar_settings(None, str(cfg), {}, [str(base)], cwd)
    assert d == str(base / "bank_src" / "settings") and "bank_src" in motivo
    # sin bank_src: padre del --config con spark.json
    d, motivo, _ = bs.buscar_settings(None, str(cfg), {}, [str(tmp_path / "otro")], cwd)
    assert d == str(tmp_path / "bin" / "settings") and "--config" in motivo
    # BIN_PATH/settings
    d, motivo, _ = bs.buscar_settings(None, None, {"BIN_PATH": str(tmp_path / "bin")}, [], cwd)
    assert d == str(tmp_path / "bin" / "settings") and "BIN_PATH" in motivo
    # ./settings y bin/settings del paquete
    (tmp_path / "vacio" / "settings").mkdir()
    (tmp_path / "vacio" / "settings" / "spark.json").write_text("{}")
    assert bs.buscar_settings(None, None, {}, [], cwd)[1] == "./settings"
    # nada -> None y lista de lugares probados
    d, motivo, probados = bs.buscar_settings(None, str(tmp_path / "x.json"), {}, [], str(tmp_path / "otro_cwd"))
    assert d is None and probados


def test_cli_sparkconf_dice_de_donde_salen_los_recursos(tmp_path):
    cfg = tmp_path / "pivot.json"
    cfg.write_text(json.dumps({"tables_info": {}}))
    out = tmp_path / "p.properties"
    r = subprocess.run([sys.executable, bs.__file__, "--modo", "cluster", "--out", str(out), "--",
                        "--config", str(cfg)], capture_output=True, text=True, cwd=str(tmp_path))
    assert r.returncode == 0, r.stderr
    assert "fuentes:" in r.stdout and "defecto=3" in r.stdout
    assert "AVISO: sin spark.json del banco" in r.stdout and "--settings" in r.stdout
    # con spark.conf en el cfg se aplica y se dice
    cfg.write_text(json.dumps({"spark": {"conf": {"spark.executor.memory": "9g"}}}))
    r = subprocess.run([sys.executable, bs.__file__, "--modo", "cluster", "--out", str(out), "--",
                        "--config", str(cfg)], capture_output=True, text=True, cwd=str(tmp_path))
    assert "cfg=1" in r.stdout and "spark.executor.memory=9g" in out.read_text()
    # con settings: cola uat del banco
    st = tmp_path / "bin" / "settings"
    st.mkdir(parents=True)
    (st / "spark.json").write_text(json.dumps({"default": {"spark.executor.cores": "5"},
                                               "spark_queue_uat": "root.q_uat"}))
    r = subprocess.run([sys.executable, bs.__file__, "--modo", "cluster", "--out", str(out), "--",
                        "--settings", str(st), "--env", "uat"], capture_output=True, text=True, cwd=str(tmp_path))
    assert "spark.json=2" in r.stdout and "spark.yarn.queue=root.q_uat" in out.read_text()


# ---------------------------------------------------------------- main.py generado
@pytest.fixture(scope="module")
def pkg(tmp_path_factory):
    tmp = tmp_path_factory.mktemp("srv_pkg")
    _, _, _, root = tk._build(tmp, tk._fuentes())
    return root


def _settings(base):
    st = base / "bin" / "settings"
    (st / "RPS").mkdir(parents=True, exist_ok=True)
    (st / "spark.json").write_text(json.dumps({"default": {}, "spark_queue_uat": "root.q"}))
    (st / "RPS" / "pivot.json").write_text(json.dumps({"tables_info": {}}))
    return st


def test_config_sin_settings_es_error_claro_no_demo(pkg, tmp_path):
    cfg = tmp_path / "pivot.json"
    cfg.write_text(json.dumps({"tables_info": {}}))
    r, lineas = tk._run(pkg, ["--config", str(cfg), "--env", "uat", "--cohort", "201406",
                              "--source", "job_2"], tmp_path)
    assert r.returncode == 2, r.stdout + r.stderr
    assert "necesita --settings <bin/settings>" in r.stderr and "No se ejecuto nada" in r.stderr
    assert "MODO DEMO" not in r.stdout and not lineas       # el job NO corrio
    assert "job_2' -> 'm1_pivot'" in r.stdout               # alias mostrado


def test_env_o_cohort_solos_tampoco_son_demo(pkg, tmp_path):
    r, lineas = tk._run(pkg, ["--env", "uat", "--source", "m1_a"], tmp_path)
    assert r.returncode == 2 and not lineas and "necesita --settings" in r.stderr


def test_demo_explicito_con_config_sigue_siendo_demo(pkg, tmp_path):
    cfg = tmp_path / "pivot.json"
    cfg.write_text("{}")
    r, lineas = tk._run(pkg, ["--demo", "--config", str(cfg), "--source", "job_2"], tmp_path)
    assert r.returncode == 0, r.stdout + r.stderr
    assert "MODO DEMO" in r.stdout and "--demo explicito" in r.stdout and "MODO REAL" not in r.stdout
    assert "'job_2' -> 'm1_pivot' (nombre por ruta m1/pivot" in r.stdout and lineas[0].startswith("m1_pivot")


def test_sin_argumentos_es_demo_con_motivo(pkg, tmp_path):
    r, _ = tk._run(pkg, ["--source", "m1_a"], tmp_path)
    assert "MODO DEMO" in r.stdout and "sin --config ni --settings" in r.stdout


def test_real_encuentra_settings_junto_al_config(pkg, tmp_path):
    st = _settings(tmp_path)
    r, lineas = tk._run(pkg, ["--config", str(st / "RPS" / "pivot.json"), "--env", "uat",
                              "--source", "job_2"], tmp_path)
    assert r.returncode == 0, r.stdout + r.stderr
    assert "MODO REAL" in r.stdout and "se indico --config, --env" in r.stdout
    assert "settings: %s" % st in r.stdout and "carpeta padre del --config" in r.stdout
    assert "[python] driver=" in r.stdout and lineas[0].startswith("m1_pivot")


def test_real_con_settings_explicito_inexistente_falla(pkg, tmp_path):
    r, lineas = tk._run(pkg, ["--settings", str(tmp_path / "nada"), "--env", "uat", "--source", "m1_a"], tmp_path)
    assert r.returncode != 0 and not lineas and "no existe" in (r.stdout + r.stderr)


def test_main_y_check_env_son_python38():
    ast.parse(mp._MAIN_PY, feature_version=(3, 8))
    ast.parse(mp._CHECK_ENV, feature_version=(3, 8))
    ast.parse(open(bs.__file__, encoding="utf-8").read(), feature_version=(3, 8))


# ---------------------------------------------------------------- run.sh de cluster
def _venv_falso(pkg, shadow=None):
    vb = os.path.join(pkg, ".venv", "bin")
    shutil.rmtree(os.path.join(pkg, ".venv"), ignore_errors=True)
    os.makedirs(vb)
    py = os.path.join(vb, "python")      # wrapper (un symlink perderia el contexto del venv de pytest)
    with open(py, "w") as fh:
        fh.write('#!/bin/bash\nexec "%s" "$@"\n' % sys.executable)
    os.chmod(py, 0o755)
    with open(os.path.join(vb, "activate"), "w") as fh:
        fh.write('export PATH="$PWD/.venv/bin:$PATH"\nexport SPARK_CONF_DIR="$PWD/.venv/spark_conf"\n')


FAKE_SUBMIT = '''#!/bin/bash
for a in "$@"; do echo "ARG:$a"; done
echo "ENV:SPARK_CONF_DIR=${SPARK_CONF_DIR-<sin definir>}"
echo "ENV:PYSPARK_PYTHON=${PYSPARK_PYTHON-<sin definir>}"
echo "ENV:PYSPARK_DRIVER_PYTHON=${PYSPARK_DRIVER_PYTHON-<sin definir>}"
'''


def _run_cluster(pkg, tmp_path, extra_env=None, args=("--demo", "--source", "m1_a"), shadow=None):
    _venv_falso(pkg)
    fake = tmp_path / "bin" / "spark3-submit"
    fake.parent.mkdir(exist_ok=True)
    fake.write_text(FAKE_SUBMIT)
    fake.chmod(fake.stat().st_mode | stat.S_IEXEC)
    env = {k: v for k, v in os.environ.items()
           if not k.startswith(("BNX_", "SPARK_", "CONF_PATH", "PYSPARK_", "BIN_PATH"))}
    env.update(BNX_SPARK="cluster", BNX_SPARK_SUBMIT=str(fake), HADOOP_CONF_DIR="/x",
               BNX_CLUSTER_CONF_CANDIDATOS=str(tmp_path / "no_hay"))
    if shadow:
        env["PYTHONPATH"] = shadow
    env.update(extra_env or {})
    r = subprocess.run(["bash", "run.sh"] + list(args), cwd=pkg, env=env, capture_output=True, text=True, timeout=120)
    sal = r.stdout.splitlines()
    return r, [l[4:] for l in sal if l.startswith("ARG:")], dict(l[4:].split("=", 1) for l in sal if l.startswith("ENV:"))


def test_run_sh_sintaxis_y_contiene_las_protecciones():
    for nombre in ("_RUN_SH", "_SETUP_SH"):
        r = subprocess.run(["bash", "-n"], input=getattr(mp, nombre), capture_output=True, text=True)
        assert r.returncode == 0, r.stderr
    assert "spark.pyspark.driver.python=$PWD/.venv/bin/python" in mp._RUN_SH
    assert "preflight.py" in mp._RUN_SH and "vendor/OFFLINE_FALTANTES.txt" in mp._RUN_SH
    assert "check_env.py --driver" in mp._SETUP_SH and "trap " in mp._SETUP_SH and ".bnx_setup_ok" in mp._SETUP_SH
    # ya no arma un conf dir con SOLO hive-site.xml en modo cluster
    assert 'if [ -z "$CLUSTER_SUBMIT" ] && [ -z "${SPARK_CONF_DIR:-}" ]; then' in mp._RUN_SH


def test_cluster_pasa_driver_python_y_no_fuerza_python_de_executors(pkg, tmp_path):
    r, args, env = _run_cluster(pkg, tmp_path)
    assert r.returncode == 0, r.stdout + r.stderr
    drv = os.path.join(pkg, ".venv", "bin", "python")
    assert "spark.pyspark.driver.python=" + drv in args
    assert not any(a.startswith("spark.pyspark.python=") for a in args)       # executors: el del cluster
    assert env["PYSPARK_DRIVER_PYTHON"] == drv and env["PYSPARK_PYTHON"] == "<sin definir>"
    assert "verificacion previa de imports del driver: OK" in r.stdout
    assert "driver: python del venv; executors: python del cluster" in r.stdout


def test_cluster_enviar_venv_si_fija_python_de_executors(pkg, tmp_path):
    (tmp_path / "x").mkdir()
    open(os.path.join(pkg, ".bnx_venv.tar.gz"), "w").close()
    try:
        r, args, _ = _run_cluster(pkg, tmp_path, {"BNX_ENVIAR_VENV": "1"})
    finally:
        os.remove(os.path.join(pkg, ".bnx_venv.tar.gz"))
    assert "spark.pyspark.python=./bnxenv/.venv/bin/python" in args
    assert sum(a.startswith("spark.pyspark.driver.python=") for a in args) == 1


def _conf_cluster(base, hive=False):
    d = base / "etc" / "spark3" / "conf"
    (d / "yarn-conf").mkdir(parents=True)
    (d / "spark-defaults.conf").write_text("spark.pyspark.python=/usr/bin/python3\nspark.yarn.jars=local:/x\n")
    (d / "spark-env.sh").write_text("export PYSPARK_PYTHON=/usr/bin/python3\n")
    (d / "yarn-conf" / "core-site.xml").write_text("<configuration/>")
    if hive:
        (d / "hive-site.xml").write_text("<configuration/>")
    return d


def test_cluster_usa_la_config_del_cluster_tal_cual(pkg, tmp_path):
    d = _conf_cluster(tmp_path, hive=True)
    r, _, env = _run_cluster(pkg, tmp_path, {"BNX_CLUSTER_CONF_CANDIDATOS": str(d)})
    assert r.returncode == 0, r.stdout + r.stderr
    assert env["SPARK_CONF_DIR"] == str(d)
    assert "tal cual" in r.stdout and "por que:" in r.stdout
    assert "el cluster fija: spark.pyspark.python=/usr/bin/python3" in r.stdout
    assert not os.path.exists(os.path.join(pkg, ".bnx_tmp", "spark_conf"))


def test_cluster_sin_hive_site_copia_completa_no_solo_hive(pkg, tmp_path):
    d = _conf_cluster(tmp_path, hive=False)
    hs = tmp_path / "hive-site.xml"
    hs.write_text("<configuration><!--hive--></configuration>")
    shutil.rmtree(os.path.join(pkg, ".bnx_tmp", "spark_conf"), ignore_errors=True)
    r, _, env = _run_cluster(pkg, tmp_path, {"BNX_CLUSTER_CONF_CANDIDATOS": str(d), "BNX_HIVE_SITE": str(hs)})
    assert r.returncode == 0, r.stdout + r.stderr
    copia = os.path.join(pkg, ".bnx_tmp", "spark_conf")
    assert env["SPARK_CONF_DIR"] == copia and "COPIA COMPLETA de %s" % d in r.stdout
    for f in ("spark-defaults.conf", "spark-env.sh", "hive-site.xml", os.path.join("yarn-conf", "core-site.xml")):
        assert os.path.isfile(os.path.join(copia, f)), f
    assert "spark.yarn.jars" in open(os.path.join(copia, "spark-defaults.conf")).read()


def test_cluster_sin_config_del_cluster_no_inventa_conf_dir(pkg, tmp_path):
    r, _, env = _run_cluster(pkg, tmp_path)
    assert r.returncode == 0, r.stdout + r.stderr
    assert env["SPARK_CONF_DIR"] == "<sin definir>"          # ni .venv/spark_conf ni un dir solo con hive
    assert "no hay config de Spark del cluster" in r.stdout


def test_cluster_respeta_spark_conf_dir_del_usuario(pkg, tmp_path):
    d = _conf_cluster(tmp_path, hive=True)
    r, _, env = _run_cluster(pkg, tmp_path, {"SPARK_CONF_DIR": str(d)})
    assert env["SPARK_CONF_DIR"] == str(d)


def test_preflight_falla_claro_si_falta_pandas_y_no_lanza_spark(pkg, tmp_path):
    sombra = tmp_path / "sombra"
    sombra.mkdir()
    (sombra / "pandas.py").write_text("raise ModuleNotFoundError(\"No module named 'pandas'\")\n")
    r, args, env = _run_cluster(pkg, tmp_path, shadow=str(sombra))
    assert r.returncode == 1 and not args                      # spark-submit NO se llamo
    assert "FALTA: pandas" in r.stderr and "bash setup.sh" in r.stderr
    assert "OFFLINE_FALTANTES.txt" in r.stderr and "No se lanzo Spark" in r.stderr
    # BNX_SKIP_PREFLIGHT=1 la salta
    r, args, _ = _run_cluster(pkg, tmp_path, {"BNX_SKIP_PREFLIGHT": "1"}, shadow=str(sombra))
    assert r.returncode == 0 and args


def test_check_env_driver_ok_y_falla(pkg, tmp_path):
    env = {k: v for k, v in os.environ.items() if not k.startswith(("BNX_", "PYTHONPATH"))}
    r = subprocess.run([sys.executable, "check_env.py", "--driver"], cwd=pkg, env=env, capture_output=True, text=True)
    assert r.returncode == 0, r.stdout + r.stderr
    assert "Python del venv: %s" % sys.executable in r.stdout and "OK  toolbox" in r.stdout
    sombra = tmp_path / "s2"
    sombra.mkdir()
    (sombra / "pandas.py").write_text("raise ModuleNotFoundError(\"No module named 'pandas'\")\n")
    env["PYTHONPATH"] = str(sombra)
    r = subprocess.run([sys.executable, "check_env.py", "--driver"], cwd=pkg, env=env, capture_output=True, text=True)
    assert r.returncode == 1 and "FALTA: pandas" in r.stdout and "FALLA" in r.stdout
