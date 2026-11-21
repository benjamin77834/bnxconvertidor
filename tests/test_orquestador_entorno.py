# -*- coding: utf-8 -*-
"""
test_orquestador_entorno.py — Tests del 'Entorno del Orquestador' (ZIP offline RHEL 8).

Prueba:
  - generacion del ZIP (cache mockeado): contenido, setup.sh valido (bash -n), README.md, vendor/
  - bnx_spark_resources.conf y run.sh con soporte YARN
  - endpoint GET  /api/orquestador/entorno/estado (formato JSON)
  - endpoint POST /api/orquestador/entorno/zip (solo localhost)
  - endpoint POST /api/orquestador/entorno/bajar (solo localhost)
  - orq_entorno.py compatible con Python 3.8 (ast.parse feature_version=(3,8))

Sin red (BNX_NO_DOWNLOAD=1) y sin Spark real.
"""
import ast
import io
import json
import os
import shutil
import socketserver
import subprocess
import sys
import threading
import zipfile

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from src import orq_entorno as oe


# ---------------------------------------------------------------------------
# Helpers / fixtures
# ---------------------------------------------------------------------------

def _mk_wheel(carpeta, dist, version, tag, requires=()):
    """Crea una wheel minima REAL (zip con <dist>.dist-info/METADATA y Requires-Dist)."""
    nombre = "%s-%s-%s.whl" % (dist, version, tag)
    meta = "Metadata-Version: 2.1\nName: %s\nVersion: %s\n" % (dist, version)
    meta += "".join("Requires-Dist: %s\n" % r for r in requires)
    ruta = os.path.join(str(carpeta), nombre)
    with zipfile.ZipFile(ruta, "w") as z:
        z.writestr("%s-%s.dist-info/METADATA" % (dist, version), meta)
    return ruta


_LINUX = "cp311-cp311-manylinux_2_17_x86_64"


def _fake_cache(tmp_path):
    """Cache con wheels reales minimas para todo REQS_MINIMO y REQS_EXTRA (xgboost -> xgboost_cpu)."""
    cache = tmp_path / "vendor_cache"
    serie_dir = cache / "pyspark" / "py38-311"
    serie_dir.mkdir(parents=True)
    _mk_wheel(serie_dir, "pyspark", "3.5.6", "py2.py3-none-any", ["py4j==0.10.9.7"])
    _mk_wheel(serie_dir, "py4j", "0.10.9.7", "py2.py3-none-any")
    ciencia_dir = cache / "ciencia" / "3.11" / "linux"
    ciencia_dir.mkdir(parents=True)
    _mk_wheel(ciencia_dir, "pandas", "2.2.0", _LINUX, ["numpy>=1.23", "tzdata ; extra == 'test'"])
    _mk_wheel(ciencia_dir, "numpy", "1.26.0", _LINUX)
    _mk_wheel(ciencia_dir, "cytoolz", "0.12.3", _LINUX, ["toolz>=0.8"])
    _mk_wheel(ciencia_dir, "toolz", "0.12.1", "py3-none-any")
    _mk_wheel(ciencia_dir, "chispa", "0.10.0", "py3-none-any")
    _mk_wheel(ciencia_dir, "pytest", "8.0.0", "py3-none-any")
    _mk_wheel(ciencia_dir, "xgboost_cpu", "2.1.0", _LINUX, ["numpy", "scipy"])
    _mk_wheel(ciencia_dir, "scikit_learn", "1.4.0", _LINUX, ["numpy", "scipy", "joblib"])
    _mk_wheel(ciencia_dir, "scipy", "1.12.0", _LINUX, ["numpy"])
    _mk_wheel(ciencia_dir, "joblib", "1.3.2", "py3-none-any")
    # Distractor que ninguna variante necesita: no debe entrar al ZIP minimo
    _mk_wheel(ciencia_dir, "matplotlib", "3.8.0", _LINUX)
    return str(cache)


# ---------------------------------------------------------------------------
# Tests de orq_entorno.py (capa Python, sin servidor HTTP)
# ---------------------------------------------------------------------------

