# -*- coding: utf-8 -*-
"""
vendor_modular.py — Vendor MODULAR: 3 piezas independientes, por version de Python y plataforma.

  pyspark  (por version; independiente del SO)   <cache>/pyspark/<serie>/       pyspark + py4j
  ciencia  (por version Y plataforma)            <cache>/ciencia/<py>/<plat>/   base + pila de ciencia de datos
  banco    (interna, NO publica)                 <cache>/banco/                 mex-lib (sdist) + pkgcode

Plataformas: linux (x86_64 manylinux, servidor del banco), windows (win_amd64),
macos (arm64) y macos-intel (x86_64, experimental).

Compatibilidad: el layout VIEJO (py38-311, py312plus, mlops_deps, bank_libs) se sigue leyendo
(mlops_pkg junta ambos); `migrar()` lo reorganiza al nuevo sin perder datos.
Las piezas publicas se publican como ZIP con entradas '.bnx_vendor_cache/<ruta>' (el mismo
formato que importa vendor_cache.importar_zip) y un 'vendor-manifest.json'.
"""
import datetime
import glob
import hashlib
import json
import os
import platform
import re
import shutil
import subprocess
import sys
import tempfile
import zipfile

from src import vendor_cache as vc

MANIFEST = "vendor-manifest.json"
SUMS = "SHA256SUMS"
PY_VERSIONES = vc.VERSIONES_DEFAULT          # 3.11 y 3.14 (3.8/3.12 = legado, sin assets)
BOOTSTRAP_NECESARIO = ("setuptools", "wheel")   # setup.sh hace 'pip install --no-build-isolation -e .'
GH_TAG_MODULAR = os.environ.get("BNX_VENDOR_TAG_MODULAR") or "vendor-v3"

# Servidor del banco: RHEL 8 x86_64 (glibc 2.28). Solo wheels manylinux con glibc <= 2.28; NUNCA
# manylinux_2_31/2_34+ ni musllinux (pip con --platform explicito solo acepta estas etiquetas).
GLIBC_MAX_LINUX = (2, 28)
_LINUX_TAGS = ["manylinux_2_28_x86_64", "manylinux_2_27_x86_64", "manylinux_2_24_x86_64",
               "manylinux_2_17_x86_64", "manylinux2014_x86_64", "manylinux2010_x86_64", "manylinux1_x86_64"]
_GLIBC_LEGADO = {"manylinux1": (2, 5), "manylinux2010": (2, 12), "manylinux2014": (2, 17)}
def glibc_minima_wheel(nombre):
    """glibc minima que pide una wheel Linux (la menor de sus etiquetas manylinux; una wheel
    'manylinux_2_17...manylinux_2_28' corre con glibc 2.17). None si no es manylinux (any/win/mac);
    (99, 0) si es musllinux o linux_x86_64 (no portable: no sirve en RHEL 8)."""
    base = os.path.basename(nombre)
    if not base.endswith(".whl"):
        return None
    plat = base[:-4].split("-")[-1]
    mins = []
    for t in plat.split("."):
        m = re.match(r"manylinux_(\d+)_(\d+)_", t)
        if m:
            mins.append((int(m.group(1)), int(m.group(2))))
        elif t.split("_")[0] in _GLIBC_LEGADO:
            mins.append(_GLIBC_LEGADO[t.split("_")[0]])
        elif t.startswith(("musllinux", "linux_")):
            mins.append((99, 0))
    return min(mins) if mins else None
def glibc_max(archivos):
    """'2.28' = la glibc mas alta que exige alguna wheel del conjunto (None si ninguna es Linux)."""
    gs = [g for g in (glibc_minima_wheel(f) for f in archivos) if g]
    return ("%d.%d" % max(gs)) if gs else None
def wheels_glibc_incompatibles(archivos, maximo=GLIBC_MAX_LINUX):
    return sorted(os.path.basename(f) for f in archivos
                  if (glibc_minima_wheel(f) or (0, 0)) > tuple(maximo))
PLATAFORMAS = {
    "linux": {"etiqueta": "Linux x86_64", "tags": _LINUX_TAGS,
              "env": {"sys_platform": "linux", "platform_system": "Linux", "os_name": "posix",
                      "platform_machine": "x86_64"}},
    "windows": {"etiqueta": "Windows x64", "tags": ["win_amd64"],
                "env": {"sys_platform": "win32", "platform_system": "Windows", "os_name": "nt",
                        "platform_machine": "AMD64"}},
    "macos": {"etiqueta": "macOS Apple Silicon", "tags": ["macosx_14_0_arm64"],
              "env": {"sys_platform": "darwin", "platform_system": "Darwin", "os_name": "posix",
                      "platform_machine": "arm64"}},
    "macos-intel": {"etiqueta": "macOS Intel (experimental)", "tags": ["macosx_14_0_x86_64"],
                    "env": {"sys_platform": "darwin", "platform_system": "Darwin", "os_name": "posix",
                            "platform_machine": "x86_64"}},
}
# Tamanos conocidos (MB) de las piezas de vendor-v3 para mostrar en la UI aunque no haya red ni
# manifiesto; el manifiesto (local o del origen) manda cuando existe.
MB_ESTIMADO = {
    ("pyspark", "3.11", "any"): 303, ("pyspark", "3.14", "any"): 435,
    ("ciencia", "3.11", "linux"): 124, ("ciencia", "3.14", "linux"): 124,
    ("ciencia", "3.11", "windows"): 105, ("ciencia", "3.14", "windows"): 107,
    ("ciencia", "3.11", "macos"): 82, ("ciencia", "3.14", "macos"): 82,
    ("ciencia", "3.11", "macos-intel"): 87, ("ciencia", "3.14", "macos-intel"): 88,
}
class ErrorRed(RuntimeError):
    """No se pudo CONECTAR al origen (sin internet, DNS, proxy, timeout, HTTP 5xx...). Distinto de
    un 404 (el manifiesto no existe): ante esto no tiene sentido probar otros releases."""


def _log0(*_a):
    pass


# ------------------------------------------------------------------ host
def host_plataforma():
    f = os.environ.get("BNX_FORZAR_PLATAFORMA", "").strip().lower()
    if f in PLATAFORMAS:
        return f
    s, m = platform.system(), platform.machine().lower()
    if s == "Windows":
        return "windows"
    if s == "Darwin":
        return "macos" if m in ("arm64", "aarch64") else "macos-intel"
    return "linux"


