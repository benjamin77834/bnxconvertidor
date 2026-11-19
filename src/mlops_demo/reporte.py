# -*- coding: utf-8 -*-
"""Reporte final del DEMO: por job, fuentes leidas, columnas, filas escritas y comandos simulados."""
import json
import os

from .estado import E


def datos():
    jobs = []
    vistos = []
    for lst in (E["lecturas"], E["escrituras"], E["comandos"]):
        for x in lst:
            if x["job"] not in vistos:
                vistos.append(x["job"])
    for j in vistos:
        jobs.append({
            "job": j,
            "lecturas": [x for x in E["lecturas"] if x["job"] == j],
            "escrituras": [x for x in E["escrituras"] if x["job"] == j],
            "comandos": [x for x in E["comandos"] if x["job"] == j],
        })
    return jobs


def _fmt_cols(cols, n=8):
    cols = list(cols or [])
    return ", ".join(cols[:n]) + (" ... (+%d)" % (len(cols) - n) if len(cols) > n else "")


def texto():
    out = ["=" * 64, "REPORTE DEL DEMO (datos sinteticos / demo_data / producidos por otro job)", "=" * 64]
    out.append("filas por tabla sintetica: %d | salidas en: %s" % (E["filas"], E["out"]))
    for j in datos():
        out.append("-" * 64)
        out.append("JOB %s" % (j["job"] or "(sin job)"))
        for x in j["lecturas"]:
            out.append("  LEE   [%s] %s | %d cols: %s%s" % (
                x["origen"], x["nombre"], len(x["cols"]), _fmt_cols(x["cols"]),
                "" if x["filas"] is None else " | %s filas" % x["filas"]))
        for x in j["escrituras"]:
            out.append("  ESCRIBE %s %s -> %s | %s filas" % (
                x["tipo"], x["destino"], os.path.relpath(x["local"], E["out"]) if E["out"] else x["local"],
                "?" if x["filas"] is None else x["filas"]))
        for x in j["comandos"]:
            out.append("  CMD   [%s] %s" % (x["tipo"], x["cmd"]))
    for j, claves in sorted((E.get("inventadas") or {}).items()):
        if claves:
            out.append("  SETTINGS INVENTADOS para %s (%d): %s" % (j, len(claves), ", ".join(claves[:12])
                                                               + (" ..." if len(claves) > 12 else "")))
    out.append("=" * 64)
    return "\n".join(out)


def guardar():
    if not E.get("out"):
        return None
    try:
        os.makedirs(E["out"], exist_ok=True)
        ruta = os.path.join(E["out"], "REPORTE_DEMO.json")
        with open(ruta, "w", encoding="utf-8") as fh:
            json.dump({"filas": E["filas"], "seed": E["seed"], "jobs": datos(),
                       "settings_inventados": E.get("inventadas") or {}}, fh, indent=1, default=str)
        return ruta
    except OSError:
        return None
