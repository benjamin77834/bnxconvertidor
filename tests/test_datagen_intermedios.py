"""Datos sinteticos: solo entradas EXTERNAS (no los intermedios que produce el plan), columnas y
tipos desde el DML, tipos inferidos por uso, sin alias de join ni col1..col3, y valores que
pasan los filtros del job."""
import json
import os
import sys
import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
from src import orquestador as o

pq = pytest.importorskip("pyarrow.parquet")

PARAMS_SRC = '''class PARAMS:
    BASE_PATH = os.environ.get("BNX_BASE_PATH", "s3://x")
'''


def _leer(base, ruta):
    return pq.read_table(os.path.join(str(base), *ruta.split("/"))).to_pylist()


def _job(d, nombre, lee, escribe, extra=""):
    d.mkdir(parents=True, exist_ok=True)
    p = d / f"{nombre}_spark.py"
    cuerpo = PARAMS_SRC
    for i, r in enumerate(lee):
        cuerpo += f'in{i}_df = spark.read.parquet(f"{{PARAMS.BASE_PATH}}/raw/{r}")\n'
    cuerpo += extra
    for w in escribe:
        cuerpo += f'in0_df.write.mode("overwrite").parquet(f"{{PARAMS.BASE_PATH}}/output/{w}")\n'
    p.write_text(cuerpo, encoding="utf-8")
    return p


def _paso(sid, job, deps=()):
    return {"id": sid, "name": sid, "action": {"type": "graph", "target": str(job),
                                               "status": "ok", "source": "x.mp"},
            "depends_on": list(deps), "dep_flags": {}, "solo_en_fallo": False,
            "enabled": True, "continue_on_error": False}


def _plan(steps, enlaces=()):
    return {"plan": "t.plan", "nombre": "t", "origen": "plan", "direccion": "prior",
            "ejecucion": {"modo": "python", "spark_args": [], "base_path": "", "env": {}},
            "steps": steps, "enlaces": list(enlaces)}


def _guardar(tmp, nombre, plan):
    p = tmp / nombre
    p.write_text(json.dumps(plan), encoding="utf-8")
    return str(p)


def test_intermedios_excluidos_en_plan(tmp_path):
    a = _job(tmp_path / "j", "a", ["ext.dat"], ["banca/mid.dat"])
    b = _job(tmp_path / "j", "b", ["banca/mid.dat"], ["banca/fin.dat"])
    plan = _plan([_paso("t1", a), _paso("t2", b, ["t1"])])   # sin enlaces explicitos
    base = tmp_path / "base"
    assert o.entradas_faltantes(plan, str(base)) == ["raw/ext.dat"]
    rep = o.generar_datos(plan, str(base), n_rows=5)
    gen = [r["ruta"] for r in rep if r["estado"] == "generado"]
    assert gen == ["raw/ext.dat"]
    assert not (base / "raw" / "banca").exists()
    assert any(r["ruta"] == "raw/banca/mid.dat" and "intermedio" in r["motivo"] for r in rep)


def test_intermedios_excluidos_en_plan_de_planes(tmp_path):
    a = _job(tmp_path / "j", "a", ["ext.dat"], ["banca/mid.dat"])
    b = _job(tmp_path / "j", "b", ["banca/mid.dat"], ["banca/fin.dat"])
    pa = _guardar(tmp_path, "orquestacion_A.json", _plan([_paso("t1", a)]))
    pb = _guardar(tmp_path, "orquestacion_B.json", _plan([_paso("t1", b)]))
    pp = _plan([{**_paso("p1", a), "action": {"type": "plan", "target": pa}},
                {**_paso("p2", b, ["p1"]), "action": {"type": "plan", "target": pb}}])
    pp["tipo"] = "plan_de_planes"
    base = tmp_path / "base"
    assert o.entradas_faltantes(pp, str(base)) == ["raw/ext.dat"]
    # el sub-plan B solo (sin A antes) SI necesita el dataset: es externo para el
    assert o.entradas_faltantes(json.load(open(pb)), str(base)) == ["raw/banca/mid.dat"]
    rep = o.generar_datos(pp, str(base), n_rows=5)
    assert [r["ruta"] for r in rep if r["estado"] == "generado"] == ["raw/ext.dat"]
    # enlace implicito output/X -> raw/X entre sub-planes (sin enlaces explicitos)
    done = {"p1"}
    by_id = {s["id"]: s for s in pp["steps"]}
    imp = o._enlaces_implicitos(pp, by_id["p2"], by_id, done, set(), [], None)
    assert [(e["desde"], e["salida"], e["entrada"]) for e in imp] == [
        ("p1", "output/banca/mid.dat", "raw/banca/mid.dat")]
    # un enlace explicito que ya lo entrega evita el implicito
    ex = [{"desde": "p1", "salida": "output/banca/mid.dat", "hacia": "p2",
           "entrada": "raw/banca/mid.dat"}]
    assert o._enlaces_implicitos(pp, by_id["p2"], by_id, done, set(), ex, None) == []


