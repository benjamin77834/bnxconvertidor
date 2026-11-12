#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
importar_vendor.py — Descomprime un ZIP de vendor (hecho con exportar_vendor.py)
en el cache local (src/vendor_cache.cache_dir(): .venv/bnx_vendor_cache/).
Las entradas '.bnx_vendor_cache/<rel>' del ZIP se extraen a <cache>/<rel>.

USO (en el servidor, en la raiz del proyecto bnxconvertidor):
    python importar_vendor.py bnx_vendor_py3.8.zip
Es idempotente. (Equivale a: preparar_vendor.py --zip <zip>)
"""
import os
import sys

ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ROOT)
from src.vendor_cache import cache_dir, importar_zip  # noqa: E402


def main():
    if len(sys.argv) < 2:
        print("USO: python importar_vendor.py <bnx_vendor_*.zip>")
        return 1
    try:
        importar_zip(sys.argv[1])
    except ValueError as e:
        print("ERROR: %s" % e)
        return 1
    print("    Ya puedes generar paquetes con 'ambiente completo' OFFLINE.")
    print("    (Reinicia serve_ui.py si estaba corriendo.)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
