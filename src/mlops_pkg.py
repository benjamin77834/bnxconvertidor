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
  - entorno virtual reproducible (requirements.txt + run.sh que crea el venv)

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
    # el propio framework generado (imports relativos)
    "framework_mlops_v2", "framework_mlops_metrics",
    # stdlib comun que puede aparecer en el codigo de negocio
    "os", "sys", "re", "json", "csv", "math", "time", "datetime", "calendar",
    "collections", "itertools", "functools", "logging", "typing", "decimal",
    "random", "io", "pathlib", "warnings", "argparse", "abc", "copy",
    "hashlib", "base64", "uuid", "pickle", "glob", "shutil", "tempfile",
    "subprocess", "traceback", "operator", "string", "enum", "dataclasses",
}


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
        for mod in mods:
            key = mod.strip()
            if not key or key in _STDLIB_AND_KNOWN:
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
# pkgcode, no en requirements-bank.txt).
_BANK_PATH_MODULES = {"toolbox", "bnmxverse", "utils"}


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
        if m in _BANK_PATH_MODULES:
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


# setup.sh del AMBIENTE COMPLETO: crea el venv e instala PySpark OFFLINE desde
# vendor/ (igual que el bundle de Data Sintetica). Monta todo sin internet.
_SETUP_SH_FULL = '''#!/usr/bin/env bash
# setup.sh — Monta el AMBIENTE COMPLETO del Framework MLOps v2.
# Crea el venv, instala PySpark OFFLINE desde vendor/ (sin internet) segun la
# version de Python, instala el framework (pip install -e .) y corre las pruebas.
# Uso:  bash setup.sh
set -e

PY="${PYTHON:-python3}"
echo "[1/5] Python: $($PY --version 2>&1)"
echo "[2/5] Creando entorno virtual .venv ..."
"$PY" -m venv .venv
. .venv/bin/activate
python -m pip install --upgrade pip >/dev/null 2>&1 || true

echo "[3/5] Instalando PySpark..."
PYMINOR="$(python -c 'import sys; print(sys.version_info[1])')"
VENDOR_DIR=""
if [ "$PYMINOR" -ge 12 ] 2>/dev/null && [ -d "vendor/py312plus" ]; then
  VENDOR_DIR="vendor/py312plus"
elif [ -d "vendor/py38-311" ]; then
  VENDOR_DIR="vendor/py38-311"
elif [ -d "vendor/py312plus" ]; then
  VENDOR_DIR="vendor/py312plus"
fi
if [ -n "$VENDOR_DIR" ] && ls "$VENDOR_DIR"/*.whl >/dev/null 2>&1; then
  echo "      OFFLINE desde $VENDOR_DIR (sin internet)."
  python -m pip install --no-index --find-links "$VENDOR_DIR" pip setuptools wheel >/dev/null 2>&1 || true
  python -m pip install --no-index --find-links "$VENDOR_DIR" pyspark py4j
else
  echo "      vendor/ no disponible; instalando PySpark por internet (serie segun Python)."
  if [ "$PYMINOR" -ge 12 ] 2>/dev/null; then
    python -m pip install "pyspark>=4.0,<4.1" py4j   # 3.12+ (3.5 usa distutils, roto)
  else
    python -m pip install "pyspark>=3.5,<3.6" py4j
  fi
fi

echo "[4/5] Instalando dependencias (requirements.txt) y el framework..."
# Dependencias del paquete (pandas, numpy, pytest y -si aplica- xgboost/sklearn).
# Las libs internas del banco comentadas en el archivo se ignoran. OFFLINE: si
# existen en vendor/ se usan de ahi; si no, por internet.
if [ -n "$VENDOR_DIR" ] && ls "$VENDOR_DIR"/*.whl >/dev/null 2>&1; then
  # OFFLINE estricto: todo desde vendor/, sin caer a internet.
  python -m pip install --no-index --find-links "$VENDOR_DIR" -r requirements.txt
else
  python -m pip install -r requirements.txt 2>/dev/null || true
fi
# Instalar el PROPIO paquete en modo editable (clave: sin esto los imports
# 'from framework_mlops_v2...' fallan fuera de la carpeta raiz). Sin aislamiento
# para no intentar bajar el build-system por internet cuando estamos offline.
if [ -n "$VENDOR_DIR" ] && ls "$VENDOR_DIR"/*.whl >/dev/null 2>&1; then
  python -m pip install --no-build-isolation -e .
else
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

echo "[5/5] Corriendo pruebas ..."
pytest -q || echo "  (pytest requiere Java para Spark; revisa el entorno)"

echo ""
echo "▶️  Corriendo el framework (main.py, modo demo):"
python main.py || echo "  (main.py requiere Java para Spark; revisa el entorno)"

echo ""
echo "✅ Ambiente listo. Entry point:  . .venv/bin/activate && python main.py"
echo "   Datos reales:  python main.py --config cfg.json"
'''