def host_python():
    """Version del Python del equipo ('3.14' en bruto) y la mas cercana soportada (3.11|3.14)."""
    f = os.environ.get("BNX_FORZAR_PYTHON", "").strip()
    real = f or "%d.%d" % sys.version_info[:2]
    try:
        menor = int(real.split(".")[1])
    except (IndexError, ValueError):
        menor = 11
    return real, ("3.14" if menor >= 12 else "3.11")


def parse_plataformas(txt):
    out = []
    for p in re.split(r"[,\s]+", str(txt or "").strip().lower()):
        if not p:
            continue
        p = {"mac": "macos", "darwin": "macos", "win": "windows", "win32": "windows"}.get(p, p)
        if p not in PLATAFORMAS:
            raise ValueError("Plataforma no valida: %r (usa %s)" % (p, ",".join(PLATAFORMAS)))
        if p not in out:
            out.append(p)
    return out


def abi_de(v):
    return "cp" + str(v).replace(".", "")


def env_destino(v, plat):
    e = {"python_version": v, "python_full_version": v + ".0", "implementation_name": "cpython",
         "platform_python_implementation": "CPython", "extra": ""}
    e.update(PLATAFORMAS[plat]["env"])
    return e


def norm(n):
    return re.sub(r"[-_.]+", "-", str(n)).lower()


# ------------------------------------------------------------------ paquete logico -> distribucion
# XGBoost: la wheel normal de Linux/Windows trae CUDA (Linux: nvidia-nccl 185-308 MB + libxgboost 55-126 MB).
# 'xgboost-cpu' (mismo modulo `import xgboost`, misma API, sin nvidia-nccl) pesa ~5 MB. macOS ya es
# solo CPU: ahi sigue 'xgboost'. Con --xgboost-gpu (o BNX_XGBOOST_GPU=1) se usa 'xgboost' en todas.
DIST_POR_PLATAFORMA = {
    "xgboost": {"linux": "xgboost-cpu", "windows": "xgboost-cpu"},
}


def xgboost_gpu():
    return os.environ.get("BNX_XGBOOST_GPU", "").strip().lower() in ("1", "true", "si", "yes")


def set_xgboost_gpu(activo=True):
    if activo:
        os.environ["BNX_XGBOOST_GPU"] = "1"
    else:
        os.environ.pop("BNX_XGBOOST_GPU", None)


def nombre_logico(dist):
    """'xgboost-cpu' -> 'xgboost'; el resto igual (normalizado)."""
    n = norm(dist)
    for logico, por_plat in DIST_POR_PLATAFORMA.items():
        if n == logico or n in {norm(d) for d in por_plat.values()}:
            return logico
    return n


def dist_para(nombre, plat, gpu=None):
    """Distribucion PyPI que se instala para el paquete logico `nombre` en `plat`."""
    n = nombre_logico(nombre)
    if gpu is None:
        gpu = xgboost_gpu()
    if gpu:
        return n
    return DIST_POR_PLATAFORMA.get(n, {}).get(plat, n)


def mapear_requisito(req, plat, gpu=None):
    """Cambia el nombre del requisito ('xgboost>=1.7' -> 'xgboost-cpu>=1.7' en linux/windows);
    el resto de la linea (extras, version, marker) queda igual."""
    m = re.match(r"^(\s*)([A-Za-z0-9][A-Za-z0-9._\-]*)(.*)$", req, re.S)
    if not m:
        return req
    return m.group(1) + dist_para(m.group(2), plat, gpu) + m.group(3)


# --------------------------------------------------------------- nombres / rutas
def archivo_pieza(tipo, py=None, plat=None):
    if tipo == "pyspark":
        return "pyspark-py%s.zip" % py
    if tipo == "ciencia":
        return "ciencia-%s-py%s.zip" % (plat, py)
    if tipo == "banco":
        return "banco.zip"
    raise ValueError(tipo)


def dir_pieza(cache, tipo, py=None, plat=None):
    if tipo == "pyspark":
        return os.path.join(cache, "pyspark", vc.serie_de(py))
    if tipo == "ciencia":
        return os.path.join(cache, "ciencia", py, plat)
    return vc.banco_dir(cache)


def _wheels(d):
    return sorted(glob.glob(os.path.join(d, "*.whl"))) if os.path.isdir(d) else []


def _bytes(archivos):
    return sum(os.path.getsize(f) for f in archivos if os.path.isfile(f))


def tiene_layout_nuevo(cache):
    return any(os.path.isdir(os.path.join(cache, d)) for d in ("pyspark", "ciencia", "banco"))


def wheels_pyspark(cache, py):
    """pyspark+py4j exactos (nuevo layout o el viejo <serie>/)."""
    serie = vc.serie_de(py)
    info = vc.SERIES[serie]
    out = []
    for d in (os.path.join(cache, "pyspark", serie), os.path.join(cache, serie)):
        out += vc._wheel_exacta(d, "pyspark", info["pyspark"]) + vc._wheel_exacta(d, "py4j", info["py4j"])
    vistos, res = set(), []
    for f in out:
        if os.path.basename(f) not in vistos:
            vistos.add(os.path.basename(f))
            res.append(f)
    return res


def _pyspark_completo(cache, py):
    ws = {os.path.basename(f).split("-")[0].lower() for f in wheels_pyspark(cache, py)}
    return {"pyspark", "py4j"} <= ws


def _ciencia_legacy_dirs(cache, py):
    serie = vc.serie_de(py)
    return [os.path.join(cache, "mlops_deps", serie + s) for s in ("_ciencia", "_dl", "_extra", "")]


def ciencia_presente(cache, py, plat):
    """(presente, layout, bytes). El layout viejo solo vale para linux (eran wheels manylinux)."""
    d = dir_pieza(cache, "ciencia", py, plat)
    ws = _wheels(d)
    if ws:
        return True, "nuevo", _bytes(ws)
    if plat == "linux":
        dc = os.path.join(cache, "mlops_deps", vc.serie_de(py) + "_ciencia")
        if _wheels(dc):
            return True, "viejo", vc._dir_bytes(dc)
    return False, "-", 0


