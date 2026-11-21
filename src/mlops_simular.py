# -*- coding: utf-8 -*-
"""Simulacion de los jobs de un paquete Framework MLOps v2 desde la UI (estilo terminal).

Monta el ZIP del token en <cache>/_simular/<hash del ZIP>/, crea su venv UNA vez con setup.sh y
corre `python main.py --demo --source <job>` (o `--demo --continuar-si-falla` para todos) en un
SUBPROCESO, con el log en vivo (offset incremental), cancelacion que mata el arbol de procesos y
un resumen por job (estado, tiempo, filas escritas segun REPORTE_DEMO.json de bnx_demo).

ORDEN: el/los PIVOTE siempre primero. 'todos': pivotes y despues el resto (orden.json / depends_on,
igual que el runner del paquete). Un job suelto que no es pivote corre antes el pivote de su mismo
modelo si su salida aun no existe en el demo_out de la sesion.

Solo Mac/Linux (en Windows devuelve un mensaje). Sin red: no importa nada del portal salvo
vendor_cache (carpeta de cache). Compatible con Python 3.8.

DONDE SIMULAR: 'mac' (este equipo, venv del host) o 'linux' (contenedor RHEL 8 x86_64 con Podman, como el
servidor del banco: glibc 2.28, Python 3.11, Java 17). En 'linux' el ZIP se extrae en un directorio del host
que se MONTA en el contenedor (nunca va dentro de la imagen) y se corre lo mismo que en el servidor:
`bash setup.sh` (--network none: prueba que vendor/ esta completo), `python check_env.py` y
`bash run.sh --demo ...`. Cancelar mata el contenedor (podman kill / rm -f).
"""
import ast
import hashlib
import json
import os
import re
import shlex
import shutil
import signal
import subprocess
import sys
import threading
import time
import uuid
import zipfile

PKG_DIR = "framework_mlops_v2_pkg"
LINUX_MAQUINA = "bnx-linux"                 # maquina de Podman (BNX_LINUX_MACHINE)
LINUX_IMG = "bnx-rhel8"                     # servidor SIN PySpark instalado
LINUX_IMG_SPARK = "bnx-rhel8-spark"         # servidor CON PySpark 3.5.6 en el python3.11 del sistema
LINUX_PLATAFORMA = "linux/amd64"
LINUX_GB = 8                                # espacio aprox. (maquina virtual + imagenes) para el boton 'Preparar'
MSG_SIN_PODMAN = "Podman no está instalado (brew install podman)"
LOG_MAX = 5 * 1024 * 1024
MSG_WINDOWS = "La simulación requiere Mac/Linux (o WSL) y Java"
_LOCK = threading.RLock()
_RUNS = {}           # run_id -> Run
_ACTIVO = {}         # hash del paquete -> run_id en curso
_HASH_CACHE = {}     # (ruta, mtime, size) -> hash


class SimError(Exception):
    def __init__(self, msg, status=400):
        super().__init__(msg)
        self.status = status


# ---------------------------------------------------------------------------
# Utilidades puras (testeables sin Spark)
# ---------------------------------------------------------------------------
def es_windows():
    return os.name == "nt"


def cache_base():
    d = os.environ.get("BNX_SIMULAR_DIR")
    if not d:
        from . import vendor_cache as _vc
        d = os.path.join(_vc.cache_dir(), "_simular")
    return os.path.abspath(d)


# ---------------------------------------------------------------------------
# Limpieza de simulaciones viejas (cada paquete distinto monta su carpeta + venv: ~1 GB c/u)
# ---------------------------------------------------------------------------
_HASH_DIR = re.compile(r"^[0-9a-f]{16}$")


def max_simulaciones():
    """Cuantas carpetas de simulacion se conservan (BNX_SIMULAR_MAX, default 2). 0 = ninguna inactiva."""
    try:
        return max(0, int(os.environ.get("BNX_SIMULAR_MAX", 2)))
    except (TypeError, ValueError):
        return 2


def _bytes_dir(ruta):
    total = 0
    pila = [ruta]
    while pila:
        d = pila.pop()
        try:
            with os.scandir(d) as it:
                for e in it:
                    try:
                        if e.is_symlink():
                            continue
                        if e.is_dir(follow_symlinks=False):
                            pila.append(e.path)
                        else:
                            total += e.stat(follow_symlinks=False).st_size
                    except OSError:
                        pass
        except OSError:
            pass
    return total


def _marcar_uso(raiz):
    try:
        with open(os.path.join(raiz, ".usado"), "w") as fh:
            fh.write(str(time.time()))
    except OSError:
        pass


def _ultimo_uso(raiz):
    mt = 0.0
    for n in (".usado", ".montado"):
        try:
            mt = max(mt, os.stat(os.path.join(raiz, n)).st_mtime)
        except OSError:
            pass
    if not mt:
        try:
            mt = os.stat(raiz).st_mtime
        except OSError:
            pass
    return mt


def listar_simulaciones(base=None, con_tamano=True):
    """[{hash, bytes, usado, activo}] de las carpetas de simulacion, la mas reciente primero."""
    base = base or cache_base()
    out = []
    try:
        nombres = os.listdir(base)
    except OSError:
        return out
    with _LOCK:
        activos = set(_ACTIVO.keys())
    for n in nombres:
        raiz = os.path.join(base, n)
        if not (_HASH_DIR.match(n) and os.path.isdir(raiz)):
            continue            # solo carpetas que creo montar(): nunca otra cosa del directorio
        out.append({"hash": n, "usado": _ultimo_uso(raiz), "activo": n in activos,
                    "bytes": _bytes_dir(raiz) if con_tamano else 0})
    out.sort(key=lambda d: d["usado"], reverse=True)
    return out


def espacio_simulaciones(base=None):
    sims = listar_simulaciones(base)
    return {"ok": True, "total": sum(d["bytes"] for d in sims), "carpetas": sims,
            "max": max_simulaciones()}


def limpiar_simulaciones(conservar=None, proteger=(), base=None):
    """Borra las simulaciones inactivas salvo las `conservar` mas recientes (default BNX_SIMULAR_MAX).
    Nunca borra la que esta corriendo (ni las de `proteger`). Devuelve {borradas, liberado, conservadas}."""
    base = base or cache_base()
    conservar = max_simulaciones() if conservar is None else max(0, int(conservar))
    sims = listar_simulaciones(base, con_tamano=False)
    borradas, liberado, conservadas = [], 0, []
    for i, d in enumerate(sims):
        with _LOCK:
            vivo = d["hash"] in _ACTIVO
        if vivo or d["hash"] in proteger or i < conservar:
            conservadas.append(d["hash"])
            continue
        raiz = os.path.join(base, d["hash"])
        tam = _bytes_dir(raiz)
        shutil.rmtree(raiz, ignore_errors=True)
        if not os.path.exists(raiz):
            borradas.append(d["hash"])
            liberado += tam
        else:
            conservadas.append(d["hash"])
    return {"ok": True, "borradas": borradas, "liberado": liberado, "conservadas": conservadas}


def espacio_total():
    """Espacio de las simulaciones de este equipo y de Linux (los paquetes montados en el contenedor)."""
    a, b = espacio_simulaciones(), espacio_simulaciones(linux_base())
    for c in a["carpetas"]:
        c["donde"] = "mac"
    for c in b["carpetas"]:
        c["donde"] = "linux"
    return {"ok": True, "total": a["total"] + b["total"], "carpetas": a["carpetas"] + b["carpetas"], "max": a["max"]}


def limpiar_todas(conservar=None):
    """Limpia las simulaciones inactivas de este equipo y de Linux. Nunca toca la que corre."""
    r1 = limpiar_simulaciones(conservar=conservar)
    r2 = limpiar_simulaciones(conservar=conservar, base=linux_base())
    return {"ok": True, "borradas": r1["borradas"] + r2["borradas"], "liberado": r1["liberado"] + r2["liberado"],
            "conservadas": r1["conservadas"] + r2["conservadas"]}


def hash_zip(path):
    st = os.stat(path)
    clave = (os.path.abspath(path), st.st_mtime, st.st_size)
    if clave not in _HASH_CACHE:
        h = hashlib.sha256()
        with open(path, "rb") as fh:
            for bloque in iter(lambda: fh.read(1 << 20), b""):
                h.update(bloque)
        _HASH_CACHE[clave] = h.hexdigest()[:16]
    return _HASH_CACHE[clave]


def entorno_soportado():
    """(ok, mensaje). Windows -> mensaje; sin Java -> mensaje claro."""
    if es_windows():
        return False, MSG_WINDOWS
    try:
        p = subprocess.run(["java", "-version"], stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                           universal_newlines=True, timeout=30)
        if p.returncode != 0:
            raise OSError(p.stdout)
        linea = (p.stdout or "").strip().splitlines()[:1]
        return True, linea[0] if linea else "java"
    except (OSError, subprocess.SubprocessError):
        return False, ("No se encontró Java (`java -version` falla). PySpark lo necesita: instala Java 17 "
                       "(Mac: brew install openjdk@17; Linux: dnf/apt install openjdk-17) y define JAVA_HOME "
                       "o ponlo en el PATH.")


def _fuentes_de_texto(texto):
    """{nombre: tupla} del _FUENTES de router.py (literal; no se importa codigo del paquete)."""
    try:
        arbol = ast.parse(texto)
    except SyntaxError:
        return {}
    for n in arbol.body:
        if isinstance(n, ast.Assign) and any(getattr(t, "id", "") == "_FUENTES" for t in n.targets):
            try:
                return ast.literal_eval(n.value)
            except ValueError:
                return {}
    return {}


