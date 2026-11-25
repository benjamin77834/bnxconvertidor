"""DEMO de los jobs del banco sin cluster (src/mlops_demo/, se empaqueta como bnx_demo/).
Fuentes FALSAS pequenas, sin red: columnas inferidas del SQL/AST, joins con filas, rutas del cluster a
demo_out/, tablas Hive locales, shim hdfs, demo_data del usuario y modo real sin parches."""
import ast
import json
import os
import re
import shutil
import subprocess
import sys

import pytest

pytest.importorskip("pyspark")
from src import mlops_demo as dm            # noqa: E402
from src import mlops_pkg as mp             # noqa: E402
from src.mlops_demo import analisis, rutas, sqlmini   # noqa: E402
from src.mlops_demo.estado import E         # noqa: E402


@pytest.fixture(scope="module")
def spark(tmp_path_factory):
    from pyspark.sql import SparkSession
    wh = tmp_path_factory.mktemp("wh")
    s = (SparkSession.builder.master("local[1]").appName("t_demo")
         .config("spark.ui.enabled", "false").config("spark.sql.shuffle.partitions", "2")
         .config("spark.sql.warehouse.dir", str(wh)).config("spark.sql.ansi.enabled", "false")
         .config("spark.local.dir", str(wh)).getOrCreate())
    yield s
    s.stop()


@pytest.fixture()
def demo(tmp_path, spark, monkeypatch):
    monkeypatch.delenv("BNX_DEMO_ESTRICTO", raising=False)
    monkeypatch.delenv("BNX_DEMO_DATA", raising=False)
    monkeypatch.setenv("BNX_DEMO_FILAS", "20")
    pkg = tmp_path / "pkg"
    (pkg / "bank_src" / "jobs").mkdir(parents=True)
    dm.iniciar(str(pkg), bank_dirs=[str(pkg / "bank_src")], cohort="202611")
    dm.activar()
    dm.set_job("job_x")
    yield pkg
    dm.desactivar()


# --- SQL minimo --------------------------------------------------------------------
def test_sqlmini_tablas_columnas_y_filtros():
    q = ("select a.x, cast(b.z as double) as zz, sum(w) from db.ta a join db.tb as b on a.k = b.k "
         "where a.mis_dt between '2026-05-01' and '2026-10-31' and b.flag = 'Y' and n in (1, 2) and c is null")
    i = sqlmini.analizar(q)
    assert [t["nombre"] for t in i["tablas"]] == ["db.ta", "db.tb"]
    assert i["cols"]["db.ta"][:2] == ["x", "k"] and "mis_dt" in i["cols"]["db.ta"]
    assert "z" in i["cols"]["db.tb"] and "flag" in i["cols"]["db.tb"]
    assert "zz" not in i["cols"]["db.tb"]                      # alias, no columna
    assert "w" in i["ambiguas"] and "num" in i["usos"]["w"] and "num" in i["usos"]["z"]
    h = i["hints"]
    assert h[("db.ta", "mis_dt")] == {"ge": "2026-05-01", "le": "2026-10-31"}
    assert h[("db.tb", "flag")]["eq"] == ["Y"]
    assert h[(None, "n")]["eq"] == [1, 2] or h[("db.ta", "n")]["eq"] == [1, 2] or any(
        v.get("eq") == [1, 2] for v in h.values())
    assert any(v.get("null") for v in h.values())


def test_sqlmini_cte_y_subconsulta():
    i = sqlmini.analizar("with t as (select a from db.x) select a from t where a > 3")
    assert [t["nombre"] for t in i["tablas"]] == ["db.x"] and "t" in i["ctes"]
    i = sqlmini.analizar("select y from db.t where mis_dt = (select max(mis_dt) from db.t where mis_dt <= '2026-10-31')")
    assert [t["nombre"] for t in i["tablas"]] == ["db.t", "db.t"]


