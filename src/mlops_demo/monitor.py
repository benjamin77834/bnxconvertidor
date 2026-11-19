# -*- coding: utf-8 -*-
"""Monitoreo de recursos del runner (CPU / memoria) durante una simulacion o una corrida real.

Muestrea cada BNX_MONITOR_INTERVALO s (default 1) el proceso del runner y TODOS sus descendientes (JVM de Spark,
workers de Python): % de CPU (100% = un nucleo; sumado en todo el arbol), memoria RSS y, si se puede, CPU/memoria
del sistema y las tareas de Spark (statusTracker + executorList del statusStore). Sin dependencias obligatorias:
  1) psutil, si esta instalado (todos los SO);
  2) Linux: /proc/<pid>/stat, /proc/stat, /proc/meminfo;
  3) macOS/BSD: `ps -axo pid=,ppid=,time=,rss=` (tiempo de CPU acumulado con centesimas; se deriva por intervalo);
  4) Windows sin psutil: se omite con un aviso.
El muestreo corre en un HILO aparte (una lectura de /proc o un `ps` por segundo: < 1% de un nucleo).
BNX_MONITOR=0 lo desactiva. Si BNX_MONITOR_FILE esta definido se escribe un JSON por linea (muestras y marcas
inicio/fin de cada job) que la simulacion lee de forma incremental para la grafica en vivo.
Compatible con Python 3.8.
"""
import atexit
import json
import os
import re
import subprocess
import sys
import threading
import time


# ---------------------------------------------------------------------------
# Parsers y calculos puros (testeables sin procesos reales)
# ---------------------------------------------------------------------------
def parse_proc_stat(texto, clk_tck=100.0, page_kb=4.0):
    """/proc/<pid>/stat -> (ppid, cpu_segundos, rss_kb) o None. El nombre (comm) puede traer espacios y parentesis."""
    i = (texto or "").rfind(")")
    if i < 0:
        return None
    campos = texto[i + 2:].split()
    try:
        ppid = int(campos[1])
        utime, stime = int(campos[11]), int(campos[12])
        rss_paginas = int(campos[21])
    except (IndexError, ValueError):
        return None
    return ppid, (utime + stime) / float(clk_tck), rss_paginas * page_kb


def parse_cputime(txt):
    """'[[dd-]hh:]mm:ss[.cc]' (ps -o time) -> segundos."""
    txt = (txt or "").strip()
    if not txt:
        return 0.0
    dias = 0
    if "-" in txt:
        d, txt = txt.split("-", 1)
        dias = int(d)
    partes = txt.split(":")
    try:
        seg = float(partes[-1])
        mins = int(partes[-2]) if len(partes) > 1 else 0
        horas = int(partes[-3]) if len(partes) > 2 else 0
    except ValueError:
        return 0.0
    return dias * 86400 + horas * 3600 + mins * 60 + seg


def parse_ps(texto):
    """`ps -axo pid=,ppid=,time=,rss=` -> {pid: (ppid, cpu_segundos, rss_kb)}."""
    out = {}
    for ln in (texto or "").splitlines():
        p = ln.split()
        if len(p) < 4:
            continue
        try:
            out[int(p[0])] = (int(p[1]), parse_cputime(p[2]), int(p[3]))
        except ValueError:
            continue
    return out


def parse_cpu_total(texto):
    """Primera linea de /proc/stat -> (ocupado, total) en ticks."""
    for ln in (texto or "").splitlines():
        if ln.startswith("cpu "):
            v = [int(x) for x in ln.split()[1:9] if x.isdigit()]
            if len(v) < 4:
                return None
            idle = v[3] + (v[4] if len(v) > 4 else 0)
            total = sum(v)
            return total - idle, total
    return None


def parse_meminfo(texto):
    """/proc/meminfo -> (usada_mb, total_mb)."""
    d = {}
    for ln in (texto or "").splitlines():
        m = re.match(r"(\w+):\s+(\d+)", ln)
        if m:
            d[m.group(1)] = int(m.group(2))
    total = d.get("MemTotal", 0)
    libre = d.get("MemAvailable", d.get("MemFree", 0))
    return (total - libre) / 1024.0, total / 1024.0


