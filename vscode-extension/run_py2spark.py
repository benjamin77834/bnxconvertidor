#!/usr/bin/env python3
# run_py2spark.py — Runner OFFLINE del motor py2spark para la extension VS Code.
#
# La extension ejecuta este script con el Python local del usuario (sin portal
# BNX ni red). Lee un JSON por STDIN: {"code": "<python>", "no_preamble": bool}
# y escribe el resultado del motor por STDOUT como JSON:
#   {"ok": bool, "code": str, "warnings": [...], "unsupported": [...], ...}
#
# El paquete py2spark va EMPAQUETADO junto a este script (carpeta ./py2spark),
# es 100% stdlib (ast/re) y compatible con Python 3.8+ (unparse con fallback).

import json
import os
import sys

# Asegura que el paquete py2spark empaquetado (misma carpeta que este script)
# tenga prioridad en el import, sin depender del cwd de VS Code.
_HERE = os.path.dirname(os.path.abspath(__file__))
if _HERE not in sys.path:
    sys.path.insert(0, _HERE)


def _fail(msg, code=""):
    """Emite un resultado de error con el mismo shape que el motor y sale 0.
    (La extension distingue el error por ok=False, no por exit code.)"""
    json.dump({"ok": False, "error": msg, "code": code,
               "warnings": [], "unsupported": []}, sys.stdout)
    sys.stdout.flush()


def main():
    raw = sys.stdin.read()
    try:
        data = json.loads(raw) if raw.strip() else {}
    except (json.JSONDecodeError, ValueError) as e:
        _fail(f"Entrada JSON invalida: {e}")
        return 0

    code = data.get("code") or data.get("python") or data.get("py") or ""
    add_preamble = not bool(data.get("no_preamble", False))

    if not code.strip():
        _fail("Se requiere codigo Python (campo 'code').")
        return 0

    try:
        from py2spark import convert_code
    except Exception as e:  # motor no importable (empaquetado incompleto)
        _fail(f"No se pudo cargar el motor py2spark: {e}")
        return 0

    try:
        result = convert_code(code, add_preamble=add_preamble)
    except Exception as e:
        import traceback
        _fail(f"Error al convertir: {e}\n{traceback.format_exc()}", code=code)
        return 0

    json.dump(result, sys.stdout, default=str)
    sys.stdout.flush()
    return 0


if __name__ == "__main__":
    sys.exit(main())