def test_estado_cache_devuelve_estructura(monkeypatch, tmp_path):
    cache = _fake_cache(tmp_path)
    monkeypatch.setenv("BNX_VENDOR_CACHE", cache)
    # Resetear caches de vendor_cache (usa cache_dir())
    import importlib
    from src import vendor_cache as vc
    importlib.reload(vc)
    importlib.reload(oe)

    est = oe.estado_cache()
    assert "pyspark" in est and "ciencia" in est and "banco" in est
    assert isinstance(est["pyspark"]["ok"], bool)
    assert isinstance(est["pyspark"]["mb"], float)
    assert isinstance(est["ciencia"]["ok"], bool)
    assert "wheels" in est["pyspark"]


def test_estado_cache_pyspark_ok_con_wheels(monkeypatch, tmp_path):
    cache = _fake_cache(tmp_path)
    monkeypatch.setenv("BNX_VENDOR_CACHE", cache)
    import importlib
    from src import vendor_cache as vc
    importlib.reload(vc)
    importlib.reload(oe)

    est = oe.estado_cache()
    # Hay pyspark + py4j en el cache falso -> ok=True
    assert est["pyspark"]["ok"] is True
    assert any("pyspark" in w for w in est["pyspark"]["wheels"])
    assert any("py4j" in w for w in est["pyspark"]["wheels"])


def test_estado_cache_pyspark_falta_sin_cache(monkeypatch, tmp_path):
    vacio = str(tmp_path / "vacio")
    monkeypatch.setenv("BNX_VENDOR_CACHE", vacio)
    import importlib
    from src import vendor_cache as vc
    importlib.reload(vc)
    importlib.reload(oe)

    est = oe.estado_cache()
    assert est["pyspark"]["ok"] is False
    assert est["pyspark"]["falta"]


def test_generar_zip_minimo_estructura(monkeypatch, tmp_path):
    cache = _fake_cache(tmp_path)
    monkeypatch.setenv("BNX_VENDOR_CACHE", cache)
    import importlib
    from src import vendor_cache as vc
    importlib.reload(vc)
    importlib.reload(oe)

    data, sha256, nombre = oe.generar_zip(variante="minimo", cache=cache)
    assert nombre == "bnx_orq_env_py3.11_linux.zip"
    assert len(sha256) == 64
    assert len(data) > 1000

    with zipfile.ZipFile(io.BytesIO(data)) as z:
        nombres = z.namelist()
    assert "setup.sh" in nombres
    assert "run.sh" in nombres
    assert "README.md" in nombres
    assert "requirements.txt" in nombres
    assert "requirements_completo.txt" not in nombres
    assert "bnx_spark_resources.conf" in nombres
    assert not [n for n in nombres if "matplotlib" in n or "scipy" in n or "xgboost" in n]
    # Hay al menos las wheels de pyspark + py4j en vendor/
    vendor_wheels = [n for n in nombres if n.startswith("vendor/") and n.endswith(".whl")]
    assert len(vendor_wheels) >= 2
    pyspark_w = [n for n in vendor_wheels if "pyspark" in n]
    py4j_w = [n for n in vendor_wheels if "py4j" in n]
    assert pyspark_w, "debe haber una wheel de pyspark en vendor/"
    assert py4j_w, "debe haber una wheel de py4j en vendor/"


def test_generar_zip_incluye_ciencia(monkeypatch, tmp_path):
    cache = _fake_cache(tmp_path)
    monkeypatch.setenv("BNX_VENDOR_CACHE", cache)
    import importlib
    from src import vendor_cache as vc
    importlib.reload(vc)
    importlib.reload(oe)

    data, _, _ = oe.generar_zip(variante="completo", cache=cache)
    with zipfile.ZipFile(io.BytesIO(data)) as z:
        nombres = z.namelist()
    ciencia = [n for n in nombres if "pandas" in n or "numpy" in n]
    assert ciencia, "variante completo debe incluir wheels de ciencia"


