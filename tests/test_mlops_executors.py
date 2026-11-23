"""Python en los EXECUTORS (UDF): deteccion, empaquetado de site-packages, probe, run.sh y mensaje del error.
Sin red ni YARN: el spark-submit del cluster es un script falso."""
import ast
import json
import os
import stat
import subprocess
import sys
import tarfile
import zipfile

import pytest

from src import bank_compat as bc
from src import bnx_sparkconf as bs
from src import mlops_pkg as mp

# Imita el PATRON de la UDF de un job del banco (no es codigo del banco).
UDF_FIXTURE = '''
import unidecode
class Job:
    def _quita(self):
        def quita(s):
            if s is None:
                return ""
            return unidecode.unidecode(s).lower()
        self.sqlContext.udf.register("quita", quita)
'''
ERROR_WORKER = (
    "org.apache.spark.SparkException: Job aborted due to stage failure: Lost task 0.3 in stage 451.0 (executor 1): "
    "org.apache.spark.api.python.PythonException: Traceback (most recent call last):\n"
    "  File \"/data/3/yarn/nm/usercache/u/appcache/application_1/container_1/pyspark.zip/pyspark/worker.py\", line 1, in main\n"
    "    command = read_command(pickleSer, infile)\n"
    "  File \".../pyspark/cloudpickle/cloudpickle.py\", line 1, in subimport\n"
    "    __import__(name)\nModuleNotFoundError: No module named 'numpy'\n")


def test_detecta_udf_register_en_codigo_y_en_wheel(tmp_path):
    hs = bs.detectar_python_en_workers(UDF_FIXTURE)
    assert any(h["patron"] == "udf" and ".udf.register" in h["codigo"] for h in hs)
    modelo = tmp_path / "bank_src"
    modelo.mkdir()
    (modelo / "dp.py").write_text(UDF_FIXTURE)
    wh = tmp_path / "wheels"
    wh.mkdir()
    with zipfile.ZipFile(wh / "mex_lib_x-1-py3-none-any.whl", "w") as z:
        z.writestr("lib_x/core.py", "def f(self):\n    self.sqlContext.udf.register('g', g, DoubleType())\n")
        z.writestr("lib_x/otro.py", "x = 1\n")
    r = bs.escanear_workers([str(modelo)], str(wh))
    archivos = sorted(h["archivo"] for h in r)
    assert any(a.endswith("dp.py") for a in archivos)
    assert any(a.endswith("whl!lib_x/core.py") for a in archivos)
    assert not any("otro.py" in a for a in archivos)


def _fake_sp(tmp_path):
    sp = tmp_path / "sp"
    for d in ("numpy", "pandas", "pyspark/sql", "py4j", "numpy/__pycache__", "unidecode"):
        (sp / d).mkdir(parents=True, exist_ok=True)
        (sp / d / "__init__.py").write_text("x = 1\n")
    (sp / "numpy" / "__pycache__" / "a.cpython-311.pyc").write_bytes(b"x")
    (sp / "numpy-1.26.4.dist-info").mkdir(exist_ok=True)
    (sp / "pyspark-3.5.dist-info").mkdir(exist_ok=True)
    (sp / "py4j-0.10.dist-info").mkdir(exist_ok=True)
    (sp / "modulo_suelto.py").write_text("y = 2\n")
    return str(sp)


def test_empaqueta_site_packages_sin_pyspark_ni_pycache_y_cachea(tmp_path):
    sp = _fake_sp(tmp_path)
    ruta, hv, mb, reus = bs.empaquetar_deps(str(tmp_path / "out"), sp)
    nombres = tarfile.open(ruta).getnames()
    assert "numpy/__init__.py" in nombres and "modulo_suelto.py" in nombres and "unidecode/__init__.py" in nombres
    assert not [n for n in nombres if n.startswith(("pyspark", "py4j")) or "__pycache__" in n or n.endswith(".pyc")]
    assert not reus
    ruta2, hv2, _, reus2 = bs.empaquetar_deps(str(tmp_path / "out"), sp)
    assert reus2 and ruta2 == ruta and hv2 == hv
    os.makedirs(os.path.join(sp, "nuevo-1.0.dist-info"))   # el venv cambia -> otro hash
    ruta3, hv3, _, reus3 = bs.empaquetar_deps(str(tmp_path / "out"), sp)
    assert hv3 != hv and not reus3 and not os.path.exists(ruta)


def test_evaluar_probe_mensaje_con_opciones():
    mal = {"workers": [{"python": "/usr/bin/python3", "version": [3, 6, 8], "mods": {"numpy": None}}]}
    est, msg = bs.evaluar_probe(mal, "3.11", ["numpy"])
    assert est is False
    for frase in ("BNX_EXECUTOR_PYTHON=/usr/bin/python3.11", "BNX_SPARK=local", "F.translate", "translate(", "quita_acentos"):
        assert frase in msg
    est, _ = bs.evaluar_probe({"error": "Exception: Python in worker has different version 3.6 than that in driver 3.11"}, "3.11", [])
    assert est is False
    est, _ = bs.evaluar_probe({"workers": [{"python": "/p", "version": [3, 11, 4], "mods": {"numpy": "/x"}}]}, "3.11", ["numpy"])
    assert est is True
    est, _ = bs.evaluar_probe({"workers": [{"python": "/p", "version": [3, 11, 4], "mods": {"numpy": None}}]}, "3.11", ["numpy"])
    assert est is False
    assert bs.evaluar_probe({"error": "YARN caido"}, "3.11", [])[0] is None


