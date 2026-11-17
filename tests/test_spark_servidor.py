# -*- coding: utf-8 -*-
"""PySpark del SERVIDOR (modo B): logica bash de setup.sh/run.sh probada con directorios falsos
(sin red, sin Spark real). Prueba real opcional: BNX_TEST_SPARK_REAL=1."""
import os
import pty
import select
import shutil
import subprocess
import sys
import zipfile

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
os.environ.setdefault("BNX_NO_DOWNLOAD", "1")
from src import mlops_pkg as mp  # noqa: E402
from src.spark_server_sh import SPARK_CFG_SH  # noqa: E402

pytestmark = pytest.mark.skipif(shutil.which("bash") is None, reason="requiere bash")


def _spark_home(base, ver="3.5.6", py4j=True, submit=True, pyspark=True):
    h = base / ("spark-" + ver)
    (h / "bin").mkdir(parents=True)
    if submit:
        (h / "bin" / "spark-submit").write_text("#!/bin/sh\nexit 0\n")
    if pyspark:
        (h / "python" / "pyspark").mkdir(parents=True)
        (h / "python" / "pyspark" / "__init__.py").write_text("__version__ = %r\n" % ver)
    (h / "python" / "lib").mkdir(parents=True, exist_ok=True)
    if py4j:
        with zipfile.ZipFile(h / "python" / "lib" / "py4j-0.10.9.7-src.zip", "w") as z:
            z.writestr("py4j/__init__.py", "")
    (h / "RELEASE").write_text("Spark %s built for Hadoop 3.3.4\n" % ver)
    return h


@pytest.fixture
def entorno(tmp_path):
    """venv vacio + java falso + script con las funciones cargadas."""
    subprocess.run([sys.executable, "-m", "venv", "--without-pip", str(tmp_path / "pkg" / ".venv")], check=True)
    jb = tmp_path / "jbin"
    jb.mkdir()
    (jb / "java").write_text("#!/bin/sh\necho 'openjdk version \"17\"' >&2\n")
    (jb / "java").chmod(0o755)
    (tmp_path / "funcs.sh").write_text(SPARK_CFG_SH)
    env = dict(os.environ, PATH="%s:%s:%s" % (tmp_path / "pkg" / ".venv" / "bin", jb, os.environ["PATH"]),
               # python "del sistema" SIN pyspark (el del .venv lo trae y se autodetectaria)
               BNX_SYSTEM_PYTHON=shutil.which("false") or "/usr/bin/false",
               PYMINOR="11", TMPDIR=str(tmp_path))
    for k in ("SPARK_HOME", "BNX_SPARK_HOME", "BNX_SPARK_RECONFIG", "JAVA_HOME"):
        env.pop(k, None)
    return tmp_path, env


def _bash(entorno, cuerpo, extra_env=None, **kw):
    tmp, env = entorno
    env = dict(env, **(extra_env or {}))
    return subprocess.run(["bash", "-c", "set -e; . %s/funcs.sh; %s" % (tmp, cuerpo)], cwd=str(tmp / "pkg"),
                          capture_output=True, text=True, env=env, timeout=60, **kw)


def test_bash_sintaxis_setup_y_run():
    for nombre in ("_SETUP_SH", "_RUN_SH"):
        r = subprocess.run(["bash", "-n"], input=getattr(mp, nombre), capture_output=True, text=True)
        assert r.returncode == 0, r.stderr
    assert "bnx_spark_configurar" in mp._SETUP_SH and "--reconfigurar-spark" in mp._SETUP_SH
    assert ".bnx_spark.env" in mp._RUN_SH and "BNX_SPARK_PYPATH" in mp._RUN_SH


def test_ruta_buena_se_valida_y_lee_version(entorno):
    h = _spark_home(entorno[0])
    r = _bash(entorno, 'bnx_spark_normalizar "%s"; echo "VER=$BS_VER HOME=$BS_HOME"' % h)
    assert r.returncode == 0, r.stderr
    assert "VER=3.5.6" in r.stdout and str(h.resolve()) in r.stdout


