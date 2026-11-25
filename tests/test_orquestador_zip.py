# -*- coding: utf-8 -*-
"""Orquestador: exportar/importar un proyecto completo como ZIP (entre maquinas y SO). Todo en
directorios temporales; datos 100% sinteticos."""
import io
import json
import os
import stat
import sys
import threading
import types
import urllib.error
import urllib.request
import zipfile
from unittest import mock
import pytest
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
from src import orq_zip as oz  # noqa: E402
from src import orquestador as o  # noqa: E402


def _paso(sid, nombre, deps=(), **accion):
    return {"id": sid, "name": nombre, "action": {"status": "ok", **accion}, "depends_on": list(deps), "dep_flags": {},
            "solo_en_fallo": False, "enabled": True, "continue_on_error": False}


def _plan(nombre="demo", targets=None, **extra):
    t = targets or {}
    steps = [
        _paso("t1", "Job", graph_target=None, **{"type": "graph", "target": t.get("g", "output/orig/job_spark.py"),
                                                   "source": "x.pset", "status": "ok"}),
        _paso("t2", "Shell", ["t1"], **{"type": "shell", "comando": t.get("sh", "ksh output/orig/carga.sh --f x")}),
        _paso("t3", "Py", ["t2"], **{"type": "python", "target": t.get("py", "output/orig/util.py"),
                                       "args": [t.get("arg", "output/orig/carga.sql")]}),
        _paso("t4", "Sql", ["t3"], **{"type": "sql", "motor": "spark_sql", "sentencia": "SELECT 1"}),
    ]
    for s in steps:
        s["action"].pop("graph_target", None)
    p = {"plan": nombre + ".plan", "nombre": nombre, "origen": "plan", "proyecto": "orig", "direccion": "prior",
         "ejecucion": {**json.loads(json.dumps(o.EJECUCION_DEFECTO)), "base_path": "/srv/otra/maquina/datos"},
         "steps": steps, "enlaces": []}
    p.update(extra)
    return p


def _crear_proyecto(root, nombre="orig", plan=None):
    d = os.path.join(root, "output", nombre)
    os.makedirs(os.path.join(d, "sub"))
    p = plan or _plan()
    with open(os.path.join(d, "orquestacion_demo.json"), "w", encoding="utf-8") as f:
        json.dump(p, f)
    with open(os.path.join(d, "orquestacion_demo__pset.json"), "w", encoding="utf-8") as f:
        json.dump({**p, "nombre": "demo__pset"}, f)
    for n, c in (("job_spark.py", "print('hola')\n"), ("carga.sh", "echo ok\n"), ("util.py", "x = 1\n"),
                 ("carga.sql", "select 1;\n"), ("sub/params.env", "A=1\n"), ("dag_demo.py", "# viejo /mnt/x\n")):
        with open(os.path.join(d, n), "w", encoding="utf-8") as f:
            f.write(c)
    os.makedirs(os.path.join(d, "__pycache__"))
    with open(os.path.join(d, "__pycache__", "a.pyc"), "wb") as f:
        f.write(b"x")
    return d


def _zip(entradas, dst):
    with zipfile.ZipFile(dst, "w") as zf:
        for n, c in entradas:
            if isinstance(n, zipfile.ZipInfo):
                zf.writestr(n, c)
            else:
                zf.writestr(n, c)
    return dst


def _leer(root, proyecto, nombre="orquestacion_demo.json"):
    with open(os.path.join(root, "output", proyecto, nombre), encoding="utf-8") as f:
        return json.load(f)


def _pasos(plan):
    return {s["id"]: s["action"] for s in plan["steps"]}


def test_exportar_trae_todo_el_proyecto(tmp_path):
    d = _crear_proyecto(str(tmp_path))
    z = str(tmp_path / "e.zip")
    r = oz.exportar(d, "orig", z)
    nombres = set(zipfile.ZipFile(z).namelist())
    assert {"orig/orquestacion_demo.json", "orig/orquestacion_demo__pset.json", "orig/job_spark.py",
            "orig/carga.sh", "orig/carga.sql", "orig/dag_demo.py", "orig/sub/params.env",
            "orig/" + oz.MANIFIESTO} <= nombres
    assert not any("__pycache__" in n for n in nombres) and r["archivos"] == 8


