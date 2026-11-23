"""UDF de Python simples -> expresiones nativas de Spark (bank_compat): sin Python en los workers.
Las fixtures imitan el PATRON de las UDF de las librerias del banco (no es codigo del banco)."""
import ast
import glob
import importlib
import os
import sys
import textwrap

import pytest

from src import bank_compat as bc

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FIXTURE = textwrap.dedent('''
    import numpy as np
    import unidecode
    from pyspark.sql.types import DoubleType


    class Job(object):
        def __init__(self, spark):
            self.sqlContext = spark

        def registrar(self):
            def quita_acentos(unicodestring):
                if unicodestring == None:
                    return ""
                return unidecode.unidecode(unicodestring).lower()
            self.sqlContext.udf.register("quita_acentos", quita_acentos)

            def rmeans(x, y):
                m_1 = np.mean(x)
                m_2 = np.mean(y)
                if m_2 != 0.0:
                    r_mean = float(m_1 / m_2)
                else:
                    r_mean = float(m_1 * 1e5)
                return(r_mean)
            self.sqlContext.udf.register("rmeans", rmeans, DoubleType())

            def rt_mod(x):
                if x[1] != 0.0:
                    rt = float((x[0] / x[1]))
                else:
                    rt = 0.0
                return rt
            self.sqlContext.udf.register("rt_mod", rt_mod, DoubleType())

            ignorar = -1.0
            def rt_mt(x):
                x = [v for v in x if v != ignorar]
                if len(x) == 0:
                    return -99999.0
                return float(x[0] - x[1])
            self.sqlContext.udf.register("rt_mt", rt_mt, DoubleType())

            def incremental(x):
                x.reverse()
                c = 0.0
                for i in range(len(x) - 1):
                    if x[i + 1] < x[i]:
                        c += 1
                return c
            self.sqlContext.udf.register("incremental", incremental, DoubleType())
            return quita_acentos, rmeans, rt_mod, rt_mt, incremental
''')
TEXTOS = ["Árbol", "ñandú", "pingüino", "CAÑÓN", "Educación Pública", "José María", "ÀÈÌÒÙ àèìòù", "Ça va",
          "Ølsen Straße", "¿Qué? ¡Sí!", "camión  ", "", None, "sin acentos", "Æsir œuvre", "Łódź", "nº 5 1ª"]


def _unidecode():
    try:
        return importlib.import_module("unidecode")
    except ImportError:
        pass
    whl = sorted(glob.glob(os.path.join(RAIZ, ".venv", "bnx_vendor_cache", "**", "Unidecode-*.whl"), recursive=True))
    if not whl:
        pytest.skip("sin unidecode (ni wheel en el vendor cache)")
    sys.path.insert(0, whl[0])
    return importlib.import_module("unidecode")


def _ref(s, ud):
    return "" if s is None else ud.unidecode(s).lower()


def test_tabla_de_acentos_coincide_con_unidecode():
    ud = _unidecode()
    assert len(bc.ACENTOS_ORIG) == len(bc.ACENTOS_DEST) > 150
    malos = [(o, d, ud.unidecode(o)) for o, d in zip(bc.ACENTOS_ORIG, bc.ACENTOS_DEST) if ud.unidecode(o) != d]
    assert not malos, malos
    for m, r in bc._MULTI_ACENTOS:
        assert ud.unidecode(m) == r, (m, r, ud.unidecode(m))


def test_analisis_estatico_marca_las_nativizables():
    r = dict((u["nombre"], u) for u in bc.analizar_udfs_fuente(FIXTURE))
    assert r["quita_acentos"]["nativa"] and r["rmeans"]["nativa"] and r["rt_mod"]["nativa"]
    assert not r["incremental"]["nativa"] and "sentencia" in r["incremental"]["motivo"]
    assert not r["rt_mt"]["nativa"]            # 'ignorar' es local: solo se resuelve en runtime (closure)
    assert ast.parse(open(bc.__file__, encoding="utf-8").read(), feature_version=(3, 8))


def test_reescribir_sql():
    q = bc.nativizar_nodo(ast.parse("def q(s):\n    if s is None:\n        return ''\n    return s.lower()\n").body[0],
                          lambda n: None, None, "quita")
    nat = {"quita": q}
    out = bc.reescribir_sql("select QUITA(a) as x, quita( concat(b, ')') ), 'quita(c)' -- quita(d)\n, mi_quita(e) "
                            "from t where quita(quita(f)) = 'x'", nat)
    assert "quita(c)" in out and "-- quita(d)" in out and "mi_quita(e)" in out
    assert out.count("lower(") == 5 and "QUITA(" not in out and "(concat(b, ')'))" in out
    assert bc.reescribir_sql("select quita(a, b) from t", nat) == "select quita(a, b) from t"   # aridad distinta