def test_analisis_ast_columnas_tipos_y_variable(tmp_path):
    f = tmp_path / "job.py"
    f.write_text(
        "import pyspark.sql.functions as F\n"
        "def run(kernel):\n"
        "    a = kernel.spark.read.parquet('/data/x').select('x', 'y')\n"
        "    b = kernel.spark.read.parquet('/data/y')\n"
        "    a = a.withColumn('t', F.col('x') * 2).filter(F.col('estado') == 'A')\n"
        "    b = b.groupBy('k').agg(F.sum('monto'))\n"
        "    return a.join(b, on='k').where(F.to_date('fecha') > F.lit('2020-01-01'))\n")
    cols_a = analisis.columnas_lectura(str(f), 3)
    cols_b = analisis.columnas_lectura(str(f), 4)
    assert {"x", "y", "estado"} <= set(cols_a) and "monto" not in cols_a
    assert {"k", "monto"} <= set(cols_b) and "y" not in cols_b
    u = analisis.usos_columna("x")
    assert u["num"] is True
    assert analisis.usos_columna("fecha")["fecha"] is True
    assert analisis.usos_columna("estado")["pool"] == ["A"]


# --- lecturas sinteticas ------------------------------------------------------------
def test_sql_devuelve_solo_las_columnas_de_la_consulta(demo, spark):
    df = spark.sql("select x, cast(y as double) as yy from db.tabla_a where flag = 'Y' and mis_dt <= '2026-10-31'")
    assert df.columns == ["x", "yy"]
    assert df.count() == 20
    lec = [x for x in E["lecturas"] if x["nombre"] == "db.tabla_a"][0]
    assert lec["origen"] == "sintetica" and {"x", "y", "flag", "mis_dt"} <= set(lec["cols"])
    # los filtros con literales dejan pasar las filas
    assert spark.sql("select flag, mis_dt from db.tabla_a where flag = 'Y' and mis_dt <= '2026-10-31'"
                     ).filter("flag = 'Y' and mis_dt = '2026-10-31'").count() == 20


def test_join_por_clave_devuelve_filas(demo, spark):
    a = spark.sql("select k, x, y from db.a")
    b = spark.sql("select k, z from db.b")
    assert a.join(b, on="k", how="inner").count() == 20
    j = spark.sql("select a.x, b.z from db.a a join db.b b on a.k = b.k where b.z > 0")
    assert j.count() > 0
    # claves con nombres distintos entre tablas coinciden por valor
    c = spark.sql("select crd_acct_nbr, v from db.c")
    d = spark.sql("select numcliente, crd_acct_nbr from db.d")
    assert c.join(d, on="crd_acct_nbr").count() == 20


def test_fechas_between_cubren_los_meses_del_rango(demo, spark):
    df = spark.sql("select mis_dt from db.p where mis_dt between '2026-05-01' and '2026-10-31'")
    meses = {r[0][:7] for r in df.distinct().collect()}
    assert meses == {"2026-05", "2026-06", "2026-07", "2026-08", "2026-09", "2026-10"}


def test_select_estrella_usa_las_columnas_del_codigo(demo, spark):
    f = demo / "bank_src" / "jobs" / "job.py"
    f.write_text("import pyspark.sql.functions as F\n"
                 "def run(spark):\n"
                 "    df = spark.table('db.t')\n"
                 "    return df.withColumn('r', F.col('saldo') / F.col('limite')).filter(F.col('mop') == 3)\n")
    analisis._CACHE.clear()
    analisis.precargar([str(demo / "bank_src")])
    ns = {}
    exec(compile(f.read_text(), str(f), "exec"), ns)
    df = ns["run"](spark)
    assert {"saldo", "limite", "mop"} <= set(df.columns)
    assert df.count() > 0


