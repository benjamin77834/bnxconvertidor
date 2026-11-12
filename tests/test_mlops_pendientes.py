"""Pendientes del convertidor -> Framework MLOps v2 (reporte de Angel Rivera, 11/11/2026).

1) faltaban cytoolz/unidecode al instalar si el codigo no usaba libs del banco
2) run.sh --source ignoraba el nombre en silencio si no coincidia exacto
3) en modo cluster el 'spark.master' del JSON pisaba el --master yarn
4) los .py sin pandas (toolbox/utils/main/settings...) se reescribian/envolvian ("cortados")
5) el REGISTRY se regeneraba con TODOS los archivos
"""
import ast
import json
import os
import zipfile

import pytest

from src import mlops_pkg as mp

BANK = os.path.join(os.path.dirname(__file__), "..", "mlops22",
                    "170589.DAA.MLOps_RPS_2026-0001-refactor_v1", "bin")
CACHE_WHEELS = os.path.join(mp._BANK_LIBS_CACHE, "wheels")


def _convert(code):
    """Conversor de prueba: no se usa con fuentes sin pandas (deben copiarse tal cual)."""
    return {"ok": True, "code": "df_out = df  # CONVERTIDO", "warnings": [], "unsupported": []}


def _build(tmp_path, sources, **kw):
    out = tmp_path / "pkg.zip"
    _, _, report = mp.build_package_from_sources(
        sources, convert_fn=_convert, include_bank_libs=True, out_path=str(out), **kw)
    z = zipfile.ZipFile(out)
    files = {n[len("framework_mlops_v2_pkg/"):]: n for n in z.namelist()
             if n.startswith("framework_mlops_v2_pkg/")}
    return z, files, [r for r in report if not r.get("_meta")]


def _read(z, files, rel):
    return z.read(files[rel]).decode("utf-8")


# --- 1) dependencias extra -------------------------------------------------

@pytest.mark.skipif(not os.path.isdir(CACHE_WHEELS), reason="sin cache de wheels del banco")
def test_extra_sin_libs_del_banco_incluye_wheels(tmp_path):
    code = "import pandas as pd\nimport cytoolz\nfrom unidecode import unidecode\ndef run(df):\n    return df\n"
    z, files, _ = _build(tmp_path, [{"name": "job_1.py", "code": code}])
    assert "requirements-extra.txt" in files
    assert "requirements-bank.txt" not in files
    # Las wheels open source van en vendor/<serie>/ (solo lo que pip resolvio), tambien
    # en el paquete LIGERO; vendor/bank/ queda solo para las mex-lib del banco.
    wheels = [os.path.basename(f) for f in files if f.startswith("vendor/py")]
    assert any(w.startswith("cytoolz-") for w in wheels)
    assert any(w.lower().startswith("unidecode-") for w in wheels)
    assert any(w.startswith("toolz-") for w in wheels)          # dependencia de cytoolz
    assert any(w.startswith("pandas-") for w in wheels)          # deps del framework
    assert not any(w.startswith("pyspark-") for w in wheels)     # ligero: sin PySpark
    assert not any(f.startswith("vendor/bank/") for f in files)  # sin libs internas


@pytest.mark.skipif(not os.path.isdir(CACHE_WHEELS), reason="sin cache de wheels del banco")
def test_ligero_trae_lo_necesario_y_no_todo_el_cache(tmp_path):
    code = "import pandas as pd\nfrom toolbox.kernel import Kernel\ndef run(df):\n    return df\n"
    z, files, rep = _build(tmp_path, [{"name": "job_1.py", "code": code}], py_target="py38-311")
    vend = [f for f in files if f.startswith("vendor/")]
    assert not any(os.path.basename(f).startswith(("xgboost-", "scipy-", "scikit_learn-")) for f in vend)
    # Python 3.8 (el del banco): pandas/numpy cp38 desde el cache del banco
    assert any("pandas-1.3.1-cp38" in f for f in vend)
    assert all(os.path.basename(f).lower().startswith("mex") for f in vend
               if f.startswith("vendor/bank/") and f.endswith((".whl", ".tar.gz")))
    meta = [r for r in mp.build_package_from_sources(
        [{"name": "job_1.py", "code": code}], convert_fn=_convert, py_target="py38-311",
        out_path=str(tmp_path / "b.zip"))[2] if r.get("_meta")][0]
    # ~65-125 MB segun cuantas versiones (3.8-3.11) tenga el cache; nunca los ~350 MB de antes
    assert meta["vendor_mb"] < 200 and meta["vendor_missing"] is False
    for rel in ("setup.sh", "run.sh"):
        assert "requirements-sin-spark" in _read(z, files, "setup.sh") or rel == "run.sh"


# --- 2) --source -----------------------------------------------------------

