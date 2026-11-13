"""Ruta de entrada de los Input File ('NOT SET'), coincidencia job <-> datos sinteticos y
columnas detectadas desde helpers / col() / where."""
import os
import re
import sys

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from src import orquestador as o
from src.codegen import params_runtime as pr

PARAMS_SRC = '''class PARAMS:
    BASE_PATH = os.environ.get("BNX_BASE_PATH", "s3://x")
    V_MF_FILE_NAME = os.environ.get("V_MF_FILE_NAME", '$ECS_FILE.DAT')
    V_NAME = os.environ.get("V_NAME", 'mi archivo.dat')
    V_DIR = os.environ.get("V_DIR", 'in')
'''


def _plan(job):
    return {"plan": "t.plan", "nombre": "t", "origen": "plan", "direccion": "prior",
            "ejecucion": {"modo": "python", "spark_args": [], "base_path": "", "env": {}},
            "steps": [{"id": "t1", "name": "j", "action": {"type": "graph", "target": str(job),
                                                           "status": "ok", "source": "x.mp"},
                       "depends_on": [], "dep_flags": {}, "solo_en_fallo": False,
                       "enabled": True, "continue_on_error": False}], "enlaces": []}


def _job(tmp_path, body, name="job_spark.py"):
    p = tmp_path / name
    p.write_text(PARAMS_SRC + body, encoding="utf-8")
    return p


# --- _bnx_raw_name / resolve_raw_name ---------------------------------------

def test_not_set_y_ecs_caen_al_nombre_del_nodo():
    n, av = pr.resolve_raw_name("${V_MF_FILE_NAME}", "V8S5_Src", {"V_MF_FILE_NAME": "$ECS_FILE.DAT"})
    assert n == "V8S5_Src" and av and "nombre del nodo" in av[0]
    assert pr.resolve_raw_name("NOT SET", "Nodo", {})[0] == "Nodo"
    assert pr.resolve_raw_name("${V_X}", "Nodo", {"V_X": "NOT SET"})[0] == "Nodo"
    assert pr.resolve_raw_name("${V_X}", "Nodo", {"V_X": ""})[0] == "Nodo"


def test_ruta_por_parametro_y_saneado():
    d = {"V_NAME": "mi archivo.dat", "V_DIR": "in"}
    assert pr.resolve_raw_name("${V_DIR}/${V_NAME}", "N", d)[0] == "in/mi_archivo.dat"
    assert pr.resolve_raw_name("$V_NAME", "N", d)[0] == "mi_archivo.dat"
    # el entorno manda, igual que en el job
    assert pr.resolve_raw_name("$V_NAME", "N", d, env={"V_NAME": "otro.csv"})[0] == "otro.csv"


def test_resolve_raw_name_no_deja_estado():
    antes = (dict(pr._BNX_RAW), dict(pr._BNX_DONE))
    pr.resolve_raw_name("${A}", "N", {"A": "x"})
    assert (pr._BNX_RAW, pr._BNX_DONE) == antes


def test_fragmento_solo_con_parametros_simples():
    assert pr.raw_path_fragment("$\\{V_X\\}", "Nodo") == "{_bnx_raw_name('${V_X}', 'Nodo')}"
    assert pr.raw_path_fragment("datos/fijo.dat", "Nodo") is None
    assert pr.raw_path_fragment("$[string_concat(A,\"x\")]", "Nodo") is None


# --- nombre usado por el job == nombre que crea generar_datos ----------------

def test_job_y_datagen_coinciden(tmp_path):
    job = _job(tmp_path,
               'src_df = spark.read.parquet(f"{PARAMS.BASE_PATH}/raw/'
               '{_bnx_raw_name(\'${V_MF_FILE_NAME}\', \'Src_Nodo\')}")\n'
               'b_df = spark.read.parquet(f"{PARAMS.BASE_PATH}/raw/'
               '{_bnx_raw_name(\'${V_DIR}/${V_NAME}\', \'B\')}")\n'
               'x = src_df.where("edad > 3")\n')
    io = o.parse_job_io(str(job))
    assert [r["ruta"] for r in io["lee"]] == ["raw/Src_Nodo", "raw/in/mi_archivo.dat"]
    assert all(r["resuelto"] for r in io["lee"])
    plan = _plan(job)
    base = tmp_path / "base"
    assert sorted(o.entradas_faltantes(plan, str(base))) == ["raw/Src_Nodo", "raw/in/mi_archivo.dat"]
    rep = o.generar_datos(plan, str(base), n_rows=4)
    assert {r["ruta"] for r in rep if r["estado"] == "generado"} == {"raw/Src_Nodo", "raw/in/mi_archivo.dat"}
    assert (base / "raw" / "Src_Nodo").is_dir() and (base / "raw" / "in" / "mi_archivo.dat").is_dir()
    assert o.entradas_faltantes(plan, str(base)) == []