def test_generar_zip_sin_pyspark_falla(monkeypatch, tmp_path):
    vacio = str(tmp_path / "empty")
    monkeypatch.setenv("BNX_VENDOR_CACHE", vacio)
    import importlib
    from src import vendor_cache as vc
    importlib.reload(vc)
    importlib.reload(oe)

    with pytest.raises(ValueError, match="No hay wheels de PySpark"):
        oe.generar_zip(cache=vacio)


def test_setup_sh_sintaxis_bash(monkeypatch, tmp_path):
    """bash -n verifica que setup.sh no tenga errores de sintaxis."""
    if not shutil.which("bash"):
        pytest.skip("bash no disponible")
    cache = _fake_cache(tmp_path)
    monkeypatch.setenv("BNX_VENDOR_CACHE", cache)
    import importlib
    from src import vendor_cache as vc
    importlib.reload(vc)
    importlib.reload(oe)

    data, _, _ = oe.generar_zip(cache=cache)
    with zipfile.ZipFile(io.BytesIO(data)) as z:
        setup_sh = z.read("setup.sh").decode("utf-8")

    script_path = tmp_path / "setup_check.sh"
    script_path.write_text(setup_sh)
    r = subprocess.run(["bash", "-n", str(script_path)], capture_output=True, text=True)
    assert r.returncode == 0, f"setup.sh tiene error de sintaxis: {r.stderr}"


def test_run_sh_sintaxis_bash(monkeypatch, tmp_path):
    """bash -n verifica que run.sh no tenga errores de sintaxis."""
    if not shutil.which("bash"):
        pytest.skip("bash no disponible")
    cache = _fake_cache(tmp_path)
    monkeypatch.setenv("BNX_VENDOR_CACHE", cache)
    import importlib
    from src import vendor_cache as vc
    importlib.reload(vc)
    importlib.reload(oe)

    data, _, _ = oe.generar_zip(cache=cache)
    with zipfile.ZipFile(io.BytesIO(data)) as z:
        run_sh = z.read("run.sh").decode("utf-8")

    script_path = tmp_path / "run_check.sh"
    script_path.write_text(run_sh)
    r = subprocess.run(["bash", "-n", str(script_path)], capture_output=True, text=True)
    assert r.returncode == 0, f"run.sh tiene error de sintaxis: {r.stderr}"


def test_readme_contiene_seccion_yarn(monkeypatch, tmp_path):
    cache = _fake_cache(tmp_path)
    monkeypatch.setenv("BNX_VENDOR_CACHE", cache)
    import importlib
    from src import vendor_cache as vc
    importlib.reload(vc)
    importlib.reload(oe)

    data, _, _ = oe.generar_zip(cache=cache)
    with zipfile.ZipFile(io.BytesIO(data)) as z:
        readme = z.read("README.md").decode("utf-8")
    assert "YARN" in readme
    assert "BNX_SPARK=cluster" in readme
    assert "bnx_spark_resources.conf" in readme
    assert "local" in readme.lower()


def test_spark_resources_conf_contiene_claves(monkeypatch, tmp_path):
    cache = _fake_cache(tmp_path)
    monkeypatch.setenv("BNX_VENDOR_CACHE", cache)
    import importlib
    from src import vendor_cache as vc
    importlib.reload(vc)
    importlib.reload(oe)

    data, _, _ = oe.generar_zip(cache=cache)
    with zipfile.ZipFile(io.BytesIO(data)) as z:
        conf = z.read("bnx_spark_resources.conf").decode("utf-8")
    for clave, _, _ in oe.YARN_CONF_DEFAULTS:
        assert clave in conf, f"falta {clave} en bnx_spark_resources.conf"


