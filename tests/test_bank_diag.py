"""Log de diagnostico en la escritura de los jobs del banco (src/bank_diag.py) y la regresion del
score con columnas NULL en el demo (vector_assembler sintetico con llaves que no empatan). Datos sinteticos."""
import ast
import os
import sys

import pytest

pytest.importorskip("pyspark")
from src import bank_compat as bc          # noqa: E402
from src import bank_diag as bd            # noqa: E402
from src import mlops_demo as dm           # noqa: E402
from src.mlops_demo import sparkpatch      # noqa: E402

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


@pytest.fixture(scope="module")
def spark(tmp_path_factory):
    from pyspark.sql import SparkSession
    wh = tmp_path_factory.mktemp("wh_diag")
    s = (SparkSession.builder.master("local[1]").appName("t_diag")
         .config("spark.ui.enabled", "false").config("spark.sql.shuffle.partitions", "2")
         .config("spark.sql.warehouse.dir", str(wh)).config("spark.local.dir", str(wh)).getOrCreate())
    yield s
    s.stop()


@pytest.fixture()
def entorno(monkeypatch, tmp_path):
    for v in ("BNX_DIAG_ESCRITURA", "BNX_DIAG_FILAS", "BNX_DIAG_MUESTRA", "BNX_DIAG_LOG", "BNX_BANK_COMPAT"):
        monkeypatch.delenv(v, raising=False)
    monkeypatch.setenv("LOG_FILE_PATH", str(tmp_path / "logs" / "job.log"))
    monkeypatch.setenv("BNX_JOB_ID", "job_sintetico")
    monkeypatch.setitem(sys.modules, "bank_compat", bc)     # otros tests dejan copias de bank_compat en sys.modules
    bd.desinstalar()
    yield tmp_path
    bd.desinstalar()


def _df_con_nulos(spark):
    from pyspark.sql import types as T
    sch = T.StructType([T.StructField("numcliente", T.IntegerType()), T.StructField("a", T.DoubleType()),
                        T.StructField("b", T.DoubleType()), T.StructField("c", T.StringType())])
    return spark.createDataFrame([(1, 1.0, None, "x"), (2, 2.0, None, None), (3, float("nan"), None, "z")], sch)


def test_diag_es_python_38():
    for f in ("bank_diag.py", "bank_compat.py"):
        ast.parse(open(os.path.join(RAIZ, "src", f), encoding="utf-8").read(), feature_version=(3, 8))


def test_activo_por_defecto_y_se_apaga_con_la_variable(monkeypatch):
    monkeypatch.delenv("BNX_DIAG_ESCRITURA", raising=False)
    assert bd.activo() is True
    for v in ("0", "off", "NO", "false"):
        monkeypatch.setenv("BNX_DIAG_ESCRITURA", v)
        assert bd.activo() is False
    monkeypatch.setenv("BNX_DIAG_ESCRITURA", "1")
    assert bd.activo() is True


def test_evaluar_todo_nulo_nan_y_subida_contra_la_entrada():
    h = bd.evaluar(10, {"k": 0.0, "a": 100.0, "b": 40.0, "c": 3.0, "d": 0.0},
                   {"x": 100.0, "a": 100.0},
                   [("/ruta/entrada", {"k": 0.0, "b": 10.0, "c": 1.0})])
    assert h["todo_nulo"] == ["a"]
    assert h["todo_nan"] == ["x"]
    assert [(c, pe, ps) for c, pe, ps, _o in h["subieron"]] == [("b", 10.0, 40.0)]      # c sube < umbral
    assert bd.evaluar(0, {}, {}, []) == {"todo_nulo": [], "todo_nan": [], "subieron": []}


def test_perfil_una_pasada_nulos_y_nan(spark, entorno):
    filas, nulos, nans = bd.perfil(_df_con_nulos(spark))
    assert filas == 3
    assert nulos == {"numcliente": 0.0, "a": 0.0, "b": 100.0, "c": 33.33}
    assert nans == {"a": 33.33, "b": 0.0}
    assert bd.perfil(_df_con_nulos(spark), n=2)[0] == 2        # la muestra se acota con limit(n)


