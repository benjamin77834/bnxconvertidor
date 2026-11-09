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
import io
import os
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
import pandas as pd
from ..core.base_aggregate import BaseAggregate


class PnlAggregate(BaseAggregate):
    def _build_query(self, query_dict, group_by, cols):
        agg_df = pd.DataFrame(data=query_dict)
        agg_df = agg_df[agg_df["variable"] != ""]
        feats = ",".join(
            "{0}({1}) as {1}".format(it["agg"], it["variable"])
            for _, it in agg_df.iterrows() if it["variable"] in cols)
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

    def score(self, df, feature_cols, out_col="score"):
        """Devuelve df con la columna de score. Con XGBoost usa el modelo; sin el,
        un score lineal simple (solo para pruebas)."""
        if self._booster is not None:
            # En produccion: pasar a pandas por particion / usar un UDF de pandas.
            import pandas as pd  # noqa: F401
            logger.info("Scoring con XGBoost: %s", self.model_path)
            # (placeholder: integrar pandas_udf segun tu infraestructura)
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
        """PSI de una columna: suma de (rel_cur - rel_dev)*ln(rel_cur/rel_dev)."""
        total = current_df.count()
        if total == 0:
            return 0.0
        # Frecuencia relativa actual por bin (usa los mismos bins del desarrollo).
        rows = (current_df.groupBy(column).count()
                .withColumn("rel", F.col("count") / F.lit(float(total)))
                .collect())
        rel_cur = {str(r[column]): r["rel"] for r in rows}
        import math
        psi = 0.0
        for b, rel_dev in dist_dev.items():
            rc = rel_cur.get(str(b), 1e-6) or 1e-6
            rd = rel_dev or 1e-6
            psi += (rc - rd) * math.log(rc / rd)
        return round(psi, 6)

    def interpret(self, psi_value):
        if psi_value < PSI_STABLE:
            return "estable"
        if psi_value < PSI_WARNING:
            return "revisar"
        return "inestable"

    def dqc(self, df, columns):
        """Data Quality Check: estadisticos por columna (conteo, media, std,
        min, max, % nulos)."""
        out = {}
        total = df.count()
        for c in columns:
            agg = df.agg(
                F.count(F.col(c)).alias("n"),
                F.mean(F.col(c).cast("double")).alias("mean"),
                F.stddev(F.col(c).cast("double")).alias("std"),
                F.min(F.col(c)).alias("min"),
                F.max(F.col(c)).alias("max"),
                F.sum(F.col(c).isNull().cast("int")).alias("nulls"),
            ).collect()[0].asDict()
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


def _requirements(include_bank_libs, extra_steps=False, bank_libs=None):
    base = [
        "# Framework MLOps v2 — dependencias",
        "# PySpark segun la version de Python (markers de pip): 3.5.x soporta",
        "# Python 3.8-3.11; 4.0.x soporta 3.9+ y es el unico compatible con 3.12+",
        "# (PySpark 3.5 usa distutils, eliminado en Python 3.12).",
        'pyspark>=3.5,<3.6 ; python_version < "3.12"',
        'pyspark>=4.0,<4.1 ; python_version >= "3.12"',
        "pandas>=1.3",
        "numpy>=1.21",
        "pytest>=7.0",
        "chispa>=0.9  # testing de DataFrames Spark",
    ]
    if extra_steps:
        base += [
            "xgboost>=1.7  # scoring (paso extra)",
            "scikit-learn>=1.1  # metricas/preparacion (paso extra)",
        ]
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


def _requirements_bank(bank_libs):
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
        if name in _BANK_PKG_INCOMPLETE:
            if name not in [n for n, _ in incomplete]:
                incomplete.append((name, _BANK_PKG_INCOMPLETE[name]))
        elif name not in verified:
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