def test_error_de_executor_se_traduce_al_formato_de_faltantes(tmp_path, monkeypatch):
    wj = tmp_path / "w.json"
    wj.write_text(json.dumps({"hallazgos": [
        {"archivo": "bank_src/bnmxverse/data_pull.py", "linea": 434, "patron": "udf", "codigo": 'self.sqlContext.udf.register("quita_acentos", q)'}]}))
    monkeypatch.setenv("BNX_WORKERS_JSON", str(wj))
    monkeypatch.setenv("BNX_FALTANTES_DIR", str(tmp_path))
    monkeypatch.setenv("LOG_FILE_PATH", str(tmp_path / "logs" / "j" / "job.log"))
    os.makedirs(tmp_path / "logs" / "j")
    info = bc.traducir_excepcion(Exception(ERROR_WORKER), "rps_datapull")
    assert info["tipo"] == "executors" and info["modulo"] == "numpy"
    txt = bc.registrar_faltante(info, job="rps_datapull")
    assert txt.startswith("FALTA numpy en los EXECUTORS (Python de los workers del cluster)")
    assert "Lo necesita: rps_datapull -> bank_src/bnmxverse/data_pull.py:434" in txt
    assert "Por que: el job ejecuta Python en los workers (UDF)" in txt
    for frase in ("BNX_DEPS_EXECUTORS=1", "BNX_EXECUTOR_PYTHON=/usr/bin/python3.11", "BNX_SPARK=local", "Pasos"):
        assert frase in txt
    assert bc.leer_faltantes()[0]["tipo"] == "executors"
    assert "FALTA numpy" in (tmp_path / "logs" / "j" / "job.log").read_text()
    # un ModuleNotFoundError del DRIVER (sin worker.py/cloudpickle) no es de executors
    assert bc.traducir_error_executor(ModuleNotFoundError("No module named 'numpy'")) is None


# ---------------------------------------------------------------- run.sh generado
def _convert(code):
    return {"ok": True, "code": "df_out = df  # CONVERTIDO", "warnings": [], "unsupported": []}


FUENTES = [{"name": "u.py", "code": "from pyspark.sql.functions import udf\nf = udf(lambda x: x)\ndf_out = df\n"}]


def _pkg(tmp_path, fuentes=None):
    out = tmp_path / "pkg.zip"
    mp.build_package_from_sources(fuentes or FUENTES, convert_fn=_convert, include_bank_libs=False, out_path=str(out), py_target="py3.11")
    zipfile.ZipFile(out).extractall(tmp_path / "pkg")
    return str(tmp_path / "pkg" / "framework_mlops_v2_pkg")


FAKE = '''#!/bin/bash
if [[ " $* " == *" --probe "* ]]; then
  echo "PROBE-CALL: $*" >> "$FAKE_LOG"
  while [ $# -gt 0 ]; do if [ "$1" = "--out" ]; then OUT="$2"; fi; shift; done
  if [ "$FAKE_PROBE" = "bad" ]; then echo '{"estado": false, "mensaje": "malo"}' > "$OUT"; echo "[probe] Python 3.6 en los workers"; exit 3; fi
  echo '{"estado": true, "mensaje": "ok"}' > "$OUT"; exit 0
fi
echo "ENV:BNX_UDF_NATIVAS=${BNX_UDF_NATIVAS:-}"
for a in "$@"; do echo "ARG:$a"; done
'''


def _run(tmp_path, pkg, **extra):
    vb = os.path.join(pkg, ".venv", "bin")
    os.makedirs(vb, exist_ok=True)
    open(os.path.join(vb, "python"), "w").write('#!/bin/bash\nexec "%s" "$@"\n' % sys.executable)
    os.chmod(os.path.join(vb, "python"), 0o755)
    open(os.path.join(vb, "activate"), "w").write('export PATH="$PWD/.venv/bin:$PATH"\n')
    fake = tmp_path / "fake-submit"
    fake.write_text(FAKE)
    fake.chmod(fake.stat().st_mode | stat.S_IEXEC)
    log = tmp_path / "fake.log"
    env = {k: v for k, v in os.environ.items() if not k.startswith(("BNX_", "SPARK_", "CONF_PATH", "FAKE_"))}
    env.update(BNX_SPARK="cluster", BNX_SPARK_SUBMIT=str(fake), HADOOP_CONF_DIR="/x", FAKE_LOG=str(log),
               BNX_DEPS_SITE_PACKAGES=_fake_sp(tmp_path))
    env.update(extra)
    r = subprocess.run(["bash", "run.sh", "--extract-only"], cwd=pkg, env=env, capture_output=True, text=True, timeout=120)
    args = [l[4:] for l in r.stdout.splitlines() if l.startswith("ARG:")]
    return r, args, (log.read_text() if log.exists() else "")