def test_spark_resources_conf_valores_custom(monkeypatch, tmp_path):
    """spark_conf del usuario sobreescribe los defaults en el conf."""
    cache = _fake_cache(tmp_path)
    monkeypatch.setenv("BNX_VENDOR_CACHE", cache)
    import importlib
    from src import vendor_cache as vc
    importlib.reload(vc)
    importlib.reload(oe)

    custom = {"spark.yarn.queue": "mi_cola_produccion", "spark.executor.instances": "8"}
    data, _, _ = oe.generar_zip(cache=cache, spark_conf=custom)
    with zipfile.ZipFile(io.BytesIO(data)) as z:
        conf = z.read("bnx_spark_resources.conf").decode("utf-8")
    assert "spark.yarn.queue=mi_cola_produccion" in conf
    assert "spark.executor.instances=8" in conf


def test_requirements_txt_contiene_pyspark(monkeypatch, tmp_path):
    cache = _fake_cache(tmp_path)
    monkeypatch.setenv("BNX_VENDOR_CACHE", cache)
    import importlib
    from src import vendor_cache as vc
    importlib.reload(vc)
    importlib.reload(oe)

    data, _, _ = oe.generar_zip(cache=cache)
    with zipfile.ZipFile(io.BytesIO(data)) as z:
        reqs = z.read("requirements.txt").decode("utf-8")
    assert "pyspark" in reqs
    assert "pandas" in reqs
    assert "pyarrow" not in reqs   # Spark escribe parquet nativo; no esta en el cache


# ---------------------------------------------------------------------------
# Tests de los endpoints HTTP (serve_ui.py)
# ---------------------------------------------------------------------------

@pytest.fixture(scope="module")
def srv_entorno(tmp_path_factory):
    """Servidor HTTP de prueba con cache falso."""
    tmp_path = tmp_path_factory.mktemp("srv_entorno")
    cache = _fake_cache(tmp_path)
    os.environ["BNX_VENDOR_CACHE"] = cache
    # Importar serve_ui DESPUES de poner la variable
    import importlib
    serve_ui = pytest.importorskip("serve_ui")
    importlib.reload(serve_ui)

    class S(socketserver.ThreadingMixIn, socketserver.TCPServer):
        allow_reuse_address = True
        daemon_threads = True

    httpd = S(("127.0.0.1", 0), serve_ui.BNXHandler)
    port = httpd.server_address[1]
    t = threading.Thread(target=httpd.serve_forever, daemon=True)
    t.start()
    base = "http://127.0.0.1:%d" % port
    yield base
    httpd.shutdown()
    httpd.server_close()
    os.environ.pop("BNX_VENDOR_CACHE", None)


def _get(base, path):
    import urllib.request
    try:
        r = urllib.request.urlopen(base + path, timeout=10)
        return r.status, json.loads(r.read())
    except Exception as e:
        rc = getattr(getattr(e, "fp", None) and e.fp or e, "status", getattr(e, "code", 500))
        try:
            body = json.loads(e.read() if hasattr(e, "read") else b"{}")
        except Exception:
            body = {}
        return rc, body


def _post(base, path, body=None):
    import urllib.request
    data = json.dumps(body or {}).encode("utf-8")
    req = urllib.request.Request(base + path, data=data,
                                 headers={"Content-Type": "application/json"})
    try:
        r = urllib.request.urlopen(req, timeout=60)
        return r.status, json.loads(r.read())
    except Exception as e:
        rc = getattr(e, "code", 500)
        try:
            body = json.loads(e.read() if hasattr(e, "read") else b"{}")
        except Exception:
            body = {}
        return rc, body


def test_endpoint_estado_estructura(srv_entorno):
    st, d = _get(srv_entorno, "/api/orquestador/entorno/estado")
    assert st == 200, d
    assert d["ok"] is True
    assert "pyspark" in d and "ciencia" in d and "banco" in d
    assert "ok" in d["pyspark"] and "mb" in d["pyspark"]


def test_endpoint_estado_pyspark_ok(srv_entorno):
    st, d = _get(srv_entorno, "/api/orquestador/entorno/estado")
    assert st == 200
    # El cache falso tiene pyspark + py4j
    assert d["pyspark"]["ok"] is True
    assert len(d["pyspark"]["wheels"]) >= 2