def test_ida_y_vuelta_posix(tmp_path):
    src = tmp_path / "A"
    dst = tmp_path / "B"
    src.mkdir()
    dst.mkdir()
    d = _crear_proyecto(str(src))
    z = str(tmp_path / "e.zip")
    oz.exportar(d, "orig", z)
    r = oz.importar(z, str(dst))
    assert r["proyecto"] == "orig" and len(r["planes"]) == 2
    plan = _leer(str(dst), "orig")
    a = _pasos(plan)
    assert a["t1"]["target"] == "output/orig/job_spark.py"
    assert a["t2"]["comando"] == "ksh output/orig/carga.sh --f x"
    assert a["t3"]["args"] == ["output/orig/carga.sql"]
    for k in ("t1", "t3"):
        assert os.path.isfile(os.path.join(str(dst), a[k]["target"]))
    assert plan["ejecucion"]["base_path"] == ""      # ruta de datos del otro equipo
    assert any("base_path" in x for x in r["avisos"])
    # el DAG del origen se regenera con rutas de ESTE equipo
    assert "viejo" not in open(dst / "output" / "orig" / "dag_demo.py").read()
    # segunda importacion: proyecto nuevo, el anterior queda intacto
    antes = open(dst / "output" / "orig" / "orquestacion_demo.json").read()
    r2 = oz.importar(z, str(dst))
    r3 = oz.importar(z, str(dst))
    assert (r2["proyecto"], r3["proyecto"]) == ("orig_2", "orig_3")
    assert _pasos(_leer(str(dst), "orig_2"))["t1"]["target"] == "output/orig_2/job_spark.py"
    assert open(dst / "output" / "orig" / "orquestacion_demo.json").read() == antes
    assert _leer(str(dst), "orig_2")["proyecto"] == "orig_2"


def test_rutas_de_windows_y_linux_del_origen(tmp_path):
    win = _plan(targets={"g": "C:\\Users\\sinte\\bnx\\output\\orig\\job_spark.py",
                         "sh": 'ksh "C:\\Users\\sinte\\bnx\\output\\orig\\carga.sh" --f x',
                         "py": "output\\orig\\util.py", "arg": "D:\\x\\output\\orig\\carga.sql"})
    lin = _plan(targets={"g": "/home/usr/bnx/output/orig/job_spark.py",
                         "sh": "ksh /home/usr/bnx/output/orig/carga.sh", "py": "/opt/bnx/output/orig/util.py",
                         "arg": "/opt/bnx/output/orig/carga.sql"})
    for i, plan in enumerate((win, lin)):
        raiz = tmp_path / f"r{i}"
        raiz.mkdir()
        entradas = [("orig/orquestacion_demo.json", json.dumps(plan)), ("orig/job_spark.py", "a"),
                    ("orig/carga.sh", "b"), ("orig/util.py", "c"), ("orig/carga.sql", "d")]
        z = _zip(entradas, str(tmp_path / f"w{i}.zip"))
        oz.importar(z, str(raiz))
        a = _pasos(_leer(str(raiz), "orig"))
        assert a["t1"]["target"] == "output/orig/job_spark.py"
        assert a["t3"]["target"] == "output/orig/util.py" and a["t3"]["args"] == ["output/orig/carga.sql"]
        assert "output/orig/carga.sh" in a["t2"]["comando"] and ":" not in a["t2"]["comando"].replace("ksh", "")
        o.validar_plan(_leer(str(raiz), "orig"))


def test_zip_hecho_en_windows_con_barras_invertidas(tmp_path):
    entradas = [("orig\\orquestacion_demo.json", json.dumps(_plan())), ("orig\\job_spark.py", "a"),
                ("orig\\util.py", "c"), ("orig\\carga.sh", "d"), ("orig\\carga.sql", "e")]
    r = oz.importar(_zip(entradas, str(tmp_path / "w.zip")), str(tmp_path))
    assert r["proyecto"] == "orig" and os.path.isfile(tmp_path / "output" / "orig" / "job_spark.py")