def contenido_wheels(archivos):
    out = []
    for f in sorted(archivos, key=lambda x: os.path.basename(x).lower()):
        p = os.path.basename(f)[:-4].split("-")
        if len(p) >= 2:
            out.append({"paquete": p[0].replace("_", "-"), "version": p[1], "archivo": os.path.basename(f),
                        "bytes": os.path.getsize(f) if os.path.isfile(f) else 0})
    return out


# ------------------------------------------------------------------ seleccion de piezas
def seleccion(versiones, plataformas=None, con_pyspark=True, con_ciencia=True,
              para_linux=True, solo_host=False):
    """Lista de piezas (tipo, py, plat) que hay que tener. Por defecto: ciencia del host +
    ciencia linux (si para_linux y no solo_host) + pyspark (si con_pyspark)."""
    if plataformas:
        plats = list(plataformas)
    else:
        plats = [host_plataforma()]
        if para_linux and not solo_host and "linux" not in plats:
            plats.append("linux")
    out = []
    for v in versiones:
        if con_pyspark:
            out.append(("pyspark", v, "any"))
        if con_ciencia:
            out += [("ciencia", v, p) for p in plats]
    return out


def estado_piezas(cache, piezas, manifiesto=None):
    """Por pieza: presente/falta con MB. 'bytes_descarga' sale del manifiesto si se conoce."""
    man = manifiesto or leer_manifiesto_local(cache) or {}
    por_clave = {(p["nombre"], p.get("python"), p.get("plataforma")): p for p in man.get("piezas", [])}
    out = []
    for tipo, v, plat in piezas:
        if tipo == "pyspark":
            ok = _pyspark_completo(cache, v)
            b = _bytes(wheels_pyspark(cache, v)) if ok else 0
            layout = "nuevo" if _wheels(os.path.join(cache, "pyspark", vc.serie_de(v))) else ("viejo" if ok else "-")
        else:
            ok, layout, b = ciencia_presente(cache, v, plat)
        m = por_clave.get((tipo, v, plat))
        est = (m or {}).get("bytes") or (MB_ESTIMADO.get((tipo, v, plat), 0) * 1048576) or None
        item = {"pieza": tipo, "python": v, "plataforma": plat, "archivo": archivo_pieza(tipo, v, plat),
                "presente": ok, "layout": layout, "bytes": b, "bytes_descarga": est,
                "glibc_max": (m or {}).get("glibc_max")}
        if ok and plat in ("linux", "any"):
            ws = wheels_pyspark(cache, v) if tipo == "pyspark" else _wheels(dir_pieza(cache, "ciencia", v, plat))
            item["glibc_max"] = glibc_max(ws) or item["glibc_max"]
            item["glibc_incompatibles"] = wheels_glibc_incompatibles(ws)
        out.append(item)
    return out


def formatear_piezas(est):
    out = ["Piezas del vendor (por version de Python y plataforma):"]
    for e in est:
        mb = e["bytes"] if e["presente"] else (e["bytes_descarga"] or 0)
        out.append("  %-8s py%-5s %-12s %-9s %s%.0f MB" % (
            e["pieza"], e["python"], e["plataforma"],
            ("OK (%s)" % e["layout"]) if e["presente"] else "FALTA",
            "" if e["presente"] else "~", mb / 1048576.0))
    return "\n".join(out)


# ------------------------------------------------------------------ metadatos / cierre
def _packaging():
    try:
        from packaging.markers import Marker
        from packaging.requirements import Requirement
        from packaging.specifiers import SpecifierSet
        from packaging.version import Version
    except ImportError:
        from pip._vendor.packaging.markers import Marker
        from pip._vendor.packaging.requirements import Requirement
        from pip._vendor.packaging.specifiers import SpecifierSet
        from pip._vendor.packaging.version import Version
    return Marker, Requirement, SpecifierSet, Version


def _requires_dist(whl):
    try:
        with zipfile.ZipFile(whl) as z:
            for n in z.namelist():
                if n.endswith(".dist-info/METADATA") and n.count("/") == 1:
                    txt = z.read(n).decode("utf-8", "replace")
                    return [ln.split(":", 1)[1].strip() for ln in txt.splitlines()
                            if ln.startswith("Requires-Dist:")]
    except (OSError, zipfile.BadZipFile):
        pass
    return []


def _nv(whl):
    p = os.path.basename(whl)[:-4].split("-")
    return norm(p[0]), p[1] if len(p) > 1 else "0"


def calcular_cierre(archivos, tops, v, plat):
    """Cierre de dependencias EVALUADO PARA EL DESTINO (no para el host: pip download evalua los
    markers del host y se salta p.ej. exceptiongroup/tomli en py3.8 o colorama en Windows).
    Devuelve (usados:set de rutas, faltan:{nombre: requisito})."""
    Marker, Requirement, SpecifierSet, Version = _packaging()
    env = env_destino(v, plat)
    por_nombre = {}
    for f in archivos:
        n, ver = _nv(f)
        por_nombre.setdefault(n, []).append((ver, f))

    def elegir(n, spec):
        cands = por_nombre.get(n, [])
        buenos = []
        for pre in (False, True):        # como pip: pre-releases solo si no hay una version final valida
            for ver, f in cands:
                try:
                    if not spec or spec.contains(Version(ver), prereleases=pre or None):
                        buenos.append((Version(ver), f))
                except Exception:
                    buenos.append((Version("0"), f))
            if buenos:
                break
        return max(buenos)[1] if buenos else None

    usados, faltan, vistos = set(), {}, set()
    cola = []
    for t in tops:
        try:
            r = Requirement(t)
        except Exception:
            continue
        cola.append(r)
    while cola:
        r = cola.pop()
        n = norm(r.name)
        if r.marker is not None and not r.marker.evaluate(env):
            continue
        f = elegir(n, r.specifier)
        if f is None:
            faltan[n] = str(r).split(";")[0].strip()
            continue
        if f in vistos:
            continue
        vistos.add(f)
        usados.add(f)
        for ln in _requires_dist(f):
            try:
                rr = Requirement(ln)
            except Exception:
                continue
            if rr.marker is not None and not rr.marker.evaluate(env):
                continue
            cola.append(rr)
    return usados, faltan


