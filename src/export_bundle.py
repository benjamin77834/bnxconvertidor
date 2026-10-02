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
import os
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
    # Fallback por INTERNET (si no hay vendor/ para la version de Python). El job
    # usa APIs estables compatibles 3.5-4.x; dejamos que pip elija la version de
    # PySpark compatible con el Python del destino (3.8-3.14). En modo OFFLINE,
    # setup.sh instala desde vendor/py38-311 (PySpark 3.5.6) o vendor/py312plus
    # (PySpark 4.0.0) segun la version de Python detectada.
    return (
        "# Dependencias para ejecutar el job PySpark generado por BNX.\n"
        "# Offline: setup.sh instala la serie de vendor/ segun la version de Python.\n"
        "# Internet (fallback): pip elige la PySpark compatible con tu Python.\n"
        "pyspark>=3.5,<5\n"
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

# 2/4 Seleccionar un Python >= 3.8 (PySpark lo exige). En muchos Linux 'python3'
# apunta al 3.6 del sistema; aqui autodetectamos un interprete 3.8+ entre los
# instalados. Se puede forzar con PYTHON=/ruta/a/python ./setup.sh
echo "[BNX] 2/4 Seleccionando Python >= 3.8 ..."

_py_ok() {{  # $1 = binario; devuelve 0 si es Python >= 3.8
  "$1" -c 'import sys; sys.exit(0 if sys.version_info[:2] >= (3,8) else 1)' >/dev/null 2>&1
}}

PYBIN=""
if [ -n "${{PYTHON:-}}" ]; then
  # Respetar el que el usuario fuerce (si cumple).
  if _py_ok "$PYTHON"; then PYBIN="$PYTHON"; else
    echo "[BNX][ERROR] PYTHON=$PYTHON no es Python >= 3.8."; exit 1
  fi
else
  # Probar candidatos comunes en orden (de mas nuevo a mas viejo).
  for c in python3.12 python3.11 python3.10 python3.9 python3.8 python3 python; do
    if command -v "$c" >/dev/null 2>&1 && _py_ok "$c"; then PYBIN="$c"; break; fi
  done
fi

if [ -z "$PYBIN" ]; then
  echo "[BNX][ERROR] No se encontro Python >= 3.8 (PySpark lo requiere)."
  echo "            Este Linux parece tener solo Python antiguo (p.ej. 3.6)."
  echo "            Instala/activa Python 3.8+ o indicalo:  PYTHON=python3.9 ./setup.sh"
  exit 1
fi
echo "[BNX]     Usando Python: $($PYBIN --version 2>&1)  ($PYBIN)"

echo "[BNX] 3/4 Creando entorno virtual .venv e instalando dependencias..."
if [ ! -d ".venv" ]; then
  "$PYBIN" -m venv .venv
fi
# shellcheck disable=SC1091
source .venv/bin/activate

# Instalacion de PySpark. El bundle trae wheels OFFLINE en vendor/ organizados por
# rango de Python (vendor/py38-311 y vendor/py312plus). Elegimos la carpeta segun
# la MINOR del Python del venv, asi cubrimos Python 3.8 a 3.14 sin tema de version.
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
  echo "[BNX]     Instalacion OFFLINE desde $VENDOR_DIR (Python 3.$PYMINOR, sin internet)."
  python -m pip install --no-index --find-links "$VENDOR_DIR" pip setuptools wheel >/dev/null 2>&1 || true
  python -m pip install --no-index --find-links "$VENDOR_DIR" pyspark py4j
else
  echo "[BNX]     vendor/ no encontrado o sin wheels para Python 3.$PYMINOR; instalando desde internet (pip)."
  python -m pip install --upgrade pip >/dev/null
  python -m pip install -r requirements.txt
fi

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

# Driver Y workers de Spark con el MISMO Python del venv. Sin esto, Spark lanza
# los workers con el python3 del sistema y falla con PYTHON_VERSION_MISMATCH si
# ese python3 tiene otra version minor que el venv.
export PYSPARK_PYTHON="$HERE/.venv/bin/python"
export PYSPARK_DRIVER_PYTHON="$HERE/.venv/bin/python"

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
- `vendor/` — **los paquetes de PySpark + py4j incluidos en el bundle**, en DOS
  series por rango de Python para cubrir 3.8-3.14 sin tema de version:
  `vendor/py38-311/` (PySpark 3.5.6) y `vendor/py312plus/` (PySpark 4.0.0).
  setup.sh elige la serie segun la version de Python detectada e instala SIN
  internet. (Si se exporto sin vendor/, setup.sh usa pip por internet.)
- `setup.sh` — **monta el ambiente completo** (crea venv, instala deps desde
  vendor/ offline, verifica Java y prepara la arquitectura de carpetas).
  Ejecutalo UNA vez.
- `run.sh` — ejecuta la prueba (si no hay venv, llama a setup.sh solo).

## Requisitos en el destino (Linux)
- Python 3.8+ (`python3`).
- Un JDK (8/11/17) con `java` en el PATH — PySpark lo necesita.
- Internet solo si el bundle NO trae `vendor/` (si lo trae, la instalacion es offline).

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


# Para cubrir TODO el rango Python 3.8-3.14 empaquetamos DOS series de PySpark en
# vendor/, en subcarpetas por rango de Python; setup.sh elige segun la version:
#   vendor/py38-311/  -> PySpark 3.5.6 (serie 3.5, soporta Python 3.8-3.11)
#   vendor/py312plus/ -> PySpark 4.0.0 (serie 4.0, soporta Python 3.9-3.13/3.14)
# Los .whl de PySpark/py4j son 'py2.py3-none-any' (Python puro, cualquier Linux);
# el unico binario nativo que necesita es Java (en el destino). Asi, caiga en el
# Python que caiga el Linux del banco, se instala el PySpark compatible.
VENDOR_SERIES = [
    {"dir": "py38-311", "pyspark": "pyspark==3.5.6", "py4j": "py4j==0.10.9.7",
     "download_py": "3.8", "min": (3, 8), "max": (3, 11)},
    {"dir": "py312plus", "pyspark": "pyspark==4.0.0", "py4j": "py4j==0.10.9.9",
     "download_py": "3.12", "min": (3, 12), "max": (3, 14)},
]

# Cache de dependencias en el server para no re-descargar/reconstruir en cada
# exportacion. Vive fuera de git (raiz del proyecto).
_VENDOR_CACHE_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".bnx_vendor_cache"
)

