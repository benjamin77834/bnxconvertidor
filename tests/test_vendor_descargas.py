# -*- coding: utf-8 -*-
"""Descargas del vendor desde el portal: generacion desde un cache de prueba (wheels falsas), ida y vuelta con
la importacion existente, control de acceso (localhost / clave / expiracion / revocar / banco / rate limit /
lista blanca) y streaming con Range. Cliente remoto simulado forzando la IP del handler."""
import ast
import io
import json
import os
import subprocess
import sys
import threading
import urllib.error
import urllib.request
import zipfile

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
os.environ.setdefault("BNX_NO_DOWNLOAD", "1")
from src import vendor_cache as vc  # noqa: E402
from src import vendor_descargas as vd  # noqa: E402

REMOTA = "10.20.30.40"


def _w(path, contenido=b"w" * 200):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "wb") as fh:
        fh.write(contenido)


@pytest.fixture
def cache(tmp_path, monkeypatch):
    c = tmp_path / "cache"
    monkeypatch.setenv("BNX_VENDOR_CACHE", str(c))
    monkeypatch.delenv("BNX_DESCARGAS_DIR", raising=False)
    # layout viejo para pyspark 3.11 (py38-311) y nuevo para el resto: ambos deben exportarse
    _w(str(c / "py38-311/pyspark-3.5.6-py2.py3-none-any.whl"), b"s" * 3000)
    _w(str(c / "py38-311/py4j-0.10.9.7-py2.py3-none-any.whl"))
    _w(str(c / "pyspark/py314/pyspark-4.1.2-py2.py3-none-any.whl"), b"t" * 3000)
    _w(str(c / "pyspark/py314/py4j-0.10.9.9-py2.py3-none-any.whl"))
    _w(str(c / "ciencia/3.11/linux/numpy-2.0.0-cp311-cp311-manylinux_2_28_x86_64.whl"))
    _w(str(c / "ciencia/3.14/linux/numpy-2.0.0-cp314-cp314-manylinux_2_28_x86_64.whl"))
    _w(str(c / "banco/wheels/mex_libextract-2.2.0-py3-none-any.whl"))
    _w(str(c / "banco/wheels/bnx_bank_pkgcode-1.0.0-py3-none-any.whl"))
    return c


@pytest.fixture
def desc(cache, tmp_path, monkeypatch):
    out = tmp_path / "desc"
    monkeypatch.setenv("BNX_DESCARGAS_DIR", str(out))

    def falso(destino, commit, root=None, log=print):
        with zipfile.ZipFile(destino, "w") as z:
            z.writestr("bnxconvertidor-empresav5/serve_ui.py", "x")
    monkeypatch.setattr(vd, "_zip_codigo", falso)
    monkeypatch.setattr(vd, "commit_corto", lambda root=vd.ROOT: "abc1234")
    vd._FALLOS.clear()
    idx = vd.preparar(str(cache), str(out), log=lambda m: None)
    return out, idx


# ------------------------------------------------------------------ generacion
def test_genera_archivos_formato_release(desc):
    out, idx = desc
    nombres = {a["nombre"] for a in idx["archivos"]}
    assert nombres == {"bnxconvertidor-empresav5_abc1234.zip", "banco.zip", "ciencia-linux-py3.11.zip",
                       "ciencia-linux-py3.14.zip", "pyspark-py3.11.zip", "pyspark-py3.14.zip",
                       "vendor-manifest.json", "SHA256SUMS"}
    with zipfile.ZipFile(out / "pyspark-py3.11.zip") as z:      # viene del layout viejo, sale en formato nuevo
        assert len(z.namelist()) == 2
        assert all(n.startswith(".bnx_vendor_cache/pyspark/py38-311/") for n in z.namelist())
    man = json.loads((out / "vendor-manifest.json").read_text())
    assert {(p["nombre"], p["python"], p["plataforma"]) for p in man["piezas"]} == {
        ("pyspark", "3.11", "any"), ("pyspark", "3.14", "any"), ("ciencia", "3.11", "linux"), ("ciencia", "3.14", "linux")}
    sums = (out / "SHA256SUMS").read_text()
    for a in idx["archivos"]:
        if a["nombre"] != "SHA256SUMS":
            assert "%s  %s" % (a["sha256"], a["nombre"]) in sums