_ROUTER_REL = "framework_mlops_v2/aggregates/router.py"


def _jobs_de_fuentes(fuentes):
    out = []
    for nombre, v in fuentes.items():
        if len(v) >= 4 and v[2] == "kernel":
            partes = str(v[3]).split("/")
            out.append({"name": nombre, "kind": "kernel", "model": partes[0],
                        "job": partes[1] if len(partes) > 1 else partes[0], "ruta": str(v[3])})
        else:
            out.append({"name": nombre, "kind": "aggregate", "model": "", "job": nombre, "ruta": ""})
    return out


def listar_jobs(pkg):
    """[{name, kind ('kernel'|'aggregate'), model, job, ruta}] en el orden del router."""
    ruta = os.path.join(pkg, *_ROUTER_REL.split("/"))
    if not os.path.isfile(ruta):
        return []
    with open(ruta, "r", encoding="utf-8") as fh:
        return _jobs_de_fuentes(_fuentes_de_texto(fh.read()))


def _leer_zip(zip_path, rel):
    try:
        with zipfile.ZipFile(zip_path) as zf:
            for n in (PKG_DIR + "/" + rel, rel):
                if n in zf.namelist():
                    return zf.read(n).decode("utf-8", "replace")
    except (OSError, zipfile.BadZipFile):
        pass
    return None


def cargar_orden(pkg):
    ruta = os.path.join(pkg, "orden.json")
    if not os.path.isfile(ruta):
        return {}
    try:
        with open(ruta, "r", encoding="utf-8") as fh:
            d = json.load(fh)
        s = d.get("sources") if isinstance(d, dict) else None
        return s if isinstance(s, dict) else {}
    except (OSError, ValueError):
        return {}


def es_pivote(job, orden=None):
    """Pivote: 'pivot': true en orden.json, nombre pivot/pivote (o *_pivot), o ruta .../pivot/."""
    nombre = job["name"] if isinstance(job, dict) else str(job)
    if ((orden or {}).get(nombre) or {}).get("pivot"):
        return True
    norm = nombre.strip().lower().replace("-", "_")
    if norm in ("pivote", "pivot") or norm.endswith(("_pivote", "_pivot")):
        return True
    if isinstance(job, dict):
        partes = [p.lower() for p in str(job.get("ruta") or "").split("/")]
        return "pivot" in partes or str(job.get("job") or "").lower() in ("pivot", "pivote")
    return False


def orden_todos(jobs, orden=None):
    """Nombres en orden de ejecucion: pivotes primero y luego el resto respetando depends_on
    (mismo criterio que _orden_dependencias del main.py del paquete)."""
    orden = orden or {}
    nombres = [j["name"] for j in jobs]
    idx = {n: i for i, n in enumerate(nombres)}
    pivotes = [j["name"] for j in jobs if es_pivote(j, orden)]
    deps = {}
    for n in nombres:
        d = (orden.get(n) or {}).get("depends_on")
        if isinstance(d, list):
            deps[n] = [x for x in d if x in idx and x != n]
        elif n in pivotes:
            deps[n] = []
        else:
            deps[n] = list(pivotes)
    pendientes = {n: len(set(deps[n])) for n in nombres}
    hijos = {n: [] for n in nombres}
    for n in nombres:
        for d in set(deps[n]):
            hijos[d].append(n)
    clave = lambda n: (0 if n in pivotes else 1, idx[n])   # noqa: E731
    listas = sorted([n for n in nombres if pendientes[n] == 0], key=clave)
    salida = []
    while listas:
        n = listas.pop(0)
        salida.append(n)
        for h in hijos[n]:
            pendientes[h] -= 1
            if pendientes[h] == 0:
                listas.append(h)
        listas.sort(key=clave)
    if len(salida) != len(nombres):
        raise SimError("ciclo de dependencias en orden.json entre: " +
                       ", ".join(sorted(set(nombres) - set(salida))))
    return salida


def pasos_job(nombre, jobs, orden=None, hechos=()):
    """Pasos para simular UN job: si no es pivote, antes el/los pivote(s) de su mismo modelo cuya
    salida no esta ya en la sesion (`hechos` = jobs OK con salida en demo_out)."""
    por_nombre = dict((j["name"], j) for j in jobs)
    if nombre not in por_nombre:
        raise SimError("job desconocido: %s (hay: %s)" % (nombre, ", ".join(por_nombre) or "ninguno"), 404)
    j = por_nombre[nombre]
    if es_pivote(j, orden):
        return [nombre]
    previos = [x["name"] for x in jobs
               if es_pivote(x, orden) and x["model"] == j["model"] and x["name"] != nombre
               and x["name"] not in set(hechos)]
    return previos + [nombre]


_RE_FIN = re.compile(r"\[kernel\] FIN (OK|ERROR) (\S+) en ([\d.]+) s(?:: (.*))?")
_RE_SALTADO = re.compile(r"\[kernel\] SALTADO (\S+):")


def resultados_de_log(texto):
    """{job: {estado, seg}} de las lineas '[kernel] FIN OK|ERROR job en N s' y SALTADO."""
    res = {}
    for m in _RE_FIN.finditer(texto or ""):
        res[m.group(2)] = {"estado": "OK" if m.group(1) == "OK" else "ERROR", "seg": float(m.group(3)),
                           "detalle": (m.group(4) or "")[:160] if m.group(1) != "OK" else ""}
    for m in _RE_SALTADO.finditer(texto or ""):
        res.setdefault(m.group(1), {"estado": "SALTADO", "seg": 0.0})
    return res


def filas_escritas(demo_out):
    """{job: [{destino, tipo, filas}]} de demo_out/REPORTE_DEMO.json (reporte de bnx_demo)."""
    ruta = os.path.join(demo_out, "REPORTE_DEMO.json")
    try:
        with open(ruta, "r", encoding="utf-8") as fh:
            d = json.load(fh)
    except (OSError, ValueError):
        return {}
    out = {}
    for j in d.get("jobs") or []:
        out[j.get("job")] = [{"destino": str(e.get("destino")), "tipo": e.get("tipo"), "filas": e.get("filas")}
                             for e in j.get("escrituras") or []]
    return out


# ---------------------------------------------------------------------------
# Montaje del paquete y entorno (venv) por hash
# ---------------------------------------------------------------------------
def _seguro_extraer(zf, destino):
    base = os.path.realpath(destino)
    for n in zf.namelist():
        if not os.path.realpath(os.path.join(base, n)).startswith(base + os.sep):
            raise SimError("el ZIP trae una ruta insegura: %s" % n)
    zf.extractall(destino)
    # extractall no conserva el bit de ejecucion de los scripts
    for n in zf.namelist():
        if n.endswith((".sh", "/bin/spark-submit")):
            try:
                os.chmod(os.path.join(base, n), 0o755)
            except OSError:
                pass


def montar(zip_path, base=None):
    """Extrae el ZIP en <cache>/_simular/<hash>/ (una vez). Devuelve (hash, carpeta del paquete)."""
    h = hash_zip(zip_path)
    raiz = os.path.join(base or cache_base(), h)
    pkg = os.path.join(raiz, PKG_DIR)
    marca = os.path.join(raiz, ".montado")
    if not os.path.isfile(marca) or not os.path.isdir(pkg):
        shutil.rmtree(raiz, ignore_errors=True)
        os.makedirs(raiz)
        with zipfile.ZipFile(zip_path) as zf:
            _seguro_extraer(zf, raiz)
        if not os.path.isdir(pkg):
            tops = [d for d in os.listdir(raiz) if os.path.isdir(os.path.join(raiz, d))]
            if len(tops) != 1:
                raise SimError("el ZIP no trae la carpeta %s" % PKG_DIR)
            os.rename(os.path.join(raiz, tops[0]), pkg)
        with open(marca, "w") as fh:
            fh.write(h)
    _marcar_uso(raiz)
    return h, pkg


def python_del_target(pkg):
    """(ruta de python<target>, target) si el target del paquete existe en esta maquina; si no (None, target)."""
    t = ""
    f = os.path.join(pkg, "vendor", "PYTHON_TARGET")
    if os.path.isfile(f):
        with open(f, "r") as fh:
            t = fh.read().strip()
    if not t or not re.fullmatch(r"3\.\d+", t):
        return None, t
    cand = [shutil.which("python" + t)] + [
        os.path.join(d, "bin", "python" + t) for d in
        ("/opt/homebrew/opt/python@" + t, "/usr/local/opt/python@" + t)] + ["/usr/bin/python" + t]
    for c in cand:
        if c and os.path.isfile(c) and os.access(c, os.X_OK):
            return c, t
    return None, t


def venv_python(pkg):
    return os.path.join(pkg, ".venv", "bin", "python")


def venv_listo(pkg):
    return os.path.isfile(os.path.join(pkg, ".bnx_sim_venv_ok")) and os.path.isfile(venv_python(pkg))


def settings_del_paquete(pkg):
    for d in ("bin/settings", "settings", "bank_src/settings"):
        p = os.path.join(pkg, *d.split("/"))
        if os.path.isfile(os.path.join(p, "spark.json")):
            return p
    return None


ENVS = ("uat", "prod", "sbx")
_RE_ENV = re.compile(r"^[A-Za-z][A-Za-z0-9_]{0,15}$")