def test_analizar_escritura_imprime_en_espanol_y_anexa_al_log(spark, entorno, capsys, monkeypatch):
    monkeypatch.setenv("BNX_BANK_COMPAT", "1")
    res = bd.analizar_escritura(_df_con_nulos(spark), "/ruta/destino", "parquet", "overwrite")
    out = capsys.readouterr().out
    assert "[diag-escritura] job=job_sintetico destino=/ruta/destino" in out
    assert "ALERTA: 1 de 4 columnas estan 100% NULL: b" in out
    assert "filas de ejemplo" in out and "numcliente=1" in out
    assert "modo UDF: ORIGINAL" in out
    assert "parches de compatibilidad (bank_compat)" in out and "BNX_BANK_COMPAT=1" in out
    log = open(os.environ["LOG_FILE_PATH"], encoding="utf-8").read()
    assert "ALERTA: 1 de 4 columnas estan 100% NULL: b" in log           # tambien en el log del job
    assert res["hallazgos"]["todo_nulo"] == ["b"]


def test_ejemplo_se_oculta_con_muestra_cero(spark, entorno, capsys, monkeypatch):
    monkeypatch.setenv("BNX_DIAG_MUESTRA", "0")
    bd.analizar_escritura(_df_con_nulos(spark), "/d", "parquet", "overwrite")
    assert "filas de ejemplo" not in capsys.readouterr().out


def test_modo_udf_nativo_y_parches_del_job_en_el_log(spark, entorno, capsys, monkeypatch):
    monkeypatch.setitem(bc._ESTADO, "udf_hooks", True)
    monkeypatch.setitem(bc._NATIVAS, "quita_acentos", object())
    monkeypatch.setitem(bc._ESTADO, "avisados", {("job_sintetico", "modulo_x parcheado"), ("udf_python", "incremental")})
    bd.analizar_escritura(_df_con_nulos(spark), "/d", "parquet", "overwrite")
    out = capsys.readouterr().out
    assert "modo UDF: NATIVO" in out and "reemplazadas: quita_acentos" in out and "se quedan en Python: incremental" in out
    assert "parches aplicados en este job: modulo_x parcheado" in out


def test_enganche_de_escritura_parquet_overwrite_relee_y_avisa(spark, entorno, capsys):
    base = str(entorno / "salida")
    assert bd.instalar() is True
    _df_con_nulos(spark).write.mode("overwrite").parquet(base)
    out = capsys.readouterr().out
    assert "destino=%s formato=parquet modo=overwrite" % base in out
    assert "100% NULL: b" in out
    assert "muestra tomada del DataFrame escrito" not in out        # se releyo lo escrito, no se recalculo el plan
    assert spark.read.parquet(base).count() == 3                    # el job no se afecta


def test_enganche_compara_con_la_entrada_y_cubre_tablas(spark, entorno, capsys):
    ent = str(entorno / "entrada")
    spark.createDataFrame([(i, float(i)) for i in range(10)], "k int, v double").write.parquet(ent)
    bd.instalar()
    df = spark.read.parquet(ent)
    from pyspark.sql import functions as F
    malo = df.withColumn("v", F.when(F.col("k") < 5, F.col("v")))      # 50% null, la entrada tenia 0%
    capsys.readouterr()
    malo.write.mode("overwrite").saveAsTable("t_diag_sintetica")
    out = capsys.readouterr().out
    assert "destino=t_diag_sintetica" in out and "formato=tabla" in out
    assert "v: 0.0% -> 50.0%" in out and "entrada: %s" % ent in out
    assert "OK: ninguna" not in out


def test_append_relee_el_destino_y_apagado_no_imprime(spark, entorno, capsys, monkeypatch):
    bd.instalar()
    base = str(entorno / "apend")
    _df_con_nulos(spark).write.mode("append").parquet(base)
    out = capsys.readouterr().out
    assert "muestra tomada del DataFrame escrito" not in out and "100% NULL: b" in out
    monkeypatch.setenv("BNX_DIAG_ESCRITURA", "0")
    _df_con_nulos(spark).write.mode("overwrite").parquet(base)
    assert capsys.readouterr().out == ""
def test_formato_no_releible_perfila_la_muestra_con_aviso(spark, entorno, capsys):
    bd.instalar()
    _df_con_nulos(spark).write.mode("overwrite").csv(str(entorno / "c"))
    out = capsys.readouterr().out
    assert "muestra tomada del DataFrame escrito" in out and "100% NULL: b" in out
def test_insertinto_con_cast_que_produce_null_alerta(spark, entorno, capsys):
    """El DataFrame tiene valores, pero la tabla destino los guarda como NULL (cast): hay que verlo en la tabla."""
    spark.conf.set("spark.sql.storeAssignmentPolicy", "LEGACY")
    try:
        spark.sql("DROP TABLE IF EXISTS t_diag_cast")
        spark.sql("CREATE TABLE t_diag_cast (k INT, v INT) USING parquet")
        bd.instalar()
        df = spark.createDataFrame([(1, "abc"), (2, "xyz")], "k int, v string")
        capsys.readouterr()
        df.write.insertInto("t_diag_cast")
        out = capsys.readouterr().out
        assert spark.table("t_diag_cast").filter("v is not null").count() == 0
        assert "100% NULL: v" in out
        assert "muestra tomada del DataFrame escrito" not in out
    finally:
        spark.conf.set("spark.sql.storeAssignmentPolicy", "ANSI")
        spark.sql("DROP TABLE IF EXISTS t_diag_cast")
