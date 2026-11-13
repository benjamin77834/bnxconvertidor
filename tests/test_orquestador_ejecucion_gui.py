"""Ejecucion real desde la GUI: base_path de Windows, escritor parquet sin pyarrow, handlers que
siempre responden JSON, validacion de rutas, omision de pasos nube/remotos, --paso/--desde y
cancelacion. Sin red / AWS / SSH (subprocess mockeado salvo la prueba de cancelar)."""
import builtins
import json
import os
import shutil
import sys
import threading
import time
import urllib.error
import urllib.request
from unittest import mock

import pytest

from src import orq_runner as rn
from src import orquestador as o

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------

def _step(sid, tipo="shell", deps=None, **action):
    a = {"type": tipo, **action}
    if tipo == "script":
        a.setdefault("status", "ok")
    return {"id": sid, "name": f"paso_{sid}", "action": a, "depends_on": deps or [], "dep_flags": {},
            "solo_en_fallo": False, "enabled": True, "continue_on_error": False}


def _plan(*steps):
    return {"plan": "t.manual", "nombre": "t", "origen": "manual", "direccion": "prior",
            "ejecucion": {"modo": "python", "spark_args": [], "base_path": "", "env": {}},
            "steps": list(steps), "enlaces": []}


def _plan_mixto():
    return _plan(
        _step("t1", "shell", comando="echo hola"),
        _step("t2", "s3_copy", ["t1"], origen="/tmp/x", destino="s3://bkt/x"),
        _step("t3", "ssh", ["t1"], host="srv.local", comando="ls"),
        _step("t4", "http", ["t1"], url="https://example.com/hook"))


# ---------------------------------------------------------------------------
# base_path de Windows (ntpath: se prueba igual en Mac)
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("entrada,esperado", [
    ("C:\\Users\\KP29465\\", "C:/Users/KP29465"),          # el caso del reporte
    ("C:/Users/KP29465/", "C:/Users/KP29465"),
    ("C:\\Users\\KP29465", "C:/Users/KP29465"),
    ('  "C:\\Users\\KP 29465\\bnx\\"  ', "C:/Users/KP 29465/bnx"),
    ("c:\\Users\\a\\..\\b\\", "c:/Users/b"),
    ("\\\\srv\\share\\bnx\\", "//srv/share/bnx"),
    ("C:\\", "C:/"),
    ("s3://bucket/pref/", "s3://bucket/pref"),
    ("", ""),
])
def test_normalizar_base_path_windows(entrada, esperado):
    assert o.normalizar_base_path(entrada) == esperado


def test_normalizar_posix_y_efectiva():
    assert o.normalizar_base_path("/tmp/bnx/") == "/tmp/bnx"
    assert o._base_efectiva({"base_path": "C:\\Users\\KP29465\\"}) == "C:/Users/KP29465"


def test_validar_base_path_windows_simulado():
    ok, err = o.validar_base_path("C:\\Users\\KP29465\\", crear=False, windows=True)
    assert (ok, err) == ("C:/Users/KP29465", None)
    assert o.validar_base_path("C:/Users/KP29465/", crear=False, windows=True)[1] is None
    # ruta Windows en un servidor que no es Windows -> mensaje claro, no excepcion
    assert "Windows" in o.validar_base_path("C:\\Users\\x\\", crear=False, windows=False)[1]
    assert "absoluta" in o.validar_base_path("datos\\rel", crear=False, windows=True)[1]
    assert "raiz" in o.validar_base_path("C:\\", crear=False, windows=True)[1]
    assert o.validar_base_path("", crear=False)[1]
    assert o.validar_base_path("s3://bkt/x/", crear=False)[1] is None
    assert o.validar_base_path("s3://", crear=False)[1]


@pytest.mark.skipif(os.name == "nt", reason="rutas POSIX")
def test_validar_base_path_posix(tmp_path):
    assert o.validar_base_path("relativa/x", crear=False)[1]
    assert o.validar_base_path("/", crear=False)[1]
    nuevo = tmp_path / "a" / "b"
    ruta, err = o.validar_base_path(str(nuevo) + "/", crear=True)
    assert err is None and ruta == str(nuevo) and nuevo.is_dir()


def test_job_env_exporta_base_sin_barra_final_y_python_de_spark():
    env = o._job_env({"base_path": "C:\\Users\\KP29465\\", "env": {"X": "1"}})
    assert env["BNX_BASE_PATH"] == "C:/Users/KP29465" and env["X"] == "1"
    assert env["PYSPARK_PYTHON"] and env["PYSPARK_DRIVER_PYTHON"]
    assert env["PYTHONUTF8"] == "1"


