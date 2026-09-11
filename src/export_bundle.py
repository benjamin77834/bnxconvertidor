"""Construccion de bundles descargables para probar un job PySpark en Linux.

Produce un ZIP contenedor con DOS zips dentro:

  <job>_export.zip
    ├── job_bundle.zip        # el job + como ejecutarlo en Linux
    │     ├── job.py
    │     ├── requirements.txt
    │     ├── run.sh
    │     └── README.md
    └── data_bundle.zip       # datos de prueba (sinteticos) del job
          ├── data/<nodo>.csv
          └── manifest.json

Diseno (opcion A): NO se empaqueta el venv (no es portable macOS->Linux). En su
lugar run.sh crea el venv en el destino Linux e instala requirements con pip
(el destino tiene internet). Java debe existir en el destino (lo verifica run.sh).
"""
import io
import json
import zipfile
import datetime


# Version de PySpark que usa el proyecto (pinneada para reproducibilidad).
PYSPARK_VERSION = "4.1.2"


def _requirements_txt():
    return (
        f"# Dependencias para ejecutar el job PySpark generado por BNX.\n"
        f"pyspark=={PYSPARK_VERSION}\n"
    )


def _run_sh(run_filename, job_name):
    """Script de arranque para Linux: crea venv, instala deps, verifica Java y corre la prueba."""
    return f"""#!/usr/bin/env bash
# ============================================================
# BNX - Runner del job PySpark en Linux
# Job: {job_name}
# ============================================================
set -euo pipefail

HERE="$(cd "$(dirname "${{BASH_SOURCE[0]}}")" && pwd)"
cd "$HERE"

echo "[BNX] Verificando Java (requerido por PySpark)..."
if ! command -v java >/dev/null 2>&1; then
  echo "[BNX][ERROR] No se encontro 'java'. Instala un JDK 8/11/17. Ej (Debian/Ubuntu):"
  echo "            sudo apt-get update && sudo apt-get install -y openjdk-17-jre-headless"
  exit 1
fi
java -version || true

PYBIN="${{PYTHON:-python3}}"
echo "[BNX] Usando Python: $($PYBIN --version 2>&1)"

if [ ! -d ".venv" ]; then
  echo "[BNX] Creando entorno virtual .venv ..."
  "$PYBIN" -m venv .venv
fi
# shellcheck disable=SC1091
source .venv/bin/activate

echo "[BNX] Instalando dependencias (requirements.txt) ..."
python -m pip install --upgrade pip >/dev/null
python -m pip install -r requirements.txt

# Carpeta con los CSV de entrada del bundle de datos. Por defecto se busca el
# data_bundle descomprimido como carpeta hermana. Se puede sobreescribir.
export BNX_DATA_DIR="${{BNX_DATA_DIR:-$HERE/../data_bundle/data}}"
export BNX_BASE_PATH="${{BNX_BASE_PATH:-$HERE/_bnx_work}}"
mkdir -p "$BNX_BASE_PATH/output"

if [ ! -d "$BNX_DATA_DIR" ]; then
  echo "[BNX][WARN] No se encontro BNX_DATA_DIR=$BNX_DATA_DIR"
  echo "            Descomprime data_bundle.zip como carpeta hermana de job_bundle/,"
  echo "            o exporta BNX_DATA_DIR apuntando a la carpeta con los CSV."
fi

echo "[BNX] Ejecutando la prueba (job + datos) ..."
echo "[BNX]   BNX_DATA_DIR=$BNX_DATA_DIR"
python "{run_filename}"

echo "[BNX] Listo. Revisa la salida arriba y las escrituras reportadas."
"""


