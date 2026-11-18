"""Simulacion de jobs desde la UI (src/mlops_simular.py + endpoints de serve_ui.py) y nombres por ruta.
Sin red y sin Spark real: el paquete es un ZIP falso (router.py + main.py que imita al runner + setup.sh que
deja un .venv/bin/python de mentira). Se prueba orden pivote-primero, reutilizacion por hash, 409,
cancelar (mata el arbol), solo localhost, Windows y el payload que manda la UI (nombres con ruta)."""
import ast
import json
import os
import sys
import time
import types
import zipfile

import pytest

from src import mlops_pkg as mp
from src import mlops_simular as sim

posix = pytest.mark.skipif(os.name == "nt", reason="la simulacion es solo Mac/Linux")

# ---------------------------------------------------------------------------
# Payload de la UI: nombres por ruta (webkitRelativePath) y main.py como apoyo
# ---------------------------------------------------------------------------
JOB = "from toolbox.kernel import Kernel\n\ndef run(kernel: Kernel) -> None:\n    pass\n"
MAIN_BANCO = "from toolbox.kernel import Kernel\n\nclass Launcher:\n    def __init__(self):\n        self.kernel = Kernel('x', 'y', 'z')\n"
KERNEL_PY = "class Kernel:\n    pass\n"
P = "170589.DAA.MLOps_RPS_2026-0001-refactor_v1/"
RUTAS_JOBS = ["liabilities/pivot", "liabilities/datapull", "rps/pivot", "rps/target", "rps/score",
              "rps/datapull", "ccp/pivot", "ccp/datapull"]
NOMBRES = ["liabilities_pivot", "liabilities_datapull", "rps_pivot", "rps_target", "rps_score",
           "rps_datapull", "ccp_pivot", "ccp_datapull"]


def _convert(code):
    return {"ok": True, "code": "df_out = df", "warnings": [], "unsupported": []}


def _ui_sources(prefijo=P):
    s = [{"name": prefijo + "main.py", "code": MAIN_BANCO},
         {"name": prefijo + "bin/toolbox/kernel.py", "code": KERNEL_PY}]
    s += [{"name": prefijo + "bin/jobs/%s/job.py" % r, "code": JOB} for r in RUTAS_JOBS]
    return s


def _ui_registry(sources):
    """Lo que calcula MLOpsPackagePage.jsx: jobs = esJob (def run) -> 'name' tal cual se subio."""
    jobs = [s["name"] for s in sources if "def run(" in s["code"]]
    return None if len(jobs) == len(sources) else jobs


def _build(tmp_path, sources, registry="ui"):
    out = tmp_path / "ui.zip"
    reg = _ui_registry(sources) if registry == "ui" else registry
    _, _, report = mp.build_package_from_sources(
        sources, convert_fn=_convert, include_bank_libs=False, out_path=str(out),
        py_target="py3.11", registry=reg)
    names = zipfile.ZipFile(out).namelist()
    return [r for r in report if not r.get("_meta")], names


def test_payload_ui_carpeta_nombres_por_ruta_y_main_como_apoyo(tmp_path):
    src = _ui_sources()
    rep, names = _build(tmp_path, src)
    jobs = [r["source"] for r in rep if r.get("role") == "job"]
    assert jobs == NOMBRES
    main = next(r for r in rep if r["name"].endswith("/main.py"))
    assert main["role"] == "apoyo" and main["file"] == "bank_src/main.py" and main["source"] is None
    assert any(n.endswith("framework_mlops_v2_pkg/bank_src/main.py") for n in names)
    assert not any("/aggregates/job" in n or "/aggregates/main.py" in n for n in names)
    assert any(n.endswith("bank_src/jobs/rps/target/job.py") for n in names)


def test_payload_ui_registry_con_mismas_rutas_no_cambia_nada(tmp_path):
    src = _ui_sources()
    rep, _ = _build(tmp_path, src, registry=[s["name"] for s in src if "def run(" in s["code"]])
    assert [r["source"] for r in rep if r.get("role") == "job"] == NOMBRES