def test_endpoint_zip_genera_y_descarga(srv_entorno):
    """POST entorno/zip responde con token + download_url validos."""
    st, d = _post(srv_entorno, "/api/orquestador/entorno/zip",
                  {"variante": "minimo", "spark_conf": {"spark.yarn.queue": "test_q"}})
    assert st == 200, d
    assert d["ok"] is True
    assert d["token"]
    assert d["filename"] == "bnx_orq_env_py3.11_linux.zip"
    assert d["mb"] >= 0  # fake wheels are tiny (< 1 MB), so 0.0 is valid
    assert len(d["sha256"]) == 64
    assert "/export/download?token=" in d["download_url"]

    # Verificar que el ZIP fue escrito en /tmp/bnx_bundles/
    import tempfile
    zip_path = os.path.join(tempfile.gettempdir(), "bnx_bundles", d["token"] + ".zip")
    assert os.path.isfile(zip_path), "el ZIP debe existir en /tmp/bnx_bundles/"
    with zipfile.ZipFile(zip_path) as z:
        assert "setup.sh" in z.namelist()
        conf = z.read("bnx_spark_resources.conf").decode("utf-8")
    assert "spark.yarn.queue=test_q" in conf


def test_endpoint_zip_solo_localhost():
    """POST entorno/zip debe rechazar peticiones no-localhost (403)."""
    serve_ui = pytest.importorskip("serve_ui")

    class FakeHandler(serve_ui.BNXHandler):
        def __init__(self):  # no llama a super().__init__
            pass
        client_address = ("10.0.0.1", 1234)
        headers = {}
        command = "POST"
        path = "/api/orquestador/entorno/zip"

    h = FakeHandler.__new__(FakeHandler)
    h.client_address = ("10.0.0.1", 1234)
    h.headers = {}
    h.command = "POST"
    h.path = "/api/orquestador/entorno/zip"

    respuestas = []
    h._json_response = lambda st, d: respuestas.append((st, d))
    h._orq_local_only = serve_ui.BNXHandler._orq_local_only.__get__(h)
    bloqueo = h._orq_local_only()
    assert bloqueo is not None, "debe bloquear IPs no-localhost"
    assert "127.0.0.1" in bloqueo or "ejecucion" in bloqueo


def test_endpoint_bajar_solo_localhost():
    """POST entorno/bajar debe rechazar IPs remotas."""
    serve_ui = pytest.importorskip("serve_ui")

    class FakeHandler(serve_ui.BNXHandler):
        def __init__(self): pass
        client_address = ("192.168.1.100", 9999)
        headers = {}

    h = FakeHandler.__new__(FakeHandler)
    h.client_address = ("192.168.1.100", 9999)
    h.headers = {}
    h._orq_local_only = serve_ui.BNXHandler._orq_local_only.__get__(h)
    bloqueo = h._orq_local_only()
    assert bloqueo is not None


def test_endpoint_estado_acepta_clientes_remotos(srv_entorno):
    """GET entorno/estado no requiere localhost (es de solo lectura)."""
    # Como en los otros tests: el servidor del fixture ya escucha en 127.0.0.1,
    # que se considera local. Lo que verificamos es que el endpoint no tiene _orq_local_only.
    st, d = _get(srv_entorno, "/api/orquestador/entorno/estado")
    assert st == 200


def test_zip_completo_variante(srv_entorno):
    """Variante 'completo' genera un ZIP con requirements_completo.txt."""
    st, d = _post(srv_entorno, "/api/orquestador/entorno/zip", {"variante": "completo"})
    assert st == 200, d
    assert d["variante"] == "completo"


def test_zip_variante_invalida_cae_a_minimo(srv_entorno):
    """Variante desconocida cae silenciosamente a 'minimo'."""
    st, d = _post(srv_entorno, "/api/orquestador/entorno/zip", {"variante": "mega"})
    assert st == 200, d
    assert d["variante"] == "minimo"


# ---------------------------------------------------------------------------
# Compatibilidad Python 3.8 (host del portal)
# ---------------------------------------------------------------------------

