#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
preparar_vendor.py — Baja/genera el cache de vendor DENTRO del venv (.venv/bnx_vendor_cache/).

USO:
    .venv/bin/python preparar_vendor.py --python 3.8              # default
    .venv/bin/python preparar_vendor.py --python 3.8 --python 3.12
    .venv/bin/python preparar_vendor.py --desde-github --python 3.12 [--tag vendor-linux-v2]
    .venv/bin/python preparar_vendor.py --zip ~/Downloads/bnx_vendor_py3.8.zip
    .venv/bin/python preparar_vendor.py --estado [--json] [--python 3.12]

Al bajar (--python) se prefiere el GitHub Release publico (rapido, sin build de PySpark; no trae
las libs del banco); si falla, cae a pip. --desde-github = solo GitHub; --sin-github = solo pip.

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
    ap.add_argument("--desde-github", action="store_true",
                    help="Bajar solo del GitHub Release publico (sin pip). Es el metodo preferido por defecto.")
    ap.add_argument("--sin-github", action="store_true", help="No intentar GitHub: usar pip directo.")
    ap.add_argument("--tag", default=vc.GH_TAG, help="Tag del Release (default %s)." % vc.GH_TAG)
    ap.add_argument("--estado", action="store_true", help="Solo reporta que falta.")
    ap.add_argument("--json", action="store_true", help="Con --estado: salida JSON.")
    ap.add_argument("--extra", "--ciencia", dest="extra", action="store_true",
                    help="Incluir tambien las deps de los pasos extra (scoring). La pila de ciencia de "
                         "datos (xgboost, lightgbm, scikit-learn, ...) ya va SIEMPRE.")
    ap.add_argument("--bank-libs", metavar="RUTA",
                    help="Importar las librerias del banco (mex-lib*.tar.gz, toolbox/bnmxverse/utils) "
                         "desde una carpeta o ZIP a bank_libs/.")
    ap.add_argument("--podar", action="store_true",
                    help="Quitar del cache todo lo que no sea el minimo para las --python elegidas "
                         "(nunca toca los sdist mex-lib de bank_libs/). Pide confirmacion en tty.")
    ap.add_argument("--mostrar", action="store_true", help="Con --podar: solo muestra (dry-run).")
    ap.add_argument("--si", action="store_true", help="Con --podar: borrar sin preguntar (no interactivo).")
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

    if args.desde_github and args.sin_github:
        print("ERROR: --desde-github y --sin-github son excluyentes.")
        return 2
    if args.estado:
        est = vc.estado(versiones or ["3.8", "3.12"], extra=args.extra)
        if args.json:
            print(json.dumps(est, ensure_ascii=False, indent=2))
        else:
            print(vc.formatear_estado(est))
        return 0 if all(e["ok"] for e in est["versiones"].values()) else 3

    print("Cache: %s" % vc.cache_dir())
    if args.bank_libs:
        try:
            vc.importar_bank_libs(args.bank_libs)
        except ValueError as e:
            print("ERROR: %s" % e)
            return 1
        if not versiones and not args.zip and not args.podar:
            print(vc.formatear_estado(vc.estado([], extra=args.extra)))
            return 0
    if args.zip:
        try:
            vc.importar_zip(os.path.expanduser(args.zip))
        except ValueError as e:
            print("ERROR: %s" % e)
            return 1
        if not versiones:
            return 0

    versiones = versiones or ["3.8"]
    if args.podar:
        def _confirmar():
            if args.si:
                return True
            if not (sys.stdin.isatty() and sys.stdout.isatty()):
                print("Sin terminal interactiva: no se borra (usa --si para confirmar).")
                return False
            return input("¿Borrar estos archivos? [s/N] ").strip().lower() in ("s", "si", "sí", "y", "yes")
        aplicar = not args.mostrar
        hubo_error = []

        def _log(msg):
            print(msg)
            if str(msg).startswith("ERROR"):
                hubo_error.append(msg)
        vc.podar(versiones, extra=args.extra, aplicar=aplicar,
                 confirmar=_confirmar if aplicar else None, log=_log)
        return 1 if hubo_error else 0     # que la UI no diga "Listo" si no se pudo podar
    # Cuanto falta realmente; si todo esta, no se necesita red.
    pendientes = [v for v in versiones if not vc.estado_version(v, extra=args.extra)["ok"]]
    if pendientes and not args.sin_github:
        # Preferido: asset del Release publico (minimo + PySpark ya construido).
        fallo_gh = False
        for v in pendientes:
            if not vc.desde_github(v, tag=args.tag):
                fallo_gh = True
        if args.desde_github:
            print("")
            print(vc.formatear_estado(vc.estado(versiones, extra=args.extra)))
            return 1 if fallo_gh else 0
        if fallo_gh:
            print("[github] no se pudo con GitHub para alguna version; sigo con pip.")
        pendientes = [v for v in versiones if not vc.estado_version(v, extra=args.extra)["ok"]]
        versiones_pip = pendientes
    else:
        versiones_pip = versiones
    if pendientes and not vc.hay_internet():
        print("ERROR: no hay internet (no se alcanza pypi.org; si hay proxy corporativo define HTTPS_PROXY/HTTP_PROXY).")
        print("       Alternativa: en una maquina con el cache lleno corre `python exportar_vendor.py --python %s`" % pendientes[0])
        print("       y aqui: python preparar_vendor.py --zip <bnx_vendor_*.zip>")
        return 1
    rc = 0
    for v in versiones_pip:
        est = vc.preparar_version(v, extra=args.extra)
        if not est["ok"]:
            rc = 3
    print("")
    print(vc.formatear_estado(vc.estado(versiones, extra=args.extra)))
    return rc


if __name__ == "__main__":
    sys.exit(main())
