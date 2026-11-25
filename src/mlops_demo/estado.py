# -*- coding: utf-8 -*-
"""Estado compartido del DEMO de los jobs del banco (solo se usa con --demo)."""
import os

E = {
    "activo": False,       # parches puestos
    "pkg": None,           # carpeta del paquete (junto a main.py)
    "out": None,           # <paquete>/demo_out
    "filas": 50,
    "seed": 7,
    "estricto": False,
    "cohort": None,
    "job": "",
    "bank_dirs": [],
    "lib_dirs": [],        # librerias del banco instaladas (requirements-bank.txt) + bank_compat.py
    "settings_dir": None,
    "demo_data": [],       # carpetas con demo_data/<tabla>.parquet|csv
    "raices": [],          # raices absolutas de cluster sacadas de los settings
    "registro": {},        # tabla(lower) -> [columnas] sacadas de los settings
    "features": {},        # fuente -> [nombres de variables] (dqc_sources de los settings)
    "tablas_prod": {},     # tabla(lower) -> {"dest","job","filas"}
    "rutas_prod": {},      # destino local -> {"orig","job","filas"}
    "lecturas": [],
    "escrituras": [],
    "comandos": [],
    "inventadas": {},      # modelo/job -> claves de settings inventadas (settings minimos inferidos)
    "orig": {},            # funciones originales (para desactivar)
    "enproceso": 0,        # >0: no interceptar (llamadas internas del demo)
}


def log(msg):
    print("[demo] " + msg)


def env_int(nombre, defecto):
    try:
        return int(os.environ.get(nombre, defecto))
    except (TypeError, ValueError):
        return defecto


def reset():
    for k in ("lecturas", "escrituras", "comandos", "bank_dirs", "lib_dirs", "demo_data", "raices"):
        E[k] = []
    for k in ("registro", "features", "tablas_prod", "rutas_prod", "orig", "inventadas"):
        E[k] = {}
    E.update({"activo": False, "job": "", "enproceso": 0, "settings_dir": None})
