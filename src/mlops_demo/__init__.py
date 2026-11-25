# -*- coding: utf-8 -*-
"""DEMO de los jobs del banco (def run(kernel)) en una maquina sin cluster.

Solo se activa en modo DEMO (main.py sin --settings o con --demo); con datos reales NADA de esto se
importa ni se parchea. No modifica el codigo del banco: parchea PySpark/os/subprocess en memoria.

  iniciar(pkg, ...)  -> estado (carpeta de salida, semilla, filas, settings, demo_data)
  activar()          -> pone los parches (lecturas sinteticas, rutas a demo_out/, shim hdfs)
  set_job(nombre)    -> atribuye lecturas/escrituras/comandos al job en curso
  reporte()          -> texto del reporte final
  desactivar()       -> quita los parches
"""
import os
import re
import shutil

from . import analisis, estado, reporte as _rep, rutas
from .estado import E, env_int, log


def iniciar(pkg, bank_dirs=(), settings_dir=None, cohort=None, limpiar=True, filas=None, seed=None):
    desactivar()                 # si habia parches puestos (reinicio), se quitan antes de limpiar el estado
    estado.reset()
    E["pkg"] = os.path.abspath(pkg)
    E["out"] = os.path.abspath(os.environ.get("BNX_DEMO_OUT") or os.path.join(E["pkg"], "demo_out"))
    E["filas"] = max(1, filas or env_int("BNX_DEMO_FILAS", 50))
    E["seed"] = seed if seed is not None else env_int("BNX_DEMO_SEED", 7)
    E["estricto"] = os.environ.get("BNX_DEMO_ESTRICTO", "") == "1"
    E["cohort"] = cohort
    E["bank_dirs"] = [os.path.abspath(d) for d in bank_dirs if d and os.path.isdir(d)]
    E["lib_dirs"] = dirs_librerias(E["pkg"])
    E["settings_dir"] = settings_dir
    dd = [os.environ.get("BNX_DEMO_DATA"), os.path.join(E["pkg"], "demo_data")]
    E["demo_data"] = [d for d in dd if d and os.path.isdir(d)]
    E["raices"] = rutas.raices_de_settings(settings_dir)
    E["registro"] = analisis.registro_settings(settings_dir)
    E["features"] = analisis.features_de_settings(settings_dir)
    analisis.precargar(E["bank_dirs"])
    if limpiar and os.path.isdir(E["out"]):
        shutil.rmtree(E["out"], ignore_errors=True)
    os.makedirs(E["out"], exist_ok=True)
    hive = os.path.join(E["out"], "hive")
    if not limpiar and os.path.isdir(hive):     # --source: tablas que dejo una corrida previa
        for db in sorted(os.listdir(hive)):
            for t in sorted(os.listdir(os.path.join(hive, db))):
                E["tablas_prod"]["%s.%s" % (db, t)] = {"dest": os.path.join(hive, db, t),
                                                       "job": "corrida previa", "filas": None}
    return E["out"]


def _nombres_requirements(ruta):
    out = []
    try:
        with open(ruta, encoding="utf-8") as fh:
            for linea in fh:
                n = re.split(r"[\s;<>=!~\[#]", linea.strip(), 1)[0]
                if n and not n.startswith("-"):
                    out.append(n)
    except OSError:
        pass
    return out


def dirs_librerias(pkg):
    """Carpetas de las librerias del banco instaladas (las de requirements-bank.txt, via top_level.txt
    de su distribucion) y la capa de compatibilidad bank_compat.py. El DEMO suma las columnas que ese
    codigo usa al generar datos sinteticos de lecturas que pasan por ellas."""
    out = []
    try:
        from importlib import metadata as _md
    except ImportError:     # Python < 3.8
        _md = None
    for nombre in _nombres_requirements(os.path.join(pkg, "requirements-bank.txt")) if _md else []:
        dist = None
        for n in (nombre, nombre.replace("-", "_")):
            try:
                dist = _md.distribution(n)
                break
            except Exception:
                continue
        if dist is None:
            continue
        tops = [t.strip() for t in (dist.read_text("top_level.txt") or "").splitlines() if t.strip()]
        if not tops:     # wheel sin top_level.txt: primeras carpetas de sus archivos (RECORD)
            tops = sorted(set(str(f).replace("\\", "/").split("/")[0] for f in (dist.files or [])
                              if "/" in str(f).replace("\\", "/") and ".dist-info" not in str(f)
                              and not str(f).startswith("..")))
        for t in tops:
            try:
                d = os.path.abspath(str(dist.locate_file(t)))
            except Exception:
                continue
            if os.path.isdir(d) and d not in out:
                out.append(d)
    compat = os.path.join(pkg, "bank_compat.py")
    if os.path.isfile(compat):
        out.append(os.path.abspath(compat))
    return out


def activar():
    from . import cli, fsrutas, sparkpatch
    if E["activo"]:
        return
    sparkpatch.aplicar()
    cli.aplicar()
    fsrutas.aplicar()
    E["activo"] = True
    log("activado: lecturas sinteticas por consulta (%d filas), rutas del cluster -> %s, shim hdfs/CLI"
        % (E["filas"], E["out"]))
    if E["demo_data"]:
        log("datos de muestra del usuario: %s" % ", ".join(E["demo_data"]))


def desactivar():
    from . import cli, fsrutas, sparkpatch
    if not E["activo"]:
        return
    fsrutas.quitar()
    cli.quitar()
    sparkpatch.quitar()
    E["activo"] = False


def set_job(nombre):
    E["job"] = nombre


def reporte(imprimir=True):
    txt = _rep.texto()
    ruta = _rep.guardar()
    if imprimir:
        print(txt)
        if ruta:
            print("[demo] reporte JSON: %s" % ruta)
    return txt

def registrar_inventadas(inventadas):
    """{'modelo/job': [claves inventadas]} de los settings minimos inferidos (va al reporte)."""
    E["inventadas"] = dict(inventadas or {})
