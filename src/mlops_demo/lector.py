# -*- coding: utf-8 -*-
"""Lecturas del DEMO: SQL/tablas -> vistas temporales (demo_data | producida | sintetica)."""
import glob
import itertools
import os
import re
import sys

from . import analisis, datos, rutas, sqlmini
from .estado import E, log

_N = itertools.count(1)
_MARCAS = ("bnmxverse", "mex_lib", "toolbox", "jobs", "bank_src", "bank_pkg")


def spark_activa():
    from pyspark.sql import SparkSession
    return SparkSession.getActiveSession() or SparkSession.getDefaultSession()


def _es_lib(ruta):
    """Archivo de una libreria del banco instalada (requirements-bank.txt) o de la capa de compatibilidad."""
    return any(ruta == d or ruta.startswith(d + os.sep) for d in E.get("lib_dirs") or ())


def sitio(profundidad=2):
    """(archivo, linea, libs) del codigo del banco que hizo la lectura (primer marco 'de negocio').
    libs = ((archivo, linea), ...) de las librerias del banco que estan en medio (p. ej. un metodo de
    una libreria pip que lee un parquet con columnas que el job no menciona)."""
    f, cand, libs = sys._getframe(profundidad), None, []
    while f is not None:
        ruta = os.path.abspath(f.f_code.co_filename)
        partes = ruta.replace("\\", "/").split("/")
        if "pyspark" not in partes and "mlops_demo" not in partes and "bnx_demo" not in partes \
                and (any(ruta.startswith(os.path.abspath(d)) for d in E["bank_dirs"])
                     or any(p.startswith(m) for p in partes for m in _MARCAS)):
            if "toolbox" not in partes:
                return ruta, f.f_lineno, tuple(libs)
            cand = cand or (ruta, f.f_lineno, tuple(libs))
        elif _es_lib(ruta) and len(libs) < 6:
            libs.append((ruta, f.f_lineno))
        f = f.f_back
    return cand or (libs[0] + (tuple(libs),) if libs else None)


def columnas_sitio(st):
    if not st:
        return []
    libs = st[2] if len(st) > 2 else ()
    cols = [] if libs and (st[0], st[1]) == libs[0] else analisis.columnas_lectura(st[0], st[1])
    for ruta, ln in libs:
        cols = _unir(cols, analisis.columnas_funcion(ruta, ln))
    return cols


def buscar_demo_data(nombre):
    """Archivo demo_data/<tabla>.parquet|csv|json del usuario (db.tabla, tabla o ultimo tramo de ruta)."""
    low = str(nombre).lower().replace("\\", "/").rstrip("/")
    base = low.split("/")[-1]
    cands = [low.replace("/", "_"), base, base.split(".")[-1], base.replace(".", "__")]
    if "/" in low:
        cands.insert(0, "_".join(low.split("/")[-2:]))
    for d in E["demo_data"]:
        if not os.path.isdir(d):
            continue
        existentes = dict((f.lower(), f) for f in os.listdir(d))
        for c in cands:
            for ext in (".parquet", ".csv", ".json", ""):
                k = (c + ext).lower()
                if k in existentes and (ext or os.path.isdir(os.path.join(d, existentes[k]))):
                    return os.path.join(d, existentes[k])
    return None


def leer_archivo(spark, ruta):
    """Lee un parquet/csv/json con los lectores ORIGINALES (sin pasar por los parches)."""
    o = E["orig"]
    low = ruta.lower()
    if low.endswith(".csv"):
        return o["r_csv"](spark.read, ruta, header=True, inferSchema=True)
    if low.endswith(".json"):
        return o["r_json"](spark.read, ruta)
    return o["r_parquet"](spark.read, ruta)


def existe_ruta(p):
    if "*" in p or "?" in p:
        return bool(glob.glob(p))
    return os.path.exists(p)


def tabla_existe(spark, nombre):
    try:
        return bool(spark.catalog.tableExists(nombre))
    except Exception:
        return False


def _unir(*listas):
    out, vistos = [], set()
    for lst in listas:
        for c in lst or []:
            if c and c.lower() not in vistos:
                vistos.add(c.lower())
                out.append(c)
    return out


