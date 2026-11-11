#!/bin/ksh
# Ejercicio BNX: avisa que el reporte de riesgo quedo listo (solo imprime).
RUN_DIR=${1:-${TMPDIR:-/tmp}/bnx_ejercicio}
echo "Reporte de riesgo disponible en $RUN_DIR/banca/output/reporte_riesgo.dat"
