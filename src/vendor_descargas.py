# -*- coding: utf-8 -*-
"""
vendor_descargas.py - Archivos del vendor para DESCARGAR desde la pagina del portal.

1) Generacion (idempotente) a partir del cache de vendor, en <cache>/_descargas/ (o BNX_DESCARGAS_DIR):
     bnxconvertidor-empresav5_<commit>.zip   codigo del portal (git archive HEAD)
     banco.zip                               librerias INTERNAS del banco (solo con casilla + clave)
     ciencia-<plat>-py<X>.zip, pyspark-py<X>.zip   mismo formato que los assets del release vendor-v3
     vendor-manifest.json, SHA256SUMS
   Reusa vendor_modular (empaquetar_zip, wheels_pyspark, ...) y vendor_banco.construir_banco.
2) Control de acceso: localhost siempre; clientes remotos SOLO si el usuario compartio (clave aleatoria
   guardada hasheada con sal, expiracion, IPs/CIDR opcionales, limite de intentos fallidos).
Compatible con Python 3.8.
"""
import datetime
import hashlib
import hmac
import ipaddress
import json
import os
import re
import secrets
import shutil
import subprocess
import tempfile
import threading
import time
import zipfile
from src import vendor_cache as vc
from src import vendor_modular as vm

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PREFIJO_CODIGO = "bnxconvertidor-empresav5"
CONFIG = "_descargas.json"
INDICE = "_indice.json"
DIAS_DEFAULT = 7
MAX_FALLOS = 5            # intentos de clave fallidos por IP ...
VENTANA_S = 60            # ... por minuto -> 429
FORMATO = 1
# Lista blanca de nombres servibles (ademas deben figurar en el indice generado).
PATRONES = (
    re.compile(r"^%s_[0-9A-Za-z.\-]{1,40}\.zip$" % PREFIJO_CODIGO),
    re.compile(r"^banco\.zip$"),
    re.compile(r"^ciencia-(linux|windows|macos)-py3\.(11|14)\.zip$"),
    re.compile(r"^pyspark-py3\.(11|14)\.zip$"),
    re.compile(r"^vendor-manifest\.json$"),
    re.compile(r"^SHA256SUMS$"),
)
EXCLUIR_DIRS = {".git", ".venv", "node_modules", "output", "abinitio", "cobol", "mlops22", "__pycache__", ".kiro"}
LOCALES = ("127.0.0.1", "::1", "::ffff:127.0.0.1", "localhost")


def descargas_dir(cache=None):
    d = os.environ.get("BNX_DESCARGAS_DIR")
    return os.path.abspath(d) if d else os.path.join(cache or vc.cache_dir(), "_descargas")


def nombre_permitido(nombre):
    n = str(nombre or "")
    if not n or n != os.path.basename(n) or "/" in n or "\\" in n or ".." in n or "\x00" in n:
        return False
    return any(p.match(n) for p in PATRONES)


def es_local(ip):
    return str(ip or "") in LOCALES


# ------------------------------------------------------------------ configuracion de compartir
_LOCK = threading.Lock()
_FALLOS = {}


def _cfg_path(outdir=None):
    return os.path.join(outdir or descargas_dir(), CONFIG)


def _leer_cfg(outdir=None):
    try:
        with open(_cfg_path(outdir), encoding="utf-8") as fh:
            c = json.load(fh)
        return c if isinstance(c, dict) else {}
    except (OSError, ValueError):
        return {}


