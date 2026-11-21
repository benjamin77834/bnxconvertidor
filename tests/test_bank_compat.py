# -*- coding: utf-8 -*-
"""bank_compat: diagnostico generico de las librerias del banco + capa de compatibilidad + mensajes de faltantes.

Modelo SINTETICO 2 (sin red): una libreria falsa del banco (wheel minima) con
  - un submodulo faltante usado solo en una rama que el modelo no usa  -> PARCHEABLE (stub)
  - otro submodulo faltante que el modelo SI usa                      -> BLOQUEADO
  - un alias 'libs.' roto                                             -> PARCHEABLE (alias)
  - una firma con parametro obligatorio extra (esta en la config)     -> PARCHEABLE (adaptador)
  - un import de numpy.source sin uso                                 -> PARCHEABLE (shim)
"""
import ast
import json
import os
import subprocess
import sys
import zipfile

import pytest

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, RAIZ)
from src import bank_compat as bc  # noqa: E402

FAKE_FILES = {
    "lib_fake/__init__.py": "from .lib_fake_core.fake import FakeClient\n",
    "lib_fake/lib_fake_core/__init__.py": "from .fake import FakeClient\n",
    "lib_fake/lib_fake_core/helpers.py": "def clean(x):\n    return 'clean:' + str(x)\n",
    "lib_fake/lib_fake_core/fake.py": (
        "from numpy import source\n"
        "from .extras.premium import PremiumPlugin\n"
        "from .extras.core_engine import CoreEngine\n"
        "from libs.helpers import clean\n\n\n"
        "class FakeClient(object):\n"
        "    def __init__(self, path, config, workers, mode='standard'):\n"
        "        self.path, self.config, self.workers, self.mode = path, config, workers, mode\n\n"
        "    def run(self):\n"
        "        if self.mode == 'premium':\n"
        "            return PremiumPlugin(self).go()\n"
        "        return clean(self.path) + ':w%s' % self.workers\n\n"
        "    def run_core(self):\n"
        "        return CoreEngine().go()\n"),
}
MODEL_JOB = (
    "from lib_fake import FakeClient\n\n\n"
    "def run(kernel):\n"
    "    c = FakeClient('/data/x', {'a': 1})\n"
    "    out = c.run()\n"
    "    c.run_core()\n"
    "    return out\n")
MODEL_CFG = json.dumps({"default": {"workers": "4", "mode": "standard"}})


def construir_wheel_fake(carpeta, files=None):
    """Escribe mex_libfake-1.0.0-py3-none-any.whl en `carpeta` y devuelve su ruta."""
    os.makedirs(carpeta, exist_ok=True)
    ruta = os.path.join(carpeta, "mex_libfake-1.0.0-py3-none-any.whl")
    with zipfile.ZipFile(ruta, "w") as z:
        for rel, txt in (files or FAKE_FILES).items():
            z.writestr(rel, txt)
        z.writestr("mex_libfake-1.0.0.dist-info/METADATA", "Metadata-Version: 2.1\nName: mex-libfake\nVersion: 1.0.0\n")
        z.writestr("mex_libfake-1.0.0.dist-info/WHEEL",
                   "Wheel-Version: 1.0\nGenerator: bnx-test\nRoot-Is-Purelib: true\nTag: py3-none-any\n")
        z.writestr("mex_libfake-1.0.0.dist-info/top_level.txt", "lib_fake\n")
    return ruta


def analizar_fake(tmp_path, cfg=MODEL_CFG, numpy="2.0.0"):
    wd = str(tmp_path / "wheels")
    construir_wheel_fake(wd)
    codigos = {"bank_src/jobs/fake/demo/job.py": MODEL_JOB}
    cfgs = {"bank_src/settings/fake/config_custom.json": cfg} if cfg is not None else {}
    return bc.analizar([wd], codigos, cfgs, {"numpy": numpy, "python": "3.11"})


def _hall(rep, tipo, **kw):
    lib = rep["librerias"][0]
    out = [h for h in lib["hallazgos"] if h["tipo"] == tipo and all(h.get(k) == v for k, v in kw.items())]
    return out


