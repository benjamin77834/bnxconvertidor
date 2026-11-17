# -*- coding: utf-8 -*-
"""Sin red: error de red vs 404 del manifiesto, tamanos sin red, glibc (RHEL 8), resolucion sin pip,
importar piezas desde ruta / subida en streaming (endpoints), bloqueo de 'generar' con vendor vacio y
compatibilidad de sintaxis Python 3.8 del codigo del portal."""
import ast
import glob
import hashlib
import io
import json
import os
import socket
import sys
import threading
import time
import urllib.error
import urllib.request
import zipfile
import pytest
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
os.environ.setdefault("BNX_NO_DOWNLOAD", "1")
from src import vendor_cache as vc  # noqa: E402
from src import vendor_modular as vm  # noqa: E402
from src import vendor_importar as vi  # noqa: E402


# ------------------------------------------------------------------ red vs 404
class _Origen(vm.OrigenGithub):
    def __init__(self, exc):
        super().__init__("vendor-v3")
        self.exc = exc

    def get_bytes(self, nombre):
        raise self.exc


def test_manifiesto_error_de_red_no_es_404():
    for exc in (urllib.error.URLError(socket.gaierror(8, "nodename nor servname provided")),
                socket.timeout("timed out"), ConnectionRefusedError(61, "Connection refused"),
                urllib.error.HTTPError("u", 503, "Service Unavailable", {}, None)):
        with pytest.raises(vm.ErrorRed):
            vm.leer_manifiesto(_Origen(exc))
    assert vm.leer_manifiesto(_Origen(urllib.error.HTTPError("u", 404, "Not Found", {}, None))) is None


def test_manifiesto_carpeta_sin_manifiesto_es_none(tmp_path):
    assert vm.leer_manifiesto(vm.OrigenDir(str(tmp_path))) is None


def test_preparar_sin_red_dice_no_pude_conectar_y_no_prueba_releases_viejas(monkeypatch, tmp_path, capsys):
    import preparar_vendor as pv
    monkeypatch.setenv("BNX_VENDOR_CACHE", str(tmp_path / "c"))
    monkeypatch.setattr(vm.OrigenGithub, "get_bytes",
                        lambda self, n: (_ for _ in ()).throw(urllib.error.URLError("getaddrinfo failed")))
    llamado = []
    monkeypatch.setattr(vc, "desde_github", lambda *a, **k: llamado.append(a))
    monkeypatch.setattr(vc, "hay_internet", lambda *a, **k: llamado.append("pip") or False)
    rc = pv.main(["--python", "3.11", "--plataformas", "linux"])
    out = capsys.readouterr().out
    assert rc == 1 and "No pude conectar a github.com: getaddrinfo failed" in out
    assert "no tiene vendor-manifest" not in out and "release anterior" not in out and not llamado


# ------------------------------------------------------------------ tamanos sin red
def test_tamanos_conocidos_sin_red_ni_manifiesto(tmp_path):
    pz = vm.estado_piezas(str(tmp_path), vm.seleccion(["3.11", "3.14"], ["linux", "windows"]))
    mb = {(p["pieza"], p["python"], p["plataforma"]): round(p["bytes_descarga"] / 1048576) for p in pz}
    assert mb[("ciencia", "3.11", "linux")] == 124 and mb[("ciencia", "3.11", "windows")] == 105
    assert mb[("ciencia", "3.14", "windows")] == 107 and mb[("pyspark", "3.11", "any")] == 303
    assert mb[("pyspark", "3.14", "any")] == 435 and all(v > 0 for v in mb.values())