def analizar_envs_textos(textos):
    """Que ambiente (uat/prod/sbx) tiene completas las claves de los settings del banco. `textos` = {ruta relativa:
    texto JSON} de jobs.json, <modelo>/<job>.json y <modelo>/config_custom.json (bloque 'env').
    Devuelve {envs, faltan:{env:[ 'archivo: clave' ]}, n:{env:int}, recomendado, motivo}."""
    claves = {}                                    # archivo -> {env: set(claves)}
    for rel, txt in (textos or {}).items():
        if rel.endswith("spark.json") or not rel.endswith(".json"):
            continue
        try:
            d = json.loads(txt)
        except ValueError:
            continue
        if not isinstance(d, dict):
            continue
        bloques = d["env"] if rel.endswith("config_custom.json") and isinstance(d.get("env"), dict) else d
        por_env = dict((e, set(v.keys())) for e, v in bloques.items() if isinstance(v, dict) and e in ENVS)
        if rel.endswith("config_custom.json") and isinstance(d.get("default"), dict):
            for e in por_env:
                por_env[e] |= set(d["default"].keys())
        if por_env:
            claves[rel] = por_env
    envs = [e for e in ENVS if any(e in v for v in claves.values())]
    faltan = dict((e, []) for e in envs)
    for rel, por_env in sorted(claves.items()):
        union = set().union(*por_env.values())
        for e in envs:
            for k in sorted(union - por_env.get(e, set())):
                faltan[e].append("%s: %s" % (rel, k))
    n = dict((e, len(v)) for e, v in faltan.items())
    rec, motivo = None, ""
    if envs:
        completos = [e for e in ENVS if e in n and n[e] == 0]
        if completos:
            rec = completos[0]
            motivo = "%s trae todas las claves" % rec
        else:
            rec = sorted(envs, key=lambda e: (n[e], 0 if e == "prod" else 1))[0]
            otros = [e for e in envs if e != rec and n[e]]
            motivo = "%s es el más completo; %s" % (rec, ", ".join(
                "%s no trae %d clave(s) (p. ej. %s)" % (e, n[e], faltan[e][0]) for e in otros))
    return {"envs": envs, "faltan": dict((e, v[:12]) for e, v in faltan.items()), "n": n,
            "recomendado": rec, "motivo": motivo}


def analizar_envs(settings_dir):
    textos = {}
    for r, _d, fs in os.walk(settings_dir):
        for f in fs:
            if f.endswith(".json"):
                p = os.path.join(r, f)
                try:
                    with open(p, "r", encoding="utf-8") as fh:
                        textos[os.path.relpath(p, settings_dir).replace(os.sep, "/")] = fh.read()
                except OSError:
                    pass
    return analizar_envs_textos(textos)


def validar_settings(ruta):
    """Carpeta bin/settings elegida por el usuario (ruta LOCAL, solo lectura): existe, es carpeta y trae
    spark.json. Devuelve la ruta real o lanza SimError con el motivo."""
    ruta = os.path.realpath(os.path.expanduser(str(ruta).strip()))
    if not os.path.isdir(ruta):
        raise SimError("la carpeta bin/settings no existe o no es una carpeta: %s" % ruta)
    if not os.path.isfile(os.path.join(ruta, "spark.json")):
        raise SimError("%s no parece bin/settings del banco: falta spark.json (trae también jobs.json, "
                       "config_custom.json y <modelo>/<job>.json)" % ruta)
    if not os.access(ruta, os.R_OK):
        raise SimError("sin permiso de lectura en %s" % ruta)
    return ruta


def sesion_path(pkg):
    return os.path.join(os.path.dirname(pkg), "sesion.json")


def leer_sesion(pkg):
    try:
        with open(sesion_path(pkg), "r", encoding="utf-8") as fh:
            d = json.load(fh)
        return d if isinstance(d, dict) else {"jobs": {}}
    except (OSError, ValueError):
        return {"jobs": {}}


def _guardar_sesion(pkg, ses):
    with open(sesion_path(pkg), "w", encoding="utf-8") as fh:
        json.dump(ses, fh, indent=1, default=str)


def jobs_hechos(pkg):
    """Jobs OK de la sesion cuya carpeta demo_out sigue existiendo."""
    if not os.path.isdir(os.path.join(pkg, "demo_out")):
        return set()
    return set(n for n, v in (leer_sesion(pkg).get("jobs") or {}).items() if v.get("estado") == "OK")


def visor_base(pkg):
    """Carpeta base para el visor de parquet: <hash>/visor/output -> <paquete>/demo_out (zona 'output')."""
    out = os.path.join(pkg, "demo_out")
    os.makedirs(out, exist_ok=True)
    vb = os.path.join(os.path.dirname(pkg), "visor")
    os.makedirs(vb, exist_ok=True)
    link = os.path.join(vb, "output")
    if os.path.islink(link) and os.path.realpath(link) != os.path.realpath(out):
        os.remove(link)
    if not os.path.lexists(link):
        os.symlink(out, link)
    return vb


def reiniciar_demo_out(pkg):
    shutil.rmtree(os.path.join(pkg, "demo_out"), ignore_errors=True)
    try:
        os.remove(sesion_path(pkg))
    except OSError:
        pass


