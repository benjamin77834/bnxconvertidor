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
    # La pila de ciencia de datos va SIEMPRE en el cache (viaja con el env que se baja).
    base = [l for l in mp._requirements(True, False, ml_libs=list(mp._ML_PIP)).splitlines()
            if l.strip() and not l.startswith("#")]
    extra = [l for l in mp._requirements(True, True, ml_libs=list(mp._ML_PIP)).splitlines() if l.strip() and not l.startswith("#")]
    bk = _bank_requires()
    return base + STACK_BANCO + bk, extra + STACK_BANCO + bk


def _bank_requires(cache=None):
    """install_requires declarados por los sdist mex-lib* del banco (setup.py/setup.cfg),
    para bajar sus dependencias open source. Los que no declaran nada (caso actual) usan
    el stack STACK_BANCO. Ignora las que son otras mex-lib (internas)."""
    import tarfile
    whl = os.path.join(cache or cache_dir(), "bank_libs", "wheels")
    out = []
    if not os.path.isdir(whl):
        return out
    for f in sorted(os.listdir(whl)):
        if not (f.lower().startswith("mex") and f.endswith(".tar.gz")):
            continue
        try:
            with tarfile.open(os.path.join(whl, f), "r:gz") as t:
                for m in t.getmembers():
                    if m.isfile() and m.name.count("/") == 1 and m.name.endswith(("setup.py", "setup.cfg")):
                        txt = t.extractfile(m).read().decode("utf-8", "replace")
                        for blk in re.findall(r"install_requires\s*=\s*\[(.*?)\]", txt, re.S):
                            out += re.findall(r"""['"]([^'"]+)['"]""", blk)
                        blk = re.search(r"install_requires\s*=\s*\n((?:[ \t]+\S.*\n?)+)", txt)
                        if blk:
                            out += [l.strip() for l in blk.group(1).splitlines() if l.strip()]
        except (tarfile.TarError, OSError):
            continue
    return sorted({r for r in out if not r.lower().startswith(("mex-lib", "mex_lib", "lib_"))})


def _wheel_exacta(sdir, nombre, version):
    return sorted(glob.glob(os.path.join(sdir, "%s-%s-*.whl" % (nombre, version))))


def estado_banco(cache=None):
    """Librerias del banco que el generador espera (mlops_pkg): los 8 sdist mex-lib* en
    bank_libs/wheels y los modulos de path (toolbox, bnmxverse, utils) en bank_libs/pkgcode.
    'mex_lib_cs' no es un paquete: BNX lo genera como shim."""
    from src import mlops_pkg as mp
    cache = cache or cache_dir()
    whl = os.path.join(cache, "bank_libs", "wheels")
    code = os.path.join(cache, "bank_libs", "pkgcode")
    archivos = os.listdir(whl) if os.path.isdir(whl) else []
    sd_ok, sd_falta = [], []
    for pkg in sorted(set(mp._BANK_MODULE_TO_PKG.values())):
        hay = any(f.lower().startswith(pkg.lower() + "-") and f.endswith((".tar.gz", ".whl"))
                  for f in archivos)
        (sd_ok if hay else sd_falta).append(pkg)
    mods = sorted(m for m in mp._BANK_PATH_MODULES if m != "mex_lib_cs")
    pc_ok = [m for m in mods if os.path.isdir(os.path.join(code, m))
             and any(f.endswith(".py") for _r, _d, fs in os.walk(os.path.join(code, m)) for f in fs)]
    return {"sdists": sd_ok, "sdists_faltan": sd_falta,
            "pkgcode": pc_ok, "pkgcode_faltan": [m for m in mods if m not in pc_ok],
            "bytes": _dir_bytes(os.path.join(cache, "bank_libs")) if os.path.isdir(os.path.join(cache, "bank_libs")) else 0}


