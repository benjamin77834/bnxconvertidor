# -*- coding: utf-8 -*-
"""Escrituras del DEMO: parquet/tablas Hive a demo_out/ y registro de lo producido."""
import os
import re

from . import lector, rutas
from .estado import E, log


def _contar(dest, fmt="parquet"):
    try:
        sp = lector.spark_activa()
        if fmt == "csv":
            return E["orig"]["r_csv"](sp.read, dest).count()
        if fmt in ("json", "orc", "text"):
            return E["orig"]["r_" + fmt](sp.read, dest).count()
        return E["orig"]["r_parquet"](sp.read, dest).count()
    except Exception:
        return None


def registrar_ruta(orig, dest, job=None, fmt="parquet"):
    filas = _contar(dest, fmt)
    E["rutas_prod"][os.path.abspath(dest)] = {"orig": orig, "job": job or E["job"], "filas": filas}
    E["escrituras"].append({"job": job or E["job"], "tipo": "ruta", "destino": orig,
                            "local": dest, "filas": filas})


def registrar_tabla(nombre, dest):
    filas = _contar(dest)
    info = {"dest": dest, "job": E["job"], "filas": filas}
    E["tablas_prod"][nombre.lower()] = info
    if nombre.lower().startswith("default."):
        E["tablas_prod"][nombre.lower()[8:]] = info
    E["escrituras"].append({"job": E["job"], "tipo": "tabla", "destino": nombre, "local": dest,
                            "filas": filas})


def dividir_tabla(nombre):
    n = str(nombre).replace("`", "")
    if "." in n:
        db, t = n.rsplit(".", 1)
        return db, t
    return "default", n


def escribir_ruta(orig_fn, writer, path, *a, fmt="parquet", **k):
    dest = rutas.redirigir(path)
    r = orig_fn(writer, dest, *a, **k)
    registrar_ruta(path if isinstance(path, str) else str(path), dest, fmt=fmt)
    return r


def escribir_tabla(df, nombre, modo=None, particion=None, fija=None, orig_parquet=None):
    """Tabla Hive -> parquet local en demo_out/hive/<db>/<tabla> (particiones como carpetas col=valor)."""
    db, t = dividir_tabla(nombre)
    dest = rutas.ruta_hive(db, t)
    modo = (modo or "append").lower()
    w = df.write.mode("overwrite" if modo == "overwrite" else ("ignore" if modo == "ignore" else "append"))
    if fija:                      # INSERT ... PARTITION (col='v'): solo esa particion
        sub = os.path.join(dest, "/".join("%s=%s" % (c, v) for c, v in fija))
        w = df.write.mode("overwrite" if modo == "overwrite" else "append")
        orig_parquet(w, sub)
    else:
        cols = [particion] if isinstance(particion, str) else list(particion or [])
        if cols:
            w = w.partitionBy(*cols)
            if modo == "overwrite":
                w = w.option("partitionOverwriteMode", "dynamic")
        orig_parquet(w, dest)
    registrar_tabla("%s.%s" % (db, t), dest)
    return dest


_INS = re.compile(r"^\s*insert\s+(overwrite|into)\s+(?:table\s+)?([\w.`]+)\s*(?:partition\s*\(([^)]*)\))?\s*([\s\S]*)$",
                  re.I)
_CTAS = re.compile(r"^\s*create\s+(?:external\s+)?table\s+(?:if\s+not\s+exists\s+)?([\w.`]+)[\s\S]*?\bas\b\s+"
                   r"((?:select|with)[\s\S]*)$", re.I)


def insertar_sql(spark, q, sql_con_vistas):
    """INSERT OVERWRITE/INTO TABLE ... SELECT y CREATE TABLE ... AS SELECT -> tabla local."""
    from pyspark.sql import functions as F
    m = _INS.match(q)
    if m:
        modo, nombre, part, cuerpo = m.group(1).lower(), m.group(2), m.group(3), m.group(4)
    else:
        m2 = _CTAS.match(q)
        if not m2:
            return None
        modo, nombre, part, cuerpo = "overwrite", m2.group(1), None, m2.group(2)
    df = sql_con_vistas(cuerpo)
    fija = []
    for p in [x.strip() for x in (part or "").split(",") if x.strip()]:
        if "=" in p:
            c, v = [x.strip() for x in p.split("=", 1)]
            fija.append((c, v.strip("'\"")))
        else:
            fija = []
    escribir_tabla(df, nombre, "overwrite" if modo == "overwrite" else "append",
                   fija=fija or None, particion=None, orig_parquet=E["orig"]["w_parquet"])
    log("tabla escrita en local: %s (%s)" % (nombre, E["tablas_prod"][".".join(dividir_tabla(nombre)).lower()]["dest"]))
    return spark.range(0)