def test_lectura_dentro_de_libreria_del_banco_suma_sus_columnas(demo, spark, tmp_path):
    """El job llama a una libreria pip del banco que lee un parquet y usa columnas que el job no
    menciona (selectExpr(lista)): el dato sintetico debe traerlas."""
    lib = tmp_path / "site" / "lib_sintetica"
    lib.mkdir(parents=True)
    lf = lib / "core.py"
    lf.write_text("def leer(spark, ruta):\n"
                  "    df = spark.read.parquet(ruta)\n"
                  "    return df\n"
                  "def calcular(spark, ruta):\n"
                  "    q = ['bigint(id_cli) as id_cli', \"to_date(fec_alta_x) as fec_alta_x\", 'periodo_x']\n"
                  "    return leer(spark, ruta).selectExpr(q)\n")
    jf = demo / "bank_src" / "jobs" / "usa_lib.py"
    jf.write_text("def run(spark, lib):\n"
                  "    return lib['calcular'](spark, '/data/fuente/preparada/tabla_x')\n")
    analisis._CACHE.clear()
    analisis.precargar([str(demo / "bank_src")])
    E["lib_dirs"] = [str(lib)]
    ns_lib, ns = {}, {}
    exec(compile(lf.read_text(), str(lf), "exec"), ns_lib)
    exec(compile(jf.read_text(), str(jf), "exec"), ns)
    df = ns["run"](spark, ns_lib)
    assert df.columns == ["id_cli", "fec_alta_x", "periodo_x"] and df.count() == 20


def test_registro_settings_bloque_de_agregacion(tmp_path):
    (tmp_path / "m.json").write_text(json.dumps({"prod": {"fuente_x": {"group_by": {
        "table_name": "tabla_agg_x", "group_by_key": ["id_x", "periodo_x"],
        "query_dict": {"variable": ["monto_x", "", "saldo_x"], "agg": ["sum", "", "max"]}}}}}))
    assert analisis.registro_settings(str(tmp_path))["tabla_agg_x"] == ["id_x", "periodo_x", "monto_x", "saldo_x"]


def test_lectura_de_ruta_sin_datos_usa_columnas_del_registro(demo, spark):
    E["registro"]["tabla_agg_y"] = ["id_y", "monto_y"]
    df = spark.read.parquet("/data/fuente/missing_treatment/tabla_agg_y")
    assert {"id_y", "monto_y"} <= set(df.columns)


def test_dirs_librerias_de_requirements_bank(tmp_path):
    (tmp_path / "requirements-bank.txt").write_text("# comentario\npytest>=1\nno-existe-xyz\n")
    (tmp_path / "bank_compat.py").write_text("")
    d = dm.dirs_librerias(str(tmp_path))
    assert any(os.path.basename(x) == "_pytest" or os.path.basename(x) == "pytest" for x in d)
    assert d[-1] == str(tmp_path / "bank_compat.py")


def test_lectura_de_parquet_sin_datos_infiere_columnas_del_job(demo, spark):
    f = demo / "bank_src" / "jobs" / "lee.py"
    f.write_text("def run(spark):\n"
                 "    p = spark.read.parquet('/data/fuente/x').select('numcliente', 'vintage')\n"
                 "    return p\n")
    analisis._CACHE.clear()
    analisis.precargar([str(demo / "bank_src")])
    ns = {}
    exec(compile(f.read_text(), str(f), "exec"), ns)
    df = ns["run"](spark)
    assert df.columns == ["numcliente", "vintage"] and df.count() == 20


def test_demo_data_del_usuario_va_antes_que_lo_sintetico(demo, spark):
    d = demo / "demo_data"
    d.mkdir()
    (d / "db.mi_tabla.csv").write_text("cliente,monto\n7,100.5\n8,200.5\n")
    (d / "mi_ruta.csv").write_text("a,b\n1,2\n")
    dm.iniciar(str(demo), bank_dirs=[str(demo / "bank_src")], cohort="202611")
    dm.activar()
    df = spark.sql("select cliente, monto from db.mi_tabla where monto > 150")
    assert [tuple(r) for r in df.collect()] == [(8, 200.5)]
    lec = [x for x in E["lecturas"] if x["nombre"] == "db.mi_tabla"][0]
    assert lec["origen"] == "demo_data"
    # una ruta cuyo ultimo tramo coincide tambien la toma
    assert spark.read.parquet("/data/lo/que/sea/mi_ruta").columns == ["a", "b"]