def test_payload_archivos_con_campo_path(tmp_path):
    """Otro cliente manda 'name' = job.py y la ruta en 'path' / 'webkitRelativePath': se usa la ruta."""
    src = _ui_sources()
    sueltas = []
    for i, s in enumerate(src):
        campo = ("path", "webkitRelativePath", "relative_path")[i % 3]
        sueltas.append({"name": os.path.basename(s["name"]), campo: s["name"], "code": s["code"]})
    rep, _ = _build(tmp_path, sueltas, registry=None)
    assert [r["source"] for r in rep if r.get("role") == "job"] == NOMBRES
    assert next(r for r in rep if r["name"].endswith("main.py"))["role"] == "apoyo"


def test_payload_ruta_con_backslash_windows(tmp_path):
    src = _ui_sources()
    for s in src:
        s["name"] = s["name"].replace("/", "\\")
    rep, _ = _build(tmp_path, src, registry=None)
    assert [r["source"] for r in rep if r.get("role") == "job"] == NOMBRES


def test_archivos_sueltos_sin_ruta_avisan(tmp_path):
    """Sin ruta no se puede nombrar por ruta (queda job, job_2...) pero se avisa que suba la carpeta."""
    src = [{"name": "main.py", "code": MAIN_BANCO}, {"name": "kernel.py", "code": KERNEL_PY},
           {"name": "job.py", "code": JOB}]
    rep, _ = _build(tmp_path, src)
    j = next(r for r in rep if r.get("role") == "job")
    assert j["source"] == "job" and "SIN ruta" in j["aviso"]
    assert next(r for r in rep if r["name"] == "main.py")["role"] == "apoyo"


# ---------------------------------------------------------------------------
# Paquete falso para la simulacion
# ---------------------------------------------------------------------------
ROUTER = '''_FUENTES = {
    "rps_target": ("jobs.rps.target.job", "run", "kernel", "rps/target"),
    "ccp_datapull": ("jobs.ccp.datapull.job", "run", "kernel", "ccp/datapull"),
    "rps_pivot": ("jobs.rps.pivot.job", "run", "kernel", "rps/pivot"),
    "ccp_pivot": ("jobs.ccp.pivot.job", "run", "kernel", "ccp/pivot"),
    "rps_score": ("jobs.rps.score.job", "run", "kernel", "rps/score"),
}
'''
MAIN_FALSO = r'''
import json, os, subprocess, sys, time
args = sys.argv[1:]
src = args[args.index("--source") + 1] if "--source" in args else None
pkg = os.path.dirname(os.path.abspath(__file__))
with open(os.path.join(pkg, "calls.log"), "a") as f:
    f.write(" ".join(args) + "\n")
nombres = [src] if src else ["rps_pivot", "ccp_pivot", "rps_target", "ccp_datapull", "rps_score"]
mode = os.environ.get("BNX_FAKE_MODE", "")
out = os.path.join(pkg, "demo_out")
os.makedirs(out, exist_ok=True)
rep = {"jobs": []}
for i, n in enumerate(nombres):
    print("[kernel] INICIO %s (%d/%d)" % (n, i + 1, len(nombres)), flush=True)
    if mode == "hang":
        p = subprocess.Popen([sys.executable, "-c", "import time; time.sleep(120)"])
        with open(os.path.join(pkg, "child.pid"), "w") as f:
            f.write(str(p.pid))
        time.sleep(120)
    if mode == "sleep":
        time.sleep(4)
    if mode == "falla" and n == "rps_pivot":
        print("[kernel] FIN ERROR %s en 0.1 s: KeyError: 'x'" % n, flush=True)
        sys.exit(1)
    print("[kernel] FIN OK %s en 0.1 s" % n, flush=True)
    rep["jobs"].append({"job": n, "escrituras": [{"tipo": "tabla", "destino": "db.t_" + n, "local": "x", "filas": 3}]})
with open(os.path.join(out, "REPORTE_DEMO.json"), "w") as f:
    json.dump(rep, f)
'''
SETUP_FALSO = '''#!/usr/bin/env bash
echo x >> "$BNX_FAKE_COUNT"
mkdir -p .venv/bin
printf '#!/usr/bin/env bash\\nexec "%s" "$@"\\n' "$BNX_FAKE_PY" > .venv/bin/python
chmod +x .venv/bin/python
'''


