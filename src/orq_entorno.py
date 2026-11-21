# -*- coding: utf-8 -*-
"""
orq_entorno.py — Entorno virtual del Orquestador para RHEL 8 x86_64 Python 3.11.

Genera  bnx_orq_env_py3.11_linux.zip  que al descomprimir contiene:
  setup.sh                 — crea el .venv offline
  run.sh                   — ejecuta un *_spark.py en local[*] o YARN
  bnx_spark_resources.conf — recursos YARN editables por el usuario
  requirements.txt         — paquetes minimos
  requirements_completo.txt — paquetes extra de ciencia de datos
  vendor/                  — wheels offline Linux Python 3.11
  README.md                — descripcion y uso

Reutiliza al maximo vendor_cache / vendor_modular.
Compatible con Python 3.8 (host del portal).
"""
import datetime
import hashlib
import io
import json
import os
import re
import zipfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


# ---- Cierre de dependencias sobre las wheels que hay en el cache -------------------------------
_ENV_MARCADORES = {
    "python_version": "3.11", "python_full_version": "3.11.13", "sys_platform": "linux",
    "platform_system": "Linux", "platform_machine": "x86_64", "implementation_name": "cpython",
    "os_name": "posix", "platform_python_implementation": "CPython", "extra": "",
}


def _norm(n):
    return re.sub(r"[-_.]+", "-", str(n)).lower()


def _nombre_dist(path):
    return _norm(os.path.basename(path).split("-")[0])


def _requiere(path, log=None):
    """Nombres (normalizados) de las dependencias de una wheel que aplican a Linux/py3.11.
    Una wheel ilegible se trata como sin dependencias (con aviso por `log`)."""
    try:
        with zipfile.ZipFile(path) as z:
            meta = [n for n in z.namelist() if n.endswith(".dist-info/METADATA")]
            texto = z.read(meta[0]).decode("utf-8", "replace") if meta else ""
    except (OSError, zipfile.BadZipFile, KeyError, RuntimeError):
        if log:
            log("[orq_entorno] AVISO: wheel ilegible, se asume sin dependencias: %s"
                % os.path.basename(path))
        return []
    try:
        from packaging.markers import Marker
    except ImportError:
        Marker = None
    out = []
    for ln in texto.splitlines():
        if not ln.startswith("Requires-Dist:"):
            continue
        spec, _, marca = ln[len("Requires-Dist:"):].strip().partition(";")
        marca = marca.strip()
        if "extra" in marca:
            continue                       # dependencias opcionales: no se instalan por defecto
        if marca and Marker is not None:
            try:
                if not Marker(marca).evaluate(_ENV_MARCADORES):
                    continue
            except Exception:
                pass
        m = re.match(r"\s*([A-Za-z0-9][A-Za-z0-9._\-]*)", spec)
        if m:
            out.append(_norm(m.group(1)))
    return out


def cierre_wheels(wheels, raices, log=None):
    """(wheels necesarias, dependencias que NO estan en `wheels`) partiendo de las `raices`
    (nombres de paquete, con o sin version). Asi 'minimo' lleva solo lo que de verdad se instala."""
    por_nombre = {}
    for w in wheels:
        por_nombre.setdefault(_nombre_dist(w), w)
    pendientes = [_norm(re.split(r"[<>=!~\[ ;]", r, maxsplit=1)[0]) for r in raices]
    vistos, elegidas, faltan = set(), [], []
    while pendientes:
        n = pendientes.pop()
        if n in vistos:
            continue
        vistos.add(n)
        w = por_nombre.get(n)
        if not w:
            faltan.append(n)
            continue
        elegidas.append(w)
        pendientes.extend(_requiere(w, log))
    return sorted(elegidas), sorted(set(faltan))

ZIP_NOMBRE = "bnx_orq_env_py3.11_linux.zip"
PYTHON_TARGET = "3.11"
VENDOR_SUBDIR = "py38-311"      # serie PySpark 3.5.6 / Python 3.8-3.11

