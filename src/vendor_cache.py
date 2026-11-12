# -*- coding: utf-8 -*-
"""
vendor_cache.py — Ubicacion UNICA del cache de vendor (wheels de PySpark, deps
open source y mex-lib del banco) + estado, preparacion (bajar/generar) e importacion.

El cache vive DENTRO del ambiente virtual:  <ROOT>/.venv/bnx_vendor_cache/
Orden de resolucion de cache_dir():
  1. env BNX_VENDOR_CACHE (si esta definida)
  2. <venv activo>/bnx_vendor_cache, si el venv (sys.prefix) esta dentro del proyecto
  3. <ROOT>/.venv/bnx_vendor_cache
  Compatibilidad: si existe el viejo <ROOT>/.bnx_vendor_cache y NO el nuevo, se usa
  el viejo y se avisa que se puede migrar (mv).
"""
import glob
import json
import os
import re
import subprocess
import sys
import zipfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LEGACY_NAME = ".bnx_vendor_cache"
ZIP_PREFIX = LEGACY_NAME + "/"          # prefijo de las entradas de los ZIPs de vendor
_AVISADO = set()

# Version de Python del servidor Linux -> serie de wheels + versiones de PySpark/py4j.
SERIES = {
    "py38-311": {"pyspark": "3.5.6", "py4j": "0.10.9.7"},
    "py312plus": {"pyspark": "4.0.0", "py4j": "0.10.9.9"},
}
STACK_BANCO = ["cytoolz", "toolz", "Unidecode", "cloudpickle", "joblib"]


def serie_de(version):
    """'3.8' -> 'py38-311'; '3.12' -> 'py312plus'."""
    v = str(version).lower().replace("py", "").strip()
    m = re.fullmatch(r"3\.(\d{1,2})", v)
    if not m:
        raise ValueError("Version de Python no valida: %r (usa 3.8 o 3.12)" % version)
    return "py312plus" if int(m.group(1)) >= 12 else "py38-311"


def norm_version(version):
    v = str(version).lower().replace("py", "").strip()
    serie_de(v)
    return v


def venv_base():
    """Carpeta del venv que aloja el cache."""
    pref = os.path.realpath(sys.prefix)
    if sys.prefix != getattr(sys, "base_prefix", sys.prefix):
        raiz = os.path.realpath(ROOT)
        if pref == raiz or pref.startswith(raiz + os.sep):
            return sys.prefix
    return os.path.join(ROOT, ".venv")


def legacy_dir():
    return os.path.join(ROOT, LEGACY_NAME)


def new_dir():
    return os.path.join(venv_base(), "bnx_vendor_cache")


def cache_dir():
    env = os.environ.get("BNX_VENDOR_CACHE", "").strip()
    if env:
        return os.path.abspath(os.path.expanduser(env))
    nuevo, viejo = new_dir(), legacy_dir()
    if os.path.isdir(viejo) and not os.path.isdir(nuevo):
        if "legacy" not in _AVISADO:
            _AVISADO.add("legacy")
            sys.stderr.write("[vendor] AVISO: usando el cache viejo %s. Puedes migrarlo al venv con:\n"
                             "         mv %s %s\n" % (viejo, viejo, nuevo))
        return viejo
    return nuevo


def _mb(n):
    return "%.1f MB" % (n / 1048576.0)


def _dir_bytes(d):
    total = 0
    for r, _s, fs in os.walk(d):
        for f in fs:
            try:
                total += os.path.getsize(os.path.join(r, f))
            except OSError:
                pass
    return total


# ---------------------------------------------------------------- estado
def _reqs_listas():
    """(base, extra) de requisitos open source, igual que exportar_vendor."""
    from src import mlops_pkg as mp
    base = [l for l in mp._requirements(True, False).splitlines() if l.strip() and not l.startswith("#")]
    extra = [l for l in mp._requirements(True, True).splitlines() if l.strip() and not l.startswith("#")]
    return base + STACK_BANCO, extra + STACK_BANCO


def _wheel_exacta(sdir, nombre, version):
    return sorted(glob.glob(os.path.join(sdir, "%s-%s-*.whl" % (nombre, version))))