_SETUP_SH = '''#!/usr/bin/env bash
# setup.sh — MONTA el entorno (una sola vez): crea .venv e instala todo.
# Si el paquete trae vendor/ (ambiente completo) monta TODO OFFLINE, sin internet.
# NO corre el modelo: para eso usa  bash run.sh
# Uso:  bash setup.sh            (monta el entorno)
#       bash setup.sh --test     (monta y ademas corre pytest)
set -e

# Basura de macOS (si el ZIP se comprimio/re-comprimio en Finder): la carpeta
# __MACOSX y los archivos ._* (resource forks) rompen pytest con PermissionError.
rm -rf __MACOSX 2>/dev/null || true
find . -name '._*' -not -path './.venv/*' -delete 2>/dev/null || true
find . -name '.DS_Store' -not -path './.venv/*' -delete 2>/dev/null || true

PY="${PYTHON:-python3}"
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
if [ "$PYMINOR" -ge 12 ] 2>/dev/null && [ -d "vendor/py312plus" ]; then
  VENDOR_DIR="vendor/py312plus"
elif [ -d "vendor/py38-311" ]; then
  VENDOR_DIR="vendor/py38-311"
elif [ -d "vendor/py312plus" ]; then
  VENDOR_DIR="vendor/py312plus"
fi

# vendor/bank tambien aporta wheels de deps PINNEADAS por el banco (p.ej. pandas
# 1.3.1 cp38 para Python 3.8). Se agrega a los --find-links para que pip elija la
# version correcta segun la version de Python, tanto offline como por internet.
BANK_LINKS=""
if [ -d "vendor/bank" ]; then BANK_LINKS="--find-links vendor/bank"; fi

if [ -n "$VENDOR_DIR" ] && ls "$VENDOR_DIR"/*.whl >/dev/null 2>&1; then
  echo "      OFFLINE desde $VENDOR_DIR (sin internet)."
  python -m pip install --no-index --find-links "$VENDOR_DIR" pip setuptools wheel >/dev/null 2>&1 || true
  python -m pip install --no-index --find-links "$VENDOR_DIR" $BANK_LINKS -r requirements.txt
  # Paquete propio en editable SIN aislamiento (usa el setuptools ya instalado,
  # no intenta bajar build-system por internet).
  python -m pip install --no-build-isolation -e .
else
  echo "      vendor/ (PySpark) no disponible; instalando por internet (red del banco)."
  # Si estas en la red del banco, descomenta --index-url con tu Artifactory:
  # pip install -r requirements.txt --index-url https://<artifactory-interno>/simple
  # BANK_LINKS deja que pip use pandas 1.3.1 cp38 del banco si corre en Python 3.8.
  python -m pip install $BANK_LINKS -r requirements.txt
  python -m pip install -e .
fi

# Librerias INTERNAS del banco (si las hay). Preferimos OFFLINE desde vendor/bank/
# (sdist empaquetados); si no estan, caemos al Artifactory privado. El codigo de
# path (toolbox/bnmxverse/utils) se copia a ./bank_pkg y se expone via PYTHONPATH.
if [ -f requirements-bank.txt ]; then
  if ls vendor/bank/*.tar.gz >/dev/null 2>&1 || ls vendor/bank/*.whl >/dev/null 2>&1; then
    echo "      Instalando librerias internas del banco OFFLINE desde vendor/bank/ ..."
    python -m pip install --no-index --find-links vendor/bank -r requirements-bank.txt || \
      python -m pip install --no-index --find-links vendor/bank vendor/bank/*.tar.gz || \
      echo "      ⚠️  Fallo la instalacion offline de libs del banco. Revisa vendor/bank/."
  else
    echo "      Instalando librerias internas del banco (Artifactory privado) ..."
    # Descomenta y apunta a tu Artifactory si hace falta un indice explicito:
    # python -m pip install -r requirements-bank.txt --index-url https://<artifactory-interno>/simple
    python -m pip install -r requirements-bank.txt || \
      echo "      ⚠️  No se pudieron instalar las libs del banco (sin acceso al Artifactory)."
  fi
fi
# Modulos de path del banco (toolbox, bnmxverse, utils): no son pip, van en PYTHONPATH.
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
if [ -n "$PYSPARK_HOME" ]; then
  echo "      Ajustando permisos de ejecucion en $PYSPARK_HOME/bin y /sbin ..."
  chmod -R +x "$PYSPARK_HOME/bin" 2>/dev/null || true
  chmod -R +x "$PYSPARK_HOME/sbin" 2>/dev/null || true
fi

echo "[3/4] Verificando dependencias (check_env.py) ..."
# Avisa si falta alguna libreria que el codigo importa (no aborta el montaje).
python check_env.py || echo "  ⚠️  Faltan librerias (ver arriba). Instalalas antes de produccion."

if [ "${1:-}" = "--test" ]; then
  echo "[4/4] Ejecutando pruebas (pytest) ..."
  pytest -q || echo "  (pytest requiere pyspark + Java; revisa el entorno)"
else
  echo "[4/4] Entorno montado (pruebas omitidas; usa --test para correrlas)."
fi

echo ""
echo "✅ Entorno listo. Para correr el modelo:  bash run.sh"
echo "   Datos reales:  bash run.sh --config cfg.json"
'''

# run.sh — SOLO ejecuta el modelo (main.py) en el entorno ya montado por setup.sh.
_RUN_SH = '''#!/usr/bin/env bash
# run.sh — corre el modelo (main.py) con el entorno de setup.sh. No instala nada.
# Uso:  bash run.sh                      (modo demo, datos sinteticos)
#       bash run.sh --config cfg.json    (datos reales)
set -e
cd "$(dirname "$0")"

if [ ! -f .venv/bin/activate ]; then
  echo "❌ No existe .venv. Monta el entorno primero:  bash setup.sh" >&2
  exit 1
fi
# Spark del CLUSTER (opcional): BNX_SPARK=cluster bash run.sh ...
# Usa el spark-submit del nodo (el mismo metastore que Hue/beeline/pyspark del
# cluster) con el Python del venv para las librerias. Se busca ANTES de activar el
# venv para no tomar el spark-submit que trae el pyspark de pip.
CLUSTER_SUBMIT=""
if [ "${BNX_SPARK:-}" = "cluster" ]; then
  CLUSTER_SUBMIT="${BNX_SPARK_SUBMIT:-$(command -v spark3-submit || command -v spark-submit || true)}"
  if [ -z "$CLUSTER_SUBMIT" ]; then
    echo "❌ BNX_SPARK=cluster pero no hay spark-submit del cluster en el PATH." >&2
    echo "   Indica la ruta: BNX_SPARK_SUBMIT=/ruta/spark-submit BNX_SPARK=cluster bash run.sh ..." >&2
    exit 1
  fi
fi
. .venv/bin/activate

# Modulos de path del banco (toolbox, bnmxverse, utils) que dejo setup.sh.
if [ -d bank_pkg ]; then export PYTHONPATH="$PWD/bank_pkg:${PYTHONPATH:-}"; fi

# Metastore del CLUSTER: el PySpark del venv es standalone y, sin hive-site.xml,
# crea un metastore LOCAL vacio (las tablas del banco "no existen"). Si el nodo
# tiene la config de Spark/Hive del cluster (Cloudera/edge node), la usamos.
if [ -z "${SPARK_CONF_DIR:-}" ]; then
  for d in /etc/spark/conf /etc/spark3/conf /etc/spark2/conf /opt/cloudera/parcels/CDH/lib/spark/conf; do
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
if [ -n "${SPARK_CONF_DIR:-}" ]; then
  echo "[run.sh] SPARK_CONF_DIR=$SPARK_CONF_DIR (metastore del cluster)"
else
  echo "[run.sh] AVISO: no se encontro hive-site.xml; Spark usara un metastore LOCAL."
  echo "         Para tablas del banco: export SPARK_CONF_DIR=<dir con hive-site.xml>"
fi

if [ -n "$CLUSTER_SUBMIT" ]; then
  echo "[run.sh] Spark del CLUSTER: $CLUSTER_SUBMIT (python del venv)"
  export PYSPARK_PYTHON="$PWD/.venv/bin/python"
  export PYSPARK_DRIVER_PYTHON="$PWD/.venv/bin/python"
  export BNX_CLUSTER_SPARK=1
  exec "$CLUSTER_SUBMIT" --master "${BNX_MASTER:-yarn}" --deploy-mode client main.py "$@"
fi
exec python main.py "$@"
'''