REQS_MINIMO = [
    "pyspark==3.5.6",
    "py4j",
    "pandas",
    "numpy",
    "cytoolz",
    "toolz",
    "chispa",
    "pytest",
]
REQS_EXTRA = [
    "xgboost",
    "scikit-learn",
    "scipy",
    "joblib",
]

# Claves de configuracion YARN con sus valores por defecto y descripcion
YARN_CONF_DEFAULTS = [
    ("spark.yarn.queue",                      "default",    "Cola YARN donde se ejecutan los jobs"),
    ("spark.executor.instances",              "2",          "Numero de executors"),
    ("spark.executor.cores",                  "2",          "Cores por executor"),
    ("spark.executor.memory",                 "4g",         "Memoria por executor (ej. 4g, 8g)"),
    ("spark.executor.memoryOverhead",         "1g",         "Overhead de memoria del executor"),
    ("spark.driver.memory",                   "2g",         "Memoria del driver"),
    ("spark.sql.shuffle.partitions",          "200",        "Particiones de shuffle de Spark SQL"),
    ("spark.dynamicAllocation.enabled",       "false",      "Activar asignacion dinamica (true/false)"),
    ("spark.dynamicAllocation.minExecutors",  "1",          "Minimo de executors (si dynamicAllocation=true)"),
    ("spark.dynamicAllocation.maxExecutors",  "10",         "Maximo de executors (si dynamicAllocation=true)"),
]

# ------------------------------------------------------------------ setup.sh
_SETUP_SH = r"""#!/usr/bin/env bash
# setup.sh — Monta el entorno virtual del Orquestador BNX (una sola vez).
# PySpark 3.5.6 + Python 3.11 + dependencias OFFLINE.
#
# Uso:
#   bash setup.sh             # variante minima (pyspark+pandas+numpy+deps)
#   bash setup.sh --completo  # +ciencia de datos (xgboost, scikit-learn, scipy)
#
# Requisitos: Python 3.11  (RHEL 8: sudo dnf install python3.11)
#             Java 8/11/17 (RHEL 8: sudo dnf install java-17-openjdk-headless)
set -e
trap 'rc=$?; if [ "$rc" -ne 0 ] && [ -z "${BNX_SETUP_FIN:-}" ]; then
  echo "[setup] ABORTADO (codigo $rc): el .venv puede quedar incompleto."
  echo "        Corrige lo anterior y vuelve a correr: bash setup.sh"
  rm -f .venv/.bnx_orq_ok 2>/dev/null; fi' EXIT

BNX_COMPLETO=0
for _a in "$@"; do
  case "$_a" in --completo) BNX_COMPLETO=1 ;; esac
done

# ---- Verificar Java ----
if ! command -v java >/dev/null 2>&1 && [ -z "${JAVA_HOME:-}" ]; then
  echo "[!] No encuentro Java. PySpark 3.5 necesita Java 8/11/17."
  echo "    RHEL 8: sudo dnf install java-17-openjdk-headless"
fi

# ---- Encontrar Python 3.11 ----
if [ -n "${PYTHON:-}" ]; then
  PY="$PYTHON"
elif command -v python3.11 >/dev/null 2>&1; then
  PY="python3.11"
else
  PY="python3"
fi
PY_V="$("$PY" -c 'import sys; print("%d.%d" % sys.version_info[:2])' 2>/dev/null || echo '')"
if [ "$PY_V" != "3.11" ]; then
  echo "[ERROR] Se necesita Python 3.11 (encontrado: ${PY_V:-ninguno})."
  echo "        RHEL 8: sudo dnf install python3.11"
  echo "        O:  PYTHON=/usr/bin/python3.11 bash setup.sh"
  exit 1
fi

echo "[1/3] Creando .venv con Python 3.11 ..."
"$PY" -m venv .venv
. .venv/bin/activate

echo "[2/3] Instalando dependencias OFFLINE desde vendor/ ..."
python -m pip install --quiet --upgrade pip --no-index --find-links vendor/ 2>/dev/null || true
python -m pip install --no-index --find-links vendor/ -r requirements.txt

if [ "$BNX_COMPLETO" = "1" ]; then
  if [ -f requirements_completo.txt ]; then
    echo "      +ciencia de datos ..."
    python -m pip install --no-index --find-links vendor/ -r requirements_completo.txt
  else
    echo "[AVISO] Este ZIP es la variante MINIMA: no trae la ciencia de datos. Genera el ZIP 'completo' desde el Orquestador."
  fi
fi

# ---- PYSPARK_PYTHON y PYSPARK_DRIVER_PYTHON ----
VPY="$(command -v python)"
{
  echo "export PYSPARK_PYTHON=\"$VPY\""
  echo "export PYSPARK_DRIVER_PYTHON=\"$VPY\""
} >> .venv/bin/activate
echo "      PYSPARK_PYTHON=$VPY"

echo "[3/3] Verificando PySpark ..."
python -c "import pyspark; print('  PySpark', pyspark.__version__, 'OK')" || {
  echo "[!] PySpark no pudo importarse; revisa que Java este instalado."
}
python -c "import pandas, numpy, pytest; print('  pandas/numpy/pytest OK')"

touch .venv/.bnx_orq_ok
BNX_SETUP_FIN=1
echo ""
echo "Entorno listo."
echo "  Local:   bash run.sh output/proyecto/job_spark.py"
echo "  Cluster: BNX_SPARK=cluster bash run.sh output/proyecto/job_spark.py"
"""