def wheel_compatible(nombre, v, plat):
    """True si la wheel `nombre` instala en CPython `v` sobre `plat` (sin pip: para hosts con un
    pip viejo, p.ej. Python 3.8 + pip 21, que no entiende --dry-run --report)."""
    base = os.path.basename(nombre)
    if not base.endswith(".whl"):
        return False
    p = base[:-4].split("-")
    if len(p) < 5:
        return False
    pys, abis, plats = p[-3].split("."), p[-2].split("."), p[-1].split(".")
    cp = abi_de(v)
    menor = int(v.split(".")[1])
    py_ok = any(t in ("py3", cp, "py3%d" % menor) or (t.startswith("cp3") and abis == ["abi3"]
                and t[3:].isdigit() and int(t[3:]) <= menor) for t in pys)
    abi_ok = any(a in (cp, "none", "abi3") for a in abis)
    validas = set(PLATAFORMAS[plat]["tags"]) | {"any"}
    plat_ok = any(t in validas for t in plats)
    return py_ok and abi_ok and plat_ok
def resolver_interno(archivos, reqs, v, plat):
    """Resolucion offline SIN pip: filtra las wheels compatibles con el destino y calcula el cierre de
    dependencias con calcular_cierre. Devuelve (usados:set de rutas, faltan:{nombre: requisito})."""
    comp = [f for f in archivos if wheel_compatible(f, v, plat)]
    return calcular_cierre(comp, [mapear_requisito(r, plat) for r in reqs], v, plat)
# ------------------------------------------------------------------ pip download por plataforma
def _flags_destino(v, plat):
    fl = ["--only-binary=:all:", "--python-version", v, "--implementation", "cp",
          "--abi", abi_de(v), "--abi", "abi3", "--abi", "none"]
    for t in PLATAFORMAS[plat]["tags"]:
        fl += ["--platform", t]
    return fl + ["--platform", "any"]


def _pip_download(reqs, v, plat, dest, cons=None, deps=True, timeout=1500):
    os.makedirs(dest, exist_ok=True)
    cmd = vc.pip_cmd() + ["download", "--quiet", "--disable-pip-version-check", "--retries", "2",
                          "--timeout", "30"] + _flags_destino(v, plat) + ["-d", dest]
    if cons:
        cmd += ["-c", cons]
    if not deps:
        cmd.append("--no-deps")
    r = subprocess.run(cmd + list(reqs), capture_output=True, text=True, timeout=timeout)
    return r.returncode == 0, (r.stderr or "")


def _nombre_fallo(err):
    for pat in (r"No matching distribution found for ([A-Za-z0-9_.\-]+)",
                r"Could not find a version that satisfies the requirement ([A-Za-z0-9_.\-]+)"):
        m = re.search(pat, err or "")
        if m:
            return m.group(1)
    return None


def _nombre_req(req):
    return norm(re.split(r"[<>=!~ ;\[(]", req, maxsplit=1)[0])


def descargar_con_huecos(tops, v, plat, dest, pins=None, log=_log0):
    """pip download (deps) de los requisitos; si alguno no tiene wheel para (v, plat) lo registra
    como hueco y sigue con el resto. `pins` {nombre: version}: versiones de Linux que se intentan
    respetar (que todas las plataformas lleven las mismas versiones); si no existe wheel, se suelta."""
    tops, huecos = list(tops), []
    # los pins vienen de Linux (xgboost-cpu): en cada plataforma se fijan con SU distribucion
    pins = {norm(dist_para(k, plat)): ver for k, ver in dict(pins or {}).items()}
    with tempfile.TemporaryDirectory(prefix="bnx_cons_") as tmp:
        for _ in range(14):
            cons = None
            if pins:
                cons = os.path.join(tmp, "c.txt")
                with open(cons, "w") as fh:
                    fh.write("\n".join("%s==%s" % kv for kv in sorted(pins.items())) + "\n")
            ok, err = _pip_download(tops, v, plat, dest, cons)
            if ok:
                return huecos
            n = _nombre_fallo(err)
            k = norm(n) if n else None
            if k and k in pins:
                huecos.append("%s: la version %s de Linux no tiene wheel para %s; se usa otra"
                              % (k, pins.pop(k), plat))
                continue
            if k and any(_nombre_req(t) == k for t in tops):
                huecos.append("%s: sin wheel para %s / Python %s" % (k, plat, v))
                tops = [t for t in tops if _nombre_req(t) != k]
                if not tops:
                    return huecos
                continue
            if pins:
                log("   [%s py%s] no se pueden fijar las versiones de Linux (%s); se resuelven sin fijar"
                    % (plat, v, vc.limpiar_stderr_pip(err, maximo=90)))
                pins.clear()
                continue
            break
        # ultimo recurso: de uno en uno (cada requisito con sus deps)
        for t in list(tops):
            ok, err = _pip_download([t], v, plat, dest)
            if not ok:
                huecos.append("%s: %s" % (_nombre_req(t), vc.limpiar_stderr_pip(err, maximo=120)))
    return huecos