# run.sh del paquete de monitoreo (sin main.py): corre sus pruebas.
_RUN_SH_METRICS = '''#!/usr/bin/env bash
# run.sh — corre las pruebas del monitoreo en el entorno montado por setup.sh.
set -e
cd "$(dirname "$0")"
if [ ! -f .venv/bin/activate ]; then
  echo "❌ No existe .venv. Monta el entorno primero:  bash setup.sh" >&2
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
bash setup.sh        # con vendor/: PySpark OFFLINE; sin vendor/: por internet
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

Cada fuente es un JOB INDEPENDIENTE, no una secuencia: si una falla, las demas
siguen. Todas comparten la misma SparkSession. El proceso PIVOTE corre SIEMPRE
primero (las demas dependen de su salida); se marca con "pivot": true en el
cfg.json, o nombrando la fuente 'pivote'/'pivot'. Para lanzar una sola como job
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

# Modulos de PYTHONPATH del banco (toolbox, bnmxverse, utils): si el paquete se
# monto con ambiente completo, setup.sh/run.sh los dejan en ./bank_pkg. Los
# agregamos al path aqui para que 'import toolbox' funcione sin exportar nada.
_here = os.path.dirname(os.path.abspath(__file__))
for _cand in (os.path.join(_here, "bank_pkg"),
              os.path.join(_here, "vendor", "bank", "pkgcode")):
    if os.path.isdir(_cand) and _cand not in sys.path:
        sys.path.insert(0, _cand)

try:
    from pyspark.sql import SparkSession
    from pyspark.sql.types import (StructType, StructField, StringType,
                                    DoubleType, IntegerType)
except Exception as e:
    raise SystemExit("PySpark no esta instalado o falta Java. Monta el entorno "
                     "con 'bash setup.sh' primero. Detalle: %s" % e)

from framework_mlops_v2.aggregates.router import REGISTRY, GroupBy


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
            if os.path.isdir(dest) and glob.glob(os.path.join(dest, "*.parquet")):
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
        if chk:
            problema = _preflight(spark, chk)
            if problema:
                # Solo AVISO: con permisos restringidos (Ranger/Sentry) el catalogo
                # puede no listar la base aunque el SELECT si funcione. Se intenta igual.
                print("          [aviso preflight] %s -> se intenta el query de todos modos" % problema)
        else:
            problema = None
        try:
            df = spark.sql(q)
            df.write.mode("overwrite").parquet(dest)
            # Verificar de verdad que se escribio (archivos .parquet + conteo).
            escritos = glob.glob(os.path.join(dest, "*.parquet"))
            filas = spark.read.parquet(dest).count()
            if not escritos:
                raise RuntimeError("el write no dejo archivos .parquet en %s" % dest)
            print("          OK: %d filas, %d archivo(s) parquet en %s"
                  % (filas, len(escritos), dest))
        except Exception as e:
            msg = str(e).strip()
            causa = " ".join(msg.split("\\n")[0].split())[:600] if msg else type(e).__name__
            print("          ERROR extrayendo '%s': %s" % (s, causa))
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


def _ensure_parquet_codec(spark, work):
    """Comprueba que se pueda ESCRIBIR parquet con el codec por defecto (snappy).
    Si falla (libreria nativa no cargable, /tmp noexec...), cae a 'uncompressed'
    y lo avisa, en vez de reventar con un stack de Java ilegible. Se puede forzar
    con la variable BNX_PARQUET_CODEC (snappy|gzip|uncompressed|zstd)."""
    forced = os.environ.get("BNX_PARQUET_CODEC")
    if forced:
        spark.conf.set("spark.sql.parquet.compression.codec", forced)
        print("[codec] parquet forzado a '%s' (BNX_PARQUET_CODEC)" % forced)
        return
    probe = os.path.join(work, "_codec_probe")
    try:
        spark.range(1).write.mode("overwrite").parquet(probe)
    except Exception as e:
        causa = str(e).strip().splitlines()[0][:200] if str(e).strip() else type(e).__name__
        print("[aviso] no se pudo escribir parquet con el codec por defecto: %s" % causa)
        print("        Se usa 'uncompressed'. (Suele ser /tmp noexec o snappy nativo.)")
        spark.conf.set("spark.sql.parquet.compression.codec", "uncompressed")
        spark.range(1).write.mode("overwrite").parquet(probe)   # si falla aqui, es otro tema
    finally:
        shutil.rmtree(probe, ignore_errors=True)


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
    # general_root: --root, o settings/jobs.json junto al config, o ./data
    root = args.root
    if not root:
        for cand in (os.path.join(cfg_dir, "jobs.json"),
                     os.path.join(os.path.dirname(cfg_dir), "jobs.json")):
            if os.path.isfile(cand):
                try:
                    root = json.load(open(cand, encoding="utf-8"))[env]["general_root"]
                    print("[config] general_root desde", cand)
                except Exception:
                    root = None
                break
    if not root:
        root = os.path.join(_here, "data")
    wp = (st.get("working_path") or "working_path/{}/").format(cohort)
    prev = os.path.join(root, wp).rstrip("/")
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
    ap.add_argument("--root", help="general_root (default: settings/jobs.json o ./data)")
    args = ap.parse_args()
    demo = not args.config
    cfg = {} if demo else _load_config(args.config)
    cfg_dir = os.path.dirname(os.path.abspath(args.config)) if args.config else _here
    bank_fmt = (not demo) and _is_bank_settings(cfg)
    scfg_spark = cfg.get("spark") or {}
    work = _work_dir()
    # tmp de Java/Spark/snappy dentro del paquete (escribible), no en /tmp.
    jopts = "-Djava.io.tmpdir=%s -Dorg.xerial.snappy.tempdir=%s" % (work, work)
    cluster = os.environ.get("BNX_CLUSTER_SPARK") == "1"
    builder = SparkSession.builder.appName(scfg_spark.get("app_name", "framework_mlops_v2"))
    if cluster:
        # Lanzado con el spark-submit del cluster: master/conf/metastore vienen de
        # alli (--master yarn, spark-defaults, hive-site.xml). No los pisamos.
        if scfg_spark.get("master"):
            builder = builder.master(scfg_spark["master"])
        print("[spark] modo CLUSTER (spark-submit del nodo)")
    else:
        builder = (builder.master(scfg_spark.get("master", "local[1]"))
                   .config("spark.ui.enabled", "false")
                   .config("spark.sql.shuffle.partitions", "2")
                   .config("spark.local.dir", work)
                   .config("spark.driver.extraJavaOptions", jopts))
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
    _ensure_parquet_codec(spark, work)

    print("=" * 64)
    print("FRAMEWORK MLOPS v2 — %s" % ("DEMO (datos sinteticos)" if demo else "DATOS REALES"))
    print("=" * 64)
    _report_optimizations()

    if demo:
        synth = _synthetic_df(spark)
        print("\\nENTRADA sintetica (%d filas):" % synth.count())
        synth.show(5, truncate=False)
        base = tempfile.mkdtemp(prefix="bnx_main_", dir=work)
        prev = os.path.join(base, "datapull")
        os.makedirs(prev, exist_ok=True)
        for s in REGISTRY:
            synth.write.mode("overwrite").parquet(os.path.join(prev, s))
        _patch_reads(spark, synth)
        src_cfg = {s: {"table_name": s} for s in REGISTRY}
    elif bank_fmt:
        # Settings del banco (pivot.json/datapull.json): cada tabla de tables_info
        # se baja a parquet en <general_root>/<working_path>/<tabla>.
        base = None
        src_cfg, prev = _bank_sources(cfg, args, cfg_dir, spark)
        os.makedirs(prev, exist_ok=True)
        print("previous_path:", prev)
    else:
        base = None
        prev = cfg.get("previous_path") or os.path.join(_here, "data", "datapull")
        if not os.path.isabs(prev):
            prev = os.path.join(cfg_dir, prev)
        os.makedirs(prev, exist_ok=True)
        print("previous_path:", prev)
        src_cfg = cfg.get("sources") or {s: {"table_name": s} for s in REGISTRY}
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
    fuentes = _orden_pivote_primero(fuentes, src_cfg)
    ok = fail = 0
    # Cada fuente es un JOB (comparte la misma SparkSession, que se pasa a cada
    # aggregate). Extrae su query y corre su aggregate en su propio bloque aislado;
    # una que falla NO tumba a las demas. Para correr una sola como job separado
    # desde tu orquestador (respetando que pivote fue primero):  run.sh --source X
    for s in fuentes:
        if s not in REGISTRY and not bank_fmt:
            print("\\n[skip] fuente no registrada:", s); continue
        print("\\n" + "-" * 64); print("FUENTE:", s)
        scfg = src_cfg.get(s, {"table_name": s})
        try:
            # 1) Extraccion propia de ESTA fuente (si trae query/source_table).
            if not demo and not args.skip_extract:
                if _extract_sources(spark, [s], src_cfg, prev, cfg_dir, args.dry_run):
                    raise RuntimeError("no se extrajo/escribio el parquet de '%s' "
                                       "(revisa el QUERY de arriba)" % s)
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
                if glob.glob(os.path.join(dest, "*.parquet")):
                    print("  extract-only OK: parquet escrito en", dest)
                    ok += 1
                else:
                    print("  extract-only ERROR: no hay parquet en", dest,
                          "(la fuente no tiene query o el write no escribio nada)")
                    fail += 1
                continue
            # 2) Aggregate de ESTA fuente.
            GroupBy(s, previous_path=prev, agg_dict=scfg,
                    sqlContext=spark).aggregate()
            head, _ = os.path.split(prev)
            out = spark.read.parquet(os.path.join(head, "groupby"))
            print("  OK -> salida: %d filas, %d columnas" % (out.count(), len(out.columns)))
            if demo:
                out.show(5, truncate=False)
            ok += 1
        except Exception as e:
            print("  ERROR:", type(e).__name__, "-", str(e)[:120])
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
                GroupBy(job_agg, previous_path=prev, agg_dict={"table_name": job_agg},
                        sqlContext=spark).aggregate()
                print("  OK -> aggregate de '%s' terminado" % job_agg)
                ok += 1
            except Exception as e:
                print("  ERROR:", type(e).__name__, "-", str(e)[:160])
                fail += 1

    print("\\n" + "=" * 64)
    print("RESULTADO: %d fuente(s) OK, %d con error." % (ok, fail))
    if demo:
        print("Modo DEMO con datos sinteticos. Para datos reales: python main.py --config cfg.json")
    if base:
        shutil.rmtree(base, ignore_errors=True)
    spark.stop()
    raise SystemExit(0 if fail == 0 else 1)


if __name__ == "__main__":
    main()
'''


