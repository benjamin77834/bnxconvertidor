# examples/mlops_framework/steps.py
"""
Contenido de la seccion "Framework MLOps" del portal BNX.

Describe, PASO A PASO, el pipeline de feature engineering para scoring
crediticio (estilo del framework DAA/MLOps_FrameworkUDF que el negocio usa en
PySpark/YARN/Hive). La idea de la seccion es didactica + operativa:

  - Para CADA paso se muestra un EJEMPLO EN PANDAS "estilo negocio" (lo que
    escribiria el area de negocio ANTES de que ingenieria lo estandarice). Ese
    pandas es el que el usuario puede CONVERTIR a PySpark con el convertidor BNX
    (/py2spark) y luego probar en Data Sintetica.
  - Y una REFERENCIA del framework real (como se ve ese mismo paso ya en
    produccion, en PySpark), para contrastar.

Los ejemplos pandas son didacticos (dominio: buro, PnL, canales, scoring) y
estan pensados para lucir la conversion pandas -> PySpark. No son datos reales.

STEPS: lista ordenada de pasos del pipeline. Cada paso:
  {
    "id": str, "title": str, "emoji": str, "summary": str,
    "pandas": str,        # ejemplo de negocio (pandas) -> convertible a Spark
    "framework_ref": str, # como se ve en el framework real (PySpark) [referencia]
    "sample_csv": str|None  # datos de muestra (CSV) para probar, si aplica
  }
"""

