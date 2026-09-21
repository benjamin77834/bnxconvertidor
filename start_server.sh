#!/bin/zsh
# Arranque LIMPIO del server BNX Convertidor.
# Evita el problema recurrente de "código viejo cacheado": mata cualquier server
# previo, borra el bytecode .pyc (que Python cachea y no recarga en procesos de
# larga vida) y arranca con -B (sin escribir nuevo bytecode).
#
# Uso:  ./start_server.sh
# El server queda en primer plano; Ctrl+C para detenerlo.

set -e
cd "$(dirname "$0")"

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