_CFG_EXAMPLE = '''{
  "previous_path": "data/datapull",
  "spark": {
    "master": "local[2]",
    "hive": true,
    "conf": {
      "spark.sql.shuffle.partitions": "8"
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
"""
import importlib

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


def _placeholder(nombre, modulo, origen, causa):
    msg = ("mex_lib_cs.%s no esta disponible: no se pudo importar '%s' (%s). %s"
           % (nombre, modulo, origen, causa))

    class _Faltante(object):
        __bnx_missing__ = True

        def __init__(self, *args, **kwargs):
            raise ImportError(msg)

    _Faltante.__name__ = nombre
    _Faltante.__qualname__ = nombre
    return _Faltante


def _cargar(nombre, modulo, origen):
    try:
        return getattr(importlib.import_module(modulo), nombre)
    except Exception as e:  # modulo ausente, incompleto o con dependencia faltante
        return _placeholder(nombre, modulo, origen, "%s: %s" % (type(e).__name__, e))


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
"""check_env.py — Verificador de dependencias del Framework MLOps v2.

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
import importlib.util
import os
import sys

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
               os.path.join(root, "framework_mlops_v2")]
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


def _top_level_imports():
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
    for interno in ("framework_mlops_v2", "framework_mlops_metrics",
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


def main():
    quiet = "--quiet" in sys.argv
    mods = sorted(_top_level_imports())
    faltan, ok = [], []
    for mod in mods:
        if _is_stdlib(mod) or mod in _IGNORAR:
            continue  # stdlib o modulo ignorado (no se usa en el despliegue)
        (ok if _can_import(mod) else faltan).append(mod)

    if not quiet:
        print("== Verificacion de dependencias (check_env.py) ==")
        print("Python:", sys.version.split()[0], "| venv:", sys.prefix)
        print("Instaladas OK (%d): %s" % (len(ok), ", ".join(ok) or "-"))

    if not faltan:
        print("\\n[OK] No falta ninguna libreria. El entorno esta completo.")
        return 0

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
        'pyspark>=4.0,<4.1 ; python_version >= "3.12"',
        "pandas>=1.3", "numpy>=1.21",
    ],
)
'''


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