STEPS = [
    {
        "id": "extract",
        "title": "1. Extract (datapull)",
        "emoji": "📥",
        "summary": (
            "Lee las fuentes crudas (buro, PnL, pasivos, canales, cajeros, nomina) "
            "por rango de fechas/cohortes y las aterriza en parquet. En el framework "
            "real se paraleliza con ThreadPool y se controla por conteos/nulos."),
        "pandas": '''# Extract: leer la fuente cruda y filtrar la ventana de observacion
import pandas as pd

# El negocio parte de un archivo/export de la fuente (aqui: buro de credito).
df = pd.read_csv("bureau.csv")

# Filtra la ventana de observacion (ultimas N fechas de corte).
df = df[df["inf_dt"] >= "2025-01-01"]

# Nos quedamos con las columnas de interes del datapull.
df = df[["cliente_id", "inf_dt", "saldo", "atraso_max", "lineas_activas"]]

df.to_parquet("extract/bureau")
''',
        "framework_ref": '''# Framework real (extract.py -> class Extract): datapull paralelo
# Genera consultas por cohorte/fecha, usa ThreadPool (hasta 32 hilos),
# controla conteos y nulos, y escribe parquets *_historic en HDFS.
reading_path = os.path.join(self.previous_path, self.agg_dict["table_name"])
df_out = self.sqlContext.read.parquet(reading_path)
# ... filtros por vintage/cohorte + checks de calidad ...
df_out.write.mode(self.mode).parquet(os.path.join(head, "extract"))
''',
        "sample_csv": (
            "cliente_id,inf_dt,saldo,atraso_max,lineas_activas\n"
            "1001,2025-01-31,15000.50,0,3\n"
            "1002,2025-01-31,0,2,1\n"
            "1003,2025-02-28,48200.00,0,5\n"
            "1004,2025-02-28,230.75,1,2\n"
            "1005,2025-03-31,9800.00,0,4\n"),
    },
    {
        "id": "groupby",
        "title": "2. Group By (agregacion por fuente)",
        "emoji": "🧮",
        "summary": (
            "Agrupa por la llave del cliente y resume la fuente (sum/avg/max). En el "
            "framework hay una clase *_aggregate.py por fuente con el mismo contrato "
            "(constructor, _save_parquet, aggregate) y un router GroupBy."),
        "pandas": '''# Group By: resumir la fuente por cliente
import pandas as pd

df = pd.read_parquet("extract/bureau")

# Agregacion por cliente: saldo total, atraso maximo, lineas promedio.
g = df.groupby("cliente_id").agg({
    "saldo": "sum",
    "atraso_max": "max",
    "lineas_activas": "mean",
})
g = g.reset_index()
g = g.fillna(0)

g.to_parquet("groupby/bureau")
''',
        "framework_ref": '''# Framework real (pnl_aggregate.py -> class PNLAggregate)
# Arma dinamicamente el GROUP BY en SQL desde un query_dict y lo ejecuta en Spark.
df_in = self.sqlContext.read.parquet(reading_path)
df_in.createOrReplaceTempView("tempPnl")
query_str = self._create_groupby_query(
    self.agg_dict["query_dict"], self.agg_dict["group_by_key"], df_in.columns)
df_out = self.sqlContext.sql(query_str)   # SELECT k, sum(x) as x ... GROUP BY k
df_out.write.mode(self.mode).parquet(os.path.join(head, "groupby"))
''',
        "sample_csv": None,
    },
    {
        "id": "pivot",
        "title": "3. Generate Pivot (largo -> ancho)",
        "emoji": "🔄",
        "summary": (
            "Transpone de formato largo a ancho: una fila por cliente y una columna "
            "por (variable, periodo). En el framework usa explode + pivot y genera "
            "columnas tipo variable_tfrom."),
        "pandas": '''# Pivot: pasar de largo (cliente, mes, variable) a ancho (una fila por cliente)
import pandas as pd

df = pd.read_parquet("groupby/bureau_mensual")

# De (cliente_id, mes, saldo) a columnas saldo_m1, saldo_m2, ...
wide = df.pivot_table(
    index="cliente_id",
    columns="mes",
    values="saldo",
    aggfunc="sum",
)
wide = wide.reset_index().fillna(0)

wide.to_parquet("pivot/bureau")
''',
        "framework_ref": '''# Framework real (generate_pivot.py -> class GeneratePivot)
# explode de los periodos + pivot de Spark -> columnas variable_tfrom.
df_long = df.select("cliente_id", explode(...).alias("kv"))
df_wide = (df_long.groupBy("cliente_id")
           .pivot("periodo")
           .agg(F.first("valor")))
df_wide.write.mode(self.mode).parquet(path)
''',
        "sample_csv": (
            "cliente_id,mes,saldo\n"
            "1001,1,15000\n1001,2,15200\n1001,3,14800\n"
            "1002,1,0\n1002,2,500\n1002,3,0\n"
            "1003,1,48200\n1003,2,47000\n1003,3,49100\n"),
    },
    {
        "id": "ratios",
        "title": "4. Generate Ratios (cocientes)",
        "emoji": "➗",
        "summary": (
            "Calcula features de ratio (numerador/denominador) con proteccion de "
            "division por cero. En el framework hay logica por fuente (pnl, corporate)."),
        "pandas": '''# Ratios: cocientes entre variables con proteccion de /0
import pandas as pd
import numpy as np

df = pd.read_parquet("groupby/bureau")

# Utilizacion = saldo / linea_total (0 si la linea es 0).
df["utilizacion"] = np.where(
    df["linea_total"] > 0,
    df["saldo"] / df["linea_total"],
    0.0,
)

# Peso del atraso respecto al numero de lineas.
df["atraso_por_linea"] = np.where(
    df["lineas_activas"] > 0,
    df["atraso_max"] / df["lineas_activas"],
    0.0,
)

df.to_parquet("ratios/bureau")
''',
        "framework_ref": '''# Framework real (generate_ratios.py -> class GenerateRatios)
# Cocientes numerador/denominador con when/otherwise para evitar /0.
df = df.withColumn(
    "utilizacion",
    F.when(F.col("linea_total") > 0, F.col("saldo") / F.col("linea_total"))
     .otherwise(F.lit(0.0)))
df.write.mode(self.mode).parquet(path)
''',
        "sample_csv": (
            "cliente_id,saldo,linea_total,atraso_max,lineas_activas\n"
            "1001,15000,30000,0,3\n"
            "1002,0,5000,2,1\n"
            "1003,48200,50000,0,5\n"
            "1004,230,1000,1,2\n"),
    },
    {
        "id": "feature_engineering",
        "title": "5. Feature Engineering (series temporales)",
        "emoji": "🧬",
        "summary": (
            "El corazon del framework: transformaciones sobre las series por cliente "
            "(media, std, min, max, tendencia, medias moviles, deltas, skew, curtosis). "
            "En produccion se ejecutan en paralelo con ThreadPool via UDFs."),
        "pandas": '''# Feature Engineering: estadisticos de la serie de saldo por cliente
import pandas as pd

df = pd.read_parquet("pivot/bureau")  # columnas saldo_m1..saldo_m6 por cliente

saldos = ["saldo_m1", "saldo_m2", "saldo_m3", "saldo_m4", "saldo_m5", "saldo_m6"]

# Estadisticos de la serie (lo que el framework hace con muchas transformaciones).
df["saldo_media"] = df[saldos].mean(axis=1)
df["saldo_std"] = df[saldos].std(axis=1)
df["saldo_min"] = df[saldos].min(axis=1)
df["saldo_max"] = df[saldos].max(axis=1)
# Tendencia simple: ultimo - primero.
df["saldo_tendencia"] = df["saldo_m6"] - df["saldo_m1"]

df.to_parquet("features/bureau")
''',
        "framework_ref": '''# Framework real (feature_engineering.py -> class FeatureEngineering)
# Catalogo amplio de transformaciones (media, std, trend, rmeans, avgmov, skew,
# curtosis, logmedia, inverso, deltas...) aplicadas via UDFs en paralelo (ThreadPool).
# La lista de transformaciones a correr llega por configuracion.
df = df.withColumn("saldo_media", mean_udf(F.array(*saldo_cols)))
df = df.withColumn("saldo_trend", trend_udf(F.array(*saldo_cols)))
# ... decenas de transformaciones mas ...
df.write.mode(self.mode).parquet(path)
''',
        "sample_csv": (
            "cliente_id,saldo_m1,saldo_m2,saldo_m3,saldo_m4,saldo_m5,saldo_m6\n"
            "1001,15000,15200,14800,15100,15300,15500\n"
            "1002,0,500,0,300,0,0\n"
            "1003,48200,47000,49100,48000,47500,46900\n"),
    },
    {
        "id": "vector_assembler",
        "title": "6. Vector Assembler (feature vector)",
        "emoji": "📦",
        "summary": (
            "Junta todas las features en un unico vector listo para el modelo. En el "
            "framework real usa pyspark.ml.VectorAssembler y preserva la metadata de "
            "nombres de columnas; aqui el equivalente de negocio es seleccionar las "
            "columnas del feature set."),
        "pandas": '''# Vector Assembler: ensamblar el feature set final para el modelo
import pandas as pd

df = pd.read_parquet("features/bureau")

# Columnas que entran al modelo (el "features_vector").
feature_cols = [
    "saldo_media", "saldo_std", "saldo_min", "saldo_max", "saldo_tendencia",
    "utilizacion", "atraso_por_linea",
]

features = df[["cliente_id"] + feature_cols].fillna(0)
features.to_parquet("vector_assembler/features")
''',
        "framework_ref": '''# Framework real (vector_assembler.py -> class FeaturesVectorAssembler)
from pyspark.ml.feature import VectorAssembler
assembler = VectorAssembler(inputCols=feature_cols, outputCol="features_vector")
df_vec = assembler.transform(df)          # preserva metadata de nombres
df_vec.write.mode(self.mode).parquet(path)
''',
        "sample_csv": None,
    },
    {
        "id": "scoring",
        "title": "7. Scoring (modelo)",
        "emoji": "🎯",
        "summary": (
            "Aplica el modelo (XGBoost en el framework real, rpsv2_*.xgb) sobre el "
            "feature vector y produce el score por cliente. Aqui un ejemplo de negocio "
            "con un modelo ya entrenado."),
        "pandas": '''# Scoring: aplicar el modelo entrenado sobre el feature set
import pandas as pd

features = pd.read_parquet("vector_assembler/features")

feature_cols = [
    "saldo_media", "saldo_std", "saldo_min", "saldo_max", "saldo_tendencia",
    "utilizacion", "atraso_por_linea",
]

# El negocio trae un score lineal de ejemplo (en produccion: XGBoost .xgb).
w = {"saldo_media": 0.00001, "utilizacion": -1.2, "atraso_por_linea": -0.8}
features["score"] = (
    0.5
    + features["saldo_media"] * w["saldo_media"]
    + features["utilizacion"] * w["utilizacion"]
    + features["atraso_por_linea"] * w["atraso_por_linea"]
)
features["score"] = features["score"].clip(0, 1)

features[["cliente_id", "score"]].to_parquet("scoring/scores")
''',
        "framework_ref": '''# Framework real (3_scoring/fitting.py): modelo XGBoost
import xgboost as xgb
booster = xgb.Booster(); booster.load_model("rpsv2_all_versions.xgb")
dmat = xgb.DMatrix(df_features[XGB_42_features])
df["score"] = booster.predict(dmat)        # escribe SCORES a Hive
''',
        "sample_csv": (
            "cliente_id,saldo_media,saldo_std,saldo_min,saldo_max,saldo_tendencia,utilizacion,atraso_por_linea\n"
            "1001,15150,240,14800,15500,500,0.50,0.0\n"
            "1002,133,210,0,500,0,0.0,2.0\n"
            "1003,47783,780,46900,49100,-1300,0.96,0.0\n"),
    },
    {
        "id": "metrics",
        "title": "8. Metrics / Monitoreo (PSI/CSI)",
        "emoji": "📊",
        "summary": (
            "Monitorea la estabilidad del modelo en produccion: PSI (poblacion) y CSI "
            "(caracteristicas) comparando la distribucion actual vs la de desarrollo, "
            "mas data quality. En el framework es la libreria lib_mkop_metrics."),
        "pandas": '''# Metrics: PSI entre la distribucion de desarrollo y la actual
import pandas as pd
import numpy as np

# Frecuencia relativa por bin del score: desarrollo (ref) vs actual.
dev = pd.read_csv("psi/dist_dev.csv")      # bin, rel_dev
cur = pd.read_csv("psi/dist_actual.csv")   # bin, rel_cur

m = dev.merge(cur, on="bin", how="inner")

# PSI por bin = (rel_cur - rel_dev) * ln(rel_cur / rel_dev).
m["psi_bin"] = (m["rel_cur"] - m["rel_dev"]) * np.log(m["rel_cur"] / m["rel_dev"])
psi = m["psi_bin"].sum()

# Regla tipica: <0.1 estable, 0.1-0.25 revisar, >0.25 inestable.
print("PSI total:", round(psi, 4))
''',
        "framework_ref": '''# Framework real (lib_mkop_metrics -> class MonitorMetrics)
# psi_csi_calculation: por variable/bin arma el intervalo, cuenta frecuencia
# actual, calcula rel_cur y aplica (rel_cur - dist_dev) * log(rel_cur / dist_dev).
# dqc: estadisticos por variable (conteo, media, std, p1..p99, min, max, n_miss).
# Lee parametros de referencia de Hive por model_id y escribe PSI/CSI + DQC.
''',
        "sample_csv": None,
    },
]