def _falta_deps(mensajes):
    """Entradas de 'falta' a partir de los mensajes de resolucion: nombres de paquete cuando se
    pueden extraer; si es un problema del pip (viejo/ausente) o de otra cosa, el mensaje ya
    saneado (una linea, nunca el texto de uso de pip)."""
    nombres, otros = set(), []
    for m in mensajes:
        m = limpiar_stderr_pip(m, maximo=2000)
        lista = re.match(r"sin wheel en el cache:\s*(.+)", m)
        hallados = ([x.strip() for x in lista.group(1).split(",") if x.strip()] if lista else
                    re.findall(r"(?:No matching distribution found for|requirement)\s+([A-Za-z0-9_.\-]+)", m))
        if hallados:
            nombres.update(hallados)
        else:
            otros.append(m[:220])
    out = []
    if nombres:
        out.append("dependencias open source: " + ", ".join(sorted(nombres, key=str.lower)))
    out += sorted(set(otros))
    return out


def estado_version(version, cache=None, extra=False):
    """Que hay/falta para UNA version de Python. 'ok' = todo lo bajable esta
    (PySpark+py4j+deps open source del framework; las de pasos extra solo con extra=True).
    Las mex-lib se reportan aparte (no se bajan)."""
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
        base, extra_l = _reqs_listas()
        pares = ((base, False), (extra_l, True)) if extra else ((base, False),)
        for reqs, xs in pares:
            _fs, f = mp._seleccionar_wheels(serie, reqs, extra_steps=xs, incluir_spark=False,
                                            _descargar=False, versiones=[v])
            for msg in f.values():
                deps_faltan.append(str(msg))
    except Exception as e:                                   # pip no disponible, etc.
        deps_faltan.append("no se pudo resolver: %s" % str(e)[:160])
    deps_faltan = sorted(set(deps_faltan))
    if deps_faltan:
        falta += _falta_deps(deps_faltan)
    bank = estado_banco(cache)
    bank_falta = bank["sdists_faltan"] + bank["pkgcode_faltan"]
    return {"version": v, "serie": serie, "ok": not falta, "falta": falta,
            "pyspark": bool(spark), "py4j": bool(py4j), "deps_faltan": deps_faltan,
            "bytes": _dir_bytes(sdir) if os.path.isdir(sdir) else 0,
            "bank_falta": bank_falta}


def estado(versiones=("3.8", "3.12"), extra=False):
    cache = cache_dir()
    return {"cache_dir": cache, "existe": os.path.isdir(cache),
            "legacy": os.path.isdir(legacy_dir()) and os.path.realpath(cache) != os.path.realpath(legacy_dir()),
            "usando_legacy": os.path.realpath(cache) == os.path.realpath(legacy_dir()),
            "nuevo": new_dir(),
            "banco": estado_banco(cache),
            "versiones": {v: estado_version(v, cache, extra=extra) for v in versiones}}


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
    b = est.get("banco")
    if b:
        out.append("Librerias del banco (%s): sdists mex-lib %d/%d, modulos de path %d/%d"
                   % (_mb(b["bytes"]), len(b["sdists"]), len(b["sdists"]) + len(b["sdists_faltan"]),
                      len(b["pkgcode"]), len(b["pkgcode"]) + len(b["pkgcode_faltan"])))
        out.append("   presentes: %s" % (", ".join(b["sdists"] + b["pkgcode"]) or "(ninguna)"))
        if b["sdists_faltan"] or b["pkgcode_faltan"]:
            out.append("   FALTAN:    %s" % ", ".join(b["sdists_faltan"] + b["pkgcode_faltan"]))
            out.append("   Son internas (no estan en PyPI): preparar_vendor.py --bank-libs <carpeta|zip>")
            out.append("   (copia los mex-lib*.tar.gz a bank_libs/wheels y toolbox/bnmxverse/utils a bank_libs/pkgcode)")
    return "\n".join(out)


# ------------------------------------------------------------- preparar
def hay_internet(timeout=8):
    import urllib.request
    try:
        urllib.request.urlopen("https://pypi.org/simple/pip/", timeout=timeout).close()
        return True
    except Exception:
        return False