def construir_ciencia(cache, v, plat, log=print, destino=None, pins_linux=None, desde_pool=None):
    """Arma (en <cache>/ciencia/<v>/<plat>/) la pieza 'ciencia': base + pila de ciencia de datos,
    SOLO con las wheels que resuelve (v, plat) y con el cierre de dependencias calculado para el
    destino. Devuelve {'dir','huecos','bytes','wheels'}."""
    from src import mlops_pkg as mp
    destino = destino or dir_pieza(cache, "ciencia", v, plat)
    base, _extra = vc._reqs_listas()
    tops = mp._reqs_para(v, base, False, plataforma=plat) + list(BOOTSTRAP_NECESARIO)
    tmp = destino + ".tmp"
    shutil.rmtree(tmp, ignore_errors=True)
    os.makedirs(tmp)
    huecos = []
    try:
        copiados = 0
        if plat == "linux":
            # el cache viejo / ya existente manda: mismas versiones que resuelven los paquetes de hoy
            prev = os.environ.get("BNX_NO_DOWNLOAD")
            os.environ["BNX_NO_DOWNLOAD"] = "1"
            try:
                mp._seleccion_cache.clear()
                fs, f = mp._seleccionar_wheels(vc.serie_de(v), base, extra_steps=True, incluir_spark=False,
                                               _descargar=False, versiones=[v], plataforma="linux")
            finally:
                if prev is None:
                    os.environ.pop("BNX_NO_DOWNLOAD", None)
                else:
                    os.environ["BNX_NO_DOWNLOAD"] = prev
            if not f:                      # solo si el cache cubre TODO; si no, se resuelve limpio con pip
                for x in fs:
                    if _nv(x)[0] not in ("pip",):
                        _enlazar(x, os.path.join(tmp, os.path.basename(x)))
                        copiados += 1
            if f:
                log("   [linux py%s] el cache no cubre todo (%s): completo con pip" % (v, "; ".join(map(str, f.values()))[:120]))
        if plat != "linux" or not copiados:
            huecos += descargar_con_huecos(tops, v, plat, tmp, pins=pins_linux, log=log)
        # cierre calculado para el destino; bajar lo que falte (markers que pip evalua mal)
        for _ in range(6):
            usados, faltan = calcular_cierre(_wheels(tmp), tops, v, plat)
            if not faltan:
                break
            ya = {h.split(":")[0] for h in huecos}
            pend = [r for n, r in faltan.items() if n not in ya]
            if not pend:
                break
            for r in pend:
                ok, err = _pip_download([r], v, plat, tmp, deps=False)
                if not ok:
                    huecos.append("%s: sin wheel para %s / Python %s" % (_nombre_req(r), plat, v))
        usados, faltan = calcular_cierre(_wheels(tmp), tops, v, plat)
        for n, r in faltan.items():
            if not any(h.startswith(n + ":") for h in huecos):
                huecos.append("%s: sin wheel para %s / Python %s" % (n, plat, v))
        for f in _wheels(tmp):                 # fuera lo que no es del cierre (otras versiones, duplicados)
            if f not in usados:
                os.remove(f)
        shutil.rmtree(destino, ignore_errors=True)
        os.makedirs(os.path.dirname(destino), exist_ok=True)
        os.rename(tmp, destino)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    ws = _wheels(destino)
    if pins_linux and plat != "linux":
        lin = {nombre_logico(k): ver for k, ver in pins_linux.items()}
        for w in ws:        # version distinta a la de Linux: se avisa (no es un hueco, pero cambia el entorno)
            n, ver = _nv(w)
            nl = nombre_logico(n)
            if nl in lin and lin[nl] != ver:
                huecos.append("%s: Linux usa %s, %s usa %s (sin wheel de %s para %s / Python %s)"
                              % (n, lin[nl], plat, ver, lin[nl], plat, v))
    return {"dir": destino, "huecos": sorted(set(huecos)), "bytes": _bytes(ws), "wheels": ws}


def _enlazar(src, dst):
    """Hardlink (sin duplicar disco) y si no se puede, copia."""
    try:
        os.link(os.path.realpath(src), dst)
    except OSError:
        shutil.copy2(src, dst)


# ------------------------------------------------------------------ pyspark (slim experimental)
SLIM_PATRONES = (
    r"^pyspark/jars/rocksdbjni-[^/]*\.jar$",          # solo estado de streaming/UI store en RocksDB
    r"^pyspark/jars/mesos-[^/]*\.jar$",               # Mesos (deprecado)
    r"^pyspark/jars/kubernetes-[^/]*\.jar$",          # cliente de Kubernetes
    r"^pyspark/jars/connect-repl/",                   # REPL de Spark Connect
    r"^pyspark/jars/scala-compiler-[^/]*\.jar$",      # solo spark-shell/REPL
    r"^pyspark/(examples|data)/",                     # ejemplos y datos de muestra
)


def slim_wheel(src, dst, patrones=SLIM_PATRONES):
    """Copia el wheel de pyspark SIN los archivos que `patrones` nombran (EXPERIMENTAL; el wheel
    original no se toca). Devuelve (bytes_quitados_comprimidos, [rutas quitadas])."""
    pats = [re.compile(p) for p in patrones]
    quitados, ahorro = [], 0
    with zipfile.ZipFile(src) as zi, zipfile.ZipFile(dst, "w", zipfile.ZIP_DEFLATED) as zo:
        for info in zi.infolist():
            if any(p.search(info.filename) for p in pats):
                quitados.append(info.filename)
                ahorro += info.compress_size
                continue
            if info.filename.endswith(".dist-info/RECORD"):
                continue
            zo.writestr(info, zi.read(info.filename), compress_type=info.compress_type)
        rec = next(i for i in zi.infolist() if i.filename.endswith(".dist-info/RECORD"))
        qs = set(quitados)
        lineas = [ln for ln in zi.read(rec.filename).decode("utf-8").splitlines() if ln.split(",")[0] not in qs]
        zo.writestr(rec, "\n".join(lineas) + "\n")
    return ahorro, quitados


def probar_pyspark_local(wheel, py, workdir, log=print, timeout=900):
    """Extrae wheel(s) pyspark(+py4j) a workdir y corre un job local[*] (groupBy + escribir/leer
    parquet) con el Python `py`. Devuelve (ok, salida). Sirve para validar el wheel slim."""
    target = os.path.join(workdir, "site")
    shutil.rmtree(target, ignore_errors=True)
    os.makedirs(target)
    for w in [wheel] + [x for x in glob.glob(os.path.join(os.path.dirname(wheel), "py4j-*.whl"))][:1]:
        with zipfile.ZipFile(w) as z:
            z.extractall(target)
    for sub in ("bin", "sbin"):      # el ZIP no conserva +x (setup.sh del paquete tambien lo restaura)
        for f in glob.glob(os.path.join(target, "pyspark", sub, "*")):
            os.chmod(f, 0o755)
    prueba = (
        "import os,sys,tempfile\n"
        "from pyspark.sql import SparkSession, functions as F\n"
        "s=SparkSession.builder.master('local[2]').config('spark.ui.enabled','false')"
        ".config('spark.sql.shuffle.partitions','2').getOrCreate()\n"
        "df=s.range(1000).withColumn('g',F.col('id')%3)\n"
        "r={x['g']:x['c'] for x in df.groupBy('g').agg(F.count('*').alias('c')).collect()}\n"
        "p=os.path.join(tempfile.mkdtemp(),'t.parquet')\n"
        "df.write.parquet(p)\n"
        "n=s.read.parquet(p).filter('id>=500').count()\n"
        "print('RESULT',sorted(r.items()),n,s.version)\n"
        "s.stop()\n")
    env = dict(os.environ, PYTHONPATH=target, SPARK_HOME=os.path.join(target, "pyspark"),
               PYSPARK_PYTHON=py, SPARK_LOCAL_IP="127.0.0.1")
    env.pop("PYTHONHOME", None)
    r = subprocess.run([py, "-c", prueba], capture_output=True, text=True, env=env, timeout=timeout, cwd=workdir)
    ok = r.returncode == 0 and "RESULT [(0, 334), (1, 333), (2, 333)] 500" in r.stdout
    return ok, (r.stdout + r.stderr)[-600:]