# ------------------------------------------------------------------ run.sh
_RUN_SH = r"""#!/usr/bin/env bash
# run.sh — Ejecuta un job convertido (*_spark.py) del Orquestador BNX.
#
# Modos:
#   Local (default):
#     bash run.sh <job_spark.py> [BNX_BASE_PATH=/ruta/datos]
#     Corre en local[*] con el .venv del setup.sh (sin cluster).
#
#   Cluster YARN:
#     BNX_SPARK=cluster bash run.sh <job_spark.py> [BNX_BASE_PATH=/ruta/datos]
#     Usa spark-submit con --master yarn --deploy-mode client.
#     Edita bnx_spark_resources.conf para ajustar queue/memoria/cores.
set -e
JOB="${1:-}"
if [ -z "$JOB" ]; then
  echo "Uso: bash run.sh <job_spark.py> [BNX_BASE_PATH=/ruta/datos]"
  echo "     BNX_SPARK=cluster bash run.sh <job_spark.py> [BNX_BASE_PATH=/ruta/datos]"
  exit 1
fi
if [ ! -f .venv/.bnx_orq_ok ]; then
  echo "[ERROR] Entorno no montado. Corre primero: bash setup.sh"
  exit 1
fi
. .venv/bin/activate
export PYSPARK_PYTHON="$(command -v python)"
export PYSPARK_DRIVER_PYTHON="$(command -v python)"

# Resto de args: variables de entorno opcionales (clave=valor)
shift || true
for _arg in "$@"; do
  export "$_arg" 2>/dev/null || true
done

echo "[run] job=$JOB  BNX_BASE_PATH=${BNX_BASE_PATH:-no definido}  BNX_SPARK=${BNX_SPARK:-local}"

if [ "${BNX_SPARK:-}" = "cluster" ]; then
  # ---- Modo YARN cluster ----
  # Buscar spark-submit (spark3-submit en RHEL 8 con HDP/CDP, o spark-submit del PATH/SPARK_HOME)
  SUBMIT=""
  if command -v spark3-submit >/dev/null 2>&1; then
    SUBMIT="spark3-submit"
  elif command -v spark-submit >/dev/null 2>&1; then
    SUBMIT="spark-submit"
  elif [ -n "${SPARK_HOME:-}" ] && [ -f "$SPARK_HOME/bin/spark-submit" ]; then
    SUBMIT="$SPARK_HOME/bin/spark-submit"
  else
    echo "[ERROR] No encuentro spark-submit ni spark3-submit en el PATH ni en SPARK_HOME."
    echo "        En RHEL 8 con HDP: sudo alternatives --config spark-submit"
    exit 1
  fi

  # Leer bnx_spark_resources.conf y convertir en args --conf
  CONF_ARGS=""
  if [ -f bnx_spark_resources.conf ]; then
    while IFS='=' read -r key val; do
      # ignorar comentarios y lineas vacias
      key="$(echo "$key" | sed 's/[[:space:]]//g')"
      val="$(echo "$val" | sed 's/^[[:space:]]*//')"
      case "$key" in
        \#*|'') continue ;;
      esac
      if [ -n "$key" ] && [ -n "$val" ]; then
        CONF_ARGS="$CONF_ARGS --conf ${key}=${val}"
      fi
    done < bnx_spark_resources.conf
  fi

  echo "[run] modo YARN: $SUBMIT --master yarn --deploy-mode client $CONF_ARGS $JOB"
  # shellcheck disable=SC2086
  exec "$SUBMIT" \
    --master yarn \
    --deploy-mode client \
    $CONF_ARGS \
    "$JOB"
else
  # ---- Modo local (default, para pruebas en el edge node) ----
  exec python "$JOB"
fi
"""

