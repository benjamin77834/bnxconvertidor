#!/bin/bash
# ═══════════════════════════════════════════════════════════
# BNX Convertidor — Empaquetador portable
# Genera un ZIP instalable en cualquier carpeta/máquina
# ═══════════════════════════════════════════════════════════

OUTPUT="bnx-convertidor-portable.zip"
echo "📦 Empaquetando BNX Convertidor..."

# Clean previous
rm -f "$OUTPUT"

zip -r "$OUTPUT" \
  main.py \
  bnx.sh \
  requirements.txt \
  README.md \
  src/mp_parser.py \
  src/xfr_parser.py \
  src/dml_parser.py \
  src/cobol_parser.py \
  src/plan_parser.py \
  src/accuracy.py \
  src/refactor_engine.py \
  src/visualizer.py \
  src/dag/builder.py \
  src/dag/__init__.py \
  src/validator/semantic.py \
  src/validator/__init__.py \
  src/codegen/glue_codegen.py \
  src/codegen/spark_codegen.py \
  src/codegen/flink_codegen.py \
  src/codegen/stepfunctions_codegen.py \
  src/codegen/terraform_codegen.py \
  src/codegen/airflow_codegen.py \
  src/codegen/__init__.py \
  src/__init__.py \
  api/server.py \
  lambda/handler.py \
  e2e/test.mp \
  e2e/test.xfr \
  samples/scan_dates/ \
  samples/abinitio_native/ \
  samples/refactor/ \
  graphs/test_mega/ \
  cobol/ \
  -x "**/__pycache__/*" "**/.DS_Store"

# Add init files if missing
zip -j "$OUTPUT" /dev/null 2>/dev/null || true

echo ""
echo "✅ Empaquetado: $OUTPUT ($(du -h $OUTPUT | cut -f1))"
echo ""
echo "Para instalar en otra carpeta:"
echo "  1. unzip $OUTPUT -d /ruta/destino"
echo "  2. cd /ruta/destino"
echo "  3. chmod +x bnx.sh"
echo "  4. ./bnx.sh test"
echo ""
echo "Requisitos: Python 3.11+ (sin dependencias externas)"
