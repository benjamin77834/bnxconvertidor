#!/bin/bash
# ═══════════════════════════════════════════════════════════
# BNX Convertidor — Empaquetador alternativo (Python → .docx → 7z)
# Convierte cada .py a .docx y empaqueta en 7z
# ═══════════════════════════════════════════════════════════

OUTPUT="bnx-convertidor-docs.7z"
TEMP_DIR=".package_doc_tmp"

echo "📦 Empaquetando BNX Convertidor (Python → DOCX → 7z)..."

# Verificar dependencias
if ! command -v 7z &> /dev/null; then
  echo "❌ 7-Zip no encontrado."
  if command -v brew &> /dev/null; then
    brew install p7zip
  else
    echo "Instala: brew install p7zip"
    exit 1
  fi
fi

if ! python3 -c "import docx" 2>/dev/null; then
  echo "📥 Instalando python-docx..."
  pip3 install python-docx
fi

# Clean previous
rm -f "$OUTPUT"
rm -rf "$TEMP_DIR"
mkdir -p "$TEMP_DIR"

# Script Python para convertir .py a .docx
python3 << 'PYEOF'
import os
import sys
from docx import Document
from docx.shared import Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH

TEMP_DIR = ".package_doc_tmp"

# Recopilar TODOS los .py recursivamente de src/, api/, lambda/
ALL_FILES = []
for root_dir in ["src", "api", "lambda"]:
    if os.path.isdir(root_dir):
        for dirpath, dirnames, filenames in os.walk(root_dir):
            # Skip __pycache__ and egg-info
            dirnames[:] = [d for d in dirnames if d != "__pycache__" and "egg-info" not in d]
            for fname in sorted(filenames):
                if fname.endswith(".py"):
                    ALL_FILES.append(os.path.join(dirpath, fname))

# Agregar main.py si existe
if os.path.isfile("main.py"):
    ALL_FILES.insert(0, "main.py")

converted = 0

for filepath in ALL_FILES:
    if not os.path.isfile(filepath):
        continue

    with open(filepath, "r", encoding="utf-8") as f:
        code = f.read()

    # Skip empty __init__.py
    if os.path.basename(filepath) == "__init__.py" and len(code.strip()) == 0:
        continue

    doc = Document()

    # Título
    doc.add_heading(f"📄 {filepath}", level=1)

    # Metadata
    meta = doc.add_paragraph()
    meta.add_run(f"Archivo: {filepath}\n").bold = True
    meta.add_run(f"Líneas: {len(code.splitlines())}\n")
    meta.add_run(f"Tamaño: {len(code)} bytes\n")
    meta.add_run("─" * 60)

    # Código fuente
    doc.add_heading("Código Fuente", level=2)
    code_para = doc.add_paragraph()
    run = code_para.add_run(code)
    run.font.name = "Courier New"
    run.font.size = Pt(8)
    run.font.color.rgb = RGBColor(30, 30, 30)

    # Guardar .docx
    rel_dir = os.path.dirname(filepath)
    out_dir = os.path.join(TEMP_DIR, rel_dir) if rel_dir else TEMP_DIR
    os.makedirs(out_dir, exist_ok=True)

    docx_name = os.path.basename(filepath).replace(".py", ".docx")
    out_path = os.path.join(out_dir, docx_name)
    doc.save(out_path)
    converted += 1
    print(f"  ✅ {filepath} → {out_path}")

print(f"\n📄 {converted} archivos convertidos a DOCX")
PYEOF

if [ $? -ne 0 ]; then
  echo "❌ Error en la conversión Python → DOCX"
  rm -rf "$TEMP_DIR"
  exit 1
fi

# Comprimir en 7z
7z a -t7z "$OUTPUT" "$TEMP_DIR"/*

# Limpiar temporal
rm -rf "$TEMP_DIR"

echo ""
echo "✅ Empaquetado: $OUTPUT ($(du -h $OUTPUT | cut -f1))"
echo ""
echo "Contenido: Cada archivo .py convertido a .docx con código fuente formateado"
echo ""
echo "Para descomprimir:"
echo "  7z x $OUTPUT"
