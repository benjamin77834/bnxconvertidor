# src/datasource.py
"""Conexion a fuentes externas (Cloudera/Hive/Impala, Teradata) para pruebas
PUNTUALES en Data Sintetica. CLAVE DE SEGURIDAD: los datos reales que llegan se
ENMASCARAN con la libreria de PII ANTES de salir de aqui. El dato real nunca se
devuelve, ni se escribe en disco, ni se muestra. Solo su version enmascarada.

Implementacion: ejecuta un script PySpark en subprocess que lee via JDBC con un
LIMIT (pruebas puntuales, no cargas masivas), aplica el enmascaramiento PII sobre
las filas y escribe SOLO el resultado enmascarado a un JSON temporal que este
proceso lee y borra. Requiere el driver JDBC correspondiente en el destino:
  - Teradata: terajdbc4.jar (licencia Teradata)
  - Hive/Impala (Cloudera): HiveJDBC/ImpalaJDBC jar
El jar se pasa por 'driver_jar' y se inyecta con --jars.
"""
import json
import os
import subprocess
import sys
import tempfile

# Plantillas de URL/driver por tipo de fuente (orientativas; el usuario puede
# sobreescribir la URL completa).
_PRESETS = {
    "teradata": {
        "driver": "com.teradata.jdbc.TeraDriver",
        "url": "jdbc:teradata://{host}/DATABASE={database}",
    },
    "hive": {
        "driver": "org.apache.hive.jdbc.HiveDriver",
        "url": "jdbc:hive2://{host}:{port}/{database}",
    },
    "impala": {
        "driver": "com.cloudera.impala.jdbc.Driver",
        "url": "jdbc:impala://{host}:{port}/{database}",
    },
}


def _resolve_python():
    # Reusa el mismo Python del venv (donde esta pyspark).
    here = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    for cand in (os.path.join(here, ".venv", "bin", "python"),
                 os.path.join(here, ".venv", "Scripts", "python.exe")):
        if os.path.isfile(cand):
            return cand
    return sys.executable