# ------------------------------------------------------------------ bnx_spark_resources.conf
def _spark_resources_conf(spark_conf=None):
    """Genera el contenido de bnx_spark_resources.conf.

    spark_conf: dict opcional {clave: valor} guardado en la orquestacion del proyecto.
    """
    lines = [
        "# bnx_spark_resources.conf — Recursos YARN para el Orquestador BNX",
        "# Edita este archivo antes de lanzar con BNX_SPARK=cluster.",
        "# Formato: clave=valor (una por linea; # = comentario)",
        "#",
    ]
    conf_map = {k: v for k, v, _ in YARN_CONF_DEFAULTS}
    if spark_conf and isinstance(spark_conf, dict):
        for k, v in spark_conf.items():
            conf_map[k] = str(v)

    for key, _default, desc in YARN_CONF_DEFAULTS:
        lines.append("# %s" % desc)
        lines.append("%s=%s" % (key, conf_map.get(key, _default)))
        lines.append("")
    return "\n".join(lines) + "\n"


# ------------------------------------------------------------------ README
_README_TPL = u"""# Entorno del Orquestador BNX \u2014 Python 3.11 / PySpark 3.5.6

Paquete offline para correr los jobs convertidos (`*_spark.py`) en servidores
RHEL\u00a08 x86\u202f64 **sin internet**.

## Contenido

| Archivo | Descripci\u00f3n |
|---|---|
| `setup.sh` | Crea el `.venv` e instala todo OFFLINE |
| `run.sh` | Ejecuta un job `*_spark.py` (local o YARN) |
| `bnx_spark_resources.conf` | Recursos YARN editables |
| `requirements.txt` | Paquetes m\u00ednimos |
| `requirements_completo.txt` | + ciencia de datos |
| `vendor/` | Wheels offline Linux Python 3.11 |

## Requisitos (servidor RHEL 8)

```bash
sudo dnf install python3.11 java-17-openjdk-headless
```

## Uso

### 1. Descomprimir

```bash
unzip bnx_orq_env_py3.11_linux.zip -d bnx_orq_env
cd bnx_orq_env
```

### 2. Montar el entorno (una sola vez)

```bash
bash setup.sh           # variante m\u00ednima
bash setup.sh --completo  # + xgboost, scikit-learn, scipy
```

### 3. Correr un job \u2014 modo local (edge node)

```bash
bash run.sh /ruta/al/job_spark.py BNX_BASE_PATH=/datos/bnx
```

Corre en `local[*]` usando el `.venv`. Ideal para probar en el edge node
sin consumir recursos del cluster.

### 4. Correr un job \u2014 modo YARN (cluster)

```bash
BNX_SPARK=cluster bash run.sh /ruta/al/job_spark.py BNX_BASE_PATH=/datos/bnx
```

Usa `spark-submit --master yarn --deploy-mode client` con los par\u00e1metros
de `bnx_spark_resources.conf`.

#### Configurar recursos YARN

Edita `bnx_spark_resources.conf` antes de lanzar:

```
spark.yarn.queue=mi_cola
spark.executor.instances=4
spark.executor.cores=4
spark.executor.memory=8g
spark.driver.memory=4g
```

Los par\u00e1metros se pasan como `--conf clave=valor` al `spark-submit`.

### Notas

- `spark3-submit` (HDP/CDP en RHEL 8) se detecta autom\u00e1ticamente.
- Para asignaci\u00f3n din\u00e1mica: pon `spark.dynamicAllocation.enabled=true` en el conf.
- El `.venv` se crea en `./` (junto a `setup.sh`).
- Generado por Portal BNX \u2014 {fecha}. Variante: **{variante}**.
"""


