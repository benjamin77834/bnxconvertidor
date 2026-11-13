"""Ejecucion REAL de orquestaciones desde la GUI (en segundo plano).

El servidor no ejecuta nada en su propio proceso: lanza `python -m src.orquestador ejecutar
... --ejecutar` como SUBPROCESO (grupo de procesos propio, para poder cancelarlo con todo su
arbol), con la salida a un archivo de log que la GUI lee de forma incremental. El estado de
cada paso viaja en lineas `##BNX {...}` del propio log (ver orquestador._evento).

Windows (Anaconda, consola cp1252): el subproceso corre con PYTHONUTF8/PYTHONIOENCODING=utf-8,
CREATE_NEW_PROCESS_GROUP y se cancela con `taskkill /T /F`; en POSIX con start_new_session +
killpg.
"""
import contextlib
import io
import json
import os
import re
import secrets
import shutil
import signal
import subprocess
import sys
import tempfile
import threading
import time

from src import orquestador as orq

ROOT = orq._ROOT
RUN_ID_RE = re.compile(r"^\d{8}-\d{6}-[0-9a-f]{6}$")
_ID_RE = re.compile(r"^[\w.\-]{1,64}$")
_MAX_RUNS = 30
_LOCK = threading.Lock()
RUNS = {}          # run_id -> Run


class RunError(Exception):
    """Error de validacion/estado con codigo HTTP sugerido."""

    def __init__(self, msg, status=400, extra=None):
        super().__init__(msg)
        self.status, self.extra = status, extra or {}


# ---------------------------------------------------------------------------
# Validacion de la solicitud
# ---------------------------------------------------------------------------

def _ids_plan(plan):
    return {s["id"] for s in plan.get("steps", [])}


def validar_solicitud(plan, data, crear_base=False):
    """Normaliza y valida los parametros de ejecucion. Devuelve un dict o lanza RunError."""
    ej = orq._ej(plan)
    modo = data.get("modo") or ej.get("modo") or "python"
    if modo not in ("python", "spark-submit"):
        raise RunError("modo debe ser python o spark-submit")
    sa = data.get("spark_args")
    if sa is None:
        sa = list(ej.get("spark_args") or [])
    if isinstance(sa, str):
        import shlex
        sa = shlex.split(sa, posix=(os.name != "nt"))
    if (not isinstance(sa, list) or len(sa) > 60
            or not all(isinstance(x, str) and len(x) < 2000 and not re.search(r"[\x00\r\n]", x) for x in sa)):
        raise RunError("spark_args debe ser una lista de textos (sin saltos de linea)")
    paso, desde = data.get("paso") or None, data.get("desde_paso") or data.get("desde") or None
    if paso and desde:
        raise RunError("use 'paso' o 'desde_paso', no ambos")
    for x in (paso, desde):
        if x is not None and (not isinstance(x, str) or not _ID_RE.match(x) or x not in _ids_plan(plan)):
            raise RunError(f"paso inexistente: {x!r}")
    permitir = data.get("permitir_remotos") is True
    base, err = orq.validar_base_path(data.get("base_path") or "", crear=crear_base)
    if err:
        raise RunError(f"base_path: {err}")
    if "://" in base and not permitir:
        raise RunError("un base_path s3:// usa la nube: marque 'permitir pasos remotos/nube' "
                       "o use una carpeta local")
    return {"modo": modo, "spark_args": sa, "paso": paso, "desde": desde,
            "permitir_remotos": permitir, "base_path": base}


def dry_run(plan, p):
    """Texto del dry-run (lista de comandos) con los mismos parametros que la ejecucion real."""
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        ok = orq.ejecutar(plan, real=False, modo=p["modo"], base_path=p["base_path"],
                          solo=p["paso"], desde=p["desde"], spark_args=p["spark_args"])
    return bool(ok), buf.getvalue()


# ---------------------------------------------------------------------------
# Preflight
# ---------------------------------------------------------------------------

