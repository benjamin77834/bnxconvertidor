"""Settings minimos COMPLETOS del DEMO inferidos del codigo (src/mlops_demo/settings_infer.py) y
autodeteccion de bin/settings en el paquete (bank_src/settings). Sin red."""
import ast
import json
import os
import subprocess
import sys
import zipfile
import pytest
from src import mlops_pkg as mp
from src.mlops_demo import settings_infer as si
JOB = '''
import os
from utils.emails_full import Email
def load_tables(kernel, settings, table_name, *args_where):
    info = settings["tables_info"][table_name]
    donde = info.get("where")
    if donde:
        return donde.format(*args_where)
    return kernel.reader.hive_table_to_df(info["database"], info["table"], ", ".join(info["columns"]))
def run(kernel):
    settings = kernel.settings.job.get(kernel.env)
    root = kernel.settings.jobs[kernel.env]["general_root"]
    path = root + settings["working_path"].format("202501")
    parquets = {k: os.path.join(path, k) for k in settings["final_parquets"]}
    lag = settings["lag"]
    start = 12 - lag
    load_tables(kernel, settings, "master")
    load_tables(kernel, settings, "pnl")
    cfg = Email(kernel, settings)
    if settings.get("solo_si_existe") is not None:
        pass
    return parquets["resultado"], start
'''
EMAIL = '''
class Email:
    def __init__(self, kernel, config):
        self.config = config
    def head(self):
        return self.config['model_name'] + self.config.get("working_path").format(1)
    def tail(self):
        if "final_tables" in list(self.config.keys()):
            return self.config["final_tables"]
        elif "otra_clave_opcional" in self.config:
            return self.config["otra_clave_opcional"]
'''
@pytest.fixture
def bank(tmp_path):
    b = tmp_path / "bank_src"
    (b / "jobs" / "m1" / "a").mkdir(parents=True)
    (b / "utils").mkdir()
    (b / "jobs" / "m1" / "a" / "job.py").write_text(JOB)
    (b / "utils" / "emails_full.py").write_text(EMAIL)
    return b
def _infer(bank):
    job = str(bank / "jobs" / "m1" / "a" / "job.py")
    return si.inferir(si.archivos_del_job(job, [str(bank)]), "m1", "a", "uat")
def test_infiere_claves_del_job_y_de_los_modulos_que_importa(bank):
    r = _infer(bank)
    assert r["job"]["model_name"] == "m1"                      # self.config['model_name'] (utils/emails_full.py)
    assert r["job"]["lag"] == 1 and isinstance(r["job"]["lag"], int)
    assert r["job"]["working_path"].endswith("{}/")            # se usa con .format
    assert r["jobs"]["general_root"]                           # kernel.settings.jobs[env]['general_root']
    assert "m1.a" not in r["job"]


def test_tablas_dinamicas_toman_los_literales_que_pasa_el_job(bank):
    t = _infer(bank)["job"]["tables_info"]
    assert sorted(t) == ["master", "pnl"]                      # load_tables(kernel, settings, 'master'|'pnl')
    assert t["master"]["database"] == "demo_db"
    assert t["master"]["table"] == "demo_db.master"
    assert t["master"]["columns"] == ["*"]
    assert "where" not in t["master"]                          # .get('where') es opcional: no se inventa


def test_claves_solo_preguntadas_no_se_inventan(bank):
    r = _infer(bank)["job"]
    assert "otra_clave_opcional" not in r and "solo_si_existe" not in r
    assert "final_tables" not in r or isinstance(r["final_tables"], dict)


def test_lista_y_diccionario_segun_el_uso(bank):
    r = _infer(bank)["job"]
    assert isinstance(r["final_parquets"], list)
    assert "resultado" in r["final_parquets"]                  # parquets['resultado'] sobre {k: ... for k in final_parquets}


def test_generar_escribe_los_json_que_lee_toolbox_settings(bank, tmp_path):
    entradas = [{"model": "m1", "job": "a", "module": "jobs.m1.a.job"}]
    d = tmp_path / "settings"
    inv = si.generar(str(d), entradas, "uat", "/tmp/root", [str(bank)])
    for rel in ("spark.json", "jobs.json", "m1/a.json", "m1/config_custom.json"):
        assert (d / rel).is_file(), rel
    assert json.loads((d / "m1" / "a.json").read_text())["uat"]["model_name"] == "m1"
    assert json.loads((d / "spark.json").read_text())["default"]["spark.yarn.queue"]   # Settings() lo indexa con env != uat
    assert json.loads((d / "jobs.json").read_text())["uat"]["general_root"].startswith("/tmp/root")
    assert any(k.endswith("model_name") for k in inv["m1/a"])   # el reporte lista lo inventado


def test_python38_y_sin_dependencias():
    ast.parse(open(si.__file__, encoding="utf-8").read(), feature_version=(3, 8))
    ast.parse(open(si.__file__.replace("settings_infer", "reporte"), encoding="utf-8").read(), feature_version=(3, 8))


def test_mezclar_faltantes_solo_anade_lo_que_falta():
    real = {"a": 1, "b": {"x": 1}}
    anadidas = si.mezclar_faltantes(real, {"a": 9, "b": {"x": 9, "y": 2}, "c": 3})
    assert real == {"a": 1, "b": {"x": 1, "y": 2}, "c": 3}
    assert sorted(anadidas) == ["b.y", "c"]
