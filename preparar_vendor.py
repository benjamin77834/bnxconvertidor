#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
preparar_vendor.py — Baja/genera el cache de vendor DENTRO del venv (.venv/bnx_vendor_cache/).

USO:
    .venv/bin/python preparar_vendor.py --python 3.8              # default
    .venv/bin/python preparar_vendor.py --python 3.8 --python 3.12
    .venv/bin/python preparar_vendor.py --zip ~/Downloads/bnx_vendor_py3.8.zip
    .venv/bin/python preparar_vendor.py --estado [--json] [--python 3.12]

Por version: PySpark (sdist -> wheel) + py4j + dependencias open source (manylinux x86_64).
Las mex-lib del banco NO estan en PyPI: se reportan como faltantes (usa --zip o copialas).
Es idempotente: no vuelve a bajar lo que ya esta.
"""
import argparse
import json
import os
import sys

ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ROOT)
os.environ.setdefault("BNX_NO_DOWNLOAD", "1")   # solo preparar() baja (ver vendor_cache)

from src import vendor_cache as vc  # noqa: E402


def main(argv=None):
    ap = argparse.ArgumentParser(description="Prepara el cache de vendor (dentro del venv).")
    ap.add_argument("--python", action="append", metavar="3.X",
                    help="Version de Python del servidor Linux (3.8 o 3.12). Repetible. Default 3.8.")
    ap.add_argument("--zip", metavar="RUTA", help="Importar un ZIP de vendor (exportar_vendor.py).")
    ap.add_argument("--estado", action="store_true", help="Solo reporta que falta.")
    ap.add_argument("--json", action="store_true", help="Con --estado: salida JSON.")
    args = ap.parse_args(argv)
    try:
        sys.stdout.reconfigure(line_buffering=True)   # progreso en vivo (log de la UI)
    except Exception:
        pass
    try:
        versiones = [vc.norm_version(v) for v in (args.python or [])]
    except ValueError as e:
        print("ERROR: %s" % e)
        return 2

    if args.estado:
        est = vc.estado(versiones or ["3.8", "3.12"])
        if args.json:
            print(json.dumps(est, ensure_ascii=False, indent=2))
        else:
            print(vc.formatear_estado(est))
        return 0 if all(e["ok"] for e in est["versiones"].values()) else 3

    print("Cache: %s" % vc.cache_dir())
    if args.zip:
        try:
            vc.importar_zip(os.path.expanduser(args.zip))
        except ValueError as e:
            print("ERROR: %s" % e)
            return 1
        if not versiones:
            return 0

    versiones = versiones or ["3.8"]
    # Cuanto falta realmente; si todo esta, no se necesita red.
    pendientes = [v for v in versiones if not vc.estado_version(v)["ok"]]
    if pendientes and not vc.hay_internet():
        print("ERROR: no hay internet (no se alcanza pypi.org). Alternativa: en una maquina con el cache lleno")
        print("       corre `python exportar_vendor.py --python %s` y aqui:" % pendientes[0])
        print("       .venv/bin/python preparar_vendor.py --zip <bnx_vendor_*.zip>")
        return 1
    rc = 0
    for v in versiones:
        est = vc.preparar_version(v)
        if not est["ok"]:
            rc = 3
    print("")
    print(vc.formatear_estado(vc.estado(versiones)))
    return rc


if __name__ == "__main__":
    sys.exit(main())