# ------------------------------------------------------------------ empaquetado de piezas
def _sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for ch in iter(lambda: fh.read(1 << 20), b""):
            h.update(ch)
    return h.hexdigest()


def empaquetar_zip(salida, entradas):
    """ZIP (STORED: las wheels ya van comprimidas) con entradas [(arcname_relativo, ruta)] bajo
    '.bnx_vendor_cache/'. Devuelve (bytes, sha256)."""
    os.makedirs(os.path.dirname(os.path.abspath(salida)), exist_ok=True)
    with zipfile.ZipFile(salida, "w", zipfile.ZIP_STORED, allowZip64=True) as z:
        for arc, ruta in entradas:
            z.write(ruta, vc.ZIP_PREFIX + arc.replace(os.sep, "/"))
    return os.path.getsize(salida), _sha256(salida)


def construir_release(cache, outdir, versiones=PY_VERSIONES, plataformas=("linux", "windows", "macos"),
                      pyspark_slim=False, log=print):
    """Arma TODAS las piezas publicas (SIN banco) a partir del cache (viejo o nuevo) + pip.
    Escribe los ZIP, vendor-manifest.json y SHA256SUMS en outdir. Devuelve el manifiesto."""
    os.makedirs(outdir, exist_ok=True)
    piezas = []
    for v in versiones:
        # --- pyspark (independiente del SO)
        ws = wheels_pyspark(cache, v)
        if ws:
            entradas, extra = [], {}
            serie = vc.serie_de(v)
            if pyspark_slim:
                tmp = tempfile.mkdtemp(prefix="bnx_slim_")
                for w in ws:
                    if os.path.basename(w).startswith("pyspark-"):
                        dst = os.path.join(tmp, os.path.basename(w))
                        ahorro, q = slim_wheel(w, dst)
                        entradas.append(("pyspark/%s/%s" % (serie, os.path.basename(w)), dst))
                        extra = {"slim": True, "quitados": len(q), "ahorro_bytes": ahorro}
                    else:
                        entradas.append(("pyspark/%s/%s" % (serie, os.path.basename(w)), w))
            else:
                entradas = [("pyspark/%s/%s" % (serie, os.path.basename(w)), w) for w in ws]
            arch = archivo_pieza("pyspark", v)
            b, sha = empaquetar_zip(os.path.join(outdir, arch), entradas)
            piezas.append(dict({"nombre": "pyspark", "python": v, "plataforma": "any", "archivo": arch,
                                "bytes": b, "sha256": sha,
                                "contenido": contenido_wheels([e[1] for e in entradas]), "huecos": [],
                                "glibc_max": glibc_max([e[1] for e in entradas])}, **extra))
            log("[pyspark py%s] %.1f MB" % (v, b / 1048576.0))
        else:
            log("[pyspark py%s] AVISO: no hay wheels de PySpark en el cache" % v)
        # --- ciencia
        pins = None
        orden = ["linux"] + [p for p in plataformas if p != "linux"]
        for plat in orden:
            if plat not in plataformas and plat != "linux":
                continue
            log("[ciencia %s py%s] armando ..." % (plat, v))
            res = construir_ciencia(cache, v, plat, log=log, pins_linux=pins)
            if plat == "linux":
                pins = dict(_nv(w) for w in res["wheels"])
            if plat not in plataformas:
                continue
            arch = archivo_pieza("ciencia", v, plat)
            entradas = [("ciencia/%s/%s/%s" % (v, plat, os.path.basename(w)), w) for w in res["wheels"]]
            b, sha = empaquetar_zip(os.path.join(outdir, arch), entradas)
            piezas.append({"nombre": "ciencia", "python": v, "plataforma": plat, "archivo": arch,
                           "bytes": b, "sha256": sha, "contenido": contenido_wheels(res["wheels"]),
                           "huecos": res["huecos"], "glibc_max": glibc_max(res["wheels"])})
            log("[ciencia %s py%s] %.1f MB, %d wheels, %d huecos" % (plat, v, b / 1048576.0, len(res["wheels"]), len(res["huecos"])))
    man = {"formato": 3, "tag": GH_TAG_MODULAR, "generado": datetime.datetime.now().isoformat(timespec="seconds"),
           "nota": "Piezas publicas (sin librerias del banco).", "piezas": piezas}
    escribir_manifiesto_release(outdir, man)
    return man


def escribir_manifiesto_release(outdir, man):
    with open(os.path.join(outdir, MANIFEST), "w", encoding="utf-8") as fh:
        json.dump(man, fh, ensure_ascii=False, indent=2)
    lineas = ["%s  %s" % (p["sha256"], p["archivo"]) for p in man["piezas"]]
    lineas.append("%s  %s" % (_sha256(os.path.join(outdir, MANIFEST)), MANIFEST))
    with open(os.path.join(outdir, SUMS), "w", encoding="utf-8") as fh:
        fh.write("\n".join(lineas) + "\n")


def construir_banco(cache, outdir, log=print):
    """banco.zip interno (solo wheels). Ver vendor_banco."""
    from src import vendor_banco
    return vendor_banco.construir_banco(cache, outdir, log)


