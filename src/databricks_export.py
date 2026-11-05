# -*- coding: utf-8 -*-
"""
databricks_export.py — Genera artefactos de despliegue para Databricks a partir
del PySpark ya generado por BNX. Tres formatos (botones distintos en el portal):

  1) notebook           -> notebook .py de Databricks (celdas # COMMAND ------)
  2) asset_bundle (DAB) -> ZIP con databricks.yml + notebook + config de job
                           (el formato moderno; se despliega con
                            `databricks bundle deploy`)
  3) job_json           -> JSON del job para la API/CLI
                           (`databricks jobs create --json @job.json`)

El linaje (Unity Catalog DDL) ya existe en metadata.build_databricks_ddl y se
expone como su propio boton; aqui no se duplica.

Databricks ejecuta PySpark NATIVO: a diferencia de Glue (GlueContext), el codigo
PySpark de BNX corre tal cual. Solo se ajusta el arranque de SparkSession (en un
cluster de Databricks 'spark' ya existe) y, opcionalmente, rutas a dbfs:/.
"""
import io
import json
import os
import re
import zipfile


def _safe_name(name):
    base = re.sub(r"[^A-Za-z0-9_-]", "_", (name or "bnx_job").strip())
    return base.strip("_") or "bnx_job"


def _strip_local_spark_bootstrap(pyspark_code):
    """En Databricks la SparkSession 'spark' ya existe en el cluster. Quitamos el
    'SparkSession.builder...getOrCreate()' del codigo generado para no recrearla
    (y evitar configs local[1]); dejamos un comentario en su lugar."""
    lines = (pyspark_code or "").split("\n")
    out = []
    skip_cont = False
    for ln in lines:
        s = ln.strip()
        # Linea(s) que crean la sesion: 'spark = SparkSession.builder...'
        if re.match(r'^\s*spark\s*=\s*SparkSession\.builder', ln):
            out.append(ln[:len(ln) - len(ln.lstrip())]
                       + "# BNX: en Databricks 'spark' ya existe (no se recrea la sesion)")
            # Si la llamada sigue en lineas siguientes (encadenada), saltarlas
            skip_cont = not s.endswith(")")
            continue
        if skip_cont:
            # Continua hasta cerrar el getOrCreate()
            if s.endswith(")") or ".getOrCreate()" in s:
                skip_cont = False
            continue
        out.append(ln)
    return "\n".join(out)


def _notebook_source(pyspark_code, job_name):
    """Devuelve el texto de un notebook .py de Databricks (celdas delimitadas por
    '# COMMAND ----------' y encabezado '# Databricks notebook source')."""
    body = _strip_local_spark_bootstrap(pyspark_code)
    head = (
        "# Databricks notebook source\n"
        "# MAGIC %md\n"
        "# MAGIC # BNX -> Databricks\n"
        "# MAGIC Notebook generado por BNX desde el PySpark del grafo.\n"
        "# MAGIC Job: **" + str(job_name) + "**\n"
    )
    cell = (
        "\n# COMMAND ----------\n\n"
        "# BNX: PySpark del grafo (Databricks ejecuta Spark nativo).\n"
        "from pyspark.sql import functions as F\n"
        "from pyspark.sql.functions import *  # noqa\n\n"
        + body + "\n"
    )
    return head + cell


def build_notebook(pyspark_code, job_name="bnx_job"):
    """Artefacto 1: notebook .py autocontenido para subir al workspace."""
    job = _safe_name(job_name)
    src = _notebook_source(pyspark_code, job)
    return {"filename": "%s.py" % job, "content": src,
            "note": "Subelo al workspace de Databricks y correlo, o adjuntalo a un Job."}


