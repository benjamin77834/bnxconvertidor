# -*- coding: utf-8 -*-
"""Bloque bash (portable, bash 3.2 de macOS) del modo B 'PySpark del SERVIDOR': detecta, pregunta,
valida y guarda la ruta de Spark/PySpark del servidor. Se inserta en setup.sh del paquete generado
(marcador @@SPARKCFG@@) y se prueba aparte en tests/test_spark_servidor.py."""

SPARK_CFG_SH = r'''
# ---------------------------------------------------------------------------
# PySpark del SERVIDOR (modo B): el paquete NO trae pyspark; se usa el Spark ya instalado.
# Autodetecta candidatos, pregunta la ruta (con terminal) o lee BNX_SPARK_HOME (sin terminal),
# la VALIDA y la guarda en .bnx_spark.env (run.sh la lee). Cambiarla:
#   bash setup.sh --reconfigurar-spark      (o BNX_SPARK_RECONFIG=1)
# ---------------------------------------------------------------------------
bnx_spark_err() { echo "      [spark] $*" >&2; }

# Version de Spark de un SPARK_HOME ($1) / paquete pyspark ($2).
bnx_spark_version() {
  _v=""
  if [ -f "$1/RELEASE" ]; then _v="$(sed -n '1s/^Spark \([0-9][0-9.A-Za-z-]*\).*/\1/p' "$1/RELEASE")"; fi
  if [ -z "$_v" ]; then
    for _f in "$2/version.py" "$1/python/pyspark/version.py"; do
      if [ -f "$_f" ]; then
        _v="$(sed -n "s/^__version__[^=]*=[ ]*[\"']\([^\"']*\)[\"'].*/\1/p" "$_f" | head -1)"
        if [ -n "$_v" ]; then break; fi
      fi
    done
  fi
  if [ -z "$_v" ]; then
    _j="$(ls "$1"/jars/spark-core_*.jar 2>/dev/null | head -1)"
    if [ -n "$_j" ]; then _v="$(basename "$_j" .jar | sed 's/^spark-core_[0-9.]*-//')"; fi
  fi
  echo "$_v"
}

# java funciona? (JAVA_HOME o PATH)
bnx_spark_java() {
  _jv=""
  if [ -n "${JAVA_HOME:-}" ] && [ -x "$JAVA_HOME/bin/java" ]; then _jv="$JAVA_HOME/bin/java"; else _jv="$(command -v java 2>/dev/null || true)"; fi
  if [ -z "$_jv" ]; then return 1; fi
  "$_jv" -version >/dev/null 2>&1
}

# Rangos oficiales de Python por Spark (classifiers de los wheels de PySpark): 3.5.x = 3.8-3.11,
# 3.4 = 3.7-3.11, 3.0-3.3 = 3.6-3.10, 4.0.x = 3.9-3.13, 4.1+ = 3.10-3.14.
bnx_spark_py_rango() {
  case "$1.$2" in
    4.0) echo "3.9-3.13" ;;
    4.*) echo "3.10-3.14" ;;
    3.5) echo "3.8-3.11 (3.12 con ajustes)" ;;
    3.4) echo "3.7-3.11" ;;
    3.*) echo "3.6-3.10" ;;
    *) echo "?" ;;
  esac
}
bnx_spark_py_ok() {   # $1=mayor $2=menor de Spark, $3=minor de Python (3.N)
  case "$1.$2" in
    4.0) [ "$3" -ge 9 ] && [ "$3" -le 13 ] ;;
    4.*) [ "$3" -ge 10 ] && [ "$3" -le 14 ] ;;
    3.5) [ "$3" -ge 8 ] && [ "$3" -le 12 ] ;;
    3.4) [ "$3" -ge 7 ] && [ "$3" -le 11 ] ;;
    3.*) [ "$3" -ge 6 ] && [ "$3" -le 10 ] ;;
    *) return 0 ;;
  esac
}
bnx_spark_py_alternativos() {   # pythons3.N del PATH que ese Spark soporta
  _o=""
  for _n in 14 13 12 11 10 9 8; do
    if command -v "python3.$_n" >/dev/null 2>&1 && bnx_spark_py_ok "$1" "$2" "$_n"; then _o="$_o python3.$_n"; fi
  done
  echo "$_o" | sed 's/^ //'
}

# Valida una ruta. Acepta: SPARK_HOME de una distribucion (bin/spark-submit + python/pyspark/ +
# python/lib/py4j-*-src.zip), la carpeta pyspark/ de un pip, o un site-packages que contiene pyspark/.
# Define BS_HOME BS_PKG BS_PY4J BS_PYPATH BS_VER BS_ERR BS_AVISO. Devuelve 0 si sirve.
bnx_spark_normalizar() {
  BS_HOME=""; BS_PKG=""; BS_PY4J=""; BS_PYPATH=""; BS_VER=""; BS_ERR=""; BS_AVISO=""
  _p="$1"; _sp=""
  if [ -z "$_p" ]; then BS_ERR="ruta vacia"; return 1; fi
  if [ ! -d "$_p" ]; then BS_ERR="no existe el directorio $_p"; return 1; fi
  _p="$(cd "$_p" && pwd -P)"
  case "$_p" in *"'"*) BS_ERR="la ruta no puede llevar comillas simples"; return 1;; esac
  if [ -f "$_p/pyspark/__init__.py" ]; then
    BS_PKG="$_p/pyspark"; BS_HOME="$BS_PKG"; _sp="$_p"
  elif [ -f "$_p/__init__.py" ] && [ -f "$_p/version.py" ] && [ -d "$_p/bin" ]; then
    BS_PKG="$_p"; BS_HOME="$_p"; _sp="$(dirname "$_p")"
  elif [ -f "$_p/python/pyspark/__init__.py" ]; then
    BS_PKG="$_p/python/pyspark"; BS_HOME="$_p"; BS_PYPATH="$_p/python"
  else
    BS_ERR="$_p no es un SPARK_HOME ni un PySpark: falta python/pyspark/__init__.py (o pyspark/__init__.py)"
    return 1
  fi
  if [ ! -f "$BS_HOME/bin/spark-submit" ]; then BS_ERR="falta $BS_HOME/bin/spark-submit"; return 1; fi
  _z="$(ls "$BS_HOME"/python/lib/py4j-*-src.zip 2>/dev/null | head -1)"
  if [ -n "$_z" ]; then
    BS_PY4J="$_z"
    if [ -n "$BS_PYPATH" ]; then BS_PYPATH="$BS_PYPATH:$_z"; else BS_PYPATH="$_z"; fi
  elif [ -n "$_sp" ] && [ -d "$_sp/py4j" ]; then
    BS_PY4J="$_sp/py4j"
  else
    BS_ERR="falta py4j: no hay $BS_HOME/python/lib/py4j-*-src.zip ni py4j instalado junto a pyspark"
    return 1
  fi
  if ! bnx_spark_java; then BS_ERR="java no funciona (define JAVA_HOME o pon java en el PATH: 'java -version')"; return 1; fi
  BS_VER="$(bnx_spark_version "$BS_HOME" "$BS_PKG")"
  _pm="${PYMINOR:-0}"
  if [ -z "$BS_VER" ]; then
    BS_AVISO="no pude leer la version de Spark en $BS_HOME"
  else
    _mj="${BS_VER%%.*}"; _rs="${BS_VER#*.}"; _mn="${_rs%%.*}"
    case "$_mj$_mn" in *[!0-9]*) _mj=0; _mn=0;; esac
    if [ "$_pm" -gt 0 ] 2>/dev/null && ! bnx_spark_py_ok "$_mj" "$_mn" "$_pm"; then
      BS_AVISO="INCOMPATIBLE: Spark $BS_VER no soporta Python 3.$_pm (soporta $(bnx_spark_py_rango "$_mj" "$_mn"))"
      _alt="$(bnx_spark_py_alternativos "$_mj" "$_mn")"
      if [ -n "$_alt" ]; then BS_AVISO="$BS_AVISO. En este servidor hay: $_alt (repite: rm -rf .venv; PYTHON=$(echo "$_alt" | cut -d' ' -f1) bash setup.sh)"; fi
    elif [ "$_mj" = "3" ] && [ "$_mn" = "5" ] && [ "$_pm" = "12" ]; then
      BS_AVISO="Spark $BS_VER con Python 3.12 funciona con ajustes (distutils/setuptools); lo oficial es 3.8-3.11"
    fi
  fi
  return 0
}

# Candidatos (uno por linea, sin repetir) en el archivo $1.
bnx_spark_candidatos() {
  _out="$1"; : > "$_out"
  bnx_spark_add() {
    if [ -n "$1" ] && [ -d "$1" ]; then
      _r="$(cd "$1" && pwd -P)"
      grep -qxF "$_r" "$_out" 2>/dev/null || echo "$_r" >> "$_out"
    fi
    return 0
  }
  bnx_spark_add "${SPARK_HOME:-}"
  for _s in spark3-submit spark-submit; do
    _b="$(command -v "$_s" 2>/dev/null || true)"
    if [ -n "$_b" ]; then
      _rb="$(python -c 'import os,sys;print(os.path.realpath(sys.argv[1]))' "$_b" 2>/dev/null || echo "$_b")"
      bnx_spark_add "$(dirname "$(dirname "$_rb")")"
    fi
  done
  for _d in /opt/cloudera/parcels/CDH/lib/spark /opt/cloudera/parcels/SPARK*/lib/spark /usr/lib/spark \
            /usr/hdp/current/spark*-client /opt/spark /usr/local/spark; do
    bnx_spark_add "$_d"
  done
  _sysp="${BNX_SYSTEM_PYTHON:-${PY:-python3}}"
  _d="$("$_sysp" -c 'import os,pyspark;print(os.path.dirname(pyspark.__file__))' 2>/dev/null || true)"
  bnx_spark_add "$_d"
  _l="$("$_sysp" -m pip show pyspark 2>/dev/null | sed -n 's/^Location: //p' | head -1)"
  if [ -n "$_l" ]; then bnx_spark_add "$_l/pyspark"; fi
  return 0
}

# Hace que `import pyspark` en el venv use el Spark del servidor (symlinks + .pth) y guarda la config.
bnx_spark_guardar() {
  _vsp="$(python -c 'import sysconfig;print(sysconfig.get_paths()["purelib"])')"
  mkdir -p "$_vsp"
  if [ -L "$_vsp/pyspark" ] || [ ! -e "$_vsp/pyspark" ]; then
    rm -f "$_vsp/pyspark"; ln -s "$BS_PKG" "$_vsp/pyspark"
  else
    echo "      [spark] el venv ya tiene su propio pyspark ($_vsp/pyspark); no lo reemplazo."
  fi
  rm -f "$_vsp/bnx_spark.pth"
  if [ -d "$BS_PY4J" ]; then
    if [ -L "$_vsp/py4j" ] || [ ! -e "$_vsp/py4j" ]; then rm -f "$_vsp/py4j"; ln -s "$BS_PY4J" "$_vsp/py4j"; fi
  else
    echo "$BS_PY4J" > "$_vsp/bnx_spark.pth"
  fi
  {
    echo "# Generado por setup.sh (PySpark del SERVIDOR). Cambiar: bash setup.sh --reconfigurar-spark"
    echo "SPARK_HOME='$BS_HOME'"
    echo "PYSPARK_PYTHON='$PWD/.venv/bin/python'"
    echo "BNX_SPARK_PYPATH='$BS_PYPATH'"
    echo "BNX_SPARK_VERSION='$BS_VER'"
    echo "BNX_SPARK_SUBMIT_CFG='$BS_HOME/bin/spark-submit'"
  } > .bnx_spark.env
  echo "      PySpark del servidor: Spark ${BS_VER:-?} en $BS_HOME (config en .bnx_spark.env)"
  if [ -n "$BS_AVISO" ]; then echo "      [AVISO] $BS_AVISO"; fi
}

bnx_spark_configurar() {
  _cfg=".bnx_spark.env"
  _tty=0; if [ -t 0 ] && [ -t 1 ]; then _tty=1; fi
  if [ "${BNX_SPARK_RECONFIG:-0}" = "1" ]; then rm -f "$_cfg"; fi
  if [ -f "$_cfg" ]; then
    _old="$(sed -n "s/^SPARK_HOME='\(.*\)'\$/\1/p" "$_cfg" | head -1)"
    if bnx_spark_normalizar "$_old"; then
      echo "      PySpark del servidor ya configurado (.bnx_spark.env). Para cambiarlo: bash setup.sh --reconfigurar-spark"
      bnx_spark_guardar; return 0
    fi
    bnx_spark_err "la ruta guardada ya no sirve: $BS_ERR"
  fi
  if [ -n "${BNX_SPARK_HOME:-}" ]; then
    if bnx_spark_normalizar "$BNX_SPARK_HOME"; then bnx_spark_guardar; return 0; fi
    bnx_spark_err "BNX_SPARK_HOME=$BNX_SPARK_HOME no sirve: $BS_ERR"
    if [ "$_tty" = "0" ]; then return 1; fi
  fi
  _cand="$(mktemp "${TMPDIR:-/tmp}/bnx_spark.XXXXXX")"
  bnx_spark_candidatos "$_cand"
  if [ "$_tty" = "0" ]; then
    bnx_spark_err "no hay terminal para preguntar la ruta de PySpark/Spark del servidor."
    bnx_spark_err "Defínela y repite:  BNX_SPARK_HOME=/ruta/al/spark bash setup.sh"
    if [ -s "$_cand" ]; then bnx_spark_err "Candidatos encontrados:"; while read -r _c; do bnx_spark_err "  $_c"; done < "$_cand"; fi
    rm -f "$_cand"; return 1
  fi
  _try=0
  while [ "$_try" -lt 3 ]; do
    echo ""
    echo "      PySpark del servidor: candidatos encontrados"
    if [ -s "$_cand" ]; then
      _i=0; while read -r _c; do _i=$((_i+1)); echo "        [$_i] $_c"; done < "$_cand"
    else
      echo "        (ninguno)"
    fi
    printf "      Ruta de SPARK_HOME / PySpark [Enter = candidato 1]: "
    read -r _ans || _ans=""
    if [ -z "$_ans" ]; then _ans="$(sed -n 1p "$_cand")"; fi
    case "$_ans" in
      [0-9]|[0-9][0-9]) _n="$(sed -n "${_ans}p" "$_cand")"; if [ -n "$_n" ]; then _ans="$_n"; fi ;;
      "~"*) _ans="$HOME${_ans#\~}" ;;
    esac
    if bnx_spark_normalizar "$_ans"; then
      case "$BS_AVISO" in
        INCOMPATIBLE*)
          echo "      [AVISO] $BS_AVISO"
          printf "      ¿Usarlo de todas formas? [s/N] "; read -r _ok || _ok=""
          case "$_ok" in s|S|si|SI) ;; *) _try=$((_try+1)); continue ;; esac ;;
      esac
      rm -f "$_cand"; bnx_spark_guardar; return 0
    fi
    bnx_spark_err "ruta no valida: $BS_ERR"
    _try=$((_try+1))
    if ls vendor/*/pyspark-*.whl >/dev/null 2>&1; then
      printf "      Este paquete trae PySpark en vendor/. ¿Instalarlo en el venv en vez de usar el del servidor? [s/N] "
      read -r _ok || _ok=""
      case "$_ok" in s|S|si|SI) rm -f "$_cand"; return 2 ;; esac
    fi
  done
  rm -f "$_cand"
  bnx_spark_err "3 intentos sin una ruta valida. Usa:  BNX_SPARK_HOME=/ruta/al/spark bash setup.sh"
  return 1
}

# Punto de entrada desde setup.sh: configura PySpark del servidor o, si el usuario lo pide, instala el del vendor.
bnx_spark_modo_b() {
  _rc=0
  bnx_spark_configurar || _rc=$?
  if [ "$_rc" = "2" ]; then
    python -m pip install --no-index --find-links "${VENDOR_DIR:-vendor}" pyspark py4j || { echo "[ERROR] no pude instalar PySpark del vendor" >&2; exit 1; }
    BNX_PYSPARK_MODO="incluido"
  elif [ "$_rc" != "0" ]; then
    echo "[ERROR] No quedo configurado PySpark del servidor (ver arriba)." >&2
    exit 1
  fi
}
'''
