"""Jobs del banco (def run(kernel)) en el Framework MLOps v2 generado (src/mlops_pkg.py).

Fuentes FALSAS pequenas que imitan el patron del banco (toolbox/kernel.py con clase Kernel,
jobs/<model>/<job>/job.py con run(kernel), main.py con Launcher). Sin red y sin Spark:
el Kernel falso no arranca una sesion; se prueba que el runner de main.py lo construya
como el banco, llame run(kernel) en orden y respete --source / --continuar-si-falla.
"""
import ast
import importlib
import json
import os
import subprocess
import sys
import zipfile

import pytest

from src import mlops_pkg as mp

_PYSPARK = pytest.importorskip("pyspark")

BANK_MAIN = '''
import os, sys, argparse, importlib
sys.path.append(os.getenv("BIN_PATH"))
from toolbox.kernel import Kernel


class Launcher:
    def __init__(self):
        self.arguments = self.argumentParser()
        self.kernel = Kernel(self.arguments["job"], os.environ["LOG_FILE_PATH"], os.environ["CONF_PATH"])

    def argumentParser(self):
        p = argparse.ArgumentParser()
        for f in ("-f", "-e", "-m", "-j", "-c"):
            p.add_argument(f, required=(f != "-c"))
        p.add_argument("-v", type=bool, default=False)
        a = p.parse_args()
        return {"fid": a.f.lower(), "env": a.e.lower(), "model": a.m.lower(), "job": a.j.lower(),
                "cohort": a.c, "verbose": a.v}

    def run(self, arguments=None):
        try:
            self.kernel.launch(arguments if arguments else self.argumentParser())
            importlib.import_module("jobs.%s.%s.job" % (self.kernel.args["model"], self.kernel.args["job"])).run(self.kernel)
            with open(os.environ["BNX_TEST_OUT"], "a") as fh:
                fh.write("via=launcher\\n")
        except Exception:
            self.kernel.log.log_error()
            raise
'''

KERNEL_PY = '''
class _Log:
    def log_error(self, msg=None):
        pass

    def log_info(self, msg=None):
        pass


class Kernel:
    def __init__(self, app_name, log_path, settings_path):
        self.log = _Log()
        self.settings_path = settings_path
        self.app_name = app_name

    def launch(self, args):
        self.args = args
'''

JOB_OK = '''
import json
import os
from toolbox.kernel import Kernel


def run(kernel: Kernel) -> None:
    assert os.path.isfile(os.path.join(kernel.settings_path, "spark.json")), "sin spark.json"
    with open(os.environ["BNX_TEST_OUT"], "a") as fh:
        fh.write("%s %s\\n" % (kernel.args["model"] + "_" + kernel.args["job"],
                              json.dumps(kernel.args, sort_keys=True)))
'''

JOB_FALLA = '''
def run(kernel):
    with open(__import__("os").environ["BNX_TEST_OUT"], "a") as fh:
        fh.write("%s_%s intento\\n" % (kernel.args["model"], kernel.args["job"]))
    raise RuntimeError("boom del job")
'''

P = "proy/bin/"


def _fuentes(con_main=True):
    f = []
    if con_main:
        f.append({"name": "proy/main.py", "code": BANK_MAIN})
    f += [
        {"name": P + "toolbox/kernel.py", "code": KERNEL_PY},
        {"name": P + "toolbox/weeks.py", "code": "def semana():\n    return 1\n"},
        {"name": P + "utils/dateUtils.py", "code": "def hoy():\n    return 'x'\n"},
        {"name": P + "jobs/m1/a/job.py", "code": JOB_OK},
        {"name": P + "jobs/m1/pivot/job.py", "code": JOB_OK},
        {"name": P + "jobs/m2/b/job.py", "code": JOB_FALLA},
        {"name": P + "jobs/m2/c/job.py", "code": JOB_OK},
    ]
    return f


def _convert(code):
    return {"ok": True, "code": "df_out = df  # CONVERTIDO", "warnings": [], "unsupported": []}