@pytest.fixture(scope="module")
def resolver():
    tree = ast.parse(mp._MAIN_PY)
    fn = [n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == "_resolver_source"]
    ns = {"os": os, "REGISTRY": {"job_3": object, "job_4": object}}
    exec(compile(ast.Module(body=fn, type_ignores=[]), "main.py", "exec"), ns)
    return ns["_resolver_source"]


def test_source_job_tolerante(resolver, capsys):
    tablas = {"universe": {}, "cycle": {}}
    for crudo in ("job_3", "job_3.py", "JOB_3", "jobs/rps/job_3.py"):
        assert resolver(crudo, tablas, True) == "job_3"
    assert "JOB del REGISTRY" in capsys.readouterr().out


def test_source_tabla_del_banco(resolver, capsys):
    assert resolver("Universe", {"universe": {}}, True) == "universe"
    assert "TABLA de tables_info" in capsys.readouterr().out


def test_source_desconocida_se_detiene(resolver):
    with pytest.raises(SystemExit, match="no es una tabla del config ni un job"):
        resolver("pivot", {"universe": {}}, True)


def test_source_cfg_no_banco_requiere_registry(resolver):
    # cfg.json propio: una fuente que no esta en el REGISTRY antes se saltaba en silencio
    with pytest.raises(SystemExit):
        resolver("solo_tabla", {"solo_tabla": {}}, False)
    assert resolver("job_4", {"job_4": {}}, False) == "job_4"


# --- 3) cluster / YARN -----------------------------------------------------

def test_cluster_no_pisa_master_de_spark_submit():
    assert 'builder.master(scfg_spark["master"])' not in mp._MAIN_PY
    assert "applicationId" in mp._MAIN_PY            # diagnostico de donde quedo la sesion
    assert 'YARN_CONF_DIR' in mp._RUN_SH


# --- 4) y 5) jobs vs modulos de apoyo --------------------------------------

def _src(rel):
    with open(os.path.join(BANK, rel), encoding="utf-8", errors="replace") as fh:
        return fh.read()


@pytest.mark.skipif(not os.path.isdir(BANK), reason="sin el proyecto del banco de ejemplo")
def test_registry_y_modulos_de_apoyo_exactos(tmp_path):
    fuentes = [
        {"name": "job_3.py", "code": _src("jobs/rps/pivot/job.py")},
        {"name": "job_4.py", "code": _src("jobs/rps/datapull/job.py")},
        {"name": "kernel.py", "code": _src("toolbox/kernel.py")},
        {"name": "log.py", "code": _src("toolbox/log.py")},
        {"name": "settings.py", "code": _src("toolbox/settings.py")},
        {"name": "overwrite.py", "code": _src("toolbox/overwrite.py")},
        {"name": "email.py", "code": _src("toolbox/email.py")},
        {"name": "main.py", "code": open(os.path.join(BANK, "..", "main.py"), encoding="utf-8").read()},
    ]
    z, files, rep = _build(tmp_path, fuentes, registry=["job_3", "JOB_4.py"])
    router = _read(z, files, "framework_mlops_v2/aggregates/router.py")
    reg = ast.literal_eval(router.split("REGISTRY = ")[1].split("}")[0].replace(
        "Job3Aggregate", "1").replace("Job4Aggregate", "1") + "}")
    assert set(reg) == {"job_3", "job_4"}                         # 5) solo los jobs elegidos
    # 4) apoyo: copia EXACTA. Los que otro archivo importa como toolbox.<x> van a su
    #    PAQUETE (bank_src/toolbox/), asi 'from toolbox.kernel import Kernel' funciona
    #    aunque el servidor no tenga toolbox en cache; el resto, sueltos en bank_src/.
    for f in fuentes[2:]:
        rel = ("bank_src/toolbox/" + f["name"]) if f["name"] != "main.py" else "bank_src/main.py"
        assert _read(z, files, rel) == f["code"], rel
        assert "framework_mlops_v2/aggregates/" + f["name"] not in files
    assert "bank_src/toolbox/__init__.py" in files
    por = {r["name"]: r for r in rep}
    assert por["kernel.py"]["role"] == "apoyo" and por["kernel.py"]["paquete"] == "toolbox"
    assert "aviso" not in por["email.py"]   # dentro del paquete toolbox ya no choca con stdlib
    assert por["job_3.py"]["job_kernel"] and por["job_4.py"]["job_kernel"]
    # job sin pandas registrado: NO pasa por el conversor (conserva comentarios)
    agg = _read(z, files, "framework_mlops_v2/aggregates/job_4.py")
    assert "CONVERTIDO" not in agg and "RPS Data Pull Proccess" in agg
    # todo lo generado es Python valido
    for rel in ("main.py", "check_env.py", "framework_mlops_v2/aggregates/router.py",
                "framework_mlops_v2/aggregates/job_3.py", "framework_mlops_v2/aggregates/job_4.py"):
        ast.parse(_read(z, files, rel))