def get_steps():
    """Devuelve la lista de pasos (copia defensiva)."""
    return [dict(s) for s in STEPS]


# ---------------------------------------------------------------------------
# DIAGNOSTICO: hallazgos del analisis del framework real (solo lectura). Se
# muestran en la seccion como "lo que detectamos" para priorizar mejoras. NO
# se modifica el framework del banco; es informativo.
# severity: critical | high | medium | low
# ---------------------------------------------------------------------------
FINDINGS = [
    {
        "id": "secrets",
        "severity": "critical",
        "title": "Credenciales en texto plano en el repositorio",
        "detail": ("`.pypirc` y `pip.conf` contienen usuario y token de Artifactory "
                   "en claro. Es una fuga activa: cualquiera con el repo tiene las "
                   "credenciales."),
        "fix": ("Rotar el token YA, borrarlo del historial de git y moverlo a "
                "variables de entorno / gestor de secretos."),
    },
    {
        "id": "validations_off",
        "severity": "critical",
        "title": "Validaciones de calidad comentadas (monitoreo ciego)",
        "detail": ("En `checks.py` el assert de umbral de nulos esta comentado y en "
                   "`emails.py` el conteo real de nulos esta comentado (reporta "
                   "'Nulls total: 0' fijo). El pipeline PARECE validar pero no valida."),
        "fix": ("Reactivar y verificar las validaciones; fallar el pipeline si se "
                "superan los umbrales de nulos."),
    },
    {
        "id": "no_tests",
        "severity": "high",
        "title": "Sin pruebas automatizadas reales",
        "detail": ("Los metodos `test()` solo imprimen 'class is working!'. No hay "
                   "una sola prueba unitaria/integracion en un pipeline que decide "
                   "scoring crediticio."),
        "fix": ("Anadir pytest + fixtures de Spark (chispa/spark-testing-base): un "
                "test por aggregate con entrada y salida esperada."),
    },
    {
        "id": "duplication",
        "severity": "medium",
        "title": "Codigo duplicado entre aggregates",
        "detail": ("`atms_aggregate.py`, `s15_aggregate.py` y `s15_nf_aggregate.py` son "
                   "casi identicos; `utils.py` y `evaluatePath.py` duplican la logica "
                   "de HDFS."),
        "fix": ("Extraer una clase base `BaseAggregate` con el contrato comun "
                "(__init__/_save_parquet/aggregate) y unificar utils/evaluatePath."),
    },
    {
        "id": "huge_files",
        "severity": "medium",
        "title": "Archivos enormes difíciles de mantener",
        "detail": ("`feature_engineering.py` (~83 KB) y `weeks.py` (~69 KB) concentran "
                   "demasiadas responsabilidades; son dificiles de testear y revisar."),
        "fix": ("Modularizar por familia de transformacion (estadisticos, tendencias, "
                "medias moviles, ratios...)."),
    },
    {
        "id": "import_divergence",
        "severity": "medium",
        "title": "Código duplicado en 3 sitios (riesgo de divergencia)",
        "detail": ("El mismo codigo vive como libreria, como copias locales en "
                   "`2_datapull/libs/` del pipeline RPS, y como paquetes `mex-lib*`. "
                   "Tarde o temprano divergen."),
        "fix": ("Consolidar en una sola fuente versionada; que el pipeline consuma "
                "solo las libs publicadas `mex-lib*`."),
    },
    {
        "id": "silent_errors",
        "severity": "medium",
        "title": "Errores silenciados (try/except genéricos)",
        "detail": ("Varios `try/except Exception: continue` esconden fallos de datos. "
                   "Un error silenciado hoy es un modelo con scores malos manana."),
        "fix": "Capturar excepciones especificas, loguearlas y no continuar en silencio.",
    },
    {
        "id": "python_versions",
        "severity": "low",
        "title": "Versiones de Python mezcladas",
        "detail": ("Jenkinsfile usa Python 3.6, setup.py exige >=3.9 y los .pyc de RPS "
                   "son cpython-310. Tres versiones en juego."),
        "fix": "Fijar una unica version objetivo de Python en todo el pipeline.",
    },
    {
        "id": "obfuscation",
        "severity": "low",
        "title": "Ofuscación con PyArmor",
        "detail": ("El deploy ofusca con PyArmor 7.7.4 y ata la ejecucion a un runtime "
                   "binario (`_pytransform.so`). Dificulta auditoria y depuracion."),
        "fix": "Es decision de negocio; documentar el runtime y versionarlo con cuidado.",
    },
]


def get_findings():
    """Devuelve los hallazgos del diagnostico (copia defensiva)."""
    return [dict(f) for f in FINDINGS]