# ------------------------------------------------------------------ RHEL 8 (glibc 2.28)
def test_glibc_de_wheels_y_tags_linux():
    g = vm.glibc_minima_wheel
    assert g("numpy-2.4.6-cp311-cp311-manylinux_2_27_x86_64.manylinux_2_28_x86_64.whl") == (2, 27)
    assert g("x-1-cp311-cp311-manylinux2014_x86_64.manylinux_2_17_x86_64.whl") == (2, 17)
    assert g("x-1-cp311-cp311-manylinux_2_34_x86_64.whl") == (2, 34)
    assert g("x-1-py3-none-any.whl") is None
    assert vm.wheels_glibc_incompatibles(["a-1-cp311-cp311-manylinux_2_31_x86_64.whl",
                                          "b-1-cp311-cp311-musllinux_1_2_x86_64.whl",
                                          "c-1-cp311-cp311-manylinux_2_28_x86_64.whl"]) == [
        "a-1-cp311-cp311-manylinux_2_31_x86_64.whl", "b-1-cp311-cp311-musllinux_1_2_x86_64.whl"]
    tags = vm.PLATAFORMAS["linux"]["tags"]
    assert "manylinux_2_28_x86_64" in tags and "manylinux_2_27_x86_64" in tags and "manylinux1_x86_64" in tags
    assert not any(t.startswith("musllinux") or t in ("manylinux_2_31_x86_64", "linux_x86_64") for t in tags)


def _whl(d, nombre, requires=(), version=None):
    p = os.path.join(str(d), nombre)
    dist, ver = nombre.split("-")[:2]
    with zipfile.ZipFile(p, "w") as z:
        z.writestr("%s-%s.dist-info/METADATA" % (dist, ver), "Metadata-Version: 2.1\nName: %s\nVersion: %s\n%s" % (
            dist, ver, "".join("Requires-Dist: %s\n" % r for r in requires)))
    return p


def test_resolver_interno_sin_pip_etiquetas_y_prerelease(tmp_path):
    fs = [_whl(tmp_path, "pandas-2.3.3-cp311-cp311-manylinux_2_24_x86_64.manylinux_2_28_x86_64.whl", ["numpy>=1.23", "wrapt"]),
          _whl(tmp_path, "numpy-2.4.6-cp311-cp311-manylinux_2_27_x86_64.manylinux_2_28_x86_64.whl"),
          _whl(tmp_path, "numpy-2.4.6-cp311-cp311-win_amd64.whl"),
          _whl(tmp_path, "numpy-2.4.6-cp314-cp314-manylinux_2_28_x86_64.whl"),
          _whl(tmp_path, "wrapt-2.6.0.dev1-cp311-cp311-manylinux1_x86_64.manylinux_2_28_x86_64.manylinux_2_5_x86_64.whl")]
    usados, faltan = vm.resolver_interno(fs, ["pandas"], "3.11", "linux")
    assert not faltan
    assert sorted(os.path.basename(u).split("-")[0] for u in usados) == ["numpy", "pandas", "wrapt"]
    assert all("win_amd64" not in u and "cp314" not in u for u in usados)
    _u, faltan = vm.resolver_interno(fs, ["scipy"], "3.11", "linux")
    assert "scipy" in faltan


# ------------------------------------------------------------------ importar desde ruta
def _pieza_zip(path, rel_files):
    with zipfile.ZipFile(path, "w") as z:
        for rel, data in rel_files.items():
            z.writestr(vc.ZIP_PREFIX + rel, data)
    return path


def _sha(p):
    return hashlib.sha256(open(p, "rb").read()).hexdigest()


def _release(d, sha_mal=False, v="3.11"):
    d.mkdir(parents=True, exist_ok=True)
    piezas = []
    cp, serie = "cp" + v.replace(".", ""), vc.serie_de(v)
    for t, v, pl, rel in (("ciencia", v, "linux", "ciencia/%s/linux/numpy-2.4.6-%s-%s-manylinux_2_28_x86_64.whl" % (v, cp, cp)),
                          ("ciencia", v, "windows", "ciencia/%s/windows/numpy-2.4.6-%s-%s-win_amd64.whl" % (v, cp, cp)),
                          ("pyspark", v, "any", "pyspark/%s/py4j-0.10.9.7-py2.py3-none-any.whl" % serie)):
        a = vm.archivo_pieza(t, v, pl)
        _pieza_zip(str(d / a), {rel: b"x" * 10})
        piezas.append({"nombre": t, "python": v, "plataforma": pl, "archivo": a, "bytes": 10,
                       "sha256": ("0" * 64) if (sha_mal and t == "ciencia" and pl == "linux") else _sha(str(d / a))})
    (d / vm.MANIFEST).write_text(json.dumps({"formato": 3, "piezas": piezas}))
    (d / vm.SUMS).write_text("".join("%s  %s\n" % (p["sha256"], p["archivo"]) for p in piezas))
    return d