# ---------------------------------------------------------------------------
# Analisis
# ---------------------------------------------------------------------------
def test_clasificacion_del_modelo_sintetico(tmp_path):
    rep = analizar_fake(tmp_path)
    lib = rep["librerias"][0]
    assert lib["libreria"] == "mex-libfake" and lib["usada_por_modelo"] is True
    assert lib["estado"] == bc.BLOQUEADO
    premium = [h for h in lib["hallazgos"] if h["tipo"] == "submodulo_faltante" and "premium" in h["modulo"]][0]
    assert premium["estado"] == bc.PARCHEABLE and premium["fuentes"] == ["premium"]
    assert "ninguna config del modelo usa la fuente premium" in premium["detalle"]
    core = [h for h in lib["hallazgos"] if h["tipo"] == "submodulo_faltante" and "core_engine" in h["modulo"]][0]
    assert core["estado"] == bc.BLOQUEADO and core["incondicional"] is True
    assert core["usos_modelo"] and core["usos_modelo"][0]["archivo"].endswith("job.py")
    alias = _hall(rep, "alias_inexistente")[0]
    assert alias["modulo"] == "libs.helpers" and alias["destino"].endswith("lib_fake_core.helpers")
    assert alias["estado"] == bc.PARCHEABLE
    firma = _hall(rep, "firma")[0]
    assert firma["estado"] == bc.PARCHEABLE and firma["faltan"] == ["workers"]
    assert firma["adaptaciones"][0]["fuente"] == "config" and firma["adaptaciones"][0]["clave"] == "workers"
    assert firma["linea_modelo"] == 5 and firma["archivo_modelo"].endswith("job.py")
    api = _hall(rep, "api_eliminada")[0]
    assert (api["modulo"], api["nombre"], api["usada"]) == ("numpy", "source", False)
    assert api["estado"] == bc.PARCHEABLE
    assert rep["parches"]["shims"] == [{"modulo": "numpy", "nombre": "source", "hallazgo": api["id"]}]
    json.dumps(rep)                       # serializable


def test_si_el_modelo_usa_la_fuente_el_stub_pasa_a_bloqueado(tmp_path):
    rep = analizar_fake(tmp_path, cfg=json.dumps({"default": {"workers": 2, "mode": "premium"}}))
    premium = [h for h in rep["librerias"][0]["hallazgos"] if "premium" in h.get("modulo", "")][0]
    assert premium["estado"] == bc.BLOQUEADO and "configura la fuente premium" in premium["detalle"]


def test_parametro_obligatorio_sin_valor_es_bloqueado(tmp_path):
    rep = analizar_fake(tmp_path, cfg=json.dumps({"default": {"mode": "standard"}}))
    firma = _hall(rep, "firma")[0]
    assert firma["estado"] == bc.BLOQUEADO and firma["sin_adaptar"] == ["workers"]
    assert not rep["parches"]["firmas"]


def test_numpy_source_no_aplica_si_el_target_es_numpy_1(tmp_path):
    rep = analizar_fake(tmp_path, numpy="1.26.4")
    api = _hall(rep, "api_eliminada")[0]
    assert api["aplica_en_target"] is False and api["estado"] == bc.OK


def test_numpy_source_usado_de_verdad_es_bloqueado(tmp_path):
    wd = str(tmp_path / "w")
    files = dict(FAKE_FILES)
    files["lib_fake/lib_fake_core/helpers.py"] = "import numpy as np\n\ndef clean(x):\n    return np.float(x)\n"
    construir_wheel_fake(wd, files)
    rep = bc.analizar([wd], {"bank_src/jobs/j.py": MODEL_JOB}, {"c.json": MODEL_CFG}, {"numpy": "2.0.0"})
    usos = [h for h in rep["librerias"][0]["hallazgos"] if h["tipo"] == "api_eliminada" and h["nombre"] == "float"]
    assert usos and usos[0]["usada"] and usos[0]["estado"] == bc.BLOQUEADO


def test_lib_que_el_modelo_no_usa_no_se_marca_bloqueada(tmp_path):
    wd = str(tmp_path / "w")
    construir_wheel_fake(wd)
    rep = bc.analizar([wd], {"bank_src/jobs/j.py": "x = 1\n"}, {"c.json": MODEL_CFG}, {"numpy": "2.0.0"})
    lib = rep["librerias"][0]
    assert lib["usada_por_modelo"] is False and lib["estado"] == bc.PARCHEABLE


