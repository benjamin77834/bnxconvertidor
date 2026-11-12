#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
exportar_vendor.py — Empaqueta el CACHE de vendor (.venv/bnx_vendor_cache/) en un ZIP
para llevarlo a un servidor AISLADO (sin internet), como el del banco o un portal
en Windows sin cache.

El servidor del banco no tiene internet y PySpark pesa ~300-450 MB (no cabe en
GitHub). Este script genera UN ZIP que copias al portal UNA vez y descomprimes con
importar_vendor.py. Asi el Framework MLOps v2 arma los paquetes offline.

USO (en tu Mac, donde SI tienes el cache lleno):
    python exportar_vendor.py --python 3.8                 # RECOMENDADO: solo lo que
                                                           # usa Python 3.8 en Linux
    python exportar_vendor.py --python 3.8 --python 3.12   # ademas Python 3.12
    python exportar_vendor.py --python 3.8 --extra         # + xgboost/scikit-learn (pasos extra)
Siempre lleva TODAS las librerias del banco (bank_libs) + solo el minimo (PySpark+deps).
    python exportar_vendor.py --serie all                  # (antiguo) cache entero, pesado
    python exportar_vendor.py -o /ruta/salida.zip
    python exportar_vendor.py --python 3.12 --sin-banco    # SIN librerias del banco (publicable)

Produce 'bnx_vendor_py3.8.zip' (o bnx_vendor_<serie>.zip). En el portal:
    python importar_vendor.py bnx_vendor_py3.8.zip
"""
import argparse
import os
import re
import sys
import zipfile

ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ROOT)
from src.vendor_cache import cache_dir  # noqa: E402
CACHE = cache_dir()   # <venv>/bnx_vendor_cache (o BNX_VENDOR_CACHE / cache viejo)

# Series de PySpark por version de Python del DESTINO.
SERIES = {"py38-311", "py312plus"}
# Carpetas que SIEMPRE se incluyen (no dependen de la serie).
ALWAYS = ["bank_libs"]


def _es_interno(ruta):
    """Codigo/libs INTERNAS del banco (nunca publicables): bank_libs/pkgcode (toolbox,
    bnmxverse, utils) y los sdist mex-lib*. Las wheels publicas de PyPI que viven en
    bank_libs/wheels (pandas 1.3.1 cp38, numpy, pytest...) NO son internas."""
    r = ruta.replace(os.sep, "/").lower()
    partes = r.split("/")
    base = partes[-1]
    return (r.startswith("bank_libs/pkgcode") or base.startswith(("mex-lib", "mex_lib"))
            or any(p in ("bnmxverse", "toolbox") for p in partes))


def _arc_sin_banco(rel, versiones):
    """Ruta(s) dentro del ZIP --sin-banco: las wheels publicas de bank_libs/wheels se
    reubican en mlops_deps/<serie>/ (el ZIP publico no lleva la carpeta bank_libs)."""
    from src.vendor_cache import serie_de
    r = rel.replace(os.sep, "/")
    if not r.startswith("bank_libs/wheels/"):
        return [r]
    nombre = r.split("/")[-1]
    m = re.search(r"-cp3(\d+)-", nombre)
    if m:
        series = {serie_de("3." + m.group(1))}
    else:
        series = {serie_de(v) for v in versiones}
    return ["mlops_deps/%s/%s" % (sr, nombre) for sr in sorted(series)]


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


def _files_for_python(versiones, extra=False, sin_banco=False):
    """Archivos MINIMOS del cache para generar paquetes (ligero y completo, con y sin
    pasos extra) para esas versiones EXACTAS de Python en Linux: lo que pip resuelve
    + el codigo de path del banco (toolbox/bnmxverse/utils) + las mex-lib."""
    sys.path.insert(0, ROOT)
    os.environ.setdefault("BNX_NO_DOWNLOAD", "1")   # exportar lo que HAY, sin bajar
    from src import mlops_pkg as mp
    from src import vendor_cache as vc
    # Minimo indispensable: lo que pip resuelve (con PySpark) para esas versiones; los pasos
    # extra (xgboost/scikit-learn) solo con extra=True.
    keep, faltan = vc.minimo(versiones, extra=extra)
    files = set(keep)
    if sin_banco:
        files = {f for f in files if not _es_interno(os.path.relpath(os.path.realpath(f), os.path.realpath(CACHE)))}
        return sorted(files), faltan
    bank = os.path.join(CACHE, "bank_libs")
    for root, subdirs, fns in os.walk(os.path.join(bank, "pkgcode")):
        subdirs[:] = [s for s in subdirs if s != "__pycache__"]
        files.update(os.path.join(root, f) for f in fns
                     if not f.endswith((".pyc", ".pyo")) and f != ".DS_Store")
    wh = os.path.join(bank, "wheels")
    if os.path.isdir(wh):          # TODAS las librerias del banco (los 8 sdist mex-lib*)
        files.update(os.path.join(wh, f) for f in os.listdir(wh) if f.lower().startswith("mex"))
    return sorted(files), faltan


def main():
    ap = argparse.ArgumentParser(description="Empaqueta el vendor para un server aislado.")
    ap.add_argument("--python", action="append", default=None, metavar="3.X",
                    help="RECOMENDADO: solo lo que necesitan los paquetes para esa version "
                         "exacta de Python (repetible: --python 3.8 --python 3.12).")
    ap.add_argument("--serie", default="all", choices=["all", "py38-311", "py312plus"],
                    help="(antiguo) cache completo de la serie: mucho mas pesado.")
    ap.add_argument("--extra", action="store_true",
                    help="Incluir tambien xgboost/scikit-learn (pasos extra). Default: solo el minimo.")
    ap.add_argument("--sin-banco", action="store_true",
                    help="NO incluir bank_libs/ ni modulos internos (bnmxverse/toolbox/utils/mex-lib): "
                         "ZIP publicable (p.ej. GitHub Release). Requiere --python.")
    ap.add_argument("-o", "--output", default=None, help="Ruta del ZIP de salida.")
    args = ap.parse_args()

    if not os.path.isdir(CACHE):
        print("ERROR: no existe el cache %s (genera un paquete 'ambiente completo' primero)." % CACHE)
        return 1

    if args.sin_banco and not args.python:
        print("ERROR: --sin-banco requiere --python 3.X")
        return 1
    if args.python:
        versiones = sorted({v.replace("py", "").strip() for v in args.python},
                           key=lambda s: [int(x) for x in s.split(".")])
        etiqueta = "py" + "_".join(versiones)
        lista, faltan = _files_for_python(versiones, extra=args.extra, sin_banco=args.sin_banco)
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
            if args.sin_banco:
                if _es_interno(rel):
                    continue
                arcs = [".bnx_vendor_cache/" + a for a in _arc_sin_banco(rel, versiones)]
            else:
                arcs = [os.path.join(".bnx_vendor_cache", rel).replace(os.sep, "/")]
            for arc in arcs:
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