def test_paso_suelto_con_entrada_intermedia_si_se_genera(tmp_path):
    a = _job(tmp_path / "j", "a", ["ext.dat"], ["mid.dat"])
    b = _job(tmp_path / "j", "b", ["mid.dat"], ["fin.dat"])
    plan = _plan([_paso("t1", a), _paso("t2", b, ["t1"])])
    sel = o.seleccion_pasos(plan, "t2", None)
    assert o.entradas_faltantes(plan, str(tmp_path / "base"), sel) == ["raw/mid.dat"]


def test_enlace_explicito_cubre_la_entrada(tmp_path):
    a = _job(tmp_path / "j", "a", ["ext.dat"], ["x/out.dat"])
    b = _job(tmp_path / "j", "b", ["otro/nombre.dat"], ["fin.dat"])
    enl = [{"id": "e1", "desde": "t1", "salida": "output/x/out.dat", "hacia": "t2",
            "entrada": "raw/otro/nombre.dat", "habilitado": True}]
    plan = _plan([_paso("t1", a), _paso("t2", b, ["t1"])], enl)
    assert o.entradas_faltantes(plan, str(tmp_path / "base")) == ["raw/ext.dat"]


def _proyecto_dml(tmp_path, monkeypatch, job_extra=""):
    """output/proj/x_spark.py + abinitio/proj/x.mp (Input File 'Fuente' con DML) + x.dml."""
    ab = tmp_path / "abinitio" / "proj"
    ab.mkdir(parents=True)
    (ab / "ent.dml").write_text(
        "record\n  string(10) id_cliente;\n  string(1) estatus;\n  decimal(12,2) monto;\n"
        "  integer(4) veces;\n  date(\"YYYY-MM-DD\") fecha;\n  string(5) extra_dml;\nend;\n",
        encoding="utf-8")
    (ab / "x.mp").write_text(
        "{2010503005|XXGfvertex|10|0|1|0|{Input|{30100001|XXparameter_set|@@@@{{30001002|XXparameter|"
        "!prototype_path|$AB_COMPONENTS/Datasets/Input_File.mdc|3|9|Pf|@{0|}}\n"
        "{30001002|XXparameter|Layout|/in/ent.dat|3|2|$|@{0|}}\n"
        "{30001002|XXparameter|metadata_file|$AI_DML/ent.dml|3|2|$|@{0|}}\n"
        "}}@Fuente|@@{0|}}}\n", encoding="utf-8")
    d = tmp_path / "output" / "proj"
    d.mkdir(parents=True)
    job = d / "x_spark.py"
    job.write_text(
        PARAMS_SRC +
        'Fuente_df = spark.read.parquet(f"{PARAMS.BASE_PATH}/raw/in/ent.dat")\n'
        'T_df = Fuente_df.where("estatus == \'A\' AND monto > 0")\n'
        'U_df = _bnx_safe_col(T_df, "ratio", "CASE WHEN veces > 0 THEN (monto * 100) / veces ELSE 0 END")\n'
        'V_df = U_df.withColumn("extra_codigo", F.col("solo_codigo"))\n'
        + job_extra, encoding="utf-8")
    monkeypatch.chdir(tmp_path)
    return job