def test_nombres_validos():
    assert vi.nombre_valido("ciencia-linux-py3.11.zip") and vi.nombre_valido("SHA256SUMS")
    assert vi.nombre_valido("mex-libextract-2.2.0.tar.gz") and vi.nombre_valido("vendor-manifest.json")
    for malo in ("../x.zip", "a/b.zip", "a\\b.zip", "x.exe", "", "..", ".zip", "C:x.zip"):
        assert not vi.nombre_valido(malo), malo


def test_importar_carpeta_release_solo_lo_elegido(tmp_path):
    rel = _release(tmp_path / "rel")
    cache = tmp_path / "cache"
    res = vi.importar_ruta(str(rel), str(cache), "3.11", ["linux"], con_pyspark=False, log=lambda *a: None)
    assert res == {"ciencia-linux-py3.11.zip": "ok"}
    assert (cache / "ciencia/3.11/linux").is_dir() and not (cache / "ciencia/3.11/windows").exists()
    assert not (cache / "pyspark").exists()


def test_importar_sha_mal_se_rechaza(tmp_path):
    rel = _release(tmp_path / "rel", sha_mal=True)
    cache = tmp_path / "cache"
    res = vi.importar_ruta(str(rel), str(cache), "3.11", ["linux"], True, log=lambda *a: None)
    assert "sha256" in res["ciencia-linux-py3.11.zip"] and not (cache / "ciencia/3.11/linux").exists()
    assert res["pyspark-py3.11.zip"] == "ok"


def test_importar_carpeta_bnx_interno_y_banco(tmp_path):
    base = tmp_path / "BNX_interno_v3"
    _release(base / "3_vendor_py3.11")
    _release(base / "3_vendor_py3.14", v="3.14")
    _pieza_zip(str(base / "2_banco.zip"), {"banco/wheels/mex_libextract-2.2.0-py3-none-any.whl": b"w"})
    cache = tmp_path / "cache"
    res = vi.importar_ruta(str(base), str(cache), "3.11", ["linux"], True, log=lambda *a: None)
    assert res.get("2_banco.zip") == "ok" and res.get("ciencia-linux-py3.11.zip") == "ok"
    assert (cache / "banco/wheels/mex_libextract-2.2.0-py3-none-any.whl").is_file()
    assert not (cache / "ciencia/3.14").exists()
    # el mismo paquete interno como UN ZIP
    zint = tmp_path / "BNX_interno_v3.zip"
    with zipfile.ZipFile(str(zint), "w") as z:
        for f in glob.glob(str(base / "**" / "*"), recursive=True):
            if os.path.isfile(f):
                z.write(f, os.path.relpath(f, str(tmp_path)))
    cache2 = tmp_path / "cache2"
    res = vi.importar_ruta(str(zint), str(cache2), "3.14", ["linux"], False, log=lambda *a: None)
    assert res.get("ciencia-linux-py3.14.zip") == "ok" and (cache2 / "banco/wheels").is_dir()
    assert not [d for d in os.listdir(str(cache2)) if d.startswith("bnx_int_")]   # temporal borrado


def test_importar_mex_lib_tar_gz_suelto(tmp_path, monkeypatch):
    monkeypatch.setattr(vc, "convertir_banco_a_wheels", lambda *a, **k: {"wheels": [], "fallos": {}})
    d = tmp_path / "libs"
    d.mkdir()
    (d / "mex-libextract-2.2.0.tar.gz").write_bytes(b"sdist")
    cache = tmp_path / "cache"
    res = vi.importar_ruta(str(d), str(cache), "3.11", ["linux"], True, log=lambda *a: None)
    assert list(res.values()) == ["ok"] and (cache / "banco/wheels/mex-libextract-2.2.0.tar.gz").is_file()