# ---------------------------------------------------------------------------
# escritor parquet: nunca PySpark en el proceso del servidor
# ---------------------------------------------------------------------------

def _sin_motores_parquet():
    real = builtins.__import__

    def fake(name, *a, **k):
        if name.split(".")[0] in ("pyarrow", "fastparquet", "pyspark"):
            raise ImportError(f"No module named '{name}' (simulado)")
        return real(name, *a, **k)
    return mock.patch("builtins.__import__", side_effect=fake)


def test_escribir_parquet_sin_pyarrow_usa_python_puro(tmp_path):
    filas = [{"a": i, "b": i * 1.5 if i % 3 else None, "c": f"x{i} ñ"} for i in range(10)]
    with _sin_motores_parquet():
        motor = o.escribir_parquet(str(tmp_path / "d"), ["a", "b", "c"], filas)
    assert motor == "python-puro"
    assert (tmp_path / "d" / "part-00000.parquet").read_bytes()[:4] == b"PAR1"


def test_parquet_puro_lo_lee_pyarrow(tmp_path):
    pq = pytest.importorskip("pyarrow.parquet")
    from src import parquet_puro
    filas = [{"a": i, "b": None if i % 2 else i / 2, "c": f"v{i}", "d": i % 2 == 0} for i in range(25)]
    parquet_puro.escribir(str(tmp_path / "t.parquet"), ["a", "b", "c", "d"], filas)
    t = pq.read_table(str(tmp_path / "t.parquet")).to_pylist()
    assert t == filas


def test_generar_datos_error_de_un_dataset_no_levanta(tmp_path):
    """Un fallo del motor se reporta en el informe (estado error), no corta la peticion."""
    ab = tmp_path / "job_spark.py"
    ab.write_text('PARAMS = None\nclientes_df = spark.read.parquet(f"{PARAMS.BASE_PATH}/raw/clientes.dat")\n'
                  'x = clientes_df.where("edad > 3")\n', encoding="utf-8")
    plan = _plan(_step("t1", "graph", target=str(ab), status="ok", source="x.mp"))
    plan["origen"] = "plan"
    with mock.patch.object(o, "escribir_parquet", side_effect=OSError("disco lleno")):
        rep = o.generar_datos(plan, str(tmp_path / "base"), n_rows=3)
    assert rep and rep[0]["estado"] == "error" and "disco lleno" in rep[0]["motivo"]


# ---------------------------------------------------------------------------
# pasos nube/remotos, --paso / --desde, scripts sin shell, eventos
# ---------------------------------------------------------------------------

def test_pasos_remotos_y_nube_se_omiten_sin_permiso(tmp_path, capsys):
    with mock.patch.object(o.subprocess, "run", return_value=mock.Mock(returncode=0)) as run:
        ok = o.ejecutar(_plan_mixto(), real=True, base_path=str(tmp_path), permitir_remotos=False)
    assert ok
    llamados = [c.args[0][0] for c in run.call_args_list]
    assert llamados == ["echo"]                      # solo el paso local
    out = capsys.readouterr().out
    assert out.count("sin permiso") == 3 and "Pasos omitidos" in out


def test_pasos_remotos_corren_con_permiso(tmp_path):
    with mock.patch.object(o.subprocess, "run", return_value=mock.Mock(returncode=0)) as run:
        assert o.ejecutar(_plan_mixto(), real=True, base_path=str(tmp_path), permitir_remotos=True)
    assert [c.args[0][0] for c in run.call_args_list] == ["echo", "aws", "ssh", "curl"]


def test_dry_run_no_omite_nube(capsys):
    assert o.ejecutar(_plan_mixto(), real=False, permitir_remotos=False)
    assert "sin permiso" not in capsys.readouterr().out


def _cadena():
    return _plan(_step("t1", comando="echo 1"), _step("t2", deps=["t1"], comando="echo 2"),
                 _step("t3", deps=["t2"], comando="echo 3"), _step("t4", comando="echo 4"))


def test_seleccion_paso_y_desde():
    p = _cadena()
    assert o.seleccion_pasos(p) is None
    assert o.seleccion_pasos(p, solo="t2") == {"t2"}
    assert o.seleccion_pasos(p, desde="t2") == {"t2", "t3"}
    with pytest.raises(ValueError):
        o.seleccion_pasos(p, solo="zz")