@pytest.fixture(scope="module")
def spark():
    pytest.importorskip("pyspark")
    from pyspark.sql import SparkSession
    s = (SparkSession.builder.master("local[2]").appName("bnx_udf_nativas").config("spark.ui.enabled", "false")
         .config("spark.sql.shuffle.partitions", "2").getOrCreate())
    yield s
    s.stop()


@pytest.fixture
def job_mod(tmp_path, monkeypatch):
    ud = _unidecode()
    (tmp_path / "bnx_fix_udf.py").write_text(FIXTURE, encoding="utf-8")
    monkeypatch.syspath_prepend(str(tmp_path))
    monkeypatch.delenv("BNX_CHECK_ENV", raising=False)     # otro test puede dejarla puesta (check_env.py)
    monkeypatch.setenv("BNX_FALTANTES_DIR", str(tmp_path))
    monkeypatch.setenv("LOG_FILE_PATH", str(tmp_path / "logs" / "j" / "job.log"))
    os.makedirs(str(tmp_path / "logs" / "j"))
    sys.modules.pop("bnx_fix_udf", None)
    mod = importlib.import_module("bnx_fix_udf")
    assert bc.instalar_udf_nativas(forzar=True)
    yield mod, ud, tmp_path
    bc.desinstalar_udf_nativas()
    bc._ESTADO["avisados"].clear()
    sys.modules.pop("bnx_fix_udf", None)


def _sin_python(df):
    plan = df._jdf.queryExecution().executedPlan().toString()
    return "EvalPython" not in plan and "PythonUDF" not in plan


def test_udf_register_se_cambia_por_expresion_nativa(spark, job_mod, capsys):
    mod, ud, tmp = job_mod
    from pyspark.sql import functions as F
    quita, rmeans, rt_mod, rt_mt, incremental = mod.Job(spark).registrar()
    salida = capsys.readouterr().out
    assert "[compat] UDF quita_acentos -> expresion nativa Spark (translate/lower), sin Python en los workers" in salida
    assert "[compat] UDF incremental: se queda en Python" in salida
    nombres = set(f.name.lower() for f in spark.catalog.listFunctions())
    assert not ({"quita_acentos", "rmeans", "rt_mod", "rt_mt"} & nombres)       # la UDF original NO se registra
    assert "incremental" in nombres                                             # no nativizable: sigue en Python
    spark.createDataFrame([(t,) for t in TEXTOS], "s string").createOrReplaceTempView("bnx_t")
    df = spark.sql("select s, quita_acentos(s) as r from bnx_t")
    assert _sin_python(df)
    for row in df.collect():
        assert row.r == _ref(row.s, ud), (row.s, row.r, _ref(row.s, ud))
    # selectExpr / expr / filter con texto
    assert spark.table("bnx_t").selectExpr("quita_acentos(s) as r").filter("quita_acentos(s) = 'nandu'").count() == 1
    assert spark.table("bnx_t").select(F.expr("quita_acentos(s)").alias("r")).where("r = 'arbol'").count() == 1
    # numericas (las que pedian numpy en los workers)
    import numpy as np
    filas = [([1.0, 2.0, 3.0], [2.0, 4.0]), ([5.0, 0.0], [0.0, 0.0]), ([-1.0, 4.0], [1.5, 0.5])]
    spark.createDataFrame(filas, "x array<double>, y array<double>").createOrReplaceTempView("bnx_n")
    dn = spark.sql("select x, y, rmeans(x, y) as rm, rt_mod(x) as rt, rt_mt(array(x[1], -1.0, 7.0)) as rmt from bnx_n")
    assert _sin_python(dn)
    for row in dn.collect():
        assert row.rm == pytest.approx(rmeans(row.x, row.y))
        assert row.rt == pytest.approx(rt_mod(row.x))
        assert row.rmt == pytest.approx(rt_mt([row.x[1], -1.0, 7.0]))
    assert np is not None
    faltantes = bc.leer_faltantes()
    assert any(f["tipo"] == "parcheado" and "quita_acentos" in f["componente"] for f in faltantes)
    assert "PARCHEADO" in (tmp / "logs" / "j" / "job.log").read_text()


def test_f_udf_y_decorador_devuelven_column_nativo(spark, job_mod):
    mod, ud, _ = job_mod
    from pyspark.sql import functions as F
    from pyspark.sql.types import DoubleType

    u = F.udf(mod.Job(spark).registrar()[0])          # quita_acentos via F.udf

    @F.udf(returnType=DoubleType())
    def doble(x):
        return float(x * 2)
    df = spark.createDataFrame([(t, 1.5) for t in TEXTOS], "s string, n double")
    out = df.select("s", u("s").alias("r"), u(F.col("s")).alias("r2"), doble("n").alias("d"))
    assert _sin_python(out)
    for row in out.collect():
        assert row.r == row.r2 == _ref(row.s, ud) and row.d == 3.0