def test_run_sh_trae_probe_y_pasa_archives_y_pythonpath(tmp_path):
    pkg = _pkg(tmp_path)
    assert subprocess.run(["bash", "-n", os.path.join(pkg, "run.sh")]).returncode == 0
    r, args, log = _run(tmp_path, pkg, BNX_SPARK_CONF="spark.executorEnv.PYTHONPATH=pyspark.zip:py4j.zip",
                        BNX_EXECUTOR_PYTHON="/usr/bin/python3.11")
    assert r.returncode == 0, r.stdout + r.stderr
    assert "PROBE-CALL" in log and "--probe" in log and "--archives" in log        # el probe viaja con el tgz
    i = args.index("--archives")
    assert args[i + 1].endswith(".tar.gz#bnxdeps") and ".bnx_deps/bnxdeps-" in args[i + 1]
    confs = [args[j + 1] for j, a in enumerate(args) if a == "--conf"]
    assert "spark.executorEnv.PYTHONPATH=./bnxdeps:pyspark.zip:py4j.zip" in confs      # antepone, conserva el del cluster
    assert "spark.pyspark.python=/usr/bin/python3.11" in confs
    assert args[-1] == "--extract-only" and "main.py" in args
    # segunda corrida: el resultado del probe esta cacheado
    r2, args2, log2 = _run(tmp_path, pkg, BNX_EXECUTOR_PYTHON="/usr/bin/python3.11")
    assert r2.returncode == 0 and "(cache)" in r2.stdout and log2.count("PROBE-CALL") == 1


def test_run_sh_no_corre_si_el_probe_dice_que_no_y_se_puede_forzar(tmp_path):
    pkg = _pkg(tmp_path)
    r, args, _ = _run(tmp_path, pkg, FAKE_PROBE="bad")
    assert r.returncode == 1 and not args and "No se lanza el job" in r.stderr
    r, args, _ = _run(tmp_path, pkg, FAKE_PROBE="bad", BNX_PROBE_IGNORAR="1", BNX_PROBE_FORZAR="1")
    assert r.returncode == 0 and "--archives" in args


def test_run_sh_deps_desactivable(tmp_path):
    pkg = _pkg(tmp_path)
    r, args, log = _run(tmp_path, pkg, BNX_DEPS_EXECUTORS="0")
    assert r.returncode == 0 and "--archives" not in args and "PROBE-CALL" not in log
    assert "BNX_DEPS_EXECUTORS=0" in r.stdout


def test_paquete_trae_probe_workers_y_notas(tmp_path):
    pkg = _pkg(tmp_path)
    src = open(os.path.join(pkg, "probe_workers.py"), encoding="utf-8").read()
    ast.parse(src, feature_version=(3, 6))
    assert "range(8), 8" in src and "numpy" in src and "pandas" in src
    notas = open(os.path.join(pkg, "NOTAS_EJECUCION.md"), encoding="utf-8").read()
    for frase in ("probe_workers.py", "BNX_DEPS_EXECUTORS=0", "BNX_EXECUTOR_PYTHON", "spark.executorEnv.PYTHONPATH=./bnxdeps",
                  "--archives", "translate(", "No module named 'numpy'"):
        assert frase in notas
    assert "--conf spark.pyspark.python=/usr/bin/python3.11 probe_workers.py" in notas
    for f in (mp._RUN_SH,):
        assert "--probe" in f and "bnxdeps" in f and "BNX_DEPS_EXECUTORS" in f


FUENTE_NATIVA = [{"name": "q.py", "code": "from pyspark.sql.functions import udf\nimport unidecode\n"
                  "def q(s):\n    if s is None:\n        return ''\n    return unidecode.unidecode(s).lower()\n"
                  "f = udf(q)\ndf_out = df\n"}]


def test_probe_malo_pero_todas_las_udf_nativizables_sigue_con_udf_nativas(tmp_path):
    import shutil
    pkg = _pkg(tmp_path, FUENTE_NATIVA)
    shutil.copy(bc.__file__, os.path.join(pkg, "bank_compat.py"))     # viaja asi en los paquetes con libs del banco
    r, args, _ = _run(tmp_path, pkg, FAKE_PROBE="bad")
    assert r.returncode == 0, r.stdout + r.stderr
    assert "TODAS las UDF detectadas se cambian por expresiones nativas" in r.stdout
    assert "ENV:BNX_UDF_NATIVAS=1" in r.stdout and "main.py" in args
    hs = json.load(open(os.path.join(pkg, ".bnx_workers_python.json")))["hallazgos"]
    assert hs and all(h["nativa"] for h in hs) and hs[0]["udf"] == "q"
    # BNX_UDF_NATIVAS=0: no se intenta y el probe malo detiene la corrida
    r, args, _ = _run(tmp_path, pkg, FAKE_PROBE="bad", BNX_UDF_NATIVAS="0", BNX_PROBE_FORZAR="1")
    assert r.returncode == 1 and not args
