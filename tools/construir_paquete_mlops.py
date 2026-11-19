#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Arma los dos ZIP del Framework MLOps v2 (con y sin PySpark) desde una carpeta de proyecto del banco,
igual que el portal (/api/mlops/package/build con variantes 'ambas'), sin levantar el servidor.

  .venv/bin/python tools/construir_paquete_mlops.py --src <proyecto> --out /tmp/paquetes [--py py3.11]

Sube los .py de la carpeta (jobs/, toolbox/, utils/, bnmxverse/, main.py) y los .json/.yaml/.cfg/.ini
de bin/settings (van a bank_src/settings/ del paquete). Con --sin-settings omite esa config.
Solo LECTURA de --src. Usa el cache de librerias (vendor_cache); sin red.
"""
import argparse
import os
import sys

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, RAIZ)
EXT_CONFIG = (".json", ".yaml", ".yml", ".cfg", ".ini")


def leer_fuentes(src, con_settings=True):
    out = []
    for r, ds, fs in os.walk(src):
        ds[:] = [d for d in ds if d not in (".git", "__pycache__", "logs", "node_modules")]
        for f in sorted(fs):
            rel = os.path.relpath(os.path.join(r, f), src).replace(os.sep, "/")
            es_cfg = f.lower().endswith(EXT_CONFIG) and "/settings/" in "/" + rel
            if not (f.lower().endswith(".py") or (con_settings and es_cfg)):
                continue
            with open(os.path.join(r, f), "r", encoding="utf-8", errors="replace") as fh:
                out.append({"name": os.path.basename(os.path.abspath(src)) + "/" + rel, "code": fh.read()})
    return out


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--src", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--py", default="py3.11")
    ap.add_argument("--sin-settings", action="store_true")
    a = ap.parse_args(argv)
    from src.mlops_pkg import build_package_from_sources, zip_from_files
    from src.mlops_pkg import ULTIMO_FALTAN_OFFLINE, ULTIMO_VENDOR  # noqa: F401
    from src.py2spark import convert_code
    from src.perf_optimizer import optimize_pyspark
    os.makedirs(a.out, exist_ok=True)
    fuentes = leer_fuentes(a.src, not a.sin_settings)
    print("[tool] %d fuente(s) de %s" % (len(fuentes), a.src))
    con = os.path.join(a.out, "framework_mlops_v2_con_pyspark.zip")
    _z, _fn, report = build_package_from_sources(
        fuentes, convert_fn=convert_code, optimize_fn=optimize_pyspark, include_bank_libs=True, optimize=True,
        full_env=True, py_target=a.py, out_path=con, ciencia=True, plataformas=["linux"], spark_modo="incluido")
    meta = next((r for r in report if r.get("_meta")), {})
    print("[tool] con PySpark: %s (%.0f MB) faltan=%s" % (con, os.path.getsize(con) / 1048576.0,
                                                          meta.get("entorno_faltan")))
    code_files = meta.get("_code_files") or {}
    sep_files = meta.get("_sep_files") or {}
    sin = os.path.join(a.out, "framework_mlops_v2_sin_pyspark.zip")
    zip_from_files(code_files, sep_files, full_env=False, py_target=a.py, out_path=sin,
                   plataformas=["linux"], spark_modo="servidor")
    print("[tool] sin PySpark: %s (%.0f MB)" % (sin, os.path.getsize(sin) / 1048576.0))
    for r in report:
        if not r.get("_meta") and (not r.get("ok") or r.get("role") == "job"):
            print("   ", r.get("name"), "->", r.get("source") or r.get("reason"), "ok=%s" % r.get("ok"))
    return 0


if __name__ == "__main__":
    sys.exit(main())
