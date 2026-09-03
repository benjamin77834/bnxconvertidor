#!/bin/bash
# ============================================================
# BNX - Sincronizar biblioteca de grafos desde S3 (DataLab)
# ============================================================
# Los grafos viven en s3://datalake-bnx-scripts-dev/library/ (cuenta DataLab)
# y NO viajan por git (bnx_library/ esta en .gitignore). Este script baja los
# grafos nuevos/actualizados a ./bnx_library/ para que el server local los vea.
#
# Uso:
#   ./sync_library.sh              # usa el perfil AWS 'datalab'
#   AWS_PROFILE=otro ./sync_library.sh
#
# Despues: reinicia el server (python serve_ui.py) para que aparezcan.
# ============================================================
set -e

BUCKET="s3://datalake-bnx-scripts-dev/library/"
DEST="$(cd "$(dirname "$0")" && pwd)/bnx_library/"
PROFILE="${AWS_PROFILE:-datalab}"

echo "Sincronizando grafos desde $BUCKET"
echo "  -> $DEST  (perfil: $PROFILE)"

# --exclude Repo_Git/*: es un repo git interno pesado, no son grafos de prueba.
aws s3 sync "$BUCKET" "$DEST" \
  --profile "$PROFILE" \
  --exclude "Repo_Git/*"

echo ""
echo "Listo. Proyectos disponibles:"
ls -1 "$DEST" | grep -v '^_flat$' | sed 's/^/  - /'
echo ""
echo "Reinicia el server para verlos:  python serve_ui.py"