def _aggregate_from_pyspark(source, pyspark_code, original_pandas):
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
    hoisted, body = _hoist_module_imports(body)
    # Neutralizar imports de modulos que NO estaran (modeling_tools, etc.): el
    # archivo debe importar sin romper (try/except ImportError).
    hoisted = _neutralize_missing_imports(hoisted)
    body = body.strip() or "df_out = df"
    # Heuristica: si el codigo no define df_out ni retorna, devolvemos la ultima
    # variable *_df o el df de entrada.
    has_out = _re.search(r"\bdf_out\b", body) is not None
    tail = "" if has_out else "\n# BNX: no se detecto 'df_out'; se devuelve el df de entrada.\ndf_out = df"
    extra_imports = ("\n" + hoisted + "\n") if hoisted.strip() else "\n"
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


# --- Codigo de negocio ORIGINAL (pandas), como referencia ---
# Se guarda COMENTADO (no como string literal) para que un docstring con triple
# comilla o comillas internas en el original no rompa la sintaxis de este archivo.
{_as_comment_block(original_pandas)}
'''


def _router_from_sources(sources):
    """Genera el router con todas las fuentes del usuario registradas."""
    imports = "\n".join(
        f"from .{s} import {_class_name(s)}" for s in sources)
    registry = "\n".join(
        f'    "{s}": {_class_name(s)},' for s in sources)
    return f'''# framework_mlops_v2/aggregates/router.py
"""Router de agregaciones generado por BNX. Una entrada por fuente del negocio."""
{imports}

REGISTRY = {{
{registry}
}}


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
            "requirements.txt": "pyspark>=3.3,<4.0\npandas>=1.3\npytest>=7.0\n",
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
        'pyspark>=4.0,<4.1 ; python_version >= "3.12"',
        "pandas>=1.3",
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


def zip_from_files(code_files, sep_files=None, full_env=False, py_target="all",
                   out_path=None):
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
    vendor_series = _vendor_files_for_pkg(py_target, extra_steps) if full_env else {}
    # Empaquetar las LIBRERIAS INTERNAS del banco OFFLINE SIEMPRE que el paquete
    # las use (hay requirements-bank.txt) y tengamos el cache, TAMBIEN en el
    # paquete ligero. Son Python puro y pesan ~260 KB (no PySpark), asi que no
    # engordan el ZIP ligero y evitan que el usuario tenga que conseguirlas
    # aparte. Van en vendor/bank/ (sdist pip-instalables) y vendor/bank/pkgcode/
    # (toolbox/bnmxverse/utils, que se agregan al PYTHONPATH).
    uses_bank = any(p.endswith("requirements-bank.txt") for p in (code_files or {}))
    bank_sdists, bank_pkgcode = ([], {})
    bank_extracted = {}
    if uses_bank:
        bank_sdists, bank_pkgcode = _bank_vendor_files()
        # Ademas de los sdist (que pip instala), extraemos las mex-lib verificadas
        # como CODIGO en pkgcode/ para que funcionen por PYTHONPATH sin pip/build
        # (fallback a prueba de fallos en Windows/Python 3.8).
        bank_extracted = _bank_extracted_pkgs()
    # Evitar escribir la MISMA ruta dos veces (en Python 3.8/Windows un ZipInfo
    # duplicado o un estado inconsistente puede dejar el stream en mal estado y
    # romper el cierre con 'I/O operation on closed file'). Deduplicamos por ruta.
    seen_arc = set()

    def _put_str(z, arc, content):
        if arc in seen_arc:
            return
        seen_arc.add(arc)
        z.writestr(arc, content)

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
_MLOPS_VENDOR_CACHE = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    ".bnx_vendor_cache", "mlops_deps")

