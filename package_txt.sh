#!/bin/bash
# ═══════════════════════════════════════════════════════════
# BNX Convertidor — Empaquetador (Python → .txt → 7z)
# Renombra .py a .txt para transporte seguro sin corrupción
# ═══════════════════════════════════════════════════════════

OUTPUT="bnx-convertidor-src.7z"
TEMP_DIR=".package_txt_tmp"

echo "📦 Empaquetando BNX Convertidor (Python → TXT → 7z)..."

# Verificar 7z
if ! command -v 7z &> /dev/null; then
  if command -v brew &> /dev/null; then
    brew install p7zip
  else
    echo "❌ Instala: brew install p7zip"
    exit 1
  fi
fi

# Clean
rm -f "$OUTPUT"
rm -rf "$TEMP_DIR"
mkdir -p "$TEMP_DIR"

# Copiar todos los .py como .txt (preserva indentación exacta)
for d in src api lambda; do
  if [ -d "$d" ]; then
    find "$d" -name "*.py" -not -path "*/__pycache__/*" -not -path "*egg-info*" | while read f; do
      rel_dir=$(dirname "$f")
      mkdir -p "$TEMP_DIR/$rel_dir"
      # Copiar como .txt para evitar que Word/email corrompa
      cp "$f" "$TEMP_DIR/${f}.txt"
    done
  fi
done

# main.py
if [ -f "main.py" ]; then
  cp main.py "$TEMP_DIR/main.py.txt"
fi

# Contar archivos
COUNT=$(find "$TEMP_DIR" -name "*.txt" | wc -l | tr -d ' ')

# Comprimir
7z a -t7z "$OUTPUT" "$TEMP_DIR"/* -xr'!.DS_Store'

# Limpiar
rm -rf "$TEMP_DIR"

echo ""
echo "✅ Empaquetado: $OUTPUT ($(du -h $OUTPUT | cut -f1))"
echo "📄 $COUNT archivos .py → .txt (indentación preservada)"
echo ""
echo "Para usar en destino:"
echo "  1. 7z x $OUTPUT"
echo "  2. Renombrar .py.txt → .py:"
echo "     find . -name '*.py.txt' -exec sh -c 'mv \"\$1\" \"\${1%.txt}\"' _ {} \\;"
echo ""
echo "💡 Se usa .txt en vez de .docx para preservar indentación exacta del código Python."