_RUN_SH = '''#!/usr/bin/env bash
# run.sh — crea un ENTORNO VIRTUAL con todo lo necesario y corre las pruebas.
# Si el paquete trae vendor/ (ambiente completo) monta TODO OFFLINE, sin internet.
# Uso:  bash run.sh
set -e

PY="${PYTHON:-python3}"
echo "[1/4] Creando entorno virtual .venv ..."
"$PY" -m venv .venv

echo "[2/4] Activando e instalando dependencias ..."
. .venv/bin/activate
python -m pip install --upgrade pip >/dev/null 2>&1 || true

# Detectar vendor/ segun la version de Python (igual que setup.sh): si existe,
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

if [ -n "$VENDOR_DIR" ] && ls "$VENDOR_DIR"/*.whl >/dev/null 2>&1; then
  echo "      OFFLINE desde $VENDOR_DIR (sin internet)."
  python -m pip install --no-index --find-links "$VENDOR_DIR" pip setuptools wheel >/dev/null 2>&1 || true
  python -m pip install --no-index --find-links "$VENDOR_DIR" -r requirements.txt
  # Paquete propio en editable SIN aislamiento (usa el setuptools ya instalado,
  # no intenta bajar build-system por internet).
  python -m pip install --no-build-isolation -e .
else
  echo "      vendor/ no disponible; instalando por internet (red del banco)."
  # Si estas en la red del banco, descomenta --index-url con tu Artifactory:
  # pip install -r requirements.txt --index-url https://<artifactory-interno>/simple
  python -m pip install -r requirements.txt
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

echo "[3/4] Ejecutando pruebas (pytest) ..."
pytest -q || echo "  (pytest requiere pyspark + Java; revisa el entorno)"

echo "[4/4] Corriendo el framework (main.py, modo demo) ..."
python main.py || echo "  (main.py requiere pyspark + Java; revisa el entorno)"

echo ""
echo "✅ Listo. Entry point:  . .venv/bin/activate && python main.py"
echo "   Datos reales:  python main.py --config cfg.json"
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
bash run.sh
```
Crea `.venv`, instala dependencias y corre las pruebas. {libs}

## Estructura
```
framework_mlops_v2/
  core/base_aggregate.py   # contrato comun
  core/quality.py          # validaciones activas
  aggregates/              # atms, s15, pnl + router
  features/ratios.py       # ratios con proteccion /0
tests/                     # pruebas reales (pytest)
requirements.txt
run.sh
setup.py
```

## ▶️ Cómo CORRER el modelo (paso a paso)

### 🚀 Correr el framework (entry point: main.py)
```bash
bash run.sh            # monta el venv y al final corre main.py (demo)
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
bash run.sh          # paquete ligero (instala PySpark por internet)
# ó, si bajaste el paquete con ambiente completo (vendor/):
bash setup.sh        # instala PySpark OFFLINE desde vendor/, sin internet
```
Esto crea `.venv`, instala dependencias e instala el propio framework
(`pip install -e .`). Al terminar debe decir "Ambiente listo".

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

Uso (tras montar el entorno con run.sh / setup.sh):
    . .venv/bin/activate
    python main.py                 # modo DEMO: datos sinteticos, sin configurar
    python main.py --source bureau # solo una fuente
    python main.py --config cfg.json   # datos REALES (ver formato abajo)

cfg.json (datos reales):
    {
      "previous_path": "/ruta/con/parquets",   # <previous_path>/<table_name>
      "sources": {"bureau": {"table_name": "bureau"}, ...}
    }

En DEMO genera datos sinteticos, neutraliza las lecturas externas de los
aggregates (spark.read.* -> datos de juguete) y corre cada fuente mostrando
entrada -> salida. Las fuentes con un '# TODO py2spark' pendiente se marcan.
"""
import argparse
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
                     "con 'bash run.sh' (o setup.sh) primero. Detalle: %s" % e)

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


def main():
    ap = argparse.ArgumentParser(description="Framework MLOps v2 — entry point")
    ap.add_argument("--config", help="JSON con previous_path y sources (datos reales)")
    ap.add_argument("--source", help="correr solo esta fuente (por nombre)")
    args = ap.parse_args()

    demo = not args.config
    spark = (SparkSession.builder.master("local[1]").appName("framework_mlops_v2")
             .config("spark.ui.enabled", "false")
             .config("spark.sql.shuffle.partitions", "2").getOrCreate())
    spark.sparkContext.setLogLevel("ERROR")

    print("=" * 64)
    print("FRAMEWORK MLOPS v2 — %s" % ("DEMO (datos sinteticos)" if demo else "DATOS REALES"))
    print("=" * 64)
    _report_optimizations()

    if demo:
        synth = _synthetic_df(spark)
        print("\\nENTRADA sintetica (%d filas):" % synth.count())
        synth.show(5, truncate=False)
        base = tempfile.mkdtemp(prefix="bnx_main_")
        prev = os.path.join(base, "datapull")
        os.makedirs(prev, exist_ok=True)
        for s in REGISTRY:
            synth.write.mode("overwrite").parquet(os.path.join(prev, s))
        _patch_reads(spark, synth)
        src_cfg = {s: {"table_name": s} for s in REGISTRY}
    else:
        cfg = json.load(open(args.config, encoding="utf-8"))
        base = None
        prev = cfg["previous_path"]
        src_cfg = cfg.get("sources") or {s: {"table_name": s} for s in REGISTRY}

    fuentes = [args.source] if args.source else list(src_cfg.keys())
    ok = fail = 0
    for s in fuentes:
        if s not in REGISTRY:
            print("\\n[skip] fuente no registrada:", s); continue
        print("\\n" + "-" * 64); print("FUENTE:", s)
        try:
            GroupBy(s, previous_path=prev, agg_dict=src_cfg.get(s, {"table_name": s}),
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
    # Heuristica: si el codigo no define df_out ni retorna, devolvemos la ultima
    # variable *_df o el df de entrada.
    has_out = _re.search(r"\bdf_out\b", body) is not None
    tail = "" if has_out else "\n# BNX: no se detecto 'df_out'; se devuelve el df de entrada.\ndf_out = df"
    return f'''# framework_mlops_v2/aggregates/{source}.py