def _readme_md(job_name, datasets):
    nodes = ", ".join(d.get("node", "?") for d in datasets) or "(sin datos sinteticos)"
    return f"""# BNX — Job PySpark listo para Linux

Job: **{job_name}**

## Contenido
- `job.py` — el job PySpark generado, FIEL al grafo Ab Initio (con sus lecturas
  reales: S3/parquet, JDBC, etc.). Es el entregable para produccion.
- `run_test.py` — version AUTONOMA para PRUEBA local: intercepta las lecturas y
  las alimenta con los CSV de `data_bundle`, y reporta las escrituras. No necesita
  S3 ni bases de datos.
- `requirements.txt` — dependencias (PySpark {PYSPARK_VERSION}).
- `run.sh` — crea un venv, instala dependencias, verifica Java y ejecuta `run_test.py`.

## Requisitos en el destino (Linux)
- Python 3.9+ (`python3`).
- Un JDK (8/11/17) con `java` en el PATH — PySpark lo necesita.
- Acceso a internet para `pip install`.

## Como probar
1. Descomprime **este** zip y el `data_bundle.zip` en la MISMA carpeta padre,
   de modo que queden como carpetas hermanas:
   ```
   <padre>/
     job_bundle/    (este)
     data_bundle/   (los datos de prueba)
   ```
2. Entra a `job_bundle/` y corre:
   ```bash
   chmod +x run.sh
   ./run.sh
   ```

### Variables de entorno utiles
- `BNX_DATA_DIR` — carpeta con los CSV de entrada (default: `../data_bundle/data`).
- `BNX_BASE_PATH` — carpeta de trabajo (default: `./_bnx_work`).
- `PYTHON` — binario de Python a usar (default: `python3`).

## Datos de prueba incluidos (nodos SOURCE)
{nodes}

> Nota: los datos son SINTETICOS y redactados, generados a partir del esquema
> inferido del grafo. Sirven para validar la ejecucion, no son datos reales.
> Puedes editar los CSV de `data_bundle/data/` y volver a correr `./run.sh`.
"""


def _manifest_json(job_name, datasets):
    return json.dumps({
        "job_name": job_name,
        "generated_at": datetime.datetime.now().isoformat(),
        "pyspark_version": PYSPARK_VERSION,
        "datasets": [
            {
                "node": d.get("node"),
                "node_type": d.get("node_type"),
                "io": d.get("io"),
                "format": d.get("format", "csv"),
                "rows": d.get("rows"),
                "columns": d.get("columns"),
                "file": f"data/{_safe_name(d.get('node'))}.{d.get('format', 'csv')}",
            }
            for d in datasets
        ],
    }, indent=2, default=str)


def _safe_name(name):
    import re
    return re.sub(r'[^A-Za-z0-9_.-]', '_', str(name or "node"))


def build_job_bundle_zip(job_code, run_test_code, job_name, datasets):
    """Construye el job_bundle.zip (bytes).

    Incluye:
      - job.py: el job crudo, fiel al grafo (entregable de produccion).
      - run_test.py: script autonomo de prueba (harness) que lee los CSV del
        data_bundle via BNX_DATA_DIR y ejecuta la logica del job.
      - requirements.txt, run.sh, README.md.
    """
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr("job.py", job_code or "# (job vacio)\n")
        z.writestr("run_test.py", run_test_code or "# (script de prueba vacio)\n")
        z.writestr("requirements.txt", _requirements_txt())
        # run.sh con permisos de ejecucion (bit 0o755 en external_attr).
        info = zipfile.ZipInfo("run.sh")
        info.external_attr = 0o755 << 16
        z.writestr(info, _run_sh("run_test.py", job_name))
        z.writestr("README.md", _readme_md(job_name, datasets))
    return buf.getvalue()


def build_data_bundle_zip(datasets):
    """Construye el data_bundle.zip (bytes) con data/<nodo>.<fmt> + manifest.json."""
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as z:
        for d in datasets:
            fmt = d.get("format", "csv")
            fname = f"data/{_safe_name(d.get('node'))}.{fmt}"
            content = d.get("content", "")
            if isinstance(content, bytes):
                z.writestr(fname, content)
            else:
                z.writestr(fname, content or "")
        z.writestr("manifest.json", _manifest_json("bundle", datasets))
    return buf.getvalue()


def build_export_bundle(job_code, run_test_code, job_name, datasets):
    """Construye el ZIP contenedor final (bytes): job_bundle.zip + data_bundle.zip + README."""
    safe_job = _safe_name(job_name)
    job_zip = build_job_bundle_zip(job_code, run_test_code, job_name, datasets)
    data_zip = build_data_bundle_zip(datasets)

    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr("job_bundle.zip", job_zip)
        z.writestr("data_bundle.zip", data_zip)
        z.writestr("README.md", (
            f"# BNX export — {job_name}\n\n"
            f"Este paquete contiene DOS zips:\n\n"
            f"- `job_bundle.zip`: el job PySpark + como ejecutarlo en Linux "
            f"(venv on-demand, requirements, run.sh).\n"
            f"- `data_bundle.zip`: datos de prueba sinteticos del job.\n\n"
            f"Descomprime AMBOS en la misma carpeta padre (quedaran como "
            f"`job_bundle/` y `data_bundle/`), luego entra a `job_bundle/` y "
            f"ejecuta `./run.sh`. Ver job_bundle/README.md para detalles.\n"
        ))
    return buf.getvalue(), f"{safe_job}_export.zip"