def test_importar_ruta_desconocida(tmp_path):
    (tmp_path / "vacia").mkdir()
    res = vi.importar_ruta(str(tmp_path / "vacia"), str(tmp_path / "c"), "3.11", ["linux"], True, log=lambda *a: None)
    assert "no reconozco" in list(res.values())[0]


# ------------------------------------------------------------------ endpoints (servidor real en un puerto libre)
@pytest.fixture
def servidor(tmp_path, monkeypatch):
    serve_ui = pytest.importorskip("serve_ui")
    monkeypatch.setenv("BNX_VENDOR_CACHE", str(tmp_path / "cache"))
    monkeypatch.setenv("BNX_UPLOAD_MAX_MB", "8")
    import socketserver

    class S(socketserver.ThreadingMixIn, socketserver.TCPServer):
        daemon_threads = True
        allow_reuse_address = True
    srv = S(("127.0.0.1", 0), serve_ui.BNXHandler)
    th = threading.Thread(target=srv.serve_forever, daemon=True)
    th.start()
    yield "http://127.0.0.1:%d" % srv.server_address[1], serve_ui
    srv.shutdown()
    srv.server_close()


_OPENER = urllib.request.build_opener(urllib.request.ProxyHandler({}))   # localhost: nunca por proxy


def _post(url, body=None, data=None, headers=None):
    if body is not None:
        data, headers = json.dumps(body).encode(), {"Content-Type": "application/json"}
    req = urllib.request.Request(url, data=data, method="POST", headers=headers or {})
    try:
        with _OPENER.open(req, timeout=600) as r:
            return r.status, json.loads(r.read() or b"{}")
    except urllib.error.HTTPError as e:
        return e.code, json.loads(e.read() or b"{}")


def _esperar(serve_ui):
    for _ in range(600):
        j = serve_ui._vendor_job_info(with_log=True)
        if not j["running"]:
            return j
        time.sleep(0.1)
    raise AssertionError("el job no termino")


def test_endpoint_importar_rutas(servidor, tmp_path):
    base, serve_ui = servidor
    assert _post(base + "/vendor/import", {"path": "relativa/x"})[0] == 400
    st, d = _post(base + "/vendor/import", {"path": str(tmp_path / "no_existe")})
    assert st == 400 and "no existe" in d["error"]
    (tmp_path / "x.txt").write_text("x")
    assert _post(base + "/vendor/import", {"path": str(tmp_path / "x.txt")})[0] == 400
    rel = _release(tmp_path / "BNX_interno_v3" / "3_vendor_py3.11")
    _pieza_zip(str(rel.parent / "2_banco.zip"), {"banco/wheels/mex_libextract-2.2.0-py3-none-any.whl": b"w"})
    st, d = _post(base + "/vendor/import", {"path": str(rel.parent), "version": "3.11",
                                            "piezas": {"pyspark": True, "ciencia_linux": True}})
    assert st == 200 and d["ok"]
    j = _esperar(serve_ui)
    assert j["returncode"] == 0, j["log"]
    assert (tmp_path / "cache/ciencia/3.11/linux").is_dir() and (tmp_path / "cache/banco/wheels").is_dir()
    assert not (tmp_path / "cache/ciencia/3.11/windows").exists()      # por defecto solo la ciencia linux


def test_endpoint_importar_solo_localhost(servidor, tmp_path):
    base, _ = servidor
    st, d = _post(base + "/vendor/import", {"path": str(tmp_path)}, )
    req = urllib.request.Request(base + "/vendor/import", data=json.dumps({"path": str(tmp_path)}).encode(),
                                 method="POST", headers={"Origin": "http://evil.example", "Content-Type": "application/json"})
    with pytest.raises(urllib.error.HTTPError) as e:
        _OPENER.open(req, timeout=30)
    assert e.value.code == 403


def _subir(base, lote, nombre, data):
    return _post(base + "/vendor/upload?lote=%s&name=%s" % (lote, nombre), data=data,
                 headers={"Content-Type": "application/octet-stream"})