def _guardar_cfg(cfg, outdir=None):
    outdir = outdir or descargas_dir()
    os.makedirs(outdir, exist_ok=True)
    tmp = _cfg_path(outdir) + ".tmp"
    fd = os.open(tmp, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    with os.fdopen(fd, "w", encoding="utf-8") as fh:
        json.dump(cfg, fh, indent=2)
    os.replace(tmp, _cfg_path(outdir))


def _hash(sal, clave):
    return hashlib.sha256((sal + clave).encode("utf-8")).hexdigest()


def _parse_ips(ips):
    """Lista de IPs/CIDR validas (str) desde lista o texto 'a, b c'. ValueError si alguna no es valida."""
    if isinstance(ips, str):
        ips = [x for x in re.split(r"[\s,;]+", ips) if x]
    out = []
    for x in ips or []:
        out.append(str(ipaddress.ip_network(str(x).strip(), strict=False)))
    return out


def compartir(dias=DIAS_DEFAULT, ips=None, incluir_banco=False, outdir=None):
    """Activa las descargas en red con una CLAVE nueva (se devuelve UNA vez; en disco solo hash+sal)."""
    dias = float(dias)
    if not 0 < dias <= 365:
        raise ValueError("dias debe estar entre 0 y 365")
    clave = secrets.token_urlsafe(16)
    sal = secrets.token_hex(16)
    ahora = time.time()
    with _LOCK:
        _guardar_cfg({"activo": True, "sal": sal, "hash": _hash(sal, clave), "creada": ahora,
                      "expira": ahora + dias * 86400, "ips": _parse_ips(ips),
                      "incluir_banco": bool(incluir_banco)}, outdir)
        _FALLOS.clear()
    return clave


def configurar(ips=None, incluir_banco=None, dias=None, outdir=None):
    """Cambia IPs / incluir banco / expiracion sin cambiar la clave (solo si ya se esta compartiendo)."""
    with _LOCK:
        cfg = _leer_cfg(outdir)
        if not cfg.get("activo"):
            raise ValueError("las descargas en red no estan activadas")
        if ips is not None:
            cfg["ips"] = _parse_ips(ips)
        if incluir_banco is not None:
            cfg["incluir_banco"] = bool(incluir_banco)
        if dias is not None:
            d = float(dias)
            if not 0 < d <= 365:
                raise ValueError("dias debe estar entre 0 y 365")
            cfg["expira"] = time.time() + d * 86400
        _guardar_cfg(cfg, outdir)


def revocar(outdir=None):
    with _LOCK:
        _guardar_cfg({"activo": False, "incluir_banco": False}, outdir)
        _FALLOS.clear()


def estado_compartir(outdir=None, ahora=None):
    cfg = _leer_cfg(outdir)
    ahora = ahora or time.time()
    activo = bool(cfg.get("activo")) and bool(cfg.get("hash"))
    expirada = activo and ahora >= float(cfg.get("expira") or 0)
    return {"activo": activo and not expirada, "expirada": bool(expirada),
            "expira": cfg.get("expira") if activo else None,
            "expira_en_s": max(0, int(float(cfg.get("expira") or 0) - ahora)) if activo else 0,
            "ips": cfg.get("ips") or [], "incluir_banco": bool(cfg.get("incluir_banco")) and activo and not expirada}


def banco_habilitado(outdir=None):
    return estado_compartir(outdir)["incluir_banco"]


def _limitado(ip, ahora):
    f = [t for t in _FALLOS.get(ip, []) if ahora - t < VENTANA_S]
    _FALLOS[ip] = f
    return len(f) >= MAX_FALLOS


def autorizar(ip, clave, outdir=None, ahora=None):
    """(status_http, motivo). localhost siempre 200; remoto requiere compartir activo y vigente, IP
    permitida (si hay lista) y clave correcta (hmac.compare_digest). Fallos de clave: 5/min por IP -> 429."""
    if es_local(ip):
        return 200, "local"
    ahora = ahora or time.time()
    cfg = _leer_cfg(outdir)
    if not cfg.get("activo") or not cfg.get("hash"):
        return 403, "desactivado"
    if ahora >= float(cfg.get("expira") or 0):
        return 403, "expirada"
    if cfg.get("ips"):
        try:
            a = ipaddress.ip_address(str(ip).split("%")[0])
            if a.version == 6 and a.ipv4_mapped:
                a = a.ipv4_mapped
            if not any(a in ipaddress.ip_network(n, strict=False) for n in cfg["ips"]):
                return 403, "ip_no_permitida"
        except ValueError:
            return 403, "ip_no_permitida"
    with _LOCK:
        if _limitado(ip, ahora):
            return 429, "demasiados_intentos"
        if not clave:
            return 403, "clave_requerida"
        if not hmac.compare_digest(_hash(cfg.get("sal", ""), str(clave)), str(cfg["hash"])):
            _FALLOS.setdefault(ip, []).append(ahora)
            return 403, "clave_incorrecta"
        _FALLOS.pop(ip, None)
    return 200, "ok"


# ------------------------------------------------------------------ generacion
def commit_corto(root=ROOT):
    try:
        r = subprocess.run(["git", "-C", root, "rev-parse", "--short", "HEAD"], capture_output=True,
                           text=True, timeout=30)
        c = r.stdout.strip()
        return c if r.returncode == 0 and re.fullmatch(r"[0-9a-f]{7,40}", c) else None
    except (OSError, subprocess.SubprocessError):
        return None


def _zip_codigo(destino, commit, root=ROOT, log=print):
    pref = PREFIJO_CODIGO + "/"
    if commit:
        r = subprocess.run(["git", "-C", root, "archive", "--format=zip", "--prefix=" + pref, "-o", destino, "HEAD"],
                           capture_output=True, text=True, timeout=600)
        if r.returncode == 0:
            log("[codigo] git archive HEAD (%s)" % commit)
            return
        log("[codigo] AVISO: git archive fallo (%s); empaqueto el arbol" % r.stderr.strip()[:120])
    with zipfile.ZipFile(destino, "w", zipfile.ZIP_DEFLATED, allowZip64=True) as z:
        for r_, ds, fs in os.walk(root):
            ds[:] = sorted(d for d in ds if d not in EXCLUIR_DIRS)
            for f in sorted(fs):
                if f.endswith((".pyc", ".pyo", ".zip")) or f == ".DS_Store" or f.startswith(".env"):
                    continue
                full = os.path.join(r_, f)
                if os.path.islink(full):
                    continue
                z.write(full, pref + os.path.relpath(full, root).replace(os.sep, "/"))
    log("[codigo] arbol del repo (sin git)")


def wheels_ciencia(cache, v, plat):
    """Wheels de la pieza 'ciencia' (layout nuevo; el viejo solo para linux, filtrado por compatibilidad)."""
    ws = vm._wheels(vm.dir_pieza(cache, "ciencia", v, plat))
    if ws:
        return ws
    if plat == "linux":
        d = os.path.join(cache, "mlops_deps", vc.serie_de(v) + "_ciencia")
        return [f for f in vm._wheels(d) if vm.wheel_compatible(f, v, plat)
                and not os.path.basename(f).lower().startswith("pip-")]
    return []


def _fuentes(cache):
    """[(tipo, py, plat, [wheels])] de lo que hay en el cache."""
    out = []
    for v in vm.PY_VERSIONES:
        if vm._pyspark_completo(cache, v):
            out.append(("pyspark", v, "any", vm.wheels_pyspark(cache, v)))
        for plat in vm.PLATAFORMAS:
            ws = wheels_ciencia(cache, v, plat)
            if ws:
                out.append(("ciencia", v, plat, ws))
    return out


def _banco_wheels(cache):
    wh = os.path.join(vc.banco_dir(cache), "wheels")
    if not os.path.isdir(wh):
        return []
    return sorted(os.path.join(wh, f) for f in os.listdir(wh)
                  if f.lower().startswith(("mex", "bnx_bank_pkgcode")) and f.endswith(".whl"))


def huella(cache, commit):
    h = hashlib.sha256()
    h.update(json.dumps([FORMATO, commit], sort_keys=True).encode())
    lista = [(t, v, p, ws) for t, v, p, ws in _fuentes(cache)] + [("banco", "", "", _banco_wheels(cache))]
    for t, v, p, ws in lista:
        h.update(("|%s|%s|%s" % (t, v, p)).encode())
        for w in ws:
            st = os.stat(w)
            h.update(("%s:%d:%d;" % (os.path.basename(w), st.st_size, int(st.st_mtime))).encode())
    return h.hexdigest()


def leer_indice(outdir=None):
    try:
        with open(os.path.join(outdir or descargas_dir(), INDICE), encoding="utf-8") as fh:
            return json.load(fh)
    except (OSError, ValueError):
        return None


def _indice_vigente(idx, outdir):
    for a in (idx or {}).get("archivos", []):
        f = os.path.join(outdir, a["nombre"])
        if not os.path.isfile(f) or os.path.getsize(f) != a["bytes"]:
            return False
    return bool(idx and idx.get("archivos"))


def estado_archivos(cache=None, outdir=None):
    """Indice generado + si esta desactualizado respecto del cache/commit actual."""
    cache = cache or vc.cache_dir()
    outdir = outdir or descargas_dir(cache)
    idx = leer_indice(outdir)
    if not idx:
        return {"generado": None, "archivos": [], "desactualizado": True}
    try:
        al_dia = idx.get("huella") == huella(cache, commit_corto()) and _indice_vigente(idx, outdir)
    except OSError:
        al_dia = False
    return {"generado": idx.get("generado"), "commit": idx.get("commit"), "archivos": idx["archivos"],
            "desactualizado": not al_dia}


def _desc(tipo, v, plat):
    if tipo == "codigo":
        return "Codigo del portal BNX (sin .venv ni datos). Descomprimelo y corre setup."
    if tipo == "banco":
        return "Librerias INTERNAS del banco (mex-lib + modulos). No reenviar fuera del banco."
    if tipo == "pyspark":
        return "PySpark + py4j para Python %s (para el entorno 'con PySpark')." % v
    if tipo == "ciencia":
        return "Pila de ciencia de datos para %s / Python %s (xgboost, scikit-learn, pandas...)." % (plat, v)
    if tipo == "manifest":
        return "Manifiesto con tamanos y sha256 de las piezas."
    return "Sumas SHA256 para verificar los archivos descargados."


def preparar(cache=None, outdir=None, log=print, forzar=False):
    """Genera (o regenera si cambio el cache/commit) los archivos de descarga. Devuelve el indice."""
    cache = os.path.abspath(cache or vc.cache_dir())
    outdir = outdir or descargas_dir(cache)
    os.makedirs(outdir, exist_ok=True)
    commit = commit_corto()
    hu = huella(cache, commit)
    idx = leer_indice(outdir)
    if not forzar and idx and idx.get("huella") == hu and _indice_vigente(idx, outdir):
        log("[descargas] ya estan al dia (sin cambios en el cache ni en el commit %s)." % (commit or "-"))
        return idx
    tmpd = os.path.join(outdir, ".tmp")
    shutil.rmtree(tmpd, ignore_errors=True)
    os.makedirs(tmpd)
    archivos, piezas, sums = [], [], []

    def registrar(nombre, ruta, tipo, v=None, plat=None, sha=None, interno=False, minimo=False):
        os.replace(ruta, os.path.join(outdir, nombre))
        f = os.path.join(outdir, nombre)
        sha = sha or vm._sha256(f)
        archivos.append({"nombre": nombre, "tipo": tipo, "para": _desc(tipo, v, plat), "python": v,
                         "plataforma": plat, "bytes": os.path.getsize(f), "sha256": sha,
                         "interno": interno, "set_linux_311": minimo})
        return sha

    try:
        cn = "%s_%s.zip" % (PREFIJO_CODIGO, commit or "sin-git")
        _zip_codigo(os.path.join(tmpd, cn), commit, log=log)
        sums.append((registrar(cn, os.path.join(tmpd, cn), "codigo", minimo=True), cn))
        for tipo, v, plat, ws in _fuentes(cache):
            arch = vm.archivo_pieza(tipo, v, plat)
            if tipo == "pyspark":
                ent = [("pyspark/%s/%s" % (vc.serie_de(v), os.path.basename(w)), w) for w in ws]
            else:
                ent = [("ciencia/%s/%s/%s" % (v, plat, os.path.basename(w)), w) for w in ws]
            b, sha = vm.empaquetar_zip(os.path.join(tmpd, arch), ent)
            piezas.append({"nombre": tipo, "python": v, "plataforma": plat, "archivo": arch, "bytes": b,
                           "sha256": sha, "contenido": vm.contenido_wheels(ws), "huecos": [],
                           "glibc_max": vm.glibc_max(ws)})
            registrar(arch, os.path.join(tmpd, arch), tipo, v, plat, sha=sha,
                      minimo=(v == "3.11" and (tipo == "pyspark" or plat == "linux")))
            sums.append((sha, arch))
            log("[%s py%s %s] %.1f MB" % (tipo, v, plat, b / 1048576.0))
        if _banco_wheels(cache):
            bdir = os.path.join(tmpd, "banco")
            r = vm.construir_banco(cache, bdir, log=log)
            sha = registrar("banco.zip", os.path.join(bdir, "banco.zip"), "banco", sha=r["sha256"],
                            interno=True, minimo=True)
            sums.append((sha, "banco.zip"))
        else:
            log("[banco] AVISO: no hay wheels del banco en el cache; no se genera banco.zip")
        man = {"formato": 3, "tag": vm.GH_TAG_MODULAR, "local": True,
               "generado": datetime.datetime.now().isoformat(timespec="seconds"),
               "nota": "Piezas del cache del portal (sin banco).", "piezas": piezas}
        vm.escribir_manifiesto_release(tmpd, man)      # vendor-manifest.json + SHA256SUMS (piezas)
        extra = ["%s  %s" % (s, n) for s, n in sums if n not in {p["archivo"] for p in piezas}]
        with open(os.path.join(tmpd, vm.SUMS), "a", encoding="utf-8") as fh:
            fh.write("\n".join(extra) + ("\n" if extra else ""))
        registrar(vm.MANIFEST, os.path.join(tmpd, vm.MANIFEST), "manifest", minimo=True)
        registrar(vm.SUMS, os.path.join(tmpd, vm.SUMS), "sums", minimo=True)
    finally:
        shutil.rmtree(tmpd, ignore_errors=True)
    nuevos = {a["nombre"] for a in archivos}
    for f in os.listdir(outdir):                     # restos de generaciones anteriores
        if f not in nuevos and nombre_permitido(f) and os.path.isfile(os.path.join(outdir, f)):
            os.remove(os.path.join(outdir, f))
    idx = {"formato": FORMATO, "huella": hu, "commit": commit,
           "generado": datetime.datetime.now().isoformat(timespec="seconds"), "archivos": archivos}
    with open(os.path.join(outdir, INDICE), "w", encoding="utf-8") as fh:
        json.dump(idx, fh, indent=2)
    log("[descargas] listo: %d archivos, %.1f MB en %s" % (len(archivos), sum(a["bytes"] for a in archivos) / 1048576.0, outdir))
    return idx


def ruta_servible(nombre, outdir=None):
    """Ruta real del archivo si el nombre pasa la lista blanca, esta en el indice y es un archivo regular
    dentro del directorio de exportacion; si no, None. Segundo valor: entrada del indice."""
    outdir = os.path.realpath(outdir or descargas_dir())
    if not nombre_permitido(nombre):
        return None, None
    ent = next((a for a in (leer_indice(outdir) or {}).get("archivos", []) if a["nombre"] == nombre), None)
    if not ent:
        return None, None
    f = os.path.join(outdir, nombre)
    if os.path.islink(f) or not os.path.isfile(f) or os.path.dirname(os.path.realpath(f)) != outdir:
        return None, None
    return f, ent