def test_archivos_sueltos_json_mas_scripts(tmp_path):
    plan = _plan(targets={"g": "/otra/maq/job_spark.py", "sh": "ksh /otra/maq/carga.sh",
                          "py": "/otra/maq/util.py", "arg": "/otra/maq/carga.sql"})
    z = _zip([("mi_plan.json", json.dumps(plan)), ("job_spark.py", "a"), ("carga.sh", "b"),
              ("util.py", "c"), ("carga.sql", "d"), ("otro.json", '{"a": 1}')], str(tmp_path / "Mi Lote.zip"))
    r = oz.importar(z, str(tmp_path))
    assert r["proyecto"] == "Mi_Lote" and r["planes"] == ["output/Mi_Lote/orquestacion_mi_plan.json"]
    a = _pasos(_leer(str(tmp_path), "Mi_Lote", "orquestacion_mi_plan.json"))
    assert a["t1"]["target"] == "output/Mi_Lote/job_spark.py" and a["t2"]["comando"] == "ksh output/Mi_Lote/carga.sh"
    assert os.path.isfile(tmp_path / "output" / "Mi_Lote" / "otro.json")


def test_archivo_faltante_avisa(tmp_path):
    z = _zip([("orig/orquestacion_demo.json", json.dumps(_plan()))], str(tmp_path / "f.zip"))
    r = oz.importar(z, str(tmp_path))
    assert any("job_spark.py" in a for a in r["avisos"])


# ---- seguridad -------------------------------------------------------------
@pytest.mark.parametrize("nombre", ["../evil.py", "a/../../evil.py", "/etc/evil.py", "C:\\evil.py",
                                    "C:/evil.py", "a\\..\\..\\evil.py", "a/b:stream.py", "a/\x01b.py"])
def test_rechaza_rutas_peligrosas(tmp_path, nombre):
    z = _zip([("orig/ok.py", "x"), (nombre, "x")], str(tmp_path / "m.zip"))
    with pytest.raises(oz.ZipError):
        oz.importar(z, str(tmp_path))
    assert not os.path.exists(tmp_path.parent / "evil.py") and not (tmp_path / "evil.py").exists()
    salida = os.path.join(str(tmp_path), "output")
    assert not os.path.isdir(salida) or os.listdir(salida) == []     # sin proyecto ni temporales


def test_rechaza_symlink(tmp_path):
    zi = zipfile.ZipInfo("orig/enlace")
    zi.create_system = 3
    zi.external_attr = (stat.S_IFLNK | 0o777) << 16
    z = _zip([("orig/ok.py", "x"), (zi, "/etc/passwd")], str(tmp_path / "s.zip"))
    with pytest.raises(oz.ZipError, match="enlace simbolico"):
        oz.importar(z, str(tmp_path))