def _asignar_ambiguas(info):
    for c in info["ambiguas"]:
        duenos = [t for t in info["reales"] if c.lower() in [x.lower() for x in E["registro"].get(t, [])]
                  or c.lower() in [x.lower() for x in info["cols"].get(t, [])]]
        destino = duenos or info["reales"][:1]
        for t in destino:
            info["cols"].setdefault(t, [])
            if c.lower() not in [x.lower() for x in info["cols"][t]]:
                info["cols"][t].append(c)


def _hints_de(info, tabla):
    out = {}
    for (t, c), h in info["hints"].items():
        if t in (tabla, None):
            d = out.setdefault(c, {})
            for k, v in h.items():
                if k == "eq":
                    d.setdefault("eq", []).extend(v)
                else:
                    d[k] = v
    return out


def _pos(v):
    return v if isinstance(v, int) else None


def crear_vista(spark, nombre, info, st, sintetica=False):
    """Registra una vista temporal para la tabla `nombre`. Devuelve (vista, origen, cols, filas)."""
    low = nombre.lower()
    vista = "bnxdemo_%d_%s" % (next(_N), re.sub(r"\W", "_", low))
    cols = list(info["cols"].get(low, []))
    if low in info["estrella"] or "*" in info["estrella"] or not cols:
        cols = _unir(cols, E["registro"].get(low, []), columnas_sitio(st))
    if not sintetica:
        dd = buscar_demo_data(nombre)
        if dd:
            df = leer_archivo(spark, dd)
            df.createOrReplaceTempView(vista)
            return vista, "demo_data", list(df.columns), None
        prod = E["tablas_prod"].get(low)
        if prod and os.path.exists(prod["dest"]):
            df = E["orig"]["r_parquet"](spark.read, prod["dest"])
            df.createOrReplaceTempView(vista)
            return vista, "producida:" + prod["job"], list(df.columns), prod.get("filas")
    df, _sp = datos.generar_df(spark, cols, _hints_de(info, low), info["usos"])
    df.createOrReplaceTempView(vista)
    return vista, "sintetica", list(df.columns), E["filas"]


def _anotar(job, nombre, origen, cols, filas):
    E["lecturas"].append({"job": job, "nombre": nombre, "origen": origen, "cols": cols, "filas": filas})


def ejecutar_select(spark, q, orig_sql, a, k, st=None):
    """Corre un SELECT con las tablas del cluster sustituidas por vistas locales."""
    info = sqlmini.analizar(q)
    ext = [t for t in info["tablas"] if not tabla_existe(spark, t["nombre"])]
    if not ext:
        return orig_sql(spark, q, *a, **k)
    _asignar_ambiguas(info)
    st = st or sitio(3)
    for intento in (0, 1):
        vistas, reemplazos, notas = {}, [], []
        for t in ext:
            low = t["nombre"].lower()
            if low not in vistas:
                vistas[low] = crear_vista(spark, t["nombre"], info, st, sintetica=bool(intento))
                notas.append((t["nombre"],) + vistas[low][1:])
            reemplazos.append((t["tok"], vistas[low][0]))
        usa_real = any(not n[1].startswith("sintetica") for n in notas)
        try:
            df = orig_sql(spark, sqlmini.reescribir(q, reemplazos), *a, **k)
            if intento == 0 and usa_real and any(n[1].startswith("producida") for n in notas) \
                    and df.limit(1).count() == 0:
                log("la tabla producida no devuelve filas con este filtro: se usa data sintetica (%s)"
                    % ", ".join(n[0] for n in notas))
                continue
        except Exception as ex:
            if intento == 0 and any(n[1].startswith("producida") for n in notas):
                log("la tabla producida no sirve para esta consulta (%s): se usa data sintetica"
                    % str(ex).splitlines()[0][:100])
                continue
            raise
        for n in notas:
            _anotar(E["job"], n[0], n[1], n[2], n[3])
        return df
    raise RuntimeError("[demo] no se pudo resolver la consulta")
