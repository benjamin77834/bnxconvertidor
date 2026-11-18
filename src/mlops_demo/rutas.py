# -*- coding: utf-8 -*-
"""Redireccion de rutas del cluster (hdfs://, s3://, /data/...) a <paquete>/demo_out/."""
import hashlib
import json
import os
import re

from .estado import E

ESQUEMAS = ("hdfs", "viewfs", "maprfs", "s3", "s3a", "s3n", "abfs", "abfss", "wasb", "wasbs",
            "adl", "gs", "oss")
PREFIJOS = ("/data", "/user", "/tmp/hive", "/apps", "/warehouse", "/hive", "/hdfs",
            "/mnt/data", "/opt/cloudera")
_ESQ_RE = re.compile(r"^([A-Za-z][A-Za-z0-9+.\-]+):(//|/)")


def _esquema(s):
    m = _ESQ_RE.match(s)
    return m.group(1).lower() if m else None


def es_ruta_cluster(p, estricto=True):
    """True si p apunta al cluster. estricto=True: solo esquemas de cluster, prefijos conocidos y
    raices de los settings (para open/makedirs). estricto=False: ademas cualquier ruta absoluta
    cuya carpeta de primer nivel no existe en esta maquina (lecturas/escrituras de Spark)."""
    if not isinstance(p, str) or not p:
        return False
    esq = _esquema(p)
    if esq is not None:
        return esq in ESQUEMAS
    if not p.startswith("/"):
        return False
    q = p.rstrip("/") or "/"
    out = E.get("out")
    if out and (q + "/").startswith(out.replace("\\", "/").rstrip("/") + "/"):
        return False
    for pre in PREFIJOS + tuple(E.get("raices") or ()):
        pre = pre.rstrip("/")
        if q == pre or q.startswith(pre + "/"):
            return True
    if not estricto:
        primero = "/" + q.strip("/").split("/")[0]
        return not os.path.exists(primero)
    return False


def _sanear(seg):
    return re.sub(r"[^\w.=\-]", "_", seg)


def ruta_demo(p):
    """Ruta local dentro de demo_out para una ruta del cluster."""
    s = str(p).strip()
    esq = _esquema(s)
    if esq:
        resto = s[len(esq) + 1:]
        autoridad, partes = "", resto.split("/")
        if resto.startswith("//"):
            autoridad, _, resto = resto[2:].partition("/")
            partes = resto.split("/")
        if autoridad and esq in ("s3", "s3a", "s3n", "gs", "oss", "abfs", "abfss", "wasb", "wasbs"):
            partes = [autoridad.split("@")[0]] + partes     # bucket / contenedor; hdfs: se descarta host:puerto
        segs = [_sanear(x) for x in partes if x and x not in (".", "..")]
    else:
        segs = [_sanear(x) for x in s.replace("\\", "/").split("/") if x and x not in (".", "..")]
    base = E.get("out") or os.path.join(os.getcwd(), "demo_out")
    ruta = os.path.join(base, *segs) if segs else base
    if len(ruta) > 190:   # limite de ruta de Windows (260) con margen para los part-files
        h = hashlib.sha1("/".join(segs).encode("utf-8")).hexdigest()[:8]
        ruta = os.path.join(base, "h" + h, *segs[-3:])
    return ruta


def ruta_hive(db, tabla):
    return os.path.join(E["out"], "hive", _sanear(db or "default"), _sanear(tabla))


def redirigir(p, estricto=False):
    """Ruta redirigida si es del cluster; si no, la misma."""
    if isinstance(p, os.PathLike):
        p = os.fspath(p)
    if isinstance(p, str) and es_ruta_cluster(p, estricto):
        return ruta_demo(p)
    return p


def raices_de_settings(settings_dir):
    """Rutas absolutas del cluster que aparecen en los JSON de settings (general_root, ...)."""
    out = set()
    if not settings_dir or not os.path.isdir(settings_dir):
        return []

    def _walk(o):
        if isinstance(o, dict):
            for v in o.values():
                _walk(v)
        elif isinstance(o, list):
            for v in o:
                _walk(v)
        elif isinstance(o, str) and o.startswith("/") and " " not in o and len(o) > 3:
            partes = o.strip("/").split("/")
            if partes and not os.path.exists("/" + partes[0]):
                out.add("/" + "/".join(partes[:2]))
    for r, _d, fs in os.walk(settings_dir):
        for f in fs:
            if f.endswith(".json"):
                try:
                    with open(os.path.join(r, f), encoding="utf-8") as fh:
                        _walk(json.load(fh))
                except (OSError, ValueError):
                    pass
    return sorted(out)