def test_texto_y_tabla(tmp_path):
    rep = analizar_fake(tmp_path)
    txt = bc.resumen_texto(rep)
    assert "BLOQUEADO" in txt and "mex-libfake" in txt and "NO validado" in txt
    tabla = bc.tabla_estados(rep)
    assert tabla[0]["estado"] == bc.BLOQUEADO and tabla[0]["bloqueos"] >= 1 and tabla[0]["parches"] >= 3


# ---------------------------------------------------------------------------
# Runtime (en un proceso aparte: cada prueba arma su sys.modules limpio)
# ---------------------------------------------------------------------------
RUN_SCRIPT = r"""
import json, os, sys
sys.path.insert(0, os.environ["T_PKG"])
sys.path.insert(0, os.environ["T_LIB"])
import bank_compat as bc
out = {}
try:
    bc.instalar()
    from lib_fake import FakeClient
    c = FakeClient("/data/x", {"a": 1})
    out["run"] = c.run()
    try:
        c.run_core()
        out["core"] = "sin error"
    except Exception as e:
        out["core_tipo"] = type(e).__name__
        out["core_msg"] = str(e)
        inf = bc.traducir_excepcion(e)
        out["core_info"] = bool(inf)
        if inf:
            sys.stdout.write("")
            bc.registrar_faltante(inf)
except Exception as e:
    out["import_tipo"] = type(e).__name__
    out["import_msg"] = str(e)
    inf = bc.traducir_excepcion(e)
    out["import_info"] = bool(inf)
    out["import_texto"] = bc.formatear(inf) if inf else ""
print("@@" + json.dumps(out))
"""


def preparar_runtime(tmp_path, rep):
    pkg = tmp_path / "pkg"
    lib = tmp_path / "libdir"
    pkg.mkdir()
    (lib).mkdir()
    with zipfile.ZipFile(construir_wheel_fake(str(tmp_path / "w"))) as z:
        z.extractall(str(lib))
    (pkg / "bank_compat.py").write_text(open(os.path.join(RAIZ, "src", "bank_compat.py"), encoding="utf-8").read(),
                                        encoding="utf-8")
    (pkg / bc.REPORTE_NOMBRE).write_text(bc.reporte_a_json(rep), encoding="utf-8")
    conf = tmp_path / "settings"
    (conf / "fake").mkdir(parents=True)
    (conf / "fake" / "config_custom.json").write_text(MODEL_CFG, encoding="utf-8")
    logs = tmp_path / "logs" / "2026_01"
    logs.mkdir(parents=True)
    return pkg, lib, conf, logs


def correr(tmp_path, rep, env_extra):
    pkg, lib, conf, logs = preparar_runtime(tmp_path, rep)
    env = dict(os.environ)
    for k in ("BNX_MODO", "BNX_SIMULACION", "BNX_BANK_COMPAT"):
        env.pop(k, None)
    env.update({"T_PKG": str(pkg), "T_LIB": str(lib), "CONF_PATH": str(conf), "BNX_JOB_ID": "fake_demo",
                "LOG_FILE_PATH": str(logs / "bnx_fake_demo.log"), "PYTHONPATH": ""})
    env.update(env_extra)
    p = subprocess.run([sys.executable, "-c", RUN_SCRIPT], env=env, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                       universal_newlines=True, timeout=120)
    linea = [l for l in p.stdout.splitlines() if l.startswith("@@")]
    assert linea, p.stdout + p.stderr
    return json.loads(linea[-1][2:]), p.stderr, tmp_path / "logs"


