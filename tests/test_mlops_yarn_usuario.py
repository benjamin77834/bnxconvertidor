"""Corrida real en YARN de un usuario del banco: --source invalido caia a DEMO, temporales del DEMO en una
ruta HDFS sin permiso. Sin cluster: main.py generado con Spark local / objetos falsos."""
import os
import subprocess
import sys

import pytest

from tests import test_mlops_kernel as tk

pytest.importorskip("pyspark")


@pytest.fixture(scope="module")
def pkg(tmp_path_factory):
    tmp = tmp_path_factory.mktemp("yarn_usuario")
    _, _, _, root = tk._build(tmp, tk._fuentes())
    st = tmp / "settings"
    st.mkdir()
    (st / "spark.json").write_text("{}")
    return root, str(st)


def _main(root, args, tmp_path):
    env = {k: v for k, v in os.environ.items()
           if k not in ("JAVA_TOOL_OPTIONS", "SPARK_CONF_DIR", "CONF_PATH", "BIN_PATH", "BNX_ORDEN")}
    env["BNX_TEST_OUT"] = str(tmp_path / "o.txt")
    return subprocess.run([sys.executable, "main.py"] + args, cwd=root, env=env, capture_output=True, text=True, timeout=240)


def test_source_que_no_es_job_con_settings_falla_antes_de_crear_spark(pkg, tmp_path):
    root, st = pkg
    r = _main(root, ["--settings", st, "--env", "prod", "--source", "main"], tmp_path)
    out = r.stdout + r.stderr
    assert r.returncode != 0
    assert "'main' no es una tabla del config ni un job del REGISTRY" in out
    assert "m1_a, m1_pivot, m2_b, m2_c" in out and "NOMBRE DEL JOB" in out
    for demo in ("MODO DEMO", "ENTRADA sintetica", "[spark] master", "[spark] modo CLUSTER"):
        assert demo not in out                         # no se levanto ninguna SparkSession


def test_settings_env_source_con_job_del_banco_corre_real_no_demo(pkg, tmp_path):
    root, st = pkg
    r = _main(root, ["--settings", st, "--env", "prod", "--source", "m1_a"], tmp_path)
    out = r.stdout + r.stderr
    assert r.returncode == 0, out
    assert "MODO REAL" in out and "FIN OK m1_a" in out and "MODO DEMO" not in out and "ENTRADA sintetica" not in out


def _main_mod(root):
    import importlib.util
    sys.path.insert(0, root)
    try:
        spec = importlib.util.spec_from_file_location("bnx_main_yarn_t", os.path.join(root, "main.py"))
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        return mod
    finally:
        sys.path.remove(root)


class _Home:
    def toString(self):
        return "hdfs://ns1/user/usuario1"


class _FS:
    def getHomeDirectory(self):
        return _Home()


class _Args:
    base_path = None


def _spark(master):
    class _SC:
        pass
    _SC.master = master

    class _S:
        sparkContext = _SC()
    return _S()


def test_temporales_del_demo_en_yarn_van_al_home_hdfs_del_usuario(pkg, monkeypatch):
    root, _ = pkg
    m = _main_mod(root)
    monkeypatch.setattr(m, "_default_fs", lambda s: "hdfs://ns1")
    monkeypatch.setattr(m, "_fs_path", lambda s, p: (_FS(), p))
    for k in ("BNX_HDFS_TMP", "BNX_BASE_PATH"):
        monkeypatch.delenv(k, raising=False)
    ruta, remota, origen = m._tmp_spark_base(_spark("yarn"), _Args(), "/data/1/pkg/.bnx_tmp")
    assert remota and ruta == "hdfs://ns1/user/usuario1/.bnx_tmp" and "HOME" in origen
    assert "/data/1" not in ruta                        # nunca la carpeta del paquete del edge
    monkeypatch.setenv("BNX_BASE_PATH", "/user/otro/base")
    assert m._tmp_spark_base(_spark("yarn"), _Args(), "/x")[0] == "/user/otro/base/.bnx_tmp"
    a = _Args()
    a.base_path = "/user/cli/base/"
    assert m._tmp_spark_base(_spark("yarn"), a, "/x")[0] == "/user/cli/base/.bnx_tmp"
    monkeypatch.setenv("BNX_HDFS_TMP", "/user/usuario1/mi_tmp")
    ruta, remota, origen = m._tmp_spark_base(_spark("yarn"), a, "/x")
    assert ruta == "/user/usuario1/mi_tmp" and origen == "BNX_HDFS_TMP"
    # local: la carpeta de trabajo (el llamador antepone file:// si el defaultFS es HDFS)
    ruta, remota, _ = m._tmp_spark_base(_spark("local[2]"), _Args(), "/tmp/w")
    assert not remota and ruta == "/tmp/w"
    monkeypatch.setattr(m, "_default_fs", lambda s: "file:///")
    assert m._tmp_spark_base(_spark("yarn"), _Args(), "/tmp/w") == ("/tmp/w", False, "disco local")


def test_mensaje_sin_permiso_dice_como_cambiar_la_ruta():
    from src import mlops_pkg as mp
    assert "BNX_HDFS_TMP=/user/<usuario>/bnx_tmp" in mp._MAIN_PY and "SIN PERMISO de escritura" in mp._MAIN_PY