def parse_vm_stat(texto, memsize_bytes):
    """vm_stat (macOS) -> (usada_mb, total_mb): total - (libres + inactivas + especulativas)."""
    m = re.search(r"page size of (\d+) bytes", texto or "")
    pag = int(m.group(1)) if m else 16384

    def n(nombre):
        mm = re.search(nombre + r":\s+(\d+)", texto or "")
        return int(mm.group(1)) if mm else 0
    libres = (n("Pages free") + n("Pages inactive") + n("Pages speculative")) * pag
    total = float(memsize_bytes or 0)
    return max(0.0, total - libres) / 1048576.0, total / 1048576.0


def descendientes(tabla, raiz):
    """{pid: ...} de `tabla` ({pid: (ppid, ...)}) que son `raiz` o descienden de ella."""
    hijos = {}
    for pid, v in tabla.items():
        hijos.setdefault(v[0], []).append(pid)
    out, pila = set(), [raiz]
    while pila:
        p = pila.pop()
        if p in out:
            continue
        out.add(p)
        pila.extend(hijos.get(p, []))
    return [p for p in out if p in tabla]


def cpu_pct(cpu_seg_delta, wall_seg):
    """% de CPU con 100% = un nucleo (varios nucleos suman >100)."""
    return 0.0 if wall_seg <= 0 else max(0.0, 100.0 * cpu_seg_delta / wall_seg)


def pct_del_total(cpu_pct_nucleo, nucleos):
    """% del total de la maquina/nucleos asignados (0..100)."""
    return 0.0 if not nucleos else min(100.0, cpu_pct_nucleo / float(nucleos))


def eficiencia(cpu_seg, wall_seg, nucleos):
    """cpu_time / (wall_time * nucleos asignados): 1.0 = todos los nucleos ocupados todo el tiempo."""
    return 0.0 if wall_seg <= 0 or not nucleos else cpu_seg / (wall_seg * float(nucleos))


def stats_de_muestras(muestras, t0, t1, nucleos):
    """CPU/memoria de un job a partir de las muestras con t0 <= t <= t1."""
    ms = [m for m in muestras if t0 <= m["t"] <= t1]
    wall = max(0.0, t1 - t0)
    if not ms:
        return {"wall": wall, "cpu_prom": 0.0, "cpu_pico": 0.0, "nuc_prom": 0.0, "nuc_pico": 0.0, "mem_pico": 0.0,
                "cpu_seg": 0.0, "eficiencia": 0.0, "muestras": 0}
    cpu_seg = sum(m["cpu"] * m.get("dt", 1.0) / 100.0 for m in ms)
    prom = sum(m["cpu"] for m in ms) / len(ms)
    pico = max(m["cpu"] for m in ms)
    return {"wall": wall, "cpu_prom": prom, "cpu_pico": pico, "nuc_prom": prom / 100.0, "nuc_pico": pico / 100.0,
            "mem_pico": max(m["rss"] for m in ms), "cpu_seg": cpu_seg,
            "eficiencia": eficiencia(cpu_seg, wall, nucleos), "muestras": len(ms)}


# ---------------------------------------------------------------------------
# Lectores del SO
# ---------------------------------------------------------------------------
def _leer_txt(ruta):
    try:
        with open(ruta, "r") as fh:
            return fh.read()
    except OSError:
        return ""


class _LectorProc(object):
    nombre = "/proc"

    def __init__(self):
        try:
            self.clk = float(os.sysconf("SC_CLK_TCK"))
            self.pag = os.sysconf("SC_PAGE_SIZE") / 1024.0
        except (ValueError, OSError, AttributeError):
            self.clk, self.pag = 100.0, 4.0
        self._cpu_prev = None

    def tabla(self):
        t = {}
        try:
            nombres = os.listdir("/proc")
        except OSError:
            return t
        for d in nombres:
            if d.isdigit():
                r = parse_proc_stat(_leer_txt("/proc/%s/stat" % d), self.clk, self.pag)
                if r:
                    t[int(d)] = r
        return t

    def sistema(self, dwall, ncpu):
        cur = parse_cpu_total(_leer_txt("/proc/stat"))
        pct = None
        if cur and self._cpu_prev and cur[1] > self._cpu_prev[1]:
            pct = 100.0 * (cur[0] - self._cpu_prev[0]) / (cur[1] - self._cpu_prev[1])
        self._cpu_prev = cur
        usada, total = parse_meminfo(_leer_txt("/proc/meminfo"))
        return pct, usada, total