def test_endpoint_subida_streaming_y_import_automatico(servidor, tmp_path):
    base, serve_ui = servidor
    lote = "ab" * 8
    rel = _release(tmp_path / "rel")
    grande = os.urandom(5 * 1048576 + 123)                              # varios MB, por bloques
    st, d = _subir(base, lote, "grande.whl", grande)
    assert st == 200 and d["bytes"] == len(grande) and d["sha256"] == hashlib.sha256(grande).hexdigest()
    os.remove(str(tmp_path / "cache/_subidas" / lote / "grande.whl"))
    for f in ("vendor-manifest.json", "SHA256SUMS", "ciencia-linux-py3.11.zip", "pyspark-py3.11.zip"):
        st, d = _subir(base, lote, f, (rel / f).read_bytes())
        assert st == 200, d
    banco = _pieza_zip(str(tmp_path / "2_banco.zip"), {"banco/wheels/mex_libgroupby-2.2.0-py3-none-any.whl": b"w"})
    assert _subir(base, lote, "2_banco.zip", open(banco, "rb").read())[0] == 200
    st, d = _post(base + "/vendor/upload/import", {"lote": lote, "version": "3.11",
                                                   "piezas": {"pyspark": True, "ciencia_linux": True}})
    assert st == 200, d
    j = _esperar(serve_ui)
    assert j["returncode"] == 0, j["log"]
    c = tmp_path / "cache"
    assert (c / "ciencia/3.11/linux").is_dir() and (c / "pyspark/py38-311").is_dir()
    assert (c / "banco/wheels/mex_libgroupby-2.2.0-py3-none-any.whl").is_file()
    assert not (c / "_subidas" / lote).exists()                        # temporales borrados


def test_endpoint_subida_rechazos(servidor, tmp_path):
    base, _ = servidor
    lote = "cd" * 8
    st, d = _subir(base, lote, "..%2Fx.zip", b"x")
    assert st == 400 and "no valido" in d["error"]
    assert _subir(base, lote, "x.exe", b"x")[0] == 400
    assert _subir(base, "../../etc", "x.zip", b"x")[0] == 400
    st, d = _subir(base, lote, "big.zip", b"0" * (9 * 1048576))         # limite BNX_UPLOAD_MAX_MB=8
    assert st == 413 and "limite" in d["error"]
    # sha256 mal -> no se importa nada y se borran las subidas
    rel = _release(tmp_path / "rel")
    for f in ("vendor-manifest.json", "SHA256SUMS", "pyspark-py3.11.zip"):
        _subir(base, lote, f, (rel / f).read_bytes())
    _subir(base, lote, "ciencia-linux-py3.11.zip", b"corrupto")
    st, d = _post(base + "/vendor/upload/import", {"lote": lote, "version": "3.11"})
    assert st == 400 and "sha256 no coincide" in d["error"] and "ciencia-linux-py3.11.zip" in d["sha_malos"]
    assert not (tmp_path / "cache/ciencia").exists() and not (tmp_path / "cache/_subidas" / lote).exists()


def test_generar_con_vendor_vacio_exige_confirmacion(servidor, tmp_path, monkeypatch):
    base, _ = servidor
    from src import mlops_pkg as mp
    vacio = tmp_path / "vacio"
    monkeypatch.setattr(mp, "_MLOPS_VENDOR_CACHE", str(vacio / "mlops_deps"))
    monkeypatch.setattr(mp, "_BANK_LIBS_CACHE", str(vacio / "banco"))
    for k in ("HTTPS_PROXY", "HTTP_PROXY", "https_proxy", "http_proxy"):   # sin red (como Angel)
        monkeypatch.setenv(k, "http://127.0.0.1:9")
    mp._seleccion_cache.clear()
    body = {"sources": [{"name": "job1.py", "code": "import xgboost\nx = 1\n"}], "py_target": "py3.11",
            "ciencia": True, "variantes": "ambas", "spark_modo": "ambas", "plataformas": []}
    st, d = _post(base + "/mlops/package/build", body)
    assert st == 409 and d["bloqueado"] and d["entorno_faltan"], d
    assert "NO trae las librerias" in d["error"]
    assert any(f.startswith("numpy") or f.startswith("xgboost") for f in d["entorno_faltan"])
    st, d = _post(base + "/mlops/package/build", dict(body, generar_sin_offline=True))
    assert st == 200 and d["ok"]
    assert [v["filename"] for v in d["variantes"]] == ["framework_mlops_v2_con_pyspark.zip",
                                                       "framework_mlops_v2_sin_pyspark.zip"]
    meta = next(r for r in d["report"] if r.get("_meta"))
    assert meta["entorno_faltan"]
    z = zipfile.ZipFile(io.BytesIO(_OPENER.open(base + d["variantes"][1]["download_url"]).read()))
    assert z.read("framework_mlops_v2_pkg/vendor/PYSPARK_MODE").decode().strip() == "servidor"
    assert "framework_mlops_v2_pkg/vendor/OFFLINE_FALTANTES.txt" in z.namelist()