def _chk(id_, nivel, msg, ayuda=None):
    return {"id": id_, "nivel": nivel, "msg": msg, **({"ayuda": ayuda} if ayuda else {})}


def _java():
    """(ruta_java|None, version_o_error)."""
    home = os.environ.get("JAVA_HOME")
    cands = []
    if home:
        cands.append(os.path.join(home, "bin", "java.exe" if os.name == "nt" else "java"))
    w = shutil.which("java")
    if w:
        cands.append(w)
    for c in cands:
        if os.path.isfile(c):
            try:
                r = subprocess.run([c, "-version"], capture_output=True, text=True, timeout=20,
                                   encoding="utf-8", errors="replace")
                txt = ((r.stderr or "") + (r.stdout or "")).strip().splitlines()
                if r.returncode == 0 and txt:
                    return c, txt[0]
            except (OSError, subprocess.TimeoutExpired):
                continue
    return None, "no se encontro java"


def _usa_jobs(plan, nivel=0):
    for s in plan.get("steps", []):
        a = s.get("action") or {}
        if s.get("enabled", True) and a.get("type") == "graph":
            return True
        if s.get("enabled", True) and a.get("type") == "plan" and nivel < 3:
            try:
                with open(orq._ruta_plan(a["target"]), "r", encoding="utf-8") as f:
                    if _usa_jobs(json.load(f), nivel + 1):
                        return True
            except (OSError, ValueError, KeyError):
                pass
    return False


def _tipos_pasos(plan, p, nivel=0, acc=None):
    """{'scripts': n, 'remotos': [..]} de los pasos que correrian (incluye sub-planes)."""
    acc = acc if acc is not None else {"scripts": 0, "remotos": []}
    sel = orq.seleccion_pasos(plan, p["paso"], p["desde"]) if nivel == 0 else None
    for s in plan.get("steps", []):
        if not s.get("enabled", True) or (sel is not None and s["id"] not in sel):
            continue
        a = s.get("action") or {}
        if a.get("type") == "script" or (a.get("type") == "shell" and
                                         re.search(r"\.(ksh|sh)\b", a.get("comando", ""))):
            acc["scripts"] += 1
        elif a.get("type") in orq.TIPOS_NUEVOS and orq.ubicacion_de(a) != "local":
            acc["remotos"].append(f"{s['name']} ({orq.ubicacion_de(a)}/{a['type']})")
        elif a.get("type") == "plan" and nivel < 3:
            try:
                with open(orq._ruta_plan(a["target"]), "r", encoding="utf-8") as f:
                    _tipos_pasos(json.load(f), p, nivel + 1, acc)
            except (OSError, ValueError, KeyError):
                pass
    return acc