# ------------------------------------------------------------------ manifiesto local
def manifiesto_local(cache):
    """Manifiesto de lo que HAY en el cache (nuevo layout y, para linux, el viejo)."""
    piezas = []
    for v in PY_VERSIONES:
        ws = wheels_pyspark(cache, v)
        if ws:
            piezas.append({"nombre": "pyspark", "python": v, "plataforma": "any", "archivo": None,
                           "bytes": _bytes(ws), "sha256": None, "contenido": contenido_wheels(ws), "huecos": [],
                           "glibc_max": glibc_max(ws)})
        for plat in PLATAFORMAS:
            d = dir_pieza(cache, "ciencia", v, plat)
            ws = _wheels(d)
            if ws:
                piezas.append({"nombre": "ciencia", "python": v, "plataforma": plat, "archivo": None,
                               "bytes": _bytes(ws), "sha256": None, "contenido": contenido_wheels(ws), "huecos": [],
                               "glibc_max": glibc_max(ws)})
    return {"formato": 3, "generado": datetime.datetime.now().isoformat(timespec="seconds"),
            "local": True, "piezas": piezas}


def guardar_manifiesto_local(cache, man=None):
    man = man or manifiesto_local(cache)
    os.makedirs(cache, exist_ok=True)
    with open(os.path.join(cache, MANIFEST), "w", encoding="utf-8") as fh:
        json.dump(man, fh, ensure_ascii=False, indent=2)
    return man


def leer_manifiesto_local(cache):
    try:
        with open(os.path.join(cache, MANIFEST), encoding="utf-8") as fh:
            return json.load(fh)
    except (OSError, ValueError):
        return None


# ------------------------------------------------------------------ origenes (GitHub / carpeta)
class OrigenDir:
    """Carpeta local con el layout de un Release (manifiesto + ZIP + SHA256SUMS). Actua como
    GitHub en pruebas y para instalaciones internas sin internet (--desde-dir)."""
    def __init__(self, path):
        self.path = os.path.abspath(os.path.expanduser(path))
        self.nombre = self.path

    def get_bytes(self, nombre):
        with open(os.path.join(self.path, nombre), "rb") as fh:
            return fh.read()

    def get_file(self, nombre, destino, log=_log0):
        shutil.copyfile(os.path.join(self.path, nombre), destino)
        return _sha256(destino)


class OrigenGithub:
    def __init__(self, tag=None):
        self.tag = tag or GH_TAG_MODULAR
        self.nombre = "GitHub %s (%s)" % (self.tag, vc.GH_REPO)

    def get_bytes(self, nombre):
        return vc._http_get(vc._gh_url(self.tag, nombre))

    def get_file(self, nombre, destino, log=print):
        return vc._http_get(vc._gh_url(self.tag, nombre), destino, log)


def _motivo_red(e):
    r = getattr(e, "reason", None) or e
    return (str(r) or type(e).__name__)[:150]
def leer_manifiesto(origen):
    """Manifiesto del origen, verificado contra SHA256SUMS si este lo lista.
    None = el origen responde pero NO tiene manifiesto (404 / archivo ausente / JSON invalido).
    Lanza ErrorRed si no se pudo conectar (URLError, DNS, timeout, proxy, HTTP != 404)."""
    import socket
    import urllib.error
    try:
        raw = origen.get_bytes(MANIFEST)
    except urllib.error.HTTPError as e:
        if e.code == 404:
            return None
        raise ErrorRed("HTTP %s %s" % (e.code, e.reason))
    except (urllib.error.URLError, socket.timeout, ConnectionError) as e:
        raise ErrorRed(_motivo_red(e))
    except FileNotFoundError:
        return None
    except OSError as e:
        if isinstance(origen, OrigenGithub):       # getaddrinfo / SSL / reset: es de red
            raise ErrorRed(_motivo_red(e))
        return None
    try:
        man = json.loads(raw.decode("utf-8"))
    except ValueError:
        return None
    try:
        for ln in origen.get_bytes(SUMS).decode("utf-8", "replace").splitlines():
            p = ln.split()
            if len(p) >= 2 and p[-1].lstrip("*") == MANIFEST and p[0].lower() != hashlib.sha256(raw).hexdigest():
                raise ValueError("el sha256 del manifiesto no coincide con SHA256SUMS")
    except ValueError:
        raise
    except Exception:
        pass
    return man


def bajar_piezas(origen, piezas, cache, log=print):
    """Baja SOLO las piezas pedidas [(tipo, py, plat)] del origen, verifica sha256 y las importa.
    Devuelve {archivo: 'ok' | motivo}."""
    man = leer_manifiesto(origen)
    if not man:
        log("[origen] %s no tiene %s" % (origen.nombre, MANIFEST))
        return None
    idx = {(p["nombre"], p.get("python"), p.get("plataforma")): p for p in man.get("piezas", [])}
    sums = {}
    try:
        for ln in origen.get_bytes(SUMS).decode("utf-8", "replace").splitlines():
            p = ln.split()
            if len(p) >= 2:
                sums[p[-1].lstrip("*")] = p[0].lower()
    except Exception:
        pass
    res = {}
    os.makedirs(cache, exist_ok=True)
    for tipo, v, plat in piezas:
        clave = (tipo, v, "any" if tipo == "pyspark" else plat)
        arch = archivo_pieza(tipo, v, plat)
        m = idx.get(clave)
        if not m:
            res[arch] = "no esta en el manifiesto (pieza no publicada)"
            log("[%s] %s: no publicada en %s" % (tipo, arch, origen.nombre))
            continue
        for h in m.get("huecos") or []:
            log("   [hueco] %s" % h)
        esperado = (m.get("sha256") or sums.get(m["archivo"]) or "").lower()
        if not esperado:
            res[arch] = "sin sha256 en el manifiesto"
            continue
        fd, tmp = tempfile.mkstemp(prefix="bnx_pz_", suffix=".zip", dir=cache)
        os.close(fd)
        try:
            log("[%s] bajando %s (%.1f MB) ..." % (tipo, m["archivo"], (m.get("bytes") or 0) / 1048576.0))
            real = origen.get_file(m["archivo"], tmp, log)
            if real != esperado or (m["archivo"] in sums and sums[m["archivo"]] != real):
                res[arch] = "sha256 no coincide: no se importa"
                log("[%s] ERROR: sha256 no coincide (%s...). No se importa." % (tipo, real[:12]))
                continue
            vc.importar_zip(tmp, log=log, cache=cache)
            res[arch] = "ok"
        except Exception as e:
            res[arch] = "error: %s" % str(e)[:150]
            log("[%s] ERROR: %s" % (tipo, res[arch]))
        finally:
            try:
                os.remove(tmp)
            except OSError:
                pass
    guardar_manifiesto_local(cache)
    return res