def _zip_falso(destino, extra=""):
    with zipfile.ZipFile(destino, "w") as z:
        r = "framework_mlops_v2_pkg/"
        z.writestr(r + "framework_mlops_v2/aggregates/router.py", ROUTER)
        z.writestr(r + "main.py", MAIN_FALSO)
        zi = zipfile.ZipInfo(r + "setup.sh")
        zi.external_attr = 0o755 << 16
        z.writestr(zi, SETUP_FALSO)
        z.writestr(r + "extra.txt", extra)
    return str(destino)


@pytest.fixture
def entorno(tmp_path, monkeypatch):
    pytest.importorskip("pyspark")        # el chequeo del venv hace 'import pyspark'
    monkeypatch.setenv("BNX_SIMULAR_DIR", str(tmp_path / "sim"))
    monkeypatch.setenv("BNX_FAKE_COUNT", str(tmp_path / "setup_count"))
    monkeypatch.setenv("BNX_FAKE_PY", sys.executable)
    monkeypatch.setattr(sim, "entorno_soportado", lambda: (True, "java falso"))
    sim._ACTIVO.clear()
    zp = _zip_falso(tmp_path / "paquete.zip")
    yield types.SimpleNamespace(zip=zp, tmp=tmp_path, count=tmp_path / "setup_count")
    for r in list(sim._RUNS.values()):
        r.cancelar_flag = True
        if r.proc is not None:
            sim.matar_arbol(r.proc)
    sim._RUNS.clear()
    sim._ACTIVO.clear()


def _esperar(rid, seg=40):
    fin = time.time() + seg
    while time.time() < fin:
        d = sim.estado(rid)
        if d["terminado"]:
            return d
        time.sleep(0.1)
    raise AssertionError("la simulacion no termino: " + sim.estado(rid)["log"][-500:])


def _calls(env):
    _, pkg = sim.montar(env.zip)
    with open(os.path.join(pkg, "calls.log")) as fh:
        return [l.split() for l in fh.read().splitlines()]


def _inicio(env, job, **kw):
    return _esperar(sim.iniciar("t", env.zip, job, **kw))


# ---------------------------------------------------------------------------
# Orden: el pivote SIEMPRE primero
# ---------------------------------------------------------------------------
def _jobs():
    return [{"name": n, "kind": "kernel", "model": n.split("_")[0], "job": n.split("_")[1],
             "ruta": "%s/%s" % tuple(n.split("_"))} for n in
            ["rps_target", "ccp_datapull", "rps_pivot", "ccp_pivot", "rps_score", "liabilities_pivot"]]


def test_orden_todos_pivotes_primero_y_resto_estable():
    assert sim.orden_todos(_jobs()) == ["rps_pivot", "ccp_pivot", "liabilities_pivot",
                                        "rps_target", "ccp_datapull", "rps_score"]


def test_orden_todos_respeta_depends_on_y_pivot_true():
    orden = {"rps_score": {"depends_on": ["rps_target"]}, "rps_target": {"depends_on": ["ccp_datapull"]},
             "ccp_datapull": {"pivot": True}}
    r = sim.orden_todos(_jobs(), orden)
    assert r.index("ccp_datapull") < r.index("rps_target") < r.index("rps_score")
    assert r[0] in ("rps_pivot", "ccp_pivot", "liabilities_pivot", "ccp_datapull")
    assert all(r.index(p) < r.index("rps_target") for p in ("rps_pivot", "ccp_pivot", "ccp_datapull"))


def test_orden_ciclo_es_error():
    with pytest.raises(sim.SimError):
        sim.orden_todos(_jobs(), {"rps_score": {"depends_on": ["rps_target"]},
                                  "rps_target": {"depends_on": ["rps_score"]}})


def test_es_pivote_por_nombre_ruta_o_orden_json():
    assert sim.es_pivote({"name": "rps_pivot"}) and sim.es_pivote({"name": "pivote"})
    assert sim.es_pivote({"name": "x", "ruta": "a/pivot", "job": "pivot"})
    assert sim.es_pivote({"name": "base"}, {"base": {"pivot": True}})
    assert not sim.es_pivote({"name": "rps_target", "ruta": "rps/target", "job": "target"})