def _build_series(cache_dir, serie):
    """Prepara los wheels de UNA serie de PySpark en cache_dir/<serie.dir>/:
    PySpark (sdist->wheel), py4j y setuptools/wheel/pip. Idempotente (reusa cache).
    Devuelve la lista de .whl de esa serie (o [] si falla)."""
    import subprocess, sys, glob
    sdir = os.path.join(cache_dir, serie["dir"])
    os.makedirs(sdir, exist_ok=True)
    dpy = serie["download_py"]

    # setuptools/wheel/pip (respaldo de build offline en destino).
    if not glob.glob(os.path.join(sdir, "setuptools-*.whl")):
        try:
            subprocess.run(
                [sys.executable, "-m", "pip", "download", "setuptools", "wheel", "pip",
                 "--only-binary=:all:", "--python-version", dpy,
                 "--implementation", "py", "--abi", "none", "--platform", "any",
                 "-d", sdir],
                check=True, capture_output=True, text=True, timeout=600)
        except Exception:
            pass
    # py4j (wheel universal).
    if not glob.glob(os.path.join(sdir, "py4j-*.whl")):
        try:
            subprocess.run(
                [sys.executable, "-m", "pip", "download", serie["py4j"],
                 "--only-binary=:all:", "--no-deps", "-d", sdir],
                check=True, capture_output=True, text=True, timeout=600)
        except Exception:
            pass
    # PySpark: bajar sdist y construir el wheel una vez.
    if not glob.glob(os.path.join(sdir, "pyspark-*.whl")):
        try:
            subprocess.run(
                [sys.executable, "-m", "pip", "download", serie["pyspark"],
                 "--no-deps", "--no-binary=pyspark",
                 "--python-version", dpy, "-d", sdir],
                check=True, capture_output=True, text=True, timeout=2400)
            sdists = glob.glob(os.path.join(sdir, "pyspark-*.tar.gz"))
            if sdists:
                subprocess.run(
                    [sys.executable, "-m", "pip", "wheel", sdists[0], "--no-deps", "-w", sdir],
                    check=True, capture_output=True, text=True, timeout=2400)
                for s in sdists:
                    try:
                        os.remove(s)
                    except OSError:
                        pass
        except Exception:
            pass
    return sorted(glob.glob(os.path.join(sdir, "*.whl")))