# --- rutas del cluster ---------------------------------------------------------------
def test_rutas_del_cluster_van_a_demo_out(demo, spark):
    df = spark.createDataFrame([(1, "a"), (2, "b")], ["id", "v"])
    df.write.mode("overwrite").parquet("/data/gcgx/work/hive/salida")
    df.write.mode("overwrite").parquet("hdfs://nn1:8020/user/foo/otra")
    df.write.mode("overwrite").csv("s3://bucket/dir/x", header=True)
    out = E["out"]
    assert os.path.isdir(os.path.join(out, "data", "gcgx", "work", "hive", "salida"))
    assert os.path.isdir(os.path.join(out, "user", "foo", "otra"))
    assert os.path.isdir(os.path.join(out, "bucket", "dir", "x"))
    assert not E["orig"]["p_exists"]("/data/gcgx")
    assert spark.read.parquet("/data/gcgx/work/hive/salida").count() == 2     # encadena lo producido
    w = [x for x in E["escrituras"] if x["destino"].endswith("salida")][0]
    assert w["filas"] == 2 and w["job"] == "job_x"
    lec = [x for x in E["lecturas"] if x["nombre"].endswith("salida")][0]
    assert lec["origen"] == "producida:job_x"


def test_os_y_open_del_codigo_del_banco_en_rutas_del_cluster(demo):
    os.makedirs("/data/zzz/logs", exist_ok=True)
    with open("/data/zzz/logs/a.txt", "w") as fh:
        fh.write("hola")
    assert os.path.isfile("/data/zzz/logs/a.txt")
    assert not E["orig"]["p_exists"]("/data/zzz")             # el sistema de archivos real no se toca
    assert os.path.isfile(os.path.join(E["out"], "data", "zzz", "logs", "a.txt"))
    assert os.listdir("/data/zzz/logs") == ["a.txt"]
    assert os.path.exists("/tmp")                         # rutas locales: sin tocar


def test_ruta_demo_saneada_y_larga():
    E["out"] = "/tmp/xx/demo_out"
    assert rutas.ruta_demo("hdfs://nn:8020/a/b c/d").endswith(os.path.join("demo_out", "a", "b_c", "d"))
    assert rutas.ruta_demo("abfss://cont@acct.dfs.core.windows.net/p/q").endswith(os.path.join("cont", "p", "q"))
    larga = rutas.ruta_demo("/data/" + "/".join(["segmento_largo_%d" % i for i in range(30)]))
    assert len(larga) < 200
    assert rutas.es_ruta_cluster("s3a://b/k") and rutas.es_ruta_cluster("/data/x")
    assert not rutas.es_ruta_cluster("relativa/x") and not rutas.es_ruta_cluster("/tmp/otra")


# --- tablas Hive -----------------------------------------------------------------------
def test_tablas_hive_se_escriben_en_local_y_se_leen_despues(demo, spark):
    df = spark.createDataFrame([(1, "a", "2026-11-01"), (2, "b", "2026-11-01")], ["id", "v", "proc_dt"])
    df.write.saveAsTable(name="dbx.t1", format="hive", mode="append", partitionBy="proc_dt")
    assert os.path.isdir(os.path.join(E["out"], "hive", "dbx", "t1"))
    got = spark.sql("select id, v, proc_dt from dbx.t1 where proc_dt = '2026-11-01'")
    assert sorted((r[0], r[1], str(r[2])) for r in got.collect()) == [(1, "a", "2026-11-01"), (2, "b", "2026-11-01")]
    # INSERT OVERWRITE ... PARTITION como hace toolbox.write
    df.drop("proc_dt").createOrReplaceTempView("t2")
    spark.sql("INSERT OVERWRITE TABLE dbx.t2 PARTITION (proc_dt='2026-11-02') SELECT * FROM t2")
    assert spark.table("dbx.t2").count() == 2
    assert E["tablas_prod"]["dbx.t2"]["filas"] == 2
    ins = [x for x in E["escrituras"] if x["destino"] == "dbx.t2"]
    assert ins and ins[0]["tipo"] == "tabla"
    # una tabla producida sin filas para el filtro cae a sintetica en vez de devolver vacio
    vacio = spark.sql("select id from dbx.t1 where proc_dt = '1999-01-01'")
    assert vacio.count() > 0