def test_dml_manda_sobre_el_codigo(tmp_path, monkeypatch):
    job = _proyecto_dml(tmp_path, monkeypatch)
    plan = _plan([_paso("t1", job)])
    base = tmp_path / "base"
    rep = o.generar_datos(plan, str(base), n_rows=10)
    assert rep[0]["estado"] == "generado"
    assert rep[0]["columnas"][:6] == [
        "id_cliente:string", "estatus:string", "monto:decimal", "veces:integer",
        "fecha:date", "extra_dml:string"]
    # lo que el codigo usa y el DML no trae se agrega al final
    assert rep[0]["columnas"][6:] == ["solo_codigo:string"]
    tabla = pq.read_table(str(base / "raw" / "in" / "ent.dat"))
    tipos = {f.name: str(f.type) for f in tabla.schema}
    assert tipos["monto"] == "double" and tipos["veces"] == "int64" and tipos["estatus"] == "string"
    assert "col1" not in tipos and "ratio" not in tipos


def test_valores_cumplen_filtros_con_rechazos(tmp_path, monkeypatch):
    job = _proyecto_dml(tmp_path, monkeypatch)
    plan = _plan([_paso("t1", job)])
    o.generar_datos(plan, str(tmp_path / "b1"), n_rows=20)
    o.generar_datos(plan, str(tmp_path / "b2"), n_rows=20)
    f1 = _leer(tmp_path / "b1", "raw/in/ent.dat")
    assert f1 == _leer(tmp_path / "b2", "raw/in/ent.dat")      # determinista
    pasan = [f for f in f1 if f["estatus"] == "A" and f["monto"] > 0]
    assert len(pasan) >= 0.7 * len(f1)
    assert len(pasan) < len(f1)                                # quedan rechazos


def test_filtros_in_y_rangos(tmp_path):
    job = _job(tmp_path / "j", "f", ["src.dat"], [],
               extra='g_df = in0_df.where("tipo IN (\'X\', \'Y\') AND edad >= 18 AND edad < 65")\n')
    o.generar_datos(_plan([_paso("t1", job)]), str(tmp_path / "base"), n_rows=20)
    filas = _leer(tmp_path / "base", "raw/src.dat")
    ok = [f for f in filas if f["tipo"] in ("X", "Y") and 18 <= f["edad"] < 65]
    assert len(ok) >= 14


def test_tipos_por_uso():
    code = '''a_df = spark.read.parquet(f"{PARAMS.BASE_PATH}/raw/a")
b_df = _bnx_safe_col(a_df, "score", "CASE WHEN lim > 0 THEN (tot * 100) / lim ELSE 100 END")
c_df = b_df.where("tipo LIKE 'AB%' AND substring(codigo, 1, 2) = 'XY'")
d_df = c_df.groupBy("k").agg(sum(_bnx_aggcol(c_df, "importe")).alias("suma"))
e_df = c_df.withColumn("n", F.col("cnt").cast("int"))
'''
    r = o._columnas_por_fuente(code, ["a"])["a"]
    assert r["lim"] == "int" and r["tot"] == "int" and r["importe"] == "int"
    assert r["tipo"] == "string" and r["codigo"] == "string"
    assert "score" not in r and "suma" not in r


def test_sin_alias_de_join_ni_col1_col3(tmp_path):
    code = '''a_df = spark.read.parquet(f"{PARAMS.BASE_PATH}/raw/a")
b_df = spark.read.parquet(f"{PARAMS.BASE_PATH}/raw/b")
_s0 = _bnx_ensure_side(a_df, ["k", "v"]).alias("s0")
_s1 = _bnx_ensure_side(b_df, ["k", "w"]).alias("s1")
_j = _s0.join(_s1, on=["k"], how="left")
c_df = _j.select(expr("`s0`.`k`").alias("k"), expr("`s1`.`w`").alias("w"))
'''
    d = tmp_path / "j"
    d.mkdir()
    job = d / "j_spark.py"
    job.write_text(PARAMS_SRC + code, encoding="utf-8")
    rep = o.generar_datos(_plan([_paso("t1", job)]), str(tmp_path / "base"), n_rows=4)
    for r in rep:
        nombres = [c.split(":")[0] for c in r["columnas"]]
        assert not {"s0", "s1", "col1", "col2", "col3"} & set(nombres), nombres
        assert "k" in nombres