def fetch_vendor_files(cache_dir=None):
    """Prepara (y cachea) los wheels de TODAS las series de PySpark para cubrir
    Python 3.8-3.14. Devuelve un dict {serie_dir: [rutas .whl]} para empaquetar
    cada serie en vendor/<serie_dir>/ dentro del bundle.

    No construye venvs (no son portables). Empaqueta wheels py2.py3-none-any
    (Python puro, cualquier Linux). setup.sh elige la serie segun el Python del
    destino. Si pip falla, devuelve {} y el bundle cae a instalacion por internet."""
    cache_dir = cache_dir or _VENDOR_CACHE_DIR
    os.makedirs(cache_dir, exist_ok=True)
    out = {}
    for serie in VENDOR_SERIES:
        whls = _build_series(cache_dir, serie)
        if whls:
            out[serie["dir"]] = whls
    return out


def _add_job_files(z, prefix, job_code, run_test_code, job_name, inputs, outputs,
                   vendor_series=None):
    """Escribe en el ZIP 'z' los archivos del job bajo 'prefix' (p.ej. 'job_bundle/').
    Incluye el job, el harness, requirements, setup.sh, run.sh, README y, si se
    pasa vendor_series (dict {serie_dir: [whls]}), los paquetes de cada serie en
    vendor/<serie_dir>/ para instalacion OFFLINE segun la version de Python."""
    z.writestr(prefix + "job.py", job_code or "# (job vacio)\n")
    z.writestr(prefix + "run_test.py", run_test_code or "# (script de prueba vacio)\n")
    z.writestr(prefix + "requirements.txt", _requirements_txt())
    for fname, content in (
        ("setup.sh", _setup_sh(job_name)),
        ("run.sh", _run_sh("run_test.py", job_name)),
    ):
        info = zipfile.ZipInfo(prefix + fname)
        info.external_attr = 0o755 << 16  # ejecutable
        z.writestr(info, content)
    z.writestr(prefix + "README.md", _readme_md(job_name, inputs, outputs))
    # Paquetes para instalacion offline, por serie en vendor/<serie_dir>/.
    # ZIP_STORED porque un .whl ya esta comprimido (no gana nada recomprimir).
    for serie_dir, whls in (vendor_series or {}).items():
        for fpath in whls:
            try:
                with open(fpath, "rb") as fh:
                    data = fh.read()
            except OSError:
                continue
            info = zipfile.ZipInfo(prefix + f"vendor/{serie_dir}/" + os.path.basename(fpath))
            info.compress_type = zipfile.ZIP_STORED
            z.writestr(info, data)


