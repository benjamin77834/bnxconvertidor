#!/usr/bin/env bash
# Simula el paquete MLOps v2 en un Linux RHEL 8 x86_64 (contenedor de Podman) desde una Mac.
#
#   bash tools/linux/simular_en_linux.sh preparar              # una vez: maquina de Podman + imagenes (~8 GB)
#   bash tools/linux/simular_en_linux.sh info                  # estado de Podman, maquina e imagenes
#   bash tools/linux/simular_en_linux.sh simular ZIP [job|todos] [--settings /ruta/bin/settings]
#   bash tools/linux/simular_en_linux.sh cluster ZIP           # run.sh en modo cluster con spark3-submit FALSO
#   bash tools/linux/simular_en_linux.sh limpiar               # borra paquetes montados (los de Linux)
#   bash tools/linux/simular_en_linux.sh apagar                # detiene la maquina de Podman (libera RAM)
#
# ZIP = framework_mlops_v2_con_pyspark.zip | framework_mlops_v2_sin_pyspark.zip (o el del token de la UI).
# En el contenedor corre lo mismo que en el servidor: bash setup.sh (SIN red), python check_env.py y
# bash run.sh --demo [--source <job>] (pivote primero). Cancelar con Ctrl+C mata el contenedor.
set -e
RAIZ="$(cd "$(dirname "$0")/../.." && pwd)"
cd "$RAIZ"
PY="${PYTHON:-$RAIZ/.venv/bin/python}"
[ -x "$PY" ] || PY="$(command -v python3)"
cmd="${1:-info}"; shift || true
case "$cmd" in
  info|preparar) exec "$PY" -m src.mlops_simular "$cmd" ;;
  simular)
    zip="${1:?falta el ZIP}"; shift
    job="todos"
    if [ $# -gt 0 ] && [ "${1#--}" = "$1" ]; then job="$1"; shift; fi
    exec "$PY" -m src.mlops_simular simular "$zip" --job "$job" "$@" ;;
  cluster) exec "$PY" -m src.mlops_simular cluster "${1:?falta el ZIP}" ;;
  limpiar) exec "$PY" -c "from src import mlops_simular as s; print(s.limpiar_simulaciones(conservar=0, base=s.linux_base()))" ;;
  apagar) exec podman machine stop "${BNX_LINUX_MACHINE:-bnx-linux}" ;;
  *) sed -n '2,14p' "$0"; exit 2 ;;
esac
