"""Construccion de bundles descargables para probar un job PySpark en Linux.

Produce un ZIP contenedor con DOS zips dentro:

  <job>_export.zip
    ├── job_bundle.zip        # el job + como montar el ambiente y ejecutarlo
    │     ├── job.py
    │     ├── run_test.py
    │     ├── requirements.txt
    │     ├── setup.sh         # crea el venv con TODA la arquitectura y deps
    │     ├── run.sh           # activa el venv y ejecuta la prueba
    │     └── README.md
    └── data_bundle.zip       # datos sinteticos de ENTRADA y SALIDA del job
          ├── data/input/<nodo>.csv    # fuentes (lo que lee el job)
          ├── data/output/<var>.csv    # resultados reales del job sobre esa entrada
          └── manifest.json

Diseno: el venv NO se empaqueta (un venv de macOS/una arquitectura no es portable
a Linux). En su lugar `setup.sh` crea el venv EN EL DESTINO con toda la
arquitectura (carpetas de trabajo, input/output) e instala requirements con pip.
Asi, "al descomprimir se crea el ambiente con toda la arquitectura" en un solo
paso. Java debe existir en el destino (lo verifica setup.sh). Requiere internet
para `pip install`.
"""
import io
import json
import zipfile
import datetime


def _detect_pyspark_version(default="3.5.3"):
    """Detecta la version de PySpark instalada en el entorno actual.

    Asi el bundle declara la version REAL con la que se probo el job (3.5, 4.1,
    etc.) en vez de un pin fijo. Si PySpark no esta instalado (o falla la
    deteccion), cae a un default conservador compatible (Spark 3.5)."""
    try:
        import pyspark
        v = getattr(pyspark, "__version__", None)
        if v:
            return v
    except Exception:
        pass
    # Fallback: intentar leer la version via importlib.metadata sin importar pyspark.
    try:
        from importlib import metadata as _md
        return _md.version("pyspark")
    except Exception:
        return default


# Version de PySpark detectada del entorno (se declara en requirements/manifest).
PYSPARK_VERSION = _detect_pyspark_version()


def _requirements_txt():
    # El job generado usa solo APIs estables de Spark, compatibles de 3.5 a 4.x.
    # Pineamos la version detectada del entorno (con la que se probo) pero
    # permitimos la serie compatible (>=3.5,<5) por si el destino tiene otra.
    return (
        f"# Dependencias para ejecutar el job PySpark generado por BNX.\n"
        f"# Probado con pyspark {PYSPARK_VERSION}. El job usa APIs compatibles 3.5-4.x.\n"
        f"pyspark>=3.5,<5\n"
    )


def _setup_sh(job_name):
    """setup.sh — monta TODA la arquitectura en Linux en un solo paso:
    verifica Java, crea el venv, instala dependencias y prepara las carpetas de
    trabajo (input/output/_bnx_work). Idempotente: se puede re-ejecutar."""
    return f"""#!/usr/bin/env bash
# ============================================================
# BNX - Setup del ambiente PySpark en Linux (una sola vez)
# Job: {job_name}
# Crea el venv con toda la arquitectura y deja listo para ejecutar run.sh.
# ============================================================
set -euo pipefail

HERE="$(cd "$(dirname "${{BASH_SOURCE[0]}}")" && pwd)"
cd "$HERE"

echo "[BNX] === Setup del ambiente ==="

echo "[BNX] 1/4 Verificando Java (requerido por PySpark)..."
if ! command -v java >/dev/null 2>&1; then
  echo "[BNX][ERROR] No se encontro 'java'. Instala un JDK 8/11/17. Ej (Debian/Ubuntu):"
  echo "            sudo apt-get update && sudo apt-get install -y openjdk-17-jre-headless"
  exit 1
fi
java -version || true

PYBIN="${{PYTHON:-python3}}"
echo "[BNX] 2/4 Usando Python: $($PYBIN --version 2>&1)"

echo "[BNX] 3/4 Creando entorno virtual .venv e instalando dependencias..."
if [ ! -d ".venv" ]; then
  "$PYBIN" -m venv .venv
fi
# shellcheck disable=SC1091
source .venv/bin/activate
python -m pip install --upgrade pip >/dev/null
python -m pip install -r requirements.txt

echo "[BNX] 4/4 Preparando arquitectura de carpetas de trabajo..."
# Estructura de trabajo del job (coherente con run_test.py):
#   _bnx_work/output      -> escrituras del job (SINKs)
#   data/input            -> CSV de entrada (fuentes) [viene en data_bundle]
#   data/output           -> CSV de salida de referencia [viene en data_bundle]
mkdir -p "_bnx_work/output"
mkdir -p "data/input" "data/output"

# Si existe un data_bundle hermano descomprimido, enlazamos sus datos aqui para
# que run.sh los encuentre sin configurar nada.
if [ -d "../data_bundle/data/input" ] && [ ! -e "data/input/.linked" ]; then
  cp -rn ../data_bundle/data/input/. data/input/ 2>/dev/null || true
  touch data/input/.linked
fi
if [ -d "../data_bundle/data/output" ]; then
  cp -rn ../data_bundle/data/output/. data/output/ 2>/dev/null || true
fi

echo "[BNX] === Ambiente listo ==="
echo "[BNX] Ejecuta la prueba con:  ./run.sh"
"""