def test_faltantes_entorno_formato():
    f = __import__("src.mlops_pkg", fromlist=["x"]).faltantes_entorno(
        {"py38-311": {"3.11": "sin wheel en el cache: numpy, pandas"}}, True, ["mex-libextract"])
    assert f == ["numpy (Python 3.11)", "pandas (Python 3.11)", "pyspark + py4j (PySpark incluido)",
                 "mex-libextract (libreria del banco)"]


# ------------------------------------------------------------------ Python 3.8 (host del portal)
_PORTAL = ["serve_ui.py", "main.py", "preparar_vendor.py", "importar_vendor.py", "exportar_vendor.py"]


def test_codigo_del_portal_parsea_con_sintaxis_python_38():
    fs = _PORTAL + [f for f in glob.glob(os.path.join(ROOT, "src", "**", "*.py"), recursive=True)
                    if "egg-info" not in f and not f.endswith("ese2gra1.py")]
    malos = []
    for f in fs:
        p = f if os.path.isabs(f) else os.path.join(ROOT, f)
        src = open(p, encoding="utf-8").read()
        try:
            tree = ast.parse(src, filename=p, feature_version=(3, 8))
        except SyntaxError as e:
            malos.append("%s: %s" % (os.path.relpath(p, ROOT), e))
            continue
        futuro = any(isinstance(n, ast.ImportFrom) and n.module == "__future__" and
                     any(a.name == "annotations" for a in n.names) for n in tree.body)
        for n in ast.walk(tree):
            if isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute) and \
                    n.func.attr in ("removeprefix", "removesuffix"):
                malos.append("%s:%d str.%s (3.9+)" % (os.path.relpath(p, ROOT), n.lineno, n.func.attr))
            if isinstance(n, ast.Call) and getattr(n.func, "id", None) == "zip" and \
                    any(k.arg == "strict" for k in n.keywords):
                malos.append("%s:%d zip(strict=) (3.10+)" % (os.path.relpath(p, ROOT), n.lineno))
            if not futuro and isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)):
                anns = [a.annotation for a in n.args.args + n.args.kwonlyargs if a.annotation] + \
                    ([n.returns] if n.returns else [])
                for a in anns:
                    for m in ast.walk(a):
                        if isinstance(m, ast.BinOp) and isinstance(m.op, ast.BitOr):
                            malos.append("%s:%d anotacion X | Y (3.10+)" % (os.path.relpath(p, ROOT), n.lineno))
                        if isinstance(m, ast.Subscript) and getattr(m.value, "id", None) in ("list", "dict", "tuple", "set"):
                            malos.append("%s:%d anotacion %s[...] (3.9+)" % (os.path.relpath(p, ROOT), n.lineno, m.value.id))
    assert not malos, "\n".join(sorted(set(malos))[:40])


def test_setup_sh_rhel8_python_exacto_y_pistas():
    from src import mlops_pkg as mp
    s = mp._SETUP_SH
    assert 'command -v "python$PY_T"' in s and "sudo dnf install python$PY_T" in s
    assert "java-17-openjdk-headless" in s and "sudo dnf install libgomp" in s
    i, j = s.index('if [ "$PY_T" != "$PY_V" ]'), s.index('"$PY" -m venv .venv')
    assert i < j and "exit 1" in s[i:j]          # version distinta = ERROR antes de crear el venv