def test_pasos_job_no_pivote_lleva_su_pivote_si_no_esta_hecho():
    j = _jobs()
    assert sim.pasos_job("rps_target", j) == ["rps_pivot", "rps_target"]
    assert sim.pasos_job("rps_target", j, hechos={"rps_pivot"}) == ["rps_target"]
    assert sim.pasos_job("rps_pivot", j) == ["rps_pivot"]
    assert sim.pasos_job("ccp_datapull", j) == ["ccp_pivot", "ccp_datapull"]     # el de SU modelo
    with pytest.raises(sim.SimError) as e:
        sim.pasos_job("nada", j)
    assert e.value.status == 404


@posix
def test_job_individual_corre_antes_el_pivote_y_lo_reutiliza(entorno):
    d = _inicio(entorno, "rps_target")
    assert d["estado"] == "ok"
    assert d["plan"] == ["rps_pivot", "rps_target"]
    assert "[1/2] rps_pivot" in d["log"] and "[2/2] rps_target" in d["log"]
    assert d["log"].index("[1/2] rps_pivot") < d["log"].index("[2/2] rps_target")
    assert [c[c.index("--source") + 1] for c in _calls(entorno)] == ["rps_pivot", "rps_target"]
    assert [r["job"] for r in d["resumen"]] == ["rps_pivot", "rps_target"]
    assert d["resumen"][1]["escrituras"][0]["filas"] == 3
    # 2a vez: la salida del pivote ya esta en demo_out de la sesion -> solo el job
    d2 = _inicio(entorno, "rps_target")
    assert d2["plan"] == ["rps_target"]
    assert [c[c.index("--source") + 1] for c in _calls(entorno)][2:] == ["rps_target"]
    # reiniciar demo_out: vuelve a correr primero el pivote
    sim.reiniciar(entorno.zip)
    d3 = _inicio(entorno, "rps_target")
    assert d3["plan"] == ["rps_pivot", "rps_target"]


@posix
def test_pivote_individual_corre_solo(entorno):
    d = _inicio(entorno, "ccp_pivot")
    assert d["plan"] == ["ccp_pivot"] and d["estado"] == "ok"


@posix
def test_todos_usa_continuar_si_falla_y_muestra_pivotes_primero(entorno):
    d = _inicio(entorno, None)
    assert d["estado"] == "ok"
    llamada = _calls(entorno)[0]
    assert llamada[:3] == ["main.py", "--demo", "--continuar-si-falla"] or "--continuar-si-falla" in llamada
    assert "--source" not in llamada
    assert d["plan"][:2] == ["rps_pivot", "ccp_pivot"]
    assert "[orden] pivotes primero: rps_pivot, ccp_pivot" in d["log"]
    assert [r["job"] for r in d["resumen"]][:2] == ["rps_pivot", "ccp_pivot"]


@posix
def test_pivote_que_falla_salta_el_job(entorno, monkeypatch):
    monkeypatch.setenv("BNX_FAKE_MODE", "falla")
    d = _inicio(entorno, "rps_target")
    assert d["estado"] == "fallo"
    est = {r["job"]: r["estado"] for r in d["resumen"]}
    assert est == {"rps_pivot": "ERROR", "rps_target": "SALTADO"}
    assert [c[c.index("--source") + 1] for c in _calls(entorno)] == ["rps_pivot"]


# ---------------------------------------------------------------------------
# Entorno: reutilizacion por hash del ZIP
# ---------------------------------------------------------------------------
@posix
def test_venv_se_reutiliza_mientras_el_zip_no_cambie(entorno):
    d1 = _inicio(entorno, "ccp_pivot")
    d2 = _inicio(entorno, "ccp_pivot")
    assert d1["venv_reutilizado"] is False and d2["venv_reutilizado"] is True
    assert entorno.count.read_text().count("x") == 1          # setup.sh corrio UNA vez
    _, pkg = sim.montar(entorno.zip)
    marca = os.path.join(pkg, "sentinela")
    open(marca, "w").close()
    _inicio(entorno, "ccp_pivot")
    assert os.path.exists(marca)                               # no se volvio a extraer
    # ZIP distinto -> otro hash -> carpeta y venv nuevos
    zp2 = _zip_falso(entorno.tmp / "otro.zip", extra="cambio")
    assert sim.hash_zip(zp2) != sim.hash_zip(entorno.zip)
    d3 = _esperar(sim.iniciar("t", zp2, "ccp_pivot"))
    assert d3["venv_reutilizado"] is False
    assert entorno.count.read_text().count("x") == 2