# ---------------------------------------------------------------------------
# Ejecucion
# ---------------------------------------------------------------------------
def matar_arbol(proc):
    """Mata el proceso y todos sus descendientes (POSIX: grupo propio; Windows: taskkill /T /F)."""
    if es_windows():
        subprocess.run(["taskkill", "/PID", str(proc.pid), "/T", "/F"],
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return
    try:
        os.killpg(proc.pid, signal.SIGTERM)
    except (ProcessLookupError, PermissionError):
        pass
    fin = time.time() + 3
    while time.time() < fin and proc.poll() is None:
        time.sleep(0.05)
    try:
        os.killpg(proc.pid, signal.SIGKILL)     # hijos que sobrevivan (JVM de Spark)
    except (ProcessLookupError, PermissionError):
        pass


def matar_run(run, proc):
    """Mata lo que corre el run: en Linux primero el CONTENEDOR (podman kill + rm -f) y luego el cliente."""
    if run.contenedor:
        _podman_limpiar(run.contenedor, matar=True)
    matar_arbol(proc)


def _popen_kwargs():
    if es_windows():
        return {"creationflags": getattr(subprocess, "CREATE_NEW_PROCESS_GROUP", 0)}
    return {"start_new_session": True}


def _env_base(pkg, py):
    e = dict(os.environ)
    for k in ("PYTHONHOME", "VIRTUAL_ENV", "BNX_CLUSTER_SPARK", "PYSPARK_SUBMIT_ARGS"):
        e.pop(k, None)
    e.update({"BNX_MONITOR_FILE": os.path.join(pkg, ".bnx_monitor.jsonl"),
              "PYTHONUNBUFFERED": "1", "PYTHONUTF8": "1", "PYTHONIOENCODING": "utf-8",
              "LC_ALL": e.get("LC_ALL") or "en_US.UTF-8", "PYSPARK_PYTHON": py, "PYSPARK_DRIVER_PYTHON": py,
              "SPARK_LOCAL_IP": "127.0.0.1", "BNX_SIMULACION": "1"})
    bp = os.path.join(pkg, "bank_pkg")
    pp = [p for p in (bp if os.path.isdir(bp) else "", e.get("PYTHONPATH", "")) if p]
    if pp:
        e["PYTHONPATH"] = os.pathsep.join(pp)
    return e


def comando_job(py, pkg, objetivo, settings=None, env=None):
    """objetivo = nombre de job o None (todos). env = uat|prod|sbx (ambiente de los settings del banco)."""
    cmd = [py, "main.py", "--demo"]
    if objetivo:
        cmd += ["--source", objetivo]
    else:
        cmd += ["--continuar-si-falla"]
    if settings:
        cmd += ["--settings", settings]
    if env:
        cmd += ["--env", env]
    return cmd


class Run(object):
    def __init__(self, token, h, pkg, objetivo, timeout, donde="mac"):
        self.id = uuid.uuid4().hex[:12]
        self.donde = donde                 # 'mac' | 'linux'
        self.monitor_file = os.path.join(pkg, ".bnx_monitor.jsonl")   # muestras de CPU/memoria del runner (jsonl)
        self._ev_off = 0                   # lectura de eventos (inicio/fin de job) para el resumen de recursos
        self.recursos = {}                 # job -> stats de CPU/memoria (del evento 'fin')
        self.env = None                    # --env de los settings del banco (uat|prod|sbx)
        self.contenedor = None             # nombre del contenedor en curso (donde == 'linux')
        self.encabezado = ""               # 'Linux RHEL 8 x86_64 · Python 3.11.x · glibc 2.28 · Java 17'
        self.imagen = ""
        self.check_env = None              # {rc, seg} de python check_env.py (linux)
        self.t_check = 0.0
        self.token, self.hash, self.pkg = token, h, pkg
        self.objetivo = objetivo           # None = todos
        self.timeout = timeout
        self.estado = "preparando"         # preparando | corriendo | ok | fallo | cancelado
        self.log = ""
        self.plan = []                     # nombres en orden
        self.pasos = []                    # [{paso, job, estado}]
        self.resumen = []                  # [{job, estado, seg, escrituras}]
        self.t0 = time.time()
        self.t1 = None
        self.t_setup = 0.0                 # segundos de arranque (montaje + venv)
        self.venv_reutilizado = None
        self.avisos = []
        self.cancelar_flag = False
        self.proc = None
        self.lock = threading.Lock()

    def emit(self, texto):
        with self.lock:
            if len(self.log) < LOG_MAX:
                self.log += texto
                if len(self.log) >= LOG_MAX:
                    self.log += "\n[sim] (log recortado: supera %d MB)\n" % (LOG_MAX // (1024 * 1024))

    def linea(self, texto):
        self.emit(texto.rstrip("\n") + "\n")

    def duracion(self):
        return round((self.t1 or time.time()) - self.t0, 1)

    def _leer_eventos(self):
        try:
            from .mlops_demo import monitor as _m
            evs, self._ev_off = _m.leer_incremental(self.monitor_file, self._ev_off, maximo=100000)
        except Exception:
            return
        for e in evs:
            if e.get("ev") == "fin" and e.get("job"):
                self.recursos[e["job"]] = e.get("stats") or {}

    def faltantes(self):
        """Faltantes/parches de librerias del banco que dejo el runner (logs/BNX_FALTANTES.json del paquete): lo
        que la pantalla muestra como tarjetas. [] si no hay."""
        ruta = os.path.join(self.pkg, "logs", "BNX_FALTANTES.json")
        try:
            with open(ruta, "r", encoding="utf-8") as fh:
                d = json.load(fh)
            lista = d.get("faltantes", []) if isinstance(d, dict) else []
        except (OSError, ValueError):
            return []
        return [f for f in lista if isinstance(f, dict)][:50]

    def muestras(self, moff=0, maximo=600):
        """(muestras y marcas nuevas desde el byte `moff`, nuevo offset) del monitor de recursos."""
        try:
            from .mlops_demo import monitor as _m
            return _m.leer_incremental(self.monitor_file, moff, maximo=maximo)
        except Exception:
            return [], int(moff or 0)

    def a_dict(self, offset=0, moff=0):
        self._leer_eventos()
        mon, moff2 = self.muestras(moff)
        with self.lock:
            offset = max(0, min(int(offset or 0), len(self.log)))
            return {"ok": True, "run": self.id, "estado": self.estado, "log": self.log[offset:],
                    "offset": len(self.log), "duracion": self.duracion(), "plan": list(self.plan),
                    "pasos": list(self.pasos), "resumen": list(self.resumen),
                    "terminado": self.estado in ("ok", "fallo", "cancelado"),
                    "arranque_seg": round(self.t_setup, 1), "venv_reutilizado": self.venv_reutilizado,
                    "avisos": list(self.avisos), "objetivo": self.objetivo or "todos",
                    "monitor": mon, "monitor_offset": moff2, "recursos": dict(self.recursos),
                    "donde": self.donde, "encabezado": self.encabezado, "imagen": self.imagen, "env": self.env,
                    "demo_conf": (re.findall(r"\[demo\] config: (demo: [^\n]*)", self.log) or [""])[-1],
                    "check_env": self.check_env, "faltantes": self.faltantes()}


def _stream(run, cmd, cwd, env, timeout):
    """Corre cmd volcando su salida al log en vivo. Devuelve el codigo de salida (-9 cancelado/timeout)."""
    try:
        proc = subprocess.Popen(cmd, cwd=cwd, env=env, stdin=subprocess.DEVNULL, stdout=subprocess.PIPE,
                                stderr=subprocess.STDOUT, **_popen_kwargs())
    except OSError as e:
        run.linea("[ERROR] no se pudo lanzar %s: %s" % (cmd[0], e))
        return -1
    run.proc = proc
    vencio = []

    def _vigilante():
        fin = time.time() + timeout
        while proc.poll() is None:
            if run.cancelar_flag:
                matar_run(run, proc)
                return
            if time.time() > fin:
                vencio.append(1)
                run.linea("[ERROR] timeout de %d s: se mata el %s" % (timeout, "contenedor" if run.contenedor else "proceso"))
                matar_run(run, proc)
                return
            time.sleep(0.2)
    vig = threading.Thread(target=_vigilante, daemon=True)
    vig.start()
    for raw in iter(proc.stdout.readline, b""):
        run.emit(raw.decode("utf-8", "replace"))
    proc.stdout.close()
    rc = proc.wait()
    vig.join(timeout=5)
    if run.contenedor:                    # --rm lo borra al salir; si quedo algo (kill/timeout) se limpia
        _podman_limpiar(run.contenedor)
        run.contenedor = None
    # el grupo puede seguir vivo (JVM) aunque el lider haya salido: se limpia siempre
    if not es_windows():
        try:
            os.killpg(proc.pid, signal.SIGKILL)
        except (ProcessLookupError, PermissionError):
            pass
    run.proc = None
    return -9 if (run.cancelar_flag or vencio) else rc


def _preparar_venv(run, pkg):
    """Crea .venv con setup.sh (offline desde vendor/ cuando las wheels sirven en esta maquina) UNA vez."""
    if venv_listo(pkg):
        run.venv_reutilizado = True
        run.linea("[sim] entorno reutilizado (.venv ya montado para este paquete)")
        return True
    run.venv_reutilizado = False
    if not os.path.isfile(os.path.join(pkg, "setup.sh")):
        run.linea("[ERROR] el paquete no trae setup.sh")
        return False
    shutil.rmtree(os.path.join(pkg, ".venv"), ignore_errors=True)
    env = dict(os.environ)
    for k in ("PYTHONHOME", "VIRTUAL_ENV", "PYTHONPATH"):
        env.pop(k, None)
    env["PYTHONUNBUFFERED"] = "1"
    py, target = python_del_target(pkg)
    if py:
        env["PYTHON"] = py
        run.linea("[sim] Python del target del paquete: %s (%s)" % (py, target))
    elif target:
        aviso = ("el paquete es para Python %s y no está en esta máquina: se usa el Python del host (%s %d.%d). "
                 "Puede variar el entorno respecto al servidor." % (
                     target or "?", os.path.basename(sys.executable), sys.version_info[0], sys.version_info[1]))
        run.avisos.append(aviso)
        run.linea("[AVISO] " + aviso)
        try:
            os.remove(os.path.join(pkg, "vendor", "PYTHON_TARGET"))
        except OSError:
            pass
    modo = os.path.join(pkg, "vendor", "PYSPARK_MODE")
    if os.path.isfile(modo):
        with open(modo, "r") as fh:
            if fh.read().strip() == "servidor":
                os.remove(modo)
                run.linea("[sim] paquete 'sin PySpark' (usa el del servidor): para simular se instala PySpark en el venv")
    run.linea("[sim] montando el entorno: bash setup.sh (una sola vez; offline desde vendor/ si las wheels sirven aqui)")
    rc = _stream(run, ["bash", "setup.sh"], pkg, env, int(os.environ.get("BNX_SIMULAR_SETUP_TIMEOUT", 3600)))
    if rc != 0:
        run.linea("[ERROR] setup.sh terminó con código %s" % rc)
        return False
    chk = subprocess.run([venv_python(pkg), "-c", "import pyspark,sys;print(pyspark.__version__)"],
                         stdout=subprocess.PIPE, stderr=subprocess.STDOUT, universal_newlines=True)
    if chk.returncode != 0:
        run.linea("[ERROR] el entorno quedó sin PySpark (sin internet y sin wheel en vendor/): " +
                  (chk.stdout or "").strip()[-300:])
        return False
    run.linea("[sim] PySpark %s listo" % chk.stdout.strip())
    with open(os.path.join(pkg, ".bnx_sim_venv_ok"), "w") as fh:
        fh.write(chk.stdout.strip())
    return True


def _ejecutar(run, jobs, orden, usar_settings):
    pkg = run.pkg
    try:
        t_ini = time.time()
        linux = run.donde == "linux"
        if not (_preparar_linux(run, pkg) if linux else _preparar_venv(run, pkg)):
            run.estado = "fallo"
            return
        run.t_setup = time.time() - t_ini
        if run.cancelar_flag:
            run.estado = "cancelado"
            return
        py = venv_python(pkg)
        env = _env_base(pkg, py) if not linux else None
        settings = usar_settings
        settings_cont, montajes = (settings_contenedor(pkg, settings) if (linux and settings) else (None, None))
        montajes = [montajes] if montajes else []
        sesion = leer_sesion(pkg)
        sesion.setdefault("jobs", {})
        run.estado = "corriendo"
        if run.objetivo is None:
            plan = orden_todos(jobs, orden)
            piv = [n for n in plan if es_pivote(next(j for j in jobs if j["name"] == n), orden)]
            run.linea("[orden] pivotes primero: %s" % (", ".join(piv) or "(ninguno)"))
            run.linea("[orden] después: %s" % (", ".join(n for n in plan if n not in piv) or "(nada)"))
            run.plan = plan
            pasos = [None]                       # un solo proceso: --continuar-si-falla (el runner ordena)
        else:
            pasos = pasos_job(run.objetivo, jobs, orden, jobs_hechos(pkg))
            run.plan = list(pasos)
            if len(pasos) > 1:
                run.linea("[orden] %s no es pivote: antes corre %s (su salida no está en demo_out de esta sesión)"
                          % (run.objetivo, ", ".join(pasos[:-1])))
        run.pasos = [{"paso": i + 1, "job": p or "todos", "estado": "pendiente"} for i, p in enumerate(pasos)]
        fallo = False
        for i, paso in enumerate(pasos):
            nombre = paso or "todos"
            if run.cancelar_flag:
                break
            if fallo:
                run.pasos[i]["estado"] = "saltado"
                run.linea("[%d/%d] %s SALTADO: falló el paso anterior (pivote)" % (i + 1, len(pasos), nombre))
                run.resumen.append({"job": nombre, "estado": "SALTADO", "seg": 0.0, "escrituras": []})
                continue
            run.pasos[i]["estado"] = "corriendo"
            run.linea("")
            run.linea("[%d/%d] %s" % (i + 1, len(pasos), nombre))
            mark = len(run.log)
            if linux:
                script = _linux_script_job(paso, settings_cont, run.env)
                run.linea("$ " + script + "   (contenedor %s, sin red)" % run.imagen)
                t0 = time.time()
                rc = _paso_linux(run, nombre, script, run.imagen, os.path.dirname(pkg), run.timeout,
                                 montajes=montajes)
            else:
                cmd = comando_job(py, pkg, paso, settings, run.env)
                run.linea("$ " + " ".join(os.path.basename(c) if c == py else c for c in cmd))
                t0 = time.time()
                rc = _stream(run, cmd, pkg, env, run.timeout)
            seg = time.time() - t0
            texto = run.log[mark:]
            res = resultados_de_log(texto)
            filas = filas_escritas(os.path.join(pkg, "demo_out"))
            if paso is None:
                nombres = run.plan
            else:
                nombres = [paso]
            for n in nombres:
                r = res.get(n)
                if r is None:      # aggregates o job que no llego a imprimir FIN: por codigo de salida
                    r = {"estado": "OK" if rc == 0 else ("CANCELADO" if rc == -9 else "ERROR"), "seg": seg} \
                        if paso is not None else {"estado": "CANCELADO" if rc == -9 else "NO CORRIÓ", "seg": 0.0}
                esc = filas.get(n, [])
                run._leer_eventos()
                run.resumen.append({"job": n, "estado": r["estado"], "seg": round(r["seg"], 1),
                                    "escrituras": esc, "detalle": r.get("detalle", ""),
                                    "recursos": run.recursos.get(n)})
                if r["estado"] in ("OK", "ERROR", "SALTADO"):     # lo que no corrio no cuenta como sesion
                    sesion["jobs"][n] = {"estado": r["estado"], "seg": round(r["seg"], 1), "escrituras": esc,
                                         "ts": time.time()}
            _guardar_sesion(pkg, sesion)
            if paso is None:
                run.pasos[i]["estado"] = "ok" if rc == 0 else "fallo"
            else:
                ok_paso = rc == 0 and run.resumen[-1]["estado"] == "OK"
                run.pasos[i]["estado"] = "ok" if ok_paso else "fallo"
                fallo = not ok_paso
        if run.cancelar_flag:
            run.estado = "cancelado"
        else:
            malos = [r for r in run.resumen if r["estado"] != "OK"]
            run.estado = "ok" if not malos and not fallo else "fallo"
        _imprimir_resumen(run)
    except SimError as e:
        run.linea("[ERROR] %s" % e)
        run.estado = "fallo"
    except Exception as e:   # no dejar el run colgado en 'corriendo'
        run.linea("[ERROR] %s: %s" % (type(e).__name__, e))
        run.estado = "fallo"
    finally:
        run.t1 = time.time()
        with _LOCK:
            if _ACTIVO.get(run.hash) == run.id:
                del _ACTIVO[run.hash]


def _imprimir_resumen(run):
    run.linea("")
    run.linea("=" * 64)
    run.linea("[sim] RESUMEN (%s)" % run.estado.upper())
    for r in run.resumen:
        total = sum(e["filas"] for e in r["escrituras"] if isinstance(e.get("filas"), int))
        marca = "[%s]" % ("OK" if r["estado"] == "OK" else "ERROR" if r["estado"] == "ERROR" else r["estado"])
        marca = marca.ljust(11)
        run.linea("  %s %-24s %6.1f s  %s" % (marca, r["job"], r["seg"],
                                              ("%d fila(s) escritas en %d salida(s)" % (total, len(r["escrituras"])))
                                              if r["escrituras"] else (r.get("detalle") or r["estado"])))
    ok = sum(1 for r in run.resumen if r["estado"] == "OK")
    run.linea("[sim] %d/%d OK en %.1f s (arranque del entorno: %.1f s)" % (
        ok, len(run.resumen), run.duracion(), run.t_setup))


# ---------------------------------------------------------------------------
# Linux RHEL 8 x86_64 (contenedor de Podman): como el servidor real del banco
# ---------------------------------------------------------------------------
def linux_maquina():
    return os.environ.get("BNX_LINUX_MACHINE") or LINUX_MAQUINA


def podman_bin():
    return shutil.which("podman")


def linux_base():
    """Carpeta (en el host) donde se extraen los paquetes que se MONTAN en el contenedor. Debe estar bajo
    /Users o /private (lo que Podman comparte con su maquina virtual); por eso se resuelve el realpath."""
    return os.path.realpath(cache_base() + "_linux")


def _podman(args, timeout=60, conexion=True):
    """(rc, salida) de `podman [--connection <maquina>] args`. Nunca lanza: sin podman -> (127, mensaje)."""
    exe = podman_bin()
    if not exe:
        return 127, MSG_SIN_PODMAN
    cmd = [exe] + (["--connection", linux_maquina()] if conexion else []) + list(args)
    try:
        p = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, universal_newlines=True,
                           timeout=timeout)
    except (OSError, subprocess.SubprocessError) as e:
        return 1, "%s: %s" % (type(e).__name__, e)
    return p.returncode, p.stdout or ""


def _podman_limpiar(nombre, matar=False):
    """podman kill (si `matar`) + rm -f del contenedor. Silencioso."""
    if matar:
        _podman(["kill", nombre], timeout=30)
    _podman(["rm", "-f", "--ignore", nombre], timeout=30)


def linux_maquina_estado():
    """{existe, activa} de la maquina de Podman (podman machine list --format json)."""
    rc, out = _podman(["machine", "list", "--format", "json"], conexion=False)
    if rc != 0:
        return {"existe": False, "activa": False}
    try:
        lista = json.loads(out or "[]")
    except ValueError:
        return {"existe": False, "activa": False}
    for m in lista if isinstance(lista, list) else []:
        if str(m.get("Name", "")).rstrip("*") == linux_maquina():
            return {"existe": True, "activa": bool(m.get("Running"))}
    return {"existe": False, "activa": False}


def linux_imagen_existe(nombre):
    rc, _o = _podman(["image", "exists", "localhost/" + nombre], timeout=30)
    return rc == 0


def linux_info():
    """Disponibilidad del entorno Linux: Podman, maquina, imagenes. `habilitado` -> se puede elegir en la UI.
    Con la maquina detenida se considera habilitado (se arranca sola al simular); las imagenes solo se
    pueden comprobar con la maquina activa."""
    d = {"podman": bool(podman_bin()), "maquina": linux_maquina(), "maquina_existe": False,
         "maquina_activa": False, "imagenes": {LINUX_IMG: False, LINUX_IMG_SPARK: False},
         "habilitado": False, "razon": "", "gb": LINUX_GB, "preparacion": preparacion_estado()}
    if not d["podman"]:
        d["razon"] = MSG_SIN_PODMAN
        return d
    m = linux_maquina_estado()
    d["maquina_existe"], d["maquina_activa"] = m["existe"], m["activa"]
    if not m["existe"]:
        d["razon"] = "Falta preparar Linux (máquina %s e imágenes, una sola vez)" % d["maquina"]
        return d
    if not m["activa"]:
        d["habilitado"] = True
        d["razon"] = "La máquina %s está detenida: se arranca sola al simular" % d["maquina"]
        return d
    for n in d["imagenes"]:
        d["imagenes"][n] = linux_imagen_existe(n)
    d["habilitado"] = all(d["imagenes"].values())
    if not d["habilitado"]:
        d["razon"] = "Faltan las imágenes (%s): prepara Linux" % ", ".join(n for n, v in d["imagenes"].items() if not v)
    return d


def imagen_para(pkg):
    """bnx-rhel8-spark si el paquete es 'sin PySpark' (usa el del servidor); si no bnx-rhel8 (sin PySpark: el
    paquete trae el suyo en vendor/ y debe bastarse solo)."""
    f = os.path.join(pkg, "vendor", "PYSPARK_MODE")
    try:
        with open(f, "r") as fh:
            if fh.read().strip() == "servidor":
                return LINUX_IMG_SPARK
    except OSError:
        pass
    return LINUX_IMG


def settings_contenedor(pkg, settings):
    """(ruta dentro del contenedor, montaje o None) de una carpeta de settings. Si vive dentro del paquete se usa
    su ruta bajo /work; si es externa se monta SOLO LECTURA en /bnx_settings."""
    real = os.path.realpath(settings)
    raiz = os.path.realpath(os.path.dirname(pkg))
    if real == raiz or real.startswith(raiz + os.sep):
        return "/work/" + os.path.relpath(real, raiz).replace(os.sep, "/"), None
    return "/bnx_settings", (real, "/bnx_settings", "ro")


def comando_podman_run(nombre, imagen, host_dir, script, red=False, env=None, montajes=(), workdir=None):
    """Comando `podman run` de un paso en el contenedor: plataforma amd64, usuario no-root `bnx`, el paquete
    montado en /work (volumen del host), --network none salvo `red=True`, --rm y nombre fijo (para podman kill)."""
    cmd = [podman_bin() or "podman", "--connection", linux_maquina(), "run", "--rm", "--name", nombre,
           "--platform", LINUX_PLATAFORMA, "--user", "bnx"]
    if not red:
        cmd += ["--network", "none"]
    cmd += ["-v", "%s:/work" % host_dir, "-w", workdir or ("/work/" + PKG_DIR)]
    # .bnx_tmp en tmpfs: la JVM (Rosetta + virtiofs) deja los temporales de Spark con permisos ilegibles
    # (d-wx--x--x) y falla con AccessDeniedException; en el servidor real no hay virtiofs.
    cmd += ["--tmpfs", "/work/%s/.bnx_tmp:rw,exec,mode=1777,size=2g" % PKG_DIR]
    for h, c, modo in montajes:
        cmd += ["-v", "%s:%s:%s" % (h, c, modo)]
    for k, v in sorted((env or {}).items()):
        cmd += ["-e", "%s=%s" % (k, v)]
    return cmd + [imagen, "bash", "-c", script]


_SCRIPT_ENCABEZADO = ("cat /etc/redhat-release; uname -m; python3.11 --version 2>&1; ldd --version | head -1; "
                      "java -version 2>&1 | head -1; id -un")


def encabezado_linux(texto):
    """'Linux RHEL 8 x86_64 · Python 3.11.x · glibc 2.28 · Java 17' a partir de la salida de _SCRIPT_ENCABEZADO."""
    rel = re.search(r"release\s+(\d+)(?:\.\d+)?", texto or "")
    arq = re.search(r"^(x86_64|aarch64)\s*$", texto or "", re.M)
    py = re.search(r"Python\s+(3\.\d+\.\d+)", texto or "")
    gl = re.search(r"\(GNU libc\)\s+(\d+\.\d+)", texto or "")
    jv = re.search(r'version\s+"(\d+)', texto or "")
    return "Linux RHEL %s %s · Python %s · glibc %s · Java %s" % (
        rel.group(1) if rel else "?", arq.group(1) if arq else "?", py.group(1) if py else "?",
        gl.group(1) if gl else "?", jv.group(1) if jv else "?")


def _linux_script_job(objetivo, settings_cont, env=None):
    """`bash run.sh --demo --source <job>` (o todos con --continuar-si-falla), igual que en el servidor."""
    partes = ["bash", "run.sh", "--demo"]
    partes += ["--source", objetivo] if objetivo else ["--continuar-si-falla"]
    if settings_cont:
        partes += ["--settings", settings_cont]
    if env:
        partes += ["--env", env]
    return " ".join(shlex.quote(x) for x in partes)


_ENV_PASO = ("BNX_DEMO_CORES", "BNX_DEMO_MEM", "BNX_DEMO_FILAS", "BNX_DEMO_SEED", "BNX_MONITOR",
             "BNX_MONITOR_INTERVALO")


def _env_contenedor():
    e = {"PYTHONUNBUFFERED": "1", "PYTHONUTF8": "1", "LC_ALL": "C.UTF-8", "SPARK_LOCAL_IP": "127.0.0.1",
         "BNX_SIMULACION": "1"}
    e["BNX_DEMO_CORES"] = "4"           # la VM de Podman tiene 4 CPU: el demo usa los 4 (BNX_DEMO_CORES del host manda)
    for k in _ENV_PASO:                 # los ajustes del demo/monitoreo que el usuario fijo en el host
        if os.environ.get(k):
            e[k] = os.environ[k]
    return e


def limpiar_tmp(host_dir):
    """Vacia <paquete>/.bnx_tmp en el host (punto de montaje del tmpfs): corridas viejas dejan carpetas ilegibles."""
    d = os.path.join(host_dir, PKG_DIR, ".bnx_tmp")
    for r, ds, fs in os.walk(d):
        for n in ds + fs:
            try:
                os.chmod(os.path.join(r, n), 0o700 if n in ds else 0o600)
            except OSError:
                pass
    shutil.rmtree(d, ignore_errors=True)
    try:
        os.makedirs(d)
    except OSError:
        pass


def _paso_linux(run, etiqueta, script, imagen, host_dir, timeout, red=False, montajes=(), env_extra=None):
    """Un `podman run` con su salida al log en vivo. Devuelve el codigo de salida."""
    limpiar_tmp(host_dir)
    run.contenedor = "bnx-sim-%s-%s" % (run.id, uuid.uuid4().hex[:6])
    env = _env_contenedor()
    env["BNX_MONITOR_FILE"] = "/work/%s/.bnx_monitor.jsonl" % PKG_DIR
    env.update(env_extra or {})
    cmd = comando_podman_run(run.contenedor, imagen, host_dir, script, red=red, env=env, montajes=montajes)
    return _stream(run, cmd, None, dict(os.environ), timeout)


def _asegurar_maquina(run):
    st = linux_maquina_estado()
    if not st["existe"]:
        run.linea("[ERROR] no existe la máquina de Podman %s: usa 'Preparar Linux'" % linux_maquina())
        return False
    if st["activa"]:
        return True
    run.linea("[sim] arrancando la máquina de Podman %s (una vez)..." % linux_maquina())
    rc, out = _podman(["machine", "start", linux_maquina()], timeout=300, conexion=False)
    if rc != 0 and "already running" not in out.lower():
        run.linea("[ERROR] no arrancó la máquina: %s" % out.strip()[-300:])
        return False
    return True


def _preparar_linux(run, pkg):
    """Encabezado del contenedor + `bash setup.sh` OFFLINE (--network none) + `python check_env.py`, una vez por paquete."""
    host_dir = os.path.dirname(pkg)
    if not _asegurar_maquina(run):
        return False
    run.imagen = imagen_para(pkg)
    if not linux_imagen_existe(run.imagen):
        run.linea("[ERROR] falta la imagen %s: usa 'Preparar Linux'" % run.imagen)
        return False
    # encabezado real, detectado DENTRO del contenedor
    run.contenedor = "bnx-sim-%s-hdr" % run.id
    cmd = comando_podman_run(run.contenedor, run.imagen, host_dir, _SCRIPT_ENCABEZADO)
    rc, out = _run_corto(cmd, 180)
    run.contenedor = None
    run.encabezado = encabezado_linux(out)
    run.linea("[sim] " + run.encabezado + " · imagen %s" % run.imagen)
    if rc != 0 or "x86_64" not in out:
        run.linea("[ERROR] el contenedor no es x86_64/RHEL 8 (rc=%s): %s" % (rc, (out or "").strip()[-300:]))
        return False
    marca = os.path.join(pkg, ".bnx_linux_ok")
    if os.path.isfile(marca) and os.path.isfile(os.path.join(pkg, ".venv", "bin", "python")):
        run.venv_reutilizado = True
        run.linea("[sim] entorno reutilizado (.venv ya montado en Linux para este paquete)")
        return True
    run.venv_reutilizado = False
    if not os.path.isfile(os.path.join(pkg, "setup.sh")):
        run.linea("[ERROR] el paquete no trae setup.sh")
        return False
    shutil.rmtree(os.path.join(pkg, ".venv"), ignore_errors=True)
    for f in (".bnx_spark.env", ".bnx_linux_ok"):
        try:
            os.remove(os.path.join(pkg, f))
        except OSError:
            pass
    run.linea("[sim] $ bash setup.sh   (sin red: --network none, offline desde vendor/ como en el servidor)")
    t0 = time.time()
    rc = _paso_linux(run, "setup", "bash setup.sh", run.imagen, host_dir,
                     int(os.environ.get("BNX_SIMULAR_SETUP_TIMEOUT", 3600)))
    run.linea("[sim] setup.sh terminó con código %s en %.1f s" % (rc, time.time() - t0))
    if rc != 0:
        run.linea("[ERROR] setup.sh falló en Linux (ver arriba qué faltó en vendor/ o qué no se detectó)")
        return False
    run.linea("[sim] $ python check_env.py")
    t1 = time.time()
    rc2 = _paso_linux(run, "check_env", ". .venv/bin/activate && python check_env.py", run.imagen, host_dir, 900)
    run.check_env = {"rc": rc2, "seg": round(time.time() - t1, 1)}
    run.linea("[sim] check_env.py terminó con código %s en %.1f s" % (rc2, time.time() - t1))
    with open(marca, "w") as fh:
        fh.write(run.encabezado)
    return True


def _run_corto(cmd, timeout):
    try:
        p = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, universal_newlines=True,
                           timeout=timeout)
        return p.returncode, p.stdout or ""
    except (OSError, subprocess.SubprocessError) as e:
        return 1, "%s: %s" % (type(e).__name__, e)


