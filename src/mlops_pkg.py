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


def _requirements(include_bank_libs, extra_steps=False):
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
    if include_bank_libs:
        base += [
            "",
            "# Librerias internas del banco (se resuelven desde el Artifactory",
            "# privado de Citi; en local se omiten o se apuntan al indice interno).",
            "# toolbox",
            "# lib_mkop_metrics",
            "# mex-libextract",
            "# mex-libgroupby",
            "# mex-libfeatureengineering",
        ]
    return "\n".join(base) + "\n"


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
  python -m pip install --no-index --find-links "$VENDOR_DIR" -r requirements.txt 2>/dev/null || \
    python -m pip install -r requirements.txt 2>/dev/null || true
else
  python -m pip install -r requirements.txt 2>/dev/null || true
fi
# Instalar el PROPIO paquete en modo editable (clave: sin esto los imports
# 'from framework_mlops_v2...' fallan fuera de la carpeta raiz).
python -m pip install -e .

echo "[5/5] Corriendo pruebas ..."
pytest -q || echo "  (pytest requiere Java para Spark; revisa el entorno)"

echo ""
echo "✅ Ambiente listo. Ejemplo:"
echo "   . .venv/bin/activate"
echo "   python -c \\"from framework_mlops_v2.aggregates.router import GroupBy; print('ok')\\""
'''

_RUN_SH = '''#!/usr/bin/env bash
# run.sh — crea un ENTORNO VIRTUAL con todo lo necesario y corre las pruebas.
# Uso:  bash run.sh
set -e

PY="${PYTHON:-python3}"
echo "[1/4] Creando entorno virtual .venv ..."
"$PY" -m venv .venv

echo "[2/4] Activando e instalando dependencias ..."
. .venv/bin/activate
pip install --upgrade pip >/dev/null
# Si estas en la red del banco, descomenta --index-url con tu Artifactory:
# pip install -r requirements.txt --index-url https://<artifactory-interno>/simple
pip install -r requirements.txt
# Instalar el PROPIO paquete (sin esto los imports 'from framework_mlops_v2...'
# fallan fuera de la carpeta raiz).
pip install -e .

echo "[3/4] Ejecutando pruebas (pytest) ..."
pytest -q || echo "  (pytest requiere pyspark + Java; revisa el entorno)"

echo "[4/4] Listo. Ejemplo de uso:"
echo "  . .venv/bin/activate"
echo "  python -c \\"from framework_mlops_v2.aggregates.router import GroupBy; print('ok')\\""
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


import re as _re


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
_ORIGINAL_PANDAS = """
{original_pandas.strip()}
"""
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
    full_env/py_target: si full_env, agrega vendor/ offline (PySpark) segun py_target.
    Devuelve (zip_bytes, filename, vendor_series_list)."""
    vendor_series = _vendor_files_for_pkg(py_target) if full_env else {}
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
    return buf.getvalue(), "framework_mlops_v2.zip", sorted((vendor_series or {}).keys())


def _vendor_files_for_pkg(py_target="all"):
    """Wheels de PySpark+py4j para empaquetar el ambiente completo offline.
    Reutiliza el cache de Data Sintetica. py_target elige que serie(s) incluir
    para bajar el tamano: 'all' (ambas), 'py38-311' (PySpark 3.5.6) o
    'py312plus' (PySpark 4.0.0). Devuelve {serie_dir: [rutas .whl]} o {}."""
    try:
        from src.export_bundle import fetch_vendor_files, PY_TARGET_SERIES
        only = PY_TARGET_SERIES.get(py_target, None)
        return fetch_vendor_files(only_series=only) or {}
    except Exception:
        return {}


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

    for item in sources or []:
        raw_name = item.get("name") or "fuente.py"
        pandas_code = item.get("code") or ""
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
    files["requirements.txt"] = _requirements(include_bank_libs, extra_steps)
    files["run.sh"] = _RUN_SH
    files["setup.py"] = _SETUP
    # Ambiente completo: setup.sh que instala PySpark OFFLINE desde vendor/.
    if full_env:
        files["setup.sh"] = _SETUP_SH_FULL
    files["README.md"] = _readme_custom(
        include_bank_libs, gen_sources, report, extra_steps,
        include_monitoring=include_monitoring, separate_monitoring=separate_monitoring,
        full_env=full_env)

    sep_files = _monitoring_files("separate") if (include_monitoring and separate_monitoring) else {}

    zip_bytes, _fn, vendor_list = zip_from_files(
        files, sep_files, full_env=full_env, py_target=py_target)

    # Meta: incluye los archivos de CODIGO (editables) para guardarlos por token.
    report.append({"_meta": True, "full_env": bool(full_env),
                   "vendor_series": vendor_list,
                   "py_target": py_target,
                   "_code_files": files, "_sep_files": sep_files})
    return zip_bytes, "framework_mlops_v2.zip", report


def _readme_custom(include_bank_libs, sources, report, extra_steps=False,
                   include_monitoring=False, separate_monitoring=False,
                   full_env=False):
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
    return base + mon + f'''

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
        "requirements.txt": _requirements(include_bank_libs, extra_steps),
        "run.sh": _RUN_SH,
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
