# -*- coding: utf-8 -*-
"""Tests (sin red) del pip viejo: eleccion de un pip moderno, saneo del texto de uso de pip,
mensaje 'Falta el cache' con nombres de paquete y job fallido sin 'Listo'."""
import os
import subprocess
import sys
import zipfile
import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
os.environ.setdefault("BNX_NO_DOWNLOAD", "1")
from src import vendor_cache as vc  # noqa: E402

USO = ("Usage:   \n  /x/python -m pip install [options] <requirement specifier> ...\n"
       "  /x/python -m pip install [options] [-e] <local project path> ...\n"
       "no such option: --dry-run\n")


@pytest.fixture(autouse=True)
def _limpio(monkeypatch, tmp_path):
    monkeypatch.setenv("BNX_VENDOR_CACHE", str(tmp_path / "cache"))
    vc._PIP_VER.clear()
    vc._PIP_CMD.clear()
    yield
    vc._PIP_VER.clear()
    vc._PIP_CMD.clear()


def _wheel_pip(cache, serie, version, requires):
    d = os.path.join(str(cache), serie)
    os.makedirs(d, exist_ok=True)
    p = os.path.join(d, "pip-%s-py3-none-any.whl" % version)
    with zipfile.ZipFile(p, "w") as z:
        z.writestr("pip-%s.dist-info/METADATA" % version, "Name: pip\nRequires-Python: %s\n" % requires)
    return p


def _fake_run(version_pip):
    """subprocess.run falso: `python -m pip --version` -> version_pip; `python <whl>/pip --version` ok."""
    def run(cmd, **kw):
        if cmd[-1] == "--version":
            if cmd[1:3] == ["-m", "pip"]:
                out = ("pip %s from /x (python 3.11)" % version_pip) if version_pip else ""
                return subprocess.CompletedProcess(cmd, 0 if version_pip else 1, out, "")
            v = os.path.basename(os.path.dirname(cmd[1])).split("-")[1]
            return subprocess.CompletedProcess(cmd, 0, "pip %s from whl" % v, "")
        raise AssertionError("comando inesperado %r" % (cmd,))
    return run


def test_pip_moderno_se_usa_tal_cual(monkeypatch):
    monkeypatch.setattr(vc.subprocess, "run", _fake_run("25.0.1"))
    assert vc.pip_cmd() == [sys.executable, "-m", "pip"]


def test_pip_viejo_elige_wheel_del_cache_compatible(monkeypatch, tmp_path):
    cache = tmp_path / "cache"
    _wheel_pip(cache, "py38-311", "25.0.1", ">=3.8")
    nuevo = _wheel_pip(cache, "py312plus", "26.2.1", ">=3.10")
    monkeypatch.setattr(vc.subprocess, "run", _fake_run("21.3.1"))
    monkeypatch.setattr(sys, "version_info", (3, 11, 0, "final", 0))
    cmd = vc.pip_cmd()
    assert cmd == [sys.executable, nuevo + os.sep + "pip"]
    # Con un Python 3.8 el pip 26 (>=3.10) no sirve: se usa el 25.0.1
    vc._PIP_CMD.clear()
    monkeypatch.setattr(sys, "version_info", (3, 8, 10, "final", 0))
    assert os.path.basename(os.path.dirname(vc.pip_cmd()[1])) == "pip-25.0.1-py3-none-any.whl"


def test_pip_viejo_sin_wheel_mensaje_claro(monkeypatch):
    monkeypatch.setattr(vc.subprocess, "run", _fake_run("21.3.1"))
    monkeypatch.setattr(vc, "hay_internet", lambda timeout=8: False)
    with pytest.raises(vc.PipViejo) as e:
        vc.pip_cmd()
    msg = str(e.value)
    assert "21.3.1" in msg and "22.2" in msg and "--upgrade pip" in msg
    assert "Usage" not in msg and "\n" not in msg


def test_sin_pip_mensaje_ensurepip(monkeypatch):
    monkeypatch.setattr(vc.subprocess, "run", _fake_run(None))
    with pytest.raises(vc.PipViejo) as e:
        vc.pip_cmd()
    assert "ensurepip" in str(e.value)


def test_limpiar_stderr_pip_quita_usage(monkeypatch):
    monkeypatch.setattr(vc.subprocess, "run", _fake_run("21.3.1"))
    txt = vc.limpiar_stderr_pip(USO)
    assert "Usage" not in txt and "\n" not in txt
    assert "no such option: --dry-run" in txt and "21.3.1" in txt and "upgrade pip" in txt
    # stderr normal: solo la primera linea ERROR
    assert vc.limpiar_stderr_pip("WARN x\nERROR: No matching distribution found for foo\nERROR: otro") == \
        "No matching distribution found for foo"


def test_falta_deps_lista_nombres_y_nunca_usage():
    out = vc._falta_deps(["sin wheel en el cache: xgboost, cytoolz", USO,
                          "No matching distribution found for pandas"])
    assert out[0] == "dependencias open source: cytoolz, pandas, xgboost"
    assert all("Usage" not in x and "\n" not in x for x in out)


def test_estado_version_con_pip_viejo_no_pega_usage(monkeypatch, tmp_path):
    from src import mlops_pkg as mp
    monkeypatch.setattr(vc.subprocess, "run", _fake_run("21.3.1"))
    monkeypatch.setattr(vc, "hay_internet", lambda timeout=8: False)
    mp._seleccion_cache.clear()
    est = vc.estado_version("3.12", cache=str(tmp_path / "cache"))
    texto = " | ".join(est["falta"])
    assert "pyspark==4.0.0" in texto and "py4j==0.10.9.9" in texto
    assert "Usage" not in texto and "<local project path>" not in texto
    assert "pip de este Python" in texto and "21.3.1" in texto


def test_podar_con_faltantes_devuelve_error_y_no_borra(monkeypatch, tmp_path):
    import preparar_vendor as pv
    monkeypatch.setattr(vc, "sobrantes", lambda v, e, c: ([], {"3.8": "El pip de este Python es viejo"}))
    monkeypatch.setattr(sys.stdin, "isatty", lambda: False)
    assert pv.main(["--podar", "--si", "--python", "3.8"]) == 1


def test_job_fallido_expone_motivo_y_no_listo(monkeypatch, tmp_path):
    pytest.importorskip("serve_ui")
    import serve_ui
    log = tmp_path / "job.log"
    log.write_text("== Python 3.12 ==\n[github] no pude conectar a github.com: timed out; usa --zip\nERROR: x\n",
                   encoding="utf-8")

    class P:
        def poll(self):
            return 1
    monkeypatch.setitem(serve_ui._VENDOR_JOB, "proc", P())
    monkeypatch.setitem(serve_ui._VENDOR_JOB, "log", str(log))
    info = serve_ui._vendor_job_info()
    assert info["returncode"] == 1 and info["motivo"].startswith("ERROR")
    ok = open(os.path.join(ROOT, "ui", "src", "components", "MLOpsPackagePage.jsx"), encoding="utf-8").read()
    assert "Listo: ya puedes generar de nuevo" not in ok     # ya no se muestra a ciegas


def test_desde_github_sin_red_explica_motivo(monkeypatch, tmp_path):
    def boom(*a, **k):
        raise OSError("[Errno 11001] getaddrinfo failed")
    monkeypatch.setattr(vc, "_http_get", boom)
    logs = []
    assert vc.desde_github("3.12", cache=str(tmp_path / "c"), log=logs.append) is False
    txt = "\n".join(logs)
    assert "no pude conectar a github.com" in txt and "getaddrinfo" in txt and "--zip" in txt and "HTTPS_PROXY" in txt
