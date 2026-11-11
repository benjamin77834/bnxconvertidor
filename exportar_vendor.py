#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
exportar_vendor.py — Empaqueta el CACHE de vendor (.bnx_vendor_cache/) en un ZIP
para llevarlo a un servidor AISLADO (sin internet), como el del banco.

El servidor del banco no tiene internet y PySpark pesa ~300-700 MB (no cabe en
GitHub). Este script genera UN ZIP con PySpark + mex-lib + toolbox + pandas, que
copias al servidor UNA vez y descomprimes con importar_vendor.py. Asi el
'ambiente completo' del Framework MLOps v2 funciona offline SIN botones ni pasos.

USO (en tu Mac, donde SI tienes el cache lleno):
    python exportar_vendor.py                 # todo (ambas series, ~1.1 GB)
    python exportar_vendor.py --serie py38-311  # solo Python 3.8-3.11 (~320 MB)
    python exportar_vendor.py --serie py312plus # solo Python 3.12+ (~440 MB)
    python exportar_vendor.py -o /ruta/salida.zip

Produce 'bnx_vendor_<serie>.zip'. Pasalo al servidor y alla corre:
    python importar_vendor.py bnx_vendor_py38-311.zip
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
    """Carpetas del cache a incluir segun la serie elegida ('all' = todo)."""
    dirs = list(ALWAYS)
    if serie == "all":
        dirs += ["py38-311", "py312plus", "mlops_deps"]
    elif serie == "py38-311":
        # PySpark 3.5 + sus deps cp311 (py38-311) de mlops_deps. '_dl' = wheels que el
        # generador bajo solo (cytoolz/unidecode/pandas para 3.9-3.10, ...).
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


def main():
    ap = argparse.ArgumentParser(description="Empaqueta el vendor para un server aislado.")
    ap.add_argument("--serie", default="all", choices=["all", "py38-311", "py312plus"],
                    help="Serie de PySpark a incluir (por version de Python del destino).")
    ap.add_argument("-o", "--output", default=None, help="Ruta del ZIP de salida.")
    args = ap.parse_args()

    if not os.path.isdir(CACHE):
        print("ERROR: no existe el cache %s (genera un paquete 'ambiente completo' primero)." % CACHE)
        return 1

    out = args.output or os.path.join(ROOT, "bnx_vendor_%s.zip" % args.serie)
    dirs = _dirs_for(args.serie)

    n_files, total = 0, 0
    with zipfile.ZipFile(out, "w", zipfile.ZIP_STORED, allowZip64=True) as z:
        for d in dirs:
            base = os.path.join(CACHE, d)
            if not os.path.isdir(base):
                continue
            for root, subdirs, files in os.walk(base):
                subdirs[:] = [s for s in subdirs if s != "__pycache__"]
                for fn in files:
                    if fn.endswith((".pyc", ".pyo")) or fn == ".DS_Store":
                        continue
                    full = os.path.join(root, fn)
                    # Ruta dentro del ZIP: relativa al cache, bajo '.bnx_vendor_cache/'.
                    rel = os.path.relpath(full, CACHE)
                    arc = os.path.join(".bnx_vendor_cache", rel).replace(os.sep, "/")
                    z.write(full, arc)
                    n_files += 1
                    total += os.path.getsize(full)

    mb = total / 1024 / 1024
    print("OK: %s" % out)
    print("    %d archivos, %.1f MB." % (n_files, mb))
    print("    Copialo al servidor y corre:  python importar_vendor.py %s"
          % os.path.basename(out))
    return 0


if __name__ == "__main__":
    sys.exit(main())