# ------------------------------------------------------------------ pip (sin release)
def preparar_pip(piezas, cache, log=print):
    """Genera con pip las piezas que falten (PySpark: sdist->wheel; ciencia: pip download)."""
    for tipo, v, plat in piezas:
        if tipo == "pyspark":
            if _pyspark_completo(cache, v):
                continue
            serie = vc.serie_de(v)
            info = vc.SERIES[serie]
            d = dir_pieza(cache, "pyspark", v)
            os.makedirs(d, exist_ok=True)
            log("[pyspark py%s] pip: py4j + sdist pyspark==%s -> wheel (varios minutos) ..." % (v, info["pyspark"]))
            vc._run(vc.cmd_py4j(serie, d), log, 600)
            if vc._run(vc.cmd_pyspark_download(serie, d), log, 2400):
                sd = glob.glob(os.path.join(d, "pyspark-%s*.tar.gz" % info["pyspark"]))
                if sd and vc._run(vc.cmd_pyspark_wheel(sd[0], d), log, 2400):
                    for s in sd:
                        os.remove(s)
        else:
            if ciencia_presente(cache, v, plat)[0]:
                continue
            log("[ciencia %s py%s] pip: resolviendo y bajando ..." % (plat, v))
            pins = None
            if plat != "linux":
                lin = _wheels(dir_pieza(cache, "ciencia", v, "linux"))
                pins = dict(_nv(w) for w in lin) or None
            res = construir_ciencia(cache, v, plat, log=log, pins_linux=pins)
            for h in res["huecos"]:
                log("   [hueco] %s" % h)
            log("[ciencia %s py%s] %.1f MB, %d wheels" % (plat, v, res["bytes"] / 1048576.0, len(res["wheels"])))
    guardar_manifiesto_local(cache)


# ------------------------------------------------------------------ migracion / poda
def migrar(cache, log=print, quitar_viejo=False):
    """Reorganiza el layout VIEJO al nuevo SIN perder datos: crea pyspark/, ciencia/<py>/linux/ y
    banco/ (hardlinks: no duplica disco). El viejo queda intacto; con quitar_viejo se MUEVE a
    <cache>/_layout_viejo/ (renombrar, nunca borrar). Devuelve un resumen."""
    resumen = {"pyspark": [], "ciencia": [], "banco": [], "huecos": {}}
    for v in PY_VERSIONES:
        serie = vc.serie_de(v)
        d = dir_pieza(cache, "pyspark", v)
        for w in vc.wheels_exactas_viejas(cache, v):
            os.makedirs(d, exist_ok=True)
            dst = os.path.join(d, os.path.basename(w))
            if not os.path.exists(dst):
                _enlazar(w, dst)
            resumen["pyspark"].append(os.path.relpath(dst, cache))
        if _wheels(os.path.join(cache, "mlops_deps", serie + "_ciencia")) or _wheels(os.path.join(cache, "mlops_deps", serie + "_dl")):
            if not _wheels(dir_pieza(cache, "ciencia", v, "linux")):
                log("[migrar] ciencia linux py%s ..." % v)
                res = construir_ciencia(cache, v, "linux", log=log)
                resumen["ciencia"].append(os.path.relpath(res["dir"], cache))
                if res["huecos"]:
                    resumen["huecos"][v] = res["huecos"]
    # banco: solo mex-lib + pkgcode (las wheels open source quedaron dentro de ciencia/linux)
    viejo = os.path.join(cache, "bank_libs")
    nuevo = os.path.join(cache, "banco")
    if os.path.isdir(viejo):
        for r, ds, fs in os.walk(viejo):
            ds[:] = [x for x in ds if x != "__pycache__"]
            for f in fs:
                rel = os.path.relpath(os.path.join(r, f), viejo)
                if rel.startswith("wheels" + os.sep) and not f.lower().startswith(("mex-lib", "mex_lib")):
                    continue
                if f.endswith((".pyc", ".pyo")) or f == ".DS_Store":
                    continue
                dst = os.path.join(nuevo, rel)
                os.makedirs(os.path.dirname(dst), exist_ok=True)
                if not os.path.exists(dst):
                    _enlazar(os.path.join(r, f), dst)
                resumen["banco"].append(os.path.relpath(dst, cache))
    guardar_manifiesto_local(cache)
    if quitar_viejo:
        dest = os.path.join(cache, "_layout_viejo")
        os.makedirs(dest, exist_ok=True)
        for n in ("py38-311", "py312plus", "mlops_deps", "bank_libs"):
            if os.path.isdir(os.path.join(cache, n)):
                os.rename(os.path.join(cache, n), os.path.join(dest, n))
        log("[migrar] layout viejo movido a %s (nada se borro)" % dest)
    return resumen


def podar_piezas(cache, elegidas, aplicar=False, log=print):
    """Conserva solo las piezas elegidas [(tipo, py, plat)] del layout NUEVO (banco nunca se toca).
    Devuelve (carpetas, bytes)."""
    quedan = set()
    for tipo, v, plat in elegidas:
        quedan.add(os.path.realpath(dir_pieza(cache, tipo, v, plat)))
    sobran = []
    pr = os.path.join(cache, "pyspark")
    if os.path.isdir(pr):
        sobran += [os.path.join(pr, d) for d in os.listdir(pr)]
    cr = os.path.join(cache, "ciencia")
    if os.path.isdir(cr):
        for v in os.listdir(cr):
            if os.path.isdir(os.path.join(cr, v)):
                sobran += [os.path.join(cr, v, p) for p in os.listdir(os.path.join(cr, v))]
    sobran = [d for d in sobran if os.path.isdir(d) and os.path.realpath(d) not in quedan]
    total = 0
    for d in sorted(sobran):
        b = vc._dir_bytes(d)
        total += b
        log("  %s %s (%s)" % ("borrar" if aplicar else "sobra ", os.path.relpath(d, cache), vc._mb(b)))
        if aplicar:
            shutil.rmtree(d, ignore_errors=True)
    if aplicar:
        for pad in (pr, cr):
            for r, ds, fs in os.walk(pad, topdown=False):
                if os.path.isdir(r) and not os.listdir(r):
                    os.rmdir(r)
    log("%s %d carpetas, %s." % ("Liberados" if aplicar else "Se podrian liberar", len(sobran), vc._mb(total)))
    return len(sobran), total