def test_un_fallo_del_diagnostico_no_rompe_el_job(spark, entorno, capsys, monkeypatch):
    bd.instalar()
    monkeypatch.setattr(bd, "perfil", lambda *a, **k: (_ for _ in ()).throw(RuntimeError("boom")))
    base = str(entorno / "fallo")
    _df_con_nulos(spark).write.mode("overwrite").parquet(base)
    assert "no se pudo generar el diagnostico" in capsys.readouterr().out
    assert spark.read.parquet(base).count() == 3


def test_desinstalar_restaura_spark(entorno):
    from pyspark.sql import DataFrameReader, DataFrameWriter
    antes = (DataFrameReader.parquet, DataFrameWriter.parquet, DataFrameWriter.mode, DataFrameWriter.saveAsTable)
    bd.instalar()
    assert DataFrameWriter.parquet is not antes[1]
    bd.desinstalar()
    assert (DataFrameReader.parquet, DataFrameWriter.parquet, DataFrameWriter.mode, DataFrameWriter.saveAsTable) == antes


# ---------------------------------------------------------------- regresion: score con features NULL en el demo
@pytest.fixture()
def demo_score(spark, tmp_path, monkeypatch):
    from src.mlops_demo.estado import E
    monkeypatch.setenv("BNX_DEMO_FILAS", "20")
    pkg = tmp_path / "pkg"
    (pkg / "bank_src" / "jobs").mkdir(parents=True)
    dm.iniciar(str(pkg), bank_dirs=[str(pkg / "bank_src")], cohort="202611")
    dm.activar()
    dm.set_job("job_score_sintetico")
    E["features"] = {"fuente_a": ["f1", "f2"]}
    yield E
    dm.desactivar()


def _leer_pivot(spark):
    from pyspark.sql import functions as F
    pivot = spark.createDataFrame([(22, "2026-10-31"), (13, "2026-10-31")], "numcliente int, vintage string") \
        .withColumn("vintage", F.col("vintage").cast("date"))
    pivot.write.mode("overwrite").parquet("/data/w/202611/pivot/universe")
    lect = spark.read.parquet("/data/w/202611/pivot/universe").select("numcliente", "vintage")
    assert lect.count() == 2
    return lect


def test_demo_llaves_del_job_son_las_del_pivot_leido(spark, demo_score):
    """Las llaves para el vector_assembler sintetico salen de lo que el job ya leyo (antes: al azar)."""
    assert sparkpatch._llaves_del_job(spark) is None            # el job aun no leyo nada con llaves
    _leer_pivot(spark)
    k = sparkpatch._llaves_del_job(spark)
    assert sorted(r["numcliente"] for r in k.collect()) == [13, 22]
    assert k.schema["numcliente"].dataType.simpleString() == "int"
    assert k.schema["vintage"].dataType.simpleString() == "date"


def test_demo_vector_assembler_sintetico_empata_con_el_pivot_sin_nulls(spark, demo_score, capsys):
    """Regresion de rps_score: antes el left join pivot x vector_assembler sintetico dejaba NULL todas las features."""
    pytest.importorskip("numpy")            # VectorAssembler de pyspark.ml necesita numpy en el driver
    from pyspark.sql import functions as F
    lect = _leer_pivot(spark)
    va = spark.read.parquet("/data/w/202611/fuente_a/vector_assembler")      # no existe: sintetico
    assert "llaves (numcliente, vintage) tomadas de lo que el job ya leyo" in capsys.readouterr().out
    final = lect.join(va.select("numcliente", "vintage", "features_vector"), ["numcliente", "vintage"], "left")
    assert final.count() == 2
    assert final.where(F.col("features_vector").isNull()).count() == 0     # antes: 2 filas con NULL


def test_demo_sin_llaves_previas_avisa_en_espanol(spark, demo_score, capsys):
    pytest.importorskip("numpy")
    spark.read.parquet("/data/w/202611/fuente_a/vector_assembler")
    out = capsys.readouterr().out
    assert "AVISO: vector_assembler sintetico con llaves al azar" in out