def preflight(plan, p):
    """Chequeos previos. nivel: ok | warn | error (error = no se puede ejecutar)."""
    out = []
    usa_jobs = _usa_jobs(plan)
    out.append(_chk("python", "ok", f"Python del servidor: {sys.executable}"))
    if usa_jobs:
        import importlib.util
        if importlib.util.find_spec("pyspark") is None:
            out.append(_chk("pyspark", "error", "pyspark no esta instalado en el Python del servidor",
                            "Instale en este mismo entorno: pip install pyspark  "
                            "(o conda install -c conda-forge pyspark)"))
        else:
            try:
                from importlib.metadata import version
                v = version("pyspark")
            except Exception:
                v = "?"
            out.append(_chk("pyspark", "ok", f"pyspark {v} importable"))
        java, info = _java()
        if java:
            out.append(_chk("java", "ok", f"Java: {info} ({java})"))
        else:
            out.append(_chk("java", "error", "Java no encontrado (Spark lo necesita)",
                            "Instale un JDK 17 (o 11) y defina JAVA_HOME; verifique con: java -version"))
        if os.name == "nt":
            hh = os.environ.get("HADOOP_HOME") or os.environ.get("hadoop.home.dir")
            wu = os.path.join(hh, "bin", "winutils.exe") if hh else None
            if wu and os.path.isfile(wu):
                out.append(_chk("winutils", "ok", f"HADOOP_HOME={hh} (winutils.exe presente)"))
            else:
                out.append(_chk(
                    "winutils", "warn",
                    "Falta HADOOP_HOME\\bin\\winutils.exe: en Windows Spark lo necesita para escribir parquet",
                    "Descargue winutils.exe y hadoop.dll de la version de Hadoop de su Spark, copielos a "
                    "C:\\hadoop\\bin y defina HADOOP_HOME=C:\\hadoop (y agregue %HADOOP_HOME%\\bin al PATH). "
                    "Puede continuar, pero los jobs que escriben parquet probablemente fallen."))
        if p["modo"] == "spark-submit":
            ss = orq._spark_submit_bin(orq._ej(plan))
            if shutil.which(ss) or os.path.isfile(ss):
                out.append(_chk("spark-submit", "ok", f"spark-submit: {ss}"))
            else:
                out.append(_chk("spark-submit", "error", "spark-submit no encontrado",
                                "Instale pyspark (trae pyspark/bin/spark-submit) o defina SPARK_HOME / PATH, "
                                "o use el modo python."))
    base = p["base_path"]
    if "://" not in base:
        if os.path.isdir(base):
            out.append(_chk("base_path", "ok", f"base_path: {base}"))
        else:
            out.append(_chk("base_path", "ok", f"base_path: {base} (se creara)"))
        if usa_jobs:
            try:
                falt = orq.entradas_faltantes(plan, base, orq.seleccion_pasos(plan, p["paso"], p["desde"]))
            except (ValueError, OSError):
                falt = []
            if falt:
                out.append(_chk("entradas", "warn",
                                f"Faltan {len(falt)} dataset(s) de entrada; los jobs esperan exactamente: "
                                + ", ".join(os.path.join(base, *r.split("/")) for r in falt[:6])
                                + ("..." if len(falt) > 6 else ""),
                                "La ejecucion FALLARA en esos jobs (PATH_NOT_FOUND). Pulse '🧪 Datos sintéticos' "
                                "(con este mismo base path) para generarlos, o copie sus datos reales "
                                "con ese nombre exacto a esa carpeta."))
            else:
                out.append(_chk("entradas", "ok", "Datos de entrada presentes en <base>/raw"))
    tipos = _tipos_pasos(plan, p)
    if tipos["scripts"] and not (shutil.which("ksh") or shutil.which("bash")):
        out.append(_chk("shell", "warn", f"{tipos['scripts']} script(s) .ksh/.sh y no hay ksh ni bash",
                        "Se omitiran. Instale Git Bash o WSL si necesita ejecutarlos."))
    if tipos["remotos"]:
        if p["permitir_remotos"]:
            out.append(_chk("remotos", "warn", "Se EJECUTARAN pasos remotos/nube: " + "; ".join(tipos["remotos"][:5])))
        else:
            out.append(_chk("remotos", "ok", "Se omitiran (sin permiso) pasos remotos/nube: "
                            + "; ".join(tipos["remotos"][:5])))
    return out


# ---------------------------------------------------------------------------
# Ejecucion en segundo plano
# ---------------------------------------------------------------------------