def test_rechaza_zip_bomb_por_razon(tmp_path):
    dst = str(tmp_path / "b.zip")
    with zipfile.ZipFile(dst, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("orig/ok.py", "x")
        zf.writestr("orig/ceros.bin", b"\0" * (50 * 1048576))
    with pytest.raises(oz.ZipError, match="zip bomb"):
        oz.importar(dst, str(tmp_path))


def test_rechaza_exceso_de_tamano_y_cantidad(tmp_path):
    z = _zip([("orig/a.py", "12345"), ("orig/b.py", "12345")], str(tmp_path / "t.zip"))
    with mock.patch.object(oz, "MAX_ARCHIVO", 4), pytest.raises(oz.ZipError, match="maximo"):
        oz.importar(z, str(tmp_path))
    with mock.patch.object(oz, "MAX_TOTAL", 8), pytest.raises(oz.ZipError, match="pesa mas"):
        oz.importar(z, str(tmp_path))
    with mock.patch.object(oz, "MAX_ARCHIVOS", 1), pytest.raises(oz.ZipError, match="entradas"):
        oz.importar(z, str(tmp_path))


def test_rechaza_cabecera_que_miente(tmp_path):
    dst = str(tmp_path / "l.zip")
    _zip([("orig/a.py", "x" * 100)], dst)
    raw = bytearray(open(dst, "rb").read())
    # la cabecera central dice 5 bytes; el contenido real son 100 (se cuenta lo real al extraer)
    for n in (b"PK\x03\x04", b"PK\x01\x02"):
        i = raw.index(n)
        off = 22 if n == b"PK\x03\x04" else 24
        raw[i + off:i + off + 4] = (5).to_bytes(4, "little")
    open(dst, "wb").write(raw)
    with mock.patch.object(oz, "MAX_ARCHIVO", 50), pytest.raises(Exception):
        oz.importar(dst, str(tmp_path))
    assert os.listdir(tmp_path / "output") == []


def test_rechaza_zip_invalido_y_planes_invalidos(tmp_path):
    (tmp_path / "x.zip").write_bytes(b"no soy un zip")
    with pytest.raises(oz.ZipError, match="no es un ZIP"):
        oz.importar(str(tmp_path / "x.zip"), str(tmp_path))
    malo = _plan()
    malo["steps"][1]["depends_on"] = ["zzz"]
    for n, c in (("orquestacion_a.json", json.dumps(malo)), ("orquestacion_b.json", "{no json"),
                 ("orquestacion_c.json", '{"x": 1}')):
        with pytest.raises(oz.ZipError, match=n):
            oz.importar(_zip([("p/" + n, c)], str(tmp_path / "p.zip")), str(tmp_path))
    assert os.listdir(tmp_path / "output") == []


def test_plan_con_accion_peligrosa_no_se_ejecuta_ni_se_acepta(tmp_path):
    p = _plan()
    p["steps"][3]["action"] = {"type": "bash", "comando": "rm -rf /"}
    z = _zip([("p/orquestacion_x.json", json.dumps(p))], str(tmp_path / "p.zip"))
    # tipo desconocido: no se ejecuta nada al importar; queda como dato inerte del plan
    with mock.patch("subprocess.Popen") as pp, mock.patch("subprocess.run") as pr:
        try:
            oz.importar(z, str(tmp_path))
        except oz.ZipError:
            pass
        assert not pp.called and not pr.called


def test_no_pisa_archivos_existentes(tmp_path):
    previo = tmp_path / "output" / "orig"
    previo.mkdir(parents=True)
    (previo / "mio.txt").write_text("mio")
    z = _zip([("orig/mio.txt", "ajeno"), ("orig/orquestacion_demo.json", json.dumps(_plan()))],
             str(tmp_path / "n.zip"))
    r = oz.importar(z, str(tmp_path))
    assert r["proyecto"] == "orig_2" and (previo / "mio.txt").read_text() == "mio"


# ---- HTTP -------------------------------------------------------------------
@pytest.fixture()
def srv(tmp_path):
    import socketserver
    import serve_ui

    class S(socketserver.ThreadingMixIn, socketserver.TCPServer):
        allow_reuse_address = True
        daemon_threads = True
    with mock.patch.object(serve_ui.BNXHandler, "_orq_raiz", lambda self: str(tmp_path)):
        httpd = S(("127.0.0.1", 0), serve_ui.BNXHandler)
        threading.Thread(target=httpd.serve_forever, daemon=True).start()
        yield {"base": f"http://127.0.0.1:{httpd.server_address[1]}", "raiz": str(tmp_path)}
        httpd.shutdown()
        httpd.server_close()


def _req(url, data=None, headers=None, method="POST"):
    r = urllib.request.Request(url, data=data, headers=headers or {}, method=method)
    try:
        with urllib.request.urlopen(r, timeout=30) as x:
            return x.status, x.read()
    except urllib.error.HTTPError as e:
        return e.code, e.read()


def test_http_exportar_importar_y_get(srv):
    _crear_proyecto(srv["raiz"])
    st, b = _req(srv["base"] + "/api/orquestador/proyecto_exportar", json.dumps({"project": "orig"}).encode(),
                 {"Content-Type": "application/json"})
    d = json.loads(b)
    assert st == 200 and d["ok"] and d["archivos"] == 8
    st, zbytes = _req(srv["base"] + d["download_url"], method="GET")
    assert st == 200 and zipfile.is_zipfile(io.BytesIO(zbytes))
    st, b = _req(srv["base"] + "/api/orquestador/proyecto_importar?name=otro.zip", zbytes,
                 {"Content-Type": "application/zip"})
    r = json.loads(b)
    assert st == 200 and r["proyecto"] == "orig_2"
    st, b = _req(srv["base"] + "/api/orquestador/get", json.dumps({"file": r["planes"][0]}).encode(),
                 {"Content-Type": "application/json"})
    g = json.loads(b)
    assert st == 200 and g["plan"]["steps"][0]["action"]["target"] == "output/orig_2/job_spark.py"
    assert os.path.isfile(os.path.join(srv["raiz"], g["plan"]["steps"][0]["action"]["target"]))
    st, b = _req(srv["base"] + "/api/orquestador/proyecto_importar", b"basura", {})
    assert st == 400 and "ZIP" in json.loads(b)["error"]
    st, b = _req(srv["base"] + "/api/orquestador/proyecto_exportar", json.dumps({"project": "../x"}).encode(), {})
    assert st == 400


def test_bloqueo_remoto_nombra_la_variable(monkeypatch):
    import serve_ui
    h = types.SimpleNamespace(client_address=("10.1.2.3", 5000), headers={})
    h._orq_local_only = lambda: serve_ui.BNXHandler._orq_local_only(h)
    monkeypatch.delenv("BNX_PERMITIR_EJECUCION_REMOTA", raising=False)
    for que in ("Exportar", "Importar"):
        msg = serve_ui.BNXHandler._orq_zip_bloqueo(h, que)
        assert "BNX_PERMITIR_EJECUCION_REMOTA=1" in msg and msg.startswith(que)
    monkeypatch.setenv("BNX_PERMITIR_EJECUCION_REMOTA", "1")
    assert serve_ui.BNXHandler._orq_zip_bloqueo(h, "Importar") is None
    h.client_address = ("127.0.0.1", 1)
    monkeypatch.delenv("BNX_PERMITIR_EJECUCION_REMOTA")
    assert serve_ui.BNXHandler._orq_zip_bloqueo(h, "Importar") is None
def test_http_rutas_exactas_de_la_ui_no_caen_en_validacion_de_plan(srv):
    """La UI llama a /orquestador/<accion> (ORQUESTADOR_URL sin /api) con JSON; no debe caer en la
    validacion por plan (orquestacion_*.json) que daba 'archivo invalido'."""
    _crear_proyecto(srv["raiz"])
    jsx = open(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                            "ui", "src", "components", "OrquestadorPage.jsx"), encoding="utf-8").read()
    assert "post('proyecto_exportar'" in jsx and "/proyecto_importar?" in jsx
    st, b = _req(srv["base"] + "/orquestador/proyecto_exportar", json.dumps({"project": "orig"}).encode(),
                 {"Content-Type": "application/json"})
    d = json.loads(b)
    assert st == 200 and d["ok"] and "archivo invalido" not in b.decode()
    st, zbytes = _req(srv["base"] + d["download_url"], method="GET")
    assert st == 200 and zipfile.is_zipfile(io.BytesIO(zbytes))
    st, b = _req(srv["base"] + "/orquestador/proyecto_importar?name=otro.zip&project=nuevo", zbytes,
                 {"Content-Type": "application/zip"})
    r = json.loads(b)
    assert st == 200 and r["proyecto"] == "nuevo" and "archivo invalido" not in b.decode()
    st, b = _req(srv["base"] + "/orquestador/proyecto_exportar", b"", {"Content-Type": "application/json"})
    assert st == 400 and "archivo invalido" not in b.decode()