def test_ejecutar_solo_y_desde_real(tmp_path):
    p = _cadena()
    with mock.patch.object(o.subprocess, "run", return_value=mock.Mock(returncode=0)) as run:
        assert o.ejecutar(p, real=True, base_path=str(tmp_path), solo="t2")
    assert [c.args[0] for c in run.call_args_list] == [["echo", "2"]]
    with mock.patch.object(o.subprocess, "run", return_value=mock.Mock(returncode=0)) as run:
        assert o.ejecutar(p, real=True, base_path=str(tmp_path), desde="t2")
    assert [c.args[0] for c in run.call_args_list] == [["echo", "2"], ["echo", "3"]]
    assert o.ejecutar(p, real=False, solo="zz") is False


def test_cli_paso_y_desde(tmp_path, capsys):
    f = tmp_path / "orquestacion_c.json"
    f.write_text(json.dumps(_cadena()), encoding="utf-8")
    assert o.main(["ejecutar", str(f), "--paso", "t3"]) == 0
    out = capsys.readouterr().out
    assert "[>] t3" in out and "[>] t1" not in out and "fuera de la seleccion" in out
    assert o.main(["ejecutar", str(f), "--desde", "t2"]) == 0
    out = capsys.readouterr().out
    assert "[>] t2" in out and "[>] t3" in out and "[>] t1" not in out
    with pytest.raises(SystemExit):
        o.main(["ejecutar", str(f), "--paso", "t1", "--desde", "t2"])


def test_cli_sin_remotos_y_spark_args_json(tmp_path):
    f = tmp_path / "orquestacion_c.json"
    f.write_text(json.dumps(_plan_mixto()), encoding="utf-8")
    with mock.patch.object(o.subprocess, "run", return_value=mock.Mock(returncode=0)) as run:
        rc = o.main(["ejecutar", str(f), "--ejecutar", "--base-path", str(tmp_path) + os.sep, "--sin-remotos",
                     "--spark-args-json", '["--master", "local[2]"]'])
    assert rc == 0 and len(run.call_args_list) == 1
    with pytest.raises(SystemExit):
        o.main(["ejecutar", str(f), "--spark-args-json", '{"no": "lista"}'])


def test_script_ksh_sin_shell_se_omite(tmp_path, capsys):
    p = _plan(_step("t1", "script", target="abinitio/x/prepara.ksh"), _step("t2", deps=["t1"], comando="echo ok"))
    with mock.patch.object(o.shutil, "which", return_value=None), \
            mock.patch.object(o.subprocess, "run", return_value=mock.Mock(returncode=0)) as run:
        ok = o.ejecutar(p, real=True, base_path=str(tmp_path))
    assert ok                                         # no falla todo el plan
    assert [c.args[0][0] for c in run.call_args_list] == ["echo"]
    assert "no hay ksh ni bash" in capsys.readouterr().out


def test_eventos_de_estado_para_la_gui(tmp_path, capsys, monkeypatch):
    monkeypatch.setenv("BNX_EVENTOS", "1")
    with mock.patch.object(o.subprocess, "run", return_value=mock.Mock(returncode=0)):
        o.ejecutar(_plan_mixto(), real=True, base_path=str(tmp_path), permitir_remotos=False)
    ev = [json.loads(ln[6:]) for ln in capsys.readouterr().out.splitlines() if ln.startswith("##BNX ")]
    assert {"ruta": "t1", "estado": "corriendo"} in ev and {"ruta": "t1", "estado": "ok"} in ev
    assert {"ruta": "t2", "estado": "omitido"} in ev


def test_falla_lanzar_proceso_no_revienta(tmp_path, capsys):
    p = _plan(_step("t1", "script", target="x.ksh"))
    with mock.patch.object(o.shutil, "which", return_value="/bin/ksh"), \
            mock.patch.object(o.subprocess, "run", side_effect=FileNotFoundError("ksh")):
        assert o.ejecutar(p, real=True, base_path=str(tmp_path)) is False
    assert "no se pudo lanzar" in capsys.readouterr().out


# ---------------------------------------------------------------------------
# validacion de la solicitud de ejecucion (runner)
# ---------------------------------------------------------------------------