def _mb(n):
    return round(n / 1048576.0, 1)


def _sha256_bytes(data):
    return hashlib.sha256(data).hexdigest()


def estado_cache():
    """Estado de las piezas del cache necesarias para el ZIP del Orquestador.

    Devuelve dict con:
      pyspark: {ok, mb, falta, wheels}
      ciencia: {ok, mb, falta, n_wheels}
      banco:   {ok, sdists, sdists_faltan, pkgcode, pkgcode_faltan}
    """
    from src import vendor_cache as vc
    from src import vendor_modular as vm

    cache = vc.cache_dir()
    v = PYTHON_TARGET

    # --- PySpark ---
    ws_spark = vc.wheels_exactas_viejas(cache, v)
    ps_wheels = [w for w in ws_spark if os.path.basename(w).startswith("pyspark-")]
    py4j_wheels = [w for w in ws_spark if os.path.basename(w).startswith("py4j-")]
    pyspark_ok = bool(ps_wheels and py4j_wheels)
    pyspark_mb = _mb(sum(os.path.getsize(w) for w in ws_spark)) if ws_spark else 0
    pyspark_falta = []
    if not ps_wheels:
        pyspark_falta.append("pyspark==3.5.6")
    if not py4j_wheels:
        pyspark_falta.append("py4j")

    # --- Ciencia (wheels de dependencias Linux Python 3.11) ---
    ciencia_ws = []
    try:
        ciencia_ws = vm._wheels(vm.dir_pieza(cache, "ciencia", v, "linux"))
        if not ciencia_ws:
            d = os.path.join(cache, "mlops_deps", VENDOR_SUBDIR + "_ciencia")
            if os.path.isdir(d):
                ciencia_ws = [f for f in vm._wheels(d) if vm.wheel_compatible(f, v, "linux")]
    except Exception:
        ciencia_ws = []
    ciencia_mb = _mb(sum(os.path.getsize(w) for w in ciencia_ws))
    ciencia_ok = bool(ciencia_ws)
    ciencia_falta = [] if ciencia_ok else ["ciencia-linux-py3.11.zip (no importado)"]

    # --- Banco ---
    banco_st = vc.estado_banco(cache)

    return {
        "pyspark": {"ok": pyspark_ok, "mb": pyspark_mb, "falta": pyspark_falta,
                    "wheels": [os.path.basename(w) for w in ws_spark]},
        "ciencia": {"ok": ciencia_ok, "mb": ciencia_mb, "falta": ciencia_falta,
                    "n_wheels": len(ciencia_ws)},
        "banco": {"ok": not (banco_st["sdists_faltan"] or banco_st["pkgcode_faltan"]),
                  "sdists": banco_st["sdists"], "sdists_faltan": banco_st["sdists_faltan"],
                  "pkgcode": banco_st["pkgcode"], "pkgcode_faltan": banco_st["pkgcode_faltan"]},
    }