def estado_version(version, cache=None):
    """Que hay/falta para UNA version de Python. 'ok' = todo lo bajable esta
    (PySpark+py4j+deps open source). Las mex-lib se reportan aparte (no se bajan)."""
    from src import mlops_pkg as mp
    v = norm_version(version)
    serie = serie_de(v)
    cache = cache or cache_dir()
    sdir = os.path.join(cache, serie)
    info = SERIES[serie]
    falta = []
    spark = _wheel_exacta(sdir, "pyspark", info["pyspark"])
    py4j = _wheel_exacta(sdir, "py4j", info["py4j"])
    if not spark:
        falta.append("pyspark==%s" % info["pyspark"])
    if not py4j:
        falta.append("py4j==%s" % info["py4j"])
    deps_faltan = []
    try:
        mp._seleccion_cache.clear()
        base, extra = _reqs_listas()
        for reqs, xs in ((base, False), (extra, True)):
            _fs, f = mp._seleccionar_wheels(serie, reqs, extra_steps=xs, incluir_spark=False,
                                            _descargar=False, versiones=[v])
            for msg in f.values():
                deps_faltan.append(str(msg))
    except Exception as e:                                   # pip no disponible, etc.
        deps_faltan.append("no se pudo resolver: %s" % str(e)[:160])
    deps_faltan = sorted(set(deps_faltan))
    if deps_faltan:
        falta.append("dependencias open source (%s)" % deps_faltan[0][:100])
    whl = os.path.join(cache, "bank_libs", "wheels")
    presentes = os.listdir(whl) if os.path.isdir(whl) else []
    bank_falta = sorted(p for p in mp._BANK_PKG_VERIFIED
                        if not any(f.lower().startswith(p.lower()) for f in presentes))
    return {"version": v, "serie": serie, "ok": not falta, "falta": falta,
            "pyspark": bool(spark), "py4j": bool(py4j), "deps_faltan": deps_faltan,
            "bytes": _dir_bytes(sdir) if os.path.isdir(sdir) else 0,
            "bank_falta": bank_falta}


def estado(versiones=("3.8", "3.12")):
    cache = cache_dir()
    return {"cache_dir": cache, "existe": os.path.isdir(cache),
            "legacy": os.path.isdir(legacy_dir()) and os.path.realpath(cache) != os.path.realpath(legacy_dir()),
            "usando_legacy": os.path.realpath(cache) == os.path.realpath(legacy_dir()),
            "nuevo": new_dir(),
            "versiones": {v: estado_version(v, cache) for v in versiones}}


def formatear_estado(est):
    out = ["Cache de vendor: %s%s" % (est["cache_dir"], "" if est["existe"] else "  (no existe)")]
    if est.get("usando_legacy"):
        out.append("  AVISO: es el cache VIEJO; migra con: mv %s %s" % (legacy_dir(), est["nuevo"]))
    for v, e in est["versiones"].items():
        out.append("Python %s (%s): %s" % (v, e["serie"], "COMPLETO" if e["ok"] else "FALTA"))
        for f in e["falta"]:
            out.append("   - falta %s" % f)
        if e["bytes"]:
            out.append("   (serie %s: %s)" % (e["serie"], _mb(e["bytes"])))
        if e["bank_falta"]:
            out.append("   - mex-lib del banco (NO se bajan de PyPI): %s" % ", ".join(e["bank_falta"]))
    if any(e["bank_falta"] for e in est["versiones"].values()):
        out.append("Las mex-lib son internas: traelas con un ZIP (--zip) o copiandolas a")
        out.append("   %s" % os.path.join(est["cache_dir"], "bank_libs", "wheels"))
        out.append("   (o desde la pagina 'Librerias del banco').")
    return "\n".join(out)


# ------------------------------------------------------------- preparar
def hay_internet(timeout=8):
    import urllib.request
    try:
        urllib.request.urlopen("https://pypi.org/simple/pip/", timeout=timeout).close()
        return True
    except Exception:
        return False


def _run(cmd, log, timeout):
    log("   $ " + " ".join(cmd[2:] if cmd[1:2] == ["-m"] else cmd))
    r = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
    if r.returncode != 0:
        err = [l for l in (r.stderr or "").splitlines() if l.strip()]
        log("   ERROR: " + (err[-1] if err else "fallo (codigo %d)" % r.returncode))
    return r.returncode == 0


def cmd_pyspark_download(serie, destino):
    return [sys.executable, "-m", "pip", "download", "--no-deps", "--no-binary", ":all:",
            "pyspark==%s" % SERIES[serie]["pyspark"], "-d", destino]


def cmd_pyspark_wheel(sdist, destino):
    return [sys.executable, "-m", "pip", "wheel", "--no-deps", sdist, "-w", destino]


def cmd_py4j(serie, destino):
    return [sys.executable, "-m", "pip", "download", "--no-deps", "--only-binary", ":all:",
            "py4j==%s" % SERIES[serie]["py4j"], "-d", destino]