def build_job_json(job_name="bnx_job", notebook_path=None,
                   spark_version="14.3.x-scala2.12", node_type="Standard_DS3_v2",
                   num_workers=2):
    """Artefacto 3: JSON de un Databricks Job (API 2.1) con una tarea notebook y
    un cluster job efimero. Se crea con:
        databricks jobs create --json @<job>.job.json
    notebook_path: ruta en el workspace (p.ej. /Workspace/Users/tu@org/bnx_job)."""
    job = _safe_name(job_name)
    nb = notebook_path or ("/Workspace/Shared/bnx/%s" % job)
    spec = {
        "name": job,
        "tasks": [
            {
                "task_key": "%s_task" % job,
                "notebook_task": {
                    "notebook_path": nb,
                    "source": "WORKSPACE",
                },
                "new_cluster": {
                    "spark_version": spark_version,
                    "node_type_id": node_type,
                    "num_workers": num_workers,
                    "spark_conf": {"spark.sql.shuffle.partitions": "8"},
                },
            }
        ],
        "tags": {"generated_by": "BNX", "graph": job},
        "max_concurrent_runs": 1,
    }
    return {"filename": "%s.job.json" % job,
            "content": json.dumps(spec, indent=2, ensure_ascii=False),
            "note": "databricks jobs create --json @%s.job.json" % job}


def _databricks_yml(job_name, spark_version, node_type, num_workers):
    """databricks.yml de un Asset Bundle (DAB) con un job que corre el notebook."""
    job = _safe_name(job_name)
    return """# databricks.yml - Asset Bundle generado por BNX
# Despliega con:
#   databricks bundle validate
#   databricks bundle deploy -t dev
#   databricks bundle run %s -t dev
bundle:
  name: bnx_%s

targets:
  dev:
    mode: development
    default: true
    # workspace:
    #   host: https://<tu-workspace>.cloud.databricks.com

resources:
  jobs:
    %s:
      name: %s
      tags:
        generated_by: BNX
      tasks:
        - task_key: %s_task
          notebook_task:
            notebook_path: ./src/%s.py
          new_cluster:
            spark_version: %s
            node_type_id: %s
            num_workers: %d
            spark_conf:
              spark.sql.shuffle.partitions: "8"
""" % (job, job, job, job, job, job, spark_version, node_type, num_workers)


def build_asset_bundle(pyspark_code, job_name="bnx_job",
                       spark_version="14.3.x-scala2.12",
                       node_type="Standard_DS3_v2", num_workers=2,
                       databricks_ddl=None):
    """Artefacto 2: ZIP de un Databricks Asset Bundle (DAB). Estructura:
        databricks.yml
        src/<job>.py            (notebook)
        resources/unity_catalog.sql  (DDL de linaje, si se pasa)
        README.md
    Devuelve {filename, zip_bytes}."""
    job = _safe_name(job_name)
    nb = _notebook_source(pyspark_code, job)
    yml = _databricks_yml(job, spark_version, node_type, num_workers)
    readme = (
        "# BNX - Databricks Asset Bundle\n\n"
        "Bundle generado por BNX desde el grafo **%s**.\n\n"
        "## Desplegar\n"
        "```bash\n"
        "databricks bundle validate\n"
        "databricks bundle deploy -t dev\n"
        "databricks bundle run %s -t dev\n"
        "```\n\n"
        "## Contenido\n"
        "- `databricks.yml` - definicion del bundle (job + cluster).\n"
        "- `src/%s.py` - notebook con el PySpark del grafo.\n"
        "%s"
        "\n> Databricks ejecuta PySpark nativo; el codigo del grafo corre tal cual.\n"
        % (job, job, job,
           "- `resources/unity_catalog.sql` - DDL de Unity Catalog (linaje).\n"
           if databricks_ddl else "")
    )
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr("databricks.yml", yml)
        z.writestr("src/%s.py" % job, nb)
        z.writestr("README.md", readme)
        if databricks_ddl:
            z.writestr("resources/unity_catalog.sql", databricks_ddl)
    return {"filename": "bnx_dab_%s.zip" % job, "zip_bytes": buf.getvalue()}