@pytest.mark.parametrize("kw,texto", [({"submit": False}, "spark-submit"), ({"py4j": False}, "py4j"),
                                     ({"pyspark": False}, "python/pyspark")])
def test_rutas_malas_se_rechazan(entorno, kw, texto):
    h = _spark_home(entorno[0], **kw)
    r = _bash(entorno, 'bnx_spark_normalizar "%s" || { echo "ERR=$BS_ERR"; exit 7; }' % h)
    assert r.returncode == 7 and texto in r.stdout


def test_ruta_inexistente_y_sin_java(entorno):
    tmp, env = entorno
    r = _bash(entorno, 'bnx_spark_normalizar "%s/nada" || { echo "ERR=$BS_ERR"; exit 7; }' % tmp)
    assert r.returncode == 7 and "no existe" in r.stdout
    h = _spark_home(tmp)
    r = _bash(entorno, 'bnx_spark_normalizar "%s" || { echo "ERR=$BS_ERR"; exit 7; }' % h,
              {"PATH": "/usr/bin:/bin", "JAVA_HOME": ""})
    assert "java" in r.stdout.lower() or r.returncode == 0   # si el sistema trae java en /usr/bin, pasa


def test_compatibilidad_version_python(entorno):
    tmp, _ = entorno
    hs = {v: _spark_home(tmp, v) for v in ("3.3.0", "3.5.6", "4.0.0", "4.1.2")}

    def aviso(ver, pm):
        r = _bash(entorno, 'bnx_spark_normalizar "%s"; echo "AV=$BS_AVISO"' % hs[ver], {"PYMINOR": str(pm)})
        return r.stdout.strip()
    assert "ajustes" in aviso("3.5.6", 12)
    assert aviso("3.5.6", 11) == "AV="
    assert "INCOMPATIBLE" in aviso("3.5.6", 14) and "3.8-3.11" in aviso("3.5.6", 14)
    assert "INCOMPATIBLE" in aviso("3.3.0", 11)
    assert "INCOMPATIBLE" in aviso("4.0.0", 8) and "INCOMPATIBLE" in aviso("4.0.0", 14)
    assert aviso("4.0.0", 13) == "AV="
    assert aviso("4.1.2", 14) == "AV=" and "INCOMPATIBLE" in aviso("4.1.2", 9)


def test_sugiere_otro_python_del_servidor(entorno):
    tmp, env = entorno
    (tmp / "jbin" / "python3.11").write_text("#!/bin/sh\n")
    (tmp / "jbin" / "python3.11").chmod(0o755)
    h = _spark_home(tmp, "3.5.6")
    r = _bash(entorno, 'bnx_spark_normalizar "%s"; echo "AV=$BS_AVISO"' % h, {"PYMINOR": "14"})
    assert "INCOMPATIBLE" in r.stdout and "python3.11" in r.stdout


def test_sin_tty_con_env_guarda_config_y_enlaza_venv(entorno):
    tmp, _ = entorno
    h = _spark_home(tmp)
    r = _bash(entorno, "bnx_spark_configurar", {"BNX_SPARK_HOME": str(h)}, stdin=subprocess.DEVNULL)
    assert r.returncode == 0, r.stdout + r.stderr
    cfg = (tmp / "pkg" / ".bnx_spark.env").read_text()
    assert "SPARK_HOME='%s'" % h.resolve() in cfg and "BNX_SPARK_VERSION='3.5.6'" in cfg and "PYSPARK_PYTHON=" in cfg
    sp = list((tmp / "pkg" / ".venv" / "lib").glob("python*/site-packages"))[0]
    assert (sp / "pyspark").is_symlink() and (sp / "bnx_spark.pth").read_text().strip().endswith(".zip")
    # segunda corrida: usa la config guardada sin preguntar ni necesitar BNX_SPARK_HOME
    r = _bash(entorno, "bnx_spark_configurar", stdin=subprocess.DEVNULL)
    assert r.returncode == 0 and "ya configurado" in r.stdout