def preparar_version(version, log=print, cache=None):
    """Baja/genera lo que falte para una version de Python. Idempotente."""
    from src import mlops_pkg as mp
    v = norm_version(version)
    serie = serie_de(v)
    cache = cache or cache_dir()
    sdir = os.path.join(cache, serie)
    os.makedirs(sdir, exist_ok=True)
    info = SERIES[serie]
    log("== Python %s (serie %s) ==" % (v, serie))
    # (a) PySpark + py4j
    if _wheel_exacta(sdir, "py4j", info["py4j"]):
        log("[py4j] ya esta (%s)" % info["py4j"])
    else:
        log("[py4j] bajando py4j==%s ..." % info["py4j"])
        _run(cmd_py4j(serie, sdir), log, 600)
    if _wheel_exacta(sdir, "pyspark", info["pyspark"]):
        log("[pyspark] ya esta (%s)" % info["pyspark"])
    else:
        log("[pyspark] bajando sdist pyspark==%s (~300-400 MB) y construyendo la wheel (puede tardar varios minutos) ..."
            % info["pyspark"])
        if _run(cmd_pyspark_download(serie, sdir), log, 2400):
            sd = glob.glob(os.path.join(sdir, "pyspark-%s*.tar.gz" % info["pyspark"]))
            if sd and _run(cmd_pyspark_wheel(sd[0], sdir), log, 2400):
                for s in sd:
                    try:
                        os.remove(s)
                    except OSError:
                        pass
        ws = _wheel_exacta(sdir, "pyspark", info["pyspark"])
        if ws:
            log("[pyspark] OK %s (%s)" % (os.path.basename(ws[0]), _mb(os.path.getsize(ws[0]))))
    # (b) resto de dependencias open source: reutiliza la logica del generador
    # (_seleccionar_wheels baja a mlops_deps/<serie>_dl con --platform manylinux).
    log("[deps] resolviendo dependencias open source para Linux x86_64 / Python %s ..." % v)
    mp._seleccion_cache.clear()
    mp._descarga_fallida.clear()
    base, extra = _reqs_listas()
    prev = os.environ.pop("BNX_NO_DOWNLOAD", None)
    try:
        for reqs, xs in ((base, False), (extra, True)):
            mp._seleccionar_wheels(serie, reqs, extra_steps=xs, incluir_spark=False,
                                   versiones=[v])
    finally:
        if prev is not None:
            os.environ["BNX_NO_DOWNLOAD"] = prev
    dl = os.path.join(cache, "mlops_deps", serie + "_dl")
    log("[deps] cache de dependencias: %s" % _mb(_dir_bytes(dl)) if os.path.isdir(dl) else "[deps] (nada bajado)")
    est = estado_version(v, cache)
    log("Resultado Python %s: %s (serie %s en cache: %s)"
        % (v, "COMPLETO" if est["ok"] else "INCOMPLETO", serie, _mb(est["bytes"])))
    for f in est["falta"]:
        log("   - falta %s" % f)
    if est["bank_falta"]:
        log("   - mex-lib del banco: %s. NO se bajan de PyPI: importa un ZIP (--zip) "
            "o copialas a %s" % (", ".join(est["bank_falta"]), os.path.join(cache, "bank_libs", "wheels")))
    return est


# --------------------------------------------------------------- importar
def importar_zip(zpath, log=print, cache=None):
    """Extrae las entradas '.bnx_vendor_cache/<rel>' a cache_dir()/<rel>.
    Devuelve (archivos, bytes). Lanza ValueError ante rutas peligrosas."""
    cache = os.path.abspath(cache or cache_dir())
    if not os.path.isfile(zpath):
        raise ValueError("no existe el archivo %s" % zpath)
    with zipfile.ZipFile(zpath, "r") as z:
        infos = z.infolist()
        bad, plan = [], []
        for info in infos:
            n = info.filename
            if n == "importar_vendor.py":          # script que agrega export_vendor_zip
                continue
            partes = n.split("/")
            if (not n.startswith(ZIP_PREFIX) or ".." in partes or "\\" in n
                    or n.startswith("/") or os.path.isabs(n)):
                bad.append(n)
                continue
            rel = n[len(ZIP_PREFIX):]
            if not rel or info.is_dir():
                continue
            dest = os.path.abspath(os.path.join(cache, rel))
            if os.path.commonpath([cache, dest]) != cache:
                bad.append(n)
                continue
            plan.append((info, dest))
        if bad:
            raise ValueError("el ZIP tiene rutas inesperadas (%d, p.ej. %r). Abortando sin extraer."
                             % (len(bad), bad[0]))
        n_files, total = 0, 0
        for info, dest in plan:
            os.makedirs(os.path.dirname(dest), exist_ok=True)
            with z.open(info) as src, open(dest, "wb") as out:
                while True:
                    chunk = src.read(1 << 20)
                    if not chunk:
                        break
                    out.write(chunk)
                    total += len(chunk)
            n_files += 1
    log("OK: importado en %s (%d archivos, %s)" % (cache, n_files, _mb(total)))
    return n_files, total