def _build(tmp_path, fuentes, **kw):
    out = tmp_path / "pkg.zip"
    _, _, report = mp.build_package_from_sources(
        fuentes, convert_fn=_convert, include_bank_libs=False, out_path=str(out),
        py_target="py3.11", **kw)
    z = zipfile.ZipFile(out)
    files = {n[len("framework_mlops_v2_pkg/"):]: n for n in z.namelist()
             if n.startswith("framework_mlops_v2_pkg/")}
    root = tmp_path / "pkg"
    z.extractall(root)
    return z, files, [r for r in report if not r.get("_meta")], str(root / "framework_mlops_v2_pkg")


def _read(z, files, rel):
    return z.read(files[rel]).decode("utf-8")


def _router_dict(z, files):
    router = _read(z, files, "framework_mlops_v2/aggregates/router.py")
    return ast.literal_eval(router.split("_FUENTES = ")[1].split("\n}")[0] + "\n}")


def _run(pkg, args, tmp_path):
    out = tmp_path / "out.txt"
    out.write_text("")
    env = {k: v for k, v in os.environ.items()
           if k not in ("JAVA_TOOL_OPTIONS", "SPARK_CONF_DIR", "CONF_PATH", "BIN_PATH", "BNX_ORDEN")}
    env["BNX_TEST_OUT"] = str(out)
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    r = subprocess.run([sys.executable, "main.py"] + args, cwd=pkg, env=env,
                       capture_output=True, text=True, timeout=240)
    lineas = [ln for ln in out.read_text().splitlines() if ln]
    return r, lineas


# --- clasificacion ------------------------------------------------------------
def test_clasificacion_main_weeks_y_nombres_por_ruta(tmp_path):
    z, files, rep, _ = _build(tmp_path, _fuentes())
    # (a) el main.py del banco no es job ni aggregate
    assert _read(z, files, "bank_src/main.py") == BANK_MAIN
    assert "framework_mlops_v2/aggregates/main.py" not in files
    # (b) weeks.py (nadie lo importa) va a su paquete de apoyo, no a aggregates/
    assert _read(z, files, "bank_src/toolbox/weeks.py").startswith("def semana")
    assert "framework_mlops_v2/aggregates/weeks.py" not in files
    assert "bank_src/toolbox/__init__.py" in files and "bank_src/utils/__init__.py" in files
    por = {r["name"]: r for r in rep}
    assert por["proy/main.py"]["role"] == "apoyo"
    assert por[P + "toolbox/weeks.py"]["role"] == "apoyo" and por[P + "toolbox/weeks.py"]["paquete"] == "toolbox"
    # (c) nombres por ruta, estables y sin colisiones (todos se llaman job.py)
    reg = _router_dict(z, files)
    assert set(reg) == {"m1_a", "m1_pivot", "m2_b", "m2_c"}
    assert reg["m1_a"] == ("jobs.m1.a.job", "run", "kernel", "m1/a")
    assert not any(f.startswith("framework_mlops_v2/aggregates/") and f.endswith("job.py") for f in files)
    for r in rep:
        if r.get("kind") == "kernel":
            assert r["job_kernel"] is True and r["source"] in reg
    assert _read(z, files, "bank_src/jobs/m1/a/job.py") == JOB_OK          # copia exacta
    assert "bank_src/jobs/m1/__init__.py" in files
    # alias de los nombres viejos (job, job_2, ...) para orden.json existentes
    router = _read(z, files, "framework_mlops_v2/aggregates/router.py")
    ns = {}
    exec(compile(router.split("def _ayuda_import")[0], "router", "exec"), ns)
    assert ns["ALIAS"] == {"job": "m1_a", "job_2": "m1_pivot", "job_3": "m2_b", "job_4": "m2_c"}
    assert set(ns["KERNEL"]) == set(reg) and ns["KERNEL"]["m2_b"]["model"] == "m2"
    # todo es Python valido (portal compatible con 3.8)
    for rel in ("main.py", "check_env.py", "framework_mlops_v2/aggregates/router.py"):
        ast.parse(_read(z, files, rel), feature_version=(3, 8))


def test_main_y_check_env_son_python38():
    ast.parse(mp._MAIN_PY, feature_version=(3, 8))
    ast.parse(mp._CHECK_ENV, feature_version=(3, 8))


def test_registry_con_ruta_completa_distingue_job_py_repetidos(tmp_path):
    reg = [P + "jobs/m1/a/job.py", P + "jobs/m1/pivot/job.py"]
    z, files, rep, _ = _build(tmp_path, _fuentes(), registry=reg)
    assert set(_router_dict(z, files)) == {"m1_a", "m1_pivot"}
    assert not any(r.get("kind") == "kernel" and r["source"].startswith("m2_") for r in rep)


