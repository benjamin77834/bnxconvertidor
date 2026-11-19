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
"""
import ast
import hashlib
import json
import os
import re
import shutil
import signal
import subprocess
import sys
import threading
import time
import uuid
import zipfile

PKG_DIR = "framework_mlops_v2_pkg"
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
        if os.path.isdir(p):
            return p
    return None


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


def _popen_kwargs():
    if es_windows():
        return {"creationflags": getattr(subprocess, "CREATE_NEW_PROCESS_GROUP", 0)}
    return {"start_new_session": True}


def _env_base(pkg, py):
    e = dict(os.environ)
    for k in ("PYTHONHOME", "VIRTUAL_ENV", "BNX_CLUSTER_SPARK", "PYSPARK_SUBMIT_ARGS"):
        e.pop(k, None)
    e.update({"PYTHONUNBUFFERED": "1", "PYTHONUTF8": "1", "PYTHONIOENCODING": "utf-8",
              "LC_ALL": e.get("LC_ALL") or "en_US.UTF-8", "PYSPARK_PYTHON": py, "PYSPARK_DRIVER_PYTHON": py,
              "SPARK_LOCAL_IP": "127.0.0.1", "BNX_SIMULACION": "1"})
    bp = os.path.join(pkg, "bank_pkg")
    pp = [p for p in (bp if os.path.isdir(bp) else "", e.get("PYTHONPATH", "")) if p]
    if pp:
        e["PYTHONPATH"] = os.pathsep.join(pp)
    return e


def comando_job(py, pkg, objetivo, settings=None):
    """objetivo = nombre de job o None (todos)."""
    cmd = [py, "main.py", "--demo"]
    if objetivo:
        cmd += ["--source", objetivo]
    else:
        cmd += ["--continuar-si-falla"]
    if settings:
        cmd += ["--settings", settings]
    return cmd


class Run(object):
    def __init__(self, token, h, pkg, objetivo, timeout):
        self.id = uuid.uuid4().hex[:12]
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

    def a_dict(self, offset=0):
        with self.lock:
            offset = max(0, min(int(offset or 0), len(self.log)))
            return {"ok": True, "run": self.id, "estado": self.estado, "log": self.log[offset:],
                    "offset": len(self.log), "duracion": self.duracion(), "plan": list(self.plan),
                    "pasos": list(self.pasos), "resumen": list(self.resumen),
                    "terminado": self.estado in ("ok", "fallo", "cancelado"),
                    "arranque_seg": round(self.t_setup, 1), "venv_reutilizado": self.venv_reutilizado,
                    "avisos": list(self.avisos), "objetivo": self.objetivo or "todos"}


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
                matar_arbol(proc)
                return
            if time.time() > fin:
                vencio.append(1)
                run.linea("[ERROR] timeout de %d s: se mata el proceso" % timeout)
                matar_arbol(proc)
                return
            time.sleep(0.2)
    vig = threading.Thread(target=_vigilante, daemon=True)
    vig.start()
    for raw in iter(proc.stdout.readline, b""):
        run.emit(raw.decode("utf-8", "replace"))
    proc.stdout.close()
    rc = proc.wait()
    vig.join(timeout=5)
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
        if not _preparar_venv(run, pkg):
            run.estado = "fallo"
            return
        run.t_setup = time.time() - t_ini
        if run.cancelar_flag:
            run.estado = "cancelado"
            return
        py = venv_python(pkg)
        env = _env_base(pkg, py)
        settings = usar_settings
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
            cmd = comando_job(py, pkg, paso, settings)
            run.linea("$ " + " ".join(os.path.basename(c) if c == py else c for c in cmd))
            mark = len(run.log)
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
                run.resumen.append({"job": n, "estado": r["estado"], "seg": round(r["seg"], 1),
                                    "escrituras": esc, "detalle": r.get("detalle", "")})
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
# API (la usa serve_ui.py)
# ---------------------------------------------------------------------------
def info(zip_path):
    ok, msg = entorno_soportado()
    d = {"ok": True, "soportado": ok, "mensaje": msg, "windows": es_windows()}
    if es_windows():
        return d
    h = hash_zip(zip_path)
    pkg = os.path.join(cache_base(), h, PKG_DIR)
    montado = os.path.isdir(pkg) and os.path.isfile(os.path.join(cache_base(), h, ".montado"))
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
    d.update({"hash": h, "jobs": jobs, "orden_todos": orden_todos(jobs, orden) if jobs else [],
              "entorno_listo": bool(montado and venv_listo(pkg)),
              "hechos": sorted(jobs_hechos(pkg)) if montado else [],
              "settings": bool(montado and settings_del_paquete(pkg))})
    with _LOCK:
        d["run_activo"] = _ACTIVO.get(h)
    return d


def iniciar(token, zip_path, objetivo=None, timeout=None, settings=None):
    """Arranca una simulacion en segundo plano. objetivo None/'todos' = todos. 409 si ya hay una."""
    ok, msg = entorno_soportado()
    if not ok:
        raise SimError(msg, 400)
    h, pkg = montar(zip_path)
    try:
        limpiar_simulaciones(proteger=(h,))      # conserva solo las BNX_SIMULAR_MAX mas recientes
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
    if settings:
        if not os.path.isdir(str(settings)):
            raise SimError("settings no es una carpeta: %s" % settings)
    else:
        settings = settings_del_paquete(pkg)
    with _LOCK:
        if h in _ACTIVO:
            raise SimError("ya hay una simulación en curso para este paquete (run %s)" % _ACTIVO[h], 409)
        run = Run(token, h, pkg, objetivo, timeout)
        _RUNS[run.id] = run
        _ACTIVO[h] = run.id
    if not settings:
        run.linea("[AVISO] sin --settings: los jobs que leen su config de negocio (model_name, tablas, "
                  "config_custom.json) fallan en el demo. Indica la carpeta bin/settings del banco en el panel.")
    run.linea("[sim] paquete %s | job: %s | timeout %d s%s" % (
        h, objetivo or "todos", timeout, " | settings: %s" % settings if settings else ""))
    hilo = threading.Thread(target=_ejecutar, args=(run, jobs, orden, settings), daemon=True)
    hilo.start()
    return run.id


def estado(run_id, offset=0):
    r = _RUNS.get(run_id)
    if r is None:
        raise SimError("run desconocido o expirado", 404)
    return r.a_dict(offset)


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
        matar_arbol(p)
    return {"ok": True, "estado": "cancelando"}


def reiniciar(zip_path):
    h, pkg = montar(zip_path)
    with _LOCK:
        if h in _ACTIVO:
            raise SimError("hay una simulación en curso: cancélala antes de reiniciar demo_out", 409)
    reiniciar_demo_out(pkg)
    return {"ok": True, "mensaje": "demo_out reiniciado"}


def base_visor(zip_path):
    h, pkg = montar(zip_path)
    return visor_base(pkg)