class _LectorPs(object):
    nombre = "ps"

    def __init__(self):
        self._t = 0
        self._mem = (0.0, 0.0)
        self._total_prev = None

    def tabla(self):
        try:
            p = subprocess.run(["ps", "-axo", "pid=,ppid=,time=,rss="], stdout=subprocess.PIPE,
                               stderr=subprocess.DEVNULL, universal_newlines=True, timeout=10)
            return parse_ps(p.stdout)
        except (OSError, subprocess.SubprocessError):
            return {}

    def sistema(self, dwall, ncpu, tabla=None):
        pct = None
        if tabla:
            total = sum(v[1] for v in tabla.values())
            if self._total_prev is not None and dwall > 0:
                pct = min(100.0, 100.0 * max(0.0, total - self._total_prev) / dwall / max(1, ncpu))
            self._total_prev = total
        self._t += 1
        if self._t % 5 == 1:             # vm_stat cada ~5 muestras
            try:
                vm = subprocess.run(["vm_stat"], stdout=subprocess.PIPE, universal_newlines=True, timeout=5).stdout
                ms = subprocess.run(["sysctl", "-n", "hw.memsize"], stdout=subprocess.PIPE,
                                    universal_newlines=True, timeout=5).stdout
                self._mem = parse_vm_stat(vm, int(ms.strip() or 0))
            except (OSError, subprocess.SubprocessError, ValueError):
                pass
        return pct, self._mem[0], self._mem[1]


class _LectorPsutil(object):
    nombre = "psutil"

    def __init__(self, psutil):
        self.ps = psutil
        psutil.cpu_percent(None)

    def tabla(self):
        t = {}
        for p in self.ps.process_iter(["pid", "ppid", "cpu_times", "memory_info"]):
            i = p.info
            if i.get("cpu_times") is None or i.get("memory_info") is None:
                continue
            t[i["pid"]] = (i["ppid"], i["cpu_times"].user + i["cpu_times"].system, i["memory_info"].rss / 1024.0)
        return t

    def sistema(self, dwall, ncpu):
        vm = self.ps.virtual_memory()
        return self.ps.cpu_percent(None), (vm.total - vm.available) / 1048576.0, vm.total / 1048576.0


def elegir_lector():
    """psutil > /proc > ps > None (Windows sin psutil)."""
    if os.environ.get("BNX_MONITOR_BACKEND"):                  # para pruebas: psutil | proc | ps
        b = os.environ["BNX_MONITOR_BACKEND"]
        if b == "proc":
            return _LectorProc()
        if b == "ps":
            return _LectorPs()
    try:
        import psutil
        return _LectorPsutil(psutil)
    except Exception:
        pass
    if os.path.isdir("/proc") and os.path.isfile("/proc/self/stat"):
        return _LectorProc()
    if os.name != "nt":
        return _LectorPs()
    return None