@posix
def test_info_lista_jobs_y_pivotes_sin_extraer(entorno):
    d = sim.info(entorno.zip)
    assert d["soportado"] and not d["entorno_listo"]
    assert [j["name"] for j in d["jobs"]][:2] == ["rps_target", "ccp_datapull"]
    assert {j["name"] for j in d["jobs"] if j["pivote"]} == {"rps_pivot", "ccp_pivot"}
    assert d["orden_todos"][:2] == ["rps_pivot", "ccp_pivot"]
    assert not os.path.isdir(os.path.join(os.environ["BNX_SIMULAR_DIR"], d["hash"]))   # no extrajo


# ---------------------------------------------------------------------------
# Concurrencia y cancelacion
# ---------------------------------------------------------------------------
@posix
def test_segunda_simulacion_del_mismo_paquete_es_409(entorno, monkeypatch):
    monkeypatch.setenv("BNX_FAKE_MODE", "sleep")
    rid = sim.iniciar("t", entorno.zip, "ccp_pivot")
    with pytest.raises(sim.SimError) as e:
        sim.iniciar("t", entorno.zip, "rps_pivot")
    assert e.value.status == 409
    with pytest.raises(sim.SimError) as e2:
        sim.reiniciar(entorno.zip)
    assert e2.value.status == 409
    assert _esperar(rid)["estado"] == "ok"
    sim.iniciar("t", entorno.zip, "ccp_pivot")      # ya libre: otra simulacion si se acepta
    _esperar(next(iter(sim._ACTIVO.values())))


@posix
def test_cancelar_mata_el_arbol_de_procesos(entorno, monkeypatch):
    monkeypatch.setenv("BNX_FAKE_MODE", "hang")
    rid = sim.iniciar("t", entorno.zip, "ccp_pivot")
    _, pkg = sim.montar(entorno.zip)
    pidf = os.path.join(pkg, "child.pid")
    fin = time.time() + 30
    while not os.path.exists(pidf) and time.time() < fin:
        time.sleep(0.1)
    time.sleep(0.3)
    hijo = int(open(pidf).read())
    os.kill(hijo, 0)                                           # el nieto esta vivo
    assert sim.cancelar(rid)["ok"]
    d = _esperar(rid, 20)
    assert d["estado"] == "cancelado"
    for _ in range(50):
        try:
            os.kill(hijo, 0)
        except ProcessLookupError:
            break
        time.sleep(0.1)
    else:
        raise AssertionError("el proceso hijo sigue vivo tras cancelar")
    assert "CANCELADO" in d["log"]
    sim.iniciar("t", entorno.zip, "ccp_pivot")       # el paquete queda libre tras cancelar
    sim.cancelar(next(iter(sim._ACTIVO.values())))


@posix
def test_timeout_mata_el_proceso(entorno, monkeypatch):
    monkeypatch.setenv("BNX_FAKE_MODE", "hang")
    rid = sim.iniciar("t", entorno.zip, "ccp_pivot", timeout=30)
    run = sim._RUNS[rid]
    run.timeout = 1          # el minimo de iniciar() es 30 s: se acorta para no esperar
    d = _esperar(rid, 30)
    assert d["estado"] == "fallo" and "timeout" in d["log"]


# ---------------------------------------------------------------------------
# Windows, Java, localhost, visor
# ---------------------------------------------------------------------------
def test_windows_devuelve_mensaje_sin_romper(tmp_path, monkeypatch):
    monkeypatch.setattr(sim, "es_windows", lambda: True)
    ok, msg = sim.entorno_soportado()
    assert not ok and msg == "La simulación requiere Mac/Linux (o WSL) y Java"
    d = sim.info(_zip_falso(tmp_path / "p.zip"))
    assert d["soportado"] is False and d["windows"] is True and "Mac/Linux" in d["mensaje"]
    with pytest.raises(sim.SimError) as e:
        sim.iniciar("t", str(tmp_path / "p.zip"), None)
    assert "Mac/Linux" in str(e.value)


def test_sin_java_mensaje_claro(monkeypatch):
    monkeypatch.setattr(sim, "es_windows", lambda: False)

    def _no(*a, **k):
        raise FileNotFoundError("java")
    monkeypatch.setattr(sim.subprocess, "run", _no)
    ok, msg = sim.entorno_soportado()
    assert not ok and "Java" in msg and "java -version" in msg