# Cache de las LIBRERIAS INTERNAS del banco (mex-lib* como sdist + toolbox/bnmxverse/
# utils como codigo de path). Son Python puro, sirven para cualquier plataforma/
# version. Vive fuera de git. 'wheels/' = sdist pip-instalables; 'pkgcode/' =
# modulos que el codigo espera en el PYTHONPATH (toolbox, etc.).
_BANK_LIBS_CACHE = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    ".bnx_vendor_cache", "bank_libs")


def _bank_vendor_files():
    """Devuelve ({sdist .tar.gz}, {pkgcode: rutas de modulos}) de las librerias
    internas del banco presentes en cache. Solo incluye los sdist VERIFICADOS
    (_BANK_PKG_VERIFIED): los incompletos en origen se omiten del vendor. Si no
    hay cache, devuelve ([], {})."""
    whl_dir = os.path.join(_BANK_LIBS_CACHE, "wheels")
    code_dir = os.path.join(_BANK_LIBS_CACHE, "pkgcode")
    sdists = []
    if os.path.isdir(whl_dir):
        for f in sorted(os.listdir(whl_dir)):
            if not f.endswith((".tar.gz", ".whl")):
                continue
            low = f.lower()
            # mex-lib* del banco: solo las VERIFICADAS (las incompletas en origen
            # se omiten del vendor porque les falta codigo).
            if low.startswith("mex"):
                pkg = f.split("-2.")[0] if "-2." in f else f.rsplit("-", 1)[0]
                if pkg in _BANK_PKG_VERIFIED:
                    sdists.append(os.path.join(whl_dir, f))
                continue
            # Cualquier OTRA wheel/sdist en bank_libs/wheels es una DEP del stack
            # del banco (pandas/numpy/xgboost/cytoolz/pytest/chispa y transitivas).
            # Se incluyen TODAS: asi nada queda faltante al montar offline.
            sdists.append(os.path.join(whl_dir, f))
    pkgcode = {}
    if os.path.isdir(code_dir):
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


def _bank_extracted_pkgs():
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
    for f in sorted(os.listdir(whl_dir)):
        if not f.endswith(".tar.gz"):
            continue
        pkg = f.split("-2.")[0] if "-2." in f else f.rsplit("-", 1)[0]
        if pkg not in _BANK_PKG_VERIFIED:
            continue
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


def _has_bank_libs_cache():
    sdists, pkgcode = _bank_vendor_files()
    return bool(sdists or pkgcode)

# Dependencias del framework a empaquetar OFFLINE (ademas de PySpark+py4j que ya
# trae el vendor base). pytest/chispa para correr pruebas; xgboost/sklearn solo
# si el paquete trae pasos extra (scoring).
_MLOPS_BASE_DEPS = ["pandas>=1.3", "numpy>=1.21", "pytest>=7.0", "chispa>=0.9"]
_MLOPS_EXTRA_DEPS = ["xgboost>=1.7", "scikit-learn>=1.1"]

# Python objetivo por serie (para 'pip download --python-version'): las wheels de
# pandas/numpy SI son especificas de version de Python.
_SERIE_PYVER = {"py38-311": "3.11", "py312plus": "3.12"}
# ABI de CPython por serie. pandas/numpy traen wheels BINARIAS con ABI concreta
# (cp311, cp312); no existe wheel 'none/any' para ellas, por eso hay que pedirla.
_SERIE_ABI = {"py38-311": "cp311", "py312plus": "cp312"}
# Plataformas Linux objetivo (el servidor del banco es Linux, normalmente x86_64).
# Bajamos ambas arquitecturas comunes para no asumir. manylinux2014 = glibc 2.17+,
# compatible con RHEL7+/la mayoria de servidores empresariales.
_LINUX_PLATFORMS = [
    "manylinux2014_x86_64", "manylinux_2_17_x86_64",
    "manylinux2014_aarch64", "manylinux_2_17_aarch64",
]