def _add_data_files(z, prefix, inputs, outputs):
    """Escribe en el ZIP 'z' los datos bajo 'prefix' (p.ej. 'data_bundle/'):
    data/input/<nodo>.<fmt>, data/output/<var>.csv y manifest.json."""
    for d in inputs:
        fmt = d.get("format", "csv")
        fname = prefix + f"data/input/{_safe_name(d.get('node'))}.{fmt}"
        content = d.get("content", "")
        z.writestr(fname, content if isinstance(content, (bytes, str)) else "")
    for d in outputs:
        fname = prefix + f"data/output/{_safe_name(d.get('node'))}.csv"
        content = d.get("content", "")
        z.writestr(fname, content if isinstance(content, (bytes, str)) else "")
    if not outputs:
        z.writestr(prefix + "data/output/.gitkeep", "")
    if not inputs:
        z.writestr(prefix + "data/LEEME.txt", (
            "No se generaron datos sinteticos de ENTRADA para este grafo.\n\n"
            "Causas tipicas:\n"
            "  - El grafo no declara un esquema inferible en sus nodos SOURCE\n"
            "    (sin .dml/.xfr que describan columnas, o formato .mp simplificado).\n"
            "  - Se exporto sin un grafo .mp valido cargado.\n\n"
            "Que hacer:\n"
            "  - Carga el .mp (y .xfr/.dml si los tienes) en la pestana Data\n"
            "    Sintetica, pulsa 'Generar datos' y confirma que aparecen columnas\n"
            "    por nodo; luego vuelve a exportar el bundle.\n"
            "  - O coloca tus propios CSV en data/input/ con el nombre de cada\n"
            "    fuente y corre ./run.sh.\n"
        ))
    z.writestr(prefix + "manifest.json", _manifest_json("bundle", inputs, outputs))


def build_export_bundle(job_code, run_test_code, job_name, inputs, outputs=None,
                        include_vendor=True):
    """Construye el ZIP de exportacion (bytes). UN SOLO zip PLANO (sin zips
    anidados) con carpetas job_bundle/ y data_bundle/.

    IMPORTANTE: antes se anidaban dos .zip dentro de un contenedor .zip. La
    Utilidad de Compresion de macOS falla al abrir ese anidamiento ('Error 0 -
    Error no definido'), sobre todo con el wheel grande de PySpark almacenado.
    Un unico zip plano lo abre cualquier descompresor (macOS incluido) de un
    doble clic, y PySpark sigue viajando dentro en job_bundle/vendor/.

    include_vendor: si True, empaqueta PySpark+py4j en job_bundle/vendor/ para
             instalacion OFFLINE en Linux (wheels py2.py3-none-any, compatibles
             con cualquier Linux y Python 3.8-3.14).
    """
    outputs = outputs or []
    safe_job = _safe_name(job_name)
    vendor_series = fetch_vendor_files() if include_vendor else {}

    buf = io.BytesIO()
    # allowZip64=True: necesario cuando se incluye el wheel de PySpark (~317 MB).
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED, allowZip64=True) as z:
        _add_job_files(z, "job_bundle/", job_code, run_test_code, job_name,
                       inputs, outputs, vendor_series=vendor_series)
        _add_data_files(z, "data_bundle/", inputs, outputs)
        series_txt = ", ".join(sorted(vendor_series.keys())) if vendor_series else ""
        offline = (f"SI (PySpark offline por version de Python: {series_txt})"
                   if vendor_series else "NO (setup.sh instala por internet)")
        z.writestr("LEEME.txt", (
            f"BNX export - {job_name}\n"
            f"=========================================\n\n"
            f"Instalacion offline: {offline}\n\n"
            f"Estructura:\n"
            f"  job_bundle/   el job PySpark + setup.sh (monta el ambiente) + run.sh\n"
            f"  data_bundle/  data/input (entrada sintetica) y data/output (salida real)\n\n"
            f"Pasos en Linux:\n"
            f"  1. Descomprime este zip (en macOS: doble clic o 'unzip').\n"
            f"  2. cd job_bundle\n"
            f"  3. ./setup.sh    (crea el venv e instala PySpark; offline si hay vendor/)\n"
            f"  4. ./run.sh      (ejecuta el job con los datos de entrada)\n\n"
            f"Nota: data_bundle/ queda como carpeta hermana de job_bundle/, que es\n"
            f"donde setup.sh/run.sh esperan los datos por defecto.\n"
        ))
    return buf.getvalue(), f"{safe_job}_export.zip"