def test_idempotente_y_regenera_si_cambia_el_cache(desc, cache):
    out, idx = desc
    msgs = []
    vd.preparar(str(cache), str(out), log=msgs.append)
    assert any("al dia" in m for m in msgs)
    t = os.path.getmtime(out / "pyspark-py3.11.zip")
    vd.preparar(str(cache), str(out), log=lambda m: None)
    assert os.path.getmtime(out / "pyspark-py3.11.zip") == t
    _w(str(cache / "ciencia/3.11/linux/pandas-2.2.0-cp311-cp311-manylinux_2_28_x86_64.whl"))
    assert vd.estado_archivos(str(cache), str(out))["desactualizado"]
    idx2 = vd.preparar(str(cache), str(out), log=lambda m: None)
    assert idx2["huella"] != idx["huella"]
    with zipfile.ZipFile(out / "ciencia-linux-py3.11.zip") as z:
        assert any("pandas" in n for n in z.namelist())


def test_ida_y_vuelta_importacion(desc, tmp_path):
    out, _ = desc
    env = dict(os.environ, BNX_VENDOR_CACHE=str(tmp_path / "angel"), BNX_NO_DOWNLOAD="1")
    pv = os.path.join(ROOT, "preparar_vendor.py")

    def run(*a):
        return subprocess.run([sys.executable, "-B", pv] + list(a), env=env, capture_output=True, text=True, timeout=300)
    r = run("--desde-dir", str(out), "--python", "3.11", "--plataformas", "linux")
    assert r.returncode == 0, r.stdout + r.stderr
    r = run("--zip", str(out / "banco.zip"))
    assert r.returncode == 0, r.stdout + r.stderr
    r = run("--estado", "--python", "3.11", "--plataformas", "linux")
    assert r.returncode == 0, r.stdout + r.stderr
    a = tmp_path / "angel"
    assert (a / "ciencia/3.11/linux").is_dir() and (a / "pyspark/py38-311").is_dir()
    assert (a / "banco/wheels/mex_libextract-2.2.0-py3-none-any.whl").is_file()


# ------------------------------------------------------------------ servidor con cliente local o remoto
@pytest.fixture
def srv(desc):
    serve_ui = pytest.importorskip("serve_ui")
    import socketserver

    ip = {"v": "127.0.0.1"}

    class H(serve_ui.BNXHandler):
        def _client_ip(self):          # simula un cliente de la red interna
            return ip["v"]

    class S(socketserver.ThreadingMixIn, socketserver.TCPServer):
        daemon_threads = True
        allow_reuse_address = True
    s = S(("127.0.0.1", 0), H)
    threading.Thread(target=s.serve_forever, daemon=True).start()
    yield "http://127.0.0.1:%d" % s.server_address[1], ip
    s.shutdown()
    s.server_close()


_OP = urllib.request.build_opener(urllib.request.ProxyHandler({}))


def _req(url, data=None, headers=None, method=None):
    h = dict(headers or {})
    if isinstance(data, dict):
        data, h["Content-Type"] = json.dumps(data).encode(), "application/json"
    rq = urllib.request.Request(url, data=data, headers=h, method=method)
    try:
        with _OP.open(rq, timeout=60) as r:
            return r.status, r.read(), dict(r.headers)
    except urllib.error.HTTPError as e:
        return e.code, e.read(), dict(e.headers)


def _compartir(base, **kw):
    st, b, _ = _req(base + "/api/vendor/descargas/compartir", dict(kw), {"Host": "localhost"})
    assert st == 200, b
    return json.loads(b)["clave"]


GET = "/api/vendor/descargas/get/"