def _run_sh(run_filename, job_name):
    """run.sh — asume que setup.sh ya corrio: activa el venv y ejecuta la prueba.
    Si el venv no existe, lanza setup.sh automaticamente (para que 'descomprimir y
    correr' funcione de un tiron)."""
    return f"""#!/usr/bin/env bash
# ============================================================
# BNX - Runner del job PySpark en Linux
# Job: {job_name}
# ============================================================
set -euo pipefail

HERE="$(cd "$(dirname "${{BASH_SOURCE[0]}}")" && pwd)"
cd "$HERE"

# Si el ambiente no esta montado todavia, montarlo (setup idempotente).
if [ ! -d ".venv" ]; then
  echo "[BNX] No hay .venv; ejecutando setup.sh primero..."
  bash ./setup.sh
fi

# shellcheck disable=SC1091
source .venv/bin/activate

# Carpeta con los CSV de entrada. Por defecto la que preparo setup.sh (./data/input);
# cae al data_bundle hermano si no existe. Se puede sobreescribir con BNX_DATA_DIR.
if [ -d "$HERE/data/input" ]; then
  export BNX_DATA_DIR="${{BNX_DATA_DIR:-$HERE/data/input}}"
else
  export BNX_DATA_DIR="${{BNX_DATA_DIR:-$HERE/../data_bundle/data/input}}"
fi
export BNX_BASE_PATH="${{BNX_BASE_PATH:-$HERE/_bnx_work}}"
mkdir -p "$BNX_BASE_PATH/output"

if [ ! -d "$BNX_DATA_DIR" ]; then
  echo "[BNX][WARN] No se encontro BNX_DATA_DIR=$BNX_DATA_DIR"
  echo "            Descomprime data_bundle.zip como carpeta hermana de job_bundle/,"
  echo "            o exporta BNX_DATA_DIR apuntando a la carpeta con los CSV de entrada."
fi

echo "[BNX] Ejecutando la prueba (job + datos de entrada) ..."
echo "[BNX]   BNX_DATA_DIR=$BNX_DATA_DIR"
python "{run_filename}"

echo "[BNX] Listo. Compara las escrituras con los CSV de referencia en data/output/."
"""


def _readme_md(job_name, inputs, outputs):
    in_nodes = ", ".join(d.get("node", "?") for d in inputs) or "(sin fuentes)"
    out_nodes = ", ".join(d.get("node", "?") for d in outputs) or "(sin salidas capturadas)"
    return f"""# BNX — Job PySpark listo para Linux

Job: **{job_name}**

## Contenido
- `job.py` — el job PySpark generado, FIEL al grafo Ab Initio (con sus lecturas
  reales: S3/parquet, JDBC, etc.). Es el entregable para produccion.
- `run_test.py` — version AUTONOMA para PRUEBA local: intercepta las lecturas y
  las alimenta con los CSV de entrada, y reporta las escrituras. No necesita
  S3 ni bases de datos.
- `requirements.txt` — dependencias (PySpark {PYSPARK_VERSION}).
- `setup.sh` — **monta el ambiente completo** (crea venv, instala deps, verifica
  Java y prepara la arquitectura de carpetas). Ejecutalo UNA vez.
- `run.sh` — ejecuta la prueba (si no hay venv, llama a setup.sh solo).

## Requisitos en el destino (Linux)
- Python 3.9+ (`python3`).
- Un JDK (8/11/17) con `java` en el PATH — PySpark lo necesita.
- Acceso a internet para `pip install`.

## Como montar y probar (un tiron)
1. Descomprime **este** zip y el `data_bundle.zip` en la MISMA carpeta padre,
   de modo que queden como carpetas hermanas:
   ```
   <padre>/
     job_bundle/    (este)
     data_bundle/   (datos de entrada y salida)
   ```
2. Entra a `job_bundle/` y monta el ambiente:
   ```bash
   chmod +x setup.sh run.sh
   ./setup.sh      # crea venv + instala deps + arma carpetas (una sola vez)
   ./run.sh        # ejecuta la prueba
   ```
   (Si corres `./run.sh` directo sin haber hecho setup, el runner monta el
   ambiente por ti la primera vez.)

### Variables de entorno utiles
- `BNX_DATA_DIR` — carpeta con los CSV de entrada (default: `./data/input`).
- `BNX_BASE_PATH` — carpeta de trabajo (default: `./_bnx_work`).
- `PYTHON` — binario de Python a usar (default: `python3`).

## Datos de prueba incluidos
- **Entrada (fuentes SOURCE):** {in_nodes}
- **Salida de referencia (resultado del job):** {out_nodes}

> Los datos de entrada son SINTETICOS, generados del esquema inferido del grafo.
> Los de salida son el RESULTADO REAL del job sobre esa entrada (capturados al
> generar el bundle), para que puedas comparar que tu corrida produce lo mismo.
> Puedes editar los CSV de `data_bundle/data/input/` y volver a correr `./run.sh`.
"""


