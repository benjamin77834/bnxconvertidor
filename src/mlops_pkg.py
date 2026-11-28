# src/mlops_pkg.py
"""
Generador del "Framework MLOps v2" (mejorado) EMPAQUETADO.

Sin tocar el framework del banco, produce un PAQUETE NUEVO que corrige los
hallazgos del diagnostico (ver examples/mlops_framework/steps.py:FINDINGS):

  - clase base `BaseAggregate` -> elimina la duplicacion de los *_aggregate.py
  - validaciones de calidad ACTIVAS (no comentadas) con umbral de nulos
  - sin errores silenciados (excepciones especificas + logging)
  - pruebas reales con pytest (fixture de Spark)
  - estructura limpia y una sola fuente de verdad
  - entorno virtual reproducible (requirements.txt + setup.sh que crea el venv + run.sh que corre el modelo)

build_mlops_package() -> (zip_bytes, filename)

El paquete declara las dependencias (incluidas las del banco, p.ej. libs de
Cloudera/Artifactory) en requirements.txt; en la red del banco se resuelven
desde su indice privado. En local corre con PySpark open source.
"""
import glob
import io
import json
import os
import shutil
import zipfile
import ast as _ast_mod
import re as _re
from datetime import datetime


# --------------------------------------------------------------------------
# Archivos del paquete (texto). Son codigo NUEVO escrito por BNX, no el del banco.
# --------------------------------------------------------------------------

_BASE_AGGREGATE = '''# framework_mlops_v2/core/base_aggregate.py
"""Clase base de agregacion. Elimina la duplicacion de los *_aggregate.py del
framework original (atms/s15/s15_nf eran casi identicos)."""
import os
import logging

from .quality import assert_nulls_below

logger = logging.getLogger(__name__)


class BaseAggregate:
    """Contrato comun de agregacion por fuente.

    Subclases implementan solo `_aggregate_df(df)` con su logica propia; el
    resto (leer parquet, validar calidad, escribir) es compartido.
    """

    # Umbral maximo de % de nulos por columna antes de fallar (configurable).
    MAX_NULL_PCT = 50.0

    def __init__(self, previous_path, agg_dict, sqlContext, mode="overwrite"):
        self.previous_path = previous_path
        self.agg_dict = agg_dict
        self.sqlContext = sqlContext
        self.mode = mode

    def _read(self):
        path = os.path.join(self.previous_path, self.agg_dict["table_name"])
        logger.info("Leyendo %s", path)
        return self.sqlContext.read.parquet(path)

    def _save_parquet(self, df, path):
        logger.info("Escribiendo %s filas en %s", df.count(), path)
        df.write.mode(self.mode).parquet(path)

    def _aggregate_df(self, df):
        """Logica de agregacion especifica de la fuente. Sobrescribir."""
        raise NotImplementedError

    def aggregate(self):
        df_in = self._read()
        df_out = self._aggregate_df(df_in)
        # VALIDACION DE CALIDAD ACTIVA (en el original estaba comentada).
        assert_nulls_below(df_out, self.MAX_NULL_PCT)
        head, _ = os.path.split(self.previous_path)
        self._save_parquet(df_out, os.path.join(head, "groupby"))
        return df_out
'''

_QUALITY = '''# framework_mlops_v2/core/quality.py
"""Validaciones de calidad ACTIVAS. En el framework original el assert de nulos
estaba comentado (monitoreo ciego); aqui falla si se supera el umbral."""
import logging
from pyspark.sql import functions as F

logger = logging.getLogger(__name__)


def null_report(df):
    """% de nulos por columna. Devuelve dict {columna: pct}."""
    total = df.count()
    if total == 0:
        return {}
    exprs = [F.sum(F.col(c).isNull().cast("int")).alias(c) for c in df.columns]
    row = df.agg(*exprs).collect()[0].asDict()
    return {c: round(100.0 * (row[c] or 0) / total, 2) for c in df.columns}


def assert_nulls_below(df, max_pct):
    """Falla (ValueError) si alguna columna supera `max_pct` de nulos."""
    rep = null_report(df)
    offenders = {c: p for c, p in rep.items() if p > max_pct}
    if offenders:
        logger.error("Calidad: columnas sobre el umbral de nulos: %s", offenders)
        raise ValueError(
            "Validacion de calidad fallida (nulos > %.1f%%): %s" % (max_pct, offenders))
    logger.info("Calidad OK: ninguna columna supera %.1f%% de nulos", max_pct)
    return rep
'''

_ATMS = '''# framework_mlops_v2/aggregates/atms.py
"""ATMs: antes era un archivo casi identico a s15. Ahora hereda de BaseAggregate
y solo declara su logica (drop + fillna)."""
from ..core.base_aggregate import BaseAggregate


class AtmsAggregate(BaseAggregate):
    def _aggregate_df(self, df):
        return df.drop("inf_dt", "tfrom_date").fillna(0)
'''

_S15 = '''# framework_mlops_v2/aggregates/s15.py
"""S15: misma base que ATMs; antes era codigo duplicado, ahora comparte BaseAggregate."""
from ..core.base_aggregate import BaseAggregate


class S15Aggregate(BaseAggregate):
    def _aggregate_df(self, df):
        return df.drop("inf_dt", "tfrom_date").fillna(0)
'''

_PNL = '''# framework_mlops_v2/aggregates/pnl.py
"""PnL: agregacion por GROUP BY dinamico. Misma logica que el framework original
pero sobre BaseAggregate, con el query construido de forma explicita."""
from ..core.base_aggregate import BaseAggregate


class PnlAggregate(BaseAggregate):
    def _build_query(self, query_dict, group_by, cols):
        # query_dict = {"variable": [...], "agg": [...]} (config, listas pequenas): Python puro.
        pares = [(v, a) for v, a in zip(query_dict["variable"], query_dict["agg"]) if v != ""]
        feats = ",".join(
            "{0}({1}) as {1}".format(a, v) for v, a in pares if v in cols)
        g = ",".join(group_by)
        return "SELECT %s,%s FROM tempPnl GROUP BY %s" % (g, feats, g)

    def _aggregate_df(self, df):
        df.createOrReplaceTempView("tempPnl")
        q = self._build_query(
            self.agg_dict["query_dict"], self.agg_dict["group_by_key"], df.columns)
        return self.sqlContext.sql(q)
'''

_ROUTER = '''# framework_mlops_v2/aggregates/router.py
"""Router de agregaciones. Reemplaza la herencia multiple del GroupBy original
por un registro simple {source: clase}. Anadir una fuente = una linea."""
from .atms import AtmsAggregate
from .s15 import S15Aggregate
from .pnl import PnlAggregate

REGISTRY = {
    "atms": AtmsAggregate,
    "s15": S15Aggregate,
    "pnl": PnlAggregate,
    # Anadir nuevas fuentes aqui: "mi_fuente": MiFuenteAggregate,
}


class GroupBy:
    def __init__(self, source, previous_path, agg_dict, sqlContext, mode="overwrite"):
        if source not in REGISTRY:
            raise KeyError("Fuente no registrada: %r. Opciones: %s" % (
                source, sorted(REGISTRY)))
        self.impl = REGISTRY[source](previous_path, agg_dict, sqlContext, mode)

    def aggregate(self):
        return self.impl.aggregate()
'''

_RATIOS = '''# framework_mlops_v2/features/ratios.py
"""Ratios con proteccion de division por cero (when/otherwise)."""
from pyspark.sql import functions as F


def add_ratio(df, name, numerator, denominator):
    """Anade `name = numerator / denominator`, 0 si el denominador es 0."""
    return df.withColumn(
        name,
        F.when(F.col(denominator) > 0, F.col(numerator) / F.col(denominator))
         .otherwise(F.lit(0.0)))
'''

# --- Pasos EXTRA del pipeline (opcionales, via checkbox) ---

_FEATURE_ENGINEERING = '''# framework_mlops_v2/features/feature_engineering.py
"""Feature Engineering: transformaciones de series temporales por cliente.
Version modular (el original era un archivo de ~83 KB). Cada transformacion es
una funcion pequena y testeable."""
from pyspark.sql import functions as F


def add_stats(df, cols, prefix):
    """Estadisticos de una serie de columnas: media, std, min, max, tendencia."""
    arr = F.array(*[F.col(c).cast("double") for c in cols])
    df = df.withColumn(prefix + "_media", F.expr(
        "aggregate(%s, CAST(0.0 AS DOUBLE), (acc, x) -> acc + x) / %d" % (
            _arr_sql(cols), len(cols))))
    df = df.withColumn(prefix + "_min", F.array_min(arr))
    df = df.withColumn(prefix + "_max", F.array_max(arr))
    # Tendencia simple: ultimo - primero.
    df = df.withColumn(prefix + "_tendencia",
                       F.col(cols[-1]).cast("double") - F.col(cols[0]).cast("double"))
    return df


def _arr_sql(cols):
    return "array(" + ",".join("CAST(%s AS DOUBLE)" % c for c in cols) + ")"
'''

_VECTOR_ASSEMBLER = '''# framework_mlops_v2/features/vector_assembler.py
"""Vector Assembler: junta las features en un unico 'features_vector' de Spark ML."""
from pyspark.ml.feature import VectorAssembler


def assemble(df, feature_cols, output_col="features_vector"):
    """Ensambla feature_cols en un vector. Preserva el resto de columnas."""
    assembler = VectorAssembler(
        inputCols=feature_cols, outputCol=output_col, handleInvalid="keep")
    return assembler.transform(df)
'''

_SCORING = '''# framework_mlops_v2/scoring/scorer.py
"""Scoring: aplica el modelo sobre el feature vector. Soporta XGBoost (.xgb) si
esta disponible, o un fallback lineal para pruebas."""
import logging
from pyspark.sql import functions as F

logger = logging.getLogger(__name__)


class Scorer:
    def __init__(self, model_path=None):
        self.model_path = model_path
        self._booster = None
        if model_path:
            try:
                import xgboost as xgb
                self._booster = xgb.Booster()
                self._booster.load_model(model_path)
            except Exception as e:
                logger.warning("No se pudo cargar XGBoost (%s); se usara fallback.", e)

    def score(self, df, feature_cols, out_col="score", max_rows=1000000):
        """Devuelve df con la columna de score. Con XGBoost usa el modelo EN EL DRIVER (xgboost no corre
        en los executors sin Python en los workers); sin el, un score lineal simple (solo para pruebas).

        ADVERTENCIA DE TAMANO: la ruta XGBoost trae al driver SOLO las columnas de features (matriz
        numerica, sin pandas) hasta `max_rows` filas; si hay mas, falla con un mensaje claro: puntua por
        lotes (filtra por cohorte/particion) o sube BNX_DRIVER_MEMORY."""
        if self._booster is not None:
            import xgboost as xgb
            rid = "_bnx_rid"
            base = df.withColumn(rid, F.monotonically_increasing_id())
            # driver: ids + features (solo lo necesario para puntuar), acotado por max_rows
            filas = base.select(rid, *[F.col(c).cast("double") for c in feature_cols]).limit(max_rows + 1).collect()
            if len(filas) > max_rows:
                raise ValueError("Scoring XGBoost en el driver: mas de %d filas; puntua por lotes "
                                 "o sube max_rows/BNX_DRIVER_MEMORY" % max_rows)
            nan = float("nan")
            matriz = [[nan if r[i + 1] is None else r[i + 1] for i in range(len(feature_cols))] for r in filas]
            logger.info("Scoring con XGBoost en el driver: %s (%d filas)", self.model_path, len(filas))
            preds = self._booster.predict(xgb.DMatrix(matriz, feature_names=list(feature_cols)))
            res = df.sparkSession.createDataFrame(
                [(r[0], float(p)) for r, p in zip(filas, preds)], [rid, out_col])
            return base.join(res, on=rid, how="left").drop(rid)
        # Fallback lineal de ejemplo (normaliza una suma de features).
        expr = sum((F.col(c).cast("double") for c in feature_cols), F.lit(0.0))
        return df.withColumn(out_col, (expr / F.lit(float(len(feature_cols) or 1))))
'''

_MONITORING = '''# framework_mlops_v2/monitoring/monitor_metrics.py
"""Monitoreo de modelos: PSI (Population Stability Index), CSI (Characteristic
Stability Index) y Data Quality Check (DQC). Compara la distribucion ACTUAL
contra la de DESARROLLO y alerta si hay drift. Reimplementacion limpia del
lib_mkop_metrics del framework original (sin su codigo propietario)."""
import logging
from pyspark.sql import functions as F

logger = logging.getLogger(__name__)

# Reglas tipicas de interpretacion del PSI/CSI.
PSI_STABLE = 0.10      # < 0.10 estable
PSI_WARNING = 0.25     # 0.10-0.25 revisar; > 0.25 inestable


class MonitorMetrics:
    """Calcula PSI/CSI y DQC sobre un DataFrame de scores/features.

    dist_dev: dict {bin: frecuencia_relativa_desarrollo} por variable, o un
    DataFrame de referencia. Aqui se recibe como dict para simplicidad.
    """

    def psi(self, current_df, column, dist_dev, bins=None):
        """PSI de una columna: suma de (rel_cur - rel_dev)*ln(rel_cur/rel_dev).
        Todo en Spark (join de la distribucion de desarrollo con la frecuencia relativa actual y UN
        agg); al driver solo vuelve el escalar. Sin pandas/numpy."""
        spark = current_df.sparkSession
        total = current_df.count()
        if total == 0 or not dist_dev:
            return 0.0
        eps = 1e-6
        dev = spark.createDataFrame([(str(k), float(v or eps)) for k, v in dist_dev.items()],
                                    "bin string, rel_dev double")
        cur = (current_df.groupBy(F.col(column).cast("string").alias("bin")).count()
               .withColumn("rel_cur", F.col("count") / F.lit(float(total))))
        j = dev.join(cur, on="bin", how="left").withColumn(
            "rc", F.coalesce(F.col("rel_cur"), F.lit(eps)))
        valor = j.agg(F.sum((F.col("rc") - F.col("rel_dev"))
                            * F.log(F.col("rc") / F.col("rel_dev"))).alias("psi")).first()[0]   # escalar
        return round(float(valor or 0.0), 6)

    def quantile_bins(self, df, column, n_bins=10):
        """Bordes de cubos por cuantiles (approxQuantile, en Spark): sirve para construir dist_dev."""
        qs = [i / float(n_bins) for i in range(1, n_bins)]
        return df.approxQuantile(column, qs, 0.001)

    def interpret(self, psi_value):
        if psi_value < PSI_STABLE:
            return "estable"
        if psi_value < PSI_WARNING:
            return "revisar"
        return "inestable"

    def dqc(self, df, columns):
        """Data Quality Check: estadisticos por columna (conteo, media, std, min, max, % nulos).
        UN solo agg para todas las columnas (una pasada); al driver solo vuelve una fila."""
        total = df.count()
        exprs = []
        for c in columns:
            col = F.col(c)
            exprs += [F.count(col).alias(c + "__n"),
                      F.mean(col.cast("double")).alias(c + "__mean"),
                      F.stddev(col.cast("double")).alias(c + "__std"),
                      F.min(col).alias(c + "__min"),
                      F.max(col).alias(c + "__max"),
                      F.sum(col.isNull().cast("int")).alias(c + "__nulls")]
        fila = df.agg(*exprs).first().asDict() if exprs else {}      # 1 fila (escalares) al driver
        out = {}
        for c in columns:
            agg = {k: fila[c + "__" + k] for k in ("n", "mean", "std", "min", "max", "nulls")}
            agg["null_pct"] = round(100.0 * (agg["nulls"] or 0) / total, 2) if total else 0.0
            out[c] = agg
        return out
'''

_PIPELINE = '''# framework_mlops_v2/pipeline.py
"""Pipeline de referencia: encadena los pasos del framework v2 en orden.
extract(ya en parquet) -> groupby (aggregates) -> features -> vector -> scoring.
Ajusta las rutas/configuracion a tu entorno."""
from .aggregates.router import GroupBy, REGISTRY
from .features import feature_engineering as fe
from .features.vector_assembler import assemble
from .scoring.scorer import Scorer


def run(previous_path, agg_dict_by_source, sqlContext, feature_cols,
        model_path=None):
    """Corre el pipeline completo para todas las fuentes registradas."""
    # 1) Agregacion por fuente.
    for source in REGISTRY:
        agg_dict = agg_dict_by_source.get(source, {"table_name": source})
        GroupBy(source, previous_path, agg_dict, sqlContext).aggregate()
    # 2) (features / vector / scoring se encadenan sobre el parquet resultante)
    #    Este run es una PLANTILLA: adapta la lectura del parquet de groupby,
    #    aplica fe.add_stats(...), assemble(...) y Scorer(model_path).score(...).
    return {"sources": list(REGISTRY), "feature_cols": feature_cols,
            "model_path": model_path}
'''

_TEST = '''# tests/test_aggregates.py
"""Pruebas REALES (antes los test() solo imprimian 'class is working!').
Requiere pyspark. Ejecuta: pytest -q"""
import pytest

pyspark = pytest.importorskip("pyspark")
from pyspark.sql import SparkSession
from framework_mlops_v2.core.quality import null_report, assert_nulls_below


@pytest.fixture(scope="session")
def spark():
    s = (SparkSession.builder.master("local[1]").appName("mlops_v2_tests")
         .getOrCreate())
    yield s
    s.stop()


def test_null_report_cuenta_bien(spark):
    df = spark.createDataFrame([(1, None), (2, "x"), (3, None)], ["id", "val"])
    rep = null_report(df)
    assert rep["id"] == 0.0
    assert rep["val"] == pytest.approx(66.67, abs=0.1)


def test_assert_nulls_falla_sobre_umbral(spark):
    # Esquema explicito: una columna toda-nula no permite inferir el tipo.
    from pyspark.sql.types import StructType, StructField, IntegerType, StringType
    schema = StructType([
        StructField("id", IntegerType(), True),
        StructField("val", StringType(), True),
    ])
    df = spark.createDataFrame([(1, None), (2, None)], schema)
    with pytest.raises(ValueError):
        assert_nulls_below(df, max_pct=50.0)


def test_assert_nulls_pasa_bajo_umbral(spark):
    df = spark.createDataFrame([(1, "a"), (2, "b")], ["id", "val"])
    assert_nulls_below(df, max_pct=50.0)  # no lanza
'''

_INIT_ROOT = '''"""Framework MLOps v2 — version mejorada y empaquetada por BNX.
Corrige: duplicacion (BaseAggregate), validaciones activas, sin errores
silenciados, pruebas reales. No contiene codigo propietario del banco."""
__version__ = "2.0.0"
'''


# Modulos que NUNCA son librerias internas del banco: stdlib + stack open source
# que ya resolvemos (pandas/numpy/pyspark/sklearn/xgboost/pytest/chispa) y el
# propio framework generado. Lo que importe el codigo original y NO este aqui se
# trata como lib interna del banco (Artifactory privado).
_STDLIB_AND_KNOWN = {
    # open source que ya empaquetamos / resolvemos
    "pandas", "numpy", "np", "pd", "pyspark", "sklearn", "scikit_learn",
    "xgboost", "lightgbm", "scipy", "pytest", "chispa", "matplotlib",
    "seaborn", "statsmodels", "joblib", "dateutil", "pytz", "six",
    # deps del stack empaquetadas en vendor/bank (no son libs internas del banco):
    "cytoolz", "toolz", "unidecode", "cloudpickle",
    # el propio framework generado (imports relativos)
    "framework_mlops_v2", "framework_mlops_metrics",
    # modulos INTERNOS del proyecto del banco (no son librerias a instalar: son
    # carpetas del propio codigo / del paquete generado). El main.py del banco
    # hace 'from aggregates...', 'import datapull', 'from libs...', etc.
    "aggregates", "datapull", "data_pull", "libs", "jobs", "settings", "static",
    "unidecode",
    # IGNORADAS a peticion: no se usan en el despliegue, no reportarlas como
    # faltantes. smtplib es stdlib (correo); modeling_tools no aplica.
    "smtplib", "modeling_tools",
    # stdlib comun que puede aparecer en el codigo de negocio
    "os", "sys", "re", "json", "csv", "math", "time", "datetime", "calendar",
    "collections", "itertools", "functools", "logging", "typing", "decimal",
    "random", "io", "pathlib", "warnings", "argparse", "abc", "copy",
    "hashlib", "base64", "uuid", "pickle", "glob", "shutil", "tempfile",
    "subprocess", "traceback", "operator", "string", "enum", "dataclasses",
}


# ---------------------------------------------------------------------------
# STDLIB: nombres de modulos de la libreria estandar de Python. NUNCA son libs del
# banco ni paquetes pip. 'sys.stdlib_module_names' solo existe en Python 3.10+, y el
# portal del banco corre en Python 3.8 (Windows): ahi esa lista no existe y 'email',
# 'types', etc. se colaban en requirements-bank.txt ("No matching distribution
# found for email"). Por eso se embebe la lista (incluye modulos de 3.8 que ya no
# estan en versiones nuevas) y ademas se comprueba contra el interprete real.
# ---------------------------------------------------------------------------
_STDLIB_FALLBACK = frozenset("""
__future__ abc aifc annotationlib antigravity argparse array ast asynchat asyncio
asyncore atexit audioop base64 bdb binascii binhex bisect builtins bz2 cProfile calendar
cgi cgitb chunk cmath cmd code codecs codeop collections colorsys compileall compression
concurrent configparser contextlib contextvars copy copyreg crypt csv ctypes curses
dataclasses datetime dbm decimal difflib dis distutils doctest dummy_threading email
encodings ensurepip enum errno faulthandler fcntl filecmp fileinput fnmatch formatter
fractions ftplib functools gc genericpath getopt getpass gettext glob graphlib grp gzip
hashlib heapq hmac html http idlelib imaplib imghdr imp importlib inspect io ipaddress
itertools json keyword lib2to3 linecache locale logging lzma macpath mailbox mailcap
marshal math mimetypes mmap modulefinder msilib msvcrt multiprocessing netrc nis nntplib
nt ntpath nturl2path numbers opcode operator optparse os ossaudiodev parser pathlib pdb
pickle pickletools pipes pkgutil platform plistlib poplib posix posixpath pprint profile
pstats pty pwd py_compile pyclbr pydoc pydoc_data pyexpat queue quopri random re
readline reprlib resource rlcompleter runpy sched secrets select selectors shelve shlex
shutil signal site smtpd smtplib sndhdr socket socketserver spwd sqlite3 sre_compile
sre_constants sre_parse ssl stat statistics string stringprep struct subprocess sunau
symbol symtable sys sysconfig syslog tabnanny tarfile telnetlib tempfile termios
textwrap this threading time timeit tkinter tkinter.tix token tokenize tomllib trace
traceback tracemalloc tty turtle turtledemo types typing unicodedata unittest urllib uu
uuid venv warnings wave weakref webbrowser winreg winsound wsgiref xdrlib xml xmlrpc
zipapp zipfile zipimport zlib zoneinfo
""".split())


def _is_stdlib_module(name):
    """True si 'name' (modulo de primer nivel) es de la stdlib de Python. Funciona
    igual en Python 3.8 y 3.14: (1) lista nativa si existe, (2) lista embebida,
    (3) find_spec: el modulo vive bajo el directorio de la stdlib, no en
    site-packages."""
    import sys as _s
    n = (name or "").strip()
    if not n:
        return False
    if n in getattr(_s, "stdlib_module_names", ()) or n in _STDLIB_FALLBACK:
        return True
    try:
        import importlib.util as _iu
        import sysconfig as _sc
        spec = _iu.find_spec(n)
        origin = getattr(spec, "origin", None) if spec else None
        if origin in ("built-in", "frozen"):
            return True
        if origin:
            std = os.path.abspath(_sc.get_paths()["stdlib"])
            o = os.path.abspath(origin)
            return o.startswith(std) and "site-packages" not in o and "dist-packages" not in o
    except Exception:
        pass
    return False


def _detect_bank_imports(source_codes):
    """Escanea el codigo ORIGINAL (pandas) de las fuentes y devuelve, ordenados,
    los modulos de PRIMER nivel importados que NO son stdlib ni del stack open
    source conocido: es decir, las librerias INTERNAS del banco (toolbox,
    mex_lib_cs, lib_mkop_metrics, mex-lib*, etc.) que hay que resolver desde el
    Artifactory privado. `source_codes` es una lista de strings (codigo pandas).

    Robusto: intenta ast; si el codigo no parsea, cae a regex sobre las lineas
    de import. Ignora imports relativos (from . import ...)."""
    found = {}
    for code in source_codes or []:
        code = code or ""
        mods = set()
        parsed = False
        try:
            tree = _ast_mod.parse(code)
            parsed = True
            for node in _ast_mod.walk(tree):
                if isinstance(node, _ast_mod.Import):
                    for a in node.names:
                        mods.add(a.name.split(".")[0])
                elif isinstance(node, _ast_mod.ImportFrom):
                    if node.level and node.level > 0:
                        continue  # relativo: no es lib externa
                    if node.module:
                        mods.add(node.module.split(".")[0])
        except Exception:
            parsed = False
        if not parsed:
            # Fallback por regex: 'import X', 'from X import ...'
            for m in _re.finditer(r'^\s*import\s+([a-zA-Z_][\w]*)', code, _re.M):
                mods.add(m.group(1))
            for m in _re.finditer(r'^\s*from\s+([a-zA-Z_][\w]*)\s+import', code, _re.M):
                mods.add(m.group(1))
        # Modulos de la STDLIB de Python (email, os, io, ...): NUNCA son libs del
        # banco. Se detectan automaticamente con sys.stdlib_module_names (3.10+)
        # para no mantener una lista manual que siempre tiene huecos (p.ej. 'email').
        for mod in mods:
            key = mod.strip()
            if not key or key in _STDLIB_AND_KNOWN or _is_stdlib_module(key):
                continue
            # Preservar primer orden de aparicion.
            found.setdefault(key, True)
    return sorted(found.keys())


# Open source que el codigo del banco importa y que NO esta en el core de
# requirements.txt: modulo importado -> paquete pip.
_EXTRA_PIP = {
    "cytoolz": "cytoolz", "toolz": "toolz", "unidecode": "Unidecode",
    "cloudpickle": "cloudpickle", "joblib": "joblib", "dateutil": "python-dateutil",
    "pytz": "pytz", "six": "six", "sklearn": "scikit-learn", "xgboost": "xgboost",
    "lightgbm": "lightgbm", "scipy": "scipy", "statsmodels": "statsmodels",
    "matplotlib": "matplotlib", "seaborn": "seaborn", "yaml": "PyYAML",
    "openpyxl": "openpyxl", "xlrd": "xlrd", "pyarrow": "pyarrow", "requests": "requests",
    "tqdm": "tqdm", "dill": "dill", "threadpoolctl": "threadpoolctl",
}
# Dependencias de una lib (para instalar offline sin --no-deps fallido).
_EXTRA_DEPS = {"cytoolz": ["toolz"]}


def _detect_extra_imports(source_codes):
    """Paquetes pip open source que importa el codigo (fuera del core)."""
    mods = set()
    for code in source_codes or []:
        try:
            tree = _ast_mod.parse(code or "")
        except Exception:
            continue
        for node in _ast_mod.walk(tree):
            if isinstance(node, _ast_mod.Import):
                for a in node.names:
                    mods.add(a.name.split(".")[0])
            elif isinstance(node, _ast_mod.ImportFrom) and not node.level and node.module:
                mods.add(node.module.split(".")[0])
    pkgs = []
    for m in sorted(mods):
        if m in _EXTRA_PIP:
            for dep in _EXTRA_DEPS.get(m, []) + [m]:
                name = _EXTRA_PIP.get(dep, dep)
                if name not in pkgs:
                    pkgs.append(name)
    return pkgs


# pandas 3 rompe codigo viejo del banco (dtype string por defecto, copy-on-write): se fija <3 en
# TODOS los lugares (requirements, deps base/condicionales, piezas de ciencia, setup.py).
_PANDAS_PIN = "pandas>=1.3,<3"
# numpy 2.0 elimino numpy.source: mex-libmissingtreatment (banco, no modificable) lo usa y truena
# con "cannot import name 'source' from 'numpy'". Con Python <= 3.12 hay wheels de numpy 1.x, asi que
# se fija <2. Python >= 3.13 no tiene numpy 1.x (cp313/cp314): ahi queda <3.
_NUMPY_PIN_1X = "numpy>=1.21,<2"
_NUMPY_PIN_2X = "numpy>=1.21,<3"
_NUMPY_SIN_1X_AVISO = ("numpy 2.x: mex-libmissingtreatment (numpy.source) no funcionara en Python %s "
                       "(numpy 1.x no tiene wheels para esa version).")
def _numpy_pins(py_target=None):
    """Lineas de requirements para numpy segun el/los Python destino. Todo <= 3.12 -> <2; todo
    >= 3.13 -> <3; mezcla ('all', serie py312plus) -> una linea con marker por rango."""
    vs = [v for vv in _versiones_target(py_target).values() for v in vv]
    menores = [int(v.split(".")[1]) for v in vs] or [11]
    if max(menores) <= 12:
        return [_NUMPY_PIN_1X]
    if min(menores) >= 13:
        return [_NUMPY_PIN_2X]
    return [_NUMPY_PIN_1X + ' ; python_version < "3.13"', _NUMPY_PIN_2X + ' ; python_version >= "3.13"']
def _numpy_pin(py_target=None):
    """Una sola linea de numpy para el destino (en mezcla, la del rango bajo con marker)."""
    return _numpy_pins(py_target)[0]
def numpy_aviso_target(py_target=None):
    """Aviso (o '') de que en algun Python destino numpy 2.x rompe mex-libmissingtreatment."""
    vs = [v for vv in _versiones_target(py_target).values() for v in vv if int(v.split(".")[1]) >= 13]
    return _NUMPY_SIN_1X_AVISO % ", ".join(vs) if vs else ""


def _imports_pandas_numpy(code):
    """{'pandas','numpy'} que importa un fuente Python (AST; regex si no parsea)."""
    found = set()
    try:
        tree = _ast_mod.parse(code or "")
    except (SyntaxError, ValueError):
        for m in _re.finditer(r"^\s*(?:import\s+(pandas|numpy)\b|from\s+(pandas|numpy)[\w.]*\s+import\b)",
                              code or "", _re.M):
            found.add(m.group(1) or m.group(2))
        return found
    for n in _ast_mod.walk(tree):
        if isinstance(n, _ast_mod.Import):
            for a in n.names:
                if a.name.split(".")[0] in ("pandas", "numpy"):
                    found.add(a.name.split(".")[0])
        elif isinstance(n, _ast_mod.ImportFrom) and n.level == 0 and (n.module or "").split(".")[0] in ("pandas", "numpy"):
            found.add(n.module.split(".")[0])
    return found


# Codigo que genera el framework (plantillas): PySpark puro, no cuenta como "codigo que importa pandas".
_PLANTILLAS_SIN_PANDAS = ("tests/", "bnx_demo/", "framework_mlops_v2/core/", "framework_mlops_v2/features/",
                          "framework_mlops_v2/monitoring/", "framework_mlops_v2/scoring/",
                          "framework_mlops_v2/pipeline.py", "framework_mlops_metrics_pkg/", "mex_lib_cs/")
_PLANTILLAS_RAIZ = ("main.py", "check_env.py", "bnx_sparkconf.py", "probe_workers.py", "setup.py")


def decidir_pandas(files, ml_libs=None, extra_steps=False, ciencia=False, codigo_banco=None, max_archivos=6):
    """Regla de inclusion de pandas/numpy en el paquete (ya no son obligatorias):
      (a) algun codigo que VIAJA en el paquete los importa (modulos del banco: toolbox/*, bnmxverse/*,
          utils/*; fuentes copiadas tal cual; mex-lib) o
      (b) la pila de ciencia esta activada (xgboost/scikit-learn los requieren; tambien extra_steps).
    files: {ruta_en_el_paquete: codigo}. codigo_banco: {ruta: codigo} de modulos del banco que viajan
    desde el cache (no estan en `files`). Devuelve {pandas, numpy, razones, texto}."""
    usan = {}                      # archivo -> {pandas,numpy}
    for rel, code in list((files or {}).items()) + list((codigo_banco or {}).items()):
        if not (isinstance(code, str) and rel.endswith(".py")):
            continue
        if rel.startswith(_PLANTILLAS_SIN_PANDAS) or rel in _PLANTILLAS_RAIZ:
            continue
        mods = _imports_pandas_numpy(code)
        if mods:
            usan[rel] = mods
    ciencia_on = bool(ml_libs) or bool(extra_steps) or bool(ciencia)
    razones, vistos = [], {}
    for rel in sorted(usan):
        nombre = rel
        for pre in ("bank_src/", "bank_pkg/"):
            if nombre.startswith(pre):
                nombre = nombre[len(pre):]
        if nombre in vistos:                 # el mismo modulo del banco en bank_src/ y en el cache
            vistos[nombre]["modulos"] = sorted(set(vistos[nombre]["modulos"]) | usan[rel])
            continue
        vistos[nombre] = {"tipo": "codigo", "archivo": nombre, "modulos": sorted(usan[rel])}
        razones.append(vistos[nombre])
    if ciencia_on:
        _det = ("pila de ciencia de datos activada" if ciencia else
                "tu codigo importa %s (la pila de ciencia las instala)" % ", ".join(ml_libs or ["xgboost/scikit-learn"])
                if ml_libs else "pasos extra (scoring con xgboost/scikit-learn)")
        razones.append({"tipo": "ciencia", "archivo": None, "modulos": ["pandas", "numpy"],
                        "detalle": "xgboost/scikit-learn requieren numpy (y pandas): " + _det})
    todos = set().union(*usan.values()) if usan else set()
    pandas_ = ciencia_on or "pandas" in todos
    numpy_ = pandas_ or "numpy" in todos
    if razones:
        cod = [r for r in razones if r["tipo"] == "codigo"]
        partes = []
        if cod:
            nombres = [r["archivo"] for r in cod]
            partes.append("lo importa " + ", ".join(nombres[:max_archivos])
                          + ("..." if len(nombres) > max_archivos else ""))
        if ciencia_on:
            partes.append(razones[-1]["detalle"])
        texto = "se incluye pandas/numpy: " + "; ".join(partes)
    else:
        texto = "no se incluye pandas ni numpy: ningun codigo del paquete los usa"
    return {"pandas": bool(pandas_), "numpy": bool(numpy_), "razones": razones, "texto": texto}


# Librerias de ML que, si el codigo las importa, viajan en requirements.txt y en el
# vendor/ OFFLINE como pandas/numpy (sin necesitar extra_steps). xgboost y
# scikit-learn van SIEMPRE juntos: en Mac scikit-learn trae su propia libomp
# (.dylibs/) que xgboost puede usar si no hay 'brew install libomp'.
_ML_PIP = ("xgboost", "lightgbm", "scikit-learn", "scipy", "statsmodels", "matplotlib",
           "seaborn", "joblib", "threadpoolctl")
# Linea de requirements.txt de cada una (las transitivas -numpy, patsy, contourpy,
# pillow...- las resuelve pip al armar vendor/).
_ML_REQ = {
    # Linux/Windows: xgboost-cpu (mismo `import xgboost`, sin CUDA/nvidia-nccl: ~5 MB en vez de
    # 60-430 MB). macOS: xgboost (ya es solo CPU). --xgboost-gpu / BNX_XGBOOST_GPU=1: xgboost normal.
    "xgboost": "xgboost>=1.7  # pila de ciencia de datos (offline en vendor/)",
    # lightgbm 3.3.5 (ultima con wheel manylinux2014) no es compatible con scikit-learn/numpy
    # recientes de Python 3.12: ahi se pide 4.x (wheel manylinux_2_28, glibc >= 2.28).
    "lightgbm": ('lightgbm>=3.3 ; python_version < "3.12"  # pila de ciencia de datos (offline en vendor/)\n'
                 'lightgbm>=4.0 ; python_version >= "3.12"  # pila de ciencia de datos (4.x: manylinux_2_28)'),
    "scikit-learn": "scikit-learn>=1.1  # pila de ciencia de datos; en Mac trae libomp para xgboost/lightgbm",
    "scipy": "scipy>=1.7  # pila de ciencia de datos",
    "statsmodels": "statsmodels>=0.13  # pila de ciencia de datos",
    "matplotlib": "matplotlib>=3.5  # pila de ciencia de datos",
    "seaborn": "seaborn>=0.11  # pila de ciencia de datos",
    "joblib": "joblib>=1.1  # pila de ciencia de datos",
    "threadpoolctl": "threadpoolctl>=3.0  # pila de ciencia de datos",
}


def _requisito_xgboost(linea):
    """requirements.txt del paquete: xgboost-cpu en Linux/Windows y xgboost en macOS (con markers,
    para que el mismo archivo sirva en cualquier SO). Con --xgboost-gpu: 'xgboost' sin markers."""
    if not linea.lower().startswith("xgboost") or _vm.xgboost_gpu():
        return linea
    cuerpo, _, com = linea.partition("#")
    cuerpo = cuerpo.strip()
    com = ("  #" + com) if com else ""
    return ('%s ; sys_platform != "darwin"%s\n%s ; sys_platform == "darwin"'
            % (cuerpo.replace("xgboost", "xgboost-cpu", 1), com + " (CPU, sin CUDA)", cuerpo))


def _ml_libs_detectadas(extra_pkgs, ciencia=False):
    """Librerias de la pila de ciencia de datos que van al paquete: TODAS si ciencia=True
    (opcion 'Incluir pila de ciencia de datos'), si no solo las que importa el codigo.
    xgboost/lightgbm siempre con scikit-learn (en Mac trae la libomp que necesitan);
    importar sklearn o xgboost trae ambos. [] si no usa ninguna."""
    if ciencia:
        return list(_ML_PIP)
    pk = set(extra_pkgs or []) & set(_ML_PIP)
    orig = set(pk)
    if orig & {"xgboost", "lightgbm"}:
        pk.add("scikit-learn")
    if orig & {"xgboost", "scikit-learn"}:
        pk |= {"xgboost", "scikit-learn"}
    return [m for m in _ML_PIP if m in pk]


def _requirements_extra(pkgs):
    lines = [
        "# Librerias OPEN SOURCE que importa tu codigo (fuera del core).",
        "# setup.sh las instala UNA POR UNA: offline desde vendor/ y vendor/bank/;",
        "# si no estan, por internet. Si alguna falla, no detiene las demas.",
    ]
    return "\n".join(lines + list(pkgs)) + "\n"


def _requirements(include_bank_libs, extra_steps=False, bank_libs=None, ml_libs=None, pandas_info=None,
                  py_target=None):
    """requirements.txt. pandas/numpy son CONDICIONALES (ver decidir_pandas): pandas_info = su
    decision; sin ella se incluyen solo si hay pila de ciencia / pasos extra."""
    if pandas_info is None:
        _hay = bool(ml_libs) or bool(extra_steps)
        pandas_info = {"pandas": _hay, "numpy": _hay, "texto": ""}
    base = [
        "# Framework MLOps v2 — dependencias",
        "# PySpark segun la version de Python (markers de pip): 3.5.x soporta",
        "# Python 3.8-3.11; 4.0.x soporta 3.9+ y es el unico compatible con 3.12+",
        "# (PySpark 3.5 usa distutils, eliminado en Python 3.12).",
        'pyspark>=3.5,<3.6 ; python_version < "3.12"',
        'pyspark>=4.0,<4.1 ; python_version >= "3.12" and python_version < "3.14"',
        'pyspark>=4.1,<4.2 ; python_version >= "3.14"',
        "pytest>=7.0",
        "chispa>=0.9  # testing de DataFrames Spark",
    ]
    _txt = pandas_info.get("texto") or ""
    if pandas_info.get("numpy") or pandas_info.get("pandas"):
        if pandas_info.get("pandas"):
            base.append(_PANDAS_PIN + "  # <3: pandas 3 cambia el comportamiento (dtype string, copy-on-write)")
        base.extend(_numpy_pins(py_target))
        if _txt:
            base.insert(1, "# " + _txt)
    else:
        base.insert(1, "# " + (_txt or "pandas/numpy NO se incluyen: ningun codigo del paquete los usa"))
    ml = list(ml_libs or [])
    if extra_steps:
        base += [
            _requisito_xgboost("xgboost>=1.7  # scoring (paso extra)"),
            "scikit-learn>=1.1  # metricas/preparacion (paso extra)",
        ]
        ml = [m for m in ml if m not in ("xgboost", "scikit-learn")]
    # Librerias de ML que importa el codigo subido (offline en vendor/, como pandas).
    for _m in ml:
        base.append(_requisito_xgboost(_ML_REQ.get(_m, _m)))

    # Librerias INTERNAS del banco detectadas en el codigo original. Se dan de
    # ALTA en requirements.txt para que pip las resuelva desde el Artifactory
    # privado (--index-url). Van ACTIVAS (no comentadas) cuando se detectaron,
    # porque el codigo realmente las importa y sin ellas el paquete no corre.
    detected = list(bank_libs or [])
    if detected:
        base += [
            "",
            "# --- Librerias INTERNAS del banco (detectadas en el codigo original) ---",
            "# NO estan en PyPI ni en vendor/: se resuelven desde el Artifactory privado.",
            "# Van en 'requirements-bank.txt' (no aqui) para que la instalacion OFFLINE",
            "# del core desde vendor/ con --no-index NO se rompa. setup.sh/run.sh las",
            "# instalan aparte. Listadas aqui COMENTADAS solo como referencia:",
        ]
        base += [f"# {lib}" for lib in detected]
    elif include_bank_libs:
        base += [
            "",
            "# Librerias internas del banco (se resuelven desde el Artifactory",
            "# privado; en local se omiten o se apuntan al indice interno).",
            "# toolbox",
            "# lib_mkop_metrics",
            "# mex-libextract",
            "# mex-libgroupby",
            "# mex-libfeatureengineering",
        ]
    return "\n".join(base) + "\n"


# Mapeo de MODULO importado -> paquete pip del banco (mex-lib*). El codigo
# importa 'lib_extract', 'lib_group_by', etc.; el paquete pip se llama distinto.
_BANK_MODULE_TO_PKG = {
    "lib_columns2_vector": "mex-libcolumns2vector",
    "lib_extract": "mex-libextract",
    "lib_feature_engineering": "mex-libfeatureengineering",
    "lib_generate_pivot": "mex-libgeneratepivot",
    "lib_generate_ratios": "mex-libgenerateratios",
    "lib_group_by": "mex-libgroupby",
    "lib_missing_treatment": "mex-libmissingtreatment",
    "lib_vector_assembler": "mex-libvectorassembler",
}
# Paquetes pip del banco VERIFICADOS (importan limpio en pruebas nuestras). Solo
# estos se empaquetan OFFLINE en vendor/bank/. Los demas sdist estan INCOMPLETOS
# en el origen (les faltan subpaquetes: extract_special_treatments, mobs, alias
# 'libs', shims *_aggregate, numpy.source) -> se omiten del vendor y se avisa.
_BANK_PKG_VERIFIED = {
    "mex-libcolumns2vector",
    "mex-libgeneratepivot",
    "mex-libgenerateratios",
    "mex-libvectorassembler",
}
# Paquetes del banco INCOMPLETOS en el origen, con el motivo (para avisar al usuario).
_BANK_PKG_INCOMPLETE = {
    "mex-libextract": "falta el subpaquete 'extract_special_treatments/' en el .tar.gz",
    "mex-libgroupby": "imports '*_aggregate' sin shim y depende de otras libs (generate_pivot)",
    "mex-libfeatureengineering": "usa 'from libs.*' (alias inexistente) y exporta nombres privados inconsistentes",
    "mex-libmissingtreatment": "falta el subpaquete 'mobs/' y usa numpy.source (API eliminada)",
}
# Modulos del banco que NO son pip, sino codigo de PYTHONPATH (van en vendor/bank/
# pkgcode, no en requirements-bank.txt). 'mex_lib_cs' es un AGREGADOR (fachada de
# las mex-lib*); BNX lo genera como shim en pkgcode, no es un paquete pip.
_BANK_PATH_MODULES = {"toolbox", "bnmxverse", "utils", "mex_lib_cs"}


def _bank_pkg_name(mod):
    """Traduce un modulo importado al nombre del paquete pip del banco (o lo deja
    igual si no hay mapeo conocido)."""
    return _BANK_MODULE_TO_PKG.get(mod, mod)


def _requirements_bank(bank_libs, con_compat=None):
    """Archivo SOLO con las librerias internas del banco (nombres de paquete pip),
    para instalarlas OFFLINE desde vendor/bank/ o desde el Artifactory privado.
    Los modulos de PYTHONPATH (toolbox, ...) NO van aqui; se montan via bank_pkg."""
    # Traducir modulos -> paquetes pip y excluir los de path (toolbox/...).
    # Separar VERIFICADOS (activos) de INCOMPLETOS (comentados con el motivo).
    verified, incomplete = [], []
    for m in bank_libs or []:
        if m in _BANK_PATH_MODULES or _is_stdlib_module(m):
            continue
        name = _bank_pkg_name(m)
        if isinstance(con_compat, dict):          # modulo -> paquete pip segun el diagnostico (cualquier libreria)
            for _pip, _tops in con_compat.items():
                if m in _tops:
                    name = _pip
        if name in _BANK_PKG_INCOMPLETE and not con_compat:
            if name not in [n for n, _ in incomplete]:
                incomplete.append((name, _BANK_PKG_INCOMPLETE[name]))
        elif name not in verified:
            verified.append(name)
    for name in (list(con_compat) if con_compat else []):     # con bank_compat: TODAS las mex-lib del cache se instalan
        if name not in verified:
            verified.append(name)
    head = [
        "# Librerias INTERNAS del banco detectadas en tu codigo original.",
        "# Se instalan OFFLINE desde vendor/bank/ si el paquete es 'ambiente completo';",
        "# si no, desde el Artifactory privado:",
        "#   pip install -r requirements-bank.txt --index-url https://<artifactory-interno>/simple",
        "# Los modulos de PYTHONPATH (toolbox, bnmxverse, utils) van en ./bank_pkg,",
        "# NO aqui (no son paquetes pip).",
    ]
    lines = list(head) + list(verified)
    if incomplete:
        lines += [
            "",
            "# --- INCOMPLETAS en el .tar.gz de origen (NO empaquetadas; pide la",
            "#     version completa al equipo del banco). Motivo por paquete: ---",
        ]
        for name, reason in incomplete:
            lines.append(f"# {name}   # {reason}")
    return "\n".join(lines) + "\n"


# pytest.ini: pytest SOLO busca tests en tests/ y nunca entra a vendor/, bank_pkg/,
# .venv/ ni a la basura de macOS (__MACOSX). Sin esto, 'pytest -q' desde la raiz
# recorre todo el arbol y revienta con PermissionError en __MACOSX/**/conftest.py
# (carpeta que Finder crea al comprimir) u otras carpetas sin permiso de lectura.
_PYTEST_INI = '''[pytest]
testpaths = tests
norecursedirs = __MACOSX vendor bank_pkg .venv venv build dist .git node_modules *.egg-info
python_files = test_*.py
addopts = -p no:cacheprovider
'''

_LIBOMP_SH = r'''# ---------------------------------------------------------------------------
# xgboost necesita OpenMP del sistema (bash 3.2 compatible, sin dependencias):
#  - macOS: libxgboost.dylib busca @rpath/libomp.dylib (Homebrew). Si no hay
#    'brew install libomp', se usa la copia que traen scikit-learn (sklearn/.dylibs)
#    o torch dentro del venv, exportando DYLD_LIBRARY_PATH. Alternativa permanente:
#    install_name_tool -add_rpath <carpeta con libomp.dylib> <venv>/.../xgboost/lib/libxgboost.dylib
#  - Linux: la wheel manylinux enlaza libgomp del sistema (yum/apt install libgomp).
# ---------------------------------------------------------------------------
bnx_libomp_fix() {
  [ "$(uname)" = "Darwin" ] || return 0
  BNX_SP="$(python -c 'import sysconfig; print(sysconfig.get_paths()["purelib"])' 2>/dev/null || true)"
  if [ -z "$BNX_SP" ] || { [ ! -d "$BNX_SP/xgboost" ] && [ ! -d "$BNX_SP/lightgbm" ]; }; then return 0; fi
  if [ -f /opt/homebrew/opt/libomp/lib/libomp.dylib ] || [ -f /usr/local/opt/libomp/lib/libomp.dylib ]; then
    return 0
  fi
  BNX_OMP_DIR=""
  for f in "$BNX_SP"/sklearn/.dylibs/libomp.dylib "$BNX_SP"/torch/lib/libomp*.dylib "$BNX_SP"/*/.dylibs/libomp*.dylib; do
    if [ -f "$f" ]; then BNX_OMP_DIR="$(dirname "$f")"; break; fi
  done
  if [ -n "$BNX_OMP_DIR" ]; then
    case ":${DYLD_LIBRARY_PATH:-}:" in
      *":$BNX_OMP_DIR:"*) ;;
      *) export DYLD_LIBRARY_PATH="$BNX_OMP_DIR${DYLD_LIBRARY_PATH:+:$DYLD_LIBRARY_PATH}" ;;
    esac
    echo "      [libomp] macOS sin Homebrew libomp: xgboost usara la de $BNX_OMP_DIR (DYLD_LIBRARY_PATH)."
    BNX_BAD=0
    for lib in xgboost lightgbm; do
      if [ -d "$BNX_SP/$lib" ] && ! python -c "import $lib" >/dev/null 2>&1; then BNX_BAD=1; fi
    done
    if [ "$BNX_BAD" = "1" ]; then
      echo "      [AVISO] xgboost/lightgbm siguen sin cargar. Instala OpenMP:  brew install libomp"
      echo "              o fija la ruta: install_name_tool -add_rpath $BNX_OMP_DIR $BNX_SP/xgboost/lib/libxgboost.dylib"
    fi
  else
    echo "      [AVISO] xgboost/lightgbm necesitan OpenMP en Mac y no hay libomp: instala  brew install libomp"
    echo "              (o instala scikit-learn en este venv: trae su propia libomp)."
  fi
  return 0
}

bnx_libgomp_check() {
  [ "$(uname)" = "Linux" ] || return 0
  BNX_SP="$(python -c 'import sysconfig; print(sysconfig.get_paths()["purelib"])' 2>/dev/null || true)"
  if [ -z "$BNX_SP" ] || { [ ! -d "$BNX_SP/xgboost" ] && [ ! -d "$BNX_SP/lightgbm" ]; }; then return 0; fi
  BNX_BAD=0
  for lib in xgboost lightgbm; do
    if [ -d "$BNX_SP/$lib" ] && ! python -c "import $lib" >/dev/null 2>&1; then BNX_BAD=1; fi
  done
  if [ "$BNX_BAD" = "0" ]; then return 0; fi
  if { ldconfig -p || /sbin/ldconfig -p; } 2>/dev/null | grep -q libgomp; then return 0; fi
  echo "      [AVISO] xgboost/lightgbm no cargan y el sistema no tiene libgomp (OpenMP). Instalalo (requiere root):"
  echo "                sudo dnf install libgomp   (RHEL 8)  |  yum install libgomp (CentOS 7)  |  apt-get install libgomp1 (Debian/Ubuntu)"
  echo "              El montaje continua; los jobs que usen xgboost fallaran hasta instalarlo."
  return 0
}
'''

_SETUP_SH = '''#!/usr/bin/env bash
# setup.sh - MONTA el entorno (una sola vez): crea .venv e instala todo.
# Si el paquete trae vendor/ (ambiente completo) monta TODO OFFLINE, sin internet.
# NO corre el modelo: para eso usa  bash run.sh
# Uso:  bash setup.sh            (monta el entorno)
#       bash setup.sh --test     (monta y ademas corre pytest)
set -e
# Si setup.sh se corta a medias (set -e) el .venv queda sin pandas/hook: se avisa claro.
trap 'rc=$?; if [ "$rc" -ne 0 ] && [ -z "${BNX_SETUP_FIN:-}" ]; then echo "[setup] ABORTADO (codigo $rc): el .venv puede estar INCOMPLETO. Corrige lo anterior y vuelve a correr: bash setup.sh"; rm -f .venv/.bnx_setup_ok 2>/dev/null; fi' EXIT

@@SPARKCFG@@
BNX_RUN_TEST=0
for _a in "$@"; do
  case "$_a" in
    --test) BNX_RUN_TEST=1 ;;
    --reconfigurar-spark) BNX_SPARK_RECONFIG=1; export BNX_SPARK_RECONFIG ;;
  esac
done
# Modo de PySpark del paquete: 'incluido' (wheel en vendor/) o 'servidor' (usa el Spark ya instalado).
BNX_PYSPARK_MODO=""
if [ -f vendor/PYSPARK_MODE ]; then BNX_PYSPARK_MODO="$(tr -d '[:space:]' < vendor/PYSPARK_MODE)"; fi

# Basura de macOS (si el ZIP se comprimio/re-comprimio en Finder): la carpeta
# __MACOSX y los archivos ._* (resource forks) rompen pytest con PermissionError.
rm -rf __MACOSX 2>/dev/null || true
find . -name '._*' -not -path './.venv/*' -delete 2>/dev/null || true
find . -name '.DS_Store' -not -path './.venv/*' -delete 2>/dev/null || true

# Python del servidor (RHEL 8: /usr/bin/python3.11, paquete python3.11 de AppStream). Con
# vendor/PYTHON_TARGET se busca python<target> y luego python3, y la version debe ser EXACTA.
PY_T=""
if [ -f vendor/PYTHON_TARGET ]; then PY_T="$(tr -d '[:space:]' < vendor/PYTHON_TARGET)"; fi
if [ -n "${PYTHON:-}" ]; then
  PY="$PYTHON"
elif [ -n "$PY_T" ] && command -v "python$PY_T" >/dev/null 2>&1; then
  PY="python$PY_T"
else
  PY="python3"
fi
# Ruta ABSOLUTA del python del SISTEMA, fijada ANTES de crear/activar el venv: despues de activarlo
# 'python3.11' (nombre relativo) resuelve al del venv y ya no ve el PySpark instalado en el sistema.
if [ -z "${BNX_SYSTEM_PYTHON:-}" ]; then
  BNX_SYSTEM_PYTHON="$(command -v "$PY" 2>/dev/null || true)"
  if [ -n "$BNX_SYSTEM_PYTHON" ]; then export BNX_SYSTEM_PYTHON; fi
fi
if ! command -v "$PY" >/dev/null 2>&1; then
  echo "[ERROR] No encuentro '$PY'.${PY_T:+ Este paquete es para Python $PY_T: instalalo (RHEL 8:  sudo dnf install python$PY_T )}"
  exit 1
fi
if [ -n "$PY_T" ]; then
  PY_V="$("$PY" -c 'import sys; print("%d.%d" % sys.version_info[:2])')"
  if [ "$PY_T" != "$PY_V" ]; then
    echo "[ERROR] Este paquete se armo para Python $PY_T y '$PY' es Python $PY_V: las librerias offline"
    echo "        (wheels cp${PY_T/./}) no van a instalar. Instala Python $PY_T (RHEL 8:  sudo dnf install python$PY_T )"
    echo "        y vuelve a correr (o:  PYTHON=/usr/bin/python$PY_T bash setup.sh ), o genera el paquete para Python $PY_V."
    exit 1
  fi
fi
if ! "$PY" -c 'import venv, ensurepip' >/dev/null 2>&1; then
  echo "[!] '$PY' no trae venv/ensurepip: RHEL 8:  sudo dnf install python${PY_T:-3}-pip  (o python${PY_T:-3}-devel)"
fi
if ! command -v java >/dev/null 2>&1 && [ -z "${JAVA_HOME:-}" ]; then
  echo "[!] No encuentro Java (PySpark lo necesita; 3.5 soporta Java 8/11/17). RHEL 8:  sudo dnf install java-17-openjdk-headless"
fi
echo "[1/4] Creando entorno virtual .venv ..."
"$PY" -m venv .venv

echo "[2/4] Activando e instalando dependencias ..."
. .venv/bin/activate
python -m pip install --upgrade pip >/dev/null 2>&1 || true

# Detectar vendor/ segun la version de Python: si existe,
# instalamos TODO offline con --no-index. pandas/numpy/pyspark/py4j/pytest estan
# ahi. Sin vendor/, caemos a internet (red del banco / Artifactory).
PYMINOR="$(python -c 'import sys; print(sys.version_info[1])')"
VENDOR_DIR=""
if [ "$PYMINOR" -ge 14 ] 2>/dev/null && [ -d "vendor/py314" ]; then
  VENDOR_DIR="vendor/py314"
elif [ "$PYMINOR" -ge 12 ] 2>/dev/null && [ -d "vendor/py312plus" ]; then
  VENDOR_DIR="vendor/py312plus"
elif [ "$PYMINOR" -lt 12 ] 2>/dev/null && [ -d "vendor/py38-311" ]; then
  VENDOR_DIR="vendor/py38-311"
elif [ -d "vendor/py314" ]; then
  VENDOR_DIR="vendor/py314"
elif [ -d "vendor/py312plus" ]; then
  VENDOR_DIR="vendor/py312plus"
elif [ -d "vendor/py38-311" ]; then
  VENDOR_DIR="vendor/py38-311"
fi

# vendor/bank tambien aporta wheels de deps PINNEADAS por el banco (p.ej. pandas
# 1.3.1 cp38 para Python 3.8). Se agrega a los --find-links para que pip elija la
# version correcta segun la version de Python, tanto offline como por internet.
BANK_LINKS=""
if [ -d "vendor/bank" ]; then BANK_LINKS="--find-links vendor/bank"; fi

if [ -n "$VENDOR_DIR" ] && ls "$VENDOR_DIR"/*.whl >/dev/null 2>&1; then
  python -m pip install --no-index --find-links "$VENDOR_DIR" pip setuptools wheel >/dev/null 2>&1 || true
  if ls "$VENDOR_DIR"/pyspark-*.whl >/dev/null 2>&1; then
    echo "      OFFLINE desde $VENDOR_DIR (ambiente completo, sin internet)."
    python -m pip install --no-index --pre --find-links "$VENDOR_DIR" $BANK_LINKS -r requirements.txt || {
      echo "      [!] Falto alguna wheel en vendor/: intento completar por internet (PyPI/PIP_INDEX_URL) ..."
      python -m pip install --find-links "$VENDOR_DIR" $BANK_LINKS -r requirements.txt
    }
  else
    # Paquete SIN PySpark: todas las librerias offline; PySpark online o del cluster.
    echo "      OFFLINE desde $VENDOR_DIR (sin PySpark: el resto de librerias offline)."
    mkdir -p .bnx_tmp
    grep -viE '^[[:space:]]*(pyspark|py4j)([^a-z0-9_-]|$)' requirements.txt > .bnx_tmp/requirements-sin-spark.txt
    python -m pip install --no-index --pre --find-links "$VENDOR_DIR" $BANK_LINKS -r .bnx_tmp/requirements-sin-spark.txt || {
      echo "      [!] Falto alguna wheel en vendor/: intento completar por internet (PyPI/PIP_INDEX_URL) ..."
      python -m pip install --find-links "$VENDOR_DIR" $BANK_LINKS -r .bnx_tmp/requirements-sin-spark.txt
    }
    # PySpark del SERVIDOR (modo B): pregunta/valida la ruta y enlaza el venv a ese Spark.
    if [ "$BNX_PYSPARK_MODO" = "servidor" ]; then
      bnx_spark_modo_b
    # PySpark: con BNX_SPARK=cluster se usa el del cluster (no se instala). Si no,
    # se intenta por internet (PyPI o PIP_INDEX_URL) la serie acorde al Python:
    # 3.5.6 para 3.8-3.11 y 4.0.0 para 3.12+. Si falla NO se rompe el resto.
    elif [ "${BNX_SPARK:-}" = "cluster" ]; then
      echo "      BNX_SPARK=cluster: PySpark NO se instala (se usa el Spark del cluster)."
    else
      if [ "$PYMINOR" -ge 14 ] 2>/dev/null; then SPARK_PIN="pyspark==4.1.2"; elif [ "$PYMINOR" -ge 12 ] 2>/dev/null; then SPARK_PIN="pyspark==4.0.0"; else SPARK_PIN="pyspark==3.5.6"; fi
      echo "      PySpark no viene en el paquete: instalando $SPARK_PIN + py4j por internet ..."
      if python -m pip install --retries 1 --timeout 30 "$SPARK_PIN" py4j >.bnx_tmp/pyspark-online.log 2>&1; then
        echo "      PySpark ($SPARK_PIN) instalado por internet."
      else
        echo "      [AVISO] No se pudo instalar PySpark por internet (sin acceso a PyPI/PIP_INDEX_URL)."
        echo "              El resto del entorno quedo instalado. Opciones:"
        echo "                - usar el Spark del cluster:  BNX_SPARK=cluster bash run.sh ..."
        echo "                - o generar el paquete con 'ambiente completo' (PySpark offline en vendor/)."
        echo "              Detalle: .bnx_tmp/pyspark-online.log"
      fi
    fi
  fi
  # Paquete propio en editable SIN aislamiento ni deps (ya estan instaladas; en el
  # ligero pyspark viene del cluster) para no intentar bajar nada por internet.
  python -m pip install --no-build-isolation --no-deps -e .
else
  echo "      vendor/ (PySpark) no disponible; instalando por internet (red del banco)."
  # Si estas en la red del banco, descomenta --index-url con tu Artifactory:
  # pip install -r requirements.txt --index-url https://<artifactory-interno>/simple
  # BANK_LINKS deja que pip use pandas 1.3.1 cp38 del banco si corre en Python 3.8.
  if [ "$BNX_PYSPARK_MODO" = "servidor" ]; then
    mkdir -p .bnx_tmp
    grep -viE '^[[:space:]]*(pyspark|py4j)([^a-z0-9_-]|$)' requirements.txt > .bnx_tmp/requirements-sin-spark.txt
    python -m pip install $BANK_LINKS -r .bnx_tmp/requirements-sin-spark.txt
    python -m pip install -e .
    bnx_spark_modo_b
  else
    python -m pip install $BANK_LINKS -r requirements.txt
    python -m pip install -e .
  fi
fi

# Librerias OPEN SOURCE extra que importa el codigo (cytoolz, unidecode, ...).
# Una por una: offline desde vendor/ y vendor/bank/; si no, por internet.
if [ -f requirements-extra.txt ]; then
  echo "      Instalando librerias open source extra (requirements-extra.txt) ..."
  EXTRA_LINKS="$BANK_LINKS"
  if [ -n "$VENDOR_DIR" ]; then EXTRA_LINKS="--find-links $VENDOR_DIR $EXTRA_LINKS"; fi
  grep -v '^[[:space:]]*#' requirements-extra.txt | grep -v '^[[:space:]]*$' | while read -r PKG; do
    if [ -n "$EXTRA_LINKS" ] && python -m pip install --no-index $EXTRA_LINKS "$PKG" >/dev/null 2>&1; then
      echo "        OK (offline) $PKG"
    elif python -m pip install $BANK_LINKS "$PKG" >/dev/null 2>&1; then
      echo "        OK (internet) $PKG"
    else
      echo "        [!]  No se pudo instalar $PKG (sin wheel para esta version de Python y sin internet)."
    fi
  done
fi
# Librerias INTERNAS del banco (si las hay). Preferimos OFFLINE desde vendor/bank/
# (sdist empaquetados); si no estan, caemos al Artifactory privado. El codigo de
# path (toolbox/bnmxverse/utils) se copia a ./bank_pkg y se expone via PYTHONPATH.
if [ -f requirements-bank.txt ]; then
  if ls vendor/bank/*.tar.gz >/dev/null 2>&1 || ls vendor/bank/*.whl >/dev/null 2>&1; then
    echo "      Instalando librerias internas del banco OFFLINE desde vendor/bank/ ..."
    # Las deps de las mex-lib (pandas, ...) estan en vendor/<serie>/, no en vendor/bank/.
    VLINKS=""; if [ -n "$VENDOR_DIR" ]; then VLINKS="--find-links $VENDOR_DIR"; fi
    python -m pip install --no-index --pre --find-links vendor/bank $VLINKS -r requirements-bank.txt || \\
      python -m pip install --no-index --find-links vendor/bank $VLINKS $(ls vendor/bank/mex*.whl vendor/bank/*.tar.gz 2>/dev/null) || \\
      echo "      [!]  Fallo la instalacion offline de libs del banco. Revisa vendor/bank/."
  else
    echo "      Instalando librerias internas del banco (Artifactory privado) ..."
    # Descomenta y apunta a tu Artifactory si hace falta un indice explicito:
    # python -m pip install -r requirements-bank.txt --index-url https://<artifactory-interno>/simple
    python -m pip install -r requirements-bank.txt || \
      echo "      [!]  No se pudieron instalar las libs del banco (sin acceso al Artifactory)."
  fi
fi
# toolbox / bnmxverse / utils del banco como WHEEL (bnx-bank-pkgcode): se instala con pip como el resto.
if ls vendor/bank/bnx_bank_pkgcode-*.whl >/dev/null 2>&1; then
  python -m pip install --no-index --no-deps vendor/bank/bnx_bank_pkgcode-*.whl >/dev/null 2>&1 \\
    && echo "      Modulos del banco (toolbox, bnmxverse, utils) instalados como wheel." \\
    || echo "      [!]  No se pudo instalar vendor/bank/bnx_bank_pkgcode (revisa vendor/bank/)."
fi
# Paquetes viejos (sin wheel): modulos de path del banco (toolbox, bnmxverse, utils) en PYTHONPATH.
if [ -d vendor/bank/pkgcode ]; then
  mkdir -p bank_pkg
  cp -R vendor/bank/pkgcode/* bank_pkg/ 2>/dev/null || true
  echo "      Modulos de path del banco en ./bank_pkg (toolbox, ...). Exporta antes de correr:"
  echo '        export PYTHONPATH="$PWD/bank_pkg:$PYTHONPATH"'
fi

# Al instalar PySpark OFFLINE desde el wheel, algunos servidores (umask estricto)
# dejan los scripts de pyspark/bin sin permiso de ejecucion, y spark-submit falla
# con 'Permission denied'. Les restauramos el bit +x.
PYSPARK_HOME="$(python -c 'import os, pyspark; print(os.path.dirname(pyspark.__file__))' 2>/dev/null || true)"
if [ -n "$PYSPARK_HOME" ] && [ "$BNX_PYSPARK_MODO" != "servidor" ]; then
  echo "      Ajustando permisos de ejecucion en $PYSPARK_HOME/bin y /sbin ..."
  chmod -R +x "$PYSPARK_HOME/bin" 2>/dev/null || true
  chmod -R +x "$PYSPARK_HOME/sbin" 2>/dev/null || true
fi

# ---------------------------------------------------------------------------
# Config de Spark DENTRO del venv (queda fija al bajar/montar el paquete):
#  - .venv/spark_conf = copia de la config del cluster (spark-defaults, hive-site,
#    core/hdfs/yarn-site, spark-env) + los ajustes BNX al final.
#  - el 'activate' del venv exporta SPARK_CONF_DIR/HADOOP_CONF_DIR y un tmp propio
#    para Java (JAVA_TOOL_OPTIONS), asi CUALQUIER uso del venv (run.sh, python
#    main.py, pyspark, spark-submit) ve el metastore/HDFS del cluster y no usa /tmp
#    (noexec en servidores del banco: rompe zstd-jni/snappy nativos).
# ---------------------------------------------------------------------------
VENV_ABS="$(cd .venv && pwd)"
PKG_ABS="$(pwd)"
SPARK_VENV_CONF="$VENV_ABS/spark_conf"
BNX_TMP_ABS="${BNX_TMPDIR:-$PKG_ABS/.bnx_tmp}"
mkdir -p "$SPARK_VENV_CONF" "$BNX_TMP_ABS"
CLUSTER_CONF=""
for d in "${SPARK_CONF_DIR:-}" /etc/spark/conf /etc/spark3/conf /etc/spark2/conf /opt/cloudera/parcels/CDH/lib/spark/conf; do
  if [ -n "$d" ] && [ -d "$d" ] && [ "$d" != "$SPARK_VENV_CONF" ] && \
     { [ -f "$d/spark-defaults.conf" ] || [ -f "$d/hive-site.xml" ]; }; then
    CLUSTER_CONF="$d"; break
  fi
done
if [ -n "$CLUSTER_CONF" ]; then
  echo "      Copiando config de Spark del cluster ($CLUSTER_CONF) a .venv/spark_conf ..."
  cp -R "$CLUSTER_CONF"/. "$SPARK_VENV_CONF"/ 2>/dev/null || true
  chmod -R u+w "$SPARK_VENV_CONF" 2>/dev/null || true
  # spark-env.sh del cluster (CDH) mete los jars del cluster en el classpath: con el
  # PySpark del venv choca. Se guarda aparte; spark-submit del cluster usa su conf.
  if [ -f "$SPARK_VENV_CONF/spark-env.sh" ]; then
    mv -f "$SPARK_VENV_CONF/spark-env.sh" "$SPARK_VENV_CONF/spark-env.sh.cluster"
  fi
else
  echo "      (no se encontro config de Spark del cluster; .venv/spark_conf solo con ajustes BNX)"
fi
[ -f "$SPARK_VENV_CONF/hive-site.xml" ] || { [ -f /etc/hive/conf/hive-site.xml ] && cp /etc/hive/conf/hive-site.xml "$SPARK_VENV_CONF"/; } || true
for x in core-site.xml hdfs-site.xml yarn-site.xml; do
  [ -f "$SPARK_VENV_CONF/$x" ] || { [ -f "/etc/hadoop/conf/$x" ] && cp "/etc/hadoop/conf/$x" "$SPARK_VENV_CONF"/; } || true
done
# Ajustes BNX (se reescriben en cada setup; van AL FINAL para ganar).
touch "$SPARK_VENV_CONF/spark-defaults.conf"
sed -i.bak '/# >>> BNX/,/# <<< BNX/d' "$SPARK_VENV_CONF/spark-defaults.conf" 2>/dev/null || true
rm -f "$SPARK_VENV_CONF/spark-defaults.conf.bak"
cat >> "$SPARK_VENV_CONF/spark-defaults.conf" <<EOF_BNX
# >>> BNX (framework_mlops_v2)
# lz4 tiene fallback Java puro; zstd-jni nativo falla con /tmp noexec.
spark.io.compression.codec                  lz4
spark.shuffle.mapStatus.compression.codec   lz4
spark.local.dir                             $BNX_TMP_ABS
# <<< BNX
EOF_BNX
if [ -f "$SPARK_VENV_CONF/hive-site.xml" ]; then
  echo "      hive-site.xml en .venv/spark_conf -> el venv ve el metastore del cluster."
else
  echo "      [!]  sin hive-site.xml: el venv usara un metastore LOCAL (no vera tablas del banco)."
  echo "         Copia el del cluster a $SPARK_VENV_CONF/ y vuelve a activar el venv."
fi
# Hook en el activate del venv (idempotente).
ACT=".venv/bin/activate"
sed -i.bak '/# >>> BNX env/,/# <<< BNX env/d' "$ACT" 2>/dev/null || true
rm -f "$ACT.bak"
cat >> "$ACT" <<EOF_ACT
# >>> BNX env (framework_mlops_v2)
export SPARK_CONF_DIR="$SPARK_VENV_CONF"
export BNX_CLUSTER_SPARK_CONF="$CLUSTER_CONF"
if [ -z "\\${HADOOP_CONF_DIR:-}" ] && [ -d /etc/hadoop/conf ]; then export HADOOP_CONF_DIR=/etc/hadoop/conf; fi
export BNX_TMPDIR="$BNX_TMP_ABS"
mkdir -p "\\$BNX_TMPDIR" 2>/dev/null || true
export TMPDIR="\\$BNX_TMPDIR"
case " \\${JAVA_TOOL_OPTIONS:-} " in
  *"-Djava.io.tmpdir="*) ;;
  *) export JAVA_TOOL_OPTIONS="-Djava.io.tmpdir=\\$BNX_TMPDIR -Dorg.xerial.snappy.tempdir=\\$BNX_TMPDIR -Djna.tmpdir=\\$BNX_TMPDIR \\${JAVA_TOOL_OPTIONS:-}" ;;
esac
export BNX_IO_CODEC="\\${BNX_IO_CODEC:-lz4}"
# <<< BNX env
EOF_ACT
echo "      Entorno virtual configurado: SPARK_CONF_DIR=.venv/spark_conf, tmp=$BNX_TMP_ABS"
. "$ACT"

@@LIBOMP@@
bnx_libomp_fix
bnx_libgomp_check

echo "[3/4] Verificando dependencias (check_env.py) ..."
# Avisa si falta alguna libreria que el codigo importa (no aborta el montaje).
python check_env.py || echo "  [!]  Faltan librerias (ver arriba). Instalalas antes de produccion."

# Verificacion FINAL de lo que importa el DRIVER (pandas, numpy, toolbox, bnmxverse, utils,
# mex-lib* y pyspark segun el modo: incluido o del servidor). Con el python de ESTE venv, que
# es el que run.sh le da al spark-submit del cluster. Si falta algo, setup.sh termina con error.
echo "      python del venv: $(command -v python) ($(python -V 2>&1))"
BNX_DRIVER_OK=1
BNX_PYSPARK_MODE="$BNX_PYSPARK_MODO" python check_env.py --driver || BNX_DRIVER_OK=0

if [ "$BNX_RUN_TEST" = "1" ]; then
  echo "[4/4] Ejecutando pruebas (pytest) ..."
  pytest -q || echo "  (pytest requiere pyspark + Java; revisa el entorno)"
else
  echo "[4/4] Entorno montado (pruebas omitidas; usa --test para correrlas)."
fi

BNX_SETUP_FIN=1
echo ""
if [ "$BNX_DRIVER_OK" != "1" ]; then
  echo "[ERROR] setup.sh termino pero el venv NO esta completo (ver 'FALTA' arriba): run.sh no va a funcionar."
  echo "        Python usado: $(command -v python)"
  echo "        Revisa vendor/OFFLINE_FALTANTES.txt y vuelve a correr:  bash setup.sh"
  rm -f .venv/.bnx_setup_ok
  exit 1
fi
: > .venv/.bnx_setup_ok
echo "[OK] Entorno listo (python: $(command -v python)). Para correr el modelo:  bash run.sh"
echo "   Datos reales:  bash run.sh --config cfg.json"
'''

# run.sh — SOLO ejecuta el modelo (main.py) en el entorno ya montado por setup.sh.
_RUN_SH = '''#!/usr/bin/env bash
# run.sh - corre el modelo (main.py) con el entorno de setup.sh. No instala nada.
# Uso:  bash run.sh                      (modo demo, datos sinteticos)
#       bash run.sh --config cfg.json    (datos reales)
set -e
cd "$(dirname "$0")"

if [ ! -f .venv/bin/activate ]; then
  echo "[ERROR] No existe .venv. Monta el entorno primero:  bash setup.sh" >&2
  exit 1
fi
# PySpark del SERVIDOR (modo B): setup.sh guardo la ruta en .bnx_spark.env.
BNX_SPARK_SERVIDOR=0
if [ -f .bnx_spark.env ]; then
  . ./.bnx_spark.env
  export SPARK_HOME
  BNX_SPARK_SERVIDOR=1
fi
# Spark del CLUSTER (opcional): BNX_SPARK=cluster bash run.sh ...
# Usa el spark-submit del nodo (el mismo metastore que Hue/beeline/pyspark del
# cluster) con el Python del venv para las librerias. Se busca ANTES de activar el
# venv para no tomar el spark-submit que trae el pyspark de pip.
CLUSTER_SUBMIT=""
if [ "${BNX_SPARK:-}" = "cluster" ]; then
  CLUSTER_SUBMIT="${BNX_SPARK_SUBMIT:-${BNX_SPARK_SUBMIT_CFG:-$(command -v spark3-submit || command -v spark-submit || true)}}"
  if [ -z "$CLUSTER_SUBMIT" ]; then
    echo "[ERROR] BNX_SPARK=cluster pero no hay spark-submit del cluster en el PATH." >&2
    echo "   Indica la ruta: BNX_SPARK_SUBMIT=/ruta/spark-submit BNX_SPARK=cluster bash run.sh ..." >&2
    exit 1
  fi
fi
# SPARK_CONF_DIR que traia el usuario (el 'activate' del venv lo pisa con .venv/spark_conf).
BNX_SPARK_CONF_DIR_USUARIO="${SPARK_CONF_DIR:-}"
. .venv/bin/activate
if [ "$BNX_SPARK_SERVIDOR" = "1" ]; then
  # `import pyspark` en el venv usa el Spark del servidor (symlink/.pth de setup.sh + PYTHONPATH)
  if [ -n "${BNX_SPARK_PYPATH:-}" ]; then export PYTHONPATH="$BNX_SPARK_PYPATH:${PYTHONPATH:-}"; fi
  echo "[run.sh] PySpark del SERVIDOR: SPARK_HOME=$SPARK_HOME (Spark ${BNX_SPARK_VERSION:-?})"
fi

# bash run.sh --limpiar-deps-hdfs : borra en BNX_DEPS_HDFS los bnxdeps_*.tgz que NO son del venv actual
# (pide confirmacion en tty; sin tty solo lista, salvo BNX_LIMPIAR_SI=1). No lanza el job.
if [ "${1:-}" = "--limpiar-deps-hdfs" ]; then
  if [ -z "${BNX_DEPS_HDFS:-}" ]; then
    echo "[run.sh] Indica la carpeta: BNX_DEPS_HDFS=hdfs:///user/<usuario>/bnx/deps bash run.sh --limpiar-deps-hdfs" >&2
    exit 1
  fi
  if ! command -v hdfs >/dev/null 2>&1; then echo "[run.sh] 'hdfs' no esta en el PATH." >&2; exit 1; fi
  mkdir -p .bnx_tmp
  python bnx_sparkconf.py --empaquetar-deps --dir .bnx_deps --mods numpy --out .bnx_tmp/deps_hdfs.env >/dev/null
  . ./.bnx_tmp/deps_hdfs.env
  _HD="${BNX_DEPS_HDFS%/}"
  _ACTUAL="bnxdeps_${BNX_DEPS_HASH}.tgz"
  _LS=$(hdfs dfs -ls "$_HD" 2>/dev/null | awk '{print $NF}' | grep '/bnxdeps_[^/]*[.]tgz$' || true)
  _VIEJOS=""
  echo "[run.sh] versiones en $_HD (actual: $_ACTUAL):"
  for _f in $_LS; do
    if [ "$(basename "$_f")" = "$_ACTUAL" ]; then echo "   $_f   <- actual"; else echo "   $_f"; _VIEJOS="$_VIEJOS $_f"; fi
  done
  if [ -z "$_VIEJOS" ]; then echo "[run.sh] no hay versiones viejas que borrar."; exit 0; fi
  _OK=0
  if [ "${BNX_LIMPIAR_SI:-0}" = "1" ]; then
    _OK=1
  elif [ -t 0 ]; then
    printf "[run.sh] Borrar las versiones viejas (sin '<- actual')? [s/N] "
    read -r _R || _R=""
    case "$_R" in s|S|y|Y|si|SI) _OK=1 ;; esac
  else
    echo "[run.sh] sin terminal: no se borra nada (BNX_LIMPIAR_SI=1 para confirmar)."
  fi
  if [ "$_OK" = "1" ]; then
    for _f in $_VIEJOS; do hdfs dfs -rm -skipTrash "$_f" || echo "[run.sh] AVISO: no se pudo borrar $_f" >&2; done
  fi
  exit 0
fi

@@LIBOMP@@
bnx_libomp_fix

# Modulos de path del banco (toolbox, bnmxverse, utils) que dejo setup.sh.
if [ -d bank_pkg ]; then export PYTHONPATH="$PWD/bank_pkg:${PYTHONPATH:-}"; fi

# Verificacion PREVIA (rapida): el python del venv debe poder importar lo que necesita el
# driver. Si falta algo se dice QUE falta y como arreglarlo ANTES de lanzar Spark (si no,
# spark-submit hace fila en YARN y revienta con "No module named pandas").
# BNX_SKIP_PREFLIGHT=1 la salta.
BNX_PY="$PWD/.venv/bin/python"
if [ "${BNX_SKIP_PREFLIGHT:-0}" != "1" ]; then
  # pandas/numpy solo se exigen si el paquete los incluye (requirements.txt)
  _NEED=""
  for _m in pandas numpy; do
    if grep -qiE "^[[:space:]]*$_m([[:space:]<>=!~;]|$)" requirements.txt 2>/dev/null; then _NEED="$_NEED $_m"; fi
  done
  if [ -d bank_src/toolbox ] || [ -d bank_pkg/toolbox ] || [ -d bank_src/jobs ]; then _NEED="$_NEED toolbox"; fi
  # PySpark en el venv solo hace falta fuera del modo cluster (spark-submit del nodo trae el suyo).
  if [ -z "$CLUSTER_SUBMIT" ]; then _NEED="$_NEED pyspark"; fi
  mkdir -p .bnx_tmp
  cat > .bnx_tmp/preflight.py <<'EOF_PREFLIGHT'
import importlib
import importlib.util
import os
import sys
for _d in ("bank_src", "bank_pkg"):
    if os.path.isdir(_d):
        sys.path.append(os.path.abspath(_d))
falta, vers = [], []
for m in sys.argv[1:]:
    try:
        if m == "toolbox":
            if importlib.util.find_spec(m) is None:
                raise ImportError("no esta en bank_src/, bank_pkg/ ni instalado en el venv")
        else:
            mod = importlib.import_module(m)
            vers.append("%s %s" % (m, getattr(mod, "__version__", "?")))
    except Exception as e:
        falta.append("%s (%s: %s)" % (m, type(e).__name__, str(e).strip()[:100]))
print("%s (Python %s)" % (sys.executable, sys.version.split()[0]))
if falta:
    for f in falta:
        print("FALTA: " + f)
    sys.exit(1)
print("OK: " + ", ".join(vers))
EOF_PREFLIGHT
  if _PF="$("$BNX_PY" .bnx_tmp/preflight.py $_NEED 2>&1)"; then
    echo "[run.sh] python del venv: $(echo "$_PF" | head -1)"
    echo "[run.sh] verificacion previa de imports del driver: $(echo "$_PF" | tail -1)"
    if [ ! -f .venv/.bnx_setup_ok ]; then
      echo "[run.sh] AVISO: .venv sin la marca de setup completo (.venv/.bnx_setup_ok): si setup.sh se interrumpio, vuelve a correr 'bash setup.sh'."
    fi
  else
    echo "[run.sh] ERROR: el python del venv no puede importar lo que necesita el driver." >&2
    echo "[run.sh] python: $(echo "$_PF" | head -1)" >&2
    echo "$_PF" | grep '^FALTA:' | sed 's/^/[run.sh]   /' >&2 || true
    echo "[run.sh] Como resolverlo (en este orden):" >&2
    echo "[run.sh]   1) bash setup.sh            (monta/repara el venv; debe terminar con [OK])" >&2
    echo "[run.sh]   2) revisa vendor/OFFLINE_FALTANTES.txt (wheels que el paquete no pudo traer)" >&2
    echo "[run.sh]   3) $BNX_PY check_env.py --driver   (diagnostico de imports del driver)" >&2
    echo "[run.sh]   4) $BNX_PY -c 'import <modulo faltante>'   (debe terminar sin error)" >&2
    echo "[run.sh] No se lanzo Spark. (BNX_SKIP_PREFLIGHT=1 salta esta verificacion)" >&2
    exit 1
  fi
fi

# Metastore del CLUSTER: el PySpark del venv es standalone y, sin hive-site.xml,
# crea un metastore LOCAL vacio (las tablas del banco "no existen"). Si el nodo
# tiene la config de Spark/Hive del cluster (Cloudera/edge node), la usamos.
if [ -z "$CLUSTER_SUBMIT" ] && [ -z "${SPARK_CONF_DIR:-}" ]; then
  for d in "${SPARK_HOME:+$SPARK_HOME/conf}" /etc/spark/conf /etc/spark3/conf /etc/spark2/conf /opt/cloudera/parcels/CDH/lib/spark/conf; do
    if [ -f "$d/hive-site.xml" ]; then export SPARK_CONF_DIR="$d"; break; fi
  done
  if [ -z "${SPARK_CONF_DIR:-}" ] && [ -f /etc/hive/conf/hive-site.xml ]; then
    # Solo hay hive-site.xml de Hive: armamos un conf dir propio con el.
    mkdir -p .bnx_tmp/spark_conf
    cp /etc/hive/conf/hive-site.xml .bnx_tmp/spark_conf/
    export SPARK_CONF_DIR="$PWD/.bnx_tmp/spark_conf"
  fi
fi
if [ -z "${HADOOP_CONF_DIR:-}" ] && [ -d /etc/hadoop/conf ]; then
  export HADOOP_CONF_DIR=/etc/hadoop/conf
fi
if [ -n "$CLUSTER_SUBMIT" ]; then
  :   # modo cluster: el conf dir se elige abajo (SIN reemplazar la config del cluster)
elif [ -n "${SPARK_CONF_DIR:-}" ]; then
  echo "[run.sh] SPARK_CONF_DIR=$SPARK_CONF_DIR (metastore del cluster)"
else
  echo "[run.sh] AVISO: no se encontro hive-site.xml; Spark usara un metastore LOCAL."
  echo "         Para tablas del banco: export SPARK_CONF_DIR=<dir con hive-site.xml>"
fi

# CLUSTER: elige el conf dir de Spark del CLUSTER y NO lo reemplaza. Un conf dir con SOLO
# hive-site.xml pierde spark-defaults.conf (spark.pyspark.python, yarn jars, ...), spark-env.sh
# y yarn-conf/ del cluster. Si el del cluster no trae hive-site.xml se arma una COPIA COMPLETA
# + hive-site.xml. Candidatos: BNX_CLUSTER_CONF_DIR, el de setup.sh (BNX_CLUSTER_SPARK_CONF),
# el SPARK_CONF_DIR del usuario, y BNX_CLUSTER_CONF_CANDIDATOS (lista separada por ':') o
# /etc/spark3/conf, /etc/spark/conf, /etc/spark2/conf, /opt/cloudera/parcels/...
bnx_conf_cluster() {
  _ours1="$PWD/.venv/spark_conf"; _ours2="$PWD/.bnx_tmp/spark_conf"
  case "$(basename "$CLUSTER_SUBMIT")" in
    spark3*) _def="/etc/spark3/conf:/opt/cloudera/parcels/SPARK3/lib/spark3/conf:/etc/spark/conf" ;;
    *) _def="/etc/spark/conf:/etc/spark3/conf:/opt/cloudera/parcels/SPARK3/lib/spark3/conf" ;;
  esac
  _def="$_def:/etc/spark2/conf:/opt/cloudera/parcels/CDH/lib/spark/conf"
  _lista="${BNX_CLUSTER_CONF_DIR:-}:${BNX_CLUSTER_SPARK_CONF:-}:${BNX_SPARK_CONF_DIR_USUARIO:-}:${BNX_CLUSTER_CONF_CANDIDATOS:-$_def}"
  _SEL=""; _OLDIFS="$IFS"; IFS=":"
  for _d in $_lista; do
    if [ -z "$_d" ] || [ "$_d" = "$_ours1" ] || [ "$_d" = "$_ours2" ]; then continue; fi
    if [ -d "$_d" ] && { [ -f "$_d/spark-defaults.conf" ] || [ -f "$_d/spark-env.sh" ]; }; then _SEL="$_d"; break; fi
  done
  IFS="$_OLDIFS"
  BNX_CONF_MOTIVO=""
  if [ -z "$_SEL" ]; then
    unset SPARK_CONF_DIR
    BNX_CONF_MOTIVO="no hay config de Spark del cluster en: $_lista; spark-submit usa su SPARK_CONF_DIR por defecto (no se inventa uno)"
    return 0
  fi
  _HIVE=""
  for _h in "$_SEL/hive-site.xml" "$_SEL/yarn-conf/hive-site.xml"; do
    if [ -f "$_h" ]; then _HIVE="$_h"; break; fi
  done
  if [ -n "$_HIVE" ]; then
    export SPARK_CONF_DIR="$_SEL"
    BNX_CONF_MOTIVO="config del CLUSTER tal cual ($_SEL; hive-site.xml: $_HIVE); no se copia ni se reemplaza"
    return 0
  fi
  _EXT=""
  for _h in "${BNX_HIVE_SITE:-}" /etc/hive/conf/hive-site.xml; do
    if [ -n "$_h" ] && [ -f "$_h" ]; then _EXT="$_h"; break; fi
  done
  if [ -n "$_EXT" ]; then
    rm -rf "$_ours2"; mkdir -p "$_ours2"
    if cp -RL "$_SEL"/. "$_ours2"/ 2>/dev/null; then
      cp "$_EXT" "$_ours2/hive-site.xml"
      export SPARK_CONF_DIR="$_ours2"
      BNX_CONF_MOTIVO="COPIA COMPLETA de $_SEL + hive-site.xml de $_EXT (el conf del cluster no trae hive-site.xml; se conservan spark-defaults.conf, spark-env.sh, yarn-conf/...)"
      return 0
    fi
    echo "[run.sh] AVISO: no se pudo copiar $_SEL a $_ours2; se usa el original sin hive-site.xml" >&2
  fi
  export SPARK_CONF_DIR="$_SEL"
  BNX_CONF_MOTIVO="config del CLUSTER tal cual ($_SEL); AVISO: sin hive-site.xml (si 'la base no existe': BNX_HIVE_SITE=/ruta/hive-site.xml)"
}

if [ -n "$CLUSTER_SUBMIT" ]; then
  echo "[run.sh] Spark del CLUSTER: $CLUSTER_SUBMIT (driver: python del venv; executors: python del cluster)"
  # Solo el DRIVER usa el venv. NO se exporta PYSPARK_PYTHON: PySpark lo manda a los executors y
  # los workers no tienen el venv (no se instala en otros nodos). Con BNX_ENVIAR_VENV=1 si.
  export PYSPARK_DRIVER_PYTHON="$PWD/.venv/bin/python"
  # El venv SOLO existe en el edge: ninguna ruta dentro de el puede llegar a los executors
  # (PYSPARK_PYTHON del entorno, spark.pyspark.python, spark.executorEnv.PYSPARK_PYTHON, ...).
  bnx_en_venv() {
    case "$1" in
      ./*|bnxenv/*) return 1 ;;   # relativas al contenedor YARN (archivo enviado con --archives): validas en los nodos
    esac
    _bv1="$PWD/.venv/"; _bv2="$(pwd -P)/.venv/"; _bv3="$(cd .venv && pwd -P)/"
    case "$1" in "$_bv1"*|"$_bv2"*|"$_bv3"*) return 0 ;; esac
    # misma carpeta alcanzada por otro camino (symlink al paquete): se compara el directorio resuelto
    _bd="$(cd "$(dirname "$1")" 2>/dev/null && pwd -P)" || _bd=""
    case "${_bd:+$_bd/}" in "$_bv2"*|"$_bv3"*) return 0 ;; esac
    return 1
  }
  if [ -n "${PYSPARK_PYTHON:-}" ] && bnx_en_venv "$PYSPARK_PYTHON"; then
    echo "[run.sh] AVISO: PYSPARK_PYTHON=$PYSPARK_PYTHON apunta al venv del edge (no existe en los nodos): se ignora (unset)." >&2
    unset PYSPARK_PYTHON
  fi
  if [ -n "${BNX_EXECUTOR_PYTHON:-}" ] && bnx_en_venv "$BNX_EXECUTOR_PYTHON"; then
    echo "[run.sh] ERROR: BNX_EXECUTOR_PYTHON=$BNX_EXECUTOR_PYTHON es el Python del venv, que solo existe en el edge node." >&2
    echo "[run.sh]   Usa el Python que tienen los NODOS (linea 'BNX_EXECUTOR_PYTHON=...' de: spark3-submit --master yarn --deploy-mode client probe_workers.py). No se lanzo Spark." >&2
    exit 1
  fi
  export BNX_CLUSTER_SPARK=1
  # /tmp del servidor suele estar 'noexec': las librerias nativas que Java extrae
  # ahi (zstd-jni, snappy) fallan con "failed to map segment from shared object".
  # Le damos a la JVM del driver un tmp propio y usamos lz4 (tiene fallback Java
  # puro) para la compresion interna de Spark en vez de zstd.
  BNX_TMP="${BNX_TMPDIR:-$PWD/.bnx_tmp}"
  mkdir -p "$BNX_TMP"
  export TMPDIR="$BNX_TMP"
  JOPTS="-Djava.io.tmpdir=$BNX_TMP -Dorg.xerial.snappy.tempdir=$BNX_TMP -Djna.tmpdir=$BNX_TMP"
  echo "[run.sh] tmp de la JVM: $BNX_TMP (no /tmp)"
  # spark-submit del CLUSTER con SU config (spark-env.sh/yarn-conf); los ajustes
  # BNX (lz4, tmp) van por --conf / --driver-java-options.
  bnx_conf_cluster
  echo "[run.sh] SPARK_CONF_DIR=${SPARK_CONF_DIR:-(sin definir: spark-submit usa el suyo)}"
  echo "[run.sh]   por que: $BNX_CONF_MOTIVO"
  if [ -n "${SPARK_CONF_DIR:-}" ]; then
    # lo que el cluster fija para python (spark-defaults.conf / spark-env.sh): el driver lo
    # pisa con --conf spark.pyspark.driver.python; los executors lo respetan.
    { grep -hE '^[[:space:]]*spark[.]pyspark[.]' "$SPARK_CONF_DIR/spark-defaults.conf" 2>/dev/null || true
      grep -hE 'PYSPARK_(DRIVER_)?PYTHON' "$SPARK_CONF_DIR/spark-env.sh" 2>/dev/null || true; } | head -6 | while IFS= read -r _l; do
      echo "[run.sh]   el cluster fija: $_l"
    done
  fi
  echo "[run.sh] python del DRIVER: $PWD/.venv/bin/python (--conf spark.pyspark.driver.python + PYSPARK_DRIVER_PYTHON)"
  # YARN: spark-submit --master yarn necesita yarn-site.xml (HADOOP_CONF_DIR o
  # YARN_CONF_DIR) para encontrar el ResourceManager.
  if [ -z "${YARN_CONF_DIR:-}" ] && [ -n "${HADOOP_CONF_DIR:-}" ]; then export YARN_CONF_DIR="$HADOOP_CONF_DIR"; fi
  echo "[run.sh] master=${BNX_MASTER:-yarn} HADOOP_CONF_DIR=${HADOOP_CONF_DIR:-(vacio)} YARN_CONF_DIR=${YARN_CONF_DIR:-(vacio)}"
  if [ -z "${HADOOP_CONF_DIR:-}${YARN_CONF_DIR:-}" ]; then
    echo "[run.sh] AVISO: sin HADOOP_CONF_DIR/YARN_CONF_DIR spark-submit no encuentra YARN." >&2
  fi
  # Recursos de YARN (cola, executors, memoria, shuffle.partitions): del spark.json del
  # banco (--settings/CONF_PATH; --env uat usa spark_queue_uat), o del cfg, o valores por
  # defecto. spark.executor.* y spark.yarn.queue son de LANZAMIENTO: van como un --conf por
  # clave (NO --properties-file: reemplazaria el spark-defaults.conf del cluster).
  # Se pueden ajustar con BNX_SPARK_CONF="k=v;k2=v2" y BNX_DRIVER_MEMORY=8g.
  CONF_ARGS=()
  if [ -f bnx_sparkconf.py ]; then
    python bnx_sparkconf.py --modo cluster --out .bnx_spark_conf.properties -- "$@" \
      || echo "[run.sh] AVISO: no se pudo calcular la conf de recursos; se usa la del cluster." >&2
    if [ -f .bnx_spark_conf.properties ]; then
      while IFS= read -r _l || [ -n "$_l" ]; do
        if [ -n "$_l" ]; then CONF_ARGS+=(--conf "$_l"); fi
      done < .bnx_spark_conf.properties
    fi
  fi
  # OPCIONAL (apagado): BNX_ENVIAR_VENV=1 empaqueta el .venv y lo envia a los executors.
  # Aun asi los nodos necesitan python3.11 en la MISMA ruta. Solo para jobs con udf/rdd.
  ARCH_ARGS=()
  if [ "${BNX_ENVIAR_VENV:-0}" = "1" ]; then
    if [ ! -f .bnx_venv.tar.gz ]; then
      echo "[run.sh] BNX_ENVIAR_VENV=1: empaquetando .venv -> .bnx_venv.tar.gz (puede pesar cientos de MB)"
      tar -czf .bnx_venv.tar.gz .venv
    fi
    ARCH_ARGS=(--archives ".bnx_venv.tar.gz#bnxenv" \
      --conf "spark.pyspark.python=./bnxenv/.venv/bin/python")
  fi
  # Python en los EXECUTORS (UDF/rdd/pandas_udf...): SIN instalar nada en los otros nodos.
  # Si el codigo (modelo + bank_src + wheels del banco) ejecuta Python en los workers, se envia
  # el site-packages del venv con el job (--archives <tgz>#bnxdeps + executorEnv.PYTHONPATH) tras
  # un PROBE (mini job en YARN) que comprueba que el Python de los executors es de la misma
  # version menor. BNX_DEPS_EXECUTORS=0 lo desactiva; BNX_EXECUTOR_PYTHON=/ruta/python3.11 fija
  # el Python de los executors; BNX_PROBE_IGNORAR=1 sigue aunque el probe diga que no sirve.
  DEPS_ARGS=()
  if [ -n "${BNX_EXECUTOR_PYTHON:-}" ]; then
    DEPS_ARGS+=(--conf "spark.pyspark.python=$BNX_EXECUTOR_PYTHON" --conf "spark.executorEnv.PYSPARK_PYTHON=$BNX_EXECUTOR_PYTHON")
    export PYSPARK_PYTHON="$BNX_EXECUTOR_PYTHON"   # el DRIVER sigue con PYSPARK_DRIVER_PYTHON (venv)
    echo "[run.sh] python de los EXECUTORS: $BNX_EXECUTOR_PYTHON (BNX_EXECUTOR_PYTHON)"
  fi
  if [ "${BNX_DEPS_EXECUTORS:-1}" = "0" ]; then
    echo "[run.sh] BNX_DEPS_EXECUTORS=0: no se envian librerias a los executors (los workers usan su Python tal cual)"
  elif [ "${BNX_ENVIAR_VENV:-0}" = "1" ]; then
    :   # el venv completo ya viaja con BNX_ENVIAR_VENV
  elif [ -f bnx_sparkconf.py ]; then
    mkdir -p .bnx_tmp
    _WS=0
    python bnx_sparkconf.py --scan-workers --out .bnx_workers_python.json --wheels .venv/bnx_vendor_cache/banco/wheels bank_src framework_mlops_v2 || _WS=$?
    if [ "${BNX_DEPS_FORZAR:-0}" = "1" ]; then _WS=10; fi
    # Si los executors YA tienen Python de la misma version con numpy/pandas (p.ej. el python de un parcel de
    # conda de Cloudera, o el de BNX_EXECUTOR_PYTHON) se usa ESE python y NO se envia el venv. Un mini job
    # (probe) lo comprueba sin enviar nada. BNX_DEPS_ENVIAR=1 (o BNX_DEPS_FORZAR=1) se salta este atajo y
    # envia siempre las librerias del venv; BNX_EXECUTOR_MODS=numpy,pandas,<otras> cambia lo exigido.
    if [ "$_WS" = "10" ] && [ "${BNX_DEPS_FORZAR:-0}" != "1" ] && [ "${BNX_DEPS_ENVIAR:-0}" != "1" ]; then
      _XK="$(printf '%s|%s|%s' "${BNX_EXECUTOR_PYTHON:-}" "${BNX_MASTER:-yarn}" "${BNX_EXECUTOR_MODS:-numpy,pandas}" | cksum | cut -d' ' -f1)"
      _XF=".bnx_tmp/probe_sinlibs_$_XK.json"
      _XR=0
      if [ -f "$_XF" ] && [ "${BNX_PROBE_FORZAR:-0}" != "1" ] && [ -z "$(find "$_XF" -mmin +"${BNX_PROBE_TTL_MIN:-720}" 2>/dev/null)" ]; then
        python bnx_sparkconf.py --probe-estado --out "$_XF" || _XR=$?
      else
        echo "[run.sh] PROBE de los executors SIN enviar librerias (mini job en YARN: Python y numpy/pandas que ya tienen los nodos)..."
        rm -f "$_XF"
        "$CLUSTER_SUBMIT" --master "${BNX_MASTER:-yarn}" --deploy-mode client \
          --driver-java-options "$JOPTS" \
          --conf "spark.pyspark.driver.python=$PWD/.venv/bin/python" \
          ${CONF_ARGS[@]+"${CONF_ARGS[@]}"} \
          --conf spark.dynamicAllocation.initialExecutors=1 --conf spark.dynamicAllocation.minExecutors=1 \
          --conf spark.dynamicAllocation.maxExecutors=2 \
          ${DEPS_ARGS[@]+"${DEPS_ARGS[@]}"} \
          bnx_sparkconf.py --probe --mods="${BNX_EXECUTOR_MODS:-numpy,pandas}" --out "$_XF" >.bnx_tmp/probe_sinlibs.log 2>&1 || _XR=$?
      fi
      _XPY=""
      if [ "$_XR" = "0" ] && [ -f "$_XF" ]; then _XPY="$(python bnx_sparkconf.py --probe-python --out "$_XF" 2>/dev/null || true)"; fi
      if [ -n "$_XPY" ]; then
        if [ -z "${BNX_EXECUTOR_PYTHON:-}" ]; then DEPS_ARGS+=(--conf "spark.pyspark.python=$_XPY"); fi
        DEPS_ARGS+=(--conf "spark.executorEnv.PYSPARK_PYTHON=$_XPY")
        export PYSPARK_PYTHON="$_XPY"   # el DRIVER sigue con PYSPARK_DRIVER_PYTHON (venv)
        echo "[run.sh] los EXECUTORS ya tienen un Python con numpy/pandas (misma version que el driver): $_XPY"
        echo "[run.sh]   se usan tal cual (spark.pyspark.python + PYSPARK_PYTHON) y NO se envia el venv. (BNX_DEPS_ENVIAR=1 lo envia igual)"
        _WS=11
      else
        echo "[run.sh] los executors no tienen ese Python con numpy/pandas (ver .bnx_tmp/probe_sinlibs.log): se envian las librerias del venv."
      fi
    fi
    if [ "$_WS" = "10" ]; then
      _DE=0
      python bnx_sparkconf.py --empaquetar-deps --dir .bnx_deps --mods numpy,pandas,unidecode,dateutil,cytoolz --out .bnx_tmp/deps.env || _DE=$?
      if [ "$_DE" != "0" ] || [ ! -f .bnx_tmp/deps.env ]; then
        echo "[run.sh] AVISO: no se pudo empaquetar el site-packages del venv; los executors usaran su Python tal cual." >&2
      else
        . ./.bnx_tmp/deps.env
        _EPP="./bnxdeps"
        _PREV=$(grep -h '^spark[.]executorEnv[.]PYTHONPATH=' .bnx_spark_conf.properties 2>/dev/null | tail -1 | cut -d= -f2-)
        if [ -z "$_PREV" ] && [ -n "${SPARK_CONF_DIR:-}" ]; then
          _PREV=$(grep -hE '^[[:space:]]*spark[.]executorEnv[.]PYTHONPATH' "$SPARK_CONF_DIR/spark-defaults.conf" 2>/dev/null | tail -1 | sed -E 's/^[^[:space:]=]+[[:space:]=]+//')
        fi
        if [ -n "$_PREV" ]; then _EPP="./bnxdeps:$_PREV"; fi
        # BNX_DEPS_HDFS=<dir hdfs>: el tgz se sube UNA vez a HDFS (bnxdeps_<hash>.tgz) y YARN lo localiza
        # en cada contenedor: todos los nodos usan EXACTAMENTE el mismo archivo y no se sube en cada corrida.
        _ASRC="$BNX_DEPS_TGZ"
        if [ -n "${BNX_DEPS_HDFS:-}" ]; then
          _HD="${BNX_DEPS_HDFS%/}"
          _HF="$_HD/bnxdeps_${BNX_DEPS_HASH}.tgz"
          if ! command -v hdfs >/dev/null 2>&1; then
            echo "[run.sh] AVISO: BNX_DEPS_HDFS definido pero 'hdfs' no esta en el PATH; las librerias se envian desde el edge." >&2
          elif hdfs dfs -test -e "$_HF"; then
            echo "[run.sh] librerias de executors: $_HF (reutilizado, $BNX_DEPS_MB MB)"
            _ASRC="$_HF"
          elif hdfs dfs -mkdir -p "$_HD" && hdfs dfs -put -f "$BNX_DEPS_TGZ" "$_HF.part" && hdfs dfs -chmod 644 "$_HF.part" && hdfs dfs -mv "$_HF.part" "$_HF"; then
            echo "[run.sh] librerias de executors: $_HF (subido ahora, $BNX_DEPS_MB MB)"
            _ASRC="$_HF"
          else
            hdfs dfs -rm -f -skipTrash "$_HF.part" >/dev/null 2>&1 || true
            echo "[run.sh] AVISO: no se pudo subir las librerias a $_HD; se envian desde el edge." >&2
          fi
        fi
        if [ "$_ASRC" = "$BNX_DEPS_TGZ" ]; then
          echo "[run.sh] el codigo ejecuta Python en los WORKERS (UDF...): se envia el site-packages del venv desde el edge ($BNX_DEPS_MB MB, Python $BNX_DEPS_MINOR, sin pyspark/py4j) con el job; NO se instala nada en los nodos"
        else
          echo "[run.sh] el codigo ejecuta Python en los WORKERS (UDF...): los nodos toman las librerias de HDFS (Python $BNX_DEPS_MINOR, sin pyspark/py4j); NO se instala nada en los nodos"
        fi
        echo "[run.sh]   --archives $_ASRC#bnxdeps  spark.executorEnv.PYTHONPATH=$_EPP"
        DEPS_ARGS+=(--archives "$_ASRC#bnxdeps" --conf "spark.executorEnv.PYTHONPATH=$_EPP")
        _PK="${BNX_DEPS_HASH}_$(printf '%s' "${BNX_EXECUTOR_PYTHON:-}|${BNX_MASTER:-yarn}" | cksum | cut -d' ' -f1)"
        _PF=".bnx_tmp/probe_$_PK.json"
        _PR=0
        if [ -f "$_PF" ] && [ "${BNX_PROBE_FORZAR:-0}" != "1" ] && [ -z "$(find "$_PF" -mmin +"${BNX_PROBE_TTL_MIN:-720}" 2>/dev/null)" ]; then
          python bnx_sparkconf.py --probe-estado --out "$_PF" || _PR=$?
        else
          echo "[run.sh] PROBE de los executors (mini job en YARN: Python y librerias que ven los workers)..."
          rm -f "$_PF"
          "$CLUSTER_SUBMIT" --master "${BNX_MASTER:-yarn}" --deploy-mode client \
            --driver-java-options "$JOPTS" \
            --conf "spark.pyspark.driver.python=$PWD/.venv/bin/python" \
            ${CONF_ARGS[@]+"${CONF_ARGS[@]}"} \
            --conf spark.dynamicAllocation.initialExecutors=1 --conf spark.dynamicAllocation.minExecutors=1 \
            --conf spark.dynamicAllocation.maxExecutors=2 \
            ${DEPS_ARGS[@]+"${DEPS_ARGS[@]}"} \
            bnx_sparkconf.py --probe --mods="$BNX_DEPS_MODS" --out "$_PF" || _PR=$?
        fi
        if [ "$_PR" = "3" ] && [ "${BNX_UDF_NATIVAS:-auto}" != "0" ]; then
          # El Python de los executors no sirve: las UDF simples se cambian por expresiones nativas de
          # Spark (bank_compat, sin tocar el codigo del banco). Si TODO el Python en workers detectado
          # se puede cambiar, el job corre sin Python en los workers.
          export BNX_UDF_NATIVAS=1
          if python bnx_sparkconf.py --workers-nativos --out .bnx_workers_python.json; then
            echo "[run.sh] el Python de los executors no sirve, pero TODAS las UDF detectadas se cambian por expresiones nativas de Spark (BNX_UDF_NATIVAS=1): se sigue sin Python en los workers"
            _PR=0
          fi
        fi
        if [ "$_PR" = "3" ]; then
          if [ "${BNX_PROBE_IGNORAR:-0}" = "1" ]; then
            echo "[run.sh] AVISO: el probe dice que los executors no sirven; BNX_PROBE_IGNORAR=1: se sigue bajo tu riesgo." >&2
          else
            echo "[run.sh] No se lanza el job. (BNX_PROBE_FORZAR=1 repite el probe; BNX_DEPS_EXECUTORS=0 omite todo esto)" >&2
            exit 1
          fi
        elif [ "$_PR" != "0" ]; then
          echo "[run.sh] AVISO: no se pudo completar el probe de los executors (codigo $_PR); se sigue con las librerias enviadas." >&2
        fi
      fi
    elif [ "$_WS" = "11" ]; then
      :   # los executors usan su propio Python (arriba): nada que empaquetar
    else
      echo "[run.sh] sin Python en workers detectado (udf/rdd/pandas_udf): no se envian librerias a los executors"
    fi
  fi
  # Python de los EXECUTORS: se imprime el EXACTO y se aborta si fuera una ruta del venv del edge.
  _EXPY=""; _EXSRC=""; _EXBAD=""
  for _a in ${CONF_ARGS[@]+"${CONF_ARGS[@]}"} ${ARCH_ARGS[@]+"${ARCH_ARGS[@]}"} ${DEPS_ARGS[@]+"${DEPS_ARGS[@]}"}; do
    case "$_a" in
      spark.pyspark.python=*|spark.executorEnv.PYSPARK_PYTHON=*|spark.yarn.appMasterEnv.PYSPARK_PYTHON=*)
        _k="${_a%%=*}"; _v="${_a#*=}"
        if bnx_en_venv "$_v"; then _EXBAD="$_EXBAD $_k=$_v"; fi
        if [ "$_k" != "spark.yarn.appMasterEnv.PYSPARK_PYTHON" ]; then _EXPY="$_v"; _EXSRC="$_k"; fi ;;
    esac
  done
  if [ -z "$_EXPY" ] && [ -n "${PYSPARK_PYTHON:-}" ]; then _EXPY="$PYSPARK_PYTHON"; _EXSRC="PYSPARK_PYTHON (entorno)"; fi
  if [ -z "$_EXPY" ] && [ -n "${SPARK_CONF_DIR:-}" ]; then
    _v="$(grep -hE '^[[:space:]]*spark[.]pyspark[.]python[[:space:]=]' "$SPARK_CONF_DIR/spark-defaults.conf" 2>/dev/null | tail -1 | sed -E 's/^[^[:space:]=]+[[:space:]=]+//')"
    if [ -n "$_v" ]; then _EXPY="$_v"; _EXSRC="spark.pyspark.python de $SPARK_CONF_DIR/spark-defaults.conf"; fi
    if [ -n "$_v" ] && bnx_en_venv "$_v"; then _EXBAD="$_EXBAD spark-defaults.conf:spark.pyspark.python=$_v"; fi
  fi
  if [ -n "$_EXBAD" ]; then
    echo "[run.sh] ERROR: los EXECUTORS recibirian el Python del venv del edge, que NO existe en los nodos:$_EXBAD" >&2
    echo "[run.sh]   (en YARN fallaria con: Cannot run program \\"$PWD/.venv/bin/python\\": error=2). No se lanzo Spark." >&2
    echo "[run.sh]   Solucion: BNX_EXECUTOR_PYTHON=<python de los nodos> (ver probe_workers.py) y quitar PYSPARK_PYTHON/spark.pyspark.python que apunten al .venv." >&2
    exit 1
  fi
  if [ -n "$_EXPY" ]; then
    echo "[run.sh] python de los EXECUTORS (YARN): $_EXPY  [origen: $_EXSRC]"
  else
    echo "[run.sh] python de los EXECUTORS (YARN): el del cluster/nodo (sin PYSPARK_PYTHON ni spark.pyspark.python; NUNCA el del venv del edge)"
  fi
  exec "$CLUSTER_SUBMIT" --master "${BNX_MASTER:-yarn}" --deploy-mode client \
    --driver-java-options "$JOPTS" \
    --conf "spark.pyspark.driver.python=$PWD/.venv/bin/python" \
    ${CONF_ARGS[@]+"${CONF_ARGS[@]}"} \
    ${ARCH_ARGS[@]+"${ARCH_ARGS[@]}"} \
    ${DEPS_ARGS[@]+"${DEPS_ARGS[@]}"} \
    --conf spark.io.compression.codec="${BNX_IO_CODEC:-lz4}" \
    --conf spark.shuffle.mapStatus.compression.codec="${BNX_IO_CODEC:-lz4}" \
    main.py "$@"
fi
if ! python -c "import pyspark" >/dev/null 2>&1; then
  echo "[run.sh] Este entorno no tiene PySpark (paquete sin PySpark y sin internet al instalar). Usa el Spark del cluster:" >&2
  echo "         BNX_SPARK=cluster bash run.sh $*" >&2
  exit 1
fi
export PYSPARK_PYTHON="$PWD/.venv/bin/python"
export PYSPARK_DRIVER_PYTHON="$PWD/.venv/bin/python"
# Datos REALES en un solo nodo (local[*]): spark.driver.memory solo vale al LANZAR la JVM,
# por eso se pasa aqui con --driver-memory (BNX_DRIVER_MEMORY=16g para cambiarla).
if [ -f bnx_sparkconf.py ]; then
  python bnx_sparkconf.py --modo local --out .bnx_spark_conf.properties -- "$@" || true
  _M=$(sed -n 's/^spark.driver.memory=//p' .bnx_spark_conf.properties 2>/dev/null | head -1)
  if [ -n "$_M" ] && [ -z "${PYSPARK_SUBMIT_ARGS:-}" ]; then
    export PYSPARK_SUBMIT_ARGS="--driver-memory $_M pyspark-shell"
  fi
fi
exec python main.py "$@"
'''

_PROBE_WORKERS_PY = '''# -*- coding: utf-8 -*-
"""probe_workers.py - que Python ven los EXECUTORS de YARN (no instala nada, no toca datos).
Correr con el spark3-submit del cluster, SIN exportar PYSPARK_PYTHON (asi se ve el default del cluster):
  spark3-submit --master yarn --deploy-mode client probe_workers.py
y de nuevo forzando Python 3.11 en los nodos:
  spark3-submit --master yarn --deploy-mode client --conf spark.pyspark.python=/usr/bin/python3.11 probe_workers.py
Imprime el conjunto de (python, version mayor.menor, numpy importable, pandas importable) de ~8 particiones.
Compatible con Python 3.6+ (puede correr con el Python del cluster)."""
from __future__ import print_function
import sys
def _w(_):
    import sys as _s
    def _ok(m):
        try:
            __import__(m)
            return True
        except Exception:
            return False
    return (_s.executable, "%d.%d" % _s.version_info[:2], "numpy=%s" % _ok("numpy"), "pandas=%s" % _ok("pandas"))
def recomendacion(res, minor_driver=None):
    """Lineas con el BNX_EXECUTOR_PYTHON exacto a usar, segun lo que vieron los executors.
    res = [(python, 'M.m', 'numpy=True', 'pandas=True'), ...]"""
    buenos = []
    for r in res:
        if r[2] == "numpy=True" and r[3] == "pandas=True" and (minor_driver is None or r[1] == minor_driver):
            if r[0] not in buenos:
                buenos.append(r[0])
    if not buenos:
        return ["[probe_workers] Ningun Python de los executors tiene numpy y pandas con la version del driver"
                + ("" if minor_driver is None else " (%s)" % minor_driver) + ".",
                "[probe_workers] run.sh enviara las librerias del venv con el job (no se instala nada en los nodos);",
                "[probe_workers] o prueba otro Python con --conf spark.pyspark.python=<ruta> y vuelve a correr este probe."]
    out = ["[probe_workers] Los executors YA tienen Python con numpy y pandas. Usa EXACTAMENTE esta variable:",
           "[probe_workers]   BNX_EXECUTOR_PYTHON=%s" % buenos[0]]
    if len(buenos) > 1:
        out.append("[probe_workers]   (otras rutas validas en otros nodos: %s)" % ", ".join(buenos[1:]))
    out.append("[probe_workers] Ejemplo:  BNX_EXECUTOR_PYTHON=%s BNX_SPARK=cluster bash run.sh --settings <ruta>/bin/settings --env prod --source <job>" % buenos[0])
    return out
def main():
    from pyspark.sql import SparkSession
    spark = SparkSession.builder.appName("bnx_probe_workers").getOrCreate()
    sc = spark.sparkContext
    print("[probe_workers] DRIVER: %s (Python %d.%d) master=%s" % (sys.executable, sys.version_info[0], sys.version_info[1], sc.master))
    try:
        res = sorted(set(sc.parallelize(range(8), 8).map(_w).collect()))
    except Exception as e:
        print("[probe_workers] ERROR en los executors: %s" % str(e)[-1500:])
        print("[probe_workers] Si dice 'different version': el Python de los nodos NO es el del driver (ver NOTAS_EJECUCION.md).")
        spark.stop()
        return 1
    print("[probe_workers] EXECUTORS (python, version, numpy, pandas):")
    for r in res:
        print("[probe_workers]   %s" % (r,))
    for l in recomendacion(res, "%d.%d" % sys.version_info[:2]):
        print(l)
    spark.stop()
    return 0
if __name__ == "__main__":
    sys.exit(main())
'''
from src.spark_server_sh import SPARK_CFG_SH as _SPARK_CFG_SH
with open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "bnx_sparkconf.py"), encoding="utf-8") as _fh:
    _SPARKCONF_PY = _fh.read()   # viaja en la raiz del paquete (run.sh y main.py lo usan)
from src import bnx_sparkconf as _bsc
_SETUP_SH = _SETUP_SH.replace("@@SPARKCFG@@", _SPARK_CFG_SH)
_SETUP_SH = _SETUP_SH.replace("@@LIBOMP@@", _LIBOMP_SH)
_RUN_SH = _RUN_SH.replace("@@LIBOMP@@", _LIBOMP_SH)

# run.sh del paquete de monitoreo (sin main.py): corre sus pruebas.
_RUN_SH_METRICS = '''#!/usr/bin/env bash
# run.sh - corre las pruebas del monitoreo en el entorno montado por setup.sh.
set -e
cd "$(dirname "$0")"
if [ ! -f .venv/bin/activate ]; then
  echo "[ERROR] No existe .venv. Monta el entorno primero:  bash setup.sh" >&2
  exit 1
fi
. .venv/bin/activate
exec pytest -q "$@"
'''

def _readme(include_bank_libs):
    libs = ("Incluye marcadores para las librerias internas del banco "
            "(toolbox, lib_mkop_metrics, mex-lib*) en requirements.txt; "
            "descomentalas y apunta a tu Artifactory."
            if include_bank_libs else
            "Solo dependencias open source (sin librerias internas del banco).")
    # Nota sobre despliegue (si el paquete fue firmado, la carpeta deploy/ existe).
    deploy_hint = (
        "## 🔐 Despliegue\n"
        "Si firmaste el paquete, en `deploy/` están el `execution_manifest.json` "
        "(firmado) y la clave pública. Verifica integridad + firma antes de "
        "desplegar; si algún `.py` fue alterado, la verificación falla.")
    return f'''# Framework MLOps v2 (mejorado)
> 📌 **Antes de correr con datos reales lee `NOTAS_EJECUCION.md`**: como leer el `pivot.json` del banco (`--env/--cohort/--dry-run`) y como usar el metastore del cluster (`BNX_SPARK=cluster` o `SPARK_CONF_DIR`) si sale "la base no existe".


Paquete NUEVO generado por BNX a partir del analisis del framework actual.
**No contiene codigo propietario del banco**: es una reimplementacion limpia del
andamiaje que corrige los problemas detectados.

## Que mejora respecto al framework actual
- **Clase base `BaseAggregate`**: elimina la duplicacion (atms/s15/s15_nf eran
  casi identicos). Una fuente nueva = heredar y escribir solo `_aggregate_df`.
- **Validaciones de calidad ACTIVAS** (`core/quality.py`): el umbral de nulos
  falla el pipeline (en el original estaba comentado).
- **Router por registro** (`aggregates/router.py`): anadir fuente = una linea,
  sin herencia multiple.
- **Pruebas reales** con pytest + Spark (`tests/`), no `print('working!')`.
- **Sin errores silenciados**: excepciones explicitas y logging.

## Como correr (entorno virtual con todo lo necesario)
```bash
bash setup.sh      # una sola vez: crea .venv e instala dependencias
bash run.sh        # corre el modelo (main.py)
```
`setup.sh` monta el entorno; `run.sh` solo ejecuta el modelo. {libs}

## Estructura
```
framework_mlops_v2/
  core/base_aggregate.py   # contrato comun
  core/quality.py          # validaciones activas
  aggregates/              # atms, s15, pnl + router
  features/ratios.py       # ratios con proteccion /0
tests/                     # pruebas reales (pytest)
requirements.txt
setup.sh
run.sh
setup.py
```

## ▶️ Cómo CORRER el modelo (paso a paso)

### 🚀 Correr el framework (entry point: main.py)
```bash
bash run.sh            # corre main.py (demo) en el venv ya montado por setup.sh
# o si ya montaste el entorno:
. .venv/bin/activate && python main.py            # modo DEMO (datos sinteticos)
. .venv/bin/activate && python main.py --config cfg.json   # datos REALES
```
`main.py` es el **punto de entrada** del framework (encapsulado en el venv):
orquesta el pipeline, reporta las **optimizaciones de Spark** aplicadas, y por
defecto corre en modo DEMO (genera datos sinteticos, neutraliza las lecturas
externas y muestra entrada → salida por fuente). Con `--config cfg.json` usa tus
datos reales. No necesitas configurar nada para la demo. (Requiere Java para Spark.)

`cfg.json` para datos reales:
```json
{{"previous_path": "/ruta/con/parquets",
 "sources": {{"bureau": {{"table_name": "bureau"}}}}}}
```

### Requisitos previos
- **Python 3.8+** instalado (el `setup.sh`/`run.sh` crea el venv con tu Python).
- **Java (JDK 8/11/17)** con `java` en el PATH — PySpark lo necesita para ejecutar
  Spark. Verifícalo con `java -version`. (No se empaqueta; debe estar en la máquina.)

### 1) Montar el entorno (una sola vez)
```bash
bash setup.sh        # con PySpark en vendor/: TODO OFFLINE. Sin PySpark en vendor/: el resto
                     # offline y PySpark por internet (3.5.6 / 4.0.0 segun tu Python), o usa
                     # BNX_SPARK=cluster para el Spark del cluster (no instala PySpark)
bash setup.sh --test # (opcional) ademas corre pytest
```
Esto crea `.venv`, instala dependencias e instala el propio framework
(`pip install -e .`). Al terminar dice "Entorno listo"; despues corre el modelo con `bash run.sh`.

### 2) Activar el entorno
```bash
source .venv/bin/activate      # Linux/macOS
# .venv\\Scripts\\activate     # Windows
```

### 3) Correr una agregación (un paso del pipeline)
Cada fuente registrada se corre por su nombre con el router `GroupBy`:
```python
from pyspark.sql import SparkSession
from framework_mlops_v2.aggregates.router import GroupBy, REGISTRY

spark = SparkSession.builder.appName("mlops_v2").getOrCreate()

print("Fuentes disponibles:", sorted(REGISTRY))   # p.ej. ['bureau', ...]

# previous_path: carpeta con el parquet de entrada (<previous_path>/<table_name>)
# agg_dict: parametros de la fuente (al menos {{"table_name": "..."}}).
GroupBy("bureau",
        previous_path="/ruta/a/datos",
        agg_dict={{"table_name": "bureau"}},
        sqlContext=spark).aggregate()
# Escribe el resultado en la carpeta hermana 'groupby/'.
```

### 4) Correr el PIPELINE completo (si generaste con "pasos extra")
Si el paquete incluye `pipeline.py` (feature engineering + vector + scoring):
```python
from framework_mlops_v2.pipeline import run
run(previous_path="/ruta/a/datos",
    agg_dict_by_source={{"bureau": {{"table_name": "bureau"}}}},
    sqlContext=spark,
    feature_cols=["saldo", "atraso_max"],   # columnas que entran al modelo
    model_path="/ruta/al/modelo.xgb")        # XGBoost entrenado (opcional)
```

### 5) Correr en un cluster (Spark real)
```bash
spark-submit --master yarn tu_job.py
# o local para probar:
spark-submit --master "local[*]" tu_job.py
```

### Revisa antes de correr
- Busca los comentarios `# TODO py2spark` en los aggregates: son las líneas que
  requieren ajuste manual (p.ej. el modelo XGBoost). Edítalas antes de producción.
- {libs}

{deploy_hint}

Generado: {datetime.now().isoformat(timespec="seconds")}
'''


# main.py: ENTRY POINT del framework, encapsulado en el venv. Orquesta el
# pipeline completo (fuentes del router), REPORTA las optimizaciones de Spark
# aplicadas, y corre por defecto en modo DEMO (datos sinteticos, sin configurar
# nada). Con --config <archivo> usa rutas/datos reales. Es la unica forma de
# correr el paquete:  python main.py  [--config cfg.json] [--source NOMBRE]
_MAIN_PY = '''#!/usr/bin/env python3
"""main.py — Punto de entrada del Framework MLOps v2 (encapsulado en el venv).

Orquesta el pipeline y reporta las optimizaciones de Spark aplicadas.

Uso (tras montar el entorno con setup.sh; o directo:  bash run.sh):
    . .venv/bin/activate
    python main.py                 # modo DEMO: datos sinteticos, sin configurar
    python main.py --source bureau # solo una fuente
    python main.py --config cfg.json   # datos REALES (ver formato abajo)

cfg.json (datos reales) — ver cfg.example.json:
    {
      "previous_path": "data/datapull",        # opcional; destino/origen de parquets
      "spark": {"master": "yarn", "hive": true, "conf": {"spark.executor.memory": "4g"}},
      "sources": {
        "bureau": {"table_name": "bureau",
                   "query": "SELECT * FROM db.bureau WHERE fecha >= '2024-01-01'"},
        "atms":   {"table_name": "atms", "source_table": "db.atms", "limit": 100000}
      }
    }
Si una fuente trae "query" (o "query_file", o "source_table"), main.py se conecta
a la sesion de Spark/Hive, ejecuta el query y BAJA el resultado a parquet en
<previous_path>/<table_name>; luego corre los aggregates sobre esos parquets.
Sin query, usa el parquet que ya exista en esa ruta. --skip-extract reutiliza
los parquets ya bajados; --extract-only solo baja los datos.

SETTINGS DEL BANCO (bin/settings/<modelo>/pivot.json, datapull.json) se leen TAL CUAL:
    python main.py --config pivot.json --env uat --cohort 202501 [--root <general_root>]
Cada tabla de 'tables_info' ({database, table, columns, where}) se convierte en
 select <columns> from <database>.<table> where <where>   (los '{}' del where se
llenan con las fechas del cohort/lag, igual que el job original) y se baja a
parquet en <general_root>/<working_path>/<tabla>. --env: prod|uat|sbx;
general_root sale de settings/jobs.json (junto al config) o de --root.

Cada fuente es un JOB: si una falla, las demas siguen. Todas comparten la misma
SparkSession. El proceso PIVOTE corre SIEMPRE primero; se marca con "pivot": true
en el cfg.json, o nombrando la fuente 'pivote'/'pivot'.
ORDEN POR DEPENDENCIAS (opcional): "depends_on": ["a", "b"] en la fuente del
cfg.json, o en orden.json (lo genera la pantalla 'Orden de las fuentes'; --orden
para otra ruta). Una fuente con depends_on corre despues de esas y SE SALTA si
alguna fallo. Sin depends_on el orden es el de siempre. Para lanzar una sola como job
aislado (p.ej. una tarea por fuente en Airflow/cron):
    python main.py --config cfg.json --source <nombre>
En DEMO genera datos sinteticos, neutraliza las lecturas externas de los
aggregates (spark.read.* -> datos de juguete) y corre cada fuente mostrando
entrada -> salida. Las fuentes con un '# TODO py2spark' pendiente se marcan.
"""
import argparse
import glob
import json
import os
import sys
import shutil
import tempfile
import time

# Modulos de PYTHONPATH del banco (toolbox, bnmxverse, utils): si el paquete se
# monto con ambiente completo, setup.sh/run.sh los dejan en ./bank_pkg. Los
# agregamos al path aqui para que 'import toolbox' funcione sin exportar nada.
_here = os.path.dirname(os.path.abspath(__file__))
# bank_src/: modulos de APOYO subidos al portal (utils, settings, ...) copiados
# exactos. Va AL FINAL del path: un 'email.py' del banco no debe tapar al stdlib.
_bank_src = os.path.join(_here, "bank_src")
if os.path.isdir(_bank_src) and _bank_src not in sys.path:
    # Solo PAQUETES (toolbox/, jobs/, bnmxverse/...): van primero, asi manda el codigo
    # que subiste y no una copia vieja del cache. Con modulos sueltos va al final.
    if any(f.endswith(".py") and f != "main.py" for f in os.listdir(_bank_src)):
        sys.path.append(_bank_src)
    else:
        sys.path.insert(0, _bank_src)
for _cand in (os.path.join(_here, "bank_pkg"),
              os.path.join(_here, "vendor", "bank", "pkgcode")):
    if os.path.isdir(_cand) and _cand not in sys.path:
        sys.path.insert(0, _cand)

try:
    import bank_compat as _bc   # diagnostico/parches de las librerias del banco + mensajes de "que falta"
except Exception:
    _bc = None
try:
    import bank_diag as _bd     # log de diagnostico en cada escritura de los jobs del banco (BNX_DIAG_ESCRITURA)
except Exception:
    _bd = None
try:
    from pyspark.sql import SparkSession
    from pyspark.sql.types import (StructType, StructField, StringType,
                                    DoubleType, IntegerType)
except Exception as e:
    raise SystemExit("PySpark no esta instalado o falta Java. Monta el entorno "
                     "con 'bash setup.sh' primero. Detalle: %s" % e)

from framework_mlops_v2.aggregates.router import REGISTRY, GroupBy
from framework_mlops_v2.aggregates import router as _router
import bnx_sparkconf as _bs   # conf de Spark, demo/real, tabla de tiempos (raiz del paquete)

# Tiempos por fuente/job para la tabla final (etapa, nombre, seg, particiones, archivos, filas, estado).
_TIEMPOS = []

# Jobs del banco (def run(kernel)) y alias de los nombres viejos (job, job_2...) -> nombre por ruta.
KERNEL = getattr(_router, "KERNEL", {})
ALIAS = getattr(_router, "ALIAS", {})


def _synthetic_df(spark, n=20):
    import random
    random.seed(7)
    schema = StructType([
        StructField("cliente_id", IntegerType(), True),
        StructField("monto", DoubleType(), True),
        StructField("saldo", DoubleType(), True),
        StructField("atraso_max", IntegerType(), True),
        StructField("pais", StringType(), True),
    ])
    rows = [(i + 1, round(random.uniform(0, 5000), 2),
             round(random.uniform(0, 20000), 2), random.randint(0, 5),
             random.choice(["MX", "US", "CA"])) for i in range(n)]
    return spark.createDataFrame(rows, schema)


def _patch_reads(spark, synth):
    """spark.read.<fmt>(...) -> df sintetico (solo en modo DEMO)."""
    class _Reader:
        def option(self, *a, **k): return self
        def options(self, *a, **k): return self
        def schema(self, *a, **k): return self
        def format(self, *a, **k): return self
        def load(self, *a, **k): return synth
        def csv(self, *a, **k): return synth
        def parquet(self, *a, **k): return synth
        def json(self, *a, **k): return synth
        def table(self, *a, **k): return synth
    try:
        type(spark).read = property(lambda self: _Reader())
    except Exception:
        pass


def _load_config(path):
    """Lee el JSON de configuracion con mensajes claros (sin KeyError)."""
    try:
        with open(path, encoding="utf-8") as fh:
            cfg = json.load(fh)
    except (OSError, ValueError) as e:
        raise SystemExit("No se pudo leer el config '%s': %s" % (path, e))
    if not isinstance(cfg, dict):
        raise SystemExit("El config '%s' debe ser un objeto JSON {...}" % path)
    return cfg
def _source_query(s, scfg, cfg_dir):
    """SQL a ejecutar para bajar la fuente, o None si no hay que extraer."""
    q = scfg.get("query")
    if not q and scfg.get("query_file"):
        qf = scfg["query_file"]
        if not os.path.isabs(qf):
            qf = os.path.join(cfg_dir, qf)
        with open(qf, encoding="utf-8") as fh:
            q = fh.read()
    if not q and scfg.get("source_table"):
        q = "SELECT * FROM %s" % scfg["source_table"]
    if not q:
        return None
    q = q.strip().rstrip(";")
    if scfg.get("limit"):
        q = "SELECT * FROM (%s) bnx_q LIMIT %d" % (q, int(scfg["limit"]))
    return q
def _preflight(spark, chk):
    """Antes de ejecutar: verifica que <db>.<table> exista y que las columnas
    simples del 'columns' del JSON existan en la tabla. Devuelve un mensaje claro
    (tabla inexistente vs columna inexistente) o None si todo cuadra."""
    import re
    full = "%s.%s" % (chk["db"], chk["table"])
    try:
        existe = spark.catalog.tableExists(full)
    except Exception:
        existe = True   # no se puede comprobar; que lo diga el query
    if not existe:
        try:
            dbs = [d.name for d in spark.catalog.listDatabases()]
        except Exception:
            dbs = []
        if dbs and set(dbs) <= {"default"}:
            hint = (" (este Spark solo ve la base 'default': NO esta conectado al metastore "
                    "del cluster; ver el AVISO [metastore] de arriba / SPARK_CONF_DIR)")
        elif dbs and chk["db"] not in dbs:
            hint = " (la base '%s' NO existe en este metastore; revisa --env)" % chk["db"]
        else:
            hint = ""
        return "la TABLA %s no existe%s" % (full, hint)
    try:
        reales = {c.lower() for c in spark.table(full).columns}
    except Exception:
        return None
    faltan = []
    for c in chk["columns"]:
        c0 = c.strip()
        if re.match(r"^[A-Za-z_][A-Za-z0-9_]*$", c0) and c0.lower() not in reales:
            faltan.append(c0)
    if faltan:
        return ("la tabla %s existe pero le faltan estas COLUMNAS: %s. Columnas reales: %s"
                % (full, ", ".join(faltan), ", ".join(sorted(reales))))
    return None
def _fs_path(spark, p):
    """(FileSystem, Path) de Hadoop para la ruta: sin esquema usa fs.defaultFS
    (HDFS en el cluster; disco local en modo local)."""
    jvm = spark._jvm
    path = jvm.org.apache.hadoop.fs.Path(p)
    return path.getFileSystem(spark._jsc.hadoopConfiguration()), path
def _fs_mkdirs(spark, p):
    try:
        fs, path = _fs_path(spark, p)
        if fs.mkdirs(path) or fs.exists(path):
            return True
        print("[aviso] no se pudo crear la carpeta de salida %s (permisos?)" % _fs_uri(spark, p))
        return False
    except Exception as e:
        print("[aviso] no se pudo crear %s: %s" % (p, _err_text(e)))
        return False
def _fs_delete(spark, p):
    try:
        fs, path = _fs_path(spark, p)
        fs.delete(path, True)
    except Exception:
        pass
def _fs_parquet_files(spark, p):
    """Numero de archivos .parquet en la carpeta (HDFS o local); 0 si no existe."""
    try:
        fs, path = _fs_path(spark, p)
        if not fs.exists(path):
            return 0
        return sum(1 for st in fs.listStatus(path) if st.getPath().getName().endswith(".parquet"))
    except Exception:
        return 0
def _fs_uri(spark, p):
    """Ruta completamente calificada (hdfs://... o file:/...) para los mensajes."""
    try:
        fs, path = _fs_path(spark, p)
        return str(fs.makeQualified(path).toString())
    except Exception:
        return p
def _err_text(e, n=700):
    """Causa REAL de un error de Spark/Java (no solo 'An error occurred while
    calling o39.parquet'): recorre la cadena de causas de la excepcion Java."""
    try:
        je = getattr(e, "java_exception", None)
        if je is not None:
            partes, c, vistos = [], je, 0
            while c is not None and vistos < 6:
                t = str(c.toString())
                if t not in partes:
                    partes.append(t)
                c = c.getCause()
                vistos += 1
            # La causa RAIZ (la ultima) es la que dice ruta/permiso: va primero.
            raiz = partes[-1]
            if len(partes) > 1:
                return ("causa raiz: %s  (origen: %s)" % (raiz, partes[0][:160]))[:n]
            return raiz[:n]
    except Exception:
        pass
    msg = str(e).strip()
    return " ".join(msg.split("\\n")[0].split())[:n] if msg else type(e).__name__
def _log_conf_efectiva(spark, cluster, real):
    """Imprime la conf con la que quedo la sesion (para ver que recursos se estan usando)."""
    sc = spark.sparkContext
    try:
        conf = dict(sc.getConf().getAll())
        conf["spark.sql.shuffle.partitions"] = spark.conf.get("spark.sql.shuffle.partitions")
    except Exception:
        conf = {}
    for l in _bs.resumen_conf(conf):
        print("[spark]   " + l)
    print("[spark]   paralelismo por defecto=%s" % sc.defaultParallelism)
    if cluster:
        _avisar_python_workers()
    elif real and str(sc.master).startswith("local") and "spark.driver.memory" not in conf:
        print("[spark] AVISO: en local la memoria del driver solo vale al lanzar. Usa 'bash run.sh' "
              "(la pasa con --driver-memory) o export PYSPARK_SUBMIT_ARGS='--driver-memory 16g pyspark-shell'.")
def _avisar_python_workers():
    """En YARN los executors son JVM sin Python SALVO que el codigo use udf/rdd/pandas_udf...
    Avisa de los archivos del paquete que lo hacen (analisis estatico)."""
    hallados = {}
    for base in ("bank_src", os.path.join("framework_mlops_v2", "aggregates")):
        for fp in glob.glob(os.path.join(_here, base, "**", "*.py"), recursive=True):
            try:
                with open(fp, encoding="utf-8") as fh:
                    hs = _bs.detectar_python_en_workers(fh.read())
            except (OSError, UnicodeDecodeError):
                continue
            if hs:
                hallados[os.path.relpath(fp, _here)] = hs
    if hallados:
        print("[spark] AVISO: %d archivo(s) ejecutan Python en los WORKERS (udf/rdd/pandas_udf...):" % len(hallados))
        for fp, hs in sorted(hallados.items()):
            print("          %s: %s" % (fp, ", ".join(sorted(set("%s (l.%d)" % (h["patron"], h["linea"]) for h in hs)))[:200]))
        print("          " + _bs.AVISO_WORKERS)
def _imprimir_tiempos(spark=None):
    if not _TIEMPOS:
        return
    master = app = None
    try:
        sc = (spark or SparkSession.getActiveSession()).sparkContext
        master, app = sc.master, sc.applicationId
    except Exception:
        pass
    print("\\n" + _bs.tabla_tiempos(_TIEMPOS, master, app, _mon_linea()))
    del _TIEMPOS[:]
def _extract_sources(spark, fuentes, src_cfg, prev, cfg_dir, dry_run=False):
    """Ejecuta el query de cada fuente en la sesion de Spark y lo baja a parquet
    en <prev>/<table_name>. Devuelve las fuentes que fallaron al extraer.
    Imprime el QUERY real y verifica que el parquet quedo escrito (si no, falla)."""
    fallidas = []
    for s in fuentes:
        scfg = src_cfg.get(s) or {}
        q = _source_query(s, scfg, cfg_dir)
        dest = os.path.join(prev, scfg.get("table_name", s))
        if q is None:
            # Sin query NO se escribe parquet: antes se saltaba en silencio y
            # '--extract-only' lo contaba como OK aunque no bajara nada.
            if _fs_parquet_files(spark, dest):
                print("[extract] %s: sin query; se usa el parquet existente en %s" % (s, dest))
            else:
                print("[extract] %s: SIN query/query_file/source_table y NO hay parquet "
                      "en %s -> nada que extraer." % (s, dest))
                fallidas.append(s)
            continue
        print("[extract] %s -> %s" % (s, dest))
        print("          QUERY: %s" % " ".join(q.split()))
        if dry_run:
            continue
        chk = scfg.get("_check")
        if chk and os.environ.get("BNX_PREFLIGHT", "1") != "0":
            # Chequeo rapido: SOLO catalogo (existe la tabla / columnas), no lee datos.
            # Se desactiva con BNX_PREFLIGHT=0.
            _tp = time.time()
            problema = _preflight(spark, chk)
            _TIEMPOS.append({"etapa": "preflight", "nombre": s, "seg": time.time() - _tp,
                             "estado": "OK" if not problema else "AVISO"})
            if problema:
                # Solo AVISO: con permisos restringidos (Ranger/Sentry) el catalogo
                # puede no listar la base aunque el SELECT si funcione. Se intenta igual.
                print("          [aviso preflight] %s -> se intenta el query de todos modos" % problema)
        else:
            problema = None
        _t0 = time.time()
        _parts = escritos = filas = None
        try:
            df = spark.sql(q)
            try:   # particiones del plan (no ejecuta nada; None si no se puede saber)
                _parts = int(df._jdf.queryExecution().toRdd().getNumPartitions())
            except Exception:
                _parts = None
            df.write.mode("overwrite").parquet(dest)
            _seg = time.time() - _t0
            # Verificar que se escribio: LISTA los .parquet (no relee los datos).
            escritos = _fs_parquet_files(spark, dest)
            if not escritos:
                raise RuntimeError("el write no dejo archivos .parquet en %s" % _fs_uri(spark, dest))
            # Contar filas = una pasada extra por todo lo escrito: solo con BNX_CONTAR_FILAS=1.
            if os.environ.get("BNX_CONTAR_FILAS") == "1":
                filas = spark.read.parquet(dest).count()
            _sc = spark.sparkContext
            print("          OK: query+write %.1f s | %s particion(es) del query | %d archivo(s) parquet%s en %s"
                  % (_seg, "?" if _parts is None else _parts, escritos,
                     "" if filas is None else " | %d filas" % filas, _fs_uri(spark, dest)))
            print("          master=%s applicationId=%s" % (_sc.master, _sc.applicationId))
            _TIEMPOS.append({"etapa": "extract", "nombre": s, "seg": _seg, "particiones": _parts,
                             "archivos": escritos, "filas": filas, "estado": "OK"})
        except Exception as e:
            print("          ERROR extrayendo '%s': %s" % (s, _err_text(e)))
            _TIEMPOS.append({"etapa": "extract", "nombre": s, "seg": time.time() - _t0,
                             "particiones": _parts, "estado": "ERROR"})
            if problema:
                print("          (pista: %s)" % problema)
            fallidas.append(s)
    return fallidas
def _orden_pivote_primero(fuentes, src_cfg):
    """Ordena las fuentes dejando el PIVOTE de primero (el resto conserva su orden).
    El pivote es el proceso del que dependen los demas, por eso corre antes.
    Se detecta por:
      1) una fuente marcada  "pivot": true  en su config, o
      2) su nombre normalizado es 'pivote' o 'pivot'.
    Si no hay pivote, se respeta el orden original."""
    def _es_pivote(s):
        scfg = src_cfg.get(s) or {}
        if isinstance(scfg, dict) and scfg.get("pivot"):
            return True
        norm = str(s).strip().lower().replace("-", "_")
        return norm in ("pivote", "pivot") or norm.endswith("_pivote") or norm.endswith("_pivot")
    pivotes = [s for s in fuentes if _es_pivote(s)]
    resto = [s for s in fuentes if s not in pivotes]
    if pivotes:
        print("[orden] pivote primero:", ", ".join(pivotes))
    return pivotes + resto


def _resolver_source(nombre, src_cfg, bank_fmt, registry=None):
    """Valida --source contra las tablas del config y los jobs del REGISTRY.
    Acepta 'job_3', 'job_3.py', 'JOB_3' o una ruta (se usa el nombre base).
    Imprime que se va a hacer y devuelve el nombre canonico; si no existe, se
    detiene con la lista de opciones (antes se ignoraba en silencio)."""
    registry = REGISTRY if registry is None else registry
    crudo = str(nombre).strip()
    norm = os.path.splitext(os.path.basename(crudo.rstrip("/")))[0].strip().lower()
    tablas = {str(k).lower(): k for k in (src_cfg or {})}
    jobs = {str(k).lower(): k for k in (registry or {})}
    if norm in tablas and (bank_fmt or tablas[norm] in (registry or {})):
        canon = tablas[norm]
        if bank_fmt and canon not in (registry or {}):
            print("[source] '%s' = TABLA de tables_info: solo se baja esa tabla "
                  "(no tiene aggregate)." % canon)
        else:
            print("[source] '%s': se corre solo esa fuente." % canon)
        return canon
    if norm in jobs:
        canon = jobs[norm]
        if bank_fmt:
            print("[source] '%s' = JOB del REGISTRY: se bajan las %d tabla(s) del config "
                  "y despues corre su aggregate (si alguna tabla falla, el job no corre)."
                  % (canon, len(src_cfg or {})))
        else:
            print("[source] '%s': se corre solo esa fuente." % canon)
        return canon
    raise SystemExit(
        "[source] ERROR: '%s' no es una tabla del config ni un job del REGISTRY.\\n"
        "  Tablas del config: %s\\n"
        "  Jobs del REGISTRY: %s\\n"
        "  Jobs del banco (run(kernel)): %s\\n"
        "  Usa el NOMBRE DEL JOB del banco (p.ej. rps_datapull), no el nombre de un archivo (main.py, job.py)."
        % (crudo, ", ".join(map(str, src_cfg or {})) or "(ninguna)",
           ", ".join(map(str, registry or {})) or "(ninguno)",
           ", ".join(map(str, globals().get("KERNEL") or {})) or "(ninguno)"))


def _validar_source_antes_de_spark(args):
    """--source que no es job del banco: se valida ANTES de crear la SparkSession (en YARN cada sesion
    pide executors; un nombre mal escrito no debe lanzar un job de 50 executors para fallar al final)."""
    tablas = []
    if args.config:
        cfg = _load_config(args.config)
        if _is_bank_settings(cfg):
            return          # las tablas salen de tables_info del ambiente: se valida mas adelante
        tablas = list((cfg.get("sources") or {}).keys())
    norm = os.path.splitext(os.path.basename(str(args.source).strip().rstrip("/")))[0].strip().lower()
    if norm in set(str(k).lower() for k in tablas) | set(str(k).lower() for k in REGISTRY):
        return
    _resolver_source(args.source, dict((t, {}) for t in tablas), False)    # imprime las opciones y se detiene


def _tmp_spark_base(spark, args, work):
    """Carpeta de temporales de Spark (el DEMO escribe parquet ahi) -> (ruta, remota, de_donde).
    Disco local (defaultFS file:/ o master local): carpeta de trabajo local (main.py le pone file:// si el
    defaultFS es HDFS). En el CLUSTER (HDFS) NUNCA
    la carpeta del paquete del edge (un /data/1/... sin permiso): BNX_HDFS_TMP > --base-path >
    BNX_BASE_PATH > el HOME del usuario en HDFS (/user/<usuario>)."""
    fs_def = _default_fs(spark)
    master = str(spark.sparkContext.master)
    if fs_def.startswith("file:") or master.startswith("local"):
        return os.path.abspath(work), False, "disco local"
    for v, o in ((os.environ.get("BNX_HDFS_TMP"), "BNX_HDFS_TMP"),
                 (getattr(args, "base_path", None), "--base-path"),
                 (os.environ.get("BNX_BASE_PATH"), "BNX_BASE_PATH")):
        if v and str(v).strip():
            suf = "" if o == "BNX_HDFS_TMP" else "/.bnx_tmp"
            return str(v).strip().rstrip("/") + suf, True, o
    try:
        fs, _p = _fs_path(spark, "/")
        home = str(fs.getHomeDirectory().toString())
    except Exception:
        home = "/user/%s" % (os.environ.get("USER") or os.environ.get("LOGNAME") or "usuario")
    return home.rstrip("/") + "/.bnx_tmp", True, "HOME del usuario en HDFS"


def _cargar_orden(path=None):
    """Lee orden.json (opcional, lo genera la pantalla 'Orden de las fuentes').
    Formato: {"sources": {"<fuente>": {"pivot": true, "depends_on": ["a", "b"]}}}
    Busca en: path explicito > BNX_ORDEN > orden.json junto a main.py.
    Si no existe devuelve {} y el orden queda como siempre (pivote primero)."""
    cand = path or os.environ.get("BNX_ORDEN") or os.path.join(_here, "orden.json")
    if not cand or not os.path.isfile(cand):
        if path:
            raise SystemExit("[orden] no existe el archivo de orden: %s" % path)
        return {}
    with open(cand, "r", encoding="utf-8") as fh:
        data = json.load(fh)
    src = data.get("sources") if isinstance(data, dict) else None
    if not isinstance(src, dict):
        raise SystemExit("[orden] %s no tiene la clave 'sources' (objeto)" % cand)
    print("[orden] usando", cand)
    return src


def _orden_dependencias(fuentes, src_cfg, orden=None, modelos=None):
    """Orden de ejecucion por DEPENDENCIAS. Devuelve (fuentes_ordenadas, deps_explicitas).

    - depends_on de cada fuente: el del cfg.json si lo trae; si no, el de orden.json.
    - pivote (cfg "pivot": true, orden.json "pivot": true o nombre pivote/pivot):
      las fuentes SIN depends_on explicito van despues de los pivotes (como siempre).
      Esa dependencia implicita solo ORDENA: si el pivote falla, las demas siguen
      (comportamiento historico).
    - modelos = {job: (modelo, tipo)} (jobs del banco): el datapull de un modelo corre antes que
      sus otros jobs no pivote (target/score/... leen lo que escribe el datapull). Solo ordena.
    - Solo las dependencias EXPLICITAS hacen que una fuente se salte si su
      dependencia fallo.
    - Sin depends_on en ningun lado el resultado es identico a _orden_pivote_primero.
    - Un ciclo detiene la ejecucion con un error (es un error de configuracion)."""
    orden = orden or {}
    presentes = set(fuentes)
    idx = {s: i for i, s in enumerate(fuentes)}

    def _cfg_de(s):
        c = src_cfg.get(s) or {}
        return c if isinstance(c, dict) else {}

    def _es_pivote(s):
        if _cfg_de(s).get("pivot") or (orden.get(s) or {}).get("pivot"):
            return True
        norm = str(s).strip().lower().replace("-", "_")
        return norm in ("pivote", "pivot") or norm.endswith("_pivote") or norm.endswith("_pivot")

    pivotes = [s for s in fuentes if _es_pivote(s)]
    explicitas = {}
    for s in fuentes:
        if "depends_on" in _cfg_de(s):
            deps = _cfg_de(s).get("depends_on")
        elif "depends_on" in (orden.get(s) or {}):
            deps = (orden.get(s) or {}).get("depends_on")
        else:
            continue
        if not isinstance(deps, list):
            raise SystemExit("[orden] depends_on de '%s' debe ser una lista" % s)
        validas = []
        for d in deps:
            if d == s:
                raise SystemExit("[orden] '%s' no puede depender de si misma" % s)
            if d in presentes:
                validas.append(d)
            else:
                print("[orden] aviso: '%s' depende de '%s', que no esta en esta corrida; se ignora" % (s, d))
        explicitas[s] = validas
    deps_todas = {}
    for s in fuentes:
        if s in explicitas:
            deps_todas[s] = list(explicitas[s])
        elif s in pivotes:
            deps_todas[s] = []
        else:
            deps_todas[s] = list(pivotes)   # implicita: solo ordena
            mt = (modelos or {}).get(s) or (None, None)
            if mt[0] and str(mt[1]).lower() != "datapull":
                for d in fuentes:
                    md = (modelos or {}).get(d) or (None, None)
                    if (d != s and d not in pivotes and md[0] == mt[0] and str(md[1]).lower() == "datapull"
                            and s not in explicitas.get(d, [])):
                        deps_todas[s].append(d)
    # Kahn estable: entre las listas para correr, primero pivotes y luego orden original
    pendientes = {s: len(set(deps_todas[s])) for s in fuentes}
    hijos = {s: [] for s in fuentes}
    for s in fuentes:
        for d in set(deps_todas[s]):
            hijos[d].append(s)
    clave = lambda s: (0 if s in pivotes else 1, idx[s])
    listas = sorted([s for s in fuentes if pendientes[s] == 0], key=clave)
    salida = []
    while listas:
        s = listas.pop(0)
        salida.append(s)
        for h in hijos[s]:
            pendientes[h] -= 1
            if pendientes[h] == 0:
                listas.append(h)
        listas.sort(key=clave)
    if len(salida) != len(fuentes):
        ciclo = sorted(set(fuentes) - set(salida), key=lambda s: idx[s])
        raise SystemExit("[orden] ciclo de dependencias entre: %s" % ", ".join(ciclo))
    if explicitas:
        print("[orden] por dependencias:", " -> ".join(salida))
    elif pivotes:
        print("[orden] pivote primero:", ", ".join(pivotes))
    return salida, explicitas


def _report_optimizations():
    """Resumen de las optimizaciones de Spark ya aplicadas al generar el paquete
    (cache / broadcast / coalesce). BNX las aplico en el portal; aqui las
    detectamos en el codigo de los aggregates para dejar constancia."""
    import glob
    counts = {"cache": 0, "broadcast": 0, "coalesce": 0}
    here = os.path.dirname(os.path.abspath(__file__))
    for fp in glob.glob(os.path.join(here, "framework_mlops_v2", "**", "*.py"), recursive=True):
        try:
            txt = open(fp, encoding="utf-8").read()
        except OSError:
            continue
        counts["cache"] += txt.count(".cache(")
        counts["broadcast"] += txt.count("broadcast(")
        counts["coalesce"] += txt.count(".coalesce(")
    total = sum(counts.values())
    if total:
        print("OPTIMIZACIONES Spark aplicadas: %d cache, %d broadcast, %d coalesce"
              % (counts["cache"], counts["broadcast"], counts["coalesce"]))
    else:
        print("OPTIMIZACIONES Spark: ninguna (el codigo generado no la amerita; "
              "cache/broadcast/coalesce aplican con joins/reuso/escrituras).")


def _work_dir():
    """Directorio de trabajo ESCRIBIBLE dentro del paquete. No depende de /tmp, que
    en servidores endurecidos suele estar montado 'noexec' o con cuota (rompe las
    librerias nativas de compresion de parquet/snappy y la escritura de temporales)."""
    here = os.path.dirname(os.path.abspath(__file__))
    for cand in (os.path.join(here, ".bnx_tmp"), tempfile.gettempdir()):
        try:
            os.makedirs(cand, exist_ok=True)
            probe = os.path.join(cand, ".w")
            open(probe, "w").close()
            os.remove(probe)
            return cand
        except OSError:
            continue
    return tempfile.gettempdir()


def _ensure_parquet_codec(spark, out_dir):
    """Comprueba que se pueda ESCRIBIR parquet con el codec por defecto (snappy) EN
    LA RUTA DE SALIDA real (en el cluster es HDFS, no el disco del servidor). Si
    falla, prueba 'uncompressed'; si tambien falla, NO aborta: avisa con la causa
    real (permisos/ruta) y deja que la extraccion reporte el error por tabla.
    Se puede forzar con BNX_PARQUET_CODEC (snappy|gzip|uncompressed|zstd)."""
    forced = os.environ.get("BNX_PARQUET_CODEC")
    if forced:
        spark.conf.set("spark.sql.parquet.compression.codec", forced)
        print("[codec] parquet forzado a '%s' (BNX_PARQUET_CODEC)" % forced)
        return
    probe = out_dir.rstrip("/") + "/_bnx_codec_probe"
    try:
        spark.range(1).write.mode("overwrite").parquet(probe)
    except Exception as e:
        causa = _err_text(e, 400)
        if "ermission" in causa or "AccessControl" in causa:
            print("[aviso] SIN PERMISO de escritura en %s: %s" % (_fs_uri(spark, out_dir), causa))
            print("        Revisa base_path/--base-path (debe ser una ruta HDFS donde puedas escribir).")
            print("        Para los temporales del DEMO: BNX_HDFS_TMP=/user/<usuario>/bnx_tmp (o --base-path <ruta HDFS>).")
            return
        print("[aviso] no se pudo escribir parquet con el codec por defecto: %s" % causa)
        print("        Se prueba 'uncompressed'.")
        spark.conf.set("spark.sql.parquet.compression.codec", "uncompressed")
        try:
            spark.range(1).write.mode("overwrite").parquet(probe)
        except Exception as e2:
            print("[aviso] tampoco con 'uncompressed' en %s: %s"
                  % (_fs_uri(spark, out_dir), _err_text(e2, 400)))
    finally:
        _fs_delete(spark, probe)


# ---------------------------------------------------------------------------
# Formato de settings DEL BANCO (bin/settings/<modelo>/pivot.json, datapull.json):
#   {"prod": {...}, "uat": {...}, "sbx": {...}}  y en cada ambiente:
#     "tables_info": {nombre: {"database", "table", "columns": [...], "where"}},
#     "working_path": "rps/working_path/{}/pivot/",  "lag": 1, ...
# El 'where' trae '{}' que el job original llena con fechas del cohort; aqui se
# replica la misma regla de load_tables()/hive_table_to_df() del framework.
# ---------------------------------------------------------------------------
_MESES = {"01": "ene", "02": "feb", "03": "mar", "04": "abr", "05": "may", "06": "jun",
          "07": "jul", "08": "ago", "09": "sep", "10": "oct", "11": "nov", "12": "dic"}
def _is_bank_settings(cfg):
    """True si el JSON es del formato del banco (ambientes con tables_info)."""
    if isinstance(cfg.get("tables_info"), dict):
        return True
    return any(isinstance(v, dict) and isinstance(v.get("tables_info"), dict)
               for v in cfg.values())
def _metastore_info(spark):
    """Diagnostico del catalogo: (catalogo, hive.metastore.uris, bases visibles).
    Primero se listan las bases: eso inicializa el catalogo y carga hive-site.xml."""
    try:
        dbs = sorted(d.name for d in spark.catalog.listDatabases())
    except Exception:
        dbs = []
    try:
        impl = spark.conf.get("spark.sql.catalogImplementation", "in-memory")
    except Exception:
        impl = "?"
    uris = ""
    try:
        uris = spark.sparkContext._jsc.hadoopConfiguration().get("hive.metastore.uris") or ""
    except Exception:
        pass
    if not uris:
        try:
            uris = spark.conf.get("spark.hadoop.hive.metastore.uris", "") or ""
        except Exception:
            pass
    return impl, uris, dbs
def _env_dbs(st):
    return {i["database"] for i in (st.get("tables_info") or {}).values()
            if isinstance(i, dict) and i.get("database")}
def _bank_env(cfg, env, spark=None):
    """Devuelve (nombre_env, settings_del_env). Sin --env, elige el ambiente cuyas
    bases EXISTEN en el metastore (en vez de adivinar 'uat')."""
    if isinstance(cfg.get("tables_info"), dict):
        return (env or "-"), cfg
    envs = [k for k, v in cfg.items() if isinstance(v, dict) and "tables_info" in v]
    if env:
        if env not in envs:
            raise SystemExit("Ambiente '%s' no existe en el config. Opciones: %s" % (env, envs))
        return env, cfg[env]
    if spark is not None:
        impl, uris, dbs = _metastore_info(spark)
        lower = {d.lower() for d in dbs}
        cand = [e for e in envs if _env_dbs(cfg[e]) and
                all(d.lower() in lower for d in _env_dbs(cfg[e]))]
        if cand:
            print("[config] --env no indicado; por las bases del metastore se usa '%s'" % cand[0])
            return cand[0], cfg[cand[0]]
    elegido = "uat" if "uat" in envs else envs[0]
    print("[config] --env no indicado y ningun ambiente coincide con el metastore; "
          "se usa '%s'. Opciones: %s" % (elegido, envs))
    return elegido, cfg[elegido]
def _cohort_dates(cohort, lag):
    """Igual que el job del banco: vintage = cohort+'01';
    start = 1er dia de (vintage - lag meses); end = ultimo dia de ese mes."""
    import calendar
    y, m = int(cohort[:4]), int(cohort[4:6])
    m -= int(lag)
    while m <= 0:
        m += 12
        y -= 1
    start = "%04d-%02d-01" % (y, m)
    end = "%04d-%02d-%02d" % (y, m, calendar.monthrange(y, m)[1])
    return start, end
def _bank_query(info, start, end):
    """SELECT <columns> FROM <database>.<table> [WHERE <where con fechas>]."""
    mes = _MESES[start[5:7]]
    cols = [c.format(mes) if "{}" in c else c for c in (info.get("columns") or [])]
    fields = ", ".join(cols) if cols else "*"
    q = "select %s from %s.%s" % (fields, info["database"], info["table"])
    where = info.get("where")
    if where:
        n = where.count("{}")
        if n == 0:
            args_w = []
        elif n == 1:
            # 1 placeholder: 'periodo = {}' usa el anio; el resto la fecha fin.
            args_w = [start[:4]] if "periodo" in where.lower() else [end]
        else:
            args_w = ([start, end] * n)[:n]
        q += " where " + where.format(*args_w)
    return q
_BASE_KEYS = ("base_path", "basePath", "BASE_PATH", "base_dir", "output_base_path")
def _pick_key(d, keys):
    if not isinstance(d, dict):
        return None
    low = {str(k).lower(): v for k, v in d.items()}
    for k in keys:
        v = d.get(k)
        if v is None:
            v = low.get(k.lower())
        if isinstance(v, str) and v.strip():
            return v.strip()
    return None
def _resolve_base_path(cfg, st, env, args, cfg_dir):
    """Ruta base de SALIDA y de donde salio. Prioridad:
    --base-path > BNX_BASE_PATH > base_path del ambiente > base_path global >
    --root > settings/jobs.json (base_path o general_root del ambiente)."""
    if getattr(args, "base_path", None):
        return args.base_path, "--base-path"
    if os.environ.get("BNX_BASE_PATH"):
        return os.environ["BNX_BASE_PATH"], "variable BNX_BASE_PATH"
    v = _pick_key(st, _BASE_KEYS)
    if v:
        return v, "base_path del ambiente '%s' en el JSON" % env
    v = _pick_key(cfg, _BASE_KEYS)
    if v:
        return v, "base_path global del JSON"
    if getattr(args, "root", None):
        return args.root, "--root"
    for cand in (os.path.join(cfg_dir, "jobs.json"),
                 os.path.join(os.path.dirname(cfg_dir), "jobs.json")):
        if os.path.isfile(cand):
            try:
                jenv = json.load(open(cand, encoding="utf-8")).get(env) or {}
                v = _pick_key(jenv, _BASE_KEYS + ("general_root",))
                if v:
                    return v, "%s (%s)" % (cand, env)
            except Exception:
                pass
    return None, None
def _default_fs(spark):
    try:
        return str(spark._jsc.hadoopConfiguration().get("fs.defaultFS") or "file:///")
    except Exception:
        return "file:///"
def _bank_sources(cfg, args, cfg_dir, spark=None):
    """Convierte el settings del banco a (src_cfg, previous_path)."""
    if spark is not None:
        impl, uris, dbs = _metastore_info(spark)
        print("[metastore] catalogo=%s | hive.metastore.uris=%s | %d base(s) visibles"
              % (impl, uris or "(vacio)", len(dbs)))
        if impl != "hive" or (not uris and set(dbs) <= {"default"}):
            print("[metastore] AVISO: esta SparkSession NO esta conectada al metastore del "
                  "cluster (catalogo '%s', uris %s). El PySpark del venv es standalone: "
                  "ve solo un metastore LOCAL vacio, por eso las tablas del banco 'no "
                  "existen'. Soluciones: (a) correr con el Spark del cluster "
                  "(spark-submit / pyspark del edge node), o (b) apuntar a su config: "
                  "export SPARK_CONF_DIR=/etc/spark/conf  (o copiar hive-site.xml a "
                  "$VIRTUAL_ENV/lib/python*/site-packages/pyspark/conf/) y/o "
                  "en el cfg: 'spark': {'conf': {'hive.metastore.uris': 'thrift://host:9083'}}"
                  % (impl, uris or "vacio"))
        if dbs:
            print("[metastore] bases visibles:", ", ".join(dbs[:25]) + (" ..." if len(dbs) > 25 else ""))
    env, st = _bank_env(cfg, args.env, spark)
    cohort = args.cohort
    if not cohort:
        import datetime
        cohort = datetime.date.today().strftime("%Y%m")
        print("[config] cohort no indicado (--cohort YYYYMM); se usa", cohort)
    lag = st.get("lag", 1)
    start, end = _cohort_dates(cohort, lag)
    print("[config] env=%s cohort=%s lag=%s -> fechas %s .. %s" % (env, cohort, lag, start, end))
    # Raiz de salida (en el cluster: ruta HDFS). Ver _resolve_base_path.
    root, origen = _resolve_base_path(cfg, st, env, args, cfg_dir)
    default_fs = _default_fs(spark) if spark is not None else "file:///"
    if not root:
        if not default_fs.startswith("file:"):
            # En HDFS NUNCA usamos la carpeta del paquete (/data/1/... del servidor):
            # no hay permiso y no es donde debe quedar la salida.
            raise SystemExit(
                "\\n[config] ERROR: falta la ruta base de SALIDA en HDFS (defaultFS=%s).\\n"
                "  No se encontro 'base_path' en el JSON (ni en el ambiente '%s', ni global),\\n"
                "  ni --base-path, ni BNX_BASE_PATH, ni general_root en settings/jobs.json.\\n"
                "  Agrega al pivot.json (global o dentro de \\"%s\\"):\\n"
                "      \\"base_path\\": \\"/data/<usuario>/managed/hive/<usuario>_managed/\\"\\n"
                "  o corre con:  --base-path /data/<usuario>/managed/hive/<usuario>_managed/\\n"
                "  Llaves de primer nivel en el JSON: %s\\n"
                "  Llaves del ambiente '%s': %s"
                % (default_fs, env, env, sorted(cfg.keys()), env, sorted(st.keys())))
        root = os.path.join(_here, "data")
        origen = "default local ./data (sin base_path)"
    print("[config] base_path de salida: %s   (origen: %s)" % (root, origen))
    wp = (st.get("working_path") or "working_path/{}/").format(cohort)
    prev = (root.rstrip("/") + "/" + wp.lstrip("/")).rstrip("/")
    src = {}
    for name, info in st["tables_info"].items():
        if not isinstance(info, dict) or "table" not in info or "database" not in info:
            print("[config] tables_info.%s sin database/table; se omite" % name)
            continue
        src[name] = {"table_name": name, "query": _bank_query(info, start, end),
                     "_check": {"db": info["database"], "table": info["table"],
                                "columns": list(info.get("columns") or [])}}
    print("[config] %d tabla(s) en tables_info: %s" % (len(src), ", ".join(src)))
    return src, prev


# ---------------------------------------------------------------------------
# JOBS DEL BANCO (def run(kernel)): se ejecutan con el Kernel de toolbox.
# Secuencia replicada de main.py del banco (class Launcher), que arma el job asi:
#   argumentos -f/--fid -e/--env -m/--model -j/--job -c/--cohort -v/--verbose
#   Kernel(job, os.environ["LOG_FILE_PATH"], os.environ["CONF_PATH"])
#   kernel.launch(args)      # Settings(spark.json, jobs.json, <model>/<job>.json) + SparkSession
#   importlib.import_module("jobs.<model>.<job>.job").run(kernel)
#   si falla: kernel.log.log_error() y se relanza la excepcion.
# Si el main.py del banco viaja en bank_src/, se IMPORTA y se usa su Launcher tal cual;
# si no, se replica esa misma secuencia. Las variables de entorno son las de
# bin/opt/profile.sh (APP_NAME, BIN_PATH, CONF_PATH, LOG_FILE_PATH, ROOT_LOCAL, PYLIB...).
# ---------------------------------------------------------------------------
def _aplicar_alias(src):
    """orden.json con nombres viejos (job, job_2...) -> nombres por ruta (rps_datapull...)."""
    al = ALIAS
    if not al:
        return src
    out = {}
    for k, v in (src or {}).items():
        if isinstance(v, dict) and isinstance(v.get("depends_on"), list):
            v = dict(v)
            v["depends_on"] = [al.get(d, d) for d in v["depends_on"]]
        out[al.get(k, k)] = v
    return out


def _nombre_job(nombre):
    """'rps_datapull', 'rps_datapull.py', 'RPS/datapull', 'job_2' (alias viejo) -> nombre canonico."""
    crudo = str(nombre).strip().replace("\\\\", "/").strip("/").lower()
    por_ruta = dict(("%s/%s" % (v.get("model"), v.get("job")), k)
                    for k, v in KERNEL.items() if v.get("model") and v.get("job"))
    if crudo in por_ruta:
        return por_ruta[crudo]
    n = os.path.splitext(os.path.basename(crudo))[0]
    n = ALIAS.get(n, n)
    return dict((k.lower(), k) for k in KERNEL).get(n, n)


def _kernel_seleccion(args):
    """(jobs de kernel a correr, si corren ademas los aggregates)."""
    if not KERNEL:
        return [], True
    if args.source:
        n = _nombre_job(args.source)
        if n not in KERNEL:
            return [], True
        crudo = os.path.splitext(os.path.basename(str(args.source).strip().replace("\\\\", "/").strip("/")))[0]
        if crudo.lower() != n.lower():
            print("[source] '%s' -> '%s' (nombre por ruta %s/%s; '%s' es el alias viejo)" % (
                args.source, n, KERNEL[n].get("model"), KERNEL[n].get("job"), crudo))
        else:
            print("[source] '%s' (job del banco %s/%s)" % (n, KERNEL[n].get("model"), KERNEL[n].get("job")))
        return [n], False
    return list(KERNEL), (len(REGISTRY) > 0 or bool(args.config))


def _kernel_buscar_settings(args):
    """Carpeta de settings del banco (bin/settings) -> (carpeta o None, motivo, lugares probados).
    --settings > CONF_PATH > BIN_PATH/settings > bank_src/settings > carpeta del --config y padres
    > ./settings > bin/settings."""
    return _bs.buscar_settings(args.settings, args.config, os.environ, bases=[_here])


def _kernel_settings_demo(settings_dir, env, entries, root):
    """settings MINIMOS COMPLETOS para el DEMO (no hay settings reales): se infieren del codigo de cada
    job (accesos self.config['x'], settings['tables_info'][t]['database'], config_custom[...]) con
    bnx_demo.settings_infer. Devuelve {'modelo/job': [claves inventadas]} (va al reporte del demo)."""
    try:
        from bnx_demo import settings_infer as _si
        return _si.generar(settings_dir, entries, env, root,
                           [d for d in (_bank_src, os.path.join(_here, "bank_pkg")) if os.path.isdir(d)])
    except Exception as ex:
        print("[kernel] aviso: no se pudieron inferir los settings del demo (%s: %s); se usan vacios"
              % (type(ex).__name__, str(ex)[:160]))
    def _w(rel, obj):
        ruta = os.path.join(settings_dir, rel)
        os.makedirs(os.path.dirname(ruta), exist_ok=True)
        with open(ruta, "w", encoding="utf-8") as fh:
            json.dump(obj, fh)
    _w("spark.json", {"logging_path": "logs/", "logging_level": "ERROR",
                      "default": {"spark.yarn.queue": "default"}, "spark_queue_uat": "default"})
    _w("jobs.json", {env: {"general_root": root.rstrip("/") + "/", "static": ""}})
    for e in entries:
        if e.get("model") and e.get("job"):
            _w("%s/%s.json" % (e["model"], e["job"]), {env: {}})
            _w("%s/config_custom.json" % e["model"], {"env": {env: {}}, "default": {}})
    return {}
def _hint_clave_faltante(ex, settings_dir, env, entry):
    """Si el error es un KeyError de la config de negocio: que clave falta y en que archivo de settings
    deberia estar (y que campo del panel de simulacion indica la carpeta real)."""
    if not isinstance(ex, KeyError):
        return ""
    import traceback
    clave = ex.args[0] if ex.args else "?"
    linea, archivo = "", ""
    try:
        fr = traceback.extract_tb(ex.__traceback__)
        if fr:
            archivo, linea = "%s:%s" % (os.path.basename(fr[-1].filename), fr[-1].lineno), fr[-1].line or ""
    except Exception:
        pass
    modelo, job = entry.get("model") or "<model>", entry.get("job") or "<job>"
    if "config_custom" in linea:
        donde = "%s/%s/config_custom.json (claves de 'default' o 'env.%s')" % (settings_dir or "<bin/settings>", modelo, env)
    elif "settings.jobs" in linea or "general_root" in linea:
        donde = "%s/jobs.json (bloque '%s')" % (settings_dir or "<bin/settings>", env)
    else:
        donde = "%s/%s/%s.json (bloque '%s')" % (settings_dir or "<bin/settings>", modelo, job, env)
    otro = _clave_en_otro_env(clave, settings_dir, env, modelo, job, linea)
    return ("[kernel] FALTA LA CLAVE %r en los settings: el codigo la lee en %s. Deberia estar en %s. "
            "Pasa la carpeta bin/settings del banco con --settings (en el panel de simulacion: campo "
            "'Carpeta bin/settings').%s" % (clave, archivo or "(archivo desconocido)", donde, otro))
def _clave_en_otro_env(clave, settings_dir, env, modelo, job, linea):
    """' AVISO: la clave existe en el ambiente prod pero no en uat' (no se modifica ningun settings)."""
    if not settings_dir or not isinstance(clave, str):
        return ""
    if "config_custom" in linea:
        rels = [modelo + "/config_custom.json"]
    elif "settings.jobs" in linea or "general_root" in linea:
        rels = ["jobs.json"]
    else:
        rels = [modelo + "/" + job + ".json", "jobs.json"]
    for rel in rels:
        try:
            with open(os.path.join(settings_dir, rel), "r", encoding="utf-8") as fh:
                d = json.load(fh)
        except (OSError, ValueError):
            continue
        bloques = d.get("env") if rel.endswith("config_custom.json") and isinstance(d.get("env"), dict) else d
        if not isinstance(bloques, dict):
            continue
        en = [e for e, v in bloques.items() if isinstance(v, dict) and clave in v and e != env]
        if en and not (isinstance(bloques.get(env), dict) and clave in bloques[env]):
            return (" AVISO: %r esta en el ambiente %s pero no en %r (%s). Corre la simulacion con ese ambiente "
                    "(selector 'Ambiente' del panel / --env %s); los settings del banco NO se modifican."
                    % (clave, " y ".join("'%s'" % e for e in en), env, rel, en[0]))
    return ""
def _patch_sql(spark, synth):
    """DEMO: spark.table(...) y spark.sql('select ...') sobre tablas que no existen -> df sintetico."""
    cls = type(spark)
    orig_sql = cls.sql

    def _sql(self, q, *a, **k):
        try:
            return orig_sql(self, q, *a, **k)
        except Exception:
            if str(q).lstrip().lower().startswith(("select", "with")):
                return synth
            raise
    try:
        cls.sql = _sql
        cls.table = lambda self, name: synth
    except Exception:
        pass


_DEMO_MOD = []
def _demo_mod():
    """bnx_demo/ (datos sinteticos por lectura, rutas del cluster -> demo_out/, shim hdfs) o None."""
    if not _DEMO_MOD:
        _DEMO_MOD.append(None)
        if os.path.isdir(os.path.join(_here, "bnx_demo")):
            try:
                import bnx_demo
                _DEMO_MOD[0] = bnx_demo
            except Exception as e:
                print("[demo] aviso: no se pudo importar bnx_demo (%s: %s); se usan lecturas de juguete"
                      % (type(e).__name__, str(e)[:120]))
    return _DEMO_MOD[0]
def _demo_out_dir():
    return os.path.abspath(os.environ.get("BNX_DEMO_OUT") or os.path.join(_here, "demo_out"))
def _demo_builder(builder):
    """Config de Spark del DEMO: todos los nucleos (BNX_DEMO_CORES), AQE, particiones acotadas, driver 4g
    (BNX_DEMO_MEM), sin barras de progreso. Sin bnx_demo/: local[1] con 2 particiones (como antes)."""
    try:
        from bnx_demo import sparkcfg
        return sparkcfg.aplicar_a(builder)
    except Exception:
        return (builder.master("local[1]").config("spark.ui.enabled", "false")
                .config("spark.sql.shuffle.partitions", "2"))
def _mon_obtener(demo=None):
    """Monitor de recursos (bnx_demo/monitor.py; BNX_MONITOR=0 lo apaga). N = nucleos asignados al demo."""
    try:
        from bnx_demo import monitor
        n = None
        if demo:
            from bnx_demo import sparkcfg
            n = sparkcfg.nucleos()
        return monitor.obtener(nucleos=n)
    except Exception:
        return None
def _mon_ini(nombre, demo=None):
    m = _mon_obtener(demo)
    if m is not None:
        m.job_inicio(nombre)
def _mon_fin(nombre, estado="OK"):
    m = _mon_obtener()
    if m is not None:
        try:
            return m.job_fin(nombre, estado)
        except Exception:
            return None
    return None
def _mon_extra(nombre):
    """Columnas de CPU/memoria de un job para la TABLA DE TIEMPOS."""
    m = _mon_obtener()
    s = m.stats.get(nombre) if m is not None else None
    if not s:
        return {}
    return {"cpu_prom": s["cpu_prom"], "cpu_pico": s["cpu_pico"], "nuc_prom": s["nuc_prom"],
            "mem_pico": s["mem_pico"], "tareas": s.get("tareas"), "eficiencia": s["eficiencia"]}
def _mon_linea():
    m = _mon_obtener()
    return m.linea_resumen() if m is not None else ""
def _demo_resumen():
    try:
        from bnx_demo import sparkcfg
        return sparkcfg.resumen()
    except Exception:
        return "demo: local[1] | shuffle 2"
def _kernel_conector_demo(work):
    """SparkConnector de DEMO: sesion LOCAL (sin yarn/Hive) con lecturas sinteticas."""
    jopts = ("-Djava.io.tmpdir=%s -Dorg.xerial.snappy.tempdir=%s -Djna.tmpdir=%s"
             % (work, work, work))

    class _ConectorDemo(object):
        def __init__(self, settings):
            self.settings = settings
            # los workers de PySpark usan el MISMO python que este (sin activar el venv no coincidia)
            # (en modo CLUSTER NO: PYSPARK_PYTHON viaja a los executors y el venv solo existe en el edge)
            if os.environ.get("BNX_CLUSTER_SPARK") != "1":
                os.environ.setdefault("PYSPARK_PYTHON", sys.executable)
                os.environ.setdefault("PYSPARK_DRIVER_PYTHON", sys.executable)
            b = SparkSession.builder.appName("bnx_kernel_demo")
            b = _demo_builder(b)       # local[N], AQE, shuffle, driver.memory (bnx_demo/sparkcfg.py)
            b = (b.config("spark.sql.warehouse.dir", os.path.join(_demo_out_dir(), "spark-warehouse"))
                 .config("spark.sql.ansi.enabled", "false")
                 .config("spark.local.dir", work)
                 .config("spark.driver.extraJavaOptions", jopts)
                 .config("spark.io.compression.codec", os.environ.get("BNX_IO_CODEC", "lz4")))
            self.session = b.getOrCreate()
            self.session.sparkContext.setLogLevel("ERROR")
            try:     # spark.driver.memory solo vale al crear la JVM: se comprueba que surtio efecto
                _mx = self.session._jvm.java.lang.Runtime.getRuntime().maxMemory() / 1048576.0
                print("[demo] sesion Spark: master=%s | JVM del driver max=%.0f MB (spark.driver.memory=%s)" % (
                    self.session.sparkContext.master, _mx, self.session.conf.get("spark.driver.memory", "?")))
            except Exception:
                pass
            if _demo_mod() is None:
                # sin bnx_demo/: lecturas de juguete (un mismo df para toda lectura)
                synth = _synthetic_df(self.session)
                _patch_reads(self.session, synth)
                _patch_sql(self.session, synth)
    return _ConectorDemo


def _kernel_demo_sin_correo():
    """DEMO: toolbox.email usa smtplib.SMTP (servidor interno del banco). En demo NUNCA se
    envia un correo ni se resuelve ese host: SMTP se reemplaza por un simulador."""
    import smtplib

    class _SmtpDemo(object):
        def __init__(self, *a, **k):
            print("[demo] SMTP simulado: el correo NO se envia (%s)" % (", ".join(map(str, a[:2])),))

        def __enter__(self):
            return self

        def __exit__(self, *a):
            return False

        def __getattr__(self, nombre):
            return lambda *a, **k: (250, b"demo")
    smtplib.SMTP = _SmtpDemo
    smtplib.SMTP_SSL = _SmtpDemo


_BANK_MAIN = []


def _bank_launcher():
    """main.py del banco (bank_src/main.py) importado, o None si no viajo / no importa."""
    if not _BANK_MAIN:
        _BANK_MAIN.append(None)
        ruta = os.path.join(_bank_src, "main.py")
        if os.path.isfile(ruta):
            import importlib.util
            try:
                spec = importlib.util.spec_from_file_location("bnx_bank_main", ruta)
                mod = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(mod)
                if hasattr(mod, "Launcher"):
                    _BANK_MAIN[0] = mod
            except Exception as e:
                print("[kernel] aviso: no se pudo importar bank_src/main.py (%s: %s); "
                      "se replica su secuencia" % (type(e).__name__, str(e)[:120]))
    return _BANK_MAIN[0]


def _bin_path_recursos(settings_dir, real_settings):
    """BIN_PATH de profile.sh: carpeta que contiene static/ y opt/ (modelos .xgb, profile.sh...).
    Preferencia: el bin/ del banco (padre de --settings) si trae esos recursos; si no, bank_src/ del paquete
    (donde viajan). Sin recursos en ninguno: el padre de --settings (REAL) o bank_src/ (DEMO), como antes.
    Evita rutas como '//static/modelo.xgb' cuando --settings es '/bnx_settings' (padre = '/')."""
    cands = []
    if real_settings and settings_dir:
        cands.append(os.path.dirname(os.path.abspath(settings_dir)))
    cands.append(_bank_src)
    for c in cands:
        # /opt existe en cualquier Linux: solo cuenta opt/profile.sh (el de bin/opt del banco)
        if os.path.isdir(os.path.join(c, "static")) or os.path.isfile(os.path.join(c, "opt", "profile.sh")):
            return c
    return cands[0]


def _kernel_entorno(args, settings_dir, real_settings, env, fid, model, job):
    """Variables de entorno de bin/opt/profile.sh que usan toolbox y los jobs."""
    import time
    bin_path = os.environ.get("BIN_PATH") or _bin_path_recursos(settings_dir, real_settings)
    root_local = os.environ.get("ROOT_LOCAL") or os.path.dirname(os.path.abspath(bin_path))
    app = "%s_%s_%s" % (os.environ.get("LOCAL_DIR") or "bnx", model or "x", job)
    log_dir = os.path.join(os.environ.get("LOG_PATH") or os.path.join(_here, "logs"),
                           time.strftime("%Y_%m"))
    os.makedirs(log_dir, exist_ok=True)
    log_file = os.path.join(log_dir, "%s_%s.log" % (app, time.strftime("%d_%H_%M_%S")))
    open(log_file, "a").close()
    pylib = os.environ.get("PYLIB")
    if not pylib:
        sh = os.environ.get("SPARK_HOME")
        pylib = os.path.join(sh, "python", "lib") if sh and os.path.isdir(os.path.join(sh, "python", "lib")) \
            else os.path.dirname(os.path.dirname(os.path.abspath(sys.modules["pyspark"].__file__)))
    os.environ.update({
        "FID": fid, "ENV": env, "MODEL": model or "", "JOB": job, "JOB_NAME": job,
        "APP_NAME": app, "BIN_PATH": bin_path, "CONF_PATH": settings_dir,
        "ROOT_LOCAL": root_local, "LOG_FILE_PATH": log_file, "PYLIB": pylib})
    return log_file


def _kernel_lanzar(entry, env, fid, cohort, verbose):
    """Construye el Kernel como el main.py del banco y llama modulo.run(kernel)."""
    model, job = entry.get("model") or "", entry.get("job") or ""
    if not model or not job:
        raise RuntimeError("no se conoce model/job de este job (el archivo se subio sin su ruta "
                           "jobs/<model>/<job>/job.py); sube la carpeta del proyecto completa")
    modulo = entry["module"]
    launcher = _bank_launcher() if modulo == "jobs.%s.%s.job" % (model, job) else None
    if launcher is not None:
        argv0 = sys.argv
        sys.argv = ["main.py", "-f", fid, "-e", env, "-m", model, "-j", job, "-c", cohort]
        if verbose:
            sys.argv += ["-v", "True"]
        try:
            return launcher.Launcher().run()
        finally:
            sys.argv = argv0
    import importlib
    from toolbox.kernel import Kernel
    kernel = Kernel(job, os.environ["LOG_FILE_PATH"], os.environ["CONF_PATH"])
    try:
        kernel.launch({"fid": fid, "env": env, "model": model, "job": job,
                       "cohort": cohort, "verbose": bool(verbose)})
        return importlib.import_module(modulo).run(kernel)
    except Exception:
        kernel.log.log_error()
        raise


def _compat_estado():
    """Tabla OK/PARCHEABLE/BLOQUEADO de las librerias del banco y si los parches estan activos."""
    if _bc is None:
        return
    rep = _bc.cargar_reporte()
    if not rep:
        return
    r = rep.get("resumen") or {}
    if not (r.get("PARCHEABLE") or r.get("BLOQUEADO")):
        return
    activo = _bc.activo_por_modo()
    print("[compat] librerias del banco: %d OK, %d PARCHEABLE, %d BLOQUEADO | parches BNX: %s" % (
        r.get("OK", 0), r.get("PARCHEABLE", 0), r.get("BLOQUEADO", 0),
        "ACTIVOS (demo/simulacion; no validado contra la salida original)" if activo else
        "INACTIVOS (modo real: BNX_BANK_COMPAT=1 los activa; " + _bc.AVISO_REAL + ")"))
    for t in _bc.tabla_estados(rep):
        if t["estado"] != "OK":
            print("[compat]   %-11s %s %s%s" % (t["estado"], t["libreria"], t["version"],
                                                 "" if t["usada"] else " (el modelo no la usa)"))
def _python_executors_seguro():
    """Modo CLUSTER (YARN): PYSPARK_PYTHON viaja a los EXECUTORS y el venv solo existe en el edge. Si apunta al
    venv del paquete se quita ANTES de crear la SparkContext. No toca el del cluster."""
    if os.environ.get("BNX_CLUSTER_SPARK") != "1":
        return
    py = os.environ.get("PYSPARK_PYTHON") or ""
    if not py or py.startswith("./"):
        return
    venvs = (os.path.join(_here, ".venv") + os.sep, os.path.realpath(os.path.join(_here, ".venv")) + os.sep)
    if py.startswith(venvs):
        print("[python] AVISO: PYSPARK_PYTHON=%s es el venv del edge (no existe en los nodos): se quita para que los "
              "executors usen el Python del cluster (o BNX_EXECUTOR_PYTHON)" % py)
        os.environ.pop("PYSPARK_PYTHON", None)
def _info_python():
    """Python del driver y lo que el cluster pudo haber fijado (diagnostico de 'No module named ...')."""
    _python_executors_seguro()
    print("[python] driver=%s (%s) | PYSPARK_PYTHON=%s | PYSPARK_DRIVER_PYTHON=%s" % (
        sys.executable, sys.version.split()[0], os.environ.get("PYSPARK_PYTHON") or "(sin definir)",
        os.environ.get("PYSPARK_DRIVER_PYTHON") or "(sin definir)"))


def _kernel_main(args, nombres, correr_agg=False):
    """Corre los jobs de kernel EN ORDEN (orden.json / depends_on; pivote primero).
    Devuelve 0 si todos OK, 1 si alguno fallo o se salto.
    DEMO solo con --demo o sin pedir nada real; con --config/--settings/--env/--cohort/--fid
    es REAL y exige los settings del banco (nunca cae a demo en silencio)."""
    import datetime
    import time
    import traceback
    conf_path = os.environ.get("CONF_PATH")
    demo, motivo_modo = _bs.modo_ejecucion(args.config, args.settings, args.demo, args.env,
                                           args.cohort, args.fid, conf_path)
    settings_dir, motivo_s, probados = None, "", []
    if not demo or args.settings or conf_path or args.config:
        settings_dir, motivo_s, probados = _kernel_buscar_settings(args)
    else:    # DEMO sin pedir nada: usa el bin/settings que VIAJA en el paquete (bank_src/settings), si lo hay
        _emp = os.path.join(_bank_src, "settings")
        if os.path.isfile(os.path.join(_emp, "spark.json")):
            settings_dir, motivo_s = _emp, "bank_src/settings del paquete (autodetectado)"
    if not demo:
        if settings_dir and not os.path.isdir(settings_dir):
            raise SystemExit("[kernel] ERROR: la carpeta de settings '%s' (%s) no existe. "
                             "No se ejecuto nada." % (settings_dir, motivo_s))
        if not settings_dir:
            if args.config and not args.source and correr_agg:
                print("[kernel] AVISO: %d job(s) del banco (run(kernel)) SALTADOS: hay --config pero no se "
                      "encontraron settings del banco; no se corrio nada de kernel ni DEMO. Para "
                      "correrlos usa  --settings <bin/settings>  o  --source <job>." % len(nombres))
                return 0
            sys.stderr.write(
                "[kernel] ERROR: Este job es del framework del banco (run(kernel)): necesita --settings "
                "<bin/settings> (spark.json, jobs.json, <model>/<job>.json). No se ejecuto nada.\\n"
                "  Modo: REAL (%s). Para probar con datos sinteticos usa --demo.\\n"
                "  Se busco settings (carpeta con spark.json) en: %s\\n"
                % (motivo_modo, ", ".join(probados[:8]) or "(sin candidatos)"))
            raise SystemExit(2)
    os.environ["BNX_MODO"] = "demo" if demo else "real"   # bank_compat: parches activos solo en demo (o BNX_BANK_COMPAT=1)
    if _bc is not None:
        try:
            _bc.instalar()      # parches de las librerias del banco (tambien para imports directos de lib_*)
        except Exception as _e_bc:
            print("[compat] aviso: no se pudieron instalar los parches (%s: %s)" % (type(_e_bc).__name__, str(_e_bc)[:120]))
    if _bd is not None:
        try:
            # ANTES de activar el demo: asi el diagnostico queda como capa interna y ve la ruta ya redirigida
            _bd.instalar()      # log de escritura: columnas nulas, filas de ejemplo, modo UDF y parches (BNX_DIAG_ESCRITURA=0 lo apaga)
        except Exception as _e_bd:
            print("[diag-escritura] aviso: no se pudo instalar el log de escritura (%s: %s)" % (type(_e_bd).__name__, str(_e_bd)[:120]))
    env = (args.env or ("uat" if demo else "")).lower()
    if not env:
        raise SystemExit("[kernel] falta --env (prod|uat|sbx): es el ambiente de los settings del banco")
    fid = (args.fid or "demo").lower()
    cohort = args.cohort or datetime.date.today().strftime("%Y%m")
    work = _work_dir()
    base = None
    entradas = dict((n, KERNEL[n]) for n in nombres)
    print("=" * 64)
    print("JOBS DEL BANCO (run(kernel)) — %s" % ("MODO DEMO (Spark local, lecturas sinteticas; NO toca "
                                                 "datos reales)" if demo else "MODO REAL (datos reales)"))
    print("  por que: %s" % motivo_modo)
    if settings_dir:
        print("  settings: %s (%s) | env=%s cohort=%s fid=%s" % (settings_dir, motivo_s, env, cohort, fid))
    if demo:
        print("  [demo] config: " + _demo_resumen())
    _info_python()
    _compat_estado()
    print("=" * 64)
    if _bc is not None and not args.source:
        try:
            _bc.limpiar_faltantes(None)
        except Exception:
            pass
    try:
        import toolbox.kernel as _tk
    except Exception as e:
        raise SystemExit("[kernel] no se pudo importar toolbox.kernel (%s: %s). Python del driver: %s. "
                         "Monta el entorno con 'bash setup.sh' (toolbox viaja en bank_pkg/ o bank_src/) y "
                         "revisa: %s -c 'import toolbox.kernel'"
                         % (type(e).__name__, e, sys.executable, sys.executable))
    if demo:
        base = tempfile.mkdtemp(prefix="bnx_kernel_", dir=work)
        _inventadas = {}
        settings_dir_demo = not settings_dir
        if not settings_dir:
            settings_dir = os.path.join(base, "settings")
            _inv = _kernel_settings_demo(settings_dir, env, list(entradas.values()), os.path.join(base, "data"))
            _inventadas = _inv or {}
            _n_inv = sum(len(v) for v in _inventadas.values())
            print("[kernel] DEMO sin --settings: settings minimos INFERIDOS del codigo de los jobs (%d clave(s) "
                  "inventadas; detalle en REPORTE_DEMO.json). Son un relleno para que no falle por claves "
                  "ausentes, no tu config de negocio: con --settings <bin/settings> se usa la real (SIN "
                  "conectar a Hive/Teradata)." % _n_inv)
        _tk.SparkConnector = _kernel_conector_demo(work)
        _kernel_demo_sin_correo()
        _dm = _demo_mod()
        if _dm is not None:
            _dm.iniciar(_here, bank_dirs=[_bank_src, os.path.join(_here, "bank_pkg")],
                        settings_dir=settings_dir, cohort=cohort, limpiar=not args.source)
            _dm.registrar_inventadas(_inventadas)
            _dm.activar()
    if args.source:
        lista, deps = list(nombres), {}
    else:
        lista, deps = _orden_dependencias(list(nombres), {}, _aplicar_alias(_cargar_orden(args.orden)),
                                          modelos=dict((n, (entradas[n].get("model"), entradas[n].get("job")))
                                                       for n in nombres))
    ok = fail = skip = 0
    resumen = []
    fallidos = set()
    for i, n in enumerate(lista):
        e = entradas[n]
        bloquean = [d for d in deps.get(n, []) if d in fallidos]
        if bloquean or (fail and not args.continuar_si_falla):
            motivo = ("depende de %s, que fallo o se salto" % ", ".join(bloquean)) if bloquean \
                else "un job anterior fallo (usa --continuar-si-falla para seguir)"
            print("[kernel] SALTADO %s: %s" % (n, motivo))
            fallidos.add(n)
            skip += 1
            resumen.append((n, "SALTADO", 0.0, motivo))
            continue
        print("-" * 64)
        print("[kernel] INICIO %s (%d/%d)  model=%s job=%s" % (n, i + 1, len(lista), e.get("model"), e.get("job")))
        t0 = time.time()
        log_file = ""
        _mon_ini(n, demo)
        if demo and _demo_mod() is not None:
            _demo_mod().set_job(n)
        try:
            log_file = _kernel_entorno(args, settings_dir, not (demo and settings_dir_demo),
                                       env, fid, e.get("model"), e.get("job") or n)
            os.environ["BNX_JOB_ID"] = n    # nombre del job para los mensajes de bank_compat (rps_datapull)
            if _bc is not None:
                try:
                    _bc.limpiar_faltantes(n)
                except Exception:
                    pass
            ret = _kernel_lanzar(e, env, fid, cohort, args.verbose)
            dt = time.time() - t0
            print("[kernel] FIN OK %s en %.1f s | log: %s%s" % (
                n, dt, log_file, "" if ret is None else " | retorno: %r" % (ret,)))
            ok += 1
            _mon_fin(n, "OK")
            resumen.append((n, "OK", dt, ""))
        except (Exception, SystemExit) as ex:
            dt = time.time() - t0
            cola = " | ".join(l.strip() for l in traceback.format_exc().strip().splitlines()[-6:])
            _falta = None
            if _bc is not None:
                try:
                    _falta = _bc.traducir_excepcion(ex, n)
                except Exception:
                    _falta = None
            if _falta:
                _corto = "FALTA %s (libreria %s %s)" % (_falta.get("componente"), _falta.get("libreria"),
                                                       _falta.get("version") or "")
                print("[kernel] FIN ERROR %s en %.1f s: %s" % (n, dt, _corto))
                print(_bc.bloque_terminal(_bc.registrar_faltante(_falta, job=n)))
            else:
                print("[kernel] FIN ERROR %s en %.1f s: %s: %s" % (n, dt, type(ex).__name__, str(ex)[:300]))
                _hint = _hint_clave_faltante(ex, settings_dir, env, e)
                if _hint:
                    print(_hint)
                print("         traceback (corto): %s" % cola[:900])
            if log_file:
                print("         log: %s" % log_file)
            fail += 1
            fallidos.add(n)
            _mon_fin(n, "ERROR")
            resumen.append((n, "ERROR", dt, (_corto if _falta else "%s: %s" % (type(ex).__name__, str(ex)[:160]))))
    print("=" * 64)
    for n, est, dt, det in resumen:
        print("  %-8s %-28s %6.1f s  %s" % (est, n, dt, det))
    print("RESULTADO jobs del banco: %d OK, %d con error, %d saltados." % (ok, fail, skip))
    for n, est, dt, det in resumen:
        _TIEMPOS.append(dict({"etapa": "kernel", "nombre": n, "seg": dt, "estado": est}, **_mon_extra(n)))
    _imprimir_tiempos()
    if demo and _demo_mod() is not None:
        _demo_mod().reporte()
        if _bc is not None:
            _bc.anexar_a_reporte_demo(os.path.join(_demo_out_dir(), "REPORTE_DEMO.json"))
        _demo_mod().desactivar()
    try:
        act = SparkSession.getActiveSession()
        if act is not None:
            act.stop()
    except Exception:
        pass
    if base:
        shutil.rmtree(base, ignore_errors=True)
    return 0 if (fail == 0 and skip == 0) else 1


def main():
    ap = argparse.ArgumentParser(description="Framework MLOps v2 — entry point")
    ap.add_argument("--config", help="JSON con previous_path y sources (datos reales)")
    ap.add_argument("--source", help="correr solo esta fuente (por nombre)")
    ap.add_argument("--skip-extract", action="store_true",
                    help="no ejecutar los query; usar los parquets ya bajados")
    ap.add_argument("--extract-only", action="store_true",
                    help="solo bajar los query a parquet, sin correr los aggregates")
    ap.add_argument("--dry-run", action="store_true",
                    help="solo imprime los QUERY que se ejecutarian; no toca Spark/Hive ni escribe")
    ap.add_argument("--env", help="ambiente del settings del banco: prod | uat | sbx")
    ap.add_argument("--cohort", help="cohort YYYYMM para las fechas del where (default: mes actual)")
    ap.add_argument("--base-path", dest="base_path",
                    help="ruta base de SALIDA (HDFS en el cluster); se le agrega working_path")
    ap.add_argument("--root", help="general_root (default: settings/jobs.json o ./data)")
    ap.add_argument("--orden", help="JSON con el orden de las fuentes (default: orden.json junto a main.py)")
    ap.add_argument("--settings", help="carpeta bin/settings del banco (jobs de kernel run(kernel)); default: $CONF_PATH")
    ap.add_argument("--fid", help="FID del banco (jobs de kernel; default: demo)")
    ap.add_argument("--demo", action="store_true",
                    help="jobs de kernel: Spark LOCAL con lecturas sinteticas (sin yarn/Hive/Teradata), aunque haya --settings")
    ap.add_argument("--continuar-si-falla", dest="continuar_si_falla", action="store_true",
                    help="jobs de kernel: si uno falla, seguir con los demas (por defecto se detiene)")
    ap.add_argument("--verbose", action="store_true", help="jobs de kernel: log extendido (-v del banco)")
    args = ap.parse_args()
    # Jobs del banco (def run(kernel)): los corre el runner con toolbox.kernel.Kernel.
    kernel_sel, correr_agg = _kernel_seleccion(args)
    kernel_rc = 0
    if args.source and not kernel_sel:
        _validar_source_antes_de_spark(args)
    if kernel_sel:
        kernel_rc = _kernel_main(args, kernel_sel, correr_agg)
        _pidio_real = bool(args.settings or args.env or args.cohort or args.fid or os.environ.get("CONF_PATH"))
        if not correr_agg or (not args.config and not args.demo and _pidio_real):
            # con --settings/--env (sin --config) NO se encadena el DEMO sintetico de los aggregates
            raise SystemExit(kernel_rc)
    demo = not args.config
    cfg = {} if demo else _load_config(args.config)
    cfg_dir = os.path.dirname(os.path.abspath(args.config)) if args.config else _here
    bank_fmt = (not demo) and _is_bank_settings(cfg)
    scfg_spark = cfg.get("spark") or {}
    work = _work_dir()
    # tmp de Java/Spark/snappy dentro del paquete (escribible), no en /tmp.
    jopts = ("-Djava.io.tmpdir=%s -Dorg.xerial.snappy.tempdir=%s -Djna.tmpdir=%s"
             % (work, work, work))
    cluster = os.environ.get("BNX_CLUSTER_SPARK") == "1"
    base_remota = False
    _python_executors_seguro()
    builder = SparkSession.builder.appName(scfg_spark.get("app_name", "framework_mlops_v2"))
    if cluster:
        # Lanzado con el spark-submit del cluster: master/conf/metastore vienen de
        # alli (--master yarn, spark-defaults, hive-site.xml). NO se pisa el master:
        # un "spark.master": "local[2]" en el JSON (como trae cfg.example.json) hacia
        # que corriera LOCAL aunque se lanzara con --master yarn. Para otro master
        # en el cluster: BNX_MASTER=... bash run.sh
        if scfg_spark.get("master"):
            print("[spark] modo CLUSTER: se IGNORA 'spark.master'=%s del JSON "
                  "(manda el --master de spark-submit; usa BNX_MASTER para cambiarlo)"
                  % scfg_spark["master"])
        print("[spark] modo CLUSTER (spark-submit del nodo)")
    else:
        if _bs.es_demo(args.config, args.settings, args.demo):
            # DEMO (datos sinteticos): chico a proposito.
            _master, _shuf = scfg_spark.get("master"), None
        else:
            # DATOS REALES en un solo nodo: todos los nucleos y mas particiones.
            # (cfg spark.master / spark.conf mandan sobre estos valores.)
            _master = scfg_spark.get("master") or os.environ.get("BNX_MASTER") or "local[*]"
            _shuf = str(_bs.shuffle_local(_bs.nucleos(_master)))
        if _shuf is None:          # DEMO: config de bnx_demo/sparkcfg.py (cores, AQE, particiones, driver 4g)
            builder = _demo_builder(builder)
            if _master:
                builder = builder.master(_master)
            print("[demo] config de Spark: " + _demo_resumen())
        else:
            builder = (builder.master(_master)
                       .config("spark.ui.enabled", "false")
                       .config("spark.sql.shuffle.partitions", _shuf))
        builder = (builder.config("spark.local.dir", work)
                   .config("spark.driver.extraJavaOptions", jopts))
    # Compresion INTERNA de Spark (shuffle/mapStatus): lz4 en vez de zstd. zstd-jni
    # es nativo y se extrae a /tmp; en servidores con /tmp 'noexec' revienta con
    # UnsatisfiedLinkError (libzstd-jni ... failed to map segment). lz4 tiene
    # fallback en Java puro. Se puede cambiar en el cfg: spark.conf o BNX_IO_CODEC.
    _io_codec = os.environ.get("BNX_IO_CODEC", "lz4")
    builder = (builder.config("spark.io.compression.codec", _io_codec)
                      .config("spark.shuffle.mapStatus.compression.codec", _io_codec))
    for k, v in (scfg_spark.get("conf") or {}).items():   # conf extra del JSON
        builder = builder.config(k, str(v))
    # Hive (tablas del catalogo/metastore): "spark.hive": true, o automatico si
    # alguna fuente usa query/source_table.
    _src0 = cfg.get("sources") or {}
    _usa_sql = any(isinstance(v, dict) and (v.get("query") or v.get("query_file")
                                            or v.get("source_table")) for v in _src0.values())
    if scfg_spark.get("hive", _usa_sql or bank_fmt):
        try:
            builder = builder.enableHiveSupport()
        except Exception as e:
            print("[aviso] no se pudo habilitar Hive:", str(e)[:120])
    spark = builder.getOrCreate()
    spark.sparkContext.setLogLevel("ERROR")
    # Donde quedo REALMENTE la sesion (para verificar que se registro en YARN).
    _sc = spark.sparkContext
    print("[spark] master=%s | applicationId=%s" % (_sc.master, _sc.applicationId))
    _log_conf_efectiva(spark, cluster, not _bs.es_demo(args.config, args.settings, args.demo))
    if cluster and not str(_sc.master).startswith("yarn") and not os.environ.get("BNX_MASTER"):
        print("[spark] AVISO: modo CLUSTER pero la sesion NO esta en YARN (master=%s). "
              "Revisa HADOOP_CONF_DIR/YARN_CONF_DIR (yarn-site.xml) y spark-defaults.conf "
              "(spark.master) del cluster." % _sc.master)

    print("=" * 64)
    print("FRAMEWORK MLOPS v2 — %s" % ("MODO DEMO (datos sinteticos)" if demo else "MODO REAL (datos reales)"))
    print("  por que: %s" % ("sin --config" if demo else "se indico --config %s" % args.config))
    if args.demo and args.config:
        print("  AVISO: --demo solo aplica a los jobs de kernel; con --config estas fuentes usan datos REALES.")
    if demo and (args.env or args.cohort or args.fid or args.settings):
        print("  AVISO: --settings/--env/--cohort/--fid se ignoran sin --config: esto es DEMO de aggregates "
              "(jobs del banco: --source <job>, p.ej. --source rps_datapull; tablas con settings: --config <json>).")
    _info_python()
    print("=" * 64)
    _report_optimizations()

    if demo:
        synth = _synthetic_df(spark)
        print("\\nENTRADA sintetica (%d filas):" % synth.count())
        synth.show(5, truncate=False)
        _tb, base_remota, _tb_origen = _tmp_spark_base(spark, args, work)
        if base_remota:
            base = "%s/bnx_main_%d_%d" % (_tb, os.getpid(), int(time.time()))
            print("[demo] temporales en HDFS: %s (origen: %s)" % (base, _tb_origen))
        else:
            base = tempfile.mkdtemp(prefix="bnx_main_", dir=work)
        _base_dir = base if (base_remota or _default_fs(spark).startswith("file:")) else "file://" + base
        prev = _base_dir + "/datapull"
        _fs_mkdirs(spark, prev)
        for s in REGISTRY:
            synth.write.mode("overwrite").parquet(prev + "/" + s)
        _patch_reads(spark, synth)
        src_cfg = {s: {"table_name": s} for s in REGISTRY}
    elif bank_fmt:
        # Settings del banco (pivot.json/datapull.json): cada tabla de tables_info
        # se baja a parquet en <general_root>/<working_path>/<tabla>.
        base = None
        src_cfg, prev = _bank_sources(cfg, args, cfg_dir, spark)
        _fs_mkdirs(spark, prev)
        print("previous_path:", _fs_uri(spark, prev))
    else:
        base = None
        prev = cfg.get("previous_path") or os.path.join(_here, "data", "datapull")
        if "://" not in prev and not os.path.isabs(prev):
            prev = os.path.join(cfg_dir, prev)
        _fs_mkdirs(spark, prev)
        print("previous_path:", _fs_uri(spark, prev))
        src_cfg = cfg.get("sources") or {s: {"table_name": s} for s in REGISTRY}
    if not args.dry_run:
        _ensure_parquet_codec(spark, prev)
    if args.source:
        # Validar y normalizar --source ANTES de tocar datos: antes un nombre que no
        # coincidia exacto (job_3.py, mayusculas, errata) se ignoraba en silencio y se
        # bajaban TODAS las tablas.
        args.source = _resolver_source(args.source, src_cfg, bank_fmt)
    if bank_fmt and args.source and args.source not in src_cfg:
        # --source es el JOB (p.ej. job_3), no una tabla: se bajan TODAS las
        # tablas del config y luego corre el aggregate del job si esta registrado.
        print("[config] '%s' no es una tabla de tables_info: se extraen todas las "
              "tablas del config para ese job." % args.source)
        fuentes = list(src_cfg.keys())
        job_agg = args.source
    else:
        fuentes = [args.source] if args.source else list(src_cfg.keys())
        job_agg = None
    # PIVOTE primero: las demas fuentes dependen de su salida, asi que el proceso
    # pivote SIEMPRE corre antes. Se identifica por nombre ('pivote'/'pivot') o
    # marcando la fuente con "pivot": true en el cfg.json.
    # Orden por DEPENDENCIAS (depends_on en cfg.json u orden.json). Sin depends_on
    # es identico a 'pivote primero'. Con --source se corre solo esa fuente: el
    # orden lo da tu orquestador externo (Airflow/cron).
    if args.source:
        fuentes, deps_explicitas = _orden_pivote_primero(fuentes, src_cfg), {}
    else:
        fuentes, deps_explicitas = _orden_dependencias(fuentes, src_cfg, _cargar_orden(args.orden))
    ok = fail = 0
    fallidas = set()          # fuentes que fallaron o se saltaron
    _prev_s, _prev_fail = None, 0
    # Cada fuente es un JOB (comparte la misma SparkSession, que se pasa a cada
    # aggregate). Extrae su query y corre su aggregate en su propio bloque aislado;
    # una que falla NO tumba a las demas. Para correr una sola como job separado
    # desde tu orquestador (respetando que pivote fue primero):  run.sh --source X
    for s in fuentes:
        # Registrar si la fuente anterior fallo (se hace aqui para no tocar cada 'continue')
        if _prev_s is not None and fail > _prev_fail:
            fallidas.add(_prev_s)
        _prev_s, _prev_fail = s, fail
        if s not in REGISTRY and not bank_fmt:
            print("\\n[skip] fuente no registrada:", s); continue
        _bloquean = [d for d in deps_explicitas.get(s, []) if d in fallidas]
        if _bloquean:
            print("\\n" + "-" * 64); print("FUENTE:", s)
            print("  [skip] no corre: depende de %s, que fallo o se salto" % ", ".join(_bloquean))
            fail += 1
            continue
        print("\\n" + "-" * 64); print("FUENTE:", s)
        scfg = src_cfg.get(s, {"table_name": s})
        try:
            # 1) Extraccion propia de ESTA fuente (si trae query/source_table).
            if not demo and not args.skip_extract:
                if _extract_sources(spark, [s], src_cfg, prev, cfg_dir, args.dry_run):
                    raise RuntimeError("no se extrajo/escribio el parquet de '%s' "
                                       "(ver la causa raiz de arriba)" % s)
            if args.dry_run:
                ok += 1
                continue
            if bank_fmt and s not in REGISTRY and not args.extract_only:
                # Tabla del settings del banco: solo se baja; no tiene aggregate.
                print("  OK (tabla extraida; sin aggregate registrado para '%s')" % s)
                ok += 1
                continue
            if args.extract_only:
                # Solo OK si el parquet existe DE VERDAD.
                dest = os.path.join(prev, scfg.get("table_name", s))
                if _fs_parquet_files(spark, dest):
                    print("  extract-only OK: parquet escrito en", _fs_uri(spark, dest))
                    ok += 1
                else:
                    print("  extract-only ERROR: no hay parquet en", dest,
                          "(la fuente no tiene query o el write no escribio nada)")
                    fail += 1
                continue
            # 2) Aggregate de ESTA fuente.
            _ta = time.time()
            _mon_ini(s, demo)
            try:
                GroupBy(s, previous_path=prev, agg_dict=scfg,
                        sqlContext=spark).aggregate()
            except Exception:
                _mon_fin(s, "ERROR")
                _TIEMPOS.append(dict({"etapa": "aggregate", "nombre": s, "seg": time.time() - _ta, "estado": "ERROR"}, **_mon_extra(s)))
                raise
            _mon_fin(s, "OK")
            _TIEMPOS.append(dict({"etapa": "aggregate", "nombre": s, "seg": time.time() - _ta, "estado": "OK"}, **_mon_extra(s)))
            head, _ = os.path.split(prev)
            _tc = time.time()
            out = spark.read.parquet(os.path.join(head, "groupby"))
            _nf = out.count()
            _TIEMPOS.append({"etapa": "conteo", "nombre": s, "seg": time.time() - _tc,
                             "filas": _nf, "estado": "OK"})
            print("  OK -> salida: %d filas, %d columnas" % (_nf, len(out.columns)))
            if demo:
                out.show(5, truncate=False)
            ok += 1
        except Exception as e:
            print("  ERROR:", type(e).__name__, "-", str(e)[:200])
            if "no se extrajo" not in str(e):
                print("  (revisa los '# TODO py2spark' de aggregates/%s.py)" % s)
            fail += 1
    # --source <job> con settings del banco: tras bajar sus tablas, corre su aggregate.
    if job_agg and not args.extract_only:
        print("\\n" + "-" * 64); print("JOB:", job_agg)
        if job_agg not in REGISTRY:
            print("  [aviso] '%s' no esta en REGISTRY; solo se bajaron las tablas." % job_agg)
        elif fail:
            print("  [skip] no corre el aggregate: fallo la extraccion de alguna tabla.")
        else:
            try:
                _ta = time.time()
                GroupBy(job_agg, previous_path=prev, agg_dict={"table_name": job_agg},
                        sqlContext=spark).aggregate()
                _TIEMPOS.append({"etapa": "aggregate", "nombre": job_agg, "seg": time.time() - _ta, "estado": "OK"})
                print("  OK -> aggregate de '%s' terminado" % job_agg)
                ok += 1
            except Exception as e:
                print("  ERROR:", type(e).__name__, "-", str(e)[:160])
                fail += 1

    _imprimir_tiempos(spark)
    print("\\n" + "=" * 64)
    print("RESULTADO: %d fuente(s) OK, %d con error." % (ok, fail))
    if demo:
        print("Modo DEMO con datos sinteticos. Para datos reales: python main.py --config cfg.json")
    if base:
        if demo and base_remota:
            _fs_delete(spark, base)
        else:
            shutil.rmtree(base, ignore_errors=True)
    spark.stop()
    raise SystemExit(0 if (fail == 0 and not kernel_rc) else 1)


if __name__ == "__main__":
    main()
'''


_NOTAS_EJECUCION = '''# Notas de ejecucion — Framework MLOps v2

## 1) Montar el entorno (una sola vez)
```bash
bash setup.sh            # crea .venv e instala todo (offline si viene vendor/)
bash setup.sh --test     # (opcional) ademas corre pytest
```
`run.sh` NO instala nada: solo corre el modelo con el entorno ya montado.

`setup.sh` deja el **entorno virtual ya configurado para el cluster** (no depende
de run.sh): al activar `.venv` (`. .venv/bin/activate`) quedan listos
- `SPARK_CONF_DIR=.venv/spark_conf`: copia de la config de Spark del cluster
  (spark-defaults, hive-site.xml, core/hdfs/yarn-site) + ajustes BNX al final
  (`lz4` para shuffle/mapStatus, `spark.local.dir` propio);
- `JAVA_TOOL_OPTIONS` con `-Djava.io.tmpdir=./.bnx_tmp` (no `/tmp`, que suele ser noexec);
- `TMPDIR=./.bnx_tmp`.
Asi `python main.py`, `pyspark` o `spark-submit` desde el venv ya ven el
metastore/HDFS del cluster y no fallan con zstd/snappy nativos. Si el
`hive-site.xml` del cluster esta en otra ruta: `SPARK_CONF_DIR=/ruta bash setup.sh`.
(Es normal ver "Picked up JAVA_TOOL_OPTIONS: ..." al arrancar Java.)

### Pila de ciencia de datos (xgboost, lightgbm, scikit-learn, scipy, statsmodels, matplotlib, seaborn, joblib, threadpoolctl) y OpenMP
Si generaste el paquete con "Incluir pila de ciencia de datos", o tu codigo importa alguna de
estas librerias, el paquete las trae AUTOMATICAMENTE (requirements.txt + wheels offline en
`vendor/`, con sus dependencias: numpy, patsy, contourpy, pillow, ...). No hace falta el paso
extra de scoring. xgboost/lightgbm viajan siempre con scikit-learn.
- **Linux (servidor)**: las wheels de xgboost/lightgbm usan `libgomp` del sistema. Si `import xgboost`
  falla: `yum install libgomp` (RHEL/CentOS) o `apt-get install libgomp1`.
- **Mac**: xgboost/lightgbm buscan `libomp.dylib` de Homebrew. `setup.sh`/`run.sh` usan solos la copia
  que trae scikit-learn (`DYLD_LIBRARY_PATH=<venv>/.../sklearn/.dylibs`) si no hay
  `brew install libomp`. Si lo corres a mano: `export DYLD_LIBRARY_PATH=<esa carpeta>`
  o `brew install libomp`.
- **Windows**: instala Microsoft Visual C++ Redistributable (vcomp140.dll).
- `python check_env.py` imprime la pista exacta de tu sistema si xgboost no carga.

## 2) Correr con los settings del banco (pivot.json / datapull.json)
Los JSON de `bin/settings/<modelo>/` se leen tal cual (ambientes prod/uat/sbx con
`tables_info`). Cada tabla se convierte en
`select <columns> from <database>.<table> where <where>` (los `{}` del where se
llenan con las fechas del cohort) y se baja a parquet en
`<general_root>/<working_path>/<tabla>`.

```bash
# Ver los QUERY sin ejecutar nada (recomendado la primera vez)
bash run.sh --config pivot.json --env uat --cohort 202501 --dry-run

# Bajar las tablas a parquet
bash run.sh --config pivot.json --env uat --cohort 202501 --extract-only

# Todo (extraer + aggregates); un job concreto
bash run.sh --config pivot.json --env uat --cohort 202501 --source job_3
```
- `--env`: prod | uat | sbx. Si no se indica, se elige el ambiente cuyas bases
  existen en el metastore.
- `--cohort`: YYYYMM (default: mes actual).
- **Ruta de SALIDA** = `base_path` + `working_path` (con el cohort). En el cluster es
  una ruta **HDFS** (no el disco del servidor). Agrega al `pivot.json`:
  `"base_path": "/data/gcgaeapmxcgnu/managed/hive/gcgaeapmxcgnu_managed/"`
  (a nivel global o dentro de cada ambiente), o pasala por CLI con `--base-path`.
  Prioridad: `--base-path` > variable `BNX_BASE_PATH` > `base_path` del ambiente >
  `base_path` global > `--root` > `settings/jobs.json` (base_path/general_root).
  En HDFS, si no hay ninguna, el programa SE DETIENE con un mensaje (nunca escribe
  en la carpeta del paquete del servidor).
  Las lineas `[config] base_path de salida: ... (origen: ...)` y
  `previous_path: hdfs://...` confirman de donde salio y a donde se escribe.
- `--skip-extract`: reutiliza los parquets ya bajados.

## 3) IMPORTANTE: usar el metastore del CLUSTER
Si sale **"la base ... NO existe en este metastore"** pero la tabla SI se consulta
desde Hue / beeline / el pyspark del cluster, NO es el JSON: el PySpark del `.venv`
es standalone y, sin el `hive-site.xml` del cluster, crea un metastore LOCAL vacio
(solo ve la base `default`).

Opcion A (recomendada): correr con el **Spark del cluster**
```bash
BNX_SPARK=cluster bash run.sh --config pivot.json --env uat --cohort 202501 --extract-only
# si spark-submit no esta en el PATH:
BNX_SPARK_SUBMIT=/ruta/spark-submit BNX_SPARK=cluster bash run.sh ...
# master por defecto yarn; para otro:  BNX_MASTER=local[2]
```

Opcion B: apuntar el PySpark del venv a la config del cluster
```bash
export SPARK_CONF_DIR=/etc/spark/conf     # carpeta que contiene hive-site.xml
bash run.sh --config pivot.json --env uat --cohort 202501 --extract-only
```
`run.sh` ya busca solo `hive-site.xml` en `/etc/spark/conf`, `/etc/spark3/conf`,
`/etc/spark2/conf`, `/opt/cloudera/parcels/CDH/lib/spark/conf` y `/etc/hive/conf`.

Como saber cual Spark se esta usando (lineas al inicio de la corrida):
- `[run.sh] SPARK_CONF_DIR=...`  -> encontro la config del cluster.
- `[run.sh] AVISO: no se encontro hive-site.xml` -> metastore LOCAL (no vera tablas del banco).
- `[spark] modo CLUSTER` -> corre con el spark-submit del nodo.
- `[metastore] catalogo=... | hive.metastore.uris=... | N base(s) visibles`

## 4) Si algo falla, enviar
- Las lineas `[run.sh]`, `[spark]`, `[metastore]` y `QUERY:` de la corrida.
- `which spark-submit spark3-submit`
- `ls /etc/spark*/conf/hive-site.xml /etc/hive/conf/hive-site.xml`
- Con que herramienta se consulta la tabla cuando SI funciona (Hue, beeline, pyspark).
- Si el error es de escritura (`Mkdirs failed`, `Permission denied`, `AccessControlException`):
  la `previous_path` no es escribible -> revisa `base_path` / `--base-path`.

## 5) Errores de librerias nativas (/tmp noexec)
Si sale `UnsatisfiedLinkError ... libzstd-jni ... failed to map segment from shared
object` (o lo mismo con snappy), NO es el query ni falta un paquete: Java extrae la
libreria nativa a `/tmp` y el servidor tiene `/tmp` montado sin ejecucion.
El paquete ya lo evita:
- la JVM usa `./.bnx_tmp` como tmp (cambiar con `BNX_TMPDIR=/ruta/con/exec`);
- la compresion interna de Spark usa `lz4` (fallback Java puro) en vez de `zstd`
  (cambiar con `BNX_IO_CODEC=snappy|zstd|lz4`);
- el parquet cae a `uncompressed` si snappy no carga (forzar con `BNX_PARQUET_CODEC`).
La linea `[run.sh] tmp de la JVM: ...` confirma la ruta usada.

## 6) Orden de los procesos
- Todos comparten la misma SparkSession.
- El proceso **pivote** corre siempre primero (marcar `"pivot": true` o nombrarlo `pivote`).
- Cada fuente es un job: si una falla, las demas siguen.
- **Orden por dependencias (opcional):** `"depends_on": ["a"]` en la fuente del `cfg.json`
  o en `orden.json` (lo genera la pantalla "Orden de las fuentes" del portal). Esa fuente
  corre despues de `a` y se salta si `a` fallo. Sin `depends_on`, el orden es el de siempre.

## 7) Ejecución en el cluster (YARN) sin instalar en otros nodos

**Regla:** todo se instala **solo en el nodo desde donde lanzas** (edge node / master). Los
workers del cluster **no se tocan**: no llevan venv, ni librerías, ni este paquete.

### Dónde se instala y qué corre dónde
| Pieza | Dónde vive / corre | Qué necesita |
|---|---|---|
| `setup.sh` (crea `.venv` con Python 3.11 y las librerías) | **solo el edge node** | nada en los workers |
| **Driver** (`main.py`, tus jobs, xgboost/sklearn y los módulos del banco que usen pandas...) | el edge node (`--deploy-mode client`) | el `.venv` del edge node |
| **Executors** | JVM de Spark en los workers (los arranca YARN) | solo Java/Spark del cluster, **sin Python** |

Mientras el código use **SQL / DataFrame** (select, join, groupBy, agg, funciones de
`pyspark.sql.functions`, `spark.sql(...)`, escribir/leer parquet), todo el trabajo pesado lo hace la
JVM de los executors y **los workers no necesitan Python**. Python solo hace de "control remoto" en el driver.

### Cómo lanzar
```bash
# una sola vez, en el edge node
bash setup.sh

# la consulta/job en YARN con los recursos del banco (cola, executors, memoria)
BNX_SPARK=cluster bash run.sh --config pivot.json --settings /ruta/bin/settings --env uat --cohort 202501 --extract-only

# jobs del banco (run(kernel)) con sus settings
BNX_SPARK=cluster bash run.sh --settings /ruta/bin/settings --env uat --fid 170589
```
Al arrancar, `run.sh` imprime `[spark-conf]` con lo que va a pedir a YARN y `main.py` imprime
`[spark] master=... applicationId=...` con lo que realmente quedó (cola, executors, memoria, particiones).

### Cómo se aplican los recursos
`run.sh` calcula la configuración de **lanzamiento** (`spark.executor.*`, `spark.yarn.queue`,
`spark.dynamicAllocation.*`, `spark.driver.memory`...) y la pasa al `spark-submit` con un `--conf` por clave
(se guarda en `.bnx_spark_conf.properties`; no se usa `--properties-file` para no perder el
`spark-defaults.conf` del cluster). Orden de prioridad, de menor a mayor:
1. Valores por defecto: asignación dinámica activada y `spark.sql.shuffle.partitions=200`, sin cola.
2. `spark.conf` del cfg JSON del framework (`{"spark": {"conf": {...}}}`).
3. `spark.json` del banco (`--settings <bin/settings>` o `CONF_PATH`): bloque `default` (o el de `spark_config`;
   con `BNX_SPARK_MODELO=<modelo>` el `spark_config` de ese modelo). Con `--env uat` la cola es `spark_queue_uat`.
4. `BNX_DRIVER_MEMORY=8g` (solo la memoria del driver).
5. `BNX_SPARK_CONF="spark.executor.memory=20g;spark.executor.cores=4"` (pares separados por `;`): lo último que dices tú.

Nunca se pisa el `--master` (usa `BNX_MASTER=...` si necesitas otro) ni se quitan `lz4` ni el tmp propio.
Aviso: `spark.driver.memory` del banco puede ser grande (p.ej. 24g); el edge node debe tener esa RAM libre
o baja la memoria con `BNX_DRIVER_MEMORY`.

### Un solo nodo (sin YARN): `local[*]`
Con datos reales (`--config` o `--settings`) y sin cluster, la sesión usa **todos los núcleos** del nodo
(`local[*]`), `spark.sql.shuffle.partitions = max(8, 2 x núcleos)` y la memoria del driver
(`BNX_DRIVER_MEMORY`, o el `spark.driver.memory` del cfg, o la mitad de la RAM hasta 32g).
En local la memoria del driver solo vale **al lanzar**, por eso `run.sh` la pasa con `--driver-memory`
(si corres `python main.py` a mano, exporta `PYSPARK_SUBMIT_ARGS="--driver-memory 16g pyspark-shell"`).
El modo demo (sin `--config` ni `--settings`, o con `--demo`) sigue en `local[1]` con 2 particiones.
```bash
bash run.sh --config cfg.json --extract-only
BNX_DRIVER_MEMORY=16g bash run.sh --config cfg.json
```

### Librerías del banco incompletas (bank_compat)
`bank_compat_report.json` (y `python bank_compat.py` / `python check_env.py`) dice, por cada librería mex-lib del banco, si está
OK, es PARCHEABLE (la capa BNX resuelve imports/firmas rotos) o BLOQUEADO (falta lógica que tu modelo SÍ usa).
Los parches se activan solos en DEMO/SIMULACIÓN; en modo REAL solo con `BNX_BANK_COMPAT=1` (NO validado contra la salida
original: pide las librerías completas al equipo dueño). Cuando algo falta, el runner imprime QUÉ falta, DÓNDE cargarlo y los
PASOS, y lo deja en el log del job, en `logs/BNX_FALTANTES.json` y en `demo_out/REPORTE_DEMO.json`.
### Cómo leer la tabla de tiempos
Al final de cada corrida sale `TABLA DE TIEMPOS` con `master` y `applicationId`, y una fila por etapa:
`preflight` (consulta al catálogo, sin leer datos), `extract` (query + write a parquet, con particiones del
query y archivos escritos), `aggregate`, `conteo` y `kernel` (jobs del banco). La última línea dice qué fue lo más
lento. Pistas: pocas particiones con mucho tiempo = poco paralelismo (sube executors o `spark.sql.shuffle.partitions`);
muchos archivos pequeños = demasiadas particiones; `preflight` lento = problema del metastore.
Para contar filas escritas (una pasada extra, apagada por defecto): `BNX_CONTAR_FILAS=1`.
Para saltar el chequeo previo del catálogo: `BNX_PREFLIGHT=0`.

### Python en los executors: librerías enviadas con el job (sin instalar en los nodos)
Caso real: `PythonException ... worker.py ... cloudpickle.loads ... ModuleNotFoundError: No module named 'numpy'`. El
código del banco registra UDF (`udf.register("quita_acentos", ...)`, y las mex-lib: feature_engineering, group_by...). Esas
funciones corren en el **Python de los workers**, que no tiene las librerías del `.venv` (el venv solo lo usa el driver).
**Qué hace `run.sh` solo** (modo cluster, `BNX_DEPS_EXECUTORS=1` por defecto): si detecta Python en workers (modelo, `bank_src`
y wheels del banco; resultado en `.bnx_workers_python.json`) empaqueta **solo el site-packages** del venv (sin intérprete, sin
`pyspark`/`py4j`, sin `__pycache__`) en `.bnx_deps/bnxdeps-<hash>.tar.gz` (cacheado por hash del venv), lo envía con
`--archives <tgz>#bnxdeps` y fija `spark.executorEnv.PYTHONPATH=./bnxdeps` (antepone; conserva lo que ya fije el cluster).
Es temporal (vive en el contenedor YARN del job): **no se instala nada en los nodos**.
Solo funciona si el Python de los executors es de la **misma versión menor (3.11)** que el venv. Por eso antes hace un
**probe** (mini job en YARN, cacheado 12 h en `.bnx_tmp/probe_*.json`; `BNX_PROBE_FORZAR=1` lo repite). Si no coincide, **no corre
el job a ciegas**: imprime las opciones y sale (`BNX_PROBE_IGNORAR=1` sigue igual).
**Comandos para Angel** (en el edge, sin exportar `PYSPARK_PYTHON`):
1. `spark3-submit --master yarn --deploy-mode client probe_workers.py` (Python por defecto del cluster)
2. `spark3-submit --master yarn --deploy-mode client --conf spark.pyspark.python=/usr/bin/python3.11 probe_workers.py`
Resultado y qué hacer:
`run.sh` imprime `python de los EXECUTORS (YARN): ...` al arrancar y NUNCA les pasa el python del `.venv` (solo existe en el edge): ignora un
`PYSPARK_PYTHON` que apunte al venv y aborta si `BNX_EXECUTOR_PYTHON`/`spark.pyspark.python` lo apuntan. Si ves `Cannot run program ".../.venv/bin/python": error=2`
usa `BNX_EXECUTOR_PYTHON=<python de los nodos>` y borra la carpeta de salida a medias en HDFS antes de reintentar.
- (1) imprime versión `3.11` y `numpy=True pandas=True`: los nodos YA tienen todo. El probe imprime la línea exacta `BNX_EXECUTOR_PYTHON=<ruta>`;
  úsala: `BNX_EXECUTOR_PYTHON=<ruta> BNX_SPARK=cluster bash run.sh --settings <ruta>/bin/settings --env prod --source <job>`.
  `run.sh` fija `spark.pyspark.python` y `PYSPARK_PYTHON` de los executors (el driver sigue con el venv) y **no envía el venv**. Aunque no
  exportes la variable, `run.sh` hace ese mismo probe y usa el Python de los nodos si ve numpy/pandas (`BNX_DEPS_ENVIAR=1` envía el venv igual;
  `BNX_EXECUTOR_MODS=numpy,pandas,<otra>` cambia lo que exige).
- (1) imprime versión `3.11` y `numpy=False`: todo listo, `BNX_SPARK=cluster bash run.sh ...` envía las librerías.
- (1) falla con "different version" o imprime otra versión, y (2) imprime `3.11`: usar `BNX_EXECUTOR_PYTHON=/usr/bin/python3.11 BNX_SPARK=cluster bash run.sh ...`.
- Ninguna da 3.11: preguntar a plataforma qué Python 3.11 hay en los nodos (otra ruta); o reescribir la UDF con funciones de Spark SQL
  (`quita_acentos` → `lower(translate(coalesce(c,''), 'áéíóúüñÁÉÍÓÚÜÑ', 'aeiouunAEIOUUN'))`); plan B: `BNX_SPARK=local bash run.sh ...` en el edge.
- Desactivar todo: `BNX_DEPS_EXECUTORS=0`. Forzar el envío aunque no se detecte UDF: `BNX_DEPS_FORZAR=1`.
Si aun así falla en runtime con ese error, el framework lo traduce a "FALTA <módulo> en los EXECUTORS" (terminal, log, `BNX_FALTANTES.json`, pantalla).
**Job del banco o DEMO:** `--source` es el NOMBRE DEL JOB del banco (p.ej. `rps_datapull`), no un archivo (`main.py`). Con `--settings` + `--env`
corre el job real; un nombre inválido se detiene al inicio listando los válidos (no levanta Spark). Los temporales del DEMO en YARN van al HOME del
usuario en HDFS (`/user/<usuario>/.bnx_tmp`), nunca a la carpeta del paquete; cámbialo con `BNX_HDFS_TMP=/user/<usuario>/bnx_tmp` o `--base-path <ruta HDFS>`.
**Librerías UNA vez en HDFS (Cloudera YARN, mismas versiones en todos los nodos):** con `BNX_DEPS_HDFS=<carpeta hdfs>` `run.sh` sube el
`.tgz` a `<carpeta>/bnxdeps_<hash12>.tgz` (hash del venv) solo si no existe (`hdfs dfs -test -e`; si falta: `-mkdir -p` y `-put`, permisos 644)
y usa `--archives hdfs://.../bnxdeps_<hash>.tgz#bnxdeps`. YARN lo localiza en cada contenedor: **todos los nodos reciben el mismo archivo**, no se
sube desde el edge en cada corrida y no se instala nada. Log: `[run.sh] librerias de executors: hdfs:///.../bnxdeps_<hash>.tgz (reutilizado|subido ahora, N MB)`.
Si `hdfs` no está en el PATH o el `put` falla, avisa y envía desde el edge como antes. Comando recomendado:
`BNX_SPARK=cluster BNX_DEPS_HDFS=hdfs:///user/<usuario>/bnx/deps bash run.sh --settings ... --env ... --source <job>`
Si el venv cambia, se sube otra versión (otro hash). Para borrar las viejas: `BNX_DEPS_HDFS=hdfs:///user/<usuario>/bnx/deps bash run.sh --limpiar-deps-hdfs`
(lista y pide confirmación en terminal; conserva la del venv actual).
**Qué UDF pedía numpy en el caso de RPS:** `rmeans` de la mex-lib *feature engineering* (`base_features.py` /
`feature_engineering_standard.py`: `np.mean(x)`), activada por `"rmeans"` en `config_custom.json`. cloudpickle manda la
función por valor y en el worker importa sus globales (`np`). `quita_acentos` (data_pull) pediría `unidecode`, no numpy.
El error salió del `worker.py` del executor, que antes de leer la UDF ya validó que su Python es de la misma versión menor que
el driver: lo más probable es que el probe salga bien y baste con enviar el site-packages.
**UDF nativas (`BNX_UDF_NATIVAS=1`; run.sh lo activa solo si el probe dice que el Python de los executors no sirve):**
`bank_compat` intercepta `udf.register` / `F.udf` / `@udf` y, si el cuerpo de la función es simple (if/return,
asignaciones, aritmética, comparaciones, `x[i]`, `np.mean/sum/min/max` sobre arrays, `[v for v in x if ...]`, `len`,
`float/int`, `lower/upper/strip/replace`, `unidecode(x)`), NO registra la UDF de Python: la cambia por una expresión nativa de
Spark (`translate`, `aggregate`, `filter`, `CASE WHEN`...). En SQL (`spark.sql`, `selectExpr`, `expr`, `filter('...')`) se
reescribe el texto; vía DataFrame devuelve un `Column`. No se toca el código del banco. En el log:
`[compat] UDF quita_acentos -> expresion nativa Spark (translate/lower), sin Python en los workers` y en `BNX_FALTANTES.json`
como PARCHEADO (no validado). Se cambian `quita_acentos`, `rmeans`, `rt_mod`, `df_mod`; `incremental` (bucle) se queda en
Python (no usa numpy). Diferencias: `unidecode` translitera todo Unicode (emojis, griego, cirílico, `€`→`EUR`); la versión
nativa solo quita diacríticos latinos (Latin-1, Latin Extended-A/B, ß/æ/œ/ø/ł...). Errores de Python (índice fuera de rango,
división entre 0) siguen la regla de Spark (`spark.sql.ansi.enabled`: error o NULL).

### Log de diagnóstico en cada escritura (`BNX_DIAG_ESCRITURA`)
`bank_diag.py` (junto a `main.py`) engancha `df.write.*` / `saveAsTable` / `insertInto` y, al terminar cada escritura de un job del
banco, imprime y anexa a `LOG_FILE_PATH` (y a `BNX_DIAG_LOG` si existe) líneas `[diag-escritura]`: columnas 100% NULL (y 100% NaN),
columnas con más nulos que su entrada, 3 filas de ejemplo, modo de las UDF (original / nativas) y parches de `bank_compat` activos.
**Activo por defecto** (`BNX_DIAG_ESCRITURA=0` lo apaga): cuesta una agregación sobre una muestra (`BNX_DIAG_FILAS`, 20000), no un
count/collect de toda la tabla. `BNX_DIAG_MUESTRA=0` oculta los valores de las filas de ejemplo (en el cluster serían datos reales).
### Cuándo SÍ hace falta Python en los workers
Estos patrones ejecutan Python **dentro de los executors** y fallan en YARN si los nodos no tienen
Python 3.11 con las mismas librerías:
- `udf`, `F.udf`, `@udf`, `pandas_udf`, `spark.udf.register(...)` con función Python
- `applyInPandas`, `mapInPandas`, `applyInPandasWithState`, `mapInArrow`
- `df.rdd`, `rdd.map / flatMap / filter / mapPartitions`, `foreach`, `foreachPartition`, `sparkContext.parallelize`
- `pyspark.pandas` / `pandas_api()`
- `xgboost.spark` / `SparkXGBClassifier`, `SparkXGBRegressor`
- sklearn / xgboost / lightgbm usados dentro de una `udf`

El portal los detecta al generar el paquete (aviso en el reporte, por archivo y línea) y `main.py` los
vuelve a avisar al arrancar en modo cluster. Qué hacer:
1. Reescribir con funciones de **Spark SQL / DataFrame** (`when`, `regexp_extract`, `expr`, ventanas...).
2. O **agregar en Spark y calcular en el driver** (xgboost/sklearn): trae al driver solo un resultado **pequeño** o una muestra
   (`.limit(n)`, agregados; `toPandas()` solo sobre eso, nunca sobre tablas grandes). El código que genera el framework no usa pandas; `scoring/scorer.py` pasa a numpy solo las
   columnas de features y avisa si superan `max_rows`. Ajusta `BNX_DRIVER_MEMORY` si hace falta.
3. Último recurso (apagado por defecto): `BNX_ENVIAR_VENV=1` empaqueta el `.venv` y lo manda con `--archives`.
   Aun así los nodos necesitan `python3.11` en la misma ruta que el edge node. Solo para quien lo necesite.

Ejemplo de ejecución local (para probar sin cluster): `bash run.sh --config cfg.json --extract-only`.

## 8) MODO REAL vs MODO DEMO, settings del banco y diagnóstico en el cluster
- **DEMO solo** con `--demo` o cuando no pides nada real (sin `--config`, `--settings`, `--env`, `--cohort`, `--fid`).
  Con cualquiera de esos (o `CONF_PATH`) es **MODO REAL**. El encabezado siempre dice `MODO REAL` o `MODO DEMO` y por qué.
- Un job del banco (`run(kernel)`) en modo real necesita los settings (`spark.json`, `jobs.json`, `<model>/<job>.json`). Si no
  pasas `--settings`, se buscan en: `CONF_PATH`, `BIN_PATH/settings`, `bank_src/settings`, la carpeta del `--config` y sus
  padres, `./settings`, `bin/settings`. Si no hay, **error y sale con código 2 sin ejecutar nada** (nunca cae a demo).
- `--source job_3` (alias viejo) se muestra como `'job_3' -> 'rps_pivot' (nombre por ruta RPS/pivot)`.
- Recursos de YARN: salen del `spark.json` de los settings; si no hay, de `spark.conf` del `--config`; si no, solo 3 claves por
  defecto. La línea `[spark-conf] fuentes:` lo dice.
- `run.sh` verifica antes de lanzar que el python del venv importa `pandas`/`numpy` (solo si están en `requirements.txt`: se incluyen únicamente si algún código del paquete los usa) y `toolbox`; si falta algo lo dice y no lanza Spark.
  `setup.sh` termina con la misma verificación (`python check_env.py --driver`) y falla si algo falta.
- En cluster el **driver** usa el python del venv (`--conf spark.pyspark.driver.python`); los **executors** usan el del cluster.
- `run.sh` **no reemplaza** la config de Spark del cluster (`/etc/spark3/conf`, `/etc/spark/conf`...): la usa tal cual, o una copia
  completa + `hive-site.xml` si ella no lo trae. El log dice cuál usó y por qué (`BNX_CLUSTER_CONF_DIR=<dir>` para forzar otra).
- `bin/settings` viaja en el paquete (`bank_src/settings/`, si lo subiste): el DEMO lo autodetecta y lo usa sin `--settings`
  (`settings: ... bank_src/settings del paquete (autodetectado)`); `--settings <otra carpeta>` manda sobre el del paquete. Sin settings
  el demo INFIERE unos minimos del codigo de los jobs (claves inventadas: `demo_out/REPORTE_DEMO.json`, `settings_inventados`). Si falta
  una clave, el log dice cual, en que archivo deberia estar y si existe en otro ambiente (`--env prod`). `--env` elige uat/prod/sbx.
- DEMO: `local[N]` con `N = BNX_DEMO_CORES` o `min(4, max(1, cpus-1))`, AQE y `repartition(n)` acotado a `2N`; driver `BNX_DEMO_MEM` (4g).
  Monitoreo de CPU/memoria en el log (`TABLA DE TIEMPOS` y linea `CPU: promedio ...`; `BNX_MONITOR=0` lo apaga, `BNX_MONITOR_INTERVALO` s).
- Simulacion en Linux RHEL 8 desde una Mac (Podman): ver el README del portal (`tools/linux/simular_en_linux.sh`).
- Si sale `No module named 'pandas'` (módulos del banco que lo importan): `.venv/bin/python -c "import pandas, sys; print(sys.executable)"`,
  `ls .venv/.bnx_setup_ok` (si no existe, setup.sh no terminó) y `bash setup.sh`.
'''

_CFG_EXAMPLE = '''{
  "previous_path": "data/datapull",
  "spark": {
    "master": "local[*]",
    "hive": true,
    "conf": {
      "spark.sql.shuffle.partitions": "16"
    }
  },
  "sources": {
    "pivote": {
      "table_name": "pivote",
      "pivot": true,
      "query": "SELECT * FROM mi_base.tabla_pivote WHERE fecha >= '2024-01-01'",
      "limit": 100000
    },
    "data_pull": {
      "table_name": "data_pull",
      "query": "SELECT * FROM mi_base.mi_tabla WHERE fecha >= '2024-01-01'",
      "limit": 100000
    }
  }
}
'''
# mex_lib_cs — FACHADA (agregador) de las mex-lib del banco. El codigo del banco hace
#   from mex_lib_cs import Extract, GroupBy, GeneratePivot, ...
# pero 'mex_lib_cs' nunca se entrego como paquete: es una capa que re-exporta las
# clases de las mex-lib*. La escribimos nosotros (NO es codigo del banco), por eso
# va EMBEBIDA en el generador y sale en TODOS los entornos (ligero, completo y
# rebuild) sin depender del cache de librerias del servidor.
_MEX_LIB_CS = '''# -*- coding: utf-8 -*-
"""mex_lib_cs — fachada de las librerias mex-lib* del banco (generada por BNX).

Re-exporta bajo un solo import las clases de cada libreria:

    from mex_lib_cs import (Extract, GroupBy, GeneratePivot, GenerateRatios,
        ColumnsToVector, FeaturesVectorAssembler, MissingTreatment,
        FeatureEngineering, WeeklyTFrom)

Cada clase se carga de forma independiente: si su libreria no esta instalada o esta
incompleta, ese nombre queda como un PLACEHOLDER que falla con un mensaje claro
SOLO al usarlo (instanciarlo); el import de mex_lib_cs nunca se cae por una sola
libreria. mex_lib_cs.disponibles() dice cuales cargaron.

Compatibilidad (bank_compat.py + bank_compat_report.json, junto a main.py): en DEMO/SIMULACION se registran,
ANTES de importar cada libreria, los parches del reporte (stubs que FALLAN al usarse, paquetes perezosos, alias de
modulos movidos, shims de APIs eliminadas, adaptadores de firma). En modo REAL solo con BNX_BANK_COMPAT=1.
"""
import importlib

try:
    import bank_compat as _bc
except Exception:  # paquete viejo sin bank_compat: la fachada funciona como antes
    _bc = None
if _bc is not None:
    try:
        _bc.instalar()
    except Exception:
        pass

# (nombre exportado, modulo de origen, de donde sale)
_EXPORTS = (
    ("Extract", "lib_extract", "mex-libextract"),
    ("GroupBy", "lib_group_by", "mex-libgroupby"),
    ("GeneratePivot", "lib_generate_pivot", "mex-libgeneratepivot"),
    ("GenerateRatios", "lib_generate_ratios", "mex-libgenerateratios"),
    ("ColumnsToVector", "lib_columns2_vector", "mex-libcolumns2vector"),
    ("FeaturesVectorAssembler", "lib_vector_assembler", "mex-libvectorassembler"),
    ("MissingTreatment", "lib_missing_treatment", "mex-libmissingtreatment"),
    ("FeatureEngineering", "lib_feature_engineering", "mex-libfeatureengineering"),
    ("WeeklyTFrom", "toolbox.weeks", "toolbox (modulo de PYTHONPATH / bank_pkg)"),
)


def _placeholder(nombre, modulo, origen, error):
    if _bc is not None:
        try:
            return _bc.placeholder(nombre, modulo, origen, error)
        except Exception:
            pass
    msg = ("mex_lib_cs.%s no esta disponible: no se pudo importar '%s' (%s). %s: %s"
           % (nombre, modulo, origen, type(error).__name__, error))

    class _Faltante(object):
        __bnx_missing__ = True

        def __init__(self, *args, **kwargs):
            raise ImportError(msg)

    _Faltante.__name__ = nombre
    _Faltante.__qualname__ = nombre
    return _Faltante


def _cargar(nombre, modulo, origen):
    try:
        obj = getattr(importlib.import_module(modulo), nombre)
    except Exception as e:  # modulo ausente, incompleto o con dependencia faltante
        return _placeholder(nombre, modulo, origen, e)
    if _bc is not None:
        try:
            obj = _bc.adaptar_firma(nombre, obj)
        except Exception:
            pass
    return obj


for _nombre, _modulo, _origen in _EXPORTS:
    globals()[_nombre] = _cargar(_nombre, _modulo, _origen)

__all__ = [n for n, _m, _o in _EXPORTS]


def disponibles():
    """{nombre: True/False} segun si la clase cargo de su libreria real."""
    return dict((n, not getattr(globals()[n], "__bnx_missing__", False)) for n in __all__)
'''


# check_env.py — verifica que TODAS las librerias que importa el codigo esten
# instaladas en el venv. Lo corren run.sh/setup.sh tras montar, y el usuario lo
# puede correr a mano:  python check_env.py
_CHECK_ENV = '''#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""check_env.py - Verificador de dependencias del Framework MLOps v2.

Escanea TODOS los imports de primer nivel del codigo del paquete
(framework_mlops_v2/, main.py) y comprueba que cada modulo se pueda importar en
este entorno virtual. Reporta lo que FALTA, separando:
  - stack open source (pandas/numpy/pyspark/...) -> deberia venir de vendor/ o pip
  - librerias internas del banco (mex-lib*/toolbox/...) -> vendor/bank/ o Artifactory

Uso:  python check_env.py          (sale con codigo !=0 si falta algo)
      python check_env.py --quiet  (solo imprime el resumen final)
Es SOLO lectura: no instala nada.
"""
import ast
import glob
import importlib.util
import os
import sys
# Modulos de PYTHONPATH del banco (toolbox, bnmxverse, utils): main.py los agrega
# al path desde ./bank_pkg; aqui igual, para no reportarlos como faltantes.
_HERE = os.path.dirname(os.path.abspath(__file__))
_BS = os.path.join(_HERE, "bank_src")
if os.path.isdir(_BS) and _BS not in sys.path:
    # con modulos sueltos va al final (no tapa al stdlib); solo paquetes: primero (manda lo subido)
    if any(f.endswith(".py") and f != "main.py" for f in os.listdir(_BS)):
        sys.path.append(_BS)
    else:
        sys.path.insert(0, _BS)
for _cand in (os.path.join(_HERE, "bank_pkg"), os.path.join(_HERE, "vendor", "bank", "pkgcode"), _HERE):
    if os.path.isdir(_cand) and _cand not in sys.path:
        sys.path.insert(0, _cand)

# Modulos del stack open source que el framework usa (deben estar instalados).
_STACK = {
    "pandas", "numpy", "pyspark", "py4j", "pytest", "chispa", "sklearn",
    "scikit_learn", "xgboost", "lightgbm", "scipy", "dateutil", "pytz",
    # deps del stack del banco que ahora SI van empaquetadas en vendor/bank:
    "cytoolz", "toolz", "unidecode", "joblib", "cloudpickle", "six",
}
# Prefijos de librerias internas del banco (para clasificar lo que falta).
_BANK_PREFIXES = ("lib_", "mex", "toolbox", "bnmxverse")

# Modulos a IGNORAR por completo en la verificacion (no se usan en el despliegue):
# no reportarlos como faltantes aunque el codigo los importe.
_IGNORAR = {"modeling_tools", "smtplib"}

# stdlib: si el modulo se resuelve y vive bajo la lib estandar, no es dependencia
# externa. Usamos sys.stdlib_module_names cuando existe (3.10+); si no, heuristica.
_STDLIB = set(getattr(sys, "stdlib_module_names", set()))


def _project_root():
    return os.path.dirname(os.path.abspath(__file__))


def _iter_py_files():
    root = _project_root()
    targets = [os.path.join(root, "main.py"),
               os.path.join(root, "framework_mlops_v2"),
               os.path.join(root, "bank_src")]   # modulos de apoyo subidos al portal
    for t in targets:
        if os.path.isfile(t) and t.endswith(".py"):
            yield t
        elif os.path.isdir(t):
            for dp, dn, fns in os.walk(t):
                # No entrar a basura de macOS ni a carpetas sin permiso.
                dn[:] = [d for d in dn if d not in ("__MACOSX", "__pycache__")]
                for fn in fns:
                    if fn.endswith(".py") and not fn.startswith("._"):
                        yield os.path.join(dp, fn)


def _top_level_imports(descartar=True):
    """Modulos de primer nivel importados por el codigo (sin relativos)."""
    mods = set()
    for path in _iter_py_files():
        try:
            with open(path, "r", encoding="utf-8") as fh:
                tree = ast.parse(fh.read(), filename=path)
        except Exception:
            continue
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for a in node.names:
                    mods.add(a.name.split(".")[0])
            elif isinstance(node, ast.ImportFrom):
                if node.level and node.level > 0:
                    continue  # relativo (del propio paquete)
                if node.module:
                    mods.add(node.module.split(".")[0])
    # El propio paquete y sus submodulos internos NO son dependencias externas.
    # (aggregates/datapull/libs/utils/jobs/settings son carpetas del propio
    # codigo del banco o del paquete generado, no librerias a instalar.)
    for interno in () if not descartar else ("framework_mlops_v2", "framework_mlops_metrics",
                    "aggregates", "datapull", "data_pull", "libs", "utils",
                    "jobs", "settings", "static", "core", "features",
                    "scoring", "monitoring"):
        mods.discard(interno)
    return mods


def _is_stdlib(mod):
    if mod in _STDLIB:
        return True
    spec = None
    try:
        spec = importlib.util.find_spec(mod)
    except Exception:
        return False
    if spec is None or not getattr(spec, "origin", None):
        return False
    origin = spec.origin
    if origin in ("built-in", "frozen"):
        return True
    std = os.path.dirname(os.__file__)
    return os.path.abspath(origin).startswith(os.path.abspath(std)) and "site-packages" not in origin


def _can_import(mod):
    try:
        return importlib.util.find_spec(mod) is not None
    except Exception:
        return False


def _classify(mod):
    low = mod.lower()
    if any(low.startswith(p) for p in _BANK_PREFIXES):
        return "banco"
    if mod in _STACK:
        return "stack"
    return "otro"


def _es_error_openmp(txt):
    return "libomp" in txt or "OpenMP" in txt or "XGBoost Library" in txt or "libgomp" in txt


def _pista_openmp():
    """Pista EXACTA por sistema operativo para que xgboost cargue (falta OpenMP)."""
    import platform
    so = platform.system()
    if so == "Darwin":
        pista = " -> en Mac instala OpenMP:  brew install libomp"
        for base in glob.glob(os.path.join(sys.prefix, "lib", "python*", "site-packages")) + \\
                    glob.glob(os.path.join(sys.prefix, "lib", "site-packages")):
            for pat in ("sklearn/.dylibs/libomp.dylib", "torch/lib/libomp*.dylib",
                        "*/.dylibs/libomp*.dylib"):
                hits = glob.glob(os.path.join(base, pat))
                if hits:
                    return (pista + "\\n     o usa la libomp de scikit-learn ya instalada (sin brew):"
                            "\\n       export DYLD_LIBRARY_PATH=%s:$DYLD_LIBRARY_PATH"
                            "\\n     (bash run.sh y setup.sh ya lo hacen solos)" % os.path.dirname(hits[0]))
        return pista
    if so == "Windows":
        return " -> instala Microsoft Visual C++ Redistributable (vcomp140.dll)"
    return " -> instala libgomp del sistema:  yum install libgomp  |  apt-get install libgomp1"


def _probar_xgboost():
    """Intenta importar xgboost/lightgbm de verdad (find_spec no detecta una libreria
    nativa rota). Devuelve '' si cargan o no estan instalados; si no, el mensaje con
    la pista por SO."""
    for lib in ("xgboost", "lightgbm"):
        if not _can_import(lib):
            continue
        try:
            importlib.import_module(lib)
        except Exception as e:
            txt = str(e)
            primera = txt.strip().splitlines()[0] if txt.strip() else type(e).__name__
            return "%s: %s: %s%s" % (lib, type(e).__name__, primera,
                                     _pista_openmp() if _es_error_openmp(txt) else "")
    return ""


os.environ["BNX_CHECK_ENV"] = "1"    # bank_compat: importar los jobs aqui no registra parches como si fuera una corrida
def _resumen_compat():
    """Resumen OK/PARCHEABLE/BLOQUEADO de las librerias del banco (bank_compat_report.json) si el paquete lo trae."""
    try:
        sys.path.insert(0, _project_root())
        import bank_compat
        rep = bank_compat.cargar_reporte(os.path.join(_project_root(), "bank_compat_report.json"))
        if rep:
            print(bank_compat.resumen_texto(rep))
    except Exception:
        pass
def _probar_jobs():
    """Importa cada aggregate del paquete. Devuelve [(job, error)] de los que fallan."""
    import importlib
    import traceback
    base = os.path.join(_project_root(), "framework_mlops_v2", "aggregates")
    if not os.path.isdir(base):
        return []
    if not _can_import("pyspark"):
        return []   # paquete ligero sin PySpark: los jobs se prueban al correr en el cluster
    if _project_root() not in sys.path:
        sys.path.insert(0, _project_root())
    errores = []

    def _probar(nombre, mod):
        try:
            importlib.import_module(mod)
        except Exception as e:   # ImportError o error al cargar el modulo
            ultimo = traceback.extract_tb(e.__traceback__)[-1]
            txt = str(e)
            primera = txt.strip().splitlines()[0] if txt.strip() else ""
            pista = ""
            if _es_error_openmp(txt):
                pista = _pista_openmp()
            errores.append((nombre, "%s: %s (en %s:%s)%s" % (
                type(e).__name__, primera, os.path.basename(ultimo.filename), ultimo.lineno, pista)))

    for fn in sorted(os.listdir(base)):
        if not fn.endswith(".py") or fn in ("__init__.py", "router.py"):
            continue
        _probar(fn[:-3], "framework_mlops_v2.aggregates." + fn[:-3])
    # Jobs del banco (def run(kernel)): el Kernel de toolbox y cada job se importan de verdad.
    try:
        kernel = dict(getattr(importlib.import_module("framework_mlops_v2.aggregates.router"), "KERNEL", {}))
    except Exception:
        kernel = {}
    if kernel:
        _probar("toolbox.kernel", "toolbox.kernel")
        for nombre, ent in sorted(kernel.items()):
            _probar(nombre, ent["module"])
    return errores


def _spark_servidor():
    """Config de PySpark del servidor (.bnx_spark.env) o {} si el paquete no la usa."""
    ruta = os.path.join(_project_root(), ".bnx_spark.env")
    out = {}
    try:
        for ln in open(ruta, encoding="utf-8"):
            ln = ln.strip()
            if ln and not ln.startswith("#") and "=" in ln:
                k, v = ln.split("=", 1)
                out[k.strip()] = v.strip().strip("'")
    except OSError:
        return {}
    return out


def verificar_driver():
    """Imports que necesita el DRIVER, con el python de ESTE venv (el que run.sh le da al
    spark-submit). pandas/numpy (y pyspark si el paquete lo trae o usa el del servidor) se
    IMPORTAN de verdad; toolbox/bnmxverse/utils/mex-lib* se localizan en el path. Devuelve 0/1."""
    root = _project_root()
    print("== Verificacion de imports del DRIVER (check_env.py --driver) ==")
    print("Python del venv: %s (%s)" % (sys.executable, sys.version.split()[0]))
    modo = (os.environ.get("BNX_PYSPARK_MODE") or "").strip()
    if not modo:
        try:
            with open(os.path.join(root, "vendor", "PYSPARK_MODE"), encoding="utf-8") as fh:
                modo = fh.read().strip()
        except OSError:
            modo = ""
    con_wheel = bool(glob.glob(os.path.join(root, "vendor", "*", "pyspark-*.whl")))
    # pandas/numpy solo si el paquete los incluye (requirements.txt): ya no son obligatorias
    reales = []
    import re
    try:
        with open(os.path.join(root, "requirements.txt"), encoding="utf-8") as fh:
            _rq = [ln.strip().lower() for ln in fh if ln.strip() and not ln.lstrip().startswith("#")]
        reales = [m for m in ("pandas", "numpy") if any(re.match(m + "($|[ <>=!~;])", ln) for ln in _rq)]
    except OSError:
        reales = ["pandas", "numpy"]
    if modo in ("incluido", "servidor") or con_wheel:
        reales.append("pyspark")
    refs = _top_level_imports(descartar=False)
    banco = sorted(m for m in refs if m in ("toolbox", "bnmxverse", "utils") or m.lower().startswith(("mex", "lib_")))
    falta = []
    for m in reales:
        try:
            mod = importlib.import_module(m)
            print("  OK  %-12s %s" % (m, getattr(mod, "__version__", "")))
        except Exception as e:
            falta.append((m, "%s: %s" % (type(e).__name__, str(e).strip().splitlines()[0] if str(e).strip() else "")))
    for m in banco:
        if _can_import(m):
            print("  OK  %-12s (banco, localizado)" % m)
        else:
            falta.append((m, "no esta en bank_src/, bank_pkg/, vendor/bank/ ni instalado"))
    if "pyspark" not in reales:
        print("  --  pyspark      no se exige: paquete ligero / Spark del cluster (BNX_SPARK=cluster)")
    elif modo == "servidor":
        print("  i   pyspark      del SERVIDOR (PYSPARK_MODE=servidor)")
    if not falta:
        print("[OK] El driver puede importar todo lo necesario con %s" % sys.executable)
        return 0
    for m, err in falta:
        print("FALTA: %s (%s)" % (m, err))
    print("[FALLA] el python del venv NO puede importar %d modulo(s) que el driver necesita." % len(falta))
    print("  -> revisa vendor/OFFLINE_FALTANTES.txt, el log de pip de setup.sh y vuelve a correr: bash setup.sh")
    return 1


def main():
    if "--driver" in sys.argv:
        return verificar_driver()
    quiet = "--quiet" in sys.argv
    mods = sorted(_top_level_imports())
    faltan, ok = [], []
    for mod in mods:
        if _is_stdlib(mod) or mod in _IGNORAR:
            continue  # stdlib o modulo ignorado (no se usa en el despliegue)
        (ok if _can_import(mod) else faltan).append(mod)
    cfg = _spark_servidor()
    if cfg:
        print("[i] PySpark del SERVIDOR: Spark %s en %s (config .bnx_spark.env)" % (cfg.get("BNX_SPARK_VERSION") or "?", cfg.get("SPARK_HOME")))
        if "pyspark" in faltan:
            print("[!] pyspark no se puede importar con la ruta guardada: revisa .bnx_spark.env o corre bash setup.sh --reconfigurar-spark")
    # Paquete LIGERO: PySpark no viene a proposito (se usa el del cluster). No es un faltante.
    if "pyspark" in faltan and not cfg and not glob.glob(os.path.join(_project_root(), "vendor", "*", "pyspark-*.whl")):
        faltan.remove("pyspark")
        print("[i] PySpark no esta en este entorno: paquete LIGERO (normal). Corre con el Spark "
              "del cluster:  BNX_SPARK=cluster bash run.sh ...")

    if not quiet:
        print("== Verificacion de dependencias (check_env.py) ==")
        print("Python:", sys.version.split()[0], "| venv:", sys.prefix)
        print("Instaladas OK (%d): %s" % (len(ok), ", ".join(ok) or "-"))
        _resumen_compat()

    # Import REAL de los jobs: detecta faltantes INDIRECTOS (un modulo del banco que
    # a su vez importa otro que no esta, p.ej. bnmxverse -> mex_lib_cs, o
    # 'utils.emails_full' tapado por otro 'utils'). El chequeo de arriba solo ve
    # los imports de primer nivel.
    errores_jobs = _probar_jobs()
    # xgboost instalado pero con la libreria nativa rota (falta OpenMP): se avisa aunque
    # ningun job se pudo probar (paquete ligero sin PySpark).
    err_xgb = _probar_xgboost()
    if err_xgb and not any(("xgboost" in e.lower() or "lightgbm" in e.lower()) for _, e in errores_jobs):
        errores_jobs.append(("xgboost", err_xgb))
    if not faltan and not errores_jobs:
        print("\\n[OK] No falta ninguna libreria. El entorno esta completo.")
        return 0
    if errores_jobs:
        print("\\n[FALLA al importar %d job(s) del REGISTRY]:" % len(errores_jobs))
        for nombre, err in errores_jobs:
            print("  - %s: %s" % (nombre, err))
    if not faltan:
        return 1

    # Agrupar lo que falta por categoria para un mensaje accionable.
    por_cat = {"stack": [], "banco": [], "otro": []}
    for mod in faltan:
        por_cat[_classify(mod)].append(mod)

    print("\\n[FALTAN %d libreria(s)]:" % len(faltan))
    if por_cat["stack"]:
        print("  - Stack open source:", ", ".join(por_cat["stack"]))
        print("    -> Instala desde vendor/ (ambiente completo) o: pip install -r requirements.txt")
    if por_cat["banco"]:
        print("  - Librerias INTERNAS del banco:", ", ".join(por_cat["banco"]))
        print("    -> Offline: vendor/bank/ (pip --no-index) y ./bank_pkg en PYTHONPATH.")
        print("       Online:  pip install -r requirements-bank.txt --index-url <artifactory>")
        print("       Si alguna es 'INCOMPLETA' (ver requirements-bank.txt), pide la version completa al banco.")
    if por_cat["otro"]:
        print("  - Otras:", ", ".join(por_cat["otro"]))
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
'''


_SETUP = '''from setuptools import setup, find_packages

setup(
    name="framework_mlops_v2",
    version="2.0.0",
    description="Framework MLOps v2 (mejorado) — feature engineering para scoring",
    packages=find_packages(exclude=["tests*"]),
    python_requires=">=3.9",
    install_requires=[
        # PySpark segun version de Python (3.5 usa distutils, roto en 3.12+).
        'pyspark>=3.5,<3.6 ; python_version < "3.12"',
        'pyspark>=4.0,<4.1 ; python_version >= "3.12" and python_version < "3.14"',
        'pyspark>=4.1,<4.2 ; python_version >= "3.14"',
@@PANDAS_REQ@@    ],
)
'''


def _setup_py(pandas_info=None, py_target=None):
    """setup.py del framework: pandas/numpy solo si el paquete los necesita (decidir_pandas)."""
    pi = pandas_info or {}
    lineas = []
    if pi.get("pandas"):
        lineas.append('        "%s",\n' % _PANDAS_PIN)
    if pi.get("numpy") or pi.get("pandas"):
        lineas += ['        "%s",\n' % _n for _n in _numpy_pins(py_target)]
    return _SETUP.replace("@@PANDAS_REQ@@", "".join(lineas))



def _safe_name(filename):
    """Nombre de modulo/fuente valido a partir de un nombre de archivo."""
    base = _re.sub(r"\.(py|txt)$", "", (filename or "").strip(), flags=_re.I)
    base = base.rsplit("/", 1)[-1].rsplit("\\", 1)[-1]
    base = _re.sub(r"[^0-9A-Za-z_]", "_", base).strip("_").lower()
    if not base:
        base = "fuente"
    if base[0].isdigit():
        base = "f_" + base
    return base


def _class_name(source):
    """CamelCase + 'Aggregate' a partir del nombre de la fuente."""
    parts = [p for p in source.split("_") if p]
    return "".join(p.capitalize() for p in parts) + "Aggregate"


def _indent(code, spaces):
    pad = " " * spaces
    return "\n".join((pad + ln if ln.strip() else ln) for ln in code.split("\n"))


def _as_comment_block(code):
    """Convierte un bloque de codigo en lineas comentadas con '# '. Seguro frente
    a docstrings con triple comilla o comillas internas (no es un string literal,
    asi que nunca cierra prematuramente ni rompe la sintaxis del archivo)."""
    lines = (code or "").strip().split("\n")
    return "\n".join((f"# {ln}" if ln.strip() else "#") for ln in lines)


# Modulos que NO estaran disponibles en el despliegue (no se usan / no se
# empaquetan). Sus imports se neutralizan con try/except para que el archivo NO
# rompa al importar; si se usan en runtime dan un error claro, no al cargar.
_MODULOS_AUSENTES = ("modeling_tools", "libs")


def _neutralize_missing_imports(imports_txt):
    """Envuelve en try/except ImportError los imports de modulos que sabemos que
    NO estaran (modeling_tools, etc.), para que el archivo importe sin romper. El
    symbolo importado queda como None (si se usa en runtime, falla claro ahi, no
    al cargar el modulo). Devuelve el bloque de imports ya neutralizado."""
    out = []
    for ln in imports_txt.split("\n"):
        s = ln.strip()
        top = s.split()[1].split(".")[0] if s.startswith(("import ", "from ")) and len(s.split()) > 1 else ""
        if top in _MODULOS_AUSENTES:
            # Nombres que define este import (para dejarlos como None si falla).
            names = []
            if s.startswith("from ") and " import " in s:
                tail = s.split(" import ", 1)[1]
                names = [p.strip().split(" as ")[-1].strip()
                         for p in tail.split(",") if p.strip() and p.strip() != "*"]
            elif s.startswith("import "):
                names = [s.split()[1].split(".")[0].split(" as ")[-1].strip()]
            out.append("try:")
            out.append("    " + s)
            out.append("except ImportError:  # BNX: modulo no disponible en el despliegue")
            if names:
                out.append("    " + " = ".join(names) + " = None")
            else:
                out.append("    pass")
        else:
            out.append(ln)
    return "\n".join(out)


def _hoist_module_imports(code):
    """Separa los imports de NIVEL SUPERIOR del resto del codigo. Devuelve
    (imports_txt, resto_txt). CLAVE para 'from X import *': Python solo lo permite
    a nivel de modulo, nunca dentro de un metodo/funcion. Al envolver el PySpark en
    _aggregate_df, los imports deben subir al tope del archivo (fuera de la clase).
    Solo mueve imports que esten SIN indentar (nivel superior del codigo generado);
    los imports dentro de funciones del propio codigo se dejan donde esten salvo el
    'import *', que SIEMPRE sube (si no, es SyntaxError)."""
    imports, rest = [], []
    for ln in (code or "").split("\n"):
        stripped = ln.strip()
        is_top_import = (
            (ln[:1] not in (" ", "\t"))  # sin indentar
            and (stripped.startswith("import ") or stripped.startswith("from ")))
        # 'import *' en cualquier nivel DEBE ir al modulo (si no, SyntaxError).
        is_star_import = stripped.startswith("from ") and stripped.endswith("import *")
        if is_top_import or is_star_import:
            imp = stripped
            if imp not in imports:
                imports.append(imp)
        else:
            rest.append(ln)
    return "\n".join(imports), "\n".join(rest)


def _is_pyspark_source(code):
    """True si el archivo YA es PySpark (importa pyspark). Esos archivos (p.ej. los
    job.py del framework del banco) NO deben pasar por el conversor pandas->PySpark:
    reescribe el codigo (pierde comentarios/formato, mete 'pass' en docstrings) y,
    con librerias ML (xgboost), sustituye logica por un esqueleto MLlib."""
    return _re.search(r"^\s*(from\s+pyspark[\w.]*\s+import|import\s+pyspark)",
                      code or "", _re.M) is not None


def _usa_pandas(code):
    """True si el archivo importa pandas (es codigo a convertir pandas->PySpark)."""
    return _re.search(r"^\s*(import\s+pandas\b|from\s+pandas[\w.]*\s+import)",
                      code or "", _re.M) is not None


def _demo_files():
    """{'bnx_demo/<modulo>.py': codigo}: el paquete del DEMO de los jobs del banco (src/mlops_demo/)."""
    d = os.path.join(os.path.dirname(os.path.abspath(__file__)), "mlops_demo")
    out = {}
    if os.path.isdir(d):
        for f in sorted(os.listdir(d)):
            if f.endswith(".py"):
                with open(os.path.join(d, f), "r", encoding="utf-8") as fh:
                    out["bnx_demo/" + f] = fh.read()
    return out
def _es_job_kernel(code):
    """True si el archivo es un job del framework del banco: def run(kernel...)."""
    return _re.search(r"^def\s+run\s*\(\s*kernel\b", code or "", _re.M) is not None


def _norm_fuente(n):
    return _re.sub(r"\.(py|txt)$", "", os.path.basename(str(n or "")).strip(), flags=_re.I).lower()


def _en_registry(raw_name, src, registry):
    """El archivo esta en la lista de jobs a registrar (por nombre de archivo o modulo)."""
    sel = {_norm_fuente(r) for r in registry or []}
    # Con rutas (carpeta subida): dos 'job.py' distintos se distinguen por su ruta completa.
    rutas = {"/".join(_partes_ruta(r)).lower() for r in registry or [] if len(_partes_ruta(r)) > 1}
    if rutas and len(_partes_ruta(raw_name)) > 1:
        return "/".join(_partes_ruta(raw_name)).lower() in rutas
    return _norm_fuente(raw_name) in sel or str(src).lower() in sel


def _apoyo_name(raw_name):
    """Nombre de archivo para bank_src/: el original si es un modulo Python valido."""
    base = os.path.basename(str(raw_name or "modulo.py")).strip()
    if base.lower().endswith(".txt"):
        base = base[:-4]
    if not base.lower().endswith(".py"):
        base += ".py"
    stem = base[:-3]
    if not _re.fullmatch(r"[A-Za-z_]\w*", stem):
        stem = _safe_name(base)
    return stem + ".py"


_SUBMOD_RE = _re.compile(
    r"^\s*(?:from\s+([A-Za-z_]\w*)\.([A-Za-z_]\w*)(?:\.[\w.]+)?\s+import\b"
    r"|import\s+([A-Za-z_]\w*)\.([A-Za-z_]\w*))", _re.M)
_NO_PAQUETE_BANCO = {"pyspark", "pandas", "numpy", "framework_mlops_v2", "sklearn",
                     "xgboost", "scipy", "dateutil", "concurrent", "importlib"}


def _imports_paquete_modulo(code):
    """[(paquete, modulo)] de los imports REALES 'paquete.modulo' (AST: ignora los que
    estan dentro de docstrings/comentarios). Si el archivo no parsea, por regex."""
    try:
        tree = _ast_mod.parse(code or "")
    except SyntaxError:
        return [((m.group(1), m.group(2)) if m.group(1) else (m.group(3), m.group(4)))
                for m in _SUBMOD_RE.finditer(code or "")]
    res = []
    for n in _ast_mod.walk(tree):
        nombres = []
        if isinstance(n, _ast_mod.ImportFrom) and n.module and not n.level:
            nombres = [n.module]
        elif isinstance(n, _ast_mod.Import):
            nombres = [a.name for a in n.names]
        for nm in nombres:
            partes = nm.split(".")
            if len(partes) >= 2:
                res.append((partes[0], partes[1]))
    return res


def _paquetes_importados(sources):
    """{modulo_lower: (paquete, modulo, [importadores])} de los 'paquete.modulo' que
    importan los archivos subidos (toolbox.kernel, utils.emails_full, ...).
    Si un archivo subido se llama como ese modulo, ES de ese paquete (apoyo)."""
    out = {}
    for it in sources or []:
        quien = os.path.basename(str(it.get("name") or ""))
        for pkg, mod in _imports_paquete_modulo(it.get("code") or ""):
            if pkg in _NO_PAQUETE_BANCO or _is_stdlib_module(pkg):
                continue
            ent = out.setdefault(mod.lower(), (pkg, mod, []))
            if quien not in ent[2]:
                ent[2].append(quien)
    return out


def _nombre_con_ruta(item):
    """Nombre de una fuente subida CON su ruta relativa si la trae: la UI manda la carpeta como
    'name' = webkitRelativePath; otros clientes mandan 'path' / 'relative_path' / 'webkitRelativePath'
    y en 'name' solo el archivo. Se prefiere el campo que lleva carpetas (los nombres por ruta,
    liabilities_pivot / rps_target..., y la clasificacion de main.py/toolbox dependen de la ruta)."""
    nombre = item.get("name") or "fuente.py"
    for k in ("path", "webkitRelativePath", "relative_path", "relativePath"):
        v = item.get(k)
        if isinstance(v, str) and len(_partes_ruta(v)) > len(_partes_ruta(nombre)):
            return v
    return nombre
def _partes_ruta(raw_name):
    """['dir', 'sub', 'archivo.py'] de un nombre subido (webkitRelativePath o solo el nombre)."""
    p = str(raw_name or "").replace("\\", "/")
    return [x for x in p.split("/") if x and x != "."]


_EXT_SETTINGS = (".json", ".yaml", ".yml", ".cfg", ".ini")
def _ruta_settings(raw_name):
    """'rps/pivot.json' si raw_name es un archivo de config (json/yaml/cfg/ini) bajo una carpeta
    'settings' (bin/settings/rps/pivot.json); None si no. Sin '..' ni rutas absolutas."""
    partes = _partes_ruta(raw_name)
    if len(partes) < 2 or not partes[-1].lower().endswith(_EXT_SETTINGS) or ".." in partes:
        return None
    dirs = [d.lower() for d in partes[:-1]]
    if "settings" not in dirs:
        return None
    rel = partes[dirs.index("settings") + 1:]
    return "/".join(rel) if rel else None
# Recursos NO Python del proyecto del banco que el codigo lee en tiempo de ejecucion
# (modelos .xgb/.pkl, bin/opt/profile.sh, tablas...). Viajan EXACTOS en bank_src/ con la ruta relativa a bin/
# (bank_src/static/modelo.xgb) y el runner apunta BIN_PATH a bank_src/. Son datos INTERNOS del banco:
# solo existen en el paquete generado.
EXT_RECURSOS = (".xgb", ".pkl", ".pickle", ".joblib", ".bin", ".model", ".json", ".txt", ".csv", ".parquet",
                ".sh", ".yaml", ".yml", ".cfg", ".ini", ".npy", ".npz", ".onnx", ".pmml")
_DIRS_NO_RECURSO = ("settings", "jobs", "toolbox", "utils", "bnmxverse", "logs", "__pycache__", "tests", ".git",
                    "node_modules")
_BIN_PREFIX = "bnx-b64:"
try:
    MAX_RECURSO_MB = float(os.environ.get("BNX_MAX_RECURSO_MB") or 100)
except ValueError:
    MAX_RECURSO_MB = 100.0


def _ruta_recurso(raw_name):
    """Ruta relativa a bin/ ('static/rpsv2_all_versions.xgb', 'opt/profile.sh') si raw_name es un RECURSO no Python
    del proyecto (bin/static/**, bin/opt/**, cualquier bin/<dato>/**); None si no (codigo, settings, otra cosa)."""
    partes = _partes_ruta(raw_name)
    if len(partes) < 2 or ".." in partes or partes[-1].lower().endswith(".py") \
            or not partes[-1].lower().endswith(EXT_RECURSOS):
        return None
    dirs = [d.lower() for d in partes[:-1]]
    if "settings" in dirs:
        return None
    ini = None
    for i, d in enumerate(dirs):
        if d == "bin":
            ini = i + 1                      # la ultima carpeta 'bin' manda
    if ini is None:                          # carpeta subida sin 'bin/': desde static/ u opt/
        for i, d in enumerate(dirs):
            if d in ("static", "opt"):
                ini = i
                break
    if ini is None or ini >= len(partes) - 1:
        return None
    rel = partes[ini:]
    if rel[0].lower() in _DIRS_NO_RECURSO or any(x.lower() in ("__pycache__", ".git") for x in rel):
        return None
    return "/".join(rel)


def recurso_a_contenido(item):
    """Contenido para guardar en code_files: texto tal cual o 'bnx-b64:<base64>' si es binario."""
    if item.get("b64"):
        return _BIN_PREFIX + str(item["b64"])
    return item.get("code") or ""


def contenido_a_bytes(content):
    """Valor a escribir en el ZIP para un valor de code_files (texto, o bytes si es un binario codificado)."""
    if isinstance(content, str) and content.startswith(_BIN_PREFIX):
        import base64
        return base64.b64decode(content[len(_BIN_PREFIX):])
    return content


def _es_main_banco(raw_name, code):
    """main.py del banco (class Launcher que arma el Kernel de toolbox): NO es un job."""
    partes = _partes_ruta(raw_name)
    return (bool(partes) and partes[-1].lower() == "main.py"
            and _re.search(r"\btoolbox\.kernel\b|\bKernel\s*\(", code or "") is not None)


def _ruta_paquete_banco(raw_name, dirs_init):
    """Ruta relativa dentro de bank_src/ si el archivo vive bajo toolbox/, bnmxverse/,
    utils/ (o un paquete con __init__.py subido): 'toolbox/weeks.py'. None si no."""
    partes = _partes_ruta(raw_name)
    dirs = partes[:-1]
    for i, d in enumerate(dirs):
        if d in _BANK_PATH_MODULES and _re.fullmatch(r"[A-Za-z_]\w*", d):
            return "/".join(partes[i:])
    for i, d in enumerate(dirs):
        if d.lower() != "jobs" and "/".join(dirs[:i + 1]).lower() in dirs_init \
                and all(_re.fullmatch(r"[A-Za-z_]\w*", x) for x in dirs[i:]):
            return "/".join(partes[i:])
    return None


def _kernel_ids(raw_name):
    """Identidad de un job de kernel segun su ruta: (nombre, modulo, model, job).
    jobs/rps/datapull/job.py -> ('rps_datapull', 'jobs.rps.datapull.job', 'rps', 'datapull').
    Sin carpeta 'jobs' en la ruta (archivo suelto) devuelve None: se usa el nombre del archivo."""
    partes = _partes_ruta(raw_name)
    dirs = [d.lower() for d in partes[:-1]]
    if "jobs" not in dirs:
        return None
    sub = [_safe_name(d) for d in dirs[dirs.index("jobs") + 1:]]
    stem = _safe_name(partes[-1])
    if not sub:
        return None
    if stem == "job":
        modulo = "jobs." + ".".join(sub) + ".job"
        nombre = "_".join(sub)
        model, job = (sub[0], sub[1]) if len(sub) >= 2 else (sub[0], sub[0])
    else:
        modulo = "jobs." + ".".join(sub) + "." + stem
        nombre = "_".join(sub + [stem])
        model, job = sub[0], (sub[1] if len(sub) >= 2 else stem)
    return nombre, modulo, model, job


def _init_dirs(sources):
    """Carpetas (minusculas) donde se subio un __init__.py: son paquetes del banco."""
    out = set()
    for it in sources or []:
        partes = _partes_ruta(it.get("name"))
        if partes and partes[-1].lower() == "__init__.py" and len(partes) > 1:
            out.add("/".join(partes[:-1]).lower())
    return out


def _hoist_imports_ast(code):
    """Como _hoist_module_imports pero con el AST: sube los imports de NIVEL
    SUPERIOR completos (incluye imports de varias lineas con parentesis o '\\')
    sin tocar el resto del texto (comentarios y formato intactos)."""
    import ast as _ast
    try:
        tree = _ast.parse(code)
    except SyntaxError:
        return _hoist_module_imports(code)
    lines = code.split("\n")
    drop, imports = set(), []
    for node in tree.body:
        if isinstance(node, (_ast.Import, _ast.ImportFrom)):
            end = getattr(node, "end_lineno", node.lineno)
            txt = "\n".join(lines[node.lineno - 1:end]).strip()
            if txt not in imports:
                imports.append(txt)
            drop.update(range(node.lineno - 1, end))
    rest = [ln for i, ln in enumerate(lines) if i not in drop]
    return "\n".join(imports), "\n".join(rest)


def _aggregate_from_pyspark(source, pyspark_code, original_pandas, verbatim=False):
    """Envuelve PySpark convertido en el contrato del framework v2.

    El codigo convertido se coloca en `_aggregate_df(self, df)`. El df de entrada
    ya viene leido por BaseAggregate; se expone como `df` y como `spark`/`F` para
    que el PySpark generado (que usa spark.read.* / F.*) siga funcionando. Las
    lecturas se reescriben para partir del df inyectado cuando aplica."""
    cls = _class_name(source)
    # Cuerpo: el PySpark convertido, indentado dentro del metodo. Nota honesta:
    # si el codigo lee de rutas propias (spark.read...), se respeta tal cual; el
    # df inyectado queda disponible como punto de partida alternativo.
    body = pyspark_code.strip() or "df_out = df"
    # Subir los imports al nivel de MODULO. Imprescindible para 'from X import *'
    # (Python prohibe import * dentro de metodos -> SyntaxError). Tambien deja el
    # metodo mas limpio.
    hoisted, body = (_hoist_imports_ast(body) if verbatim else _hoist_module_imports(body))
    # Neutralizar imports de modulos que NO estaran (modeling_tools, etc.): el
    # archivo debe importar sin romper (try/except ImportError).
    hoisted = _neutralize_missing_imports(hoisted)
    body = body.strip() or "df_out = df"
    # Heuristica: si el codigo no define df_out ni retorna, devolvemos la ultima
    # variable *_df o el df de entrada.
    has_out = _re.search(r"\bdf_out\b", body) is not None
    tail = "" if has_out else "\n# BNX: no se detecto 'df_out'; se devuelve el df de entrada.\ndf_out = df"
    extra_imports = ("\n" + hoisted + "\n") if hoisted.strip() else "\n"
    if verbatim:
        footer = ("# --- BNX: el archivo original (PySpark o Python sin pandas) va arriba COMPLETO\n"
                  "# y sin conversion (comentarios, formato y logica intactos). Solo se subieron\n"
                  "# los imports al nivel de modulo y se indento dentro de _aggregate_df.\n"
                  "# Si es un MODULO DE APOYO (no un job), desmarcalo de 'Registrar como job'\n"
                  "# en el portal: se copia exacto a bank_src/ sin esta envoltura.")
    else:
        footer = ("# --- Codigo de negocio ORIGINAL (pandas), como referencia ---\n"
                  "# Se guarda COMENTADO (no como string literal) para que un docstring con triple\n"
                  "# comilla o comillas internas en el original no rompa la sintaxis de este archivo.\n"
                  + _as_comment_block(original_pandas))
    return f'''# framework_mlops_v2/aggregates/{source}.py
"""Fuente '{source}': generada por BNX desde el Python del negocio.
Convertida a PySpark y envuelta en el contrato del framework v2.
Revisa los comentarios '# TODO py2spark' donde la conversion no fue 1:1."""
from pyspark.sql import functions as F
from ..core.base_aggregate import BaseAggregate
{extra_imports}

class {cls}(BaseAggregate):
    """Agregacion de la fuente '{source}'. La logica proviene del codigo de
    negocio original (pandas) convertido a PySpark por BNX."""

    def _aggregate_df(self, df):
        spark = self.sqlContext            # alias para el PySpark generado
{_indent(body, 8)}{_indent(tail, 8)}
        return df_out


{footer}
'''


def _router_from_sources(sources, kernel=None, alias=None):
    """Genera el router con todas las fuentes del usuario registradas.

    El registro es PEREZOSO: cada job se importa al usarse. Asi una libreria nativa que
    no carga en esta maquina (p.ej. xgboost sin libomp en Mac) solo afecta a los jobs
    que la usan, no a todo el framework, y el error dice como resolverlo.

    kernel: jobs del banco (def run(kernel)): [{"name","module","model","job"}]. No son
    aggregates: van en KERNEL y los ejecuta main.py con toolbox.kernel.Kernel.
    alias: {nombre_viejo: nombre_nuevo} para orden.json/--source hechos con los nombres
    anteriores (job, job_2...)."""
    registry = "\n".join(
        f'    "{s}": (".{s}", "{_class_name(s)}"),' for s in sources)
    if kernel:
        registry += "\n" + "\n".join(
            f'    "{k["name"]}": ("{k["module"]}", "run", "kernel", "{k["model"]}/{k["job"]}"),'
            for k in kernel)
    alias_txt = "\n".join(f'    "{a}": "{b}",' for a, b in sorted((alias or {}).items()))
    return f'''# framework_mlops_v2/aggregates/router.py
"""Router de agregaciones generado por BNX. Una entrada por fuente del negocio.
Los jobs se importan al usarse (registro perezoso).
Entradas de 2 elementos = aggregate (clase). Entradas con "kernel" = job del banco
(def run(kernel)): NO es un aggregate; lo ejecuta main.py con toolbox.kernel.Kernel."""
import importlib
import platform
from collections.abc import Mapping

_FUENTES = {{
{registry}
}}

# nombre viejo (job, job_2...) -> nombre por ruta (rps_datapull...)
ALIAS = {{
{alias_txt}
}}

_AGGREGATES = {{k: v for k, v in _FUENTES.items() if len(v) == 2}}
KERNEL = {{k: {{"module": v[0], "model": v[3].split("/")[0], "job": v[3].split("/")[1]}}
          for k, v in _FUENTES.items() if len(v) == 4}}


def _ayuda_import(e):
    msg = str(e)
    if "libomp" in msg or "OpenMP" in msg or "XGBoost Library" in msg:
        if platform.system() == "Darwin":
            return "xgboost necesita OpenMP en Mac: instala 'brew install libomp' y vuelve a correr."
        if platform.system() == "Windows":
            return "xgboost necesita vcomp140.dll: instala 'Microsoft Visual C++ Redistributable'."
        return "xgboost necesita libgomp: instala el paquete del sistema (p.ej. 'yum install libgomp')."
    return "revisa que la libreria este instalada en el venv (bash setup.sh)."


class _RegistroPerezoso(Mapping):
    def __init__(self, fuentes):
        self._fuentes = dict(fuentes)
        self._cache = {{}}

    def __getitem__(self, source):
        if source not in self._fuentes:
            raise KeyError(source)
        if source not in self._cache:
            mod, cls = self._fuentes[source]
            try:
                self._cache[source] = getattr(importlib.import_module(mod, __package__), cls)
            except Exception as e:  # noqa: BLE001 - mensaje claro para el usuario
                raise ImportError("No se pudo cargar el job %r (%s): %s: %s -> %s" % (
                    source, mod, type(e).__name__, str(e).splitlines()[0] if str(e) else "",
                    _ayuda_import(e))) from e
        return self._cache[source]

    def __contains__(self, source):  # sin importar el job (Mapping lo haria via __getitem__)
        return source in self._fuentes

    def __iter__(self):
        return iter(self._fuentes)

    def __len__(self):
        return len(self._fuentes)


REGISTRY = _RegistroPerezoso(_AGGREGATES)   # solo aggregates (GroupBy)


def cargar_job_kernel(nombre):
    """Importa (al usarse) el modulo de un job del banco y devuelve el modulo (tiene run(kernel))."""
    if nombre not in KERNEL:
        raise KeyError("Job del banco no registrado: %r. Opciones: %s" % (nombre, sorted(KERNEL)))
    mod = KERNEL[nombre]["module"]
    try:
        return importlib.import_module(mod)
    except Exception as e:  # noqa: BLE001 - mensaje claro para el usuario
        raise ImportError("No se pudo cargar el job del banco %r (%s): %s: %s -> %s" % (
            nombre, mod, type(e).__name__, str(e).splitlines()[0] if str(e) else "",
            _ayuda_import(e))) from e


class GroupBy:
    def __init__(self, source, previous_path, agg_dict, sqlContext, mode="overwrite"):
        if source not in REGISTRY:
            raise KeyError("Fuente no registrada: %r. Opciones: %s" % (
                source, sorted(REGISTRY)))
        self.impl = REGISTRY[source](previous_path, agg_dict, sqlContext, mode)

    def aggregate(self):
        return self.impl.aggregate()
'''


_TEST_MONITORING = '''# tests/test_monitoring.py
"""Pruebas del monitoreo (PSI/CSI/DQC). Requiere pyspark."""
import pytest

pyspark = pytest.importorskip("pyspark")
from pyspark.sql import SparkSession
from framework_mlops_v2.monitoring.monitor_metrics import MonitorMetrics


@pytest.fixture(scope="session")
def spark():
    s = SparkSession.builder.master("local[1]").appName("mon_tests").getOrCreate()
    yield s
    s.stop()


def test_psi_cero_si_misma_distribucion(spark):
    # Poblacion actual identica a la de desarrollo -> PSI ~ 0 (estable).
    df = spark.createDataFrame([("a",)] * 50 + [("b",)] * 50, ["bin"])
    dist_dev = {"a": 0.5, "b": 0.5}
    m = MonitorMetrics()
    psi = m.psi(df, "bin", dist_dev)
    assert abs(psi) < 0.01
    assert m.interpret(psi) == "estable"


def test_psi_alto_si_cambia_distribucion(spark):
    # La actual se corrio fuerte respecto al desarrollo -> PSI alto.
    df = spark.createDataFrame([("a",)] * 95 + [("b",)] * 5, ["bin"])
    dist_dev = {"a": 0.5, "b": 0.5}
    m = MonitorMetrics()
    psi = m.psi(df, "bin", dist_dev)
    assert psi > 0.25
    assert m.interpret(psi) == "inestable"


def test_dqc_reporta_nulos(spark):
    from pyspark.sql.types import StructType, StructField, IntegerType
    schema = StructType([StructField("x", IntegerType(), True)])
    df = spark.createDataFrame([(1,), (2,), (None,), (4,)], schema)
    rep = MonitorMetrics().dqc(df, ["x"])
    assert rep["x"]["null_pct"] == 25.0
'''


def _monitoring_files(target="package"):
    """Archivos del monitoreo. target='package' -> dentro de framework_mlops_v2;
    'separate' -> como paquete independiente framework_mlops_metrics."""
    if target == "separate":
        return {
            "framework_mlops_metrics/__init__.py":
                '"""Monitoreo de modelos (PSI/CSI/DQC) — paquete separado."""\n__version__ = "2.0.0"\n',
            "framework_mlops_metrics/monitor_metrics.py":
                _MONITORING.replace("framework_mlops_v2/monitoring/monitor_metrics.py",
                                    "framework_mlops_metrics/monitor_metrics.py"),
            "tests/test_monitoring.py":
                _TEST_MONITORING.replace(
                    "framework_mlops_v2.monitoring.monitor_metrics",
                    "framework_mlops_metrics.monitor_metrics"),
            "setup.py": _SETUP_METRICS,
            "requirements.txt": "pyspark>=3.3,<4.0\npytest>=7.0\n",
            "README.md": _README_METRICS,
            "setup.sh": _SETUP_SH,
            "run.sh": _RUN_SH_METRICS,
        }
    return {
        "framework_mlops_v2/monitoring/__init__.py": "",
        "framework_mlops_v2/monitoring/monitor_metrics.py": _MONITORING,
        "tests/test_monitoring.py": _TEST_MONITORING,
    }


_SETUP_METRICS = '''from setuptools import setup, find_packages

setup(
    name="framework_mlops_metrics",
    version="2.0.0",
    description="Monitoreo de modelos (PSI/CSI/DQC) — separado del datapull",
    packages=find_packages(exclude=["tests*"]),
    python_requires=">=3.9",
    install_requires=[
        'pyspark>=3.5,<3.6 ; python_version < "3.12"',
        'pyspark>=4.0,<4.1 ; python_version >= "3.12" and python_version < "3.14"',
        'pyspark>=4.1,<4.2 ; python_version >= "3.14"',
    ],
)
'''

_README_METRICS = '''# Framework MLOps — Monitoreo (paquete separado)

Librería de monitoreo de modelos (PSI/CSI + Data Quality) extraída como paquete
independiente, igual que el `lib_mkop_metrics` del framework original. Corre en
producción, con su propio ciclo de vida, sin depender del datapull.

## Uso
```python
from framework_mlops_metrics.monitor_metrics import MonitorMetrics
m = MonitorMetrics()
psi = m.psi(current_df, "score_bin", dist_dev={"0": 0.2, "1": 0.3, "2": 0.5})
print(psi, m.interpret(psi))   # estable | revisar | inestable
```

## Correr pruebas
```bash
bash setup.sh   # una vez
bash run.sh
```
'''


def _extra_step_files(extra_steps, include_monitoring=False, monitoring_target="package"):
    """Archivos de los pasos EXTRA segun el flag (opcional). Devuelve dict.

    include_monitoring: anade el modulo de monitoreo.
    monitoring_target: 'package' (dentro del framework) o 'separate' (se maneja
        aparte, no aqui)."""
    files = {}
    if extra_steps:
        files["framework_mlops_v2/features/feature_engineering.py"] = _FEATURE_ENGINEERING
        files["framework_mlops_v2/features/vector_assembler.py"] = _VECTOR_ASSEMBLER
        files["framework_mlops_v2/scoring/__init__.py"] = ""
        files["framework_mlops_v2/scoring/scorer.py"] = _SCORING
        files["framework_mlops_v2/pipeline.py"] = _PIPELINE
    # Monitoreo DENTRO del paquete (cuando no se separa).
    if include_monitoring and monitoring_target == "package":
        files.update(_monitoring_files("package"))
    return files


def _extract_todos(code):
    """Extrae los comentarios '# TODO py2spark' de un archivo generado, con su
    numero de linea (1-based) y el texto, ademas de la linea 'Original:' que les
    sigue (el pandas que no se pudo traducir). Devuelve [{line, text, original}]."""
    out = []
    lines = code.split("\n")
    for i, ln in enumerate(lines):
        s = ln.strip()
        # Solo TODOs REALES: comentario que ARRANCA con '# TODO py2spark'. Las
        # menciones dentro de docstrings/prosa ("Revisa los # TODO py2spark...")
        # no son puntos a revisar y se ignoran.
        if not s.startswith("#"):
            continue
        body_c = s.lstrip("#").strip()
        if not body_c.startswith("TODO py2spark"):
            continue
        if True:
            # Texto del TODO (sin el '# ').
            text = body_c
            # Buscar la linea 'Original: ...' siguiente (si la hay) para citar el
            # codigo pandas original.
            original = ""
            for j in range(i + 1, min(i + 4, len(lines))):
                js = lines[j].strip().lstrip("# ").strip()
                if js.startswith("Original:"):
                    original = js[len("Original:"):].strip()
                    break
            out.append({"line": i + 1, "text": text, "original": original})
    return out


# {serie: {version_python: error}} del ultimo zip_from_files: que version no podria
# instalar offline (se muestra en el portal y va en vendor/OFFLINE_FALTANTES.txt).
ULTIMO_FALTAN_OFFLINE = {}
ULTIMO_VENDOR = {}   # {"pyspark": bool, "mb": float} del ultimo vendor empaquetado


def faltantes_entorno(offline_faltan, vendor_missing=False, bank_faltan=None):
    """Lista legible de lo que le falta al vendor/ para instalar el entorno Linux COMPLETO offline
    (deps + ciencia + banco + PySpark si va incluido). [] = completo."""
    out = []
    for _s, vs in sorted((offline_faltan or {}).items()):
        for v, e in sorted(vs.items()):
            e = str(e)
            m = _re.match(r"^(\[[a-z-]+\] )?sin wheel en el cache: (.*)$", e)
            if m:
                pref = (m.group(1) or "").strip()
                out += ["%s%s (Python %s)" % (pref + " " if pref else "", n.strip(), v)
                        for n in m.group(2).split(",") if n.strip()]
            else:
                out.append("Python %s: %s" % (v, e[:200]))
    if vendor_missing:
        out.append("pyspark + py4j (PySpark incluido)")
    out += ["%s (libreria del banco)" % b for b in (bank_faltan or [])]
    return list(dict.fromkeys(out))
def zip_from_files(code_files, sep_files=None, full_env=False, py_target="all",
                   out_path=None, plataformas=("linux",), spark_modo=None):
    """Empaqueta un ZIP a partir de dicts de archivos YA LISTOS (texto). Reusable
    para re-empaquetar tras EDITAR los archivos generados.

    code_files: {ruta_relativa: contenido} del paquete principal (framework_mlops_v2_pkg/).
    sep_files:  {ruta_relativa: contenido} del paquete separado de monitoreo (opcional).
    full_env/py_target: si full_env, agrega vendor/ offline (PySpark + deps del
    framework) segun py_target. extra_steps se infiere del paquete (si trae
    scoring/, necesita xgboost/sklearn offline).
    out_path: si se da, el ZIP se escribe DIRECTO a ese archivo en disco (no a
        memoria). CLAVE para el ambiente completo (~700 MB): en Windows/Python 3.8
        de 32 bits construirlo en un BytesIO agota el espacio de direcciones y
        rompe con 'I/O operation on closed file'. Con out_path la salida es por
        streaming a disco. En ese caso el primer valor devuelto es out_path (str),
        no los bytes.
    Devuelve (zip_bytes_o_ruta, filename, vendor_series_list)."""
    extra_steps = any("scoring/scorer.py" in p for p in (code_files or {}))
    # Modo de PySpark: 'incluido' (wheel en vendor/) | 'servidor' (usa el Spark del servidor; setup.sh
    # pregunta la ruta). Sin indicar: lo decide full_env (compatibilidad con 'ambiente completo').
    if spark_modo in ("incluido", "servidor"):
        full_env = spark_modo == "incluido"
    else:
        spark_modo = "incluido" if full_env else "servidor"
    # Requisitos open source del paquete (los de requirements-bank.txt son mex-lib*:
    # van como sdist aparte en vendor/bank/).
    req_lineas = []
    for _rq in ("requirements.txt", "requirements-extra.txt"):
        req_lineas += [ln for ln in (code_files or {}).get(_rq, "").splitlines()
                       if ln.strip() and not ln.strip().startswith("#")]
    if full_env:
        # Completo: SOLO lo que pip resuelve para la(s) version(es) destino, CON PySpark.
        # Antes se metia ademas la serie entera del cache (wheels de 4 versiones de
        # Python y de aarch64): ~870 MB. _vendor_files_for_pkg se llama solo para que
        # el cache tenga PySpark (lo baja si falta); su lista ya no se empaqueta.
        try:
            for _serie in _versiones_target(py_target):
                _vendor_files_for_pkg(_serie, extra_steps)
        except Exception:
            pass
        vendor_series, faltan_offline = _vendor_ligero(py_target, extra_steps, req_lineas,
                                                       incluir_spark=True, plataformas=plataformas)
    else:
        # Ligero: TODAS las librerias offline MENOS PySpark (~300-400 MB): en el
        # cluster se usa su Spark (BNX_SPARK=cluster). Antes no llevaba ninguna.
        vendor_series, faltan_offline = _vendor_ligero(py_target, extra_steps, req_lineas,
                                                       incluir_spark=False, plataformas=plataformas)
    ULTIMO_FALTAN_OFFLINE.clear()
    ULTIMO_FALTAN_OFFLINE.update(faltan_offline)
    _todos = [f for fs in (vendor_series or {}).values() for f in fs]
    ULTIMO_VENDOR.clear()
    ULTIMO_VENDOR.update({
        "pyspark": any(_wheel_dist(f) == "pyspark" for f in _todos),
        "mb": round(sum(os.path.getsize(f) for f in _todos if os.path.isfile(f)) / 1048576, 1)})
    # Empaquetar las LIBRERIAS INTERNAS del banco OFFLINE SIEMPRE que el paquete
    # las use (hay requirements-bank.txt) y tengamos el cache, TAMBIEN en el
    # paquete ligero. Son Python puro y pesan ~260 KB (no PySpark), asi que no
    # engordan el ZIP ligero y evitan que el usuario tenga que conseguirlas
    # aparte. Van en vendor/bank/ (sdist pip-instalables) y vendor/bank/pkgcode/
    # (toolbox/bnmxverse/utils, que se agregan al PYTHONPATH).
    uses_bank = any(p.endswith("requirements-bank.txt") for p in (code_files or {}))
    # requirements-extra.txt (cytoolz/unidecode/...): sus wheels viven en el MISMO
    # cache (bank_libs/wheels). Antes solo se empaquetaban si ademas habia libs del
    # banco, y setup.sh no las encontraba offline ("faltan cytoolz, unidecode").
    uses_extra = any(p.endswith("requirements-extra.txt") for p in (code_files or {}))
    bank_sdists, bank_pkgcode = ([], {})
    bank_extracted = {}
    if uses_bank:
        _todas_bank = "bank_compat_report.json" in (code_files or {})   # compat activa: se instalan TODAS las mex-lib
        bank_sdists, bank_pkgcode = _bank_vendor_files(_todas_bank)
        # vendor/bank/ SOLO lleva las mex-lib* del banco. Las deps open source del
        # stack (cytoolz/unidecode/pandas cp38/...) ya van en vendor/<serie>/ con
        # solo lo que pip resolvio (antes se metian TODAS: ~350 MB).
        bank_sdists = [p for p in bank_sdists if os.path.basename(p).lower().startswith(("mex", "bnx_bank_pkgcode"))]
        # Ademas de los sdist (que pip instala), extraemos las mex-lib verificadas
        # como CODIGO en pkgcode/ para que funcionen por PYTHONPATH sin pip/build
        # (fallback a prueba de fallos en Windows/Python 3.8).
        bank_extracted = _bank_extracted_pkgs(_todas_bank)
    # mex-lib que pide requirements-bank.txt y que NO hay en el cache (no irian en vendor/bank/)
    _bk = [_re.split(r"[<>=!~ ;\[]", ln.strip(), maxsplit=1)[0] for ln in
           (code_files or {}).get("requirements-bank.txt", "").splitlines()
           if ln.strip().lower().startswith("mex")]
    _hay = [os.path.basename(p_).lower().replace("_", "-") for p_ in bank_sdists]
    ULTIMO_VENDOR["bank_faltan"] = [b for b in _bk
                                    if not any(h.startswith(b.lower().replace("_", "-") + "-") for h in _hay)]
    # Evitar escribir la MISMA ruta dos veces (en Python 3.8/Windows un ZipInfo
    # duplicado o un estado inconsistente puede dejar el stream en mal estado y
    # romper el cierre con 'I/O operation on closed file'). Deduplicamos por ruta.
    seen_arc = set()

    def _put_str(z, arc, content):
        if arc in seen_arc:
            return
        seen_arc.add(arc)
        z.writestr(arc, contenido_a_bytes(content))

    def _put_bin(z, arc, fpath, stored=False):
        if arc in seen_arc:
            return
        try:
            with open(fpath, "rb") as fh:
                data = fh.read()
        except OSError:
            return
        seen_arc.add(arc)
        if stored:
            info = zipfile.ZipInfo(arc)
            info.compress_type = zipfile.ZIP_STORED
            z.writestr(info, data)
        else:
            z.writestr(arc, data)

    # Destino: archivo en disco (out_path) o memoria (BytesIO). Para el ambiente
    # completo (pesado) el handler pasa out_path y evitamos cargarlo todo en RAM.
    buf = None
    if out_path:
        sink = open(out_path, "wb")
    else:
        buf = io.BytesIO()
        sink = buf
    z = zipfile.ZipFile(sink, "w", zipfile.ZIP_DEFLATED, allowZip64=True)
    try:
        for path, content in (code_files or {}).items():
            _put_str(z, "framework_mlops_v2_pkg/" + path, content)
        _vts = [v for vs in _versiones_target(py_target).values() for v in vs]
        _put_str(z, "framework_mlops_v2_pkg/vendor/PYSPARK_MODE", spark_modo + "\n")
        if len(_vts) == 1:   # version exacta: setup.sh avisa si el servidor tiene otra
            _put_str(z, "framework_mlops_v2_pkg/vendor/PYTHON_TARGET", _vts[0] + "\n")
        if faltan_offline:
            _txt = ["Versiones de Python que NO podran instalar todo OFFLINE con este paquete",
                    "(faltan wheels en el cache del generador). En esas versiones setup.sh",
                    "intentara bajar lo que falte por internet / Artifactory.", ""]
            for _s, _vs in sorted(faltan_offline.items()):
                for _v, _e in sorted(_vs.items()):
                    _txt.append(f"- {_s} / Python {_v}: {_e}")
            if any(_re.match(r"\s*(xgboost|lightgbm|scikit[-_]learn|scipy|statsmodels|matplotlib|seaborn)\b", _l, _re.I) for _l in req_lineas):
                _txt += ["", "Tu codigo usa xgboost/scikit-learn/scipy: para tener sus wheels offline corre en",
                         "el generador:  .venv/bin/python preparar_vendor.py --extra --python 3.X"]
            _put_str(z, "framework_mlops_v2_pkg/vendor/OFFLINE_FALTANTES.txt", "\n".join(_txt) + "\n")
        for path, content in (sep_files or {}).items():
            _put_str(z, "framework_mlops_metrics_pkg/" + path, content)
        for serie_dir, whls in (vendor_series or {}).items():
            for fpath in whls:
                _put_bin(z, "framework_mlops_v2_pkg/vendor/" + serie_dir + "/"
                         + os.path.basename(fpath), fpath, stored=True)
        # sdist de las mex-lib* del banco -> vendor/bank/
        for fpath in bank_sdists:
            _put_bin(z, "framework_mlops_v2_pkg/vendor/bank/" + os.path.basename(fpath),
                     fpath, stored=True)
        # Codigo de path del banco (toolbox/bnmxverse/utils) -> vendor/bank/pkgcode/
        for rel, full in sorted(bank_pkgcode.items()):
            _put_bin(z, "framework_mlops_v2_pkg/vendor/bank/pkgcode/"
                     + rel.replace(os.sep, "/"), full, stored=False)
        # Paquetes de path SIN __init__.py (utils/, bnmxverse/ del banco) son
        # 'namespace packages': CUALQUIER modulo o paquete 'utils' en otro lugar del
        # sys.path les gana aunque este despues, y 'from utils.emails_full import
        # Email' falla. Con un __init__.py vacio son paquetes normales y, como van
        # al inicio del path, ganan.
        _tops = {rel.replace(os.sep, "/").split("/")[0] for rel in bank_pkgcode
                 if "/" in rel.replace(os.sep, "/")}
        _con_init = {rel.replace(os.sep, "/").split("/")[0] for rel in bank_pkgcode
                     if rel.replace(os.sep, "/").endswith("/__init__.py")
                     and rel.replace(os.sep, "/").count("/") == 1}
        for top in sorted(_tops - _con_init):
            _put_str(z, "framework_mlops_v2_pkg/vendor/bank/pkgcode/%s/__init__.py" % top,
                     "# BNX: hace de '%s' un paquete normal (no namespace) para que no lo\n"
                     "# tape otro modulo '%s' del sys.path.\n" % (top, top))
        # mex-lib VERIFICADAS extraidas como codigo -> vendor/bank/pkgcode/ tambien.
        # Asi quedan en el PYTHONPATH listas para importar sin pip (fallback).
        for rel, data in sorted(bank_extracted.items()):
            arc = "framework_mlops_v2_pkg/vendor/bank/pkgcode/" + rel
            if arc in seen_arc:
                continue
            seen_arc.add(arc)
            z.writestr(arc, data)
    finally:
        # Cerrar SIEMPRE antes de leer el resultado; si algo fallo arriba, el
        # cierre no debe lanzar un segundo error que oculte el real.
        try:
            z.close()
        except Exception:
            pass
        if out_path:
            try:
                sink.close()
            except Exception:
                pass
    series_out = sorted((vendor_series or {}).keys())
    if bank_sdists or bank_pkgcode:
        series_out = series_out + ["bank"]
    result = out_path if out_path else buf.getvalue()
    return result, "framework_mlops_v2.zip", series_out


import subprocess as _sp
import sys as _sys

# Cache propio del paquete MLOps para las deps del framework (pandas/numpy/...),
# separado por serie de Python. Vive fuera de git.
from src import vendor_cache as _vc   # ubicacion unica del cache (dentro del venv)
_MLOPS_VENDOR_CACHE = os.path.join(_vc.cache_dir(), "mlops_deps")

# Cache de las LIBRERIAS INTERNAS del banco (mex-lib* como sdist + toolbox/bnmxverse/
# utils como codigo de path). Son Python puro, sirven para cualquier plataforma/
# version. Vive fuera de git. 'wheels/' = sdist pip-instalables; 'pkgcode/' =
# modulos que el codigo espera en el PYTHONPATH (toolbox, etc.).
from src import vendor_modular as _vm   # piezas modulares: pyspark / ciencia / banco
# 'banco/' (layout nuevo) o 'bank_libs/' (viejo): vendor_cache.banco_dir elige el que exista.
_BANK_LIBS_CACHE = _vc.banco_dir()


def _bank_vendor_files(todas=False):
    """Devuelve ({sdist .tar.gz}, {pkgcode: rutas de modulos}) de las librerias
    internas del banco presentes en cache. Solo incluye los sdist VERIFICADOS
    (_BANK_PKG_VERIFIED): los incompletos en origen se omiten del vendor. Si no
    hay cache, devuelve ([], {})."""
    whl_dir = os.path.join(_BANK_LIBS_CACHE, "wheels")
    code_dir = os.path.join(_BANK_LIBS_CACHE, "pkgcode")
    sdists = []
    if os.path.isdir(whl_dir):
        _todos = sorted(os.listdir(whl_dir))
        _con_whl = {f.split("-2.")[0].replace("_", "-").lower() for f in _todos
                    if f.lower().startswith("mex") and f.endswith(".whl")}
        for f in _todos:
            if not f.endswith((".tar.gz", ".whl")):
                continue
            low = f.lower()
            if f.endswith(".tar.gz") and low.startswith("mex") and \
                    f.split("-2.")[0].replace("_", "-").lower() in _con_whl:
                continue          # ya hay wheel de esta mex-lib: el paquete lleva solo wheels
            # mex-lib* del banco: solo las VERIFICADAS (las incompletas en origen
            # se omiten del vendor porque les falta codigo).
            if low.startswith("mex"):
                pkg = (f.split("-2.")[0] if "-2." in f else f.rsplit("-", 1)[0]).replace("_", "-")
                if todas or pkg in _BANK_PKG_VERIFIED:   # todas: con bank_compat las incompletas tambien se instalan
                    sdists.append(os.path.join(whl_dir, f))
                continue
            # Cualquier OTRA wheel/sdist en bank_libs/wheels es una DEP del stack
            # del banco (pandas/numpy/xgboost/cytoolz/pytest/chispa y transitivas).
            # Se incluyen TODAS: asi nada queda faltante al montar offline.
            sdists.append(os.path.join(whl_dir, f))
    pkgcode = {}
    # Con wheel bnx_bank_pkgcode (toolbox/bnmxverse/utils) el codigo ya viaja ahi: no se copia a bank_pkg/.
    _pk_whl = bool(glob.glob(os.path.join(whl_dir, "bnx_bank_pkgcode-*.whl")))
    if os.path.isdir(code_dir) and not _pk_whl:
        for root, dirs, files in os.walk(code_dir):
            # No empaquetar artefactos de compilacion ni basura.
            dirs[:] = [d for d in dirs if d != "__pycache__"]
            for fn in files:
                if fn.endswith((".pyc", ".pyo")) or fn == ".DS_Store":
                    continue
                full = os.path.join(root, fn)
                rel = os.path.relpath(full, code_dir)
                pkgcode[rel] = full
    return sdists, pkgcode


from src import bank_compat as _bcm   # diagnostico + capa de compatibilidad de las librerias del banco


def _bank_compat_fuente():
    """Texto de src/bank_compat.py: viaja en el paquete como bank_compat.py (analisis + runtime, solo stdlib)."""
    with open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "bank_compat.py"), "r", encoding="utf-8") as fh:
        return fh.read()


def _bank_diag_fuente():
    """Texto de src/bank_diag.py: viaja en el paquete como bank_diag.py (log de diagnostico en la escritura, solo stdlib)."""
    with open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "bank_diag.py"), "r", encoding="utf-8") as fh:
        return fh.read()
def _compat_analizar(files, py_target):
    """Reporte de compatibilidad de TODAS las librerias del banco del cache contra el codigo/config del modelo
    (los archivos bank_src/** que viajan, mas toolbox/bnmxverse/utils de la wheel pkgcode). None si no hay cache."""
    try:
        codigos = dict((p, c) for p, c in files.items()
                       if p.startswith("bank_src/") and p.endswith(".py") and isinstance(c, str))
        cfgs = dict((p, c) for p, c in files.items()
                    if p.startswith("bank_src/settings/") and p.endswith(".json") and isinstance(c, str))
        dirs = [os.path.join(_BANK_LIBS_CACHE, "wheels")]
        if not os.path.isdir(dirs[0]):
            return None
        # toolbox/bnmxverse/utils de la wheel pkgcode que el codigo subido importa (transitivamente) tambien es
        # codigo del modelo (p.ej. bnmxverse/data_pull.py llama a las mex-lib); lo que nadie importa no cuenta.
        for lib in _bcm.cargar_librerias(dirs):
            if lib.nombre.startswith("bnx-bank"):
                pendientes, vistos = list(codigos.values()), set()
                while pendientes:
                    tree = _ast_mod.parse(pendientes.pop())
                    for nd in _ast_mod.walk(tree):
                        mods = []
                        if isinstance(nd, _ast_mod.Import):
                            mods = [a_.name for a_ in nd.names]
                        elif isinstance(nd, _ast_mod.ImportFrom) and not nd.level and nd.module:
                            mods = [nd.module] + [nd.module + "." + a_.name for a_ in nd.names]
                        for mod in mods:
                            if mod in lib.mods and mod not in vistos:
                                vistos.add(mod)
                                rel = lib.mods[mod]["rel"]
                                if "bank_src/" + rel not in codigos:
                                    codigos["vendor/bank/pkgcode/" + rel] = lib.mods[mod]["texto"]
                                    pendientes.append(lib.mods[mod]["texto"])
        vs = [v for vv in _versiones_target(py_target).values() for v in vv]
        menores = [int(v.split(".")[1]) for v in vs] or [11]
        vers = {"numpy": "1.26.4" if max(menores) <= 12 else "2.2.0", "python": vs[0] if len(vs) == 1 else "multiple"}
        rep = _bcm.analizar(dirs, codigos, cfgs, vers)
        return rep if rep.get("librerias") else None
    except Exception:
        return None


def _bank_extracted_pkgs(todas=False):
    """Extrae el MODULO IMPORTABLE de cada sdist mex-lib VERIFICADO (lib_extract,
    lib_generate_pivot, ...) y lo devuelve como {ruta_relativa: bytes}, listo para
    colocarlo en pkgcode/ del paquete. Asi las mex-lib funcionan por PYTHONPATH
    SIN pip/build (a prueba de fallos en Windows/Python 3.8). Ignora egg-info,
    setup.py y basura; solo trae el paquete Python que se importa."""
    import tarfile as _tar
    whl_dir = os.path.join(_BANK_LIBS_CACHE, "wheels")
    out = {}
    if not os.path.isdir(whl_dir):
        return out
    _wh = {x.split("-2.")[0].replace("_", "-").lower() for x in os.listdir(whl_dir) if x.endswith(".whl")}
    for f in sorted(os.listdir(whl_dir)):
        if not f.endswith(".tar.gz"):
            continue
        pkg = (f.split("-2.")[0] if "-2." in f else f.rsplit("-", 1)[0]).replace("_", "-")
        if not (todas or pkg in _BANK_PKG_VERIFIED) or pkg.lower() in _wh:
            continue          # con wheel instalable no hace falta el codigo extraido (fallback)
        # Modulo importable esperado (lib_extract, etc.) via el mapeo conocido.
        top = None
        for mod, p2 in _BANK_MODULE_TO_PKG.items():
            if p2 == pkg:
                top = mod
                break
        try:
            with _tar.open(os.path.join(whl_dir, f), "r:gz") as tf:
                for member in tf.getmembers():
                    if not member.isfile():
                        continue
                    # Rutas dentro del tar: '<pkg>-2.2.0/<...>'. Quitar el prefijo.
                    parts = member.name.split("/", 1)
                    if len(parts) != 2:
                        continue
                    rel = parts[1]
                    # Solo el paquete importable; descartar egg-info/setup/metadata.
                    first = rel.split("/", 1)[0]
                    if first.endswith(".egg-info") or first in (
                            "setup.py", "setup.cfg", "PKG-INFO", "MANIFEST.in"):
                        continue
                    if top and first != top:
                        continue
                    if rel.endswith((".pyc", ".pyo")) or "__pycache__" in rel:
                        continue
                    fobj = tf.extractfile(member)
                    if fobj is None:
                        continue
                    out[rel.replace(os.sep, "/")] = fobj.read()
        except Exception:
            continue
    return out


def _codigo_banco_que_viaja(bank_libs):
    """{ruta: codigo} de los modulos del banco que viajan en el paquete DESDE EL CACHE (wheel
    bnx_bank_pkgcode con toolbox/bnmxverse/utils, mex-lib*, pkgcode/). Solo si el codigo usa libs del
    banco (si no, no viajan). Sirve para decidir si pandas/numpy hacen falta (decidir_pandas)."""
    if not bank_libs:
        return {}
    out = {}
    try:
        sdists, pkgcode = _bank_vendor_files()
    except Exception:
        return out
    for rel, full in pkgcode.items():
        if rel.endswith(".py"):
            try:
                with open(full, encoding="utf-8", errors="replace") as fh:
                    out[rel.replace(os.sep, "/")] = fh.read()
            except OSError:
                pass
    for w in sdists:
        if not w.endswith(".whl"):
            continue
        try:
            with zipfile.ZipFile(w) as z:
                for n in z.namelist():
                    if n.endswith(".py") and ".dist-info/" not in n:
                        out.setdefault(n, z.read(n).decode("utf-8", "replace"))
        except (OSError, zipfile.BadZipFile):
            pass
    try:
        for rel, data in _bank_extracted_pkgs().items():
            if rel.endswith(".py"):
                out.setdefault(rel, data.decode("utf-8", "replace"))
    except Exception:
        pass
    return out


def _has_bank_libs_cache():
    sdists, pkgcode = _bank_vendor_files()
    return bool(sdists or pkgcode)

# Dependencias del framework a empaquetar OFFLINE (ademas de PySpark+py4j que ya
# trae el vendor base). pytest/chispa para correr pruebas; xgboost/sklearn solo
# si el paquete trae pasos extra (scoring).
def _mlops_base_deps(py_target=None):
    return [_PANDAS_PIN, *_numpy_pins(py_target), "pytest>=7.0", "chispa>=0.9"]
_MLOPS_EXTRA_DEPS = ["xgboost>=1.7", "scikit-learn>=1.1"]

# Python objetivo por serie (para 'pip download --python-version'): las wheels de
# pandas/numpy SI son especificas de version de Python.
_SERIE_PYVER = {"py38-311": "3.11", "py312plus": "3.12", "py314": "3.14"}
# ABI de CPython por serie. pandas/numpy traen wheels BINARIAS con ABI concreta
# (cp311, cp312); no existe wheel 'none/any' para ellas, por eso hay que pedirla.
_SERIE_ABI = {"py38-311": "cp311", "py312plus": "cp312", "py314": "cp314"}
# Plataformas Linux objetivo (el servidor del banco es Linux, normalmente x86_64).
# Bajamos ambas arquitecturas comunes para no asumir. manylinux2014 = glibc 2.17+,
# compatible con RHEL7+/la mayoria de servidores empresariales.
# Servidor del banco: RHEL 8 x86_64 (glibc 2.28): solo manylinux <= 2_28 (ver vendor_modular).
_LINUX_PLATFORMS = list(_vm._LINUX_TAGS)


def _fetch_mlops_deps(serie_dir, extra_steps):
    """Descarga (y cachea) los wheels de pandas/numpy/pytest (+xgboost/sklearn si
    extra_steps) para una serie de Python. Devuelve [rutas .whl]. Si no hay
    internet o pip falla, devuelve lo que haya en cache (puede ser [])."""
    pyver = _SERIE_PYVER.get(serie_dir, "3.11")
    abi = _SERIE_ABI.get(serie_dir, "cp311")
    # layout NUEVO (ciencia/<py>/linux/); mlops_deps/ ya no se crea
    cache = os.path.join(os.path.dirname(_MLOPS_VENDOR_CACHE), "ciencia", pyver, "linux")
    os.makedirs(cache, exist_ok=True)
    deps = _mlops_base_deps(pyver) + ([_vm.mapear_requisito(d, "linux") for d in _MLOPS_EXTRA_DEPS]
                                     if extra_steps else [])
    # Si ya hay wheels en cache, reusar sin re-descargar.
    existing = [os.path.join(cache, f) for f in os.listdir(cache) if f.endswith(".whl")]
    if existing:
        return existing
    # El paquete corre en Linux (servidor del banco), pero el generador puede
    # correr en macOS/otra version de Python. Hay que pedirle a pip, por cada
    # dependencia binaria, la wheel de Linux con la ABI de CPython correcta
    # (cp311/cp312) y, ademas, las wheels puras ('none'/'any' para pytest etc.).
    # Se intenta por cada plataforma Linux; pip trae la que resuelva y descarta
    # las que no apliquen. La restriccion de ABI/plataforma NO depende del host.
    ok_any = False
    for plat in _LINUX_PLATFORMS:
        try:
            _sp.run(
                [*_vc.pip_cmd(), "download",
                 "--only-binary=:all:",
                 "--python-version", pyver,
                 "--implementation", "cp",
                 "--abi", abi, "--abi", "abi3", "--abi", "none",
                 "--platform", plat, "--platform", "any",
                 "-d", cache, *deps],
                check=True, capture_output=True, timeout=600)
            ok_any = True
        except Exception:
            # Esta plataforma no resolvio (p.ej. no hay aarch64); seguir con la
            # siguiente. Lo importante es que al menos x86_64 funcione.
            continue
    if not ok_any:
        # Ultimo recurso: descarga para este host (puede no servir en el servidor;
        # mejor que nada para entornos de prueba locales).
        try:
            _sp.run([*_vc.pip_cmd(), "download", "-d", cache, *deps],
                    check=True, capture_output=True, timeout=600)
        except Exception:
            pass
    return [os.path.join(cache, f) for f in os.listdir(cache) if f.endswith(".whl")]


def _vendor_files_for_pkg(py_target="all", extra_steps=False):
    """Wheels para el ambiente completo OFFLINE: PySpark+py4j (del vendor base de
    Data Sintetica) MAS las deps del framework (pandas/numpy/pytest y, si
    extra_steps, xgboost/sklearn). py_target elige serie(s) para bajar tamano.
    Devuelve {serie_dir: [rutas .whl]} o {}."""
    try:
        from src.export_bundle import fetch_vendor_files, PY_TARGET_SERIES
        only = PY_TARGET_SERIES.get(py_target, None)
        base = fetch_vendor_files(only_series=only) or {}
    except Exception:
        return {}
    # (las deps open source las resuelve _seleccionar_wheels desde requirements.txt: pandas/numpy
    # solo si el paquete las necesita; ya no se descargan aqui por defecto)
    return base


# Versiones de Python que cubre cada serie de vendor/ (las wheels binarias de
# pandas/numpy/cytoolz son por version: hay que resolver para cada una).
_SERIE_VERSIONES = {"py38-311": ["3.8", "3.9", "3.10", "3.11"], "py312plus": ["3.12", "3.13"], "py314": ["3.14"]}
_SPARK_DISTS = ("pyspark", "py4j")
_BOOTSTRAP = ("pip", "setuptools", "wheel")
_seleccion_cache = {}
_descarga_fallida = set()   # (serie, version, reqs) cuya bajada ya se intento


def _wheel_dist(fname):
    return _re.split(r"-\d", os.path.basename(fname), maxsplit=1)[0].lower().replace("-", "_")


def _pool_wheels(serie_dir, extra_steps, incluir_spark, ml=False, plataforma="linux", versiones=None):
    """Wheels disponibles en cache para una serie: deps del framework, deps del stack
    del banco (cp38, cytoolz, ...) y, si incluir_spark, PySpark/py4j.
    Lee el layout NUEVO (ciencia/<py>/<plataforma>/, pyspark/<serie>/) y, solo para linux, el
    VIEJO (mlops_deps/*, bank_libs/wheels, <serie>/: eran wheels manylinux)."""
    raiz = os.path.dirname(_MLOPS_VENDOR_CACHE)
    ciencia_dirs = [os.path.join(raiz, "ciencia", v, plataforma)
                    for v in (versiones or _SERIE_VERSIONES.get(serie_dir, []))]
    nuevos = list(ciencia_dirs)
    nuevo_spark = os.path.join(raiz, "pyspark", serie_dir)
    if incluir_spark:
        nuevos.append(nuevo_spark)

    def _hay(d):
        return os.path.isdir(d) and any(f.endswith(".whl") for f in os.listdir(d))
    if plataforma != "linux":
        dirs = nuevos
    elif ciencia_dirs and all(_hay(d) for d in ciencia_dirs):
        # PREFIERE la pieza ciencia/<py>/linux del layout nuevo: el layout viejo (mlops_deps/...) solo
        # se lee cuando falta (no mezcla otra version de pandas/numpy). Siguen el banco y, si no hay
        # pieza pyspark nueva, el pyspark viejo.
        dirs = nuevos + [os.path.join(_BANK_LIBS_CACHE, "wheels")]
        if incluir_spark and not _hay(nuevo_spark):
            dirs.append(os.path.join(raiz, serie_dir))
    else:
        dirs = nuevos + _pool_dirs_viejos(raiz, serie_dir, extra_steps, ml)
    pool = {}
    for d in dirs:
        if not d or not os.path.isdir(d):
            continue
        for f in os.listdir(d):
            if not f.endswith(".whl"):
                continue
            dist = _wheel_dist(f)
            if not incluir_spark and dist in _SPARK_DISTS:
                continue
            pool.setdefault(f, os.path.join(d, f))
    return pool


def _pool_dirs_viejos(raiz, serie_dir, extra_steps, ml):
    dirs = [os.path.join(_MLOPS_VENDOR_CACHE, serie_dir),
            os.path.join(_MLOPS_VENDOR_CACHE, serie_dir + "_extra") if (extra_steps or ml) else None,
            os.path.join(_MLOPS_VENDOR_CACHE, serie_dir + "_dl"),   # bajadas automaticas
            # pila de ciencia de datos: aparte, para no cambiar lo que resuelven los
            # paquetes que NO la usan (pandas/numpy mas nuevos, glibc, ...)
            os.path.join(_MLOPS_VENDOR_CACHE, serie_dir + "_ciencia") if ml else None,
            os.path.join(_BANK_LIBS_CACHE, "wheels"),
            os.path.join(raiz, serie_dir)]
    return dirs


def _reqs_para(version, lineas, incluir_spark, plataforma="linux"):
    """Requisitos (sin markers) que aplican a una version de Python destino en la plataforma
    (linux por defecto; tambien windows / macos)."""
    try:
        from packaging.requirements import Requirement
    except ImportError:          # pip trae packaging vendorizado
        from pip._vendor.packaging.requirements import Requirement
    env = _vm.env_destino(version, plataforma)
    out = []
    for ln in lineas:
        ln = ln.split("#")[0].strip()
        if not ln:
            continue
        try:
            r = Requirement(ln)
        except Exception:
            continue
        if r.marker is not None and not r.marker.evaluate(env):
            continue
        if not incluir_spark and r.name.lower() in _SPARK_DISTS:
            continue
        r.marker = None
        r.name = _vm.dist_para(r.name, plataforma)     # xgboost -> xgboost-cpu (linux/windows)
        if str(r) not in out:
            out.append(str(r))
    return out


def _fijar_pandas_numpy(serie_dir, extra_steps, incluir_spark, v, dl):
    """Con la pila de ciencia de datos: archivo de constraints que FIJA pandas/numpy a lo
    que ya resuelve el paquete sin ella (p.ej. pandas 1.3.1 del banco en py3.8), para no
    cambiar la version del usuario ni bajar otro pandas/numpy. None si no hay nada."""
    try:
        from packaging.version import Version as _Ver
    except ImportError:
        from pip._vendor.packaging.version import Version as _Ver
    base_pool = _pool_wheels(serie_dir, extra_steps, incluir_spark, ml=False)
    abi_ = "cp" + v.replace(".", "")
    fijas = []
    for dist_ in ("pandas", "numpy"):
        cand = []
        for f_ in base_pool:
            pt = f_[:-4].split("-")
            if len(pt) >= 5 and _wheel_dist(f_) == dist_ and (
                    pt[-3] == abi_ or (pt[-3].startswith("py") and pt[-2] == "none")):
                try:
                    cand.append((_Ver(pt[1]), pt[1]))
                except Exception:
                    pass
        if cand:
            fijas.append("%s==%s" % (dist_, max(cand)[1]))
    if not fijas:
        return None
    path = os.path.join(dl, "constraints-%s.txt" % v)
    with open(path, "w") as fh_:
        fh_.write("\n".join(fijas) + "\n")
    return path


def _seleccionar_wheels(serie_dir, req_lineas, extra_steps=False, incluir_spark=True,
                        _descargar=True, versiones=None, plataforma="linux"):
    """Resuelve con pip (sin instalar) que wheels hacen falta para TODAS las versiones
    de Python de la serie, usando solo el cache local. Devuelve ([rutas], {version:
    error}). Asi el paquete lleva lo necesario (no los 350 MB del cache del banco) y
    se sabe de antemano si a alguna version le falta algo para instalar offline."""
    import json as _json
    import tempfile as _tf
    ml = any(_re.match(r"\s*(xgboost|lightgbm|scikit[-_]learn|scipy|statsmodels|matplotlib|seaborn)\b", ln, _re.I) for ln in req_lineas)
    versiones = list(versiones or _SERIE_VERSIONES.get(serie_dir, []))
    pool = _pool_wheels(serie_dir, extra_steps, incluir_spark, ml, plataforma, versiones)
    clave = (serie_dir, tuple(req_lineas), extra_steps, incluir_spark, tuple(versiones),
             tuple(sorted(pool)), plataforma)
    if clave in _seleccion_cache:
        return _seleccion_cache[clave]
    elegidas = {f for f in pool if _wheel_dist(f) in _BOOTSTRAP}
    faltan = {}
    with _tf.TemporaryDirectory() as tmp:
        links = os.path.join(tmp, "links")
        os.makedirs(links)
        for f, full in pool.items():          # un solo find-links (enlaces, no copias)
            try:
                os.symlink(full, os.path.join(links, f))
            except OSError:
                shutil.copy2(full, os.path.join(links, f))
        for v in versiones:
            reqs = _reqs_para(v, req_lineas, incluir_spark, plataforma)
            if not reqs:
                continue
            rep = os.path.join(tmp, f"r{v}.json")
            abi = "cp" + v.replace(".", "")
            try:
                _pip = _vc.pip_cmd()
            except _vc.PipViejo:
                # pip del host viejo (Python 3.8 + pip 21) y sin pip moderno en el cache: resolucion
                # interna (etiquetas + Requires-Dist), sin pip. Mismo resultado para un pool offline.
                usados, sin = _vm.resolver_interno(list(pool.values()), reqs, v, plataforma)
                elegidas.update(os.path.basename(u) for u in usados)
                if sin:
                    faltan[v] = "sin wheel en el cache: " + ", ".join(sorted(sin, key=str.lower))
                continue
            cmd = [*_pip, "install", "--dry-run", "--ignore-installed",
                   "--quiet", "--no-index", "--find-links", links, "--only-binary=:all:",
                   "--python-version", v, "--implementation", "cp",
                   "--abi", abi, "--abi", "abi3", "--abi", "none",
                   *[x for t_ in _vm.PLATAFORMAS[plataforma]["tags"] for x in ("--platform", t_)],
                   "--platform", "any", "--target", os.path.join(tmp, "t"),
                   "--report", rep, *reqs]
            try:
                r = _sp.run(cmd, capture_output=True, text=True, timeout=300)
            except Exception as e:
                faltan[v] = str(e)[:200]
                continue
            if r.returncode != 0 or not os.path.isfile(rep):
                # Nombres de los requisitos directos que no tienen wheel en el pool (pip se
                # detiene en el primer faltante); el mensaje nunca lleva el texto de uso de pip.
                en_pool = {_wheel_dist(f) for f in pool}
                sin = sorted({_re.split(r"[<>=!~ ;\[]", q, maxsplit=1)[0].strip() for q in reqs
                              if _re.split(r"[<>=!~ ;\[]", q, maxsplit=1)[0].strip().lower().replace("-", "_")
                              not in en_pool}, key=str.lower)
                msg = _vc.limpiar_stderr_pip(r.stderr or "fallo pip")
                faltan[v] = ("sin wheel en el cache: " + ", ".join(sin)) if sin and "no such" not in msg.lower() else msg
                continue
            with open(rep, encoding="utf-8") as fh:
                for item in _json.load(fh).get("install", []):
                    url = (item.get("download_info") or {}).get("url", "")
                    name = os.path.basename(url.split("?")[0])
                    if name in pool:
                        elegidas.add(name)
    if faltan and _descargar and plataforma == "linux" and os.environ.get("BNX_NO_DOWNLOAD") != "1":
        # Al cache le faltan wheels (p.ej. el servidor del portal no tiene cytoolz /
        # unidecode): bajarlas UNA vez, para Linux y esa version de Python, y resolver
        # de nuevo. Sin internet falla rapido y queda el aviso.
        # La auto-descarga guarda SIEMPRE en el layout nuevo (ciencia/<py>/linux/); nunca recrea mlops_deps/.
        bajo_algo = False
        for v in list(faltan):
            dl = os.path.join(os.path.dirname(_MLOPS_VENDOR_CACHE), "ciencia", v, "linux")
            os.makedirs(dl, exist_ok=True)
            # Sin pyspark/py4j: en PyPI pyspark es sdist (no hay wheel binaria) y con
            # --only-binary tumbaria toda la bajada; su wheel ya viene en el cache.
            reqs = _reqs_para(v, req_lineas, incluir_spark=False)
            intento = (serie_dir, v, tuple(reqs))
            if intento in _descarga_fallida:
                continue          # ya fallo en este proceso (sin red): no reintentar
            _descarga_fallida.add(intento)
            abi = "cp" + v.replace(".", "")
            # RHEL 8 (glibc 2.28): de la mas vieja a 2_28 (se prefiere la mas portable)
            _plats = ["manylinux2014_x86_64", "manylinux_2_17_x86_64", "manylinux_2_24_x86_64",
                      "manylinux_2_27_x86_64", "manylinux_2_28_x86_64"]
            _cf = _fijar_pandas_numpy(serie_dir, extra_steps, incluir_spark, v,
                                      _tf.mkdtemp(prefix="bnx_cons_"))
            _cons = ["-c", _cf] if _cf else []
            # Todo se baja preferentemente manylinux2014 (glibc 2.17), una plataforma por
            # vez. Excepcion Python >= 3.12: lightgbm 4.x solo existe en manylinux_2_28; se
            # baja APARTE (--no-deps, sus deps ya vienen en 2014) para no arrastrar
            # numpy/scipy/scikit-learn 2_28 al resto de paquetes.
            _lgbm = [r_ for r_ in reqs if r_.lower().startswith("lightgbm")] \
                if int(v.split(".")[1]) >= 12 else []
            if _lgbm:
                reqs = [r_ for r_ in reqs if r_ not in _lgbm]
                try:
                    _sp.run([*_vc.pip_cmd(), "download", "--quiet", "--no-deps",
                             "--retries", "1", "--timeout", "15", "--only-binary=:all:",
                             "--python-version", v, "--implementation", "cp",
                             "--abi", abi, "--abi", "abi3", "--abi", "none",
                             *[x for pl in _plats for x in ("--platform", pl)],
                             "--platform", "any", "-d", dl, *_lgbm],
                            capture_output=True, text=True, timeout=240)
                    bajo_algo = True
                    # Sus dependencias (narwhals, ...) se bajan con el resto (en 2014).
                    for w_ in sorted(glob.glob(os.path.join(dl, "lightgbm-*.whl")))[-1:]:
                        with zipfile.ZipFile(w_) as zw:
                            meta_ = next(zw.read(n_).decode("utf-8", "replace")
                                         for n_ in zw.namelist() if n_.endswith(".dist-info/METADATA"))
                        for ln_ in meta_.splitlines():
                            if ln_.startswith("Requires-Dist:") and "extra ==" not in ln_:
                                reqs += _reqs_para(v, [ln_.split(":", 1)[1].strip()], False)
                except Exception:
                    pass
            _grupos = [[p_] for p_ in _plats]
            for grupo in _grupos:
                try:
                    r = _sp.run([*_vc.pip_cmd(), "download", "--quiet",
                                 "--retries", "1", "--timeout", "15", "--only-binary=:all:",
                                 "--python-version", v, "--implementation", "cp",
                                 "--abi", abi, "--abi", "abi3", "--abi", "none",
                                 *[x for pl in grupo for x in ("--platform", pl)],
                                 "--platform", "any", "-d", dl, *_cons, *reqs],
                                capture_output=True, text=True, timeout=240)
                    if r.returncode == 0:
                        bajo_algo = True
                        break
                except Exception:
                    break   # sin red / timeout: no insistir
        if bajo_algo:
            return _seleccionar_wheels(serie_dir, req_lineas, extra_steps, incluir_spark,
                                       _descargar=False, versiones=versiones)
    res = ([pool[f] for f in sorted(elegidas)], faltan)
    _seleccion_cache[clave] = res
    return res


def _versiones_target(py_target):
    """{serie_dir: [versiones]} para un destino. Version EXACTA ('py3.8', 'py3.12',
    '3.8') = solo esa (lo mas ligero: una wheel por libreria). 'py38-311'/'py312plus'
    = la serie completa; 'all' = las dos."""
    m = _re.fullmatch(r"(?:py)?3\.(\d{1,2})", str(py_target or "").strip())
    if m:
        v = "3." + m.group(1)
        return {_vc.serie_de(v): [v]}
    if py_target in _SERIE_VERSIONES:
        return {py_target: list(_SERIE_VERSIONES[py_target])}
    return {s: list(vs) for s, vs in _SERIE_VERSIONES.items()}


def _vendor_ligero(py_target, extra_steps, req_lineas, incluir_spark=False, plataformas=("linux",)):
    """vendor/ por serie con SOLO lo necesario (sin PySpark si incluir_spark=False).
    plataformas: linux (servidor del banco; default) + opcionalmente windows / macos para
    correr TAMBIEN offline ahi; pip --no-index --find-links elige solo las compatibles, asi
    que mezclarlas en vendor/<serie>/ no cambia setup.sh. PySpark es el mismo wheel en todas.
    Devuelve ({serie_dir: [rutas]}, {serie_dir: {version: error}})."""
    out, faltan = {}, {}
    plats = ["linux"] + [p for p in (plataformas or ()) if p != "linux"]
    for s, versiones in _versiones_target(py_target).items():
        for plat in plats:
            files, f = _seleccionar_wheels(s, req_lineas, extra_steps, incluir_spark,
                                           versiones=versiones, plataforma=plat)
            if files:
                lst = out.setdefault(s, [])
                lst += [x for x in files if x not in lst]
            if f:
                for v, e in f.items():
                    faltan.setdefault(s, {}).setdefault(v, e if plat == "linux" else "[%s] %s" % (plat, e))
    return out, faltan


def build_package_from_sources(sources, convert_fn, optimize_fn=None,
                               include_bank_libs=True, optimize=True,
                               extra_steps=False, include_monitoring=False,
                               separate_monitoring=False, full_env=False,
                               py_target="all", out_path=None, registry=None,
                               ciencia=False, plataformas=("linux",), spark_modo=None,
                               max_recurso_mb=None):
    """Arma el Framework v2 EMPAQUETADO con la logica del usuario dentro.
    ciencia: si True agrega la PILA DE CIENCIA DE DATOS (xgboost, lightgbm, scikit-learn,
        scipy, statsmodels, matplotlib, seaborn, joblib, threadpoolctl + transitivas) a
        requirements.txt y al vendor/ offline aunque el codigo no las importe. Con False
        solo se agregan las que el codigo importa (el paquete ligero sigue ligero).
    registry: lista de fuentes (nombre de archivo o de modulo, sin importar .py ni
        mayusculas) que se REGISTRAN como jobs en router.py. Las demas son MODULOS
        DE APOYO: se copian EXACTOS a bank_src/<archivo> (sin conversion ni
        envoltura) y no entran al REGISTRY. None = todas registradas (como antes).

    include_monitoring: anade el modulo de monitoreo (PSI/CSI/DQC).
    separate_monitoring: si True, el monitoreo va como PAQUETE APARTE
        (framework_mlops_metrics_pkg/) dentro del mismo ZIP, con su propio
        setup.py/run.sh/tests. Si False, va dentro del framework principal.
    full_env: si True, empaqueta el AMBIENTE COMPLETO (PySpark offline en
        vendor/ + setup.sh que monta el venv sin internet), igual que el bundle
        'con todo' de Data Sintetica.

    sources: lista [{"name": "<archivo>.py", "code": "<pandas>"}].
    convert_fn: funcion pandas->PySpark (p.ej. py2spark convert_code). Debe
        devolver {"ok","code","warnings","unsupported"}.
    optimize_fn: opcional, PySpark->PySpark optimizado (optimize_pyspark).
    out_path: si se da, el ZIP se escribe a ese archivo en disco (no a memoria) y
        el primer valor devuelto es out_path en vez de los bytes. Recomendado para
        ambiente completo (~700 MB) y servidores de 32 bits (Windows/Python 3.8).
    Devuelve (zip_bytes_o_ruta, filename, report) donde report describe cada fuente.
    """
    # Cada fuente con su RUTA (si la trae en path/webkitRelativePath/...) antes de clasificar.
    sources = [dict(it, name=_nombre_con_ruta(it)) if isinstance(it, dict) else it for it in sources or []]
    gen_sources = []       # nombres de modulo validos, unicos
    files = {}
    report = []
    seen = set()
    original_codes = []    # codigo pandas original de cada fuente (para detectar libs)
    paquetes = _paquetes_importados(sources)
    dirs_init = _init_dirs(sources)
    kernel_jobs = []       # jobs del banco (def run(kernel)): los ejecuta main.py con el Kernel
    alias = {}             # nombre viejo (job, job_2...) -> nombre por ruta
    usados = set()         # nombres finales de jobs (aggregates y de kernel)
    _init_txt = "# BNX: paquete armado con los archivos subidos al portal.\n"

    for item in sources or []:
        raw_name = _nombre_con_ruta(item)
        pandas_code = item.get("code") or ""
        # (0) config del banco (bin/settings: spark.json, jobs.json, config_custom.json, <model>/<job>.json...):
        # va EXACTA a bank_src/settings/ (config interna del banco: queda en el paquete, nunca en git);
        # el demo/simulacion la usa por defecto con --settings.
        _rel_set = _ruta_settings(raw_name)
        if _rel_set:
            if pandas_code.strip():
                files["bank_src/settings/" + _rel_set] = pandas_code
                report.append({"name": raw_name, "source": None, "ok": True, "role": "settings", "verbatim": True,
                               "file": "bank_src/settings/" + _rel_set, "todos": [], "warnings": 0,
                               "unsupported": 0, "nota": "settings del banco: la simulacion/demo los usa con --settings"})
            continue
        # (0b) RECURSO no Python (bin/static/*.xgb, bin/opt/profile.sh...): EXACTO a bank_src/<ruta bajo bin/>.
        _rel_rec = _ruta_recurso(raw_name)
        if _rel_rec:
            _cont = recurso_a_contenido(item)
            _tam = (len(_cont) - len(_BIN_PREFIX)) * 3 // 4 if _cont.startswith(_BIN_PREFIX) \
                else len(_cont.encode("utf-8"))
            _lim = float(item.get("max_mb") or max_recurso_mb or MAX_RECURSO_MB)
            if not _cont:
                report.append({"name": raw_name, "ok": False, "role": "recurso", "reason": "vacio"})
            elif _tam > _lim * 1048576:
                report.append({"name": raw_name, "ok": False, "role": "recurso", "size": _tam,
                               "reason": "recurso de %.1f MB supera el limite de %.0f MB (BNX_MAX_RECURSO_MB / "
                                         "campo 'limite' de la UI)" % (_tam / 1048576.0, _lim)})
            else:
                files["bank_src/" + _rel_rec] = _cont
                report.append({"name": raw_name, "source": None, "ok": True, "role": "recurso", "verbatim": True,
                               "file": "bank_src/" + _rel_rec, "size": _tam, "todos": [], "warnings": 0,
                               "unsupported": 0,
                               "nota": "recurso del banco (bin/%s): BIN_PATH apunta a bank_src/ en el paquete"
                                       % _rel_rec})
            continue
        if pandas_code.strip():
            original_codes.append(pandas_code)
        if not pandas_code.strip():
            if _partes_ruta(raw_name)[-1:] == ["__init__.py"]:
                continue      # marcador de paquete vacio: no es una fuente ni un error
            report.append({"name": raw_name, "ok": False, "reason": "vacio"})
            continue
        src = _safe_name(raw_name)
        # (a) main.py del banco (Launcher): NO es un job ni un aggregate. Va exacto a
        # bank_src/main.py; el runner de main.py importa su Launcher para armar el Kernel.
        if _es_main_banco(raw_name, pandas_code):
            files["bank_src/main.py"] = pandas_code
            report.append({"name": raw_name, "source": None, "ok": True, "role": "apoyo",
                           "verbatim": True, "file": "bank_src/main.py", "todos": [],
                           "warnings": 0, "unsupported": 0,
                           "nota": "main.py del banco: no es un job; el runner usa su Launcher "
                                   "(construye el Kernel igual que el banco)"})
            continue
        # (b) todo lo que vive bajo toolbox/, bnmxverse/, utils/ (o un paquete con
        # __init__.py) es modulo de apoyo de ese paquete, aunque nadie lo importe.
        _rel_pkg = _ruta_paquete_banco(raw_name, dirs_init)
        if _rel_pkg:
            _rel = "bank_src/" + _rel_pkg
            _dirs = _rel_pkg.split("/")[:-1]
            if _rel in files and files[_rel] != pandas_code:
                report.append({"name": raw_name, "ok": False, "role": "apoyo",
                               "reason": f"nombre repetido en bank_src/: {_rel}"})
                continue
            files[_rel] = pandas_code
            for _i in range(len(_dirs)):
                files.setdefault("bank_src/" + "/".join(_dirs[:_i + 1]) + "/__init__.py", _init_txt)
            report.append({"name": raw_name, "source": None, "ok": True, "role": "apoyo",
                           "verbatim": True, "file": _rel, "todos": [], "warnings": 0,
                           "unsupported": 0, "paquete": _dirs[0] if _dirs else None,
                           "nota": "ruta del paquete del banco " + (_dirs[0] if _dirs else "")})
            continue
        # (c) job del framework del banco (def run(kernel)): se registra como job de
        # KERNEL (no como aggregate). Nombre por ruta: jobs/rps/datapull/job.py -> rps_datapull.
        if _es_job_kernel(pandas_code) and (registry is None or _en_registry(raw_name, src, registry)):
            legacy, _n = src, 1
            while legacy in seen:
                _n += 1
                legacy = f"{src}_{_n}"
            seen.add(legacy)
            ids = _kernel_ids(raw_name)
            if ids:
                nombre, modulo, model, job = ids
            else:   # archivo suelto (sin ruta): se queda con el nombre del archivo
                nombre, model, job = legacy, "", legacy
                modulo = f"jobs.{legacy}.job"
            _base, _n = nombre, 1
            while nombre in usados:
                _n += 1
                nombre = f"{_base}_{_n}"
            usados.add(nombre)
            if legacy != nombre:
                alias[legacy] = nombre
            _rel = "bank_src/" + modulo.replace(".", "/") + ".py"
            _dirs = modulo.split(".")[:-1]
            files[_rel] = pandas_code      # COPIA EXACTA: nunca se convierte ni se envuelve
            for _i in range(len(_dirs)):
                files.setdefault("bank_src/" + "/".join(_dirs[:_i + 1]) + "/__init__.py", _init_txt)
            kernel_jobs.append({"name": nombre, "module": modulo, "model": model, "job": job})
            report.append({"name": raw_name, "source": nombre, "ok": True, "role": "job",
                           "kind": "kernel", "verbatim": True, "job_kernel": True,
                           "file": _rel, "todos": [], "warnings": 0, "unsupported": 0,
                           "modulo": modulo, "alias": legacy if legacy != nombre else None,
                           **({} if ids else {"aviso": "archivo suelto SIN ruta: el nombre del job sale del "
                              "archivo (job, job_2...). Sube la carpeta completa (o con su ruta, p.ej. "
                              "bin/jobs/rps/target/job.py) para nombrarlo por ruta (rps_target)."})})
            continue
        # ¿Otro archivo subido lo importa como 'paquete.este_modulo'? Entonces es un
        # modulo de ESE paquete (toolbox/kernel.py, utils/emails_full.py, ...): va
        # EXACTO a bank_src/<paquete>/ para que el import funcione aunque el servidor
        # del portal no tenga ese paquete en su cache. Salvo que el usuario lo haya
        # marcado explicitamente como job, NO se registra.
        _stem = _norm_fuente(raw_name)
        _imp = paquetes.get(_stem)
        if _imp and os.path.basename(raw_name) not in _imp[2]:
            pkg, mod, quienes = _imp
            rel_pkg = f"bank_src/{pkg}/{mod}.py"
            if rel_pkg not in files:
                files[rel_pkg] = pandas_code
                files.setdefault(f"bank_src/{pkg}/__init__.py",
                                 f"# BNX: paquete '{pkg}' armado con los archivos subidos al portal.\n")
            explicito = registry is not None and _en_registry(raw_name, src, registry)
            if not explicito:
                report.append({"name": raw_name, "source": None, "ok": True, "role": "apoyo",
                               "verbatim": True, "file": rel_pkg, "todos": [], "warnings": 0,
                               "unsupported": 0, "paquete": pkg,
                               "nota": f"se importa como {pkg}.{mod} desde " + ", ".join(quienes[:3])})
                continue
        if registry is not None and not _en_registry(raw_name, src, registry):
            # MODULO DE APOYO (toolbox/utils/settings/main del banco...): copia EXACTA,
            # importable via bank_src/ en el sys.path. Antes se convertia y se metia
            # dentro de _aggregate_df ("salian cortados") y quedaba en el REGISTRY.
            rel = "bank_src/" + _apoyo_name(raw_name)
            if rel in files:
                report.append({"name": raw_name, "ok": False, "role": "apoyo",
                               "reason": f"nombre repetido en bank_src/: {rel}"})
                continue
            files[rel] = pandas_code
            item = {"name": raw_name, "source": None, "ok": True, "role": "apoyo",
                    "verbatim": True, "file": rel, "todos": [], "warnings": 0,
                    "unsupported": 0}
            stem = rel[len("bank_src/"):-3]
            if stem in _BANK_PATH_MODULES:
                item["aviso"] = (f"'{stem}' ya viene como PAQUETE del banco (bank_pkg/{stem}/), "
                                 f"que tiene prioridad: 'import {stem}' usara ese paquete, no esta "
                                 "copia. Si tu archivo es distinto, renombralo.")
            elif _is_stdlib_module(stem):
                # p.ej. email.py de toolbox: como modulo suelto chocaria con el stdlib.
                item["aviso"] = (f"'{stem}' es un modulo de la libreria estandar: desde "
                                 "bank_src/ no se podra importar como '" + stem + "'. "
                                 "Si es parte de toolbox ya viene en bank_pkg/toolbox/.")
            report.append(item)
            continue
        base = src
        n = 1
        while src in seen or src in usados:
            n += 1
            src = f"{base}_{n}"
        seen.add(src)
        usados.add(src)

        # Sin pandas no hay nada que convertir pandas->PySpark: el conversor solo
        # reescribiria el archivo (perdia comentarios/formato). Se copia tal cual.
        verbatim = _is_pyspark_source(pandas_code) or not _usa_pandas(pandas_code)
        if verbatim:
            # Ya es PySpark: se copia TAL CUAL (comentarios, formato y logica
            # completos). Sin conversor ni optimizador, que lo reescribirian.
            conv = {"ok": True, "code": pandas_code, "warnings": [], "unsupported": []}
        else:
            conv = convert_fn(pandas_code)
        if not conv or conv.get("ok") is False:
            reason = (conv or {}).get("unsupported", ["no es Python valido"])
            report.append({"name": raw_name, "source": src, "ok": False,
                           "reason": (reason[0] if reason else "no convertible")})
            # Igual generamos un aggregate placeholder para no romper el paquete.
            pyspark_code = "# BNX: el codigo no se pudo convertir; revisar.\ndf_out = df"
            warnings, unsupported = [], (reason if isinstance(reason, list) else [])
        else:
            pyspark_code = conv.get("code", "")
            warnings = conv.get("warnings", []) or []
            unsupported = conv.get("unsupported", []) or []
            if optimize and optimize_fn and not verbatim:
                try:
                    opt = optimize_fn(pyspark_code)
                    if opt and opt.get("code"):
                        pyspark_code = opt["code"]
                except Exception:
                    pass
            report.append({"name": raw_name, "source": src, "ok": True,
                           "warnings": len(warnings), "unsupported": len(unsupported),
                           "verbatim": verbatim, "role": "job",
                           # Job del framework del banco (def run(kernel)): el contrato
                           # aggregate del framework v2 NO llama a su run(kernel).
                           "job_kernel": _es_job_kernel(pandas_code)})

        gen_sources.append(src)
        rel_path = f"framework_mlops_v2/aggregates/{src}.py"
        agg_code = _aggregate_from_pyspark(src, pyspark_code, pandas_code, verbatim=verbatim)
        files[rel_path] = agg_code
        # Extraer los TODO (lineas no traducibles) CON su numero de linea en el
        # ARCHIVO generado (donde el usuario los abrira), para el reporte.
        todos = _extract_todos(agg_code)
        report[-1]["file"] = rel_path
        report[-1]["todos"] = todos
        report[-1]["unsupported"] = len(todos) if todos else report[-1].get("unsupported", 0)

    if not gen_sources and not kernel_jobs and not any(
            r.get("role") == "apoyo" and r.get("ok") for r in report):
        # Nada convertible: devolvemos el paquete base de ejemplo.
        data, filename = build_mlops_package(include_bank_libs)
        return data, filename, report

    # Archivos comunes del framework v2 + router con las fuentes del usuario.
    files["framework_mlops_v2/__init__.py"] = _INIT_ROOT
    files["framework_mlops_v2/core/__init__.py"] = ""
    files["framework_mlops_v2/core/base_aggregate.py"] = _BASE_AGGREGATE
    files["framework_mlops_v2/core/quality.py"] = _QUALITY
    files["framework_mlops_v2/aggregates/__init__.py"] = ""
    _nombres_finales = set(gen_sources) | {k["name"] for k in kernel_jobs}
    files["framework_mlops_v2/aggregates/router.py"] = _router_from_sources(
        gen_sources, kernel_jobs,
        {a: b for a, b in alias.items() if a not in _nombres_finales})
    files["framework_mlops_v2/features/__init__.py"] = ""
    files["framework_mlops_v2/features/ratios.py"] = _RATIOS
    # Pasos EXTRA opcionales + monitoreo DENTRO del paquete (si no se separa).
    mon_in_pkg = include_monitoring and not separate_monitoring
    files.update(_extra_step_files(
        extra_steps, include_monitoring=mon_in_pkg, monitoring_target="package"))
    files["tests/test_aggregates.py"] = _TEST
    files["main.py"] = _MAIN_PY   # entry point del framework (demo + --config)
    files["check_env.py"] = _CHECK_ENV   # verificador de deps (que no falte nada)
    if kernel_jobs:
        files.update(_demo_files())   # bnx_demo/: DEMO de los jobs del banco sin cluster
        # Log de diagnostico de escritura: viaja SIEMPRE con los jobs del banco, exista o no la cache de wheels
        # (no depende de bank_compat; sin el archivo main.py lo omitiria en silencio).
        files["bank_diag.py"] = _bank_diag_fuente()
    # Detectar librerias INTERNAS del banco (toolbox, mex_lib_cs, ...) en el
    # codigo original. Van en requirements.txt (dadas de alta) para visibilidad,
    # y ADEMAS en requirements-bank.txt para que el montaje offline del core
    # (vendor/) no se rompa: el core se instala con --no-index y las del banco se
    # intentan aparte desde el Artifactory (sin abortar si no hay acceso).
    bank_libs = _detect_bank_imports(original_codes)
    extra_pkgs = _detect_extra_imports(original_codes)
    # Diagnostico de compatibilidad de las librerias del banco (bank_compat): reporte + capa de parches.
    _compat_rep, _compat_libs = None, None
    if bank_libs:
        _compat_rep = _compat_analizar(files, py_target)
        if _compat_rep:
            files["bank_compat_report.json"] = _bcm.reporte_a_json(_compat_rep)
            files["bank_compat.py"] = _bank_compat_fuente()
            _compat_libs = dict((l["libreria"], l["paquetes"]) for l in _compat_rep["librerias"]
                                if l["libreria"].startswith("mex-lib"))
            for _m in _compat_rep.get("dependencias_terceros", []):    # deps de terceros de las mex-lib (cytoolz...)
                for _dep in _EXTRA_DEPS.get(_m, []) + [_m]:
                    _pn = _EXTRA_PIP.get(_dep)
                    if _pn and _pn not in extra_pkgs:
                        extra_pkgs.append(_pn)
    ml_libs = _ml_libs_detectadas(extra_pkgs, ciencia)
    # pandas/numpy ya no son obligatorias: solo si algun codigo que viaja las importa o hay pila de ciencia.
    pandas_info = decidir_pandas(files, ml_libs=ml_libs, extra_steps=extra_steps, ciencia=ciencia,
                                 codigo_banco=_codigo_banco_que_viaja(bank_libs))
    files["requirements.txt"] = _requirements(include_bank_libs, extra_steps, bank_libs, ml_libs, pandas_info, py_target)
    if bank_libs:
        files["requirements-bank.txt"] = _requirements_bank(bank_libs, _compat_libs)
    # xgboost/scikit-learn/scipy ya van en requirements.txt (y en vendor/): no se repiten.
    extra_pkgs = [p for p in extra_pkgs if p not in _ML_PIP
                  and not (extra_steps and p in ("xgboost", "scikit-learn"))]
    if extra_pkgs:
        files["requirements-extra.txt"] = _requirements_extra(extra_pkgs)
    # 'mex_lib_cs' es una fachada que escribimos nosotros: va EMBEBIDA en la raiz
    # del paquete (ligero, completo y rebuild), sin depender del cache del server.
    # Tambien cuando el codigo usa OTRA lib del banco: el codigo de path que viaja en
    # vendor/bank/pkgcode (p.ej. bnmxverse/data_pull.py, que usa job_4/datapull)
    # importa mex_lib_cs, y antes faltaba ("No module named 'mex_lib_cs'").
    if bank_libs:
        files["mex_lib_cs/__init__.py"] = _MEX_LIB_CS
    files["setup.sh"] = _SETUP_SH
    files["run.sh"] = _RUN_SH
    files["bnx_sparkconf.py"] = _SPARKCONF_PY
    files["probe_workers.py"] = _PROBE_WORKERS_PY
    files["cfg.example.json"] = _CFG_EXAMPLE
    files["NOTAS_EJECUCION.md"] = _NOTAS_EJECUCION
    files["pytest.ini"] = _PYTEST_INI   # pytest solo en tests/, ignora __MACOSX/vendor
    files["setup.py"] = _setup_py(pandas_info, py_target)
    files["README.md"] = _readme_custom(
        include_bank_libs, gen_sources, report, extra_steps,
        include_monitoring=include_monitoring, separate_monitoring=separate_monitoring,
        full_env=full_env, bank_libs=bank_libs)

    sep_files = _monitoring_files("separate") if (include_monitoring and separate_monitoring) else {}

    zip_result, _fn, vendor_list = zip_from_files(
        files, sep_files, full_env=full_env, py_target=py_target, out_path=out_path,
        plataformas=plataformas, spark_modo=spark_modo)

    # Clasificar libs del banco para el reporte (verificadas vs incompletas).
    bank_verified, bank_incomplete = [], []
    for lib in bank_libs or []:
        if lib in _BANK_PATH_MODULES:
            continue
        name = _bank_pkg_name(lib)
        if name in _BANK_PKG_INCOMPLETE:
            if name not in bank_incomplete:
                bank_incomplete.append(name)
        elif name not in bank_verified:
            bank_verified.append(name)

    # Detectar si se pidio ambiente completo pero el vendor de PySpark NO quedo
    # (cache vacio / sin internet en el server). vendor_list trae las series
    # incluidas; 'bank' no cuenta como PySpark. Si no hay ninguna serie de
    # PySpark, el ambiente completo salio SIN PySpark (ZIP chico, engañoso).
    # (El ligero ahora tambien trae series en vendor/, pero sin PySpark: se mira el wheel.)
    vendor_missing = bool(full_env) and not ULTIMO_VENDOR.get("pyspark")
    entorno_faltan = faltantes_entorno(ULTIMO_FALTAN_OFFLINE, vendor_missing, ULTIMO_VENDOR.get("bank_faltan"))

    # Modulos de paquetes del banco que el codigo importa (toolbox.log, ...) y que NO
    # vienen ni en lo subido ni en el cache de este servidor: el job fallaria con
    # "No module named ...". Se avisa en el portal para que los suban.
    _cache_code = os.path.join(_BANK_LIBS_CACHE, "pkgcode")
    modulos_faltantes = {}
    for _cod in original_codes + [c for p, c in files.items() if p.startswith("bank_src/") and p.endswith(".py")]:
        for pkg, mod in _imports_paquete_modulo(_cod):
            if pkg in _NO_PAQUETE_BANCO or _is_stdlib_module(pkg) or pkg == "mex_lib_cs":
                continue
            if not (pkg in (bank_libs or []) or any(p.startswith(f"bank_src/{pkg}/") for p in files)):
                continue   # no es un paquete del banco/de lo subido (p.ej. libreria pip)
            en_subido = (f"bank_src/{pkg}/{mod}.py" in files
                         or any(p.startswith(f"bank_src/{pkg}/{mod}/") for p in files))
            from src import vendor_banco as _vb
            _en_whl = _vb.archivos_pkgcode_en_wheel(_BANK_LIBS_CACHE)
            en_cache = (bool(bank_libs) and (os.path.isfile(os.path.join(_cache_code, pkg, mod + ".py"))
                        or os.path.isdir(os.path.join(_cache_code, pkg, mod))
                        or (pkg + "/" + mod + ".py") in _en_whl
                        or any(n.startswith(pkg + "/" + mod + "/") for n in _en_whl)))
            if not en_subido and not en_cache:
                modulos_faltantes.setdefault(pkg, set()).add(mod)
    modulos_faltantes = {k: sorted(v) for k, v in sorted(modulos_faltantes.items())}

    # Python en los WORKERS (udf/rdd/pandas_udf...): aviso estatico por archivo.
    workers_python = {}
    for _p, _c in files.items():
        if _p.endswith(".py") and (_p.startswith("bank_src/")
                                   or (_p.startswith("framework_mlops_v2/aggregates/")
                                       and not _p.endswith("router.py"))):
            _h = _bsc.detectar_python_en_workers(_c if isinstance(_c, str) else "")
            if _h:
                workers_python[_p] = _h
    for _r in report:
        if _r.get("file") in workers_python:
            _r["workers_python"] = len(workers_python[_r["file"]])
    # Meta: incluye los archivos de CODIGO (editables) para guardarlos por token.
    report.append({"_meta": True, "full_env": bool(full_env),
                   "pandas": pandas_info,
                   "workers_python": workers_python,
                   "workers_python_aviso": _bsc.AVISO_WORKERS if workers_python else "",
                   "vendor_series": vendor_list,
                   "vendor_missing": vendor_missing,
                   "entorno_faltan": entorno_faltan,
                   "offline_faltan": json.loads(json.dumps(ULTIMO_FALTAN_OFFLINE)),
                   "modulos_faltantes": modulos_faltantes,
                   "vendor_mb": ULTIMO_VENDOR.get("mb"),
                   "recursos": [{"file": r["file"], "size": r.get("size", 0)} for r in report
                                if r.get("role") == "recurso" and r.get("ok")],
                   "recursos_mb": round(sum(r.get("size", 0) for r in report
                                            if r.get("role") == "recurso" and r.get("ok")) / 1048576.0, 2),
                   "py_target": py_target,
                   "numpy_aviso": numpy_aviso_target(py_target) if pandas_info.get("numpy") else "",
                   "bank_libs": bank_libs,
                   "bank_verified": bank_verified,
                   "bank_incomplete": bank_incomplete,
                   "compat": ({"resumen": _compat_rep.get("resumen"), "tabla": _bcm.tabla_estados(_compat_rep),
                               "texto": _bcm.resumen_texto(_compat_rep), "entorno": _compat_rep.get("entorno")}
                              if _compat_rep else None),
                   "_code_files": files, "_sep_files": sep_files})
    return zip_result, "framework_mlops_v2.zip", report


def _readme_custom(include_bank_libs, sources, report, extra_steps=False,
                   include_monitoring=False, separate_monitoring=False,
                   full_env=False, bank_libs=None):
    rows = "\n".join(
        (f"- `{r.get('file')}` ← {r['name']} (módulo de apoyo, copia exacta; no está en el REGISTRY)"
         if r.get("role") == "apoyo" else
         f"- `{r.get('file')}` ← {r['name']} (recurso del banco, {round(r.get('size', 0) / 1024.0)} KB; "
         f"`BIN_PATH` apunta a `bank_src/`)" if r.get("role") == "recurso" and r.get("ok") else
         f"- {r['name']} ⚠️ recurso NO incluido: {r.get('reason', '')}" if r.get("role") == "recurso" else
         f"- `{r.get('source')}` ← {r['name']} (job del banco `run(kernel)`: lo ejecuta `main.py` con `toolbox.Kernel`; "
         f"`python main.py --source {r.get('source')}`)"
         if r.get("kind") == "kernel" else
         f"- `{r.get('source', '?')}` ← {r['name']}"
         + (" ✅" if r.get("ok") else f" ⚠️ {r.get('reason', '')}")
         + (f" ({r['unsupported']} revisión manual)" if r.get("unsupported") else ""))
        for r in report if not r.get("_meta"))
    # Puede no haber ningun job (solo modulos de apoyo): el ejemplo usa un nombre generico.
    sources = list(sources) or ["<tu_job>"]
    kernel_md = ""
    if any(r.get("kind") == "kernel" for r in report):
        kernel_md = '''
## Jobs del banco (`def run(kernel)`)
Estos jobs NO son aggregates: `main.py` construye el `Kernel` de `toolbox` como el `main.py` del
banco (usa su `Launcher` si viajo en `bank_src/main.py`) y llama `modulo.run(kernel)` en el orden de
`orden.json` / `depends_on` (pivote primero).
```bash
. .venv/bin/activate
python main.py                                   # DEMO: Spark local, lecturas sinteticas
python main.py --source rps_datapull             # un solo job (acepta los nombres viejos job, job_2...)
python main.py --continuar-si-falla              # no se detiene al primer error
python main.py --settings <bin/settings> --env uat --fid <fid> --cohort 202501   # datos REALES
```
Datos reales: `--settings` es la carpeta `bin/settings` del banco (`spark.json`, `jobs.json`,
`<model>/<job>.json`, `config_custom.json`) y el `toolbox` usa `master("yarn")` + Hive + Kerberos
del servidor (como `spark_exe.sh`). En DEMO no se conecta a nada externo.

### DEMO sin cluster (`--demo`, Mac/Windows; con `--settings` usa tu config de negocio)
```bash
python main.py --demo --settings <bin/settings> --env prod --continuar-si-falla
```
Sin tocar el codigo del banco, `bnx_demo/` parchea en memoria (solo en DEMO; con datos reales NO se activa):
- **Lecturas**: cada `spark.sql('select ... from db.tabla')`, `spark.table`, `read.parquet/csv/json`, JDBC y
  `pandas.read_*` devuelve datos sinteticos con las COLUMNAS que ese SQL / ese job usa (AST + SQL + settings),
  tipos por nombre y uso, y valores que pasan los filtros (`where`). Las claves (`numcliente`, `crd_acct_nbr`...)
  coinciden entre tablas para que los joins devuelvan filas. Determinista (`BNX_DEMO_SEED`); filas con
  `BNX_DEMO_FILAS` (default 50).
- **Tus datos de muestra**: `demo_data/<tabla>.parquet|csv` (o `<db>.<tabla>`) se usan antes que lo sintetico
  (tambien `BNX_DEMO_DATA=<carpeta>`).
- **Rutas del cluster** (`/data/...`, `hdfs://`, `s3://`, `abfss://`, rutas de los settings) se redirigen a
  `demo_out/<ruta>`; las tablas Hive (`saveAsTable`, `insertInto`, `INSERT OVERWRITE`) se escriben como parquet en
  `demo_out/hive/<db>/<tabla>` y los jobs siguientes las leen (datapull -> pivot -> target -> score encadenan).
- **CLI del cluster**: `hdfs dfs -ls/-test/-mkdir/-rm/-put/-get/-cat/-du/-mv` se emulan en local; `beeline`,
  `impala-shell`, `kinit`... se simulan (rc 0, sin salida; con `BNX_DEMO_ESTRICTO=1` fallan).
- Al final imprime (y guarda en `demo_out/REPORTE_DEMO.json`) por job: fuentes leidas, columnas, filas escritas y
  comandos simulados. Un `--source <job>` conserva `demo_out/` de la corrida anterior.
'''
    base = _readme(include_bank_libs)
    env = ""
    if full_env:
        env = '''

## Ambiente completo (offline)
El paquete incluye `vendor/` con los wheels de **PySpark + py4j** (dos series,
para Python 3.8–3.14) y un `setup.sh` que monta todo **sin internet**:
```bash
bash setup.sh
```
`setup.sh` crea el venv con TU Python (3.8+ del sistema), instala PySpark desde
`vendor/` offline, instala el framework (no corre el modelo: eso lo hace `bash run.sh`). Requisitos en la
máquina: Python 3.8+ y un JDK (Java) para Spark. (Python y Java NO se empaquetan;
sí las dependencias Python.)
'''
    extra = ""
    if extra_steps:
        extra = '''

## Pasos extra incluidos (opcionales)
Además de los aggregates, el paquete trae los demás pasos del pipeline como
módulos listos para usar/extender:
- `features/feature_engineering.py` — estadísticos de series (media, min, max, tendencia).
- `features/vector_assembler.py` — ensambla el `features_vector` de Spark ML.
- `scoring/scorer.py` — scoring con XGBoost (`.xgb`) o fallback lineal de prueba.
- `pipeline.py` — encadena extract → groupby → features → vector → scoring.
'''
    mon = ""
    if include_monitoring and not separate_monitoring:
        mon = '''

## Monitoreo (incluido en el paquete)
- `monitoring/monitor_metrics.py` — PSI/CSI y Data Quality (DQC). Compara la
  distribución actual contra la de desarrollo y alerta si hay drift.
'''
    elif include_monitoring and separate_monitoring:
        mon = '''

## Monitoreo (paquete SEPARADO)
El monitoreo se entrega aparte en `framework_mlops_metrics_pkg/`
(`framework_mlops_metrics`), con su propio setup.py/tests, para que corra en
producción con su propio ciclo de vida (igual que el `lib_mkop_metrics` original).
'''
    banklibs = ""
    if bank_libs:
        # Clasificar lo detectado: paquetes pip verificados / incompletos, y
        # modulos de PYTHONPATH (toolbox/...).
        ver, inc, pathmods = [], [], []
        for lib in bank_libs:
            if lib in _BANK_PATH_MODULES:
                pathmods.append(lib)
                continue
            name = _bank_pkg_name(lib)
            if name in _BANK_PKG_INCOMPLETE:
                if (name, _BANK_PKG_INCOMPLETE[name]) not in inc:
                    inc.append((name, _BANK_PKG_INCOMPLETE[name]))
            elif name not in ver:
                ver.append(name)
        ver_md = "\n".join(f"- `{n}`" for n in ver) or "- (ninguna)"
        inc_md = "\n".join(f"- `{n}` — {r}" for n, r in inc) or "- (ninguna)"
        path_md = "\n".join(f"- `{m}`" for m in pathmods) or "- (ninguno)"
        banklibs = f'''

## ⚠️ Librerías internas del banco
Tu código importa librerías **internas** del banco (no están en PyPI).

### ✅ Empaquetadas OFFLINE (verificadas, importan limpio)
{ver_md}

Vienen en `vendor/bank/` **tanto en el paquete ligero como en el ambiente
completo** (pesan ~260 KB, son Python puro). Se instalan con `--no-index` desde
ahí (ver `requirements-bank.txt`). Los módulos de PYTHONPATH se copian a
`./bank_pkg` y `main.py` los agrega al path solo:
{path_md}

> `mex_lib_cs` NO es un paquete pip: es una **fachada** que BNX genera en la raíz
> del paquete (`mex_lib_cs/`) y que re-exporta las clases de las `mex-lib*`
> (`Extract`, `GroupBy`, `GeneratePivot`, ...). Viene en todos los entornos. Si una
> `mex-lib` no está instalada o está incompleta, esa clase falla con un mensaje claro
> solo al usarla; `mex_lib_cs.disponibles()` dice cuáles cargaron.

### ⛔ NO empaquetadas (sdist INCOMPLETO en el origen)
Estas vienen defectuosas desde el `.tar.gz` del banco (les falta código). **No**
se incluyen en `vendor/bank/`; pide la versión completa al equipo del banco:
{inc_md}

Si tu servidor tiene acceso al **Artifactory privado**, pueden intentarse desde ahí:
```bash
pip install -r requirements-bank.txt --index-url https://<artifactory-interno>/simple
```
'''
    return base + banklibs + mon + '''
> 📌 **Antes de correr con datos reales lee `NOTAS_EJECUCION.md`**: como leer el `pivot.json` del banco (`--env/--cohort/--dry-run`) y como usar el metastore del cluster (`BNX_SPARK=cluster` o `SPARK_CONF_DIR`) si sale "la base no existe".

''' + f'''

## Fuentes generadas desde tu código
Cada archivo que subiste se convirtió a PySpark y se envolvió como un aggregate
que hereda de `BaseAggregate`, registrado en `aggregates/router.py`:

{rows}

Uso:
```python
from framework_mlops_v2.aggregates.router import GroupBy
GroupBy("{sources[0]}", previous_path, agg_dict, sqlContext).aggregate()
```
Revisa los comentarios `# TODO py2spark` donde la conversión no fue 1:1.
{kernel_md}{extra}{env}'''


def build_mlops_package(include_bank_libs=True, extra_steps=False,
                        include_monitoring=False, separate_monitoring=False):
    """Arma el ZIP del Framework MLOps v2 (plantilla base). Devuelve (bytes, nombre)."""
    files = {
        "framework_mlops_v2/__init__.py": _INIT_ROOT,
        "framework_mlops_v2/core/__init__.py": "",
        "framework_mlops_v2/core/base_aggregate.py": _BASE_AGGREGATE,
        "framework_mlops_v2/core/quality.py": _QUALITY,
        "framework_mlops_v2/aggregates/__init__.py": "",
        "framework_mlops_v2/aggregates/atms.py": _ATMS,
        "framework_mlops_v2/aggregates/s15.py": _S15,
        "framework_mlops_v2/aggregates/pnl.py": _PNL,
        "framework_mlops_v2/aggregates/router.py": _ROUTER,
        "framework_mlops_v2/features/__init__.py": "",
        "framework_mlops_v2/features/ratios.py": _RATIOS,
        "tests/test_aggregates.py": _TEST,
        "main.py": _MAIN_PY,
        "requirements.txt": _requirements(include_bank_libs, extra_steps),
        "setup.sh": _SETUP_SH,
        "run.sh": _RUN_SH,
        "bnx_sparkconf.py": _SPARKCONF_PY,
        "probe_workers.py": _PROBE_WORKERS_PY,
        "cfg.example.json": _CFG_EXAMPLE,
        "NOTAS_EJECUCION.md": _NOTAS_EJECUCION,
        "pytest.ini": _PYTEST_INI,
        "README.md": _readme(include_bank_libs),
        "setup.py": _setup_py(),
    }
    mon_in_pkg = include_monitoring and not separate_monitoring
    files.update(_extra_step_files(
        extra_steps, include_monitoring=mon_in_pkg, monitoring_target="package"))
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as z:
        for path, content in files.items():
            z.writestr("framework_mlops_v2_pkg/" + path, content)
        if include_monitoring and separate_monitoring:
            for path, content in _monitoring_files("separate").items():
                z.writestr("framework_mlops_metrics_pkg/" + path, content)
    return buf.getvalue(), "framework_mlops_v2.zip"


# --------------------------------------------------------------------------
# Ejemplos cargables de un clic en la UI (pandas de negocio por fuente).
# --------------------------------------------------------------------------
EXAMPLES = [
    {
        "id": "bureau",
        "title": "Buró de crédito (groupby)",
        "name": "bureau.py",
        "code": ("import pandas as pd\n\n"
                 "df = pd.read_parquet('extract/bureau')\n"
                 "df = df[df['inf_dt'] >= '2025-01-01']\n"
                 "df_out = df.groupby('cliente_id').agg({\n"
                 "    'saldo': 'sum',\n"
                 "    'atraso_max': 'max',\n"
                 "    'lineas_activas': 'mean',\n"
                 "})\n"),
    },
    {
        "id": "canales",
        "title": "Canales (filtro + flags)",
        "name": "canales.py",
        "code": ("import pandas as pd\n\n"
                 "df = pd.read_csv('canales.csv')\n"
                 "df = df[df['monto'] > 0]\n"
                 "df['usa_app'] = (df['canal'] == 'APP').astype(int)\n"
                 "df['usa_web'] = (df['canal'] == 'WEB').astype(int)\n"
                 "df_out = df\n"),
    },
    {
        "id": "pnl_ratios",
        "title": "PnL (ratios con protección /0)",
        "name": "pnl.py",
        "code": ("import pandas as pd\n"
                 "import numpy as np\n\n"
                 "df = pd.read_parquet('groupby/pnl')\n"
                 "df['margen'] = np.where(df['ingresos'] > 0,\n"
                 "                        df['utilidad'] / df['ingresos'], 0.0)\n"
                 "df['costo_rel'] = np.where(df['ingresos'] > 0,\n"
                 "                           df['costo'] / df['ingresos'], 0.0)\n"
                 "df_out = df\n"),
    },
    {
        "id": "pasivos",
        "title": "Pasivos (join + agregación)",
        "name": "pasivos.py",
        "code": ("import pandas as pd\n\n"
                 "cuentas = pd.read_parquet('extract/cuentas')\n"
                 "clientes = pd.read_parquet('extract/clientes')\n"
                 "j = cuentas.merge(clientes, on='cliente_id', how='left')\n"
                 "j = j[j['saldo_prom'] > 0]\n"
                 "df_out = j.groupby('cliente_id').agg({'saldo_prom': 'sum'})\n"),
    },
]


def get_examples():
    return [dict(e) for e in EXAMPLES]


def package_manifest(include_bank_libs=True):
    """Describe que trae el paquete (para mostrarlo en la UI antes de descargar)."""
    improvements = [
        {"from": "atms/s15/s15_nf duplicados", "to": "clase base BaseAggregate (sin duplicacion)"},
        {"from": "validaciones de nulos comentadas", "to": "core/quality.py con assert activo"},
        {"from": "GroupBy con herencia multiple", "to": "router por registro (una linea por fuente)"},
        {"from": "test() que imprime 'working!'", "to": "pytest real con fixture de Spark"},
        {"from": "try/except que silencian errores", "to": "excepciones explicitas + logging"},
        {"from": "sin entorno reproducible", "to": "setup.sh monta el venv; run.sh solo corre el modelo"},
    ]
    tree = [
        "framework_mlops_v2/core/base_aggregate.py",
        "framework_mlops_v2/core/quality.py",
        "framework_mlops_v2/aggregates/{atms,s15,pnl,router}.py",
        "framework_mlops_v2/features/ratios.py",
        "tests/test_aggregates.py",
        "requirements.txt  ·  setup.sh  ·  run.sh  ·  setup.py  ·  README.md",
    ]
    return {"improvements": improvements, "tree": tree,
            "include_bank_libs": include_bank_libs}


# --------------------------------------------------------------------------
# Verificacion REAL del paquete: monta un venv, instala deps (offline si hay
# vendor/), corre check_env.py y pytest. Devuelve el log estilo terminal para
# mostrarlo en la GUI. Es lo que hace el boton "Probar entorno" del portal.
# --------------------------------------------------------------------------
def verify_package_env(code_files, full_env=False, py_target="all", timeout=900,
                       run_pytest=False, emulate_linux=True):
    """Verifica el paquete simulando el SERVIDOR LINUX del banco (default), o
    montando un venv local. No deja residuos.

    emulate_linux=True (RECOMENDADO): resuelve TODAS las dependencias contra el
        target Linux (manylinux, cp38 o cp312 segun py_target) con
        'pip download --no-index' desde vendor/. Reporta que resuelve y que falta
        EXACTAMENTE como lo hara el server del banco, aunque el portal corra en
        Mac/Windows. No instala ni importa (no depende de la plataforma del host).
    emulate_linux=False: monta un venv real en el host (solo fiel si el host ES
        el destino; en Mac da falsos faltantes por diferencia de plataforma).

    code_files/full_env/py_target: como en zip_from_files.
    run_pytest: solo aplica al modo venv local (arranca JVM/Spark).
    Devuelve {log, steps, ok_env, checks, mode}."""
    import tempfile as _tf
    import shutil as _sh
    import venv as _venv

    workdir = _tf.mkdtemp(prefix="bnx_verify_")
    pkg_root = os.path.join(workdir, "framework_mlops_v2_pkg")
    log_lines = []
    steps = []

    def _log(s):
        log_lines.append(s)

    def _run(name, args, cwd):
        """Corre un comando, captura stdout+stderr, lo agrega al log."""
        _log("$ " + " ".join(args))
        try:
            p = _sp.run(args, cwd=cwd, capture_output=True, text=True,
                        timeout=timeout)
            out = (p.stdout or "") + (p.stderr or "")
            if out.strip():
                _log(out.rstrip("\n"))
            steps.append({"name": name, "exit_code": p.returncode,
                          "ok": p.returncode == 0})
            _log("")
            return p.returncode, out
        except Exception as e:  # pragma: no cover
            _log("[ERROR] %s: %s" % (name, e))
            steps.append({"name": name, "exit_code": -1, "ok": False})
            _log("")
            return -1, str(e)

    checks = {"missing": [], "ok": []}
    ok_env = False
    try:
        # 1) Materializar el paquete en disco (incluye vendor/ si full_env, para
        #    poder instalar offline exactamente como en el servidor del banco).
        zb, _fn, _series = zip_from_files(
            code_files or {}, None, full_env=full_env, py_target=py_target)
        import zipfile as _zf
        _zf.ZipFile(io.BytesIO(zb)).extractall(workdir)
        _log("== Entorno de prueba: %s ==" % pkg_root)
        _log("Paquete extraido (%d archivos).\n" % len(code_files or {}))

        # MODO LINUX (default): resolver dependencias contra el target del banco
        # (manylinux, cp38/cp312), sin instalar en el host. Fiel al server aunque
        # el portal corra en Mac/Windows.
        if emulate_linux:
            res = _verify_resolve_linux(pkg_root, py_target, _log, steps, timeout)
            checks = res["checks"]
            ok_env = res["ok_env"]
            _log("== Fin de la verificacion (modo Linux del banco) ==")
            return {"log": "\n".join(log_lines), "steps": steps,
                    "ok_env": ok_env, "checks": checks, "mode": "linux"}

        # 2) Crear el venv.
        venv_dir = os.path.join(workdir, ".venv")
        _log("$ python -m venv .venv")
        _venv.EnvBuilder(with_pip=True).create(venv_dir)
        py = os.path.join(venv_dir, "bin", "python")
        if not os.path.exists(py):  # Windows
            py = os.path.join(venv_dir, "Scripts", "python.exe")
        _log("venv creado.\n")
        steps.append({"name": "venv", "exit_code": 0, "ok": True})

        # 3) Elegir serie de vendor segun la version del python del venv.
        vendor_root = os.path.join(pkg_root, "vendor")
        vendor_dir = None
        if os.path.isdir(vendor_root):
            minor = _sys.version_info[1]
            cand = _vc.serie_de("3.%d" % minor)
            for d in (cand, "py38-311", "py312plus", "py314"):
                if os.path.isdir(os.path.join(vendor_root, d)):
                    vendor_dir = os.path.join(vendor_root, d)
                    break

        # pip/setuptools/wheel: OFFLINE desde vendor/ si hay (no toca internet);
        # si no, upgrade normal por pip.
        if vendor_dir:
            _run("pip/setuptools (offline)",
                 [py, "-m", "pip", "install", "--no-index", "--find-links",
                  vendor_dir, "pip", "setuptools", "wheel"], pkg_root)
        else:
            _run("pip upgrade", [py, "-m", "pip", "install", "--upgrade", "pip",
                                 "setuptools", "wheel"], pkg_root)
        req = os.path.join(pkg_root, "requirements.txt")
        if vendor_dir:
            _run("deps (offline vendor/)",
                 [py, "-m", "pip", "install", "--no-index", "--pre",
                  "--find-links", vendor_dir, "-r", req], pkg_root)
            _run("framework (editable)",
                 [py, "-m", "pip", "install", "--no-build-isolation", "-e", "."],
                 pkg_root)
        else:
            _run("deps (pip)", [py, "-m", "pip", "install", "-r", req], pkg_root)
            _run("framework (editable)", [py, "-m", "pip", "install", "-e", "."],
                 pkg_root)

        # 4) Libs del banco OFFLINE (si el paquete las trae).
        bank_dir = os.path.join(vendor_root, "bank")
        req_bank = os.path.join(pkg_root, "requirements-bank.txt")
        if os.path.isdir(bank_dir) and os.path.isfile(req_bank):
            _run("libs banco (offline)",
                 [py, "-m", "pip", "install", "--no-index", "--no-build-isolation",
                  "--find-links", bank_dir, "-r", req_bank], pkg_root)
            # Copiar pkgcode (toolbox/...) a bank_pkg para el PYTHONPATH.
            pkgcode = os.path.join(bank_dir, "pkgcode")
            if os.path.isdir(pkgcode):
                dst = os.path.join(pkg_root, "bank_pkg")
                _sh.copytree(pkgcode, dst, dirs_exist_ok=True)

        # 5) check_env.py — el verificador de dependencias.
        env_vars = dict(os.environ)
        bank_pkg = os.path.join(pkg_root, "bank_pkg")
        if os.path.isdir(bank_pkg):
            env_vars["PYTHONPATH"] = bank_pkg + os.pathsep + env_vars.get("PYTHONPATH", "")
        _log("$ python check_env.py")
        try:
            pe = _sp.run([py, "check_env.py"], cwd=pkg_root, capture_output=True,
                         text=True, timeout=timeout, env=env_vars)
            ce_out = (pe.stdout or "") + (pe.stderr or "")
            _log(ce_out.rstrip("\n"))
            ok_env = pe.returncode == 0
            steps.append({"name": "check_env", "exit_code": pe.returncode,
                          "ok": ok_env})
            # Parsear faltantes/ok del texto (lineas 'Instaladas OK' y 'FALTAN').
            for ln in ce_out.splitlines():
                s = ln.strip()
                if s.startswith("Instaladas OK"):
                    part = s.split(":", 1)[1].strip() if ":" in s else ""
                    checks["ok"] = [x.strip() for x in part.split(",")
                                    if x.strip() and x.strip() != "-"]
                elif s.startswith("- ") and ":" in s and (
                        "open source" in s or "banco" in s or "Otras" in s):
                    part = s.split(":", 1)[1].strip()
                    checks["missing"] += [x.strip() for x in part.split(",")
                                          if x.strip()]
            _log("")
        except Exception as e:  # pragma: no cover
            _log("[ERROR] check_env: %s\n" % e)
            steps.append({"name": "check_env", "exit_code": -1, "ok": False})

        # 6) pytest OPCIONAL (lento: arranca JVM/Spark). Solo si se pide.
        if run_pytest:
            _run("pytest", [py, "-m", "pytest", "-q"], pkg_root)
        else:
            _log("(pytest omitido; activalo con 'Correr pruebas' para ejecutar Spark)\n")

        _log("== Fin de la verificacion (venv local) ==")
    finally:
        _sh.rmtree(workdir, ignore_errors=True)

    return {"log": "\n".join(log_lines), "steps": steps,
            "ok_env": ok_env, "checks": checks, "mode": "venv"}


def _verify_resolve_linux(pkg_root, py_target, _log, steps, timeout):
    """Resuelve las dependencias del paquete contra el target LINUX del banco con
    'pip download --no-index' (manylinux, cp38/cp312). No instala: solo comprueba
    que pip encuentre una version valida de cada dep para Linux, exactamente como
    en el server. Analiza requirements.txt (core) y requirements-bank.txt (banco)
    + los imports del codigo. Devuelve {ok_env, checks{ok,missing}}."""
    import tempfile as _tf
    import shutil as _sh

    # Version(es) destino: exacta (py3.8 / py3.12) o la serie. Por cada version se SIMULA
    # la instalacion COMPLETA (pip resuelve todo el arbol de dependencias, como el
    # 'pip install' del servidor Linux), no paquete por paquete: asi tambien se detecta
    # una dependencia transitiva que falte (python-dateutil de pandas, threadpoolctl...).
    destino = _versiones_target(py_target)
    series = list(destino)
    plats = list(_vm._LINUX_TAGS)   # RHEL 8 x86_64 (glibc 2.28): nunca manylinux_2_31+ ni musllinux
    bank_dir = os.path.join(pkg_root, "vendor", "bank")

    _log("== Verificacion emulando el SERVIDOR LINUX del banco ==")
    _log("Se resuelve con pip, sin instalar, en CADA version de Python de la serie.\n")

    def _read_reqs(path):
        reqs = []
        if os.path.isfile(path):
            for ln in open(path, encoding="utf-8"):
                s_ = ln.split("#", 1)[0].strip()
                if s_:
                    reqs.append(s_)
        return reqs

    core = _read_reqs(os.path.join(pkg_root, "requirements.txt"))
    extra = _read_reqs(os.path.join(pkg_root, "requirements-extra.txt"))
    bank = _read_reqs(os.path.join(pkg_root, "requirements-bank.txt"))

    def _mex_ok(name):
        nlow = name.lower().replace("_", "-")
        return os.path.isdir(bank_dir) and any(
            f.lower().replace("_", "-").startswith(nlow) and f.endswith((".tar.gz", ".whl"))
            for f in os.listdir(bank_dir))

    faltan_por_ver = {}
    for serie in series:
        vendor_dir = os.path.join(pkg_root, "vendor", serie)
        links = []
        for d in (vendor_dir, bank_dir):
            if os.path.isdir(d):
                links += ["--find-links", d]
        # Paquete LIGERO: no trae PySpark a proposito (se usa el del cluster).
        ligero = not (os.path.isdir(vendor_dir) and any(
            f.startswith("pyspark-") for f in os.listdir(vendor_dir)))
        if ligero:
            _log("[%s] paquete LIGERO: PySpark no se verifica (en el servidor se usa el Spark "
                 "del cluster: BNX_SPARK=cluster bash run.sh)." % serie)
        for pyver in destino[serie]:
            abi = "cp" + pyver.replace(".", "")
            _pkw = ["bnx-bank-pkgcode"] if (os.path.isdir(bank_dir) and any(
                f.startswith("bnx_bank_pkgcode-") for f in os.listdir(bank_dir))) else []
            reqs = _reqs_para(pyver, core + extra + [b for b in bank if not b.lower().startswith("mex")] + _pkw,
                              incluir_spark=not ligero)
            base_cmd = (["--no-index", "--only-binary=:all:"] + links
                        + ["--python-version", pyver, "--implementation", "cp",
                           "--abi", abi, "--abi", "abi3", "--abi", "none"]
                           + [x for pl in plats for x in ("--platform", pl)] + ["--platform", "any"])
            faltan, instalaria = [], 0
            tmp = _tf.mkdtemp(prefix="bnx_res_")
            try:
                rep = os.path.join(tmp, "r.json")
                p = _sp.run([*_vc.pip_cmd(), "install", "--dry-run", "--ignore-installed",
                             "--quiet", "--target", os.path.join(tmp, "t"), "--report", rep]
                            + base_cmd + reqs, capture_output=True, text=True, timeout=timeout)
                if p.returncode == 0 and os.path.isfile(rep):
                    with open(rep, encoding="utf-8") as fh:
                        instalaria = len(json.load(fh).get("install", []))
                else:
                    # pip se detiene en el PRIMER faltante: listar todos (directos + el
                    # transitivo que reporto pip) para que el mensaje sea completo.
                    faltan += _re.findall(r"No matching distribution found for ([A-Za-z0-9_.\-]+)",
                                          p.stderr or "")
                    for req in reqs:
                        d = os.path.join(tmp, "d")
                        q = _sp.run([*_vc.pip_cmd(), "download", "--no-deps",
                                     "--quiet", "-d", d] + base_cmd + [req],
                                    capture_output=True, text=True, timeout=timeout)
                        if q.returncode != 0:
                            faltan.append(_re.split(r"[<>=!~ ;\[]", req, maxsplit=1)[0].strip())
                    if not faltan:
                        faltan.append("(conflicto de versiones: " +
                                      _vc.limpiar_stderr_pip(p.stderr, maximo=120) + ")")
            except _vc.PipViejo as e:
                # pip del host viejo (Python 3.8 + pip 21) sin pip moderno en el cache: se verifica con
                # la resolucion interna (etiquetas manylinux<=2_28/cp + Requires-Dist), sin pip.
                _ws = [os.path.join(d_, f_) for d_ in (vendor_dir, bank_dir) if os.path.isdir(d_)
                       for f_ in os.listdir(d_) if f_.endswith(".whl")]
                _us, _sin = _vm.resolver_interno(_ws, reqs, pyver, "linux")
                instalaria = len(_us)
                faltan += sorted(_sin)
                _log("   (resolucion interna sin pip: %s)" % str(e)[:160])
            except Exception as e:
                faltan.append("(error al simular: %s)" % str(e)[:120])
            finally:
                _sh.rmtree(tmp, ignore_errors=True)
            # RHEL 8 (glibc 2.28): ninguna wheel del vendor puede pedir una glibc mayor
            _malas = _vm.wheels_glibc_incompatibles(
                [f_ for d_ in (vendor_dir, bank_dir) if os.path.isdir(d_) for f_ in os.listdir(d_)])
            if _malas:
                _log("   glibc > 2.28 (no instalan en RHEL 8): " + ", ".join(_malas))
                faltan += ["%s (glibc > 2.28)" % m_ for m_ in _malas]
            # mex-lib del banco: son sdist (.tar.gz), se comprueba que esten en vendor/bank
            faltan += [b for b in (_re.split(r"[<>=!~ ;]", x, maxsplit=1)[0].strip()
                                   for x in bank if x.lower().startswith("mex")) if not _mex_ok(b)]
            faltan = sorted(set(faltan), key=str.lower)
            ok = not faltan
            _log("$ Python %s (Linux %s): instalacion completa simulada -> %s"
                 % (pyver, abi, ("OK, %d paquetes" % instalaria) if ok else "faltan: " + ", ".join(faltan)))
            steps.append({"name": "Python %s (%s)" % (pyver, serie), "exit_code": 0 if ok else 1, "ok": ok})
            if faltan:
                faltan_por_ver["%s/%s" % (serie, pyver)] = sorted(set(faltan))

    faltantes = sorted({f for fs in faltan_por_ver.values() for f in fs})
    ok_env = not faltantes
    _log("")
    if ok_env:
        _log("[OK] El paquete se instala OFFLINE en el servidor Linux (Python %s)."
             % ", ".join(v for vs in destino.values() for v in vs))
    else:
        _log("[FALTAN] para Linux:")
        for k, fs in sorted(faltan_por_ver.items()):
            _log("  - Python %s: %s" % (k.split("/")[1], ", ".join(fs)))
        _log("  -> El cache de ESTE servidor del portal no tiene esas wheels. Bajalas/generalas con")
        _log("     `.venv/bin/python preparar_vendor.py --python 3.X` (o el boton 'Bajar/generar cache'")
        _log("     de la pagina), o importa un ZIP hecho en otra maquina con")
        _log("     `exportar_vendor.py --python 3.X` (aqui: preparar_vendor.py --zip <zip>).")
        if any(_vm.nombre_logico(f.lower().split("[")[0]) in _ML_PIP
               for f in faltantes):
            _log("     pila de ciencia de datos: corre `.venv/bin/python preparar_vendor.py --extra --python 3.X`.")
        _log("     Las mex-lib del banco no estan en PyPI: cargalas en 'Librerias del banco' o por ZIP.")
    return {"ok_env": ok_env, "checks": {"ok": [], "missing": faltantes,
                                         "por_version": faltan_por_ver}}


def bank_libs_list():
    """Inventario del cache de librerias del banco. Devuelve:
      {wheels: [{name, size, kind, pkg, status, reason}],
       pkgcode: [{module, files:[{name,size}]}]}
    - kind: 'mex-lib' | 'dep' (pandas/numpy/...) | 'otro'
    - status (solo mex-lib): 'verificada' | 'incompleta' | 'desconocida'"""
    whl_dir = os.path.join(_BANK_LIBS_CACHE, "wheels")
    code_dir = os.path.join(_BANK_LIBS_CACHE, "pkgcode")
    wheels = []
    if os.path.isdir(whl_dir):
        for f in sorted(os.listdir(whl_dir)):
            if not f.endswith((".tar.gz", ".whl")):
                continue
            full = os.path.join(whl_dir, f)
            low = f.lower()
            pkg = f.split("-2.")[0] if "-2." in f else f.rsplit("-", 1)[0]
            if low.startswith("mex"):
                kind = "mex-lib"
                if pkg in _BANK_PKG_VERIFIED:
                    status, reason = "verificada", ""
                elif pkg in _BANK_PKG_INCOMPLETE:
                    status, reason = "incompleta", _BANK_PKG_INCOMPLETE[pkg]
                else:
                    status, reason = "desconocida", "sin verificar (usa 'Verificar')"
            elif low.startswith(("pandas-", "numpy-", "xgboost-", "xgboost_cpu-", "scikit_learn-",
                                 "scikit-learn-", "scipy-")):
                kind, status, reason = "dep", "incluida", ""
            else:
                kind, status, reason = "otro", "incluida", ""
            wheels.append({"name": f, "size": os.path.getsize(full),
                           "kind": kind, "pkg": pkg,
                           "status": status, "reason": reason})
    pkgcode = []
    if os.path.isdir(code_dir):
        for mod in sorted(os.listdir(code_dir)):
            mdir = os.path.join(code_dir, mod)
            if not os.path.isdir(mdir):
                continue
            files = []
            for root, dirs, fns in os.walk(mdir):
                dirs[:] = [d for d in dirs if d != "__pycache__"]
                for fn in fns:
                    if fn.endswith((".pyc", ".pyo")) or fn == ".DS_Store":
                        continue
                    full = os.path.join(root, fn)
                    rel = os.path.relpath(full, mdir)
                    files.append({"name": rel.replace(os.sep, "/"),
                                  "size": os.path.getsize(full)})
            pkgcode.append({"module": mod, "files": sorted(files, key=lambda x: x["name"])})
    return {"wheels": wheels, "pkgcode": pkgcode}


def bank_libs_import_from_path(src_path):
    """Importa librerias del banco desde una RUTA del disco (carpeta de release
    como '.../170589.DAA.MLOps_RPS...'). Copia al cache:
      - *.tar.gz / *.whl  -> bank_libs/wheels/
      - bin/toolbox, bin/utils, bin/bnmxverse (o en la raiz) -> bank_libs/pkgcode/<mod>/
    Devuelve {copiados: [...], omitidos: [...]} (resumen por archivo/modulo)."""
    import shutil as _sh
    src_path = os.path.expanduser((src_path or "").strip())
    if not src_path or not os.path.isdir(src_path):
        raise ValueError("Ruta no valida o no es un directorio: %r" % src_path)
    whl_dir = os.path.join(_BANK_LIBS_CACHE, "wheels")
    code_dir = os.path.join(_BANK_LIBS_CACHE, "pkgcode")
    os.makedirs(whl_dir, exist_ok=True)
    os.makedirs(code_dir, exist_ok=True)
    copiados, omitidos = [], []

    # Cache de PySpark (series). pyspark 3.5.x -> py38-311; 4.0.x -> py312plus.
    pyspark_cache = os.path.join(
        os.path.dirname(_BANK_LIBS_CACHE), "")  # raiz del cache (vendor_cache.cache_dir())

    def _pyspark_serie(fname):
        low = fname.lower()
        if low.startswith("pyspark-"):
            ver = low.split("pyspark-", 1)[1]
            if ver.startswith("3."):
                return "py38-311"
            if ver.startswith(("4.", "5.")):
                return "py312plus"
        if low.startswith("py4j-"):
            # py4j 0.10.9.7 -> 3.5; 0.10.9.9 -> 4.0. Copiamos a AMBAS por si acaso.
            return "both-py4j"
        return None

    # 1) Wheels/sdist: buscar en la raiz de la ruta (no recursivo profundo para
    #    no arrastrar basura; 1 nivel cubre el layout de release del banco).
    #    El servidor del banco es LINUX: se omiten wheels de macOS/Windows (no
    #    corren alla y solo engordan el paquete). Los sdist (.tar.gz) son
    #    multiplataforma, se copian siempre.
    for f in sorted(os.listdir(src_path)):
        full = os.path.join(src_path, f)
        if not (os.path.isfile(full) and f.endswith((".tar.gz", ".whl"))):
            continue
        low = f.lower()
        if f.endswith(".whl") and ("macosx" in low or "win_amd64" in low
                                   or "win32" in low or "-win-" in low):
            omitidos.append(f + " (wheel no-Linux; el servidor del banco es Linux)")
            continue
        # PySpark / py4j -> van al cache de vendor de PySpark (no a bank_libs),
        # para que el 'ambiente completo' los empaquete offline.
        serie = _pyspark_serie(f)
        if serie:
            targets = (["py38-311", "py312plus"] if serie == "both-py4j" else [serie])
            for sdir in targets:
                dcache = os.path.join(pyspark_cache, sdir)
                os.makedirs(dcache, exist_ok=True)
                dst = os.path.join(dcache, f)
                if os.path.exists(dst) and os.path.getsize(dst) == os.path.getsize(full):
                    omitidos.append("%s/%s (ya estaba)" % (sdir, f))
                else:
                    _sh.copy2(full, dst)
                    copiados.append("vendor-pyspark/%s/%s" % (sdir, f))
            continue
        dst = os.path.join(whl_dir, f)
        if os.path.exists(dst) and os.path.getsize(dst) == os.path.getsize(full):
            omitidos.append(f + " (ya estaba, identico)")
        else:
            _sh.copy2(full, dst)
            copiados.append("wheels/" + f)

    # 2) Modulos de PYTHONPATH: toolbox/utils/bnmxverse, esten en la raiz o en bin/.
    for base in (src_path, os.path.join(src_path, "bin")):
        if not os.path.isdir(base):
            continue
        for mod in ("toolbox", "utils", "bnmxverse"):
            mdir = os.path.join(base, mod)
            if not os.path.isdir(mdir):
                continue
            dst = os.path.join(code_dir, mod)
            n_before = 0
            if os.path.isdir(dst):
                for _r, _d, _fs in os.walk(dst):
                    n_before += len([x for x in _fs if not x.endswith((".pyc", ".pyo"))])
            # Copiar archivos (merge), sin .pyc/__pycache__.
            for root, dirs, fns in os.walk(mdir):
                dirs[:] = [d for d in dirs if d != "__pycache__"]
                for fn in fns:
                    if fn.endswith((".pyc", ".pyo")) or fn == ".DS_Store":
                        continue
                    srcf = os.path.join(root, fn)
                    rel = os.path.relpath(srcf, mdir)
                    dstf = os.path.join(dst, rel)
                    os.makedirs(os.path.dirname(dstf), exist_ok=True)
                    changed = not (os.path.exists(dstf)
                                   and os.path.getsize(dstf) == os.path.getsize(srcf))
                    _sh.copy2(srcf, dstf)
                    if changed:
                        copiados.append("pkgcode/%s/%s" % (mod, rel.replace(os.sep, "/")))
            if not any(c.startswith("pkgcode/" + mod) for c in copiados):
                omitidos.append("pkgcode/%s (sin cambios)" % mod)
    return {"copiados": copiados, "omitidos": omitidos}


def bank_libs_delete(name, kind):
    """Elimina del cache una entrada: kind='wheel' -> wheels/<name>;
    kind='pkgcode' -> pkgcode/<name> (modulo completo). Devuelve {ok, deleted}."""
    import shutil as _sh
    if kind == "wheel":
        # name debe ser un basename simple (sin separadores de ruta).
        if not name or "/" in name or "\\" in name or ".." in name:
            raise ValueError("nombre invalido")
        target = os.path.join(_BANK_LIBS_CACHE, "wheels", name)
        if os.path.isfile(target):
            os.remove(target)
            return {"ok": True, "deleted": "wheels/" + name}
    elif kind == "pkgcode":
        if not name or "/" in name or "\\" in name or ".." in name:
            raise ValueError("nombre invalido")
        target = os.path.join(_BANK_LIBS_CACHE, "pkgcode", name)
        if os.path.isdir(target):
            _sh.rmtree(target, ignore_errors=True)
            return {"ok": True, "deleted": "pkgcode/" + name}
    return {"ok": False, "deleted": None}


def bank_lib_verify(name, timeout=300):
    """Instala una mex-lib (sdist del cache) en un venv temporal y comprueba que
    su modulo importe limpio. Devuelve {ok, module, log}. Solo lectura del cache.
    El resultado NO cambia _BANK_PKG_VERIFIED (eso es manual, por seguridad); sirve
    para que el usuario DECIDA con datos si una lib nueva/incompleta ya sirve."""
    import tempfile as _tf
    import shutil as _sh
    import venv as _venv
    whl = os.path.join(_BANK_LIBS_CACHE, "wheels", name or "")
    if not os.path.isfile(whl):
        raise ValueError("no existe en el cache: %r" % name)
    pkg = name.split("-2.")[0] if "-2." in name else name.rsplit("-", 1)[0]
    # Modulo que exporta (p.ej. mex-libextract -> lib_extract).
    mod = None
    for m2, p2 in _BANK_MODULE_TO_PKG.items():
        if p2 == pkg:
            mod = m2
            break
    log = []
    workdir = _tf.mkdtemp(prefix="bnx_banklib_")
    ok = False
    try:
        venv_dir = os.path.join(workdir, ".venv")
        _venv.EnvBuilder(with_pip=True).create(venv_dir)
        py = os.path.join(venv_dir, "bin", "python")
        if not os.path.exists(py):
            py = os.path.join(venv_dir, "Scripts", "python.exe")
        # Instalar deps de prueba (pandas/pyspark/cytoolz) OFFLINE desde el cache
        # local si existe (rapido); si no, por internet. Las mex-lib importan
        # pyspark/pandas en su __init__, por eso hacen falta para probar el import.
        cache_root = _vc.cache_dir()
        links = []
        for sub in ("py38-311", "py312plus",
                    os.path.join("mlops_deps", "py38-311"),
                    os.path.join("mlops_deps", "py312plus"),
                    os.path.join("bank_libs", "wheels")):
            d = os.path.join(cache_root, sub)
            if os.path.isdir(d):
                links += ["--find-links", d]
        log.append("$ pip install pandas pyspark cytoolz %s"
                   % ("(offline desde cache)" if links else "(internet)"))
        base_cmd = [py, "-m", "pip", "install", "-q", "setuptools", "wheel"]
        # Intento 1: OFFLINE con el cache local.
        r1 = _sp.run(base_cmd + links + ["pandas", "pyspark", "cytoolz"],
                     capture_output=True, text=True, timeout=timeout) if links else None
        if r1 is None or r1.returncode != 0:
            # Fallback: por internet (host de desarrollo / server con salida).
            _sp.run(base_cmd + ["pandas", "pyspark", "cytoolz"],
                    capture_output=True, timeout=timeout)
        p = _sp.run([py, "-m", "pip", "install", "--no-build-isolation", whl],
                    capture_output=True, text=True, timeout=timeout)
        log.append((p.stdout or "") + (p.stderr or ""))
        if mod:
            log.append("$ python -c 'import %s'" % mod)
            pe = _sp.run([py, "-c", "import %s; print('IMPORT OK')" % mod],
                         capture_output=True, text=True, timeout=timeout)
            out = (pe.stdout or "") + (pe.stderr or "")
            log.append(out)
            ok = pe.returncode == 0
        else:
            log.append("(no se conoce el modulo de %s; se verifico solo la instalacion)" % pkg)
            ok = p.returncode == 0
    finally:
        _sh.rmtree(workdir, ignore_errors=True)
    return {"ok": ok, "module": mod or pkg, "log": "\n".join(log)}


# --------------------------------------------------------------------------
# Exportar el VENDOR (PySpark + mex-lib + toolbox + deps) como ZIP descargable,
# para montar el entorno virtual en un servidor AISLADO sin internet. Es la
# version 'servida por web' de exportar_vendor.py: el portal arma el ZIP a disco
# y lo sirve por streaming (no carga cientos de MB en memoria).
# --------------------------------------------------------------------------
_VENDOR_EXPORT_DIRS = {
    # serie -> carpetas del cache a incluir (relativas a .bnx_vendor_cache/)
    "all": ["bank_libs", "py38-311", "py312plus", "mlops_deps"],
    "py38-311": ["bank_libs", "py38-311",
                 os.path.join("mlops_deps", "py38-311"),
                 os.path.join("mlops_deps", "py38-311_extra")],
    "py312plus": ["bank_libs", "py312plus",
                  os.path.join("mlops_deps", "py312plus"),
                  os.path.join("mlops_deps", "py312plus_extra")],
}


def export_vendor_zip(out_path, serie="py38-311"):
    """Empaqueta el cache de vendor (.bnx_vendor_cache/) en out_path, filtrando
    por serie de Python del destino. Devuelve {ok, files, bytes, missing}. El ZIP
    se descomprime en el server con importar_vendor.py. Escribe a DISCO (streaming).
    """
    cache = _vc.cache_dir()
    dirs = _VENDOR_EXPORT_DIRS.get(serie, _VENDOR_EXPORT_DIRS["py38-311"])
    n_files, total = 0, 0
    missing = []
    with zipfile.ZipFile(out_path, "w", zipfile.ZIP_STORED, allowZip64=True) as z:
        for d in dirs:
            base = os.path.join(cache, d)
            if not os.path.isdir(base):
                missing.append(d)
                continue
            for root, subdirs, files in os.walk(base):
                subdirs[:] = [s for s in subdirs if s != "__pycache__"]
                for fn in files:
                    if fn.endswith((".pyc", ".pyo")) or fn == ".DS_Store":
                        continue
                    full = os.path.join(root, fn)
                    rel = os.path.relpath(full, cache)
                    arc = os.path.join(".bnx_vendor_cache", rel).replace(os.sep, "/")
                    z.write(full, arc)
                    n_files += 1
                    total += os.path.getsize(full)
    # Incluir el importador dentro del ZIP para que el server lo tenga a mano.
    imp = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                       "importar_vendor.py")
    if os.path.isfile(imp):
        with zipfile.ZipFile(out_path, "a", zipfile.ZIP_DEFLATED, allowZip64=True) as z:
            z.write(imp, "importar_vendor.py")
    return {"ok": n_files > 0, "files": n_files, "bytes": total, "missing": missing}


def vendor_cache_status():
    """Resumen del cache de vendor para la UI: que series de PySpark hay y su
    tamaño. Asi el usuario sabe si puede exportar o si falta poblar el cache."""
    cache = _vc.cache_dir()
    out = {}
    for serie in ("py38-311", "py312plus"):
        sdir = os.path.join(cache, serie)
        has_pyspark, size = False, 0
        if os.path.isdir(sdir):
            for f in os.listdir(sdir):
                if f.endswith(".whl"):
                    fp = os.path.join(sdir, f)
                    size += os.path.getsize(fp)
                    if f.lower().startswith("pyspark-"):
                        has_pyspark = True
        out[serie] = {"has_pyspark": has_pyspark, "bytes": size}
    return out