def test_sin_tty_sin_env_falla_con_mensaje_claro(entorno):
    r = _bash(entorno, "bnx_spark_configurar", stdin=subprocess.DEVNULL)
    assert r.returncode != 0 and "BNX_SPARK_HOME" in r.stderr
    assert not (entorno[0] / "pkg" / ".bnx_spark.env").exists()


def test_sin_tty_env_malo_falla(entorno):
    r = _bash(entorno, "bnx_spark_configurar", {"BNX_SPARK_HOME": str(entorno[0] / "no_existe")},
              stdin=subprocess.DEVNULL)
    assert r.returncode != 0 and "no sirve" in r.stderr


def test_reconfigurar_ignora_la_config_guardada(entorno):
    tmp, _ = entorno
    h1, h2 = _spark_home(tmp, "3.5.6"), _spark_home(tmp, "3.5.5")
    _bash(entorno, "bnx_spark_configurar", {"BNX_SPARK_HOME": str(h1)}, stdin=subprocess.DEVNULL)
    r = _bash(entorno, "bnx_spark_configurar", {"BNX_SPARK_HOME": str(h2), "BNX_SPARK_RECONFIG": "1"},
              stdin=subprocess.DEVNULL)
    assert r.returncode == 0
    assert "spark-3.5.5" in (tmp / "pkg" / ".bnx_spark.env").read_text()


def _con_tty(entorno, entradas, extra_env=None):
    tmp, env = entorno
    env = dict(env, **(extra_env or {}))
    m, s = pty.openpty()
    p = subprocess.Popen(["bash", "-c", "set -e; . %s/funcs.sh; bnx_spark_configurar" % tmp], cwd=str(tmp / "pkg"),
                         stdin=s, stdout=s, stderr=s, env=env, close_fds=True)
    os.close(s)
    salida = b""
    pendientes = list(entradas)
    enviados = 0
    import time
    fin = time.time() + 60
    ultimo = time.time()
    while time.time() < fin:
        if select.select([m], [], [], 0.2)[0]:
            try:
                nuevo = os.read(m, 65536)
            except OSError:
                break
            if nuevo:
                salida += nuevo
                ultimo = time.time()
        # una respuesta por cada prompt "Ruta de SPARK_HOME" mostrado
        if pendientes and salida.count(b"Ruta de SPARK_HOME") > enviados:
            os.write(m, (pendientes.pop(0) + "\n").encode())
            enviados += 1
        if p.poll() is not None and not select.select([m], [], [], 0.2)[0]:
            break
        if not pendientes and time.time() - ultimo > 3:
            break
    if p.poll() is None:
        p.kill()
    p.wait(timeout=10)
    os.close(m)
    return p.returncode, salida.decode("utf-8", "replace")


def test_con_tty_un_candidato_valido_se_autodetecta_sin_preguntar(entorno):
    tmp, _ = entorno
    h = _spark_home(tmp)
    rc, out = _con_tty(entorno, [], {"SPARK_HOME": str(h)})
    assert rc == 0, out
    assert "AUTODETECTADO" in out and "Ruta de SPARK_HOME" not in out
    assert "spark-3.5.6" in (tmp / "pkg" / ".bnx_spark.env").read_text()


def test_sin_tty_un_candidato_valido_se_autodetecta(entorno):
    tmp, _ = entorno
    h = _spark_home(tmp)
    r = _bash(entorno, "bnx_spark_configurar", {"SPARK_HOME": str(h)}, stdin=subprocess.DEVNULL)
    assert r.returncode == 0 and "AUTODETECTADO" in r.stdout, r.stdout + r.stderr