def _manifest_json(job_name, inputs, outputs):
    return json.dumps({
        "job_name": job_name,
        "generated_at": datetime.datetime.now().isoformat(),
        "pyspark_version": PYSPARK_VERSION,
        "inputs": [
            {
                "node": d.get("node"),
                "node_type": d.get("node_type"),
                "io": d.get("io"),
                "format": d.get("format", "csv"),
                "rows": d.get("rows"),
                "columns": d.get("columns"),
                "file": f"data/input/{_safe_name(d.get('node'))}.{d.get('format', 'csv')}",
            }
            for d in inputs
        ],
        "outputs": [
            {
                "node": d.get("node"),
                "rows": d.get("rows"),
                "columns": d.get("columns"),
                "file": f"data/output/{_safe_name(d.get('node'))}.csv",
            }
            for d in outputs
        ],
    }, indent=2, default=str)


def _safe_name(name):
    import re
    return re.sub(r'[^A-Za-z0-9_.-]', '_', str(name or "node"))


def build_job_bundle_zip(job_code, run_test_code, job_name, inputs, outputs):
    """Construye el job_bundle.zip (bytes).

    Incluye el job crudo (produccion), el harness de prueba, requirements,
    setup.sh (monta el ambiente completo), run.sh (ejecuta) y README.
    """
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr("job.py", job_code or "# (job vacio)\n")
        z.writestr("run_test.py", run_test_code or "# (script de prueba vacio)\n")
        z.writestr("requirements.txt", _requirements_txt())
        # setup.sh y run.sh con permisos de ejecucion (bit 0o755 en external_attr).
        for fname, content in (
            ("setup.sh", _setup_sh(job_name)),
            ("run.sh", _run_sh("run_test.py", job_name)),
        ):
            info = zipfile.ZipInfo(fname)
            info.external_attr = 0o755 << 16
            z.writestr(info, content)
        z.writestr("README.md", _readme_md(job_name, inputs, outputs))
    return buf.getvalue()


def build_data_bundle_zip(inputs, outputs):
    """Construye el data_bundle.zip (bytes) con:
      data/input/<nodo>.<fmt>   -> datos sinteticos de ENTRADA
      data/output/<var>.csv     -> datos de SALIDA (resultado real del job)
      manifest.json
    """
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as z:
        for d in inputs:
            fmt = d.get("format", "csv")
            fname = f"data/input/{_safe_name(d.get('node'))}.{fmt}"
            content = d.get("content", "")
            z.writestr(fname, content if isinstance(content, (bytes, str)) else "")
        for d in outputs:
            fname = f"data/output/{_safe_name(d.get('node'))}.csv"
            content = d.get("content", "")
            z.writestr(fname, content if isinstance(content, (bytes, str)) else "")
        if not outputs:
            # Deja la carpeta presente aunque no haya salidas capturadas.
            z.writestr("data/output/.gitkeep", "")
        z.writestr("manifest.json", _manifest_json("bundle", inputs, outputs))
    return buf.getvalue()


def build_export_bundle(job_code, run_test_code, job_name, inputs, outputs=None):
    """Construye el ZIP contenedor final (bytes): job_bundle.zip + data_bundle.zip + README.

    inputs:  datasets de ENTRADA (fuentes SOURCE) con 'content' CSV.
    outputs: datasets de SALIDA (resultado real del job) con 'content' CSV.
             Puede ser None/[] si no se capturaron salidas.
    """
    outputs = outputs or []
    safe_job = _safe_name(job_name)
    job_zip = build_job_bundle_zip(job_code, run_test_code, job_name, inputs, outputs)
    data_zip = build_data_bundle_zip(inputs, outputs)

    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr("job_bundle.zip", job_zip)
        z.writestr("data_bundle.zip", data_zip)
        z.writestr("README.md", (
            f"# BNX export — {job_name}\n\n"
            f"Este paquete contiene DOS zips:\n\n"
            f"- `job_bundle.zip`: el job PySpark + como montar el ambiente en Linux "
            f"(setup.sh crea el venv con toda la arquitectura, run.sh ejecuta).\n"
            f"- `data_bundle.zip`: datos sinteticos de ENTRADA (data/input) y la "
            f"SALIDA real del job (data/output) para comparar.\n\n"
            f"Descomprime AMBOS en la misma carpeta padre (quedaran como "
            f"`job_bundle/` y `data_bundle/`), luego entra a `job_bundle/` y "
            f"ejecuta `./setup.sh` y despues `./run.sh`. Ver job_bundle/README.md.\n"
        ))
    return buf.getvalue(), f"{safe_job}_export.zip"