def test_runtime_demo_aplica_parches_y_bloqueado_falla_con_mensaje_completo(tmp_path):
    pytest.importorskip("numpy")
    rep = analizar_fake(tmp_path)
    out, err, logs = correr(tmp_path, rep, {"BNX_MODO": "demo"})
    assert "import_tipo" not in out, out
    assert out["run"] == "clean:/data/x:w4"            # alias libs + firma completada con config (workers=4)
    assert out["core_tipo"] == "BNXFaltaComponente"
    msg = out["core_msg"]
    assert msg.startswith("FALTA CoreEngine (modulo lib_fake.lib_fake_core.extras.core_engine de la libreria "
                          "mex-libfake 1.0.0)")
    assert "Lo necesita: fake_demo -> " in msg and "job.py:" in msg
    assert "Por que: el .tar.gz/.whl del banco no trae el subpaquete" in msg
    assert "(1) en el portal BNX, pestana Framework MLOps v2 -> Librerias / Vendor -> Banco: subir el .whl/.tar.gz " \
           "completo de mex-libfake" in msg
    assert "(2) o en terminal: python preparar_vendor.py --bank-libs <carpeta|zip>" in msg
    assert "(3) o actualizar el repo privado bnx-banco (wheels/) y git pull" in msg
    assert "Pasos: 1) pedir al equipo duenio mex-libfake completa" in msg and "4) bash setup.sh y volver a correr fake_demo" in msg
    assert "PARCHEADO" in err and "no validado" in err      # avisos ambar en la terminal
    f = json.load(open(str(logs / bc.FALTANTES_NOMBRE), encoding="utf-8"))["faltantes"]
    tipos = sorted(set(x["tipo"] for x in f))
    assert tipos == ["falta", "parcheado"]
    falta = [x for x in f if x["tipo"] == "falta"][0]
    assert falta["job"] == "fake_demo" and falta["severidad"] == "error" and falta["texto"] == msg
    assert any("workers" in x["componente"] for x in f if x["tipo"] == "parcheado")
    log_job = open(str(logs / "2026_01" / "bnx_fake_demo.log"), encoding="utf-8").read()
    assert msg in log_job and "PARCHEADO" in log_job          # tambien en el log del job


def test_runtime_real_sin_variable_no_parchea_y_explica(tmp_path):
    rep = analizar_fake(tmp_path)
    out, err, _ = correr(tmp_path, rep, {"BNX_MODO": "real"})
    assert "run" not in out
    assert out["import_info"] is True
    assert out["import_tipo"] in ("ModuleNotFoundError", "ImportError")
    t = out["import_texto"]
    assert t.startswith("FALTA ") and "Lo necesita: fake_demo -> " in t and "Donde cargarlo: (1)" in t
    assert "Pasos: 1) pedir al equipo duenio mex-libfake completa" in t
    assert "BNX_BANK_COMPAT=1" in t and "NO validado" in t       # parche disponible pero apagado en modo real


def test_runtime_real_con_variable_muestra_aviso_grande(tmp_path):
    pytest.importorskip("numpy")
    rep = analizar_fake(tmp_path)
    out, err, _ = correr(tmp_path, rep, {"BNX_MODO": "real", "BNX_BANK_COMPAT": "1"})
    assert out.get("run") == "clean:/data/x:w4"
    assert "Parches BNX sobre librerias del banco: NO validado contra la salida original. " \
           "Pide al equipo duenio las librerias completas." in err


def test_traduccion_generica_de_un_import_roto_sin_reporte(tmp_path):
    """Sin bank_compat_report.json: la libreria se identifica por la ruta del frame y el modulo por el mensaje."""
    lib = tmp_path / "lib_otra"
    (lib / "lib_otra_core").mkdir(parents=True)
    (lib / "__init__.py").write_text("", encoding="utf-8")
    (lib / "lib_otra_core" / "__init__.py").write_text("from .no_existe import X\n", encoding="utf-8")
    sys.path.insert(0, str(tmp_path))
    try:
        with pytest.raises(ImportError) as ei:
            __import__("lib_otra.lib_otra_core")
    finally:
        sys.path.remove(str(tmp_path))
        for k in [k for k in sys.modules if k.startswith("lib_otra")]:
            del sys.modules[k]
    os.environ["BNX_JOB_ID"] = "otro_job"
    try:
        inf = bc.traducir_excepcion(ei.value)
    finally:
        del os.environ["BNX_JOB_ID"]
    assert inf and inf["modulo"] == "lib_otra.lib_otra_core.no_existe"
    txt = bc.formatear(inf, "otro_job")
    assert txt.startswith("FALTA no_existe (modulo lib_otra.lib_otra_core.no_existe de la libreria")
    assert "Lo necesita: otro_job -> " in txt and "Donde cargarlo: (1)" in txt and "Pasos: 1)" in txt


def test_traduccion_de_typeerror_de_firma():
    def run():
        class MissingTreatment(object):
            def __init__(self, a, n_threads):
                pass
        MissingTreatment(1)
    with pytest.raises(TypeError) as ei:
        run()
    inf = bc.traducir_excepcion(ei.value)
    assert inf and inf["libreria"] == "mex-libmissingtreatment" and "firma distinta" in inf["por_que"]
    assert "n_threads" in inf["por_que"]