def test_localhost_sin_clave_ok_y_streaming(srv):
    base, ip = srv
    st, body, h = _req(base + GET + "pyspark-py3.11.zip")
    assert st == 200 and h["Content-Length"] == str(len(body)) and "attachment" in h["Content-Disposition"]
    assert zipfile.ZipFile(io.BytesIO(body)).testzip() is None
    st, b, h = _req(base + GET + "pyspark-py3.11.zip", headers={"Range": "bytes=10-19"})
    assert st == 206 and b == body[10:20] and h["Content-Range"] == "bytes 10-19/%d" % len(body)
    st, b, _ = _req(base + GET + "pyspark-py3.11.zip", headers={"Range": "bytes=-5"})
    assert st == 206 and b == body[-5:]
    assert _req(base + GET + "pyspark-py3.11.zip", headers={"Range": "bytes=99999999-"})[0] == 416
    st, b, _ = _req(base + GET + "banco.zip")                  # el dueno (localhost) siempre puede
    assert st == 200


def test_remoto_sin_compartir_403(srv):
    base, ip = srv
    ip["v"] = REMOTA
    assert _req(base + GET + "pyspark-py3.11.zip")[0] == 403
    assert _req(base + GET + "pyspark-py3.11.zip", headers={"X-BNX-Clave": "x"})[0] == 403
    assert _req(base + "/api/vendor/descargas/estado")[0] == 403
    # y no puede gestionar
    assert _req(base + "/api/vendor/descargas/compartir", {}, {"Host": "localhost"})[0] == 403


def test_remoto_clave_buena_y_mala_con_rate_limit(srv, capsys):
    base, ip = srv
    clave = _compartir(base)
    ip["v"] = REMOTA
    assert _req(base + GET + "pyspark-py3.11.zip")[0] == 403                    # sin clave
    for _ in range(5):
        assert _req(base + GET + "pyspark-py3.11.zip", headers={"X-BNX-Clave": "mala"})[0] == 403
    assert _req(base + GET + "pyspark-py3.11.zip", headers={"X-BNX-Clave": "mala"})[0] == 429
    assert _req(base + GET + "pyspark-py3.11.zip", headers={"X-BNX-Clave": clave})[0] == 429   # bloqueada 1 min
    vd._FALLOS.clear()
    st, body, h = _req(base + GET + "pyspark-py3.11.zip", headers={"X-BNX-Clave": clave})
    assert st == 200 and h["Content-Length"] == str(len(body))
    # formulario del navegador: la clave va en el cuerpo, no en la URL
    st, body2, _ = _req(base + GET + "ciencia-linux-py3.11.zip", ("clave=%s" % clave).encode(),
                        {"Content-Type": "application/x-www-form-urlencoded"})
    assert st == 200 and zipfile.ZipFile(io.BytesIO(body2)).testzip() is None
    st, b, _ = _req(base + "/api/vendor/descargas/estado", headers={"X-BNX-Clave": clave})
    d = json.loads(b)
    assert st == 200 and not d["local"] and "compartir" not in d
    assert "banco.zip" not in {a["nombre"] for a in d["archivos"]}
    sal = capsys.readouterr().out
    assert clave not in sal and "mala" not in sal
    assert "ip=%s archivo=pyspark-py3.11.zip bytes=" % REMOTA in sal
    cfg = open(os.path.join(os.environ["BNX_DESCARGAS_DIR"], vd.CONFIG)).read()
    assert clave not in cfg and '"hash"' in cfg and '"sal"' in cfg


def test_banco_requiere_casilla_y_clave(srv):
    base, ip = srv
    clave = _compartir(base)                       # incluir_banco=False por defecto
    ip["v"] = REMOTA
    h = {"X-BNX-Clave": clave}
    st, b, _ = _req(base + GET + "banco.zip", headers=h)
    assert st == 403 and json.loads(b)["motivo"] == "banco_no_habilitado"
    ip["v"] = "127.0.0.1"
    assert _req(base + "/api/vendor/descargas/config", {"incluir_banco": True}, {"Host": "127.0.0.1"})[0] == 200
    ip["v"] = REMOTA
    assert _req(base + GET + "banco.zip", headers={"X-BNX-Clave": "mala"})[0] == 403   # casilla sola no basta
    st, body, _ = _req(base + GET + "banco.zip", headers=h)
    assert st == 200 and zipfile.ZipFile(io.BytesIO(body)).testzip() is None