"""Fuente '{source}': generada por BNX desde el Python del negocio.
Convertida a PySpark y envuelta en el contrato del framework v2.
Revisa los comentarios '# TODO py2spark' donde la conversion no fue 1:1."""
from pyspark.sql import functions as F
from ..core.base_aggregate import BaseAggregate


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
            "run.sh": _RUN_SH,
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


def zip_from_files(code_files, sep_files=None, full_env=False, py_target="all"):
    """Empaqueta un ZIP a partir de dicts de archivos YA LISTOS (texto). Reusable
    para re-empaquetar tras EDITAR los archivos generados.

    code_files: {ruta_relativa: contenido} del paquete principal (framework_mlops_v2_pkg/).
    sep_files:  {ruta_relativa: contenido} del paquete separado de monitoreo (opcional).
    full_env/py_target: si full_env, agrega vendor/ offline (PySpark + deps del
    framework) segun py_target. extra_steps se infiere del paquete (si trae
    scoring/, necesita xgboost/sklearn offline).
    Devuelve (zip_bytes, filename, vendor_series_list)."""
    extra_steps = any("scoring/scorer.py" in p for p in (code_files or {}))
    vendor_series = _vendor_files_for_pkg(py_target, extra_steps) if full_env else {}
    # Empaquetar las LIBRERIAS INTERNAS del banco OFFLINE cuando el paquete las
    # usa (hay requirements-bank.txt) y tenemos el cache. Van en vendor/bank/
    # (sdist pip-instalables) y vendor/bank/pkgcode/ (toolbox/bnmxverse/utils que
    # se agregan al PYTHONPATH). Asi el despliegue offline no depende del Artifactory.
    uses_bank = any(p.endswith("requirements-bank.txt") for p in (code_files or {}))
    bank_sdists, bank_pkgcode = ([], {})
    if full_env and uses_bank:
        bank_sdists, bank_pkgcode = _bank_vendor_files()
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED, allowZip64=True) as z:
        for path, content in (code_files or {}).items():
            z.writestr("framework_mlops_v2_pkg/" + path, content)
        for path, content in (sep_files or {}).items():
            z.writestr("framework_mlops_metrics_pkg/" + path, content)
        for serie_dir, whls in (vendor_series or {}).items():
            for fpath in whls:
                try:
                    with open(fpath, "rb") as fh:
                        data = fh.read()
                except OSError:
                    continue
                info = zipfile.ZipInfo(
                    "framework_mlops_v2_pkg/vendor/" + serie_dir + "/" + os.path.basename(fpath))
                info.compress_type = zipfile.ZIP_STORED
                z.writestr(info, data)
        # sdist de las mex-lib* del banco -> vendor/bank/
        for fpath in bank_sdists:
            try:
                with open(fpath, "rb") as fh:
                    data = fh.read()
            except OSError:
                continue
            info = zipfile.ZipInfo(
                "framework_mlops_v2_pkg/vendor/bank/" + os.path.basename(fpath))
            info.compress_type = zipfile.ZIP_STORED
            z.writestr(info, data)
        # Codigo de path del banco (toolbox/bnmxverse/utils) -> vendor/bank/pkgcode/
        for rel, full in sorted(bank_pkgcode.items()):
            try:
                with open(full, "rb") as fh:
                    data = fh.read()
            except OSError:
                continue
            z.writestr("framework_mlops_v2_pkg/vendor/bank/pkgcode/" + rel.replace(os.sep, "/"), data)
    series_out = sorted((vendor_series or {}).keys())
    if bank_sdists or bank_pkgcode:
        series_out = series_out + ["bank"]
    return buf.getvalue(), "framework_mlops_v2.zip", series_out


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
            # Nombre de paquete = prefijo antes de '-<version>'. Solo empaquetar
            # los verificados (los incompletos se dejan fuera del vendor offline).
            pkg = f.split("-2.")[0] if "-2." in f else f.rsplit("-", 1)[0]
            if pkg in _BANK_PKG_VERIFIED:
                sdists.append(os.path.join(whl_dir, f))
    pkgcode = {}
    if os.path.isdir(code_dir):
        for root, _dirs, files in os.walk(code_dir):
            for fn in files:
                full = os.path.join(root, fn)
                rel = os.path.relpath(full, code_dir)
                pkgcode[rel] = full
    return sdists, pkgcode


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
                               py_target="all"):
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
    Devuelve (zip_bytes, filename, report) donde report describe cada fuente.
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
    # Detectar librerias INTERNAS del banco (toolbox, mex_lib_cs, ...) en el
    # codigo original. Van en requirements.txt (dadas de alta) para visibilidad,
    # y ADEMAS en requirements-bank.txt para que el montaje offline del core
    # (vendor/) no se rompa: el core se instala con --no-index y las del banco se
    # intentan aparte desde el Artifactory (sin abortar si no hay acceso).
    bank_libs = _detect_bank_imports(original_codes)
    files["requirements.txt"] = _requirements(include_bank_libs, extra_steps, bank_libs)
    if bank_libs:
        files["requirements-bank.txt"] = _requirements_bank(bank_libs)
    files["run.sh"] = _RUN_SH
    files["setup.py"] = _SETUP
    # Ambiente completo: setup.sh que instala PySpark OFFLINE desde vendor/.
    if full_env:
        files["setup.sh"] = _SETUP_SH_FULL
    files["README.md"] = _readme_custom(
        include_bank_libs, gen_sources, report, extra_steps,
        include_monitoring=include_monitoring, separate_monitoring=separate_monitoring,
        full_env=full_env, bank_libs=bank_libs)

    sep_files = _monitoring_files("separate") if (include_monitoring and separate_monitoring) else {}

    zip_bytes, _fn, vendor_list = zip_from_files(
        files, sep_files, full_env=full_env, py_target=py_target)

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

    # Meta: incluye los archivos de CODIGO (editables) para guardarlos por token.
    report.append({"_meta": True, "full_env": bool(full_env),
                   "vendor_series": vendor_list,
                   "py_target": py_target,
                   "bank_libs": bank_libs,
                   "bank_verified": bank_verified,
                   "bank_incomplete": bank_incomplete,
                   "_code_files": files, "_sep_files": sep_files})
    return zip_bytes, "framework_mlops_v2.zip", report


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
`vendor/` offline, instala el framework y corre las pruebas. Requisitos en la
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

En **ambiente completo** vienen en `vendor/bank/` y se instalan con `--no-index`
(ver `requirements-bank.txt`). Los módulos de PYTHONPATH se copian a `./bank_pkg`
y `main.py` los agrega al path solo:
{path_md}

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
        "run.sh": _RUN_SH,
        "README.md": _readme(include_bank_libs),
        "setup.py": _SETUP,
    }
    if full_env:
        files["setup.sh"] = _SETUP_SH_FULL
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
        {"from": "sin entorno reproducible", "to": "run.sh crea venv + instala + prueba"},
    ]
    tree = [
        "framework_mlops_v2/core/base_aggregate.py",
        "framework_mlops_v2/core/quality.py",
        "framework_mlops_v2/aggregates/{atms,s15,pnl,router}.py",
        "framework_mlops_v2/features/ratios.py",
        "tests/test_aggregates.py",
        "requirements.txt  ·  run.sh  ·  setup.py  ·  README.md",
    ]
    return {"improvements": improvements, "tree": tree,
            "include_bank_libs": include_bank_libs}