def test_matar_arbol_windows_usa_taskkill(monkeypatch):
    llamadas = []
    monkeypatch.setattr(sim, "es_windows", lambda: True)
    monkeypatch.setattr(sim.subprocess, "run", lambda cmd, **k: llamadas.append(cmd))
    sim.matar_arbol(types.SimpleNamespace(pid=4242))
    assert llamadas == [["taskkill", "/PID", "4242", "/T", "/F"]]
    assert sim._popen_kwargs()["creationflags"] == getattr(sim.subprocess, "CREATE_NEW_PROCESS_GROUP", 0)


def _handler(ip, origin=None, metodo="POST", cuerpo=b"{}", ruta="/mlops/simular/iniciar"):
    import io
    import serve_ui
    h = serve_ui.BNXHandler.__new__(serve_ui.BNXHandler)
    h.client_address = (ip, 5555)
    h.headers = {"Content-Length": str(len(cuerpo))}
    if origin:
        h.headers["Origin"] = origin
    h.command, h.path = metodo, ruta
    h.rfile = io.BytesIO(cuerpo)
    h.respuestas = []
    h._json_response = lambda st, d: h.respuestas.append((st, d))
    return h, serve_ui


@pytest.mark.parametrize("ip,origin", [("10.1.2.3", None), ("127.0.0.1", "http://evil.example.com")])
def test_endpoints_solo_localhost(ip, origin, monkeypatch):
    h, _ = _handler(ip, origin)
    llamado = []
    monkeypatch.setattr(sim, "iniciar", lambda *a, **k: llamado.append(a))
    for ruta, metodo in (("/mlops/simular/iniciar", "POST"), ("/mlops/simular/cancelar", "POST"),
                         ("/mlops/simular/estado?run=x", "GET"), ("/mlops/simular/info?token=ab", "GET"),
                         ("/mlops/simular/visor", "POST"), ("/mlops/simular/reiniciar", "POST")):
        h.respuestas.clear()
        h.command, h.path = metodo, ruta
        h._handle_mlops_simular(ruta.split("?")[0])
        assert h.respuestas[0][0] == 403, ruta
    assert llamado == []


def test_endpoint_localhost_token_invalido_404(monkeypatch):
    h, _ = _handler("127.0.0.1", "http://localhost:5173", cuerpo=b'{"token": "../../etc"}')
    h._handle_mlops_simular("/mlops/simular/iniciar")
    assert h.respuestas[0][0] == 404


@posix
def test_visor_lee_solo_demo_out_del_paquete(entorno):
    from src import parquet_visor as pv
    _inicio(entorno, "ccp_pivot")
    _, pkg = sim.montar(entorno.zip)
    os.makedirs(os.path.join(pkg, "demo_out", "hive", "db", "t"))
    with open(os.path.join(pkg, "demo_out", "hive", "db", "t", "part-0.csv"), "w") as fh:
        fh.write("a,b\n1,2\n3,4\n")
    base = sim.base_visor(entorno.zip)
    lst = pv.listar(base)["datasets"]
    assert [x["nombre"] for x in lst] == ["hive/db/t"] and lst[0]["zona"] == "output"
    assert pv.leer(base, "output", "hive/db/t")["filas"] == [["1", "2"], ["3", "4"]]
    with pytest.raises(pv.VisorError):
        pv.leer(base, "output", "../calls.log")
    with pytest.raises(pv.VisorError):
        pv.leer(base, "raw", "x")


def test_resultados_de_log_y_filas():
    txt = ("[kernel] FIN OK a en 1.5 s | log: x\n[kernel] FIN ERROR b en 0.2 s: KeyError: 'k'\n"
           "[kernel] SALTADO c: depende de b\n")
    r = sim.resultados_de_log(txt)
    assert r["a"] == {"estado": "OK", "seg": 1.5, "detalle": ""}
    assert r["b"]["estado"] == "ERROR" and "KeyError" in r["b"]["detalle"]
    assert r["c"]["estado"] == "SALTADO"


def test_modulo_compatible_con_python_38():
    here = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    with open(os.path.join(here, "src", "mlops_simular.py"), encoding="utf-8") as fh:
        ast.parse(fh.read(), feature_version=(3, 8))
