#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
importar_vendor.py — Descomprime un ZIP de vendor (hecho con exportar_vendor.py)
en el cache local del portal, en un servidor AISLADO (sin internet).

Despues de esto, el 'ambiente completo' del Framework MLOps v2 empaqueta PySpark
offline SIN necesidad de internet ni del boton de importar. Corre UNA sola vez.

USO (en el servidor del banco, en la raiz del proyecto bnxconvertidor):
    python importar_vendor.py bnx_vendor_py38-311.zip

Es idempotente: vuelve a correrlo y solo sobrescribe/añade lo que traiga el ZIP.
"""
import os
import sys
import zipfile

ROOT = os.path.dirname(os.path.abspath(__file__))


def main():
    if len(sys.argv) < 2:
        print("USO: python importar_vendor.py <bnx_vendor_*.zip>")
        return 1
    zpath = sys.argv[1]
    if not os.path.isfile(zpath):
        print("ERROR: no existe el archivo %s" % zpath)
        return 1

    with zipfile.ZipFile(zpath, "r") as z:
        names = z.namelist()
        # Seguridad: todas las entradas deben vivir bajo '.bnx_vendor_cache/'.
        bad = [n for n in names if not n.startswith(".bnx_vendor_cache/")
               or ".." in n.split("/")]
        if bad:
            print("ERROR: el ZIP tiene rutas inesperadas (%d). Abortando." % len(bad))
            return 1
        n, total = 0, 0
        for info in z.infolist():
            if info.is_dir():
                continue
            dest = os.path.join(ROOT, info.filename)
            os.makedirs(os.path.dirname(dest), exist_ok=True)
            with z.open(info) as src, open(dest, "wb") as out:
                data = src.read()
                out.write(data)
                total += len(data)
            n += 1

    print("OK: importado en %s" % os.path.join(ROOT, ".bnx_vendor_cache"))
    print("    %d archivos, %.1f MB." % (n, total / 1024 / 1024))
    print("    Ya puedes generar paquetes con 'ambiente completo' OFFLINE.")
    print("    (Reinicia serve_ui.py si estaba corriendo.)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