def test_validar_solicitud(tmp_path):
    p = _cadena()
    base = str(tmp_path)
    v = rn.validar_solicitud(p, {"base_path": base + os.sep, "modo": "spark-submit",
                                 "spark_args": ["--master", "local[*]"], "paso": "t2"})
    assert v["base_path"] == base and v["paso"] == "t2" and v["permitir_remotos"] is False
    for malo in ({"base_path": base, "modo": "x"}, {"base_path": base, "paso": "zz"},
                 {"base_path": base, "paso": "t1", "desde_paso": "t2"},
                 {"base_path": base, "spark_args": ["a\nb"]}, {"base_path": base, "spark_args": 5},
                 {"base_path": ""}, {"base_path": "relativa"},
                 {"base_path": "s3://bkt/x"}):                       # s3 exige permitir_remotos
        with pytest.raises(rn.RunError):
            rn.validar_solicitud(p, malo)
    assert rn.validar_solicitud(p, {"base_path": "s3://bkt/x/", "permitir_remotos": True})["base_path"] == "s3://bkt/x"


def test_preflight_reporta_java_pyspark_y_entradas(tmp_path):
    p = _plan(_step("t1", "graph", target="x_spark.py", status="ok", source="x.mp"))
    p["origen"] = "plan"
    par = rn.validar_solicitud(p, {"base_path": str(tmp_path)})
    with mock.patch.object(rn, "_java", return_value=(None, "no se encontro java")), \
            mock.patch("importlib.util.find_spec", return_value=None):
        ch = {c["id"]: c for c in rn.preflight(p, par)}
    assert ch["pyspark"]["nivel"] == "error" and "pip install pyspark" in ch["pyspark"]["ayuda"]
    assert ch["java"]["nivel"] == "error" and "JAVA_HOME" in ch["java"]["ayuda"]


def test_preflight_winutils_en_windows(tmp_path):
    p = _plan(_step("t1", "graph", target="x_spark.py", status="ok", source="x.mp"))
    p["origen"] = "plan"
    par = rn.validar_solicitud(p, {"base_path": str(tmp_path)})
    with mock.patch.object(rn.os, "name", "nt"), mock.patch.dict(os.environ, {}, clear=False), \
            mock.patch.object(rn, "_java", return_value=("java", "openjdk 17")):
        os.environ.pop("HADOOP_HOME", None)
        ch = {c["id"]: c for c in rn.preflight(p, par)}
    assert ch["winutils"]["nivel"] == "warn" and "HADOOP_HOME" in ch["winutils"]["ayuda"]


@pytest.mark.skipif(os.name == "nt", reason="usa sleep POSIX")
def test_ejecutar_en_segundo_plano_409_y_cancelar(tmp_path):
    plan_f = tmp_path / "orquestacion_lento.json"
    plan_f.write_text(json.dumps(_plan(_step("t1", comando="sleep 30"), _step("t2", deps=["t1"], comando="echo fin"))),
                      encoding="utf-8")
    p = rn.validar_solicitud(_plan(_step("t1", comando="x")), {"base_path": str(tmp_path / "b")}, crear_base=True)
    run = rn.iniciar(str(plan_f), p)
    try:
        t0 = time.time()
        while time.time() - t0 < 15 and rn.estado(run.id)["pasos"].get("t1") != "corriendo":
            time.sleep(0.3)                      # esperar a que arranque el paso (python tarda en iniciar)
        assert rn.estado(run.id)["estado"] == "corriendo"
        with pytest.raises(rn.RunError) as e:
            rn.iniciar(str(plan_f), p)
        assert e.value.status == 409
        assert rn.cancelar(run.id)["estado"] == "cancelado"
        d = rn.estado(run.id)
        assert d["estado"] == "cancelado" and d["pasos"].get("t1") == "cancelado"
        assert "CANCELADA" in d["log"] or "CANCELADA" in rn.estado(run.id, 0)["log"]
        # ya no queda el sleep huerfano
        import subprocess
        assert subprocess.run(["pgrep", "-f", "sleep 30"], capture_output=True).stdout.strip() == b""
    finally:
        if run.corriendo():
            rn._matar_arbol(run.proc)
        rn.RUNS.pop(run.id, None)


def test_estado_run_invalido():
    for rid in ("../../etc/passwd", "", "20260101-000000-zzzzzz", "20260101-000000-abcdef"):
        with pytest.raises(rn.RunError) as e:
            rn.estado(rid)
        assert e.value.status == 404


# ---------------------------------------------------------------------------
# handlers HTTP: siempre JSON (nunca conexion cortada), rutas, localhost
# ---------------------------------------------------------------------------

