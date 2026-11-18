# -*- coding: utf-8 -*-
"""Parches de sistema de archivos (open/os/shutil) y pandas.read_* para rutas del cluster (solo DEMO)."""
import builtins
import os
import shutil

from . import datos, lector, rutas
from .estado import E, log

_OS = ("makedirs", "mkdir", "listdir", "remove", "unlink", "walk")
_PATH = ("exists", "isdir", "isfile", "getsize")
_SHUTIL = ("rmtree", "copy", "copy2", "copyfile", "copytree", "move")


def _r(p):
    return rutas.redirigir(p, True) if isinstance(p, (str, os.PathLike)) else p


def _envolver(fn):
    def f(*a, **k):
        if a:
            a = (_r(a[0]),) + a[1:]
        return fn(*a, **k)
    f.__name__ = getattr(fn, "__name__", "f")
    return f


def _open(file, mode="r", *a, **k):
    if isinstance(file, (str, os.PathLike)):
        d = _r(file)
        if d != file and any(c in str(mode) for c in "wax+"):
            os.makedirs(os.path.dirname(d) or ".", exist_ok=True)
        file = d
    return E["orig"]["open"](file, mode, *a, **k)


def _copia(fn):
    def f(src, dst, *a, **k):
        return fn(_r(src), _r(dst), *a, **k)
    return f


def _pandas(nombre):
    def f(path, *a, **k):
        import pandas as pd
        orig = E["orig"]["pd_" + nombre]
        if not isinstance(path, (str, os.PathLike)) or E["enproceso"]:
            return orig(path, *a, **k)
        dest = rutas.redirigir(os.fspath(path))
        if os.path.exists(dest):
            return orig(dest, *a, **k)
        dd = lector.buscar_demo_data(os.fspath(path))
        if dd:
            return orig(dd, *a, **k) if dd.lower().endswith(("." + nombre.replace("read_", ""),)) else \
                lector.leer_archivo(lector.spark_activa(), dd).toPandas()
        cols = lector.columnas_sitio(lector.sitio(2)) or ["id", "valor", "fecha"]
        c, _sp, filas = datos.datos_py(cols)
        lector._anotar(E["job"], os.fspath(path), "sintetica", c, E["filas"])
        return pd.DataFrame(filas, columns=c)
    return f


def aplicar():
    O = E["orig"]
    O["open"] = builtins.open
    builtins.open = _open
    for n in _OS:
        if hasattr(os, n):
            O["os_" + n] = getattr(os, n)
            setattr(os, n, _envolver(getattr(os, n)))
    for n in _PATH:
        O["p_" + n] = getattr(os.path, n)
        setattr(os.path, n, _envolver(getattr(os.path, n)))
    for n in _SHUTIL:
        O["sh_" + n] = getattr(shutil, n)
        setattr(shutil, n, _envolver(getattr(shutil, n)) if n in ("rmtree",) else _copia(getattr(shutil, n)))
    try:
        import pandas as pd
        for n in ("read_csv", "read_parquet", "read_json", "read_excel"):
            if hasattr(pd, n):
                O["pd_" + n] = getattr(pd, n)
                setattr(pd, n, _pandas(n))
    except Exception:
        pass


def quitar():
    O = E["orig"]
    if "open" not in O:
        return
    builtins.open = O["open"]
    for n in _OS:
        if "os_" + n in O:
            setattr(os, n, O["os_" + n])
    for n in _PATH:
        setattr(os.path, n, O["p_" + n])
    for n in _SHUTIL:
        setattr(shutil, n, O["sh_" + n])
    try:
        import pandas as pd
        for k, v in list(O.items()):
            if k.startswith("pd_"):
                setattr(pd, k[3:], v)
    except Exception:
        pass
