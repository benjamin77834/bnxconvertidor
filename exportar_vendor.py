#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
exportar_vendor.py — Empaqueta el CACHE de vendor (.bnx_vendor_cache/) en un ZIP
para llevarlo a un servidor AISLADO (sin internet), como el del banco o un portal
en Windows sin cache.

El servidor del banco no tiene internet y PySpark pesa ~300-450 MB (no cabe en
GitHub). Este script genera UN ZIP que copias al portal UNA vez y descomprimes con
importar_vendor.py. Asi el Framework MLOps v2 arma los paquetes offline.

USO (en tu Mac, donde SI tienes el cache lleno):
    python exportar_vendor.py --python 3.8                 # RECOMENDADO: solo lo que
                                                           # usa Python 3.8 en Linux
    python exportar_vendor.py --python 3.8 --python 3.12   # ademas Python 3.12
    python exportar_vendor.py --serie all                  # (antiguo) cache entero, pesado
    python exportar_vendor.py -o /ruta/salida.zip

Produce 'bnx_vendor_py3.8.zip' (o bnx_vendor_<serie>.zip). En el portal:
    python importar_vendor.py bnx_vendor_py3.8.zip
"""
import argparse
import os
import sys
import zipfile

ROOT = os.path.dirname(os.path.abspath(__file__))
CACHE = os.path.join(ROOT, ".bnx_vendor_cache")

# Series de PySpark por version de Python del DESTINO.
SERIES = {"py38-311", "py312plus"}
# Carpetas que SIEMPRE se incluyen (no dependen de la serie).
ALWAYS = ["bank_libs"]


def _dirs_for(serie):
    """(antiguo) Carpetas del cache a incluir segun la serie ('all' = todo)."""
    dirs = list(ALWAYS)
    if serie == "all":
        dirs += ["py38-311", "py312plus", "mlops_deps"]
    elif serie == "py38-311":
        dirs += ["py38-311"]
        dirs += [os.path.join("mlops_deps", "py38-311"),
                 os.path.join("mlops_deps", "py38-311_extra"),
                 os.path.join("mlops_deps", "py38-311_dl")]
    elif serie == "py312plus":
        dirs += ["py312plus"]
        dirs += [os.path.join("mlops_deps", "py312plus"),
                 os.path.join("mlops_deps", "py312plus_extra"),
                 os.path.join("mlops_deps", "py312plus_dl")]
    return dirs


def _files_for_python(versiones):
    """Archivos MINIMOS del cache para generar paquetes (ligero y completo, con y sin
    pasos extra) para esas versiones EXACTAS de Python en Linux: lo que pip resuelve
    + el codigo de path del banco (toolbox/bnmxverse/utils) + las mex-lib."""
    sys.path.insert(0, ROOT)
    os.environ.setdefault("BNX_NO_DOWNLOAD", "1")   # exportar lo que HAY, sin bajar
    from src import mlops_pkg as mp
    base = [l for l in mp._requirements(True, False).splitlines() if l.strip() and not l.startswith("#")]
    extra = [l for l in mp._requirements(True, True).splitlines() if l.strip() and not l.startswith("#")]
    stack = ["cytoolz", "toolz", "Unidecode", "cloudpickle", "joblib"]   # stack del banco
    files, faltan = set(), {}
    for v in versiones:
        serie = list(mp._versiones_target("py" + v))[0]
        for reqs, xs in ((base + stack, False), (extra + stack, True)):
            for spark in (True, False):
                fs, f = mp._seleccionar_wheels(serie, reqs, extra_steps=xs, incluir_spark=spark,
                                               versiones=[v])
                files.update(fs)
                faltan.update(f)
    bank = os.path.join(CACHE, "bank_libs")
    for root, subdirs, fns in os.walk(os.path.join(bank, "pkgcode")):
        subdirs[:] = [s for s in subdirs if s != "__pycache__"]
        files.update(os.path.join(root, f) for f in fns
                     if not f.endswith((".pyc", ".pyo")) and f != ".DS_Store")
    wh = os.path.join(bank, "wheels")
    if os.path.isdir(wh):
        files.update(os.path.join(wh, f) for f in os.listdir(wh) if f.lower().startswith("mex"))
    return sorted(files), faltan


def main():
    ap = argparse.ArgumentParser(description="Empaqueta el vendor para un server aislado.")
    ap.add_argument("--python", action="append", default=None, metavar="3.X",
                    help="RECOMENDADO: solo lo que necesitan los paquetes para esa version "
                         "exacta de Python (repetible: --python 3.8 --python 3.12).")
    ap.add_argument("--serie", default="all", choices=["all", "py38-311", "py312plus"],
                    help="(antiguo) cache completo de la serie: mucho mas pesado.")
    ap.add_argument("-o", "--output", default=None, help="Ruta del ZIP de salida.")
    args = ap.parse_args()

    if not os.path.isdir(CACHE):
        print("ERROR: no existe el cache %s (genera un paquete 'ambiente completo' primero)." % CACHE)
        return 1

    if args.python:
        versiones = sorted({v.replace("py", "").strip() for v in args.python},
                           key=lambda s: [int(x) for x in s.split(".")])
        etiqueta = "py" + "_".join(versiones)
        lista, faltan = _files_for_python(versiones)
        if faltan:
            print("AVISO: al cache le faltan wheels para:", faltan)
    else:
        etiqueta = args.serie
        lista = []
        for d in _dirs_for(args.serie):
            for root, subdirs, fns in os.walk(os.path.join(CACHE, d)):
                subdirs[:] = [s for s in subdirs if s != "__pycache__"]
                lista += [os.path.join(root, f) for f in fns
                          if not f.endswith((".pyc", ".pyo")) and f != ".DS_Store"]

    out = args.output or os.path.join(ROOT, "bnx_vendor_%s.zip" % etiqueta)
    cache_real = os.path.realpath(CACHE)
    n_files, total = 0, 0
    with zipfile.ZipFile(out, "w", zipfile.ZIP_STORED, allowZip64=True) as z:
        for full in lista:
            # Ruta dentro del ZIP: relativa al cache, bajo '.bnx_vendor_cache/'.
            rel = os.path.relpath(os.path.realpath(full), cache_real)
            if rel.startswith(".."):
                continue
            arc = os.path.join(".bnx_vendor_cache", rel).replace(os.sep, "/")
            z.write(full, arc)
            n_files += 1
            total += os.path.getsize(full)

    mb = total / 1024 / 1024
    print("OK: %s" % out)
    print("    %d archivos, %.1f MB." % (n_files, mb))
    print("    Copialo al portal y corre:  python importar_vendor.py %s"
          % os.path.basename(out))
    return 0


if __name__ == "__main__":
    sys.exit(main())