def generar_zip(variante="minimo", spark_conf=None, log=None, cache=None):
    """Genera el ZIP offline del entorno del Orquestador.

    variante:   'minimo' | 'completo'
    spark_conf: dict de claves spark.* guardadas desde la UI (para bnx_spark_resources.conf)
    Devuelve (bytes_del_zip, sha256, nombre_archivo).
    """
    if log is None:
        log = lambda *_: None
    from src import vendor_cache as vc
    from src import vendor_modular as vm

    cache = cache or vc.cache_dir()
    v = PYTHON_TARGET
    variante = "completo" if variante == "completo" else "minimo"

    log("[orq_entorno] preparando ZIP '%s' (Python %s, PySpark 3.5.6) ..." % (variante, v))

    # Recopilar wheels de pyspark+py4j
    ws_spark = vc.wheels_exactas_viejas(cache, v)
    if not ws_spark:
        raise ValueError(
            "No hay wheels de PySpark en el cache para Python %s. "
            "Usa 'Bajar desde GitHub' en la seccion Entorno de ejecucion." % v)

    # Recopilar wheels de dependencias Linux
    ciencia_ws = []
    try:
        ciencia_ws = vm._wheels(vm.dir_pieza(cache, "ciencia", v, "linux"))
        if not ciencia_ws:
            d = os.path.join(cache, "mlops_deps", VENDOR_SUBDIR + "_ciencia")
            if os.path.isdir(d):
                ciencia_ws = [f for f in vm._wheels(d) if vm.wheel_compatible(f, v, "linux")]
    except Exception:
        ciencia_ws = []

    reqs_extra_l = [vm.mapear_requisito(d, "linux") for d in REQS_EXTRA]   # xgboost -> xgboost-cpu
    raices = list(REQS_MINIMO) + (reqs_extra_l if variante == "completo" else [])
    todas = list(ws_spark) + list(ciencia_ws)
    elegidas, faltan = cierre_wheels(todas, raices, log)
    if faltan:
        raise ValueError(
            "Faltan en el cache wheels para Linux/Python %s: %s. Usa 'Bajar desde GitHub' o importa "
            "la pieza 'ciencia-linux-py%s.zip' (sin ellas setup.sh no podria instalar offline)."
            % (v, ", ".join(faltan), v))
    ws_spark = [w for w in elegidas if w in set(ws_spark)]
    ciencia_ws = [w for w in elegidas if w not in set(ws_spark)]
    fecha = datetime.datetime.now().strftime("%Y-%m-%d")
    reqs_base = "\n".join(REQS_MINIMO) + "\n"
    reqs_extra = "\n".join(reqs_extra_l) + "\n"
    conf_txt = _spark_resources_conf(spark_conf)
    readme_txt = _README_TPL.format(fecha=fecha, variante=variante)

    buf = io.BytesIO()
    total_wheels = 0
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED, allowZip64=True) as z:
        z.writestr("setup.sh", _SETUP_SH.lstrip())
        z.writestr("run.sh", _RUN_SH.lstrip())
        z.writestr("README.md", readme_txt)
        z.writestr("requirements.txt", reqs_base)
        if variante == "completo":
            z.writestr("requirements_completo.txt", reqs_extra)
        z.writestr("bnx_spark_resources.conf", conf_txt)

        for w in ws_spark:
            z.write(w, "vendor/" + os.path.basename(w))
            total_wheels += 1
            log("  + pyspark: %s" % os.path.basename(w))

        for w in ciencia_ws:
            z.write(w, "vendor/" + os.path.basename(w))
            total_wheels += 1

        log("  wheels totales: %d" % total_wheels)

    data = buf.getvalue()
    sha = _sha256_bytes(data)
    mb = _mb(len(data))
    log("[orq_entorno] ZIP listo: %.1f MB, sha256=%s..." % (mb, sha[:12]))
    return data, sha, ZIP_NOMBRE


def descripcion_estado(est):
    """Texto de resumen para la UI."""
    ps = est.get("pyspark", {})
    ci = est.get("ciencia", {})
    partes = []
    partes.append("PySpark: %s" % ("OK %.0f MB" % ps["mb"] if ps.get("ok") else "FALTA"))
    partes.append("Ciencia: %s" % ("OK %.0f MB" % ci["mb"] if ci.get("ok") else "FALTA"))
    return " | ".join(partes)