def test_sin_ruta_el_job_de_kernel_se_registra_con_el_nombre_del_archivo(tmp_path):
    z, files, rep, _ = _build(tmp_path, [{"name": "job_3.py", "code": JOB_OK}])
    reg = _router_dict(z, files)
    assert reg["job_3"][:3] == ("jobs.job_3.job", "run", "kernel")
    assert _read(z, files, "bank_src/jobs/job_3/job.py") == JOB_OK


# --- router perezoso con los dos tipos ------------------------------------------
def test_router_soporta_aggregates_y_kernel_sin_importar_todo(tmp_path, monkeypatch):
    kernel = [{"name": "m1_a", "module": "jobs_x.m1.a.job", "model": "m1", "job": "a"},
              {"name": "m1_roto", "module": "jobs_x.m1.roto.job", "model": "m1", "job": "roto"}]
    pkg = tmp_path / "fwk" / "aggregates"
    pkg.mkdir(parents=True)
    (tmp_path / "fwk" / "__init__.py").write_text("")
    (pkg / "__init__.py").write_text("")
    (pkg / "router.py").write_text(mp._router_from_sources(["agg"], kernel, {"job": "m1_a"}))
    (pkg / "agg.py").write_text("class AggAggregate:\n    ok = True\n")
    for rel in ("jobs_x", "jobs_x/m1", "jobs_x/m1/a", "jobs_x/m1/roto"):
        (tmp_path / rel).mkdir(exist_ok=True)
        (tmp_path / rel / "__init__.py").write_text("")
    (tmp_path / "jobs_x/m1/a/job.py").write_text("def run(kernel):\n    return 'ok'\n")
    (tmp_path / "jobs_x/m1/roto/job.py").write_text("raise OSError('no carga')\n")
    monkeypatch.syspath_prepend(str(tmp_path))
    for m in [m for m in sys.modules if m.startswith(("fwk", "jobs_x"))]:
        del sys.modules[m]
    router = importlib.import_module("fwk.aggregates.router")
    assert "jobs_x.m1.a.job" not in sys.modules                      # nada se importa al inicio
    assert sorted(router.REGISTRY) == ["agg"]                        # REGISTRY = solo aggregates
    assert router.REGISTRY["agg"].ok is True
    assert sorted(router.KERNEL) == ["m1_a", "m1_roto"] and router.ALIAS == {"job": "m1_a"}
    assert router.cargar_job_kernel("m1_a").run(None) == "ok"
    with pytest.raises(ImportError) as ei:
        router.cargar_job_kernel("m1_roto")
    assert "m1_roto" in str(ei.value)
    with pytest.raises(KeyError):
        router.cargar_job_kernel("nada")


# --- el main.py generado ejecuta run(kernel) -------------------------------------
@pytest.fixture(scope="module")
def pkg_kernel(tmp_path_factory):
    tmp = tmp_path_factory.mktemp("kernel_pkg")
    z, files, rep, root = _build(tmp, _fuentes())
    return root


def test_demo_corre_en_orden_pivote_primero_y_se_detiene_al_primer_error(pkg_kernel, tmp_path):
    r, lineas = _run(pkg_kernel, [], tmp_path)
    jobs = [ln.split()[0] for ln in lineas if not ln.startswith("via=")]
    assert jobs == ["m1_pivot", "m1_a", "m2_b"]       # pivote primero; c NO corre tras el error de b
    assert r.returncode == 1
    assert "DEMO" in r.stdout and "FIN OK m1_pivot" in r.stdout
    assert "FIN ERROR m2_b" in r.stdout and "RuntimeError: boom del job" in r.stdout
    assert "SALTADO m2_c" in r.stdout
    assert "via=launcher" in lineas                    # uso el Launcher del main.py del banco
    # el Kernel recibio los mismos argumentos que arma el banco (-f -e -m -j -c)
    args = json.loads(next(ln for ln in lineas if ln.startswith("m1_a ")).split(" ", 1)[1])
    assert args["model"] == "m1" and args["job"] == "a" and args["env"] == "uat" and args["fid"] == "demo"
    assert len(args["cohort"]) == 6 and args["verbose"] is False