# ------------------------------------------------------------- pip moderno
# `pip install --dry-run --report` (resolver sin instalar) existe desde pip 22.2. Con un pip
# viejo (p.ej. el de un Miniconda antiguo) pip responde "no such option" + todo su texto de
# uso, y eso acababa pegado en los avisos de la UI. pip_cmd() entrega SIEMPRE un pip que sirve
# (el del interprete, o el wheel de pip que viaja en el cache, que Python ejecuta directo:
# `python pip-X.whl/pip ...`) o lanza PipViejo con un mensaje claro de una linea.
PIP_MIN = (22, 2)
_PIP_VER = {}
_PIP_CMD = {}


class PipViejo(RuntimeError):
    """El pip del interprete no sirve (viejo o ausente) y no hay un pip moderno disponible."""


def _ver_tuple(s):
    m = re.match(r"\s*(\d+)(?:\.(\d+))?(?:\.(\d+))?", str(s or ""))
    return tuple(int(x or 0) for x in m.groups()) if m else None


def pip_version(py=None):
    """(major, minor, patch) del pip de `python -m pip`, o None si no hay pip."""
    py = py or sys.executable
    if py not in _PIP_VER:
        try:
            r = subprocess.run([py, "-m", "pip", "--version"], capture_output=True, text=True, timeout=60)
            m = re.match(r"pip (\d+(?:\.\d+)*)", (r.stdout or "").strip()) if r.returncode == 0 else None
            _PIP_VER[py] = _ver_tuple(m.group(1)) if m else None
        except Exception:
            _PIP_VER[py] = None
    return _PIP_VER[py]


def _fmt_ver(v):
    return ".".join(str(x) for x in v) if v else "?"


def _requires_python_ok(spec, pyver=None):
    """Evalua un Requires-Python simple ('>=3.10', '>=3.8,<4') contra el Python en curso."""
    pyver = tuple(pyver or sys.version_info[:2])
    ops = {">=": lambda a, b: a >= b, ">": lambda a, b: a > b, "<=": lambda a, b: a <= b,
           "<": lambda a, b: a < b, "==": lambda a, b: a[:len(b)] == b, "!=": lambda a, b: a[:len(b)] != b}
    for part in str(spec or "").split(","):
        m = re.match(r"\s*(>=|<=|==|!=|>|<)\s*(\d+(?:\.\d+)*)", part)
        if m:
            b = tuple(int(x) for x in m.group(2).split("."))
            if not ops[m.group(1)](pyver[:max(len(b), 2)], b):
                return False
    return True


def _wheel_requires_python(whl):
    try:
        with zipfile.ZipFile(whl) as z:
            for n in z.namelist():
                if n.endswith(".dist-info/METADATA"):
                    for ln in z.read(n).decode("utf-8", "replace").splitlines():
                        if ln.lower().startswith("requires-python:"):
                            return ln.split(":", 1)[1].strip()
                    break
    except (OSError, zipfile.BadZipFile, KeyError):
        pass
    return ""


def _prueba_pip(cmd):
    """Ejecuta `<cmd> --version`; devuelve la version (tupla) o None."""
    try:
        r = subprocess.run(cmd + ["--version"], capture_output=True, text=True, timeout=60)
        m = re.match(r"pip (\d+(?:\.\d+)*)", (r.stdout or "").strip()) if r.returncode == 0 else None
        return _ver_tuple(m.group(1)) if m else None
    except Exception:
        return None


def pip_wheels_cache(cache=None):
    """Wheels de pip que viajan en el cache (<cache>/*/pip-*.whl), la mas nueva primero."""
    cache = cache or cache_dir()
    ws = glob.glob(os.path.join(cache, "*", "pip-*.whl")) + glob.glob(os.path.join(cache, "*", "*", "pip-*.whl"))
    ws = [w for w in ws if re.match(r"pip-\d", os.path.basename(w))]
    return sorted(ws, key=lambda w: _ver_tuple(os.path.basename(w)[4:]) or (0,), reverse=True)