# --- autodeteccion de settings en el paquete -----------------------------------------------------
def _convert(code):
    return {"ok": True, "code": "df_out = df", "warnings": [], "unsupported": []}
def test_ruta_settings_acepta_config_bajo_settings_y_rechaza_el_resto():
    assert mp._ruta_settings("proy/bin/settings/rps/pivot.json") == "rps/pivot.json"
    assert mp._ruta_settings("bin/settings/spark.json") == "spark.json"
    assert mp._ruta_settings("proy/bin/settings/x.yaml") == "x.yaml"
    assert mp._ruta_settings("proy/config/otra.json") is None
    assert mp._ruta_settings("proy/bin/settings/../../x.json") is None
    assert mp._ruta_settings("settings.json") is None
def test_el_paquete_incluye_bin_settings_en_bank_src_settings(tmp_path):
    fuentes = [
        {"name": "proy/bin/jobs/m1/a/job.py", "code": JOB},
        {"name": "proy/bin/settings/spark.json", "code": '{"default": {}}'},
        {"name": "proy/bin/settings/m1/a.json", "code": '{"uat": {"model_name": "REAL"}}'},
    ]
    out = tmp_path / "p.zip"
    _, _, rep = mp.build_package_from_sources(fuentes, convert_fn=_convert, include_bank_libs=False,
                                              out_path=str(out), py_target="py3.11")
    nombres = zipfile.ZipFile(out).namelist()
    assert "framework_mlops_v2_pkg/bank_src/settings/spark.json" in nombres
    assert "framework_mlops_v2_pkg/bank_src/settings/m1/a.json" in nombres
    roles = [r.get("role") for r in rep if not r.get("_meta")]
    assert roles.count("settings") == 2
    # el settings json NO se trata como fuente/job
    router = zipfile.ZipFile(out).read("framework_mlops_v2_pkg/framework_mlops_v2/aggregates/router.py").decode()
    assert "settings" not in router.split("_FUENTES")[1].split("\n}")[0]
def test_main_del_paquete_trae_autodeteccion_e_ayuda_de_clave_faltante(tmp_path):
    out = tmp_path / "p.zip"
    mp.build_package_from_sources([{"name": "proy/bin/jobs/m1/a/job.py", "code": JOB}], convert_fn=_convert,
                                  include_bank_libs=False, out_path=str(out), py_target="py3.11")
    main = zipfile.ZipFile(out).read("framework_mlops_v2_pkg/main.py").decode()
    ast.parse(main, feature_version=(3, 8))
    assert "bank_src/settings del paquete (autodetectado)" in main
    assert "FALTA LA CLAVE" in main and "Carpeta bin/settings" in main
    assert "settings_infer" in main
    assert "settings_infer.py" in "".join(zipfile.ZipFile(out).namelist())
# --- demo de punta a punta: sin settings no falla por KeyError de config -----------------------------
KERNEL_PY = '''
class _Log:
    def log_error(self, msg=None): pass
    def log_info(self, msg=None): pass
class Kernel:
    def __init__(self, app_name, log_path, settings_path):
        self.log = _Log(); self.settings_path = settings_path; self.app_name = app_name
    def launch(self, args): self.args = args
'''
JOB_E2E = '''
import json, os
from toolbox.kernel import Kernel
def run(kernel):
    env = kernel.args["env"]
    settings = json.load(open(os.path.join(kernel.settings_path, kernel.args["model"], kernel.args["job"] + ".json")))[env]
    nombre = settings["model_name"] + ":" + settings["tables_info"]["t1"]["table"]
    n = settings["lag"] + 1
    with open(os.environ["BNX_TEST_OUT"], "a") as fh:
        fh.write("%s %s\\n" % (nombre, n))
'''
def test_demo_sin_settings_infiere_y_no_falla_por_keyerror(tmp_path):
    pytest.importorskip("pyspark")
    out = tmp_path / "p.zip"
    mp.build_package_from_sources([
        {"name": "proy/bin/toolbox/kernel.py", "code": KERNEL_PY},
        {"name": "proy/bin/jobs/m1/a/job.py", "code": JOB_E2E},
        {"name": "proy/bin/jobs/m1/a/helper.py", "code": "def f(settings, kernel):\n    return settings['tables_info']['t1']\n"}],
        convert_fn=_convert, include_bank_libs=False, out_path=str(out), py_target="py3.11")
    root = tmp_path / "x"
    zipfile.ZipFile(out).extractall(root)
    pkg = str(root / "framework_mlops_v2_pkg")
    salida = tmp_path / "o.txt"
    salida.write_text("")
    env = {k: v for k, v in os.environ.items() if k not in ("CONF_PATH", "BIN_PATH", "SPARK_CONF_DIR")}
    env.update({"BNX_TEST_OUT": str(salida), "PYTHONDONTWRITEBYTECODE": "1"})
    r = subprocess.run([sys.executable, "main.py", "--demo", "--source", "m1_a"], cwd=pkg, env=env,
                       capture_output=True, text=True, timeout=240)
    assert "FIN OK m1_a" in r.stdout, r.stdout[-1500:] + r.stderr[-800:]
    assert salida.read_text().strip() == "m1:demo_db.t1 2"
    assert "INFERIDOS del codigo" in r.stdout
    rep = json.load(open(os.path.join(pkg, "demo_out", "REPORTE_DEMO.json")))
    assert any(k.endswith("model_name") for k in rep["settings_inventados"]["m1/a"])
