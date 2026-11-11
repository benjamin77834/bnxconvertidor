#!/bin/ksh
# Ejercicio BNX: prepara las carpetas de trabajo del dia (datos inventados).
RUN_DIR=${1:-${TMPDIR:-/tmp}/bnx_ejercicio}
mkdir -p "$RUN_DIR/banca/raw" "$RUN_DIR/banca/output"
echo "Directorios listos en $RUN_DIR/banca"