def _mensaje_pip_viejo(py, ver):
    if ver is None:
        return ("Este Python (%s) no tiene pip. Instalalo: %s -m ensurepip --upgrade" % (py, py))
    return ("El pip de este Python (%s) es muy viejo (%s < %s); actualiza: %s -m pip install --upgrade pip"
            % (py, _fmt_ver(ver), _fmt_ver(PIP_MIN), py))


def pip_cmd(py=None, cache=None, log=None, descargar=True):
    """Prefijo de comando para ejecutar un pip >= 22.2 (lista de args, sin shell):
      1. `python -m pip` si su pip ya es moderno;
      2. el wheel de pip del cache compatible con este Python (`python <whl>/pip`);
      3. <cache>/_pip_moderno (pip instalado con --target; si hay internet se crea con el pip
         viejo: `pip install --target`, que sirve en cualquier version);
      4. PipViejo con un mensaje claro. No instala nada global."""
    py = py or sys.executable
    cache = cache or cache_dir()
    clave = (py, os.path.realpath(cache))
    if clave in _PIP_CMD:
        return list(_PIP_CMD[clave])
    log = log or (lambda *_a: None)
    ver = pip_version(py)
    if ver and ver >= PIP_MIN:
        _PIP_CMD[clave] = [py, "-m", "pip"]
        return list(_PIP_CMD[clave])
    log("[pip] el pip de %s es %s (< %s): busco un pip moderno" % (py, _fmt_ver(ver) if ver else "inexistente",
                                                                   _fmt_ver(PIP_MIN)))
    for w in pip_wheels_cache(cache):
        if not _requires_python_ok(_wheel_requires_python(w)):
            continue
        cmd = [py, w + os.sep + "pip"]
        v = _prueba_pip(cmd)
        if v and v >= PIP_MIN:
            log("[pip] uso el pip %s del cache (%s)" % (_fmt_ver(v), os.path.basename(w)))
            _PIP_CMD[clave] = cmd
            return list(cmd)
    alt = os.path.join(cache, "_pip_moderno")
    cmd = [py, os.path.join(alt, "pip")]
    if os.path.isdir(os.path.join(alt, "pip")):
        v = _prueba_pip(cmd)
        if v and v >= PIP_MIN:
            _PIP_CMD[clave] = cmd
            return list(cmd)
    if descargar and ver and hay_internet(timeout=8):
        log("[pip] instalando un pip moderno en %s (no toca el pip global) ..." % alt)
        try:
            r = subprocess.run([py, "-m", "pip", "install", "--quiet", "--disable-pip-version-check",
                                "--upgrade", "--target", alt, "pip>=%s" % _fmt_ver(PIP_MIN)],
                               capture_output=True, text=True, timeout=600)
            v = _prueba_pip(cmd) if r.returncode == 0 else None
            if v and v >= PIP_MIN:
                _PIP_CMD[clave] = cmd
                return list(cmd)
            log("[pip] no pude instalarlo: " + limpiar_stderr_pip(r.stderr, ver))
        except Exception as e:
            log("[pip] no pude instalarlo: %s" % str(e)[:150])
    raise PipViejo(_mensaje_pip_viejo(py, ver))


def limpiar_stderr_pip(texto, ver=None, maximo=200):
    """UNA linea legible a partir del stderr de pip. Si es el texto de uso ('Usage:' / 'no such
    option', tipico de un pip viejo) NO se pega: se deja la linea de error y el hint de version."""
    lineas = [l.strip() for l in str(texto or "").splitlines() if l.strip()]
    if not lineas:
        return "pip fallo sin mensaje"
    uso = any(l.startswith("Usage:") or l.lower().startswith("no such option")
              or l.lower().startswith("no such command") for l in lineas)
    if uso:
        err = next((l for l in lineas if l.lower().startswith(("no such", "error:"))), "pip no entendio las opciones")
        hint = ""
        if ver is None:
            ver = pip_version()
        if ver and ver < PIP_MIN:
            hint = " (pip %s es muy viejo, se necesita >= %s: python -m pip install --upgrade pip)" % (
                _fmt_ver(ver), _fmt_ver(PIP_MIN))
        return (err.replace("ERROR: ", "") + hint)[:maximo]
    err = [l for l in lineas if "ERROR" in l]
    return (err[0] if err else lineas[-1]).replace("ERROR: ", "")[:maximo]


