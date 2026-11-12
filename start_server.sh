#!/bin/zsh
# Arranque LIMPIO del server BNX Convertidor.
# Evita el problema recurrente de "código viejo cacheado": mata cualquier server
# previo, borra el bytecode .pyc (que Python cachea y no recarga en procesos de
# larga vida) y arranca con -B (sin escribir nuevo bytecode).
#
# Uso:  ./start_server.sh
# El server queda en primer plano; Ctrl+C para detenerlo.
#
# Cache de vendor (wheels de PySpark/deps para armar paquetes Linux offline) en
# .venv/bnx_vendor_cache. Al arrancar se revisa; si falta algo se ofrece bajarlo/generarlo.
# Bajar = primero el GitHub Release publico (vendor-linux-v1: rapido, sin libs del banco),
# si falla cae a pip. Las libs del banco: preparar_vendor.py --bank-libs <carpeta|zip>.
#   BNX_VENDOR_AUTO=3.8|3.12|ambas  sin tty: baja automatico sin preguntar
#   BNX_VENDOR_PODAR=3.8|3.12|ambas  quita del cache lo que no sea el minimo (sin preguntar)
#   BNX_VENDOR_CHECK=0              omite el chequeo
#   BNX_ONLY_CHECK=1                solo hace el chequeo y sale (no mata ni arranca el server)

set -e
cd "$(dirname "$0")"

vendor_check() {
  [ "${BNX_VENDOR_CHECK:-1}" = "0" ] && return 0
  if [ ! -x ".venv/bin/python" ]; then
    echo "[vendor] AVISO: no existe .venv; omito el chequeo del cache de vendor (crea el venv con ./setup.sh)."
    return 0
  fi
  local VPY=".venv/bin/python" interactivo=0 rc=0 op z
  local -a zips
  [ -t 0 ] && [ -t 1 ] && interactivo=1
  # Cache viejo en la raiz -> migrarlo al venv (mv en el mismo disco: instantaneo).
  if [ -z "$BNX_VENDOR_CACHE" ] && [ -d ".bnx_vendor_cache" ] && [ ! -e ".venv/bnx_vendor_cache" ]; then
    if [ "$interactivo" = "1" ]; then
      echo "[vendor] Encontre el cache viejo .bnx_vendor_cache/ en la raiz del proyecto."
      printf "[vendor] ¿Migrarlo al ambiente virtual (.venv/bnx_vendor_cache)? [S/n] "
      read -r op || op="n"
      case "$op" in
        n|N|no|NO) echo "[vendor] Sigo con el cache viejo (migralo luego con: mv .bnx_vendor_cache .venv/bnx_vendor_cache)." ;;
        *) mv .bnx_vendor_cache .venv/bnx_vendor_cache && echo "[vendor] Migrado a .venv/bnx_vendor_cache" ;;
      esac
    else
      echo "[vendor] AVISO: hay un cache viejo .bnx_vendor_cache/. Migralo con: mv .bnx_vendor_cache .venv/bnx_vendor_cache"
    fi
  fi
  echo "[vendor] Revisando el cache de vendor..."
  "$VPY" -B preparar_vendor.py --estado || rc=$?
  if [ -n "${BNX_VENDOR_PODAR:-}" ]; then
    case "$BNX_VENDOR_PODAR" in
      3.8)   "$VPY" -B preparar_vendor.py --podar --si --python 3.8 || true ;;
      3.12)  "$VPY" -B preparar_vendor.py --podar --si --python 3.12 || true ;;
      ambas) "$VPY" -B preparar_vendor.py --podar --si --python 3.8 --python 3.12 || true ;;
    esac
  fi
  [ "$rc" = "0" ] && return 0
  if [ "$rc" != "3" ]; then
    echo "[vendor] AVISO: no pude revisar el cache (codigo $rc); sigo."
    return 0
  fi
  if [ "$interactivo" = "0" ]; then
    case "${BNX_VENDOR_AUTO:-}" in
      3.8)   "$VPY" -B preparar_vendor.py --python 3.8 || true ;;
      3.12)  "$VPY" -B preparar_vendor.py --python 3.12 || true ;;
      ambas) "$VPY" -B preparar_vendor.py --python 3.8 --python 3.12 || true ;;
      *) echo "[vendor] AVISO: falta cache de vendor. Corre: .venv/bin/python preparar_vendor.py --python 3.8"
         echo "         (o arranca con BNX_VENDOR_AUTO=3.8|3.12|ambas, o usa el boton 'Bajar/generar cache' en la UI)." ;;
    esac
    return 0
  fi
  echo ""
  echo "Falta el cache de vendor para armar paquetes Linux offline. ¿Qué hago?"
  echo "  [1] Bajar (GitHub Release; si falla, pip) para Python 3.8"
  echo "  [2] Bajar (GitHub Release; si falla, pip) para Python 3.12"
  echo "  [3] Ambas"
  echo "  [4] Importar desde ZIP"
  echo "  [5] Podar: quitar del cache lo que no sea el mínimo (3.8 y 3.12; muestra y pregunta)"
  echo "  [6] Ahora no"
  printf "Opción [6]: "
  read -r op || op=6
  case "${op:-6}" in
    1) "$VPY" -B preparar_vendor.py --python 3.8 || true ;;
    2) "$VPY" -B preparar_vendor.py --python 3.12 || true ;;
    3) "$VPY" -B preparar_vendor.py --python 3.8 --python 3.12 || true ;;
    4)
      zips=(~/Downloads/bnx_vendor_*.zip(N.om))
      z=""
      if [ ${#zips} -gt 0 ]; then
        printf "Ruta del ZIP [%s]: " "${zips[1]}"
        read -r z || z=""
        z="${z:-${zips[1]}}"
      else
        printf "Ruta del ZIP (bnx_vendor_*.zip): "
        read -r z || z=""
      fi
      z="${z/#\~/$HOME}"
      if [ -n "$z" ]; then "$VPY" -B preparar_vendor.py --zip "$z" || true; fi ;;
    5) "$VPY" -B preparar_vendor.py --podar --python 3.8 --python 3.12 || true ;;
    *) echo "[vendor] Ok, sin cache por ahora (puedes usar el boton 'Bajar/generar cache' en la UI)." ;;
  esac
  return 0
}
vendor_check
if [ "${BNX_ONLY_CHECK:-0}" = "1" ]; then exit 0; fi

echo "[start] Matando servers previos en el puerto 8081..."
pkill -9 -f serve_ui.py 2>/dev/null || true
sleep 2

echo "[start] Limpiando bytecode cacheado (.pyc)..."
rm -rf src/__pycache__ __pycache__ 2>/dev/null || true

# Elegir el Python del venv si existe (tiene pyspark + numpy); si no, el del sistema.
if [ -x ".venv/bin/python" ]; then
  PY=".venv/bin/python"
else
  PY="python3"
fi

echo "[start] Version del codigo:"
git log --oneline -1 2>/dev/null || true

echo "[start] Arrancando server con $PY -B serve_ui.py (puerto 8081)..."
exec "$PY" -B serve_ui.py