def test_continuar_si_falla_corre_todo_y_sale_con_error(pkg_kernel, tmp_path):
    r, lineas = _run(pkg_kernel, ["--continuar-si-falla"], tmp_path)
    jobs = [ln.split()[0] for ln in lineas if not ln.startswith("via=")]
    assert jobs == ["m1_pivot", "m1_a", "m2_b", "m2_c"]
    assert r.returncode == 1
    assert "3 OK, 1 con error, 0 saltados" in r.stdout


def test_source_corre_uno_solo_y_acepta_nombres_viejos(pkg_kernel, tmp_path):
    r, lineas = _run(pkg_kernel, ["--source", "m1_a"], tmp_path)
    assert r.returncode == 0 and [ln.split()[0] for ln in lineas if " " in ln and not ln.startswith("via")] == ["m1_a"]
    r, lineas = _run(pkg_kernel, ["--source", "job"], tmp_path)      # alias viejo de m1_a
    assert r.returncode == 0 and "FIN OK m1_a" in r.stdout
    r, lineas = _run(pkg_kernel, ["--source", "m2_b"], tmp_path)
    assert r.returncode == 1 and "FIN ERROR m2_b" in r.stdout
    r, lineas = _run(pkg_kernel, ["--source", "nada"], tmp_path)
    assert r.returncode != 0 and "m1_a" in (r.stdout + r.stderr) and "Jobs del banco" in (r.stdout + r.stderr)


def test_orden_json_con_nombres_viejos_y_dependencias(pkg_kernel, tmp_path):
    orden = os.path.join(pkg_kernel, "orden.json")
    # 'job' = m1_a, 'job_3' = m2_b (nombres viejos): m1_a depende de m2_b, que falla
    with open(orden, "w") as fh:
        json.dump({"sources": {"job": {"depends_on": ["job_3"]}}}, fh)
    try:
        r, lineas = _run(pkg_kernel, ["--continuar-si-falla"], tmp_path)
    finally:
        os.remove(orden)
    jobs = [ln.split()[0] for ln in lineas if not ln.startswith("via=")]
    assert jobs == ["m1_pivot", "m2_b", "m2_c"]                       # m1_a se salto: su dependencia fallo
    assert "SALTADO m1_a: depende de m2_b" in r.stdout
    assert r.returncode == 1


def test_sin_main_del_banco_replica_la_secuencia_del_kernel(tmp_path):
    _, _, _, root = _build(tmp_path, _fuentes(con_main=False))
    assert not os.path.exists(os.path.join(root, "bank_src", "main.py"))
    r, lineas = _run(root, ["--source", "m1_pivot"], tmp_path)
    assert r.returncode == 0, r.stdout + r.stderr
    assert "via=launcher" not in lineas
    args = json.loads(lineas[0].split(" ", 1)[1])
    assert args["model"] == "m1" and args["job"] == "pivot" and args["env"] == "uat"


def test_check_env_prueba_el_import_de_toolbox_kernel_y_de_los_jobs(tmp_path):
    fuentes = _fuentes()
    fuentes.append({"name": P + "jobs/m3/rota/job.py",
                    "code": "import modulo_que_no_existe_bnx\n\ndef run(kernel):\n    pass\n"})
    _, _, _, root = _build(tmp_path, fuentes)
    r = subprocess.run([sys.executable, "check_env.py"], cwd=root, capture_output=True, text=True, timeout=120,
                       env={k: v for k, v in os.environ.items() if k != "JAVA_TOOL_OPTIONS"})
    out = r.stdout + r.stderr
    assert r.returncode == 1
    assert "m3_rota" in out and "modulo_que_no_existe_bnx" in out
    assert "m1_a" not in out.split("FALLA al importar")[1].split("FALTAN")[0]   # los sanos no se reportan
    # y con todo sano, toolbox.kernel y los jobs importan de verdad: sin errores
    (tmp_path / "ok").mkdir()
    _, _, _, root2 = _build(tmp_path / "ok", _fuentes())
    r2 = subprocess.run([sys.executable, "check_env.py"], cwd=root2, capture_output=True, text=True, timeout=120,
                        env={k: v for k, v in os.environ.items() if k != "JAVA_TOOL_OPTIONS"})
    assert r2.returncode == 0, r2.stdout + r2.stderr