# --- preparacion (una vez): maquina + imagenes, en segundo plano con log y estado real -----------------------
_PREP = {"estado": "idle", "log": "", "t0": None, "t1": None, "rc": None}
_PREP_LOCK = threading.RLock()


def preparacion_estado(offset=None):
    with _PREP_LOCK:
        d = {"estado": _PREP["estado"], "duracion": round(((_PREP["t1"] or time.time()) - _PREP["t0"]), 1)
             if _PREP["t0"] else 0.0}
        if offset is not None:
            offset = max(0, min(int(offset or 0), len(_PREP["log"])))
            d.update({"log": _PREP["log"][offset:], "offset": len(_PREP["log"]), "ok": True,
                      "terminado": _PREP["estado"] in ("ok", "fallo")})
        return d


def _prep_log(txt):
    with _PREP_LOCK:
        _PREP["log"] += txt if txt.endswith("\n") else txt + "\n"


def _prep_cmd(cmd, timeout=3600):
    _prep_log("$ " + " ".join(cmd))
    try:
        p = subprocess.Popen(cmd, stdin=subprocess.DEVNULL, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    except OSError as e:
        _prep_log("[ERROR] %s" % e)
        return 1
    fin = time.time() + timeout
    for raw in iter(p.stdout.readline, b""):
        _prep_log(raw.decode("utf-8", "replace"))
        if time.time() > fin:
            p.kill()
            _prep_log("[ERROR] timeout")
            break
    return p.wait()


def comandos_preparacion(ctx=None):
    """Lista de (descripcion, comando) para preparar Linux: init + start de la maquina (si falta) y build de las
    dos imagenes. Pura (testeable)."""
    exe = podman_bin() or "podman"
    ctx = ctx or os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "tools", "linux")
    cf = os.path.join(ctx, "Containerfile.rhel8")
    m = linux_maquina()
    return {
        "init": [exe, "machine", "init", m, "--cpus", "4", "--memory", "6144", "--disk-size", "30"],
        "start": [exe, "machine", "start", m],
        "build": [exe, "--connection", m, "build", "--platform", LINUX_PLATAFORMA, "-t", LINUX_IMG, "-f", cf, ctx],
        "build_spark": [exe, "--connection", m, "build", "--platform", LINUX_PLATAFORMA, "--build-arg",
                        "PYSPARK=3.5.6", "-t", LINUX_IMG_SPARK, "-f", cf, ctx],
    }