def _run(cmd, log, timeout):
    log("   $ " + " ".join(cmd[2:] if cmd[1:2] == ["-m"] else cmd))
    r = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
    if r.returncode != 0:
        log("   ERROR: " + (limpiar_stderr_pip(r.stderr) if (r.stderr or "").strip()
                            else "fallo (codigo %d)" % r.returncode))
    return r.returncode == 0


def cmd_pyspark_download(serie, destino):
    return pip_cmd() + ["download", "--no-deps", "--no-binary", ":all:",
                        "pyspark==%s" % SERIES[serie]["pyspark"], "-d", destino]


def cmd_pyspark_wheel(sdist, destino):
    return pip_cmd() + ["wheel", "--no-deps", sdist, "-w", destino]


def cmd_py4j(serie, destino):
    return pip_cmd() + ["download", "--no-deps", "--only-binary", ":all:",
                        "py4j==%s" % SERIES[serie]["py4j"], "-d", destino]


def preparar_version(version, log=print, cache=None, extra=False):
    """Baja/genera lo MINIMO que falte para una version de Python (extra=True agrega las
    deps de pasos extra: xgboost/scikit-learn). Idempotente."""
    from src import mlops_pkg as mp
    v = norm_version(version)
    serie = serie_de(v)
    cache = cache or cache_dir()
    sdir = os.path.join(cache, serie)
    os.makedirs(sdir, exist_ok=True)
    info = SERIES[serie]
    log("== Python %s (serie %s) ==" % (v, serie))
    try:
        pip_cmd(cache=cache, log=log)
    except PipViejo as e:
        log("ERROR: %s" % e)
        log("       Alternativa sin pip: preparar_vendor.py --desde-github --python %s" % v)
        est = estado_version(v, cache, extra=extra)
        log("Resultado Python %s: INCOMPLETO (serie %s en cache: %s)" % (v, serie, _mb(est["bytes"])))
        return est
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
    base, extra_l = _reqs_listas()
    prev = os.environ.pop("BNX_NO_DOWNLOAD", None)
    try:
        for reqs, xs in ((base, False), (extra_l, True)) if extra else ((base, False),):
            mp._seleccionar_wheels(serie, reqs, extra_steps=xs, incluir_spark=False,
                                   versiones=[v])
    finally:
        if prev is not None:
            os.environ["BNX_NO_DOWNLOAD"] = prev
    dl = os.path.join(cache, "mlops_deps", serie + "_dl")
    log("[deps] cache de dependencias: %s" % _mb(_dir_bytes(dl)) if os.path.isdir(dl) else "[deps] (nada bajado)")
    est = estado_version(v, cache, extra=extra)
    log("Resultado Python %s: %s (serie %s en cache: %s)"
        % (v, "COMPLETO" if est["ok"] else "INCOMPLETO", serie, _mb(est["bytes"])))
    for f in est["falta"]:
        log("   - falta %s" % f)
    if est["bank_falta"]:
        log("   - librerias del banco que faltan: %s. NO estan en PyPI: usa --bank-libs <carpeta|zip> "
            "(o --zip) o copialas a %s" % (", ".join(est["bank_falta"]), os.path.join(cache, "bank_libs")))
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