class Run:
    def __init__(self, plan_abs, params, cmd, logpath, proc):
        self.id = os.path.basename(logpath)[:-4]
        self.plan, self.params, self.cmd, self.logpath, self.proc = plan_abs, params, cmd, logpath, proc
        self.inicio, self.fin, self.rc = time.time(), None, None
        self.cancelado = False
        self.pasos, self.subpasos = {}, {}
        self._ev_off = 0
        self._lock = threading.Lock()

    def corriendo(self):
        return self.proc.poll() is None

    def _scan(self):
        """Lee del log las lineas ##BNX nuevas (solo lineas completas)."""
        with self._lock:
            try:
                with open(self.logpath, "rb") as f:
                    f.seek(self._ev_off)
                    data = f.read()
            except OSError:
                return
            fin = data.rfind(b"\n") + 1 if self.corriendo() else len(data)
            for ln in data[:fin].splitlines():
                if ln.startswith(b"##BNX "):
                    try:
                        ev = json.loads(ln[6:].decode("utf-8", "replace"))
                        (self.subpasos if "/" in ev["ruta"] else self.pasos)[ev["ruta"]] = ev["estado"]
                    except (ValueError, KeyError):
                        pass
            self._ev_off += fin

    def estado(self):
        if self.corriendo():
            return "corriendo"
        if self.cancelado:
            return "cancelado"
        return "ok" if self.proc.returncode == 0 else "fallo"


def _limpiar_antiguos():
    if len(RUNS) <= _MAX_RUNS:
        return
    for rid in sorted(RUNS)[: len(RUNS) - _MAX_RUNS]:
        if not RUNS[rid].corriendo():
            with contextlib.suppress(OSError):
                os.remove(RUNS[rid].logpath)
            RUNS.pop(rid, None)


def iniciar(plan_abs, p):
    """Lanza la ejecucion. RunError(409) si el plan (o el mismo base_path) ya esta corriendo."""
    with _LOCK:
        for r in RUNS.values():
            if r.corriendo():
                if r.plan == plan_abs:
                    raise RunError("este plan ya se esta ejecutando", 409, {"run": r.id})
                if r.params["base_path"] == p["base_path"]:
                    raise RunError("otra ejecucion en curso usa el mismo base_path", 409, {"run": r.id})
        logdir = os.path.join(tempfile.gettempdir(), "bnx_runs")
        os.makedirs(logdir, exist_ok=True)
        rid = time.strftime("%Y%m%d-%H%M%S") + "-" + secrets.token_hex(3)
        logpath = os.path.join(logdir, rid + ".log")
        rel = os.path.relpath(plan_abs, ROOT)
        cmd = [sys.executable, "-u", "-m", "src.orquestador", "ejecutar", rel, "--ejecutar",
               "--modo", p["modo"], f"--base-path={p['base_path']}",
               "--spark-args-json", json.dumps(p["spark_args"])]
        if p["paso"]:
            cmd.append(f"--paso={p['paso']}")
        if p["desde"]:
            cmd.append(f"--desde={p['desde']}")
        if not p["permitir_remotos"]:
            cmd.append("--sin-remotos")
        env = dict(os.environ)
        env.update({"PYTHONIOENCODING": "utf-8", "PYTHONUTF8": "1", "PYTHONUNBUFFERED": "1",
                    "BNX_EVENTOS": "1"})
        if os.name == "nt":
            env["PYSPARK_PYTHON"] = env["PYSPARK_DRIVER_PYTHON"] = sys.executable
            kw = {"creationflags": subprocess.CREATE_NEW_PROCESS_GROUP | 0x08000000}  # sin ventana
        else:
            env.setdefault("PYSPARK_PYTHON", sys.executable)
            env.setdefault("PYSPARK_DRIVER_PYTHON", sys.executable)
            kw = {"start_new_session": True}
        with open(logpath, "wb") as lf:
            lf.write(("[*] " + " ".join(cmd[1:]) + "\n").encode("utf-8", "replace"))
        logf = open(logpath, "ab")
        try:
            proc = subprocess.Popen(cmd, cwd=ROOT, env=env, stdin=subprocess.DEVNULL,
                                    stdout=logf, stderr=subprocess.STDOUT, **kw)
        except OSError as e:
            raise RunError(f"no se pudo lanzar el proceso: {e}", 500)
        finally:
            logf.close()
        run = Run(plan_abs, p, cmd, logpath, proc)
        RUNS[run.id] = run
        _limpiar_antiguos()
        return run