def _preparar_hilo():
    try:
        cmds = comandos_preparacion()
        st = linux_maquina_estado()
        if not st["existe"]:
            if _prep_cmd(cmds["init"]) != 0:
                raise RuntimeError("podman machine init falló")
            st = linux_maquina_estado()
        if not st["activa"]:
            rc = _prep_cmd(cmds["start"], 600)
            if rc != 0 and not linux_maquina_estado()["activa"]:
                raise RuntimeError("podman machine start falló")
        for nombre, clave in ((LINUX_IMG, "build"), (LINUX_IMG_SPARK, "build_spark")):
            if linux_imagen_existe(nombre):
                _prep_log("[prep] imagen %s ya existe" % nombre)
                continue
            if _prep_cmd(cmds[clave], 3600) != 0:
                raise RuntimeError("falló el build de %s" % nombre)
        _prep_log("[prep] LISTO: Linux RHEL 8 x86_64 preparado (máquina %s, imágenes %s y %s)" % (
            linux_maquina(), LINUX_IMG, LINUX_IMG_SPARK))
        estado_fin = "ok"
    except Exception as e:
        _prep_log("[ERROR] %s: %s" % (type(e).__name__, e))
        estado_fin = "fallo"
    with _PREP_LOCK:
        _PREP["estado"], _PREP["t1"] = estado_fin, time.time()