# ------------------------------------------------- GitHub Release (repo publico)
GH_REPO = "benjamin77834/bnxconvertidor"
GH_TAG = os.environ.get("BNX_VENDOR_TAG") or "vendor-linux-v2"   # incluye la pila de ciencia de datos
GH_VERSIONES = ("3.8", "3.12")          # assets publicados (sin librerias del banco)
def _gh_url(tag, nombre):
    return "https://github.com/%s/releases/download/%s/%s" % (GH_REPO, tag, nombre)
def _http_get(url, destino=None, log=print, timeout=60):
    """GET sin token (repo publico). Con destino escribe a disco en streaming y devuelve
    el sha256; sin destino devuelve los bytes."""
    import hashlib
    import urllib.request
    req = urllib.request.Request(url, headers={"User-Agent": "bnxconvertidor"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        if destino is None:
            return r.read()
        h, hecho, total = hashlib.sha256(), 0, int(r.headers.get("Content-Length") or 0)
        marca = 0
        with open(destino, "wb") as out:
            while True:
                chunk = r.read(1 << 20)
                if not chunk:
                    break
                out.write(chunk)
                h.update(chunk)
                hecho += len(chunk)
                if hecho - marca >= 50 << 20:
                    marca = hecho
                    log("   ... %s%s" % (_mb(hecho), " de " + _mb(total) if total else ""))
        return h.hexdigest()
def desde_github(version, tag=GH_TAG, log=print, cache=None):
    """Baja bnx_vendor_linux_py<v>.zip del Release publico, verifica su sha256 contra
    SHA256SUMS e importa con importar_zip (anti path-traversal). True si quedo importado.
    No trae las librerias del banco (usa --bank-libs)."""
    import tempfile
    v = norm_version(version)
    if v not in GH_VERSIONES:
        log("[github] el Release solo publica Python %s; para %s uso pip." % (" y ".join(GH_VERSIONES), v))
        return False
    nombre = "bnx_vendor_linux_py%s.zip" % v
    cache = cache or cache_dir()
    os.makedirs(cache, exist_ok=True)
    try:
        log("[github] SHA256SUMS de %s (%s) ..." % (tag, GH_REPO))
        sums = _http_get(_gh_url(tag, "SHA256SUMS")).decode("utf-8", "replace")
        esperado = None
        for ln in sums.splitlines():
            partes = ln.split()
            if len(partes) >= 2 and partes[-1].lstrip("*") == nombre:
                esperado = partes[0].lower()
        if not esperado:
            log("[github] SHA256SUMS no lista %s" % nombre)
            return False
        fd, tmp = tempfile.mkstemp(prefix="bnx_gh_", suffix=".zip", dir=cache)
        os.close(fd)
        try:
            log("[github] bajando %s ..." % nombre)
            real = _http_get(_gh_url(tag, nombre), tmp, log)
            if real != esperado:
                log("[github] ERROR: sha256 no coincide (esperado %s..., real %s...). No se importa."
                    % (esperado[:12], real[:12]))
                return False
            log("[github] sha256 OK (%s...)" % real[:12])
            importar_zip(tmp, log=log, cache=cache)
            return True
        finally:
            try:
                os.remove(tmp)
            except OSError:
                pass
    except ValueError as e:
        log("[github] ERROR al importar: %s" % e)
    except Exception as e:  # red, proxy, 404, etc.
        motivo = getattr(e, "reason", None) or e
        log("[github] no pude conectar a github.com: %s; descarga el ZIP en otra maquina "
            "(%s) y usa preparar_vendor.py --zip <archivo>. Si hay proxy corporativo define "
            "HTTPS_PROXY/HTTP_PROXY." % (str(motivo)[:150], _gh_url(tag, nombre)))
    return False
# ----------------------------------------------------- minimo indispensable / podar
def minimo(versiones, extra=False):
    """Conjunto MINIMO de archivos del cache para generar paquetes (ligero y completo, con
    PySpark) de esas versiones de Python en Linux x86_64: exactamente las wheels que pip
    resuelve (--dry-run --report, cp exacto) para los requisitos base (+ extra si extra=True)
    + PySpark/py4j de la serie + el stack/dependencias del banco.
    Siempre se conserva TODO bank_libs (sdists mex-lib y pkgcode).
    Devuelve (set de rutas reales, {version: error}). No baja nada."""
    from src import mlops_pkg as mp
    prev = os.environ.get("BNX_NO_DOWNLOAD")
    os.environ["BNX_NO_DOWNLOAD"] = "1"
    keep, faltan = set(), {}
    try:
        mp._seleccion_cache.clear()
        base, extra_l = _reqs_listas()
        for v in [norm_version(x) for x in versiones]:
            serie = serie_de(v)
            pares = ((base, False), (extra_l, True)) if extra else ((base, False),)
            for reqs, xs in pares:
                fs, f = mp._seleccionar_wheels(serie, reqs, extra_steps=xs, incluir_spark=True,
                                               _descargar=False, versiones=[v])
                keep.update(os.path.realpath(x) for x in fs)
                for ver, msg in f.items():
                    faltan[ver] = str(msg)
            info = SERIES[serie]
            sdir = os.path.join(cache_dir(), serie)
            for n in ("pyspark", "py4j"):
                w = _wheel_exacta(sdir, n, info[n])
                if not w:
                    faltan.setdefault(v, "falta %s==%s" % (n, info[n]))
                keep.update(os.path.realpath(x) for x in w)
    finally:
        if prev is None:
            os.environ.pop("BNX_NO_DOWNLOAD", None)
        else:
            os.environ["BNX_NO_DOWNLOAD"] = prev
    return keep, faltan


def sobrantes(versiones, extra=False, cache=None):
    """Archivos del cache (.whl / .tar.gz / .zip) fuera del minimo. Nunca incluye nada de
    bank_libs que sea sdist/pkgcode. Devuelve (lista de (ruta, bytes), faltan)."""
    cache = os.path.realpath(cache or cache_dir())
    keep, faltan = minimo(versiones, extra)
    banco = os.path.join(cache, "bank_libs")
    out = []
    for r, ds, fs in os.walk(cache):
        ds[:] = [d for d in ds if d != "__pycache__"]
        for f in fs:
            if not f.endswith((".whl", ".tar.gz", ".zip")):
                continue
            full = os.path.join(r, f)
            real = os.path.realpath(full)
            if real in keep:
                continue
            if full.startswith(banco + os.sep) and (f.endswith(".tar.gz") or
                                                    os.path.relpath(full, banco).startswith("pkgcode")):
                continue                      # sdists del banco y pkgcode: intocables
            out.append((full, os.path.getsize(full)))
    return sorted(out), faltan


def podar(versiones, extra=False, aplicar=False, confirmar=None, log=print, cache=None):
    """Elimina del cache todo lo que no esta en el minimo para `versiones`.
    aplicar=False: solo muestra (dry-run). confirmar: callable() -> bool para pedir
    confirmacion antes de borrar. Devuelve (archivos_borrados, bytes_liberados);
    si la resolucion tiene faltantes NO borra (el minimo estaria incompleto)."""
    cache = os.path.realpath(cache or cache_dir())
    lista, faltan = sobrantes(versiones, extra, cache)
    if faltan:
        log("ERROR: no puedo calcular el minimo: al cache le falta algo para %s. No se borra nada."
            % "; ".join("%s: %s" % (k, v[:120]) for k, v in sorted(faltan.items())))
        log("       Corre primero: preparar_vendor.py %s" % " ".join("--python " + v for v in versiones))
        return 0, 0
    por_dir = {}
    for f, n in lista:
        top = os.path.relpath(f, cache).split(os.sep)
        clave = os.sep.join(top[:2]) if top[0] == "mlops_deps" else top[0]
        por_dir.setdefault(clave, []).append((os.path.relpath(f, cache), n))
    total = sum(n for _f, n in lista)
    log("Se pueden quitar %d archivos, %s (minimo para Python %s%s):"
        % (len(lista), _mb(total), ", ".join(versiones), " + extra" if extra else ""))
    for d in sorted(por_dir):
        log("  %-28s %4d archivos  %s" % (d, len(por_dir[d]), _mb(sum(n for _f, n in por_dir[d]))))
        for rel, n in sorted(por_dir[d]):
            log("      - %s (%s)" % (rel, _mb(n)))
    if not lista:
        log("El cache ya es el minimo.")
        return 0, 0
    if not aplicar:
        log("(dry-run: no se borro nada; usa --podar --si para aplicar)")
        return 0, 0
    if confirmar is not None and not confirmar():
        log("Cancelado: no se borro nada.")
        return 0, 0
    borrados, liberado = 0, 0
    for f, n in lista:
        try:
            os.remove(f)
            borrados += 1
            liberado += n
        except OSError as e:
            log("   no pude borrar %s: %s" % (f, e))
    for r, ds, fs in os.walk(cache, topdown=False):      # carpetas que quedaron vacias
        if r != cache and not os.listdir(r):
            try:
                os.rmdir(r)
            except OSError:
                pass
    log("OK: %d archivos borrados, %s liberados." % (borrados, _mb(liberado)))
    return borrados, liberado


# ------------------------------------------------------------ librerias del banco
BANK_PATH_DIRS = ("toolbox", "bnmxverse", "utils")


def importar_bank_libs(origen, log=print, cache=None):
    """Importa las librerias internas del banco desde una carpeta o ZIP:
      - mex-lib*.tar.gz / .whl            -> bank_libs/wheels/
      - carpetas toolbox/ bnmxverse/ utils/ (donde esten, o dentro de pkgcode/)
                                          -> bank_libs/pkgcode/<modulo>/
    Devuelve (sdists copiados, modulos copiados)."""
    import shutil
    import tempfile
    cache = os.path.abspath(cache or cache_dir())
    origen = os.path.abspath(os.path.expanduser(origen))
    tmp = None
    if os.path.isfile(origen) and zipfile.is_zipfile(origen):
        tmp = tempfile.mkdtemp(prefix="bnx_bank_")
        with zipfile.ZipFile(origen) as z:
            for n in z.namelist():
                partes = n.replace("\\", "/").split("/")
                if ".." in partes or n.startswith("/") or os.path.isabs(n):
                    raise ValueError("el ZIP tiene rutas peligrosas (%r)" % n)
            z.extractall(tmp)
        raiz = tmp
    elif os.path.isdir(origen):
        raiz = origen
    else:
        raise ValueError("no existe la carpeta o ZIP %s" % origen)
    try:
        wh = os.path.join(cache, "bank_libs", "wheels")
        pc = os.path.join(cache, "bank_libs", "pkgcode")
        sd, mods = [], []
        for r, ds, fs in os.walk(raiz):
            ds[:] = [d for d in ds if d not in ("__pycache__", ".git")]
            for f in fs:
                if f.lower().startswith(("mex-lib", "mex_lib")) and f.endswith((".tar.gz", ".whl")):
                    os.makedirs(wh, exist_ok=True)
                    shutil.copy2(os.path.join(r, f), os.path.join(wh, f))
                    sd.append(f)
            for d in list(ds):
                if d in BANK_PATH_DIRS and any(x.endswith(".py") for _r, _d, xs in
                                               os.walk(os.path.join(r, d)) for x in xs):
                    dest = os.path.join(pc, d)
                    shutil.copytree(os.path.join(r, d), dest, dirs_exist_ok=True,
                                    ignore=shutil.ignore_patterns("__pycache__", "*.pyc", ".DS_Store"))
                    mods.append(d)
                    ds.remove(d)
    finally:
        if tmp:
            shutil.rmtree(tmp, ignore_errors=True)
    log("OK: librerias del banco importadas: %d sdist/wheel (%s), %d modulo(s) de path (%s)"
        % (len(sd), ", ".join(sorted(sd)) or "-", len(mods), ", ".join(sorted(mods)) or "-"))
    return sd, mods