def test_formato_del_mensaje_tiene_las_cinco_secciones():
    inf = {"componente": "PreviousFixerPayrollIncome", "modulo": "lib_x.core.mobs.payroll_income",
           "libreria": "mex-libx", "version": "2.2.0", "por_que": "falta el subpaquete",
           "subpaquete": "lib_x/core/mobs/",
           "necesita": {"archivo": "bnmxverse/data_pull.py", "linea": 652, "funcion": "MissingTreatment.run_mobs",
                        "condicion": "solo si la fuente es payroll_income"}}
    t = bc.formatear(inf, "rps_datapull")
    lineas = t.splitlines()
    assert lineas[0] == "FALTA PreviousFixerPayrollIncome (modulo lib_x.core.mobs.payroll_income de la libreria " \
                        "mex-libx 2.2.0)"
    assert "Lo necesita: rps_datapull -> bnmxverse/data_pull.py:652 (MissingTreatment.run_mobs, solo si la fuente es " \
           "payroll_income)" in lineas[1]
    assert lineas[2].strip().startswith("Por que: falta el subpaquete")
    assert "Donde cargarlo:" in t and "(incluyendo lib_x/core/mobs/)" in t


# ---------------------------------------------------------------------------
# Compatibilidad de sintaxis y consistencia con la fachada / el empaquetado
# ---------------------------------------------------------------------------
def test_bank_compat_es_python_38():
    src = open(os.path.join(RAIZ, "src", "bank_compat.py"), encoding="utf-8").read()
    ast.parse(src, feature_version=(3, 8))
    from src import mlops_pkg as mp
    ast.parse(mp._MEX_LIB_CS, feature_version=(3, 8))


def test_la_fachada_y_bank_compat_comparten_la_tabla_de_exports():
    from src import mlops_pkg as mp
    ns = {}
    tree = ast.parse(mp._MEX_LIB_CS)
    for n in tree.body:
        if isinstance(n, ast.Assign) and getattr(n.targets[0], "id", "") == "_EXPORTS":
            ns["_EXPORTS"] = ast.literal_eval(n.value)
    assert ns["_EXPORTS"] == bc.FACHADA_EXPORTS


def test_el_empaquetado_instala_todas_las_mex_lib_con_compat(tmp_path, monkeypatch):
    from src import mlops_pkg as mp
    banco = tmp_path / "banco"
    construir_wheel_fake(str(banco / "wheels"))
    monkeypatch.setattr(mp, "_BANK_LIBS_CACHE", str(banco))
    files = {"bank_src/jobs/fake/demo/job.py": MODEL_JOB, "bank_src/settings/fake/config_custom.json": MODEL_CFG}
    rep = mp._compat_analizar(files, "py3.11")
    assert rep and rep["librerias"][0]["libreria"] == "mex-libfake"
    txt = mp._requirements_bank(["lib_fake"], {"mex-libfake": ["lib_fake"]})
    assert "mex-libfake" in [l for l in txt.splitlines() if not l.startswith("#")]
    sd, _pk = mp._bank_vendor_files(True)
    assert [os.path.basename(x) for x in sd] == ["mex_libfake-1.0.0-py3-none-any.whl"]
    sd0, _ = mp._bank_vendor_files(False)
    assert sd0 == []                       # sin compat, las no verificadas se siguen omitiendo
    assert "bank_compat.py" in mp._bank_compat_fuente()[:200] or "bank_compat" in mp._bank_compat_fuente()[:300]


def test_el_endpoint_de_simulacion_expone_los_faltantes(tmp_path):
    from src import mlops_simular as sim
    pkg = tmp_path / "pkg"
    (pkg / "logs").mkdir(parents=True)
    run = sim.Run("tok", "h", str(pkg), None, 30)
    assert run.a_dict()["faltantes"] == []
    (pkg / "logs" / bc.FALTANTES_NOMBRE).write_text(json.dumps({"version": 1, "faltantes": [
        {"job": "rps_datapull", "tipo": "falta", "componente": "X", "texto": "FALTA X (...)"}]}), encoding="utf-8")
    d = run.a_dict()
    assert d["faltantes"][0]["job"] == "rps_datapull" and d["faltantes"][0]["texto"].startswith("FALTA X")