def test_registry_none_registra_todo_como_antes(tmp_path):
    fuentes = [{"name": "a.py", "code": "import pandas as pd\ndef run(df):\n    return df\n"},
               {"name": "util.py", "code": "def ayuda():\n    return 1\n"}]
    z, files, rep = _build(tmp_path, fuentes)
    router = _read(z, files, "framework_mlops_v2/aggregates/router.py")
    assert '"a":' in router and '"util":' in router
    assert not any(f.startswith("bank_src/") for f in files)
    # el archivo con pandas SI pasa por el conversor; el que no, se copia tal cual
    assert "CONVERTIDO" in _read(z, files, "framework_mlops_v2/aggregates/a.py")
    assert "CONVERTIDO" not in _read(z, files, "framework_mlops_v2/aggregates/util.py")


def test_solo_modulos_de_apoyo_no_devuelve_paquete_de_ejemplo(tmp_path):
    z, files, rep = _build(tmp_path, [{"name": "utils.py", "code": "X = 1\n"}], registry=[])
    assert _read(z, files, "bank_src/utils.py") == "X = 1\n"
    assert "main.py" in files


# --- dependencias indirectas (encontradas al probar con el proyecto real) ----

@pytest.mark.skipif(not os.path.isdir(os.path.join(mp._BANK_LIBS_CACHE, "pkgcode")),
                    reason="sin cache de codigo de path del banco")
def test_paquetes_de_path_llevan_init_y_fachada_mex_lib_cs(tmp_path):
    # job_4 importa bnmxverse; su data_pull.py importa mex_lib_cs y utils.emails_full
    code = "from bnmxverse.data_pull import DataPull\nfrom toolbox.kernel import Kernel\n\ndef run(kernel):\n    pass\n"
    z, files, _ = _build(tmp_path, [{"name": "job_4.py", "code": code}])
    tops = {f.split("/")[3] for f in files if f.startswith("vendor/bank/pkgcode/") and f.count("/") >= 4}
    for top in tops:   # utils/, bnmxverse/, toolbox/... como paquetes normales
        assert f"vendor/bank/pkgcode/{top}/__init__.py" in files, top
    assert "mex_lib_cs/__init__.py" in files


def test_check_env_importa_los_jobs_de_verdad():
    assert "def _probar_jobs" in mp._CHECK_ENV
    assert "_probar_jobs()" in mp._CHECK_ENV
    ast.parse(mp._CHECK_ENV)


# --- version EXACTA de Python (Linux): lo mas ligero con todas las librerias -------

def test_versiones_target():
    assert mp._versiones_target("py3.8") == {"py38-311": ["3.8"]}
    assert mp._versiones_target("py3.12") == {"py312plus": ["3.12"]}
    assert mp._versiones_target("py38-311") == {"py38-311": ["3.8", "3.9", "3.10", "3.11"]}
    assert set(mp._versiones_target("all")) == {"py38-311", "py312plus"}


@pytest.mark.skipif(not os.path.isdir(CACHE_WHEELS), reason="sin cache de wheels del banco")
@pytest.mark.parametrize("tgt,abi", [("py3.8", "cp38"), ("py3.12", "cp312")])
def test_version_exacta_solo_lo_necesario(tmp_path, tgt, abi, monkeypatch):
    monkeypatch.setenv("BNX_NO_DOWNLOAD", "1")
    code = "import pandas as pd\nimport cytoolz\ndef run(df):\n    return df\n"
    z, files, _ = _build(tmp_path, [{"name": "job_1.py", "code": code}], py_target=tgt)
    whl = [os.path.basename(f) for f in files if f.endswith(".whl")]
    assert _read(z, files, "vendor/PYTHON_TARGET").strip() == tgt[2:]
    assert not any("aarch64" in w for w in whl)                       # solo x86_64
    otras = [w for w in whl if "-cp3" in w and f"-{abi}-" not in w and "abi3" not in w]
    assert not otras, otras                                            # solo esa version
    dists = [w.split("-")[0].lower() for w in whl]
    assert len(dists) == len(set(dists))                               # sin duplicadas
    assert {"pandas", "numpy", "cytoolz", "toolz"} <= set(dists)
    assert "pyspark" not in dists                                      # ligero


def test_setup_sh_pyspark_online_y_respeta_cluster():
    s = mp._SETUP_SH
    assert 'BNX_SPARK:-}" = "cluster"' in s                      # cluster: no instala pyspark
    assert "pyspark==3.5.6" in s and "pyspark==4.0.0" in s       # pin por serie
    assert 'pip install --retries 1 --timeout 30 "$SPARK_PIN" py4j' in s
    assert "[AVISO] No se pudo instalar PySpark por internet" in s
    assert "BNX_SPARK=cluster bash run.sh" in s                  # alternativa en el aviso
    assert 'PYSPARK_PYTHON="$PWD/.venv/bin/python"' in mp._RUN_SH
    assert 'PYSPARK_DRIVER_PYTHON="$PWD/.venv/bin/python"' in mp._RUN_SH