def _get(rid):
    if not isinstance(rid, str) or not RUN_ID_RE.match(rid) or rid not in RUNS:
        raise RunError("ejecucion no encontrada", 404)
    return RUNS[rid]


def _salidas(run, limite=200):
    base = run.params["base_path"]
    if "://" in base:
        return base + "/output", []
    d = os.path.join(base, "output")
    items = []
    if os.path.isdir(d):
        for dp, _, fs in os.walk(d):
            for fn in sorted(fs):
                if fn.startswith((".", "_")) or fn.endswith(".crc"):
                    continue
                fp = os.path.join(dp, fn)
                items.append({"ruta": os.path.relpath(fp, base).replace(os.sep, "/"),
                              "bytes": os.path.getsize(fp)})
                if len(items) >= limite:
                    return d, items
    return d, items


def estado(rid, offset=0):
    run = _get(rid)
    run._scan()
    try:
        offset = max(0, int(offset))
    except (TypeError, ValueError):
        offset = 0
    texto, nuevo = "", offset
    try:
        with open(run.logpath, "rb") as f:
            f.seek(offset)
            data = f.read(256 * 1024)
    except OSError:
        data = b""
    if data:
        if run.corriendo() and len(data) < 256 * 1024:
            data = data[: data.rfind(b"\n") + 1]    # solo lineas completas mientras corre
        nuevo = offset + len(data)
        lineas = [ln for ln in data.decode("utf-8", "replace").splitlines(True) if not ln.startswith("##BNX ")]
        texto = "".join(lineas)
    corriendo = run.corriendo()
    pasos, subpasos = dict(run.pasos), dict(run.subpasos)
    if not corriendo:
        run.fin = run.fin or time.time()
        run.rc = run.proc.returncode
        for dic in (pasos, subpasos):
            for k, v in list(dic.items()):
                if v == "corriendo":
                    dic[k] = "cancelado" if run.cancelado else "fallo"
    out = {"ok": True, "run": run.id, "estado": run.estado(), "rc": run.proc.returncode if not corriendo else None,
           "pasos": pasos, "subpasos": subpasos, "log": texto, "offset": nuevo,
           "segundos": round((run.fin or time.time()) - run.inicio, 1),
           "plan": os.path.relpath(run.plan, ROOT), "base_path": run.params["base_path"]}
    if not corriendo and nuevo >= os.path.getsize(run.logpath):
        d, items = _salidas(run)
        out["salidas_dir"], out["salidas"] = d, items
    return out


def activo():
    """Ejecucion en curso mas reciente (para recuperar el panel al recargar la pagina)."""
    vivos = [r for r in RUNS.values() if r.corriendo()]
    return max(vivos, key=lambda r: r.inicio) if vivos else None


def _matar_arbol(proc):
    if proc.poll() is not None:
        return
    if os.name == "nt":
        subprocess.run(["taskkill", "/PID", str(proc.pid), "/T", "/F"], capture_output=True)
    else:
        try:
            os.killpg(proc.pid, signal.SIGTERM)
        except (ProcessLookupError, PermissionError):
            pass
        for _ in range(30):
            if proc.poll() is not None:
                break
            time.sleep(0.1)
        if proc.poll() is None:
            with contextlib.suppress(ProcessLookupError, PermissionError):
                os.killpg(proc.pid, signal.SIGKILL)
    with contextlib.suppress(subprocess.TimeoutExpired):
        proc.wait(timeout=10)


def cancelar(rid):
    run = _get(rid)
    if not run.corriendo():
        return {"ok": True, "estado": run.estado(), "mensaje": "ya habia terminado"}
    run.cancelado = True
    _matar_arbol(run.proc)
    with open(run.logpath, "ab") as f:
        f.write("\n[x] Ejecucion CANCELADA por el usuario\n".encode("utf-8"))
    return {"ok": True, "estado": "cancelado"}