# ---------------------------------------------------------------------------
class Monitor(object):
    def __init__(self, nucleos=None, intervalo=None, archivo=None, pid=None):
        try:
            self.intervalo = max(0.2, float(intervalo or os.environ.get("BNX_MONITOR_INTERVALO") or 1.0))
        except ValueError:
            self.intervalo = 1.0
        self.nucleos = nucleos or os.cpu_count() or 1
        self.ncpu = os.cpu_count() or 1
        self.archivo = archivo if archivo is not None else os.environ.get("BNX_MONITOR_FILE")
        self.pid = pid or os.getpid()
        self.muestras = []
        self.stats = {}                  # job -> stats
        self.trabajos = {}               # job -> (t0, tareas0, dur0)
        self.job = ""
        self.lector = elegir_lector()
        self.aviso = "" if self.lector else "monitoreo omitido: sin psutil ni /proc ni ps (instala psutil)"
        self._prev = None
        self._lock = threading.Lock()
        self._stop = threading.Event()
        self._hilo = None
        self._fh = None
        self._t_ini = time.time()
        self._sc = None

    # -- ciclo de vida --------------------------------------------------------------------------
    def iniciar(self):
        if self.lector is None or self._hilo is not None:
            return self
        if self.archivo:
            try:
                self._fh = open(self.archivo, "a")
            except OSError:
                self._fh = None
        self._hilo = threading.Thread(target=self._bucle, name="bnx-monitor", daemon=True)
        self._hilo.start()
        return self

    def detener(self):
        self._stop.set()
        if self._hilo is not None:
            self._hilo.join(timeout=3)
        if self._fh:
            try:
                self._fh.close()
            except OSError:
                pass
            self._fh = None

    def _bucle(self):
        self._tomar()
        while not self._stop.wait(self.intervalo):
            try:
                self._tomar()
            except Exception:
                pass

    def _escribir(self, obj):
        if self._fh:
            try:
                self._fh.write(json.dumps(obj) + "\n")
                self._fh.flush()
            except (OSError, ValueError):
                pass

    # -- una muestra ---------------------------------------------------------------------------------
    def _spark(self):
        """(tareas activas, tareas completadas acumuladas, ms de ejecucion de tareas acumulados) o (None, None, None)."""
        try:
            from pyspark import SparkContext
            sc = SparkContext._active_spark_context
            if sc is None:
                return None, None, None
            st = sc.statusTracker()
            act = 0
            for sid in st.getActiveStageIds():
                si = st.getStageInfo(sid)
                act += si.numActiveTasks if si else 0
            hechas = dur = 0
            lst = sc._jsc.sc().statusStore().executorList(False)
            for i in range(lst.size()):
                e = lst.apply(i)
                hechas += int(e.completedTasks())
                dur += int(e.totalDuration())
            return act, hechas, dur
        except Exception:
            return None, None, None

    def _tomar(self, forzar=False):
        if self.lector is None:
            return None
        ahora = time.time()
        tabla = self.lector.tabla()
        pids = descendientes(tabla, self.pid) if tabla else []
        cpu_por_pid = dict((p, tabla[p][1]) for p in pids)
        rss = sum(tabla[p][2] for p in pids) / 1024.0
        with self._lock:
            prev = self._prev
            self._prev = (ahora, cpu_por_pid)
            if prev is None:
                return None
            dwall = ahora - prev[0]
            if dwall < 0.2 * self.intervalo or dwall < 0.1:     # intervalo demasiado corto: ruido de cuantizacion
                self._prev = prev
                return None
            delta = 0.0
            for p, c in cpu_por_pid.items():
                antes = prev[1].get(p)
                if antes is None:
                    antes = 0.0 if c > self.intervalo * 2 else 0.0     # proceso nuevo: cuenta todo su CPU
                delta += max(0.0, c - antes)
            if isinstance(self.lector, _LectorPs):
                sis = self.lector.sistema(dwall, self.ncpu, tabla)
            else:
                sis = self.lector.sistema(dwall, self.ncpu)
            act, hechas, dur = self._spark()
            m = {"t": round(ahora, 3), "dt": round(dwall, 3), "cpu": round(min(cpu_pct(delta, dwall), 100.0 * self.ncpu * 1.1), 1),
                 "cpu_sis": None if sis[0] is None else round(sis[0], 1), "rss": round(rss, 1),
                 "mem_sis": round(sis[1], 0), "mem_tot": round(sis[2], 0), "act": act, "hechas": hechas,
                 "job": self.job, "n": self.nucleos, "ncpu": self.ncpu}
            self.muestras.append(m)
            if len(self.muestras) > 20000:
                del self.muestras[:5000]
        self._escribir(m)
        return m

    # -- por job -------------------------------------------------------------------------------
    def job_inicio(self, nombre):
        if self.lector is None:
            return
        self._tomar(forzar=True)
        _a, hechas, dur = self._spark()
        self.trabajos[nombre] = (time.time(), hechas, dur)
        self.job = nombre
        self._escribir({"ev": "inicio", "job": nombre, "t": round(time.time(), 3)})

    def job_fin(self, nombre, estado="OK"):
        if self.lector is None or nombre not in self.trabajos:
            return None
        self._tomar(forzar=True)
        t0, h0, d0 = self.trabajos.pop(nombre)
        t1 = time.time()
        with self._lock:
            ms = list(self.muestras)
        s = stats_de_muestras(ms, t0, t1, self.nucleos)
        _a, h1, d1 = self._spark()
        s["tareas"] = (h1 - h0) if (h1 is not None and h0 is not None) else None
        s["tareas_seg"] = ((d1 - d0) / 1000.0) if (d1 is not None and d0 is not None) else None
        self.stats[nombre] = s
        self.job = ""
        self._escribir({"ev": "fin", "job": nombre, "estado": estado, "t": round(t1, 3),
                        "stats": dict((k, (round(v, 3) if isinstance(v, float) else v)) for k, v in s.items())})
        return s

    # -- resumen ----------------------------------------------------------------------------------
    def resumen(self):
        with self._lock:
            ms = list(self.muestras)
        if not ms:
            return None
        prom = sum(m["cpu"] for m in ms) / len(ms)
        mas = max(self.stats.items(), key=lambda kv: kv[1]["cpu_seg"]) if self.stats else None
        return {"cpu_prom": prom, "efectivos": prom / 100.0, "pct_total": pct_del_total(prom, self.nucleos),
                "nucleos": self.nucleos, "ncpu": self.ncpu, "pct_maquina": pct_del_total(prom, self.ncpu),
                "mem_pico": max(m["rss"] for m in ms),
                "mas_pesado": mas[0] if mas else None, "mas_pesado_cpu_seg": mas[1]["cpu_seg"] if mas else 0.0,
                "muestras": len(ms)}

    def linea_resumen(self):
        r = self.resumen()
        if not r:
            return ""
        return ("CPU: promedio %.0f%% de %d nucleos (efectivos %.1f; %.0f%% de los %d de la maquina); "
                "memoria pico %.0f MB%s" % (
            r["pct_total"], r["nucleos"], r["efectivos"], r["pct_maquina"], r["ncpu"], r["mem_pico"],
            "; job mas pesado de CPU: %s (%.1f s de CPU)" % (r["mas_pesado"], r["mas_pesado_cpu_seg"])
            if r["mas_pesado"] else ""))