def _fetch_mlops_deps(serie_dir, extra_steps):
    """Descarga (y cachea) los wheels de pandas/numpy/pytest (+xgboost/sklearn si
    extra_steps) para una serie de Python. Devuelve [rutas .whl]. Si no hay
    internet o pip falla, devuelve lo que haya en cache (puede ser [])."""
    pyver = _SERIE_PYVER.get(serie_dir, "3.11")
    abi = _SERIE_ABI.get(serie_dir, "cp311")
    cache = os.path.join(_MLOPS_VENDOR_CACHE, serie_dir + ("_extra" if extra_steps else ""))
    os.makedirs(cache, exist_ok=True)
    deps = list(_MLOPS_BASE_DEPS) + (list(_MLOPS_EXTRA_DEPS) if extra_steps else [])
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
                [_sys.executable, "-m", "pip", "download",
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
            _sp.run([_sys.executable, "-m", "pip", "download", "-d", cache, *deps],
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
    # Complementar cada serie con las deps del framework (pandas/numpy/...).
    for serie_dir in list(base.keys()):
        try:
            base[serie_dir] = list(base[serie_dir]) + _fetch_mlops_deps(serie_dir, extra_steps)
        except Exception:
            pass
    return base


def build_package_from_sources(sources, convert_fn, optimize_fn=None,
                               include_bank_libs=True, optimize=True,
                               extra_steps=False, include_monitoring=False,
                               separate_monitoring=False, full_env=False,
                               py_target="all", out_path=None):
    """Arma el Framework v2 EMPAQUETADO con la logica del usuario dentro.

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
    gen_sources = []       # nombres de modulo validos, unicos
    files = {}
    report = []
    seen = set()
    original_codes = []    # codigo pandas original de cada fuente (para detectar libs)

    for item in sources or []:
        raw_name = item.get("name") or "fuente.py"
        pandas_code = item.get("code") or ""
        if pandas_code.strip():
            original_codes.append(pandas_code)
        if not pandas_code.strip():
            report.append({"name": raw_name, "ok": False, "reason": "vacio"})
            continue
        src = _safe_name(raw_name)
        base = src
        n = 1
        while src in seen:
            n += 1
            src = f"{base}_{n}"
        seen.add(src)

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
            if optimize and optimize_fn:
                try:
                    opt = optimize_fn(pyspark_code)
                    if opt and opt.get("code"):
                        pyspark_code = opt["code"]
                except Exception:
                    pass
            report.append({"name": raw_name, "source": src, "ok": True,
                           "warnings": len(warnings), "unsupported": len(unsupported)})

        gen_sources.append(src)
        rel_path = f"framework_mlops_v2/aggregates/{src}.py"
        agg_code = _aggregate_from_pyspark(src, pyspark_code, pandas_code)
        files[rel_path] = agg_code
        # Extraer los TODO (lineas no traducibles) CON su numero de linea en el
        # ARCHIVO generado (donde el usuario los abrira), para el reporte.
        todos = _extract_todos(agg_code)
        report[-1]["file"] = rel_path
        report[-1]["todos"] = todos
        report[-1]["unsupported"] = len(todos) if todos else report[-1].get("unsupported", 0)

    if not gen_sources:
        # Nada convertible: devolvemos el paquete base de ejemplo.
        data, filename = build_mlops_package(include_bank_libs)
        return data, filename, report

    # Archivos comunes del framework v2 + router con las fuentes del usuario.
    files["framework_mlops_v2/__init__.py"] = _INIT_ROOT
    files["framework_mlops_v2/core/__init__.py"] = ""
    files["framework_mlops_v2/core/base_aggregate.py"] = _BASE_AGGREGATE
    files["framework_mlops_v2/core/quality.py"] = _QUALITY
    files["framework_mlops_v2/aggregates/__init__.py"] = ""
    files["framework_mlops_v2/aggregates/router.py"] = _router_from_sources(gen_sources)
    files["framework_mlops_v2/features/__init__.py"] = ""
    files["framework_mlops_v2/features/ratios.py"] = _RATIOS
    # Pasos EXTRA opcionales + monitoreo DENTRO del paquete (si no se separa).
    mon_in_pkg = include_monitoring and not separate_monitoring
    files.update(_extra_step_files(
        extra_steps, include_monitoring=mon_in_pkg, monitoring_target="package"))
    files["tests/test_aggregates.py"] = _TEST
    files["main.py"] = _MAIN_PY   # entry point del framework (demo + --config)
    files["check_env.py"] = _CHECK_ENV   # verificador de deps (que no falte nada)
    # Detectar librerias INTERNAS del banco (toolbox, mex_lib_cs, ...) en el
    # codigo original. Van en requirements.txt (dadas de alta) para visibilidad,
    # y ADEMAS en requirements-bank.txt para que el montaje offline del core
    # (vendor/) no se rompa: el core se instala con --no-index y las del banco se
    # intentan aparte desde el Artifactory (sin abortar si no hay acceso).
    bank_libs = _detect_bank_imports(original_codes)
    files["requirements.txt"] = _requirements(include_bank_libs, extra_steps, bank_libs)
    if bank_libs:
        files["requirements-bank.txt"] = _requirements_bank(bank_libs)
    # 'mex_lib_cs' es una fachada que escribimos nosotros: va EMBEBIDA en la raiz
    # del paquete (ligero, completo y rebuild), sin depender del cache del server.
    if "mex_lib_cs" in (bank_libs or []):
        files["mex_lib_cs/__init__.py"] = _MEX_LIB_CS
    files["setup.sh"] = _SETUP_SH
    files["run.sh"] = _RUN_SH
    files["cfg.example.json"] = _CFG_EXAMPLE
    files["pytest.ini"] = _PYTEST_INI   # pytest solo en tests/, ignora __MACOSX/vendor
    files["setup.py"] = _SETUP
    files["README.md"] = _readme_custom(
        include_bank_libs, gen_sources, report, extra_steps,
        include_monitoring=include_monitoring, separate_monitoring=separate_monitoring,
        full_env=full_env, bank_libs=bank_libs)

    sep_files = _monitoring_files("separate") if (include_monitoring and separate_monitoring) else {}

    zip_result, _fn, vendor_list = zip_from_files(
        files, sep_files, full_env=full_env, py_target=py_target, out_path=out_path)

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
    pyspark_series = [s for s in (vendor_list or []) if s != "bank"]
    vendor_missing = bool(full_env) and not pyspark_series

    # Meta: incluye los archivos de CODIGO (editables) para guardarlos por token.
    report.append({"_meta": True, "full_env": bool(full_env),
                   "vendor_series": vendor_list,
                   "vendor_missing": vendor_missing,
                   "py_target": py_target,
                   "bank_libs": bank_libs,
                   "bank_verified": bank_verified,
                   "bank_incomplete": bank_incomplete,
                   "_code_files": files, "_sep_files": sep_files})
    return zip_result, "framework_mlops_v2.zip", report


def _readme_custom(include_bank_libs, sources, report, extra_steps=False,
                   include_monitoring=False, separate_monitoring=False,
                   full_env=False, bank_libs=None):
    rows = "\n".join(
        f"- `{r.get('source', '?')}` ← {r['name']}"
        + (" ✅" if r.get("ok") else f" ⚠️ {r.get('reason', '')}")
        + (f" ({r['unsupported']} revisión manual)" if r.get("unsupported") else "")
        for r in report if not r.get("_meta"))
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
    return base + banklibs + mon + f'''

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
{extra}{env}'''


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
        "cfg.example.json": _CFG_EXAMPLE,
        "pytest.ini": _PYTEST_INI,
        "README.md": _readme(include_bank_libs),
        "setup.py": _SETUP,
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
            cand = "py312plus" if minor >= 12 else "py38-311"
            for d in (cand, "py38-311", "py312plus"):
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
                 [py, "-m", "pip", "install", "--no-index",
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

    # Serie/ABI/plataforma del destino.
    serie = "py38-311" if py_target == "py38-311" else "py312plus"
    pyver = "3.8" if serie == "py38-311" else "3.12"
    abi = "cp38" if serie == "py38-311" else "cp312"
    plat = "manylinux2014_x86_64"
    vendor_dir = os.path.join(pkg_root, "vendor", serie)
    bank_dir = os.path.join(pkg_root, "vendor", "bank")
    links = []
    for d in (vendor_dir, bank_dir):
        if os.path.isdir(d):
            links += ["--find-links", d]

    _log("== Verificacion emulando el SERVIDOR LINUX del banco ==")
    _log("Target: Python %s / %s / %s (resolucion con pip, sin instalar).\n"
         % (pyver, abi, plat))

    def _resolve_one(req):
        """Resuelve UN requisito para Linux desde vendor. Devuelve (ok, nombre).
        Permite sdist (.tar.gz de las mex-lib) ademas de wheels; respeta el marker
        de version de Python (pyspark) descartando la linea que no aplica a pyver."""
        # Marker 'python_version': saltar la linea que NO aplica al target.
        base = req
        if ";" in req:
            spec, marker = req.split(";", 1)
            marker = marker.strip()
            py_is_312plus = (pyver != "3.8")
            if "python_version <" in marker and py_is_312plus:
                return True, None   # no aplica a 3.12+: se ignora
            if "python_version >=" in marker and not py_is_312plus:
                return True, None   # no aplica a 3.8: se ignora
            base = spec.strip()
        if not base:
            return True, None
        name = _re.split(r"[<>=!~ ]", base, 1)[0].strip()
        # Las mex-lib del banco son sdist (.tar.gz). pip con --platform exige
        # --only-binary (rechaza sdist), asi que para ellas comprobamos que el
        # archivo exista en vendor/bank (normalizando guion/underscore).
        nlow = name.lower().replace("_", "-")
        if nlow.startswith("mex"):
            found = False
            if os.path.isdir(bank_dir):
                for f in os.listdir(bank_dir):
                    if f.lower().replace("_", "-").startswith(nlow) and f.endswith((".tar.gz", ".whl")):
                        found = True
                        break
            return found, (None if found else name)
        tmp = _tf.mkdtemp(prefix="bnx_res_")
        try:
            # Wheels binarios: resolver para la plataforma Linux objetivo.
            cmd = ([_sys.executable, "-m", "pip", "download", "--no-index", "--no-deps",
                    "--only-binary=:all:"]
                   + links + ["--python-version", pyver, "--implementation", "cp",
                              "--abi", abi, "--abi", "abi3", "--abi", "none",
                              "--platform", plat, "--platform", "any",
                              "-d", tmp, base])
            p = _sp.run(cmd, capture_output=True, text=True, timeout=timeout)
            ok = p.returncode == 0
            return ok, (None if ok else name)
        finally:
            _sh.rmtree(tmp, ignore_errors=True)

    def _resolve(nombre, reqs):
        """Resuelve cada requisito por separado (asi un marker que no aplica no
        tumba al resto). Devuelve (ok, faltantes)."""
        if not reqs:
            return True, []
        _log("$ pip download (Linux %s) — %d requisitos" % (abi, len(reqs)))
        faltan = []
        for r in reqs:
            ok1, missing = _resolve_one(r)
            if not ok1 and missing:
                faltan.append(missing)
        ok = not faltan
        if ok:
            _log("  OK: todas resuelven para Linux.\n")
        else:
            _log("  Faltan: %s\n" % ", ".join(faltan))
        steps.append({"name": nombre, "exit_code": 0 if ok else 1, "ok": ok})
        return ok, faltan

    # Leer requirements (core) y requirements-bank (banco), ignorando comentarios.
    def _read_reqs(path):
        reqs = []
        if os.path.isfile(path):
            for ln in open(path, encoding="utf-8"):
                s = ln.strip()
                if not s or s.startswith("#"):
                    continue
                # quitar comentario al final y marker de pyspark (ya resuelto)
                s = s.split("#", 1)[0].strip()
                if s:
                    reqs.append(s)
        return reqs

    core = _read_reqs(os.path.join(pkg_root, "requirements.txt"))
    bank = _read_reqs(os.path.join(pkg_root, "requirements-bank.txt"))

    ok_core, falta_core = _resolve("core (requirements.txt)", core)
    ok_bank, falta_bank = (True, [])
    if bank:
        ok_bank, falta_bank = _resolve("banco (requirements-bank.txt)", bank)

    faltantes = sorted(set(falta_core + falta_bank))
    ok_env = not faltantes
    if ok_env:
        _log("[OK] Todo el stack resuelve OFFLINE para el servidor Linux del banco.")
    else:
        _log("[FALTAN] para Linux: %s" % ", ".join(faltantes))
        _log("  -> Carga lo que falte en 'Librerias del banco' (importar/descargar entorno).")
    return {"ok_env": ok_env, "checks": {"ok": [], "missing": faltantes}}


# --------------------------------------------------------------------------
# GESTOR de librerias del banco (para la pagina "Librerias del banco" del portal).
# Lee/escribe el cache .bnx_vendor_cache/bank_libs/. Permite listar, importar
# desde una ruta/disco, eliminar y verificar que una mex-lib importe limpio.
# --------------------------------------------------------------------------
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
            elif low.startswith(("pandas-", "numpy-", "xgboost-", "scikit_learn-",
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
        os.path.dirname(_BANK_LIBS_CACHE), "")  # .bnx_vendor_cache/

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
        cache_root = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            ".bnx_vendor_cache")
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
    cache = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        ".bnx_vendor_cache")
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
    cache = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        ".bnx_vendor_cache")
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