def test_con_tty_varios_candidatos_pregunta_y_enter_toma_el_1(entorno):
    tmp, _ = entorno
    h1, h2 = _spark_home(tmp, "3.5.6"), _spark_home(tmp, "3.5.5")
    bindir = tmp / "binspark"
    bindir.mkdir()
    (h2 / "bin" / "spark-submit").chmod(0o755)
    os.symlink(str(h2 / "bin" / "spark-submit"), str(bindir / "spark-submit"))
    env = {"SPARK_HOME": str(h1), "PATH": "%s:%s" % (bindir, entorno[1]["PATH"])}
    rc, out = _con_tty(entorno, [""], env)
    assert rc == 0, out
    assert "candidatos encontrados" in out and "[1]" in out and "[2]" in out and "Ruta de SPARK_HOME" in out
    assert "spark-3.5.6" in (tmp / "pkg" / ".bnx_spark.env").read_text()


def test_con_tty_repregunta_3_veces_y_falla(entorno):
    rc, out = _con_tty(entorno, ["/no/existe", "/tampoco", "/nada"])
    assert rc != 0 and out.count("ruta no valida") == 3 and "3 intentos" in out


def test_con_tty_acepta_la_segunda(entorno):
    tmp, _ = entorno
    h = _spark_home(tmp)
    rc, out = _con_tty(entorno, ["/mala", str(h)])
    assert rc == 0 and "ruta no valida" in out


def test_paquete_modo_servidor_e_incluido():
    files = {"requirements.txt": "pandas\n", "main.py": "x=1\n"}
    for modo, full in (("servidor", False), ("incluido", True)):
        # solo se ejercita el marcador de modo (BNX_NO_DOWNLOAD evita bajar nada; sin cache: sin wheels)
        data, _fn, _ = mp.zip_from_files(files, py_target="py3.8", spark_modo=modo)
        z = zipfile.ZipFile(__import__("io").BytesIO(data))
        assert z.read("framework_mlops_v2_pkg/vendor/PYSPARK_MODE").decode().strip() == modo
    # compat: sin spark_modo manda full_env
    data, _fn, _ = mp.zip_from_files(files, py_target="py3.8", full_env=False)
    assert zipfile.ZipFile(__import__("io").BytesIO(data)).read(
        "framework_mlops_v2_pkg/vendor/PYSPARK_MODE").decode().strip() == "servidor"


@pytest.mark.skipif(os.environ.get("BNX_TEST_SPARK_REAL") != "1", reason="prueba real: BNX_TEST_SPARK_REAL=1")
def test_real_pyspark_del_venv_como_servidor(entorno):
    """Usa el pyspark instalado en este venv como 'servidor' y corre un job local SIN wheel de pyspark."""
    import pyspark
    tmp, _env = entorno
    r = _bash(entorno, "bnx_spark_configurar", {"BNX_SPARK_HOME": os.path.dirname(pyspark.__file__),
                                                 "PATH": "%s:%s" % (tmp / "pkg" / ".venv" / "bin", os.environ["PATH"])},
              stdin=subprocess.DEVNULL)
    assert r.returncode == 0, r.stdout + r.stderr
    env = dict(entorno[1], PYSPARK_PYTHON=str(tmp / "pkg" / ".venv" / "bin" / "python"),
               PATH="%s:%s" % (tmp / "pkg" / ".venv" / "bin", os.environ["PATH"]))   # java REAL
    env.pop("PYTHONPATH", None)
    out = subprocess.run(
        ["bash", "-c", "set -e; . ./.bnx_spark.env; export SPARK_HOME; [ -n \"$BNX_SPARK_PYPATH\" ] && export PYTHONPATH=\"$BNX_SPARK_PYPATH\"; "
         ".venv/bin/python -c \"import pyspark;from pyspark.sql import SparkSession as S;"
         "s=S.builder.master('local[1]').config('spark.ui.enabled','false').getOrCreate();"
         "print('N',s.range(10).count(),pyspark.__file__);s.stop()\""],
        cwd=str(tmp / "pkg"), capture_output=True, text=True, env=env, timeout=300)
    assert "N 10" in out.stdout, out.stdout + out.stderr[-500:]