def fetch_masked(source_type, conn, query=None, table=None, limit=50,
                 driver_jar=None, columns=None, timeout=180):
    """Lee de la fuente via JDBC (con LIMIT) y devuelve filas YA ENMASCARADAS.

    source_type: 'teradata' | 'hive' | 'impala' | 'jdbc'
    conn: dict con url|host|port|database|user|password (password no se loguea).
    query/table: consulta o tabla a leer (se aplica LIMIT por seguridad).
    limit: maximo de filas (pruebas puntuales).
    driver_jar: ruta al .jar del driver JDBC (requerido en el destino).
    columns: opcional [{name,pii}] para dirigir el enmascaramiento.

    Devuelve {"ok", "rows": [...enmascaradas...], "columns": [...], "n": N}
    o {"ok": False, "error": ...}. NUNCA devuelve datos reales en claro."""
    preset = _PRESETS.get(source_type, {})
    url = conn.get("url") or (preset.get("url", "").format(
        host=conn.get("host", ""), port=conn.get("port", ""),
        database=conn.get("database", "")))
    driver = conn.get("driver") or preset.get("driver")
    if not url:
        return {"ok": False, "error": "Falta la URL de conexion (o host/database)."}
    if not driver_jar or not os.path.isfile(driver_jar):
        return {"ok": False, "error": "Falta el driver JDBC (driver_jar). "
                "Teradata: terajdbc4.jar; Cloudera: HiveJDBC/ImpalaJDBC jar."}

    # dbtable: subconsulta con LIMIT para no traer de mas.
    lim = max(1, min(int(limit or 50), 1000))
    if query:
        dbtable = f"({query.rstrip(';')} ) t_bnx"  # se envuelve; el LIMIT lo pone el usuario o abajo
        dbtable = f"(SELECT * FROM {dbtable} LIMIT {lim}) t_lim" if source_type in ("hive", "impala") else f"({query.rstrip(';')}) t_bnx"
    elif table:
        if source_type == "teradata":
            dbtable = f"(SELECT * FROM {table} SAMPLE {lim}) t_lim"
        else:
            dbtable = f"(SELECT * FROM {table} LIMIT {lim}) t_lim"
    else:
        return {"ok": False, "error": "Indica 'table' o 'query'."}

    out_tmp = tempfile.NamedTemporaryFile(delete=False, suffix="_bnx_src.json")
    out_tmp.close()
    # Script PySpark: lee via JDBC y escribe las filas CRUDAS a un JSON temporal.
    # El enmascaramiento se hace en ESTE proceso (abajo), no se expone por API.
    reader = f'''# -*- coding: utf-8 -*-
import json, sys
from pyspark.sql import SparkSession
spark = SparkSession.builder.appName("bnx_src_fetch").getOrCreate()
try:
    df = (spark.read.format("jdbc")
          .option("url", {json.dumps(url)})
          .option("driver", {json.dumps(driver)})
          .option("dbtable", {json.dumps(dbtable)})
          .option("user", {json.dumps(conn.get("user",""))})
          .option("password", {json.dumps(conn.get("password",""))})
          .load())
    df = df.limit({lim})
    cols = df.columns
    rows = [r.asDict() for r in df.collect()]
    with open({json.dumps(out_tmp.name)}, "w", encoding="utf-8") as f:
        json.dump({{"columns": cols, "rows": rows}}, f, default=str)
    print("BNX_SRC_OK")
except Exception as e:
    print("BNX_SRC_ERR:" + str(e))
    sys.exit(1)
finally:
    spark.stop()
'''
    script_tmp = tempfile.NamedTemporaryFile(delete=False, suffix="_bnx_src_reader.py",
                                             mode="w", encoding="utf-8")
    script_tmp.write(reader)
    script_tmp.close()

    py = _resolve_python()
    env = dict(os.environ)
    env["PYSPARK_PYTHON"] = py
    env["PYSPARK_DRIVER_PYTHON"] = py
    # Inyectar el driver JDBC.
    env["PYSPARK_SUBMIT_ARGS"] = f'--jars "{driver_jar}" pyspark-shell'

    try:
        proc = subprocess.run([py, script_tmp.name], capture_output=True, text=True,
                              timeout=timeout, env=env)
        if proc.returncode != 0 or "BNX_SRC_OK" not in (proc.stdout or ""):
            err = ""
            for line in (proc.stdout or "").splitlines():
                if line.startswith("BNX_SRC_ERR:"):
                    err = line[len("BNX_SRC_ERR:"):]
            return {"ok": False, "error": err or "No se pudo leer de la fuente "
                    "(revisa URL, credenciales, driver y acceso de red)."}
        with open(out_tmp.name, encoding="utf-8") as f:
            raw = json.load(f)
    except subprocess.TimeoutExpired:
        return {"ok": False, "error": f"Timeout tras {timeout}s leyendo la fuente."}
    finally:
        for p in (out_tmp.name, script_tmp.name):
            try:
                os.remove(p)   # el JSON con datos CRUDOS se borra siempre.
            except OSError:
                pass

    # ENMASCARAR INMEDIATAMENTE. A partir de aqui no existe el dato real.
    cols = raw.get("columns", [])
    rows = raw.get("rows", [])
    masked = mask_records(rows, columns=columns)
    # Liberar las filas crudas de memoria.
    del rows, raw
    # Marcar que columnas quedaron enmascaradas (para la UI).
    col_meta = []
    for c in cols:
        cat = None
        if columns:
            for cc in columns:
                if cc.get("name") == c:
                    cat = cc.get("pii"); break
        col_meta.append({"name": c, "pii": cat or _detect(c)})
    return {"ok": True, "n": len(masked), "columns": col_meta, "rows": masked}


# imports diferidos para evitar ciclos y mantener el modulo ligero al cargar.
def mask_records(rows, columns=None):
    from .datagen import mask_records as _m
    return _m(rows, columns=columns)


def _detect(name):
    from .datagen import detect_pii
    return detect_pii(name)