def preparar_linux():
    """Prepara Linux en segundo plano (una vez): maquina de Podman + imagenes. 409 si ya hay una preparacion."""
    if not podman_bin():
        raise SimError(MSG_SIN_PODMAN, 400)
    with _PREP_LOCK:
        if _PREP["estado"] == "corriendo":
            raise SimError("ya hay una preparación de Linux en curso", 409)
        _PREP.update({"estado": "corriendo", "log": "", "t0": time.time(), "t1": None})
    threading.Thread(target=_preparar_hilo, daemon=True).start()
    return {"ok": True, "estado": "corriendo"}


# ---------------------------------------------------------------------------
# API (la usa serve_ui.py)
# ---------------------------------------------------------------------------
def info(zip_path, donde="mac"):
    ok, msg = entorno_soportado()
    d = {"ok": True, "soportado": ok, "mensaje": msg, "windows": es_windows(), "donde": donde}
    if es_windows():
        return d
    d["linux"] = linux_info()
    h = hash_zip(zip_path)
    base = linux_base() if donde == "linux" else cache_base()
    pkg = os.path.join(base, h, PKG_DIR)
    montado = os.path.isdir(pkg) and os.path.isfile(os.path.join(base, h, ".montado"))
    if montado:
        jobs, orden = listar_jobs(pkg), cargar_orden(pkg)
    else:       # sin extraer los cientos de MB: solo se lee router.py y orden.json del ZIP
        jobs = _jobs_de_fuentes(_fuentes_de_texto(_leer_zip(zip_path, _ROUTER_REL) or ""))
        try:
            o = json.loads(_leer_zip(zip_path, "orden.json") or "{}").get("sources")
            orden = o if isinstance(o, dict) else {}
        except (ValueError, AttributeError):
            orden = {}
    for j in jobs:
        j["pivote"] = es_pivote(j, orden)
    en_zip = montado and settings_del_paquete(pkg) or None
    if not montado:     # sin extraer: ¿el ZIP trae bank_src/settings/spark.json?
        en_zip = (PKG_DIR + "/bank_src/settings") if _leer_zip(zip_path, "bank_src/settings/spark.json") else None
    firma = hashlib.sha1("|".join(sorted(j["name"] for j in jobs)).encode("utf-8")).hexdigest()[:12]
    listo = (os.path.isfile(os.path.join(pkg, ".bnx_linux_ok")) if donde == "linux" else venv_listo(pkg))
    envs = None
    try:
        if montado and en_zip:
            envs = analizar_envs(en_zip)
        elif en_zip:
            pref = PKG_DIR + "/bank_src/settings/"
            with zipfile.ZipFile(zip_path) as zf:
                envs = analizar_envs_textos(dict((n[len(pref):], zf.read(n).decode("utf-8", "replace"))
                                                 for n in zf.namelist() if n.startswith(pref) and n.endswith(".json")))
    except (OSError, zipfile.BadZipFile):
        envs = None
    d["envs"] = envs
    d.update({"hash": h, "jobs": jobs, "orden_todos": orden_todos(jobs, orden) if jobs else [],
              "entorno_listo": bool(montado and listo),
              "hechos": sorted(jobs_hechos(pkg)) if montado else [],
              "settings": bool(en_zip), "settings_detectado": en_zip or "", "proyecto": firma})
    with _LOCK:
        d["run_activo"] = _ACTIVO.get(h)
    return d


def iniciar(token, zip_path, objetivo=None, timeout=None, settings=None, donde="mac", env=None):
    """Arranca una simulacion en segundo plano. objetivo None/'todos' = todos. 409 si ya hay una.
    donde: 'mac' (este equipo) | 'linux' (contenedor RHEL 8 x86_64 con Podman)."""
    donde = "linux" if str(donde or "").lower() == "linux" else "mac"
    if donde == "linux":
        if es_windows():
            raise SimError(MSG_WINDOWS, 400)
        li = linux_info()
        if not li["habilitado"]:
            raise SimError("Linux no está listo: %s" % (li["razon"] or "prepara Linux"), 400)
        with _LOCK:
            if any(r.donde == "linux" and r.estado in ("preparando", "corriendo") for r in _RUNS.values()):
                raise SimError("ya hay una simulación Linux en curso (se corre una a la vez)", 409)
        base = linux_base()
    else:
        ok, msg = entorno_soportado()
        if not ok:
            raise SimError(msg, 400)
        base = None
    h, pkg = montar(zip_path, base=base) if base else montar(zip_path)
    try:
        limpiar_simulaciones(proteger=(h,), base=base)      # conserva solo las BNX_SIMULAR_MAX mas recientes
    except Exception:
        pass
    jobs = listar_jobs(pkg)
    if not jobs:
        raise SimError("el paquete no trae jobs para simular (router.py sin fuentes)")
    orden = cargar_orden(pkg)
    if objetivo in (None, "", "todos"):
        objetivo = None
    else:
        pasos_job(objetivo, jobs, orden)      # valida el nombre (404)
    try:
        timeout = int(timeout or os.environ.get("BNX_SIMULAR_TIMEOUT", 1800))
    except (TypeError, ValueError):
        timeout = 1800
    timeout = max(30, min(timeout, 7200))
    del_paquete = settings_del_paquete(pkg)
    if settings:
        settings = validar_settings(settings)
        if del_paquete and os.path.realpath(del_paquete) == settings:
            settings = None          # es la del paquete: main.py la autodetecta (bank_src/settings)
    if env is not None and str(env).strip() == "":
        env = None
    if env is not None and not _RE_ENV.match(str(env)):
        raise SimError("env inválido: %r (uat, prod o sbx)" % env)
    analisis = None
    carpeta = settings or del_paquete
    if carpeta:
        try:
            analisis = analizar_envs(carpeta)
        except Exception:
            analisis = None
    if env is None and analisis and analisis["recomendado"]:
        env = analisis["recomendado"]
    with _LOCK:
        if h in _ACTIVO:
            raise SimError("ya hay una simulación en curso para este paquete (run %s)" % _ACTIVO[h], 409)
        run = Run(token, h, pkg, objetivo, timeout, donde)
        run.env = env
        try:
            open(run.monitor_file, "w").close()
        except OSError:
            pass
        _RUNS[run.id] = run
        _ACTIVO[h] = run.id
    if settings:
        origen = "carpeta elegida (solo lectura)"
    elif del_paquete:
        origen = "bank_src/settings del paquete (autodetectado)"
    else:
        origen = ""
    if not origen:
        run.linea("[AVISO] el paquete no trae bin/settings y no indicaste una carpeta: el demo INFIERE settings mínimos "
                  "del código de los jobs (claves inventadas, ver REPORTE_DEMO.json). Para tu config real, "
                  "indica 'Carpeta bin/settings' en el panel o sube bin/settings (.json) al generar el paquete.")
    if analisis and analisis["envs"]:
        faltan_env = analisis["n"].get(env, 0) if env else 0
        run.linea("[sim] env=%s (ambientes en settings: %s; %s)%s" % (
            env, ", ".join(analisis["envs"]), analisis["motivo"] or "completos",
            " AVISO: %s no trae %d clave(s) que otro ambiente sí (p. ej. %s): los jobs que las lean fallarán"
            % (env, faltan_env, analisis["faltan"][env][0]) if faltan_env else ""))
    run.linea("[sim] paquete %s | job: %s | timeout %d s | dónde: %s%s" % (
        h, objetivo or "todos", timeout, "Linux RHEL 8 x86_64 (contenedor)" if donde == "linux" else "este equipo",
        " | settings: %s" % (settings or del_paquete) + " [%s]" % origen if origen else ""))
    hilo = threading.Thread(target=_ejecutar, args=(run, jobs, orden, settings), daemon=True)
    hilo.start()
    return run.id


