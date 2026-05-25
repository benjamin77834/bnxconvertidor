#!/bin/bash
# ═══════════════════════════════════════════════════════════
# BNX Convertidor — Empaquetador portable (7z)
# Genera un .7z con toda la estructura lista para ejecutar
# ═══════════════════════════════════════════════════════════

OUTPUT="bnx-convertidor-portable.7z"

echo "📦 Empaquetando BNX Convertidor..."

# Verificar que 7z está instalado
if ! command -v 7z &> /dev/null; then
  echo "❌ 7-Zip no encontrado."
  if command -v brew &> /dev/null; then
    brew install p7zip
  else
    echo "Instala 7-Zip manualmente: brew install p7zip"
    exit 1
  fi
fi

# Clean previous
rm -f "$OUTPUT"

# Comprimir directamente (sin renombrar, sin temp)
# Incluye todo src/, api/, lambda/, main.py, grafos, samples
7z a -t7z "$OUTPUT" \
  main.py \
  bnx.sh \
  requirements.txt \
  README.md \
  src/ \
  api/ \
  lambda/ \
  e2e/ \
  samples/ \
  graphs/ \
  cobol/ \
  abinitio/ \
  dml/ \
  -xr'!__pycache__' \
  -xr'!.DS_Store' \
  -xr'!*.egg-info' \
  -xr'!*.pyc'

echo ""
echo "✅ Empaquetado: $OUTPUT ($(du -h $OUTPUT | cut -f1))"
echo ""
echo "Para instalar en destino (Linux/Mac):"
echo "  1. 7z x $OUTPUT -o/ruta/destino"
echo "  2. cd /ruta/destino"
echo "  3. chmod +x bnx.sh"
echo "  4. python3 main.py --project gr1.mp --target glue --output job.py"
echo ""
echo "Requisitos: Python 3.11+"
