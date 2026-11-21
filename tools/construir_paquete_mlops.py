#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Arma los dos ZIP del Framework MLOps v2 (con y sin PySpark) desde una carpeta de proyecto del banco,
igual que el portal (/api/mlops/package/build con variantes 'ambas'), sin levantar el servidor.

  .venv/bin/python tools/construir_paquete_mlops.py --src <proyecto> --out /tmp/paquetes [--py py3.11]

Sube los .py de la carpeta (jobs/, toolbox/, utils/, bnmxverse/, main.py) y los .json/.yaml/.cfg/.ini
de bin/settings (van a bank_src/settings/ del paquete). Con --sin-settings omite esa config.
Tambien sube los RECURSOS no Python (bin/static/** modelos .xgb/.pkl/..., bin/opt/** profile.sh, ...) a
bank_src/ con la misma ruta relativa a bin/; --max-recurso-mb limita cada archivo (default 100, o
BNX_MAX_RECURSO_MB) y se avisa el tamano total. --sin-recursos los omite. Son datos INTERNOS del banco:
solo van al ZIP generado, nunca a git.
Solo LECTURA de --src. Usa el cache de librerias (vendor_cache); sin red.
"""
import argparse
import os
import sys

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, RAIZ)
EXT_CONFIG = (".json", ".yaml", ".yml", ".cfg", ".ini")


def leer_fuentes(src, con_settings=True, con_recursos=True, max_mb=None, avisos=None):
    """Fuentes del proyecto: .py, config de bin/settings y (con_recursos) recursos no Python de bin/**.
    Un recurso mayor que max_mb se omite y se anota en `avisos` (lista)."""
    import base64
    from src import mlops_pkg as mp
    lim = float(max_mb if max_mb is not None else mp.MAX_RECURSO_MB)
    out = []
    base = os.path.basename(os.path.abspath(src))
    for r, ds, fs in os.walk(src):
        ds[:] = [d for d in ds if d not in (".git", "__pycache__", "logs", "node_modules")]
        for f in sorted(fs):
            ruta = os.path.join(r, f)
            rel = os.path.relpath(ruta, src).replace(os.sep, "/")
            es_cfg = f.lower().endswith(EXT_CONFIG) and "/settings/" in "/" + rel
            if not f.lower().endswith(".py") and not es_cfg:
                if con_recursos and mp._ruta_recurso(base + "/" + rel):
                    tam = os.path.getsize(ruta)
                    if tam > lim * 1048576:
                        if avisos is not None:
                            avisos.append("%s (%.1f MB) supera el limite de %.0f MB: omitido" % (rel, tam / 1048576.0, lim))
                        continue
                    with open(ruta, "rb") as fh:
                        out.append({"name": base + "/" + rel, "b64": base64.b64encode(fh.read()).decode("ascii")})
                continue
            if f.lower().endswith(".py") or con_settings:
                with open(ruta, "r", encoding="utf-8", errors="replace") as fh:
                    out.append({"name": base + "/" + rel, "code": fh.read()})
    return out


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--src", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--py", default="py3.11")
    ap.add_argument("--sin-settings", action="store_true")
    ap.add_argument("--sin-recursos", action="store_true", help="no incluir bin/static, bin/opt, ...")
    ap.add_argument("--max-recurso-mb", type=float, default=None, help="limite por recurso (default 100 / BNX_MAX_RECURSO_MB)")
    a = ap.parse_args(argv)
    from src.mlops_pkg import build_package_from_sources, zip_from_files
    from src.mlops_pkg import ULTIMO_FALTAN_OFFLINE, ULTIMO_VENDOR  # noqa: F401
    from src.py2spark import convert_code
    from src.perf_optimizer import optimize_pyspark
    os.makedirs(a.out, exist_ok=True)
    avisos = []
    fuentes = leer_fuentes(a.src, not a.sin_settings, not a.sin_recursos, a.max_recurso_mb, avisos)
    print("[tool] %d fuente(s) de %s" % (len(fuentes), a.src))
    for av in avisos:
        print("[tool] AVISO:", av)
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
    if meta.get("compat"):
        print("[tool] " + meta["compat"]["texto"].replace("\n", "\n[tool] "))
    print("[tool] recursos incluidos: %d archivo(s), %.2f MB" % (len(meta.get("recursos") or []), meta.get("recursos_mb") or 0))
    for rc in meta.get("recursos") or []:
        print("   recurso %s (%.1f KB)" % (rc["file"], rc["size"] / 1024.0))
    for r in report:
        if not r.get("_meta") and (not r.get("ok") or r.get("role") == "job"):
            print("   ", r.get("name"), "->", r.get("source") or r.get("reason"), "ok=%s" % r.get("ok"))
    return 0


if __name__ == "__main__":
    sys.exit(main())