def estado(run_id, offset=0, moff=0):
    r = _RUNS.get(run_id)
    if r is None:
        raise SimError("run desconocido o expirado", 404)
    return r.a_dict(offset, moff)


def cancelar(run_id):
    r = _RUNS.get(run_id)
    if r is None:
        raise SimError("run desconocido o expirado", 404)
    if r.estado in ("ok", "fallo", "cancelado"):
        return {"ok": True, "estado": r.estado, "mensaje": "ya había terminado"}
    r.cancelar_flag = True
    r.linea("[sim] CANCELADO por el usuario: se mata el árbol de procesos")
    p = r.proc
    if p is not None:
        matar_run(r, p)
    elif r.contenedor:
        _podman_limpiar(r.contenedor, matar=True)
    return {"ok": True, "estado": "cancelando"}


def reiniciar(zip_path, donde="mac"):
    h, pkg = montar(zip_path, base=linux_base() if donde == "linux" else None)
    with _LOCK:
        if h in _ACTIVO:
            raise SimError("hay una simulación en curso: cancélala antes de reiniciar demo_out", 409)
    reiniciar_demo_out(pkg)
    return {"ok": True, "mensaje": "demo_out reiniciado"}


def base_visor(zip_path, donde="mac"):
    h, pkg = montar(zip_path, base=linux_base() if donde == "linux" else None)
    return visor_base(pkg)


# --- modo cluster con spark3-submit FALSO ---------------------------------------------------------------
def _dir_fake():
    return os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "tools", "linux", "fake")


def comando_cluster_fake(nombre, imagen, host_dir, fake=None, env_fase="uat"):
    """`podman run` de `BNX_SPARK=cluster bash run.sh` con spark3-submit FALSO (PATH), /etc/spark3/conf FALSO y un
    spark.json de prueba (cola/executors), todo montado SOLO LECTURA desde tools/linux/fake/."""
    fake = os.path.realpath(fake or _dir_fake())
    montajes = [(os.path.join(fake, "bin"), "/opt/fake/bin", "ro"),
                (os.path.join(fake, "spark3conf"), "/etc/spark3/conf", "ro"),
                (os.path.join(fake, "settings"), "/bnx_settings", "ro")]
    script = ("export PATH=/opt/fake/bin:$PATH BNX_SPARK=cluster HADOOP_CONF_DIR=/etc/hadoop/conf; "
              "bash run.sh --settings /bnx_settings --env %s --cohort 202501 --fid 170589" % shlex.quote(env_fase))
    return comando_podman_run(nombre, imagen, host_dir, script, montajes=montajes, env=_env_contenedor())


def evaluar_cluster(salida, pkg_cont="/work/" + PKG_DIR):
    """Comprueba la salida de run.sh en modo cluster con el submit falso. Devuelve [(descripcion, ok)]."""
    t = salida or ""
    return [
        ("run.sh usó el spark3-submit del PATH (falso)", "FAKE-SPARK3-SUBMIT: argv" in t),
        ("--conf spark.pyspark.driver.python = python del venv",
         "ARG: spark.pyspark.driver.python=%s/.venv/bin/python" % pkg_cont in t),
        ("SPARK_CONF_DIR = el del cluster (/etc/spark3/conf), no reemplazado",
         "FAKE-SPARK3-SUBMIT: SPARK_CONF_DIR=/etc/spark3/conf" in t),
        ("no pisa el python de los executors (PYSPARK_PYTHON sin definir)",
         "PYSPARK_PYTHON=(sin definir)" in t),
        ("cola YARN del spark.json (spark_queue_uat con --env uat)", "ARG: spark.yarn.queue=root.cola_uat_prueba" in t),
        ("executors del spark.json", "ARG: spark.executor.instances=7" in t),
        ("memoria del executor del spark.json", "ARG: spark.executor.memory=6g" in t),
        ("shuffle.partitions del spark.json", "ARG: spark.sql.shuffle.partitions=123" in t),
        ("muestra lo que fija el cluster (spark.pyspark.python)", "el cluster fija: spark.pyspark.python" in t),
        ("tmp de la JVM propio (no /tmp)", "tmp de la JVM:" in t),
    ]


def probar_cluster_linux(zip_path, imprimir=print):
    """Monta el paquete (setup.sh offline si falta) y corre `BNX_SPARK=cluster bash run.sh` con spark3-submit falso.
    Devuelve {ok, checks, log}. Valida el ARMADO del comando (--conf del driver, SPARK_CONF_DIR del cluster,
    cola/executors del spark.json); no hay YARN ni cluster real."""
    li = linux_info()
    if not li["habilitado"]:
        raise SimError("Linux no está listo: %s" % (li["razon"] or "prepara Linux"))
    h, pkg = montar(zip_path, base=linux_base())
    run = Run("cluster", h, pkg, None, 1800, "linux")

    visto = [0]

    def _vaciar():
        with run.lock:
            nuevo = run.log[visto[0]:]
            visto[0] = len(run.log)
        if nuevo and imprimir:
            imprimir(nuevo.rstrip("\n"))
    if not _preparar_linux(run, pkg):
        _vaciar()
        return {"ok": False, "checks": [], "log": run.log}
    _vaciar()
    limpiar_tmp(os.path.dirname(pkg))
    run.contenedor = "bnx-sim-%s-cluster" % run.id
    cmd = comando_cluster_fake(run.contenedor, run.imagen, os.path.dirname(pkg))
    run.linea("[sim] $ BNX_SPARK=cluster bash run.sh --settings /bnx_settings --env uat ...   (spark3-submit FALSO)")
    rc = _stream(run, cmd, None, dict(os.environ), 900)
    _vaciar()
    checks = evaluar_cluster(run.log)
    for desc, ok in checks:
        run.linea("[%s] %s" % ("OK" if ok else "ERROR", desc))
    _vaciar()
    return {"ok": rc == 0 and all(o for _d, o in checks), "checks": checks, "log": run.log}


def _cli(argv=None):
    import argparse
    ap = argparse.ArgumentParser(prog="python -m src.mlops_simular",
                                 description="Simulación en Linux RHEL 8 x86_64 (Podman) sin levantar el portal.")
    sub = ap.add_subparsers(dest="cmd")
    sub.add_parser("info", help="estado de Podman, la máquina y las imágenes")
    sub.add_parser("preparar", help="crea la máquina e imágenes (una vez; bloquea hasta terminar)")
    p = sub.add_parser("simular", help="setup offline + check_env + run.sh --demo en el contenedor")
    p.add_argument("zip")
    p.add_argument("--job", default="todos")
    p.add_argument("--settings", default=None, help="carpeta bin/settings local (solo lectura)")
    p.add_argument("--env", default=None, choices=("uat", "prod", "sbx"), help="ambiente de los settings del banco")
    p.add_argument("--timeout", type=int, default=None)
    p.add_argument("--donde", default="linux", choices=("linux", "mac"))
    p = sub.add_parser("cluster", help="BNX_SPARK=cluster bash run.sh con spark3-submit FALSO")
    p.add_argument("zip")
    a = ap.parse_args(argv)
    if a.cmd == "info":
        print(json.dumps(linux_info(), indent=1, default=str))
        return 0
    if a.cmd == "preparar":
        preparar_linux()
        off = 0
        while True:
            d = preparacion_estado(off)
            off = d["offset"]
            sys.stdout.write(d["log"])
            sys.stdout.flush()
            if d["terminado"]:
                return 0 if d["estado"] == "ok" else 1
            time.sleep(1)
    if a.cmd == "simular":
        rid = iniciar("cli", os.path.abspath(a.zip), a.job, a.timeout, a.settings, a.donde, a.env)
        off = 0
        while True:
            d = estado(rid, off)
            off = d["offset"]
            sys.stdout.write(d["log"])
            sys.stdout.flush()
            if d["terminado"]:
                return 0 if d["estado"] == "ok" else 1
            time.sleep(1)
    if a.cmd == "cluster":
        r = probar_cluster_linux(os.path.abspath(a.zip), imprimir=print)
        return 0 if r["ok"] else 1
    ap.print_help()
    return 2


if __name__ == "__main__":
    sys.exit(_cli())