def test_sentencias_ddl_se_simulan(demo, spark):
    spark.sql("CREATE TABLE IF NOT EXISTS db.nueva (a int)")
    spark.sql("MSCK REPAIR TABLE db.nueva")
    assert [c["tipo"] for c in E["comandos"]] == ["sql", "sql"]


def test_jdbc_teradata_devuelve_columnas_del_sql(demo, spark):
    df = (spark.read.format("jdbc").option("url", "jdbc:teradata://host/db")
          .option("query", "select cliente, saldo from tdb.cuentas where saldo > 0").load())
    assert df.columns == ["cliente", "saldo"] and df.count() > 0
    assert any(c["tipo"] == "jdbc" for c in E["comandos"])


# --- shim hdfs / CLI ----------------------------------------------------------------------
def _hdfs(*args):
    p = subprocess.Popen(["hdfs", "dfs"] + list(args), stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    out, err = p.communicate()
    return p.returncode, out.decode(), err.decode()


def test_shim_hdfs_ls_parseable_como_el_job(demo, spark):
    spark.createDataFrame([(1,)], ["a"]).write.mode("overwrite").parquet("/data/w/202611/pivot/universe")
    spark.createDataFrame([(1,)], ["a"]).write.mode("overwrite").parquet("/data/w/202611/pivot/elegible")
    path = "/data/w/202611/pivot"
    rc, out, _ = _hdfs("-ls", path)
    assert rc == 0 and out.splitlines()[0] == "Found 2 items"
    # parseo identico al de bnmxverse.data_pull._check_files
    elems = [e[re.search(path, e).end():].replace("/", "") for e in out.splitlines() if path in e]
    assert sorted(elems) == ["elegible", "universe"]
    assert _hdfs("-test", "-d", path)[0] == 0
    assert _hdfs("-test", "-d", "/data/w/no_existe")[0] == 1
    assert _hdfs("-ls", "/data/w/no_existe")[0] == 1


def test_shim_hdfs_mkdir_put_get_cat_du_mv_rm(demo, tmp_path):
    loc = tmp_path / "f.txt"
    loc.write_text("contenido\n")
    assert _hdfs("-mkdir", "-p", "/user/u/dir")[0] == 0
    assert _hdfs("-put", str(loc), "/user/u/dir/")[0] == 0
    assert _hdfs("-cat", "/user/u/dir/f.txt")[1] == "contenido\n"
    assert _hdfs("-du", "-s", "/user/u/dir")[1].split()[0] == str(len("contenido\n"))
    assert _hdfs("-mv", "/user/u/dir/f.txt", "/user/u/dir/g.txt")[0] == 0
    dest = tmp_path / "back.txt"
    assert _hdfs("-get", "/user/u/dir/g.txt", str(dest))[0] == 0 and dest.read_text() == "contenido\n"
    assert _hdfs("-rm", "-r", "-skipTrash", "/user/u/dir")[0] == 0
    assert _hdfs("-test", "-e", "/user/u/dir")[0] == 1
    assert not E["orig"]["p_exists"]("/user/u")


def test_shim_hadoop_fs_y_os_system(demo, capfd):
    rc = subprocess.run(["hadoop", "fs", "-test", "-d", "/data/nada"]).returncode
    assert rc == 1
    assert os.system("hdfs dfs -mkdir -p /data/viaos/x") == 0
    assert os.path.isdir(os.path.join(E["out"], "data", "viaos", "x"))


def test_otros_comandos_externos_se_simulan_y_estricto_falla(demo, capfd, monkeypatch):
    r = subprocess.run(["beeline", "-u", "jdbc:hive2://h:10000", "-e", "show tables"], capture_output=True)
    assert r.returncode == 0 and r.stdout == b""
    assert os.system("impala-shell -i host -q 'invalidate metadata db.t'") == 0
    assert "comando externo simulado" in capfd.readouterr().out
    assert [c["tipo"] for c in E["comandos"]] == ["externo", "externo"]
    # los comandos locales corren de verdad
    assert subprocess.run([sys.executable, "-c", "print(5)"], capture_output=True).stdout.strip() == b"5"
    E["estricto"] = True
    with pytest.raises(RuntimeError):
        subprocess.run(["kinit", "-kt", "x", "y"])


# --- modo real: sin parches --------------------------------------------------------------
def test_modo_real_no_parchea_nada(spark):
    from pyspark.sql import DataFrameReader, DataFrameWriter, SparkSession
    import builtins
    antes = (SparkSession.sql, DataFrameReader.parquet, DataFrameWriter.parquet, subprocess.Popen,
             os.system, builtins.open, os.makedirs)
    dm.iniciar("/tmp/no_importa_real")
    assert (SparkSession.sql, DataFrameReader.parquet, DataFrameWriter.parquet, subprocess.Popen,
            os.system, builtins.open, os.makedirs) == antes      # iniciar() solo prepara estado
    dm.activar()
    assert SparkSession.sql is not antes[0] and subprocess.Popen is not antes[3]
    dm.desactivar()
    assert (SparkSession.sql, DataFrameReader.parquet, DataFrameWriter.parquet, subprocess.Popen,
            os.system, builtins.open, os.makedirs) == antes
    shutil.rmtree("/tmp/no_importa_real", ignore_errors=True)


def test_main_generado_solo_activa_el_demo_en_modo_demo():
    src = mp._MAIN_PY
    ast.parse(src, feature_version=(3, 8))
    i_demo, i_act = src.index("    if demo:\n        base = tempfile.mkdtemp"), src.index("_dm.activar()")
    assert i_demo < i_act < src.index("def main():")
    assert src.count("_dm.activar()") == 1 and "import bnx_demo" in src
    # el modulo no se importa al cargar main.py: solo bajo demanda
    assert not re.search(r"^import bnx_demo|^from bnx_demo", src, re.M)


def test_paquete_incluye_bnx_demo_solo_con_jobs_de_kernel(tmp_path):
    job = "def run(kernel):\n    return 1\n"
    out = tmp_path / "a.zip"
    mp.build_package_from_sources(
        [{"name": "p/bin/toolbox/kernel.py", "code": "class Kernel:\n    pass\n"},
         {"name": "p/bin/jobs/m/j/job.py", "code": job}],
        convert_fn=lambda c: {"ok": True, "code": "df_out = df", "warnings": [], "unsupported": []},
        include_bank_libs=False, out_path=str(out), py_target="py3.11")
    import zipfile
    nombres = zipfile.ZipFile(out).namelist()
    assert "framework_mlops_v2_pkg/bnx_demo/__init__.py" in nombres
    assert "framework_mlops_v2_pkg/bnx_demo/sparkpatch.py" in nombres
    sin = tmp_path / "b.zip"
    mp.build_package_from_sources(
        [{"name": "x.py", "code": "import pandas as pd\ndf = pd.DataFrame({'a': [1]})\n"}],
        convert_fn=lambda c: {"ok": True, "code": "df_out = df", "warnings": [], "unsupported": []},
        include_bank_libs=False, out_path=str(sin), py_target="py3.11")
    assert not [n for n in zipfile.ZipFile(sin).namelist() if "/bnx_demo/" in n]


def test_modulos_del_demo_son_python38():
    d = os.path.dirname(mp.__file__)
    for f in os.listdir(os.path.join(d, "mlops_demo")):
        if f.endswith(".py"):
            with open(os.path.join(d, "mlops_demo", f), encoding="utf-8") as fh:
                ast.parse(fh.read(), feature_version=(3, 8))


def test_reporte_resume_lecturas_escrituras_y_comandos(demo, spark):
    spark.sql("select x from db.r")
    spark.createDataFrame([(1,)], ["a"]).write.mode("overwrite").parquet("/data/rep/x")
    os.system("beeline -e 'show tables'")
    txt = dm.reporte(imprimir=False)
    assert "JOB job_x" in txt and "LEE   [sintetica] db.r" in txt
    assert "ESCRIBE ruta /data/rep/x" in txt and "1 filas" in txt and "CMD   [externo] beeline" in txt
    assert os.path.isfile(os.path.join(E["out"], "REPORTE_DEMO.json"))