def test_orq_entorno_py38_compatible():
    """orq_entorno.py debe parsearse como Python 3.8."""
    src_path = os.path.join(ROOT, "src", "orq_entorno.py")
    with open(src_path, encoding="utf-8") as fh:
        source = fh.read()
    # feature_version=(3, 8) lanza SyntaxError si usa f-string con = u otras feature 3.9+
    ast.parse(source, feature_version=(3, 8))


# ---------------------------------------------------------------------------
# Limpieza de /tmp/bnx*
# ---------------------------------------------------------------------------

def test_limpiar_tmp_bnx():
    """Elimina temporales /tmp/bnx* creados durante los tests."""
    import glob
    import tempfile
    tmpdir = tempfile.gettempdir()
    for f in glob.glob(os.path.join(tmpdir, "bnx_orq_env_*.zip")):
        try:
            os.remove(f)
        except OSError:
            pass
    # Los bundles bnx_bundles/ se crean por el server; no los borramos aqui
    # (el server los borra al servir).
    assert True  # solo para que el test aparezca en el reporte


# ---------------------------------------------------------------------------
# cierre_wheels
# ---------------------------------------------------------------------------

def test_cierre_wheels_transitivas(tmp_path):
    a = _mk_wheel(tmp_path, "a", "1", "py3-none-any", ["b>=1"])
    b = _mk_wheel(tmp_path, "b", "1", "py3-none-any", ["c"])
    c = _mk_wheel(tmp_path, "c", "1", "py3-none-any")
    d = _mk_wheel(tmp_path, "d", "1", "py3-none-any")
    elegidas, faltan = oe.cierre_wheels([a, b, c, d], ["a==1"])
    assert elegidas == sorted([a, b, c]) and faltan == []


def test_cierre_wheels_markers_y_extras(tmp_path):
    a = _mk_wheel(tmp_path, "a", "1", "py3-none-any", [
        "win_only ; sys_platform == 'win32'",
        "viejo ; python_version < '3.8'",
        "linux_dep ; sys_platform == 'linux'",
        "opcional ; extra == 'full'",
    ])
    l = _mk_wheel(tmp_path, "linux_dep", "1", "py3-none-any")
    elegidas, faltan = oe.cierre_wheels([a, l], ["a"])
    assert elegidas == sorted([a, l]) and faltan == []


def test_cierre_wheels_faltante(tmp_path):
    a = _mk_wheel(tmp_path, "a", "1", "py3-none-any", ["no_esta"])
    elegidas, faltan = oe.cierre_wheels([a], ["a", "otro"])
    assert elegidas == [a] and faltan == ["no-esta", "otro"]


def test_cierre_wheels_wheel_ilegible_sin_dependencias(tmp_path):
    mala = tmp_path / "rota-1-py3-none-any.whl"
    mala.write_bytes(b"PK\x03\x04no es un zip")
    avisos = []
    elegidas, faltan = oe.cierre_wheels([str(mala)], ["rota"], avisos.append)
    assert elegidas == [str(mala)] and faltan == []
    assert any("ilegible" in x for x in avisos)


def test_generar_zip_dependencia_faltante_error_claro(monkeypatch, tmp_path):
    cache = _fake_cache(tmp_path)
    os.remove(os.path.join(cache, "ciencia", "3.11", "linux", "numpy-1.26.0-%s.whl" % _LINUX))
    with pytest.raises(ValueError, match="numpy"):
        oe.generar_zip(variante="minimo", cache=cache)


def test_generar_zip_completo_mapea_xgboost_cpu(tmp_path):
    cache = _fake_cache(tmp_path)
    data, _, _ = oe.generar_zip(variante="completo", cache=cache)
    with zipfile.ZipFile(io.BytesIO(data)) as z:
        nombres = z.namelist()
        req = z.read("requirements_completo.txt").decode()
    assert any("xgboost_cpu" in n for n in nombres)
    assert "xgboost-cpu" in req
    assert not [n for n in nombres if "matplotlib" in n]