def test_nombres_fuera_de_lista_blanca_400(srv):
    base, ip = srv
    for n in ("../_descargas.json", "..%2F..%2Fetc%2Fpasswd", "_descargas.json", "_indice.json", "passwd",
              "pyspark-py3.8.zip", "%2e%2e%2fserve_ui.py", "ciencia-linux-py3.11.zip%00", "a%5Cb.zip"):
        assert _req(base + GET + n)[0] in (400, 404), n
    assert _req(base + GET + "_descargas.json")[0] == 400
    assert _req(base + GET + "..%2F_descargas.json")[0] == 400
    assert _req(base + GET + "pyspark-py3.9.zip")[0] == 400
    assert _req(base + GET + "pyspark-py3.11.zip.bak")[0] == 400
    assert _req(base + GET + "ciencia-linux-py3.14.zip")[0] == 200


def test_expirada_y_revocada_403(srv, desc, monkeypatch):
    out, _ = desc
    base, ip = srv
    clave = _compartir(base, dias=1)
    ip["v"] = REMOTA
    h = {"X-BNX-Clave": clave}
    assert _req(base + GET + "SHA256SUMS", headers=h)[0] == 200
    cfgp = out / vd.CONFIG
    cfg = json.loads(cfgp.read_text())
    cfg["expira"] = 1.0
    cfgp.write_text(json.dumps(cfg))
    st, b, _ = _req(base + GET + "SHA256SUMS", headers=h)
    assert st == 403 and json.loads(b)["motivo"] == "expirada"
    ip["v"] = "127.0.0.1"
    clave = _compartir(base)
    ip["v"] = REMOTA
    assert _req(base + GET + "SHA256SUMS", headers={"X-BNX-Clave": clave})[0] == 200
    ip["v"] = "127.0.0.1"
    assert _req(base + "/api/vendor/descargas/revocar", {}, {"Host": "localhost"})[0] == 200
    ip["v"] = REMOTA
    assert _req(base + GET + "SHA256SUMS", headers={"X-BNX-Clave": clave})[0] == 403


def test_lista_de_ips_y_origen_ajeno(srv):
    base, ip = srv
    clave = _compartir(base, ips="192.168.0.0/16, 10.20.30.0/24")
    ip["v"] = "172.16.0.9"
    assert _req(base + GET + "SHA256SUMS", headers={"X-BNX-Clave": clave})[0] == 403
    ip["v"] = REMOTA
    assert _req(base + GET + "SHA256SUMS", headers={"X-BNX-Clave": clave})[0] == 200
    ip["v"] = "127.0.0.1"
    assert _req(base + "/api/vendor/descargas/compartir", {}, {"Origin": "http://evil.example"})[0] == 403
    assert _req(base + "/api/vendor/descargas/compartir", {"ips": "no-es-ip"}, {"Host": "localhost"})[0] == 400
    assert _req(base + "/api/vendor/descargas/compartir", {}, {"Host": "intranet.banco:8081"})[0] == 403   # rebinding


def test_autorizar_unitario(desc):
    out, _ = desc
    assert vd.autorizar("::1", None, str(out))[0] == 200
    clave = vd.compartir(outdir=str(out))
    assert vd.autorizar("10.0.0.1", clave, str(out))[1] == "ok"
    assert vd.autorizar("10.0.0.1", clave, str(out), ahora=10 ** 11)[1] == "expirada"
    assert os.stat(out / vd.CONFIG).st_mode & 0o077 == 0


def test_sintaxis_python38():
    for f in ("src/vendor_descargas.py", "exportar_vendor.py", "serve_ui.py"):
        with open(os.path.join(ROOT, f), encoding="utf-8") as fh:
            ast.parse(fh.read(), feature_version=(3, 8))