def test_codigo_generado_y_runtime_dan_el_mismo_nombre(tmp_path):
    """El job real (runtime incrustado) y resolve_raw_name devuelven lo mismo."""
    ns = {"os": os, "re": re}
    exec(PARAMS_SRC, ns)
    exec(pr.runtime_source(), ns)
    ns["_bnx_resolve_params"](ns["PARAMS"])
    for path in ("${V_MF_FILE_NAME}", "${V_DIR}/${V_NAME}", "NOT SET"):
        defaults = {"V_MF_FILE_NAME": "$ECS_FILE.DAT", "V_NAME": "mi archivo.dat", "V_DIR": "in"}
        assert ns["_bnx_raw_name"](path, "Nodo") == pr.resolve_raw_name(path, "Nodo", defaults)[0]


def test_ya_no_se_emite_not_set():
    """main.py: un parametro declarado 'NOT SET' en el .mp no sustituye a la referencia."""
    mp = os.path.join(ROOT, "abinitio", "NUEVONUEVO", "T002_File_To_Dataset 1.mp")
    if not os.path.exists(mp):
        pytest.skip("proyecto de ejemplo no disponible")
    import subprocess
    out = os.path.join(os.environ.get("TMPDIR", "/tmp"), "bnx_notset_spark.py")
    try:
        subprocess.run([sys.executable, os.path.join(ROOT, "main.py"), "--project", mp, "--output", out,
                        "--target", "spark"], cwd=ROOT, capture_output=True, timeout=300)
        code = open(out, encoding="utf-8").read()
    finally:
        if os.path.exists(out):
            os.remove(out)
    assert "raw/NOT SET" not in code
    assert "_bnx_raw_name('${V_MF_FILE_NAME}', 'V8S5_Src_DRI_SF')" in code


# --- columnas -----------------------------------------------------------------

def test_columnas_desde_helper_col_where_y_join():
    code = '''a_df = spark.read.parquet(f"{PARAMS.BASE_PATH}/raw/a")
b_df = spark.read.parquet(f"{PARAMS.BASE_PATH}/raw/b")
f_df = filter_by_expression_hdr_trl(a_df, "FileRead", 1, 3, ["HDR", "TRL"])
g_df = f_df.where("Monto > 10")
h_df = g_df.withColumn("z", F.col("Otra"))
j_df = h_df.join(b_df, on="Llave", how="inner")
k_df = j_df.select(df_x["Idx"]) if False else j_df
s_df = _bnx_safe_col(a_df, "creada", "1")
'''
    marcas = {}
    r = o._columnas_por_fuente(code, ["a", "b"], marcas)
    assert set(r["a"]) >= {"FileRead", "Monto", "Otra", "Llave"}
    assert r["a"]["Monto"] == "int"
    assert "Llave" in r["b"]
    assert "creada" not in r["a"] and "z" not in r["a"]
    assert marcas["a"]["FileRead"] == (1, 3, ["HDR", "TRL"])


def test_sin_col1_col3_cuando_hay_columnas_y_hdr_trl(tmp_path):
    pq = pytest.importorskip("pyarrow.parquet")
    job = _job(tmp_path,
               'src_df = spark.read.parquet(f"{PARAMS.BASE_PATH}/raw/src")\n'
               'f_df = filter_by_expression_hdr_trl(src_df, "FileRead", 1, 3, ["HDR", "TRL"])\n')
    base = tmp_path / "base"
    rep = o.generar_datos(_plan(job), str(base), n_rows=6)
    assert rep[0]["estado"] == "generado"
    assert rep[0]["columnas"] == ["FileRead:string"]
    filas = pq.read_table(str(base / "raw" / "src")).to_pylist()
    vals = [f["FileRead"] for f in filas]
    assert vals[0].startswith("HDR") and vals[-1].startswith("TRL")
    assert any(v.startswith("DAT") for v in vals)
    # lo que deja pasar el filtro del job
    assert [v for v in vals if v[:3] not in ("HDR", "TRL")]


def test_sin_columnas_detectadas_sigue_el_relleno(tmp_path):
    job = _job(tmp_path, 'src_df = spark.read.parquet(f"{PARAMS.BASE_PATH}/raw/src")\n')
    rep = o.generar_datos(_plan(job), str(tmp_path / "base"), n_rows=2)
    assert rep[0]["estado"] == "generado" and rep[0]["columnas"]


def test_preflight_avisa_con_ruta_exacta(tmp_path):
    from src import orq_runner as rn
    job = _job(tmp_path,
               'src_df = spark.read.parquet(f"{PARAMS.BASE_PATH}/raw/'
               '{_bnx_raw_name(\'${V_MF_FILE_NAME}\', \'Src_Nodo\')}")\n')
    base = tmp_path / "base"
    plan = _plan(job)
    p = {"modo": "python", "base_path": str(base), "paso": None, "desde": None, "permitir_remotos": False}
    chk = [c for c in rn.preflight(plan, p) if c["id"] == "entradas"][0]
    assert chk["nivel"] == "warn"
    assert os.path.join(str(base), "raw", "Src_Nodo") in chk["msg"]
    assert "Datos sint" in chk["ayuda"]