@pytest.fixture(scope="module")
def srv():
    import socketserver
    import serve_ui

    class S(socketserver.ThreadingMixIn, socketserver.TCPServer):
        allow_reuse_address = True
        daemon_threads = True

    httpd = S(("127.0.0.1", 0), serve_ui.BNXHandler)
    th = threading.Thread(target=httpd.serve_forever, daemon=True)
    th.start()
    proy = os.path.join(ROOT, "output", "pytest_gui_tmp")
    shutil.rmtree(proy, ignore_errors=True)
    f = o.nueva("gui", "pytest_gui_tmp", base=os.path.join(ROOT, "output"))
    plan = json.load(open(f, encoding="utf-8"))
    o.agregar_paso(plan, "shell", "x", None, comando="echo hi")
    o._write(f, plan)
    yield {"url": f"http://127.0.0.1:{httpd.server_address[1]}/orquestador",
           "plan": os.path.relpath(f, ROOT)}
    httpd.shutdown()
    httpd.server_close()
    shutil.rmtree(proy, ignore_errors=True)


def _post(srv, action, body, headers=None):
    req = urllib.request.Request(f"{srv['url']}/{action}", data=json.dumps(body).encode(),
                                 headers={"Content-Type": "application/json", **(headers or {})}, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            return r.status, json.loads(r.read())
    except urllib.error.HTTPError as e:
        return e.code, json.loads(e.read())


def test_handler_datos_excepcion_responde_json(srv):
    with mock.patch.object(o, "generar_datos", side_effect=OSError("boom: disco")):
        st, d = _post(srv, "datos", {"file": srv["plan"]})
    assert st == 500 and d["ok"] is False and "boom: disco" in d["error"] and "traceback" in d


def test_handler_datos_sin_motor_py4j_responde_json(srv):
    class Py4JError(Exception):
        pass
    with mock.patch.object(o, "generar_datos", side_effect=Py4JError("Java gateway process exited")):
        st, d = _post(srv, "datos", {"file": srv["plan"]})
    assert st == 500 and "Java gateway" in d["error"]


def test_handler_datos_base_windows_en_mac_es_400_json(srv):
    if os.name == "nt":
        pytest.skip("en Windows la ruta es valida")
    st, d = _post(srv, "datos", {"file": srv["plan"], "base_path": "C:\\Users\\KP29465\\"})
    assert st == 400 and d["ok"] is False and "Windows" in d["error"]


def test_handler_ejecutar_valida_rutas_y_confirmacion(srv, tmp_path):
    base = str(tmp_path)
    cuerpo = {"base_path": base, "confirmado": True}
    for malo in ("output/../serve_ui.py", "/etc/passwd", "../outside.json", "serve_ui.py",
                 "output/pytest_gui_tmp/../../serve_ui.py", ""):
        st, d = _post(srv, "ejecutar", {**cuerpo, "plan_json": malo})
        assert st == 400 and d["ok"] is False, malo
    st, d = _post(srv, "ejecutar", {"plan_json": srv["plan"], "base_path": base})      # sin confirmar
    assert st == 400 and "confirmacion" in d["error"]
    st, d = _post(srv, "ejecutar", {"plan_json": srv["plan"], "confirmado": True})      # sin base
    assert st == 400 and "base_path" in d["error"]
    st, d = _post(srv, "ejecutar", {"plan_json": srv["plan"], "base_path": "rel/x", "confirmado": True})
    assert st == 400 and "absoluta" in d["error"]


def test_handler_ejecutar_rechaza_origen_ajeno(srv, tmp_path):
    st, d = _post(srv, "ejecutar", {"plan_json": srv["plan"], "base_path": str(tmp_path), "confirmado": True},
                  headers={"Origin": "http://evil.example.com"})
    assert st == 403 and d["ok"] is False
    st, d = _post(srv, "cancelar", {"run": "x"}, headers={"Origin": "http://evil.example.com"})
    assert st == 403


def test_handler_preflight_y_ejecutar_end_to_end(srv, tmp_path):
    base = str(tmp_path / "b")
    st, d = _post(srv, "preflight", {"plan_json": srv["plan"], "base_path": base})
    assert st == 200 and d["params"]["base_path"] == base and "DRY-RUN" in d["dry_run"]
    st, d = _post(srv, "ejecutar", {"plan_json": srv["plan"], "base_path": base, "confirmado": True, "real": True})
    assert st == 200, d
    rid, off, log = d["run"], 0, ""
    t0 = time.time()
    while time.time() - t0 < 60:
        st, e = _post(srv, "estado", {"run": rid, "offset": off})
        log += e["log"]
        off = e["offset"]
        if e["estado"] != "corriendo" and "salidas" in e:
            break
        time.sleep(0.5)
    assert e["estado"] == "ok" and e["rc"] == 0 and e["pasos"] == {"t1": "ok"}
    assert "hi" in log and "##BNX" not in log
    rn.RUNS.pop(rid, None)