# ---------------------------------------------------------------------------
# Singleton para el runner
# ---------------------------------------------------------------------------
_MON = []


def activo():
    return os.environ.get("BNX_MONITOR", "1") not in ("0", "false", "no")


def obtener(nucleos=None):
    """Monitor unico del proceso (arranca en la primera llamada). None si BNX_MONITOR=0 o sin lector."""
    if not activo():
        return None
    if not _MON:
        m = Monitor(nucleos=nucleos)
        if m.lector is None:
            print("[monitor] " + m.aviso)
            _MON.append(None)
        else:
            m.iniciar()
            atexit.register(m.detener)
            _MON.append(m)
    return _MON[0]


def reset():
    """Pruebas: olvida el singleton."""
    if _MON and _MON[0] is not None:
        _MON[0].detener()
    del _MON[:]


# ---------------------------------------------------------------------------
# Lectura incremental del archivo de muestras (la usa la simulacion, sin importar el paquete)
# ---------------------------------------------------------------------------
def leer_incremental(ruta, offset=0, maximo=2000):
    """(lineas JSON parseadas, nuevo offset en bytes) de un archivo .jsonl; ignora una ultima linea incompleta."""
    try:
        with open(ruta, "rb") as fh:
            fh.seek(max(0, int(offset or 0)))
            datos = fh.read(4 * 1024 * 1024)
    except OSError:
        return [], int(offset or 0)
    fin = datos.rfind(b"\n")
    if fin < 0:
        return [], int(offset or 0)
    out = []
    for ln in datos[:fin].split(b"\n"):
        try:
            out.append(json.loads(ln.decode("utf-8", "replace")))
        except ValueError:
            continue
    nuevo = int(offset or 0) + fin + 1
    if len(out) > maximo:
        out = out[-maximo:]
    return out, nuevo
