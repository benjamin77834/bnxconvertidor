# src/presentacion.py
"""
Presentaciones ejecutivas de 2 laminas como maximo, separadas:
  grafos: migracion de grafos Ab Initio -> PySpark (cifras reales de output/<proyecto>/reporte_lote.md,
          clasificador de src/migracion_grafos.py, orquestaciones; estimacion con parametros editables).
  mlops:  Framework MLOps v2 (cifras del paquete armado con tools/construir_paquete_mlops.py en modo
          lectura y de la ultima simulacion registrada).
Lamina 1 = mensaje ejecutivo (titular, cifras grandes, que se necesita); lamina 2 = como se logra y plan.
Cada lamina es una lista de primitivas (rect/text) sobre un lienzo de 960x540 pt; el mismo dibujo se usa
para la vista previa (SVG), el .pptx (python-pptx) y el .pdf (reportlab).
Un dato que no existe se muestra como "sin dato": nunca se estima.

Todo pasa por handle(action, data) -> (status_http, dict). Compatible con Python 3.8.
Los archivos generados se guardan en data/presentacion/ (fuera de git; BNX_PRESENTACION_DIR).
"""
import io
import json
import math
import os
import re
from datetime import date, datetime

from src import migracion_grafos as mg
from src import pset_map

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
W, H = 960, 540
SIN_DATO = "sin dato"
N_LAMINAS = 2

COL_FONDO = "#0f2a43"
COL_ACENTO = "#1d9bd1"
COL_TEXTO = "#1f2937"
COL_SUAVE = "#eef3f8"
COL_NIVEL = {"Simple": "#22a06b", "Medio": "#e8a317", "Alto": "#d64545"}


class PresentacionError(ValueError):
    pass


# ---------------------------------------------------------------------------
# Datos reales
# ---------------------------------------------------------------------------
def proyectos_disponibles():
    """Proyectos de output/ con reporte_lote.md: [{nombre, tiene_abinitio, grafos_ok}]."""
    base = os.path.join(_ROOT, "output")
    res = []
    if not os.path.isdir(base):
        return res
    for n in sorted(os.listdir(base)):
        if not os.path.isfile(os.path.join(base, n, "reporte_lote.md")):
            continue
        filas = _leer_reporte(os.path.join(base, n, "reporte_lote.md"))
        res.append({"nombre": n, "tiene_abinitio": os.path.isdir(os.path.join(_ROOT, "abinitio", n)),
                    "grafos_ok": sum(1 for f in filas if f["ok"])})
    return res


def _leer_reporte(path):
    """Filas de la tabla de reporte_lote.md: [{grafo, ok, accuracy|None}]."""
    filas = []
    try:
        with open(path, "r", encoding="utf-8", errors="replace") as f:
            lineas = f.read().splitlines()
    except OSError:
        return filas
    for ln in lineas:
        if not ln.startswith("|"):
            continue
        c = [x.strip() for x in ln.strip().strip("|").split("|")]
        if len(c) < 3 or not c[0].lower().endswith((".mp", ".plan")):
            continue  # encabezado, separador u otra fila
        try:
            acc = float(c[2])
        except ValueError:
            acc = None
        filas.append({"grafo": c[0], "ok": c[1].lower() in ("si", "sí", "ok", "true"), "accuracy": acc})
    return filas


def _contar_salidas_ok(carpeta):
    """Marcadores _SUCCESS de Spark bajo la carpeta (evidencia de que un job escribio su salida)."""
    n = visitados = 0
    for _r, _d, files in os.walk(carpeta):
        for f in files:
            visitados += 1
            if f == "_SUCCESS":
                n += 1
        if visitados > 50000:
            break
    return n


def _norm(nombre):
    return pset_map._norm_name(nombre).lower()


def _con_plan_pset(mapa):
    """Grafos (nombre normalizado en minusculas) que instancia algun pset o usa algun plan, segun pset_map."""
    if not mapa:
        return set()
    con = {k.lower() for k, v in mapa["instances"].items() if v}
    for e in mapa["edges"]:
        if e["type"] == "usa" and mapa["nodes"].get(e["from"], {}).get("kind") == "plan":
            con.add(e["to"].lower())
    return con


def _proyecto(nombre):
    if not re.match(r"^[\w.\-]+$", nombre or "") or nombre in (".", ".."):
        raise PresentacionError("proyecto invalido: %r" % (nombre,))
    out = os.path.join(_ROOT, "output", nombre)
    if not os.path.isfile(os.path.join(out, "reporte_lote.md")):
        raise PresentacionError("el proyecto no tiene output/%s/reporte_lote.md" % nombre)
    ab = os.path.join(_ROOT, "abinitio", nombre)
    filas = _leer_reporte(os.path.join(out, "reporte_lote.md"))
    conv = [f for f in filas if f["ok"]]
    accs = [f["accuracy"] for f in conv if f["accuracy"] is not None]
    p = {"nombre": nombre, "reportados": len(filas), "convertidos": len(conv),
         "accuracy": round(sum(accs) / len(accs), 1) if accs else None,
         "niveles": {"Simple": 0, "Medio": 0, "Alto": 0}, "sin_clasificar": 0,
         "orquestaciones": 0, "dags": 0, "salidas_ok": 0, "psets_ligados": 0,
         "sin_pset": 0, "faltantes": 0, "_graficos": []}
    mapa = None
    if os.path.isdir(ab):
        try:
            mapa = pset_map.scan(ab)
        except Exception:  # noqa: BLE001
            mapa = None
    con_plan = _con_plan_pset(mapa)
    for f in conv:
        mp = os.path.join(ab, f["grafo"])
        nivel = None
        if os.path.isfile(mp):
            try:
                nivel = mg.clasificar(mg.analizar_grafo(mp)["metricas"])["nivel"]
            except Exception:  # noqa: BLE001 - un .mp raro no debe tumbar la presentacion
                nivel = None
        if nivel in p["niveles"]:
            p["niveles"][nivel] += 1
        else:
            p["sin_clasificar"] += 1
        p["_graficos"].append((_norm(f["grafo"]), nivel, (_norm(f["grafo"]) in con_plan) if (mapa and nivel) else None))
    try:
        names = os.listdir(out)
    except OSError:
        names = []
    p["orquestaciones"] = sum(1 for n in names if n.startswith("orquestacion_") and n.endswith(".json"))
    p["dags"] = sum(1 for n in names if n.startswith("dag_") and n.endswith(".py"))
    p["salidas_ok"] = _contar_salidas_ok(out)
    if mapa:
        try:
            p["psets_ligados"] = sum(len(v) for v in mapa["instances"].values())
            p["sin_pset"] = len(mapa["graphs_without_pset"])
            p["faltantes"] = len(mapa["missing"])
        except Exception:  # noqa: BLE001
            pass
    return p


def recolectar(proyectos):
    """Cifras reales de los proyectos elegidos. Un grafo repetido en dos proyectos cuenta una vez."""
    if not isinstance(proyectos, (list, tuple)) or not proyectos:
        raise PresentacionError("elige al menos un proyecto")
    ps, vistos = [], {}
    for n in proyectos:
        p = _proyecto(str(n))
        for nm, nivel, con in p.pop("_graficos"):
            if nm not in vistos or (vistos[nm][1] is None and con is not None):
                vistos[nm] = (nivel, con)
        ps.append(p)
    niv = {k: 0 for k in mg.NIVELES}
    sin = 0
    alto = {"con": 0, "sin": 0, "sd": 0}  # Alto: con plan/pset, sin plan/pset, sin dato
    for nivel, con in vistos.values():
        if nivel in niv:
            niv[nivel] += 1
            if nivel == "Alto":
                alto["sd" if con is None else ("con" if con else "sin")] += 1
        else:
            sin += 1
    accs = []
    for p in ps:
        if p["accuracy"] is not None:
            accs.append((p["accuracy"], p["convertidos"]))
    peso = sum(c for _a, c in accs)
    acc_total = round(sum(a * c for a, c in accs) / peso, 1) if peso else None
    clasif = sum(niv.values())
    return {
        "proyectos": ps,
        "total": {
            "convertidos_suma": sum(p["convertidos"] for p in ps),
            "convertidos": len(vistos),
            "accuracy": acc_total,
            "niveles": niv,
            "alto_con_plan": alto["con"], "alto_sin_plan": alto["sin"], "alto_sin_dato": alto["sd"],
            "clasificados": clasif,
            "sin_clasificar": sin,
            "porcentajes": {k: (round(100.0 * v / clasif, 1) if clasif else None) for k, v in niv.items()},
            "orquestaciones": sum(p["orquestaciones"] for p in ps),
            "dags": sum(p["dags"] for p in ps),
            "salidas_ok": sum(p["salidas_ok"] for p in ps),
            "proyectos_con_salidas_ok": sum(1 for p in ps if p["salidas_ok"]),
            "psets_ligados": sum(p["psets_ligados"] for p in ps),
            "sin_pset": sum(p["sin_pset"] for p in ps),
            "faltantes": sum(p["faltantes"] for p in ps),
        },
    }


# ---------------------------------------------------------------------------
# Estimacion de esfuerzo
# ---------------------------------------------------------------------------
PARAMS_BASE = {
    "n_simple": None, "n_medio": None, "n_alto": None,  # None = los clasificados reales
    "horas_simple": 2.0, "horas_medio": 2.0,            # horas de 1 persona por grafo tras el convertidor
    "auto_simple": 80.0, "auto_medio": 80.0, "auto_alto": 30.0,  # % que deja listo el convertidor
    "alto_modo": "por_grafo",                            # "por_grafo" o "total" (punto abierto)
    "alto_horas": 80.0,                                  # 2 semanas x 40 h de 1 persona, solo muy complejos con plan/pset
    "n_alto_plan": None,                                 # None = los Alto con plan/pset reales
    "alto_sin_plan_horas": 40.0,                         # PENDIENTE DE CONFIRMAR: complejo sin plan/pset (supuesto: 1 semana)
    "horas_semana": 40.0, "equipo": 1.0,
    "manual_simple": 10.0, "manual_medio": 10.0,         # supuesto: todo a mano, horas por grafo
    "manual_alto": 114.0,                                # supuesto: en el mismo modo que alto_horas
}
_ENTEROS = ("n_simple", "n_medio", "n_alto", "n_alto_plan")
_PORC = ("auto_simple", "auto_medio", "auto_alto")
MODOS = ("total", "por_grafo")


def normalizar_params(entrada, reales=None):
    """Parametros validados (floats >= 0). Los n_* vacios toman los clasificados reales."""
    e = entrada if isinstance(entrada, dict) else {}
    p = dict(PARAMS_BASE)
    for k in p:
        v = e.get(k)
        if v is None or v == "":
            continue
        if k == "alto_modo":
            if v not in MODOS:
                raise PresentacionError("alto_modo debe ser 'total' o 'por_grafo'")
            p[k] = v
            continue
        try:
            x = float(v)
        except (TypeError, ValueError):
            raise PresentacionError("valor no numerico en '%s'" % k)
        if math.isnan(x) or math.isinf(x) or x < 0:
            raise PresentacionError("'%s' debe ser un numero >= 0" % k)
        if k in _PORC and x > 100:
            raise PresentacionError("'%s' debe estar entre 0 y 100" % k)
        p[k] = x
    if p["horas_semana"] <= 0:
        raise PresentacionError("'horas_semana' debe ser mayor que 0")
    if p["equipo"] < 1:
        raise PresentacionError("'equipo' debe ser al menos 1")
    base = (reales or {}).get("niveles", {})
    reales_t = reales or {}
    for k, nv in zip(_ENTEROS, mg.NIVELES):
        if p[k] is None:
            p[k] = base.get(nv, 0)
        p[k] = int(round(p[k]))
    if p["n_alto_plan"] is None:
        p["n_alto_plan"] = min(reales_t.get("alto_con_plan", 0), p["n_alto"])
    p["n_alto_plan"] = int(round(p["n_alto_plan"]))
    if p["n_alto_plan"] > p["n_alto"]:
        raise PresentacionError("'n_alto_plan' no puede superar a los grafos Alto")
    p["n_alto_sin_dato"] = min(reales_t.get("alto_sin_dato", 0), p["n_alto"] - p["n_alto_plan"])
    return p


def estimar(p):
    """Horas, semanas y ahorro. p viene de normalizar_params."""
    n = {"Simple": p["n_simple"], "Medio": p["n_medio"], "Alto": p["n_alto"]}
    por_grafo = p["alto_modo"] == "por_grafo"
    n_plan = p["n_alto_plan"]
    n_sin = n["Alto"] - n_plan  # complejos sin plan/pset (incluye los sin dato)

    def _grupo(cant, horas):
        return (cant * horas) if por_grafo else (horas if cant else 0.0)
    h_plan, h_sin = _grupo(n_plan, p["alto_horas"]), _grupo(n_sin, p["alto_sin_plan_horas"])
    h = {"Simple": n["Simple"] * p["horas_simple"], "Medio": n["Medio"] * p["horas_medio"], "Alto": h_plan + h_sin}
    m = {"Simple": n["Simple"] * p["manual_simple"], "Medio": n["Medio"] * p["manual_medio"],
         "Alto": (n["Alto"] * p["manual_alto"]) if por_grafo else (p["manual_alto"] if n["Alto"] else 0.0)}
    total, manual = sum(h.values()), sum(m.values())
    sem_persona = total / p["horas_semana"]
    ahorro = manual - total
    return {
        "grafos": n, "alto_plan": n_plan, "alto_sin_plan": n_sin,
        "horas_alto_plan": round(h_plan, 1), "horas_alto_sin_plan": round(h_sin, 1), "horas": {k: round(v, 1) for k, v in h.items()}, "horas_total": round(total, 1),
        "horas_manual": {k: round(v, 1) for k, v in m.items()}, "horas_manual_total": round(manual, 1),
        "semanas_persona": round(sem_persona, 2),
        "semanas_calendario": round(sem_persona / p["equipo"], 2),
        "ahorro_horas": round(ahorro, 1),
        "ahorro_pct": round(100.0 * ahorro / manual, 1) if manual else None,
    }


# ---------------------------------------------------------------------------
# Laminas (contenido) y dibujo (primitivas)
# ---------------------------------------------------------------------------
def _fmt(v, suf=""):
    if v is None:
        return SIN_DATO
    if isinstance(v, float) and v == int(v):
        v = int(v)
    return "%s%s" % (v, suf)


def _num(v):
    """Numero compacto en espanol claro: 12.0 -> '12', 12.34 -> '12.3'."""
    if isinstance(v, float):
        v = round(v, 1)
        return str(int(v)) if v == int(v) else str(v)
    return str(v)




# ---------------------------------------------------------------------------
# Datos del Framework MLOps v2 (solo lectura del proyecto; cifras verificables)
# ---------------------------------------------------------------------------
_RE_PKG = re.compile(r"\[tool\]\s+(con|sin) PySpark:\s+\S+\s+\((\d+) MB\)")
_RE_LIB = re.compile(r"^\[tool\]\s+(OK|PARCHEABLE|BLOQUEADO)\s+(\S+)\s+(\S+)")
_RE_TOT = re.compile(r"Total:\s+(\d+) OK,\s+(\d+) PARCHEABLE,\s+(\d+) BLOQUEADO")
_RE_JOB = re.compile(r"^\s+\S+/bin/jobs/([\w.\-]+)/\S+\s+->\s+(\S+)\s+ok=(True|False)")
FUENTES_MLOPS = "mlops22"


def fuentes_mlops():
    base = os.path.join(_ROOT, FUENTES_MLOPS)
    try:
        return sorted(n for n in os.listdir(base) if os.path.isdir(os.path.join(base, n)) and not n.startswith("."))
    except OSError:
        return []


def parsear_log_paquete(texto):
    """Cifras del log de tools/construir_paquete_mlops.py (jobs, tamanos y tabla de compatibilidad)."""
    r = {"jobs": 0, "jobs_rps": 0, "mb_con": None, "mb_sin": None, "librerias": [],
         "resumen": None}
    vistos = set()
    for ln in (texto or "").splitlines():
        m = _RE_PKG.search(ln)
        if m:
            r["mb_con" if m.group(1) == "con" else "mb_sin"] = int(m.group(2))
            continue
        m = _RE_TOT.search(ln)
        if m:
            r["resumen"] = {"OK": int(m.group(1)), "PARCHEABLE": int(m.group(2)), "BLOQUEADO": int(m.group(3))}
            continue
        m = _RE_LIB.match(ln)
        if m:
            r["librerias"].append({"libreria": m.group(2), "version": m.group(3), "estado": m.group(1)})
            continue
        m = _RE_JOB.match(ln)
        if m and m.group(3) == "True" and m.group(2) not in vistos:
            vistos.add(m.group(2))
            r["jobs"] += 1
            if m.group(1).lower().split("/")[0] == "rps":
                r["jobs_rps"] += 1
    return r


def _ruta_cache_mlops():
    return os.path.join(_dir_salida(), "mlops_datos.json")


def _ultima_registrada(bases):
    """ULTIMA_SIMULACION.json mas reciente (la escribe la simulacion de todos los jobs, Mac o Linux)."""
    mejor, mt = None, -1.0
    for b in bases:
        ruta = os.path.join(b, "ULTIMA_SIMULACION.json")
        try:
            t = os.path.getmtime(ruta)
        except OSError:
            continue
        if t > mt:
            mejor, mt = ruta, t
    if not mejor:
        return None
    try:
        with open(mejor, "r", encoding="utf-8") as f:
            d = json.load(f)
    except (OSError, ValueError):
        return None
    jobs = [j for j in (d.get("jobs") or []) if isinstance(j, dict) and j.get("job")]
    if not jobs:
        return None
    return {"jobs": len(jobs), "ok": sum(1 for j in jobs if j.get("estado") == "OK"),
            "con_salida": sum(1 for j in jobs if j.get("filas")),
            "fecha": str(d.get("fecha") or datetime.fromtimestamp(mt).strftime("%Y-%m-%d"))[:10],
            "donde": "Linux RHEL 8" if d.get("donde") == "linux" else "Mac",
            "env": d.get("env"),
            "detalle": [{"job": j["job"], "estado": j.get("estado"), "seg": j.get("seg"),
                         "filas": j.get("filas")} for j in jobs]}
def _ultima_simulacion():
    """Resultado de la ultima simulacion: ULTIMA_SIMULACION.json (estado por job) o, si no hay, el
    REPORTE_DEMO.json mas reciente (filas escritas por job). None si no hay ninguna."""
    base = os.environ.get("BNX_SIMULAR_DIR")
    if not base:
        try:
            from src import vendor_cache as _vc
            base = os.path.join(_vc.cache_dir(), "_simular")
        except Exception:  # noqa: BLE001
            return None
    reg = _ultima_registrada([os.path.abspath(base), os.path.realpath(os.path.abspath(base) + "_linux")])
    if reg:
        return reg
    mejor, mt = None, -1.0
    raiz = os.path.abspath(base)
    if not os.path.isdir(raiz):
        return None
    for r, ds, fs in os.walk(raiz):
        if r[len(raiz):].count(os.sep) > 5:
            ds[:] = []
            continue
        if "REPORTE_DEMO.json" in fs:
            ruta = os.path.join(r, "REPORTE_DEMO.json")
            try:
                t = os.path.getmtime(ruta)
            except OSError:
                continue
            if t > mt:
                mejor, mt = ruta, t
    if not mejor:
        return None
    try:
        with open(mejor, "r", encoding="utf-8") as f:
            d = json.load(f)
    except (OSError, ValueError):
        return None
    jobs = [j for j in (d.get("jobs") or []) if isinstance(j, dict)]
    if not jobs:
        return None
    con = 0
    for j in jobs:
        if any((e or {}).get("filas") for e in (j.get("escrituras") or [])):
            con += 1
    return {"jobs": len(jobs), "con_salida": con,
            "fecha": datetime.fromtimestamp(mt).strftime("%Y-%m-%d")}


def recolectar_mlops():
    """Cifras reales del paquete MLOps (cache escrito por 'actualizar_mlops') y de la ultima simulacion."""
    cache = None
    try:
        with open(_ruta_cache_mlops(), "r", encoding="utf-8") as f:
            cache = json.load(f)
    except (OSError, ValueError):
        cache = None
    if not isinstance(cache, dict):
        cache = None
    c = cache or {}
    lib = c.get("librerias") or []
    res = c.get("resumen")
    return {"hay_paquete": bool(cache and c.get("jobs")),
            "jobs": c.get("jobs") or None, "jobs_rps": c.get("jobs_rps") or None,
            "mb_con": c.get("mb_con"), "mb_sin": c.get("mb_sin"),
            "librerias": lib, "resumen": res, "generado": c.get("generado"),
            "simulacion": _ultima_simulacion()}


def actualizar_mlops(fuente):
    """Arma los paquetes con tools/construir_paquete_mlops.py (solo lee la fuente), guarda las cifras
    y borra los ZIP temporales."""
    import shutil
    import subprocess
    import sys
    import tempfile
    if fuente not in fuentes_mlops():
        raise PresentacionError("fuente invalida: %r (carpetas de %s/: %s)" % (fuente, FUENTES_MLOPS, ", ".join(fuentes_mlops()) or "ninguna"))
    tmp = tempfile.mkdtemp(prefix="bnx_pres_")
    try:
        cmd = [sys.executable, os.path.join(_ROOT, "tools", "construir_paquete_mlops.py"),
               "--src", os.path.join(_ROOT, FUENTES_MLOPS, fuente), "--out", tmp]
        try:
            pr_ = subprocess.run(cmd, cwd=_ROOT, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                                 universal_newlines=True, timeout=1500)
        except subprocess.TimeoutExpired:
            raise PresentacionError("armar el paquete tardo mas de 25 minutos")
        d = parsear_log_paquete(pr_.stdout)
        if pr_.returncode != 0 or not d["jobs"]:
            cola = " | ".join((pr_.stdout or "").strip().splitlines()[-3:])[:300]
            raise PresentacionError("no se pudo armar el paquete (codigo %s): %s" % (pr_.returncode, cola))
        d["generado"] = datetime.now().strftime("%Y-%m-%d %H:%M")
        os.makedirs(_dir_salida(), exist_ok=True)
        with open(_ruta_cache_mlops(), "w", encoding="utf-8") as f:
            json.dump(d, f, ensure_ascii=False, indent=1)
        return d
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


# ---------------------------------------------------------------------------
# Laminas (contenido): 2 por presentacion
# ---------------------------------------------------------------------------
def _valor_tam(v):
    n = len(v)
    return 34 if n <= 7 else 28 if n <= 11 else 22 if n <= 16 else 16


def _cabecera(P, titulo):
    P.append(_rect(0, 0, W, 66, COL_FONDO))
    P.append(_txt(40, 18 if len(titulo) > 55 else 16, 880, 40, titulo, 22 if len(titulo) > 55 else 26, "#ffffff", True))
    P.append(_rect(0, 66, W, 4, COL_ACENTO))


def _pie(P, texto):
    P.append(_rect(40, H - 46, 880, 1, "#c8d2dd"))
    P.append(_txt(40, H - 42, 880, 38, texto, 9 if len(texto) > 150 else 11, "#5b6b7b"))


def _kpi(P, x, y, w, h, valor, etiqueta, nota, color):
    P.append(_rect(x, y, w, h, COL_SUAVE, "#d5dde6"))
    P.append(_rect(x, y, w, 6, color))
    P.append(_txt(x + 12, y + 16, w - 24, 44, valor, _valor_tam(valor), COL_FONDO, True))
    P.append(_txt(x + 12, y + 64, w - 24, 20, etiqueta, 12, COL_TEXTO, True))
    P.append(_txt(x + 12, y + 84, w - 24, h - 86, nota, 10, "#5b6b7b"))


def _caja(P, x, y, w, h, titulo, items, color, maximo=13, minimo=9):
    P.append(_rect(x, y, w, h, COL_SUAVE, "#d5dde6"))
    P.append(_rect(x, y, w, 26, color))
    P.append(_txt(x + 10, y + 5, w - 16, 18, titulo, 13, "#ffffff", True))
    size = _ajustar(items, w - 28, h - 40, maximo, minimo, 1.25, 5)
    P.append(_txt(x + 12, y + 34, w - 24, h - 38, items, size, COL_TEXTO, bullets=True))


def _pasos(P, y, h, pasos):
    P.append(_txt(40, y, 600, 20, "Siguientes pasos e hitos", 14, COL_FONDO, True))
    n = len(pasos)
    gap = 12
    cw = (880 - gap * (n - 1)) / float(n)
    for i, (tit, txt) in enumerate(pasos):
        cx = 40 + i * (cw + gap)
        P.append(_rect(cx, y + 24, cw, h - 24, "#ffffff", COL_ACENTO))
        P.append(_rect(cx, y + 24, 6, h - 24, COL_ACENTO))
        P.append(_txt(cx + 14, y + 30, cw - 20, 18, "%d · %s" % (i + 1, tit), 12, COL_FONDO, True))
        size = _ajustar([txt], cw - 24, h - 56, 11, 9, 1.25, 0)
        P.append(_txt(cx + 14, y + 50, cw - 22, h - 54, txt, size, COL_TEXTO))


def _ejecutiva(titulo, titular, bajada, kpis, necesita, pie):
    P = []
    _cabecera(P, titulo)
    P.append(_txt(40, 82, 880, 64, titular, 24 if len(titular) <= 120 else 20, COL_FONDO, True))
    P.append(_txt(40, 148, 880, 38, bajada, 13, "#35506b"))
    cw = (880 - 3 * 16) / 4.0
    cols = [COL_ACENTO, "#22a06b", "#e8a317", "#7a5af8"]
    for i, (v, e, nota) in enumerate(kpis):
        _kpi(P, 40 + i * (cw + 16), 192, cw, 124, v, e, nota, cols[i % 4])
    P.append(_rect(40, 332, 880, 148, "#ffffff", COL_ACENTO))
    P.append(_rect(40, 332, 6, 148, COL_ACENTO))
    P.append(_txt(60, 340, 800, 22, "Qué necesitamos en Banamex", 16, COL_FONDO, True))
    items = ["%d. %s" % (i + 1, t) for i, t in enumerate(necesita)]
    size = _ajustar(items, 840, 108, 17, 10, 1.25, 8)
    P.append(_txt(60, 368, 840, 108, items, size, COL_TEXTO))
    _pie(P, pie)
    return P


def laminas_grafos(datos, est, p, fecha_corte):
    """Presentacion A: migracion de grafos Ab Initio -> PySpark (2 laminas, sin MLOps)."""
    t = datos["total"]
    nproj = len(datos["proyectos"])
    por_grafo = p["alto_modo"] == "por_grafo"
    alto_txt = ("%s h por cada grafo muy complejo con plan/pset" % _num(p["alto_horas"]) if por_grafo
                else "%s h en total para los grafos muy complejos con plan/pset" % _num(p["alto_horas"]))
    sin_txt = ("%s h por cada grafo complejo sin plan/pset (pendiente de confirmar)" % _num(p["alto_sin_plan_horas"]) if por_grafo
               else "%s h en total para los grafos complejos sin plan/pset (pendiente de confirmar)" % _num(p["alto_sin_plan_horas"]))
    sd = p["n_alto_sin_dato"]
    nconv = t["convertidos"]
    titulo = "Migración de grafos Ab Initio → PySpark"
    titular = ("Reducimos el riesgo y el costo de depender de Ab Initio: %d grafos ya están convertidos a PySpark" % nconv
               if nconv else "Reducimos el riesgo y el costo de depender de Ab Initio con una conversión automática a PySpark")
    bajada = ("El convertidor deja listo ~%s%% de los grafos simples y medios y ~%s%% de los complejos; una persona cierra el resto."
              % (_num(p["auto_simple"]), _num(p["auto_alto"])))
    sem_ahorro = est["ahorro_horas"] / p["horas_semana"]
    kpis = [
        (_fmt(nconv), "Grafos convertidos",
         "%d proyecto(s). Simples %d · medios %d · altos %d%s" % (
             nproj, t["niveles"]["Simple"], t["niveles"]["Medio"], t["niveles"]["Alto"],
             " · %d sin clasificar" % t["sin_clasificar"] if t["sin_clasificar"] else "")),
        (_fmt(t["accuracy"], "%"), "Exactitud promedio", "Promedio de los reportes de conversión por lote"),
        ("%s h" % _num(est["ahorro_horas"]), "Ahorro estimado",
         "≈ %s semanas-persona menos que todo manual%s" % (_num(round(sem_ahorro, 1)),
                                      " (%s%%)" % _num(est["ahorro_pct"]) if est["ahorro_pct"] is not None else "")),
        ("%s sem" % _num(est["semanas_calendario"]), "Esfuerzo humano restante",
         "%s h con %s persona(s) a %s h por semana" % (_num(est["horas_total"]), _num(p["equipo"]), _num(p["horas_semana"]))),
    ]
    necesita = [
        "Confirmar el alcance: cuántos grafos tiene el portafolio completo, para proyectar la estimación (hoy se usan los ya convertidos).",
        "Asignar %s persona(s) a la revisión humana, empezando por los grafos de complejidad alta." % _num(p["equipo"]),
        "Decidir cómo leer las 2 semanas de los grafos muy complejos con plan/pset: por grafo o en total (esta versión usa: %s)."
        % ("por grafo" if por_grafo else "en total"),
        "Confirmar las horas de un grafo complejo sin plan/pset (pendiente; esta versión supone %s h)." % _num(p["alto_sin_plan_horas"]),
    ]
    pie1 = "Cifras reales de los reportes de conversión y del clasificador de complejidad. Fecha de corte: %s" % fecha_corte
    s1 = {"n": 1, "titulo": "Mensaje ejecutivo", "pie": pie1,
          "prims": _ejecutiva(titulo, titular, bajada, kpis, necesita, pie1)}

    # ---- lamina 2: como lo logramos y plan
    P = []
    _cabecera(P, titulo + " · Cómo lo logramos y plan")
    tec = ["Convertidor automático: grafo + pset + plan → PySpark, con parámetros y expresiones validadas con Spark.",
           "Mapa pset ↔ grafo ↔ plan: se ve qué falta antes de convertir.",
           "Ya contamos con un Orquestador: plan y plan de planes, dry-run y ejecución real con log, DAG de Airflow, entorno offline RHEL 8%s."
           % ("; %s orquestaciones disponibles" % t["orquestaciones"] if t["orquestaciones"] else ""),
           "Datos sintéticos y visor para probar sin datos reales.",
           "Seguimiento con complejidad 50/30/20 y roles."]
    _caja(P, 40, 82, 270, 240, "Tecnología ya construida", tec, COL_ACENTO, 12, 9)
    g, h = est["grafos"], est["horas"]
    P.append(_txt(330, 82, 300, 20, "Estimación de esfuerzo", 14, COL_FONDO, True))
    tabla = {"cols": ["Nivel", "Grafos", "Auto.", "Horas"], "pesos": [1.3, 1, 1, 1],
             "filas": [["Simple", g["Simple"], "%s%%" % _num(p["auto_simple"]), _num(h["Simple"])],
                       ["Medio", g["Medio"], "%s%%" % _num(p["auto_medio"]), _num(h["Medio"])],
                       ["Alto con plan", est["alto_plan"], "%s%%" % _num(p["auto_alto"]), _num(est["horas_alto_plan"])],
                       ["Alto sin plan", est["alto_sin_plan"], "%s%%" % _num(p["auto_alto"]), _num(est["horas_alto_sin_plan"])],
                       ["Total", sum(g.values()), "", _num(est["horas_total"])]]}
    yy = _tabla(P, 330, 108, 300, tabla, 22, 10)
    resumen = ["%s semanas-persona · %s semanas calendario con %s persona(s)." % (
                   _num(est["semanas_persona"]), _num(est["semanas_calendario"]), _num(p["equipo"])),
               "Muy complejo con plan/pset: %d grafos, %s." % (est["alto_plan"], alto_txt),
               "Complejo sin plan/pset: %d grafos%s, %s." % (
                   est["alto_sin_plan"], " (%d %s)" % (sd, SIN_DATO) if sd else "", sin_txt),
               "Básicos y medios: %d grafos, %s h de 1 persona por grafo." % (g["Simple"] + g["Medio"], _num(p["horas_simple"]))]
    P.append(_txt(330, yy + 8, 300, 322 - yy - 8, resumen, _ajustar(resumen, 288, 322 - yy - 8, 11, 7, 1.2, 6), COL_TEXTO, bullets=True))
    _barras(P, 650, 82, 270, 240, {
        "series": [("Todo manual", "#9aa5b1"), ("Con convertidor", COL_ACENTO)],
        "categorias": [(nv, [est["horas_manual"][nv], h[nv]]) for nv in ("Simple", "Medio", "Alto")]})
    nsm = g["Simple"] + g["Medio"]
    pasos = [("Alcance", "Confirmar el portafolio completo y cargarlo en el seguimiento de migración."),
             ("Simples y medios", "Convertir y revisar %d grafos: ~%s h de 1 persona por grafo para llegar al 100%%." % (nsm, _num(p["horas_simple"]))),
             ("Complejos", "Revisión dedicada: %d muy complejos con plan/pset (%s h) y %d complejos sin plan/pset (%s h, pendiente de confirmar)." % (
                 est["alto_plan"], _num(p["alto_horas"]), est["alto_sin_plan"], _num(p["alto_sin_plan_horas"]))),
             ("Validación", "Ejecutar los planes con el Orquestador sobre datos reales y registrar la evidencia.")]
    _pasos(P, 340, 144, pasos)
    pie2 = ("Supuestos editables: Simple y Medio %s h por grafo; todo manual = horas / (1 − %% automático). Alto: %s; %s (modo: %s). %s h por persona por semana. "
            "Fecha de corte: %s" % (_num(p["horas_simple"]), alto_txt, sin_txt, "por grafo" if por_grafo else "total",
                                    _num(p["horas_semana"]), fecha_corte))
    _pie(P, pie2)
    s2 = {"n": 2, "titulo": "Cómo lo logramos y plan", "pie": pie2, "prims": P}
    return [s1, s2]


def laminas_mlops(m, fecha_corte):
    """Presentacion B: Framework MLOps v2 (2 laminas, sin migracion de grafos)."""
    titulo = "Framework MLOps v2"
    res = m["resumen"] or {}
    libs = m["librerias"] or []
    pendientes = [l["libreria"] for l in libs if l["estado"] != "OK" and not l["libreria"].startswith("bnx-")]
    sim = m["simulacion"]
    titular = ("Llevamos los modelos del banco al servidor RHEL 8 sin conexión a internet y sin instalar nada en otros nodos, "
               "con menos riesgo en el paso a producción")
    bajada = "Un solo paquete con todo lo necesario, que se puede simular antes de tocar el servidor; lo que falta de las librerías del banco queda identificado."
    jobs_nota = ("%s del modelo RPS · detectados al armar el paquete" % m["jobs_rps"] if m["jobs_rps"]
                 else "detectados al armar el paquete")
    if m["mb_con"] is not None and m["mb_sin"] is not None:
        tam = ("%s / %s MB" % (m["mb_con"], m["mb_sin"]))
    else:
        tam = SIN_DATO
    if res:
        lib_v = "%s / %s / %s" % (res.get("OK", 0), res.get("PARCHEABLE", 0), res.get("BLOQUEADO", 0))
        lib_n = "OK / parcheables / bloqueadas, de %d analizadas (análisis estático)" % len(libs)
    else:
        lib_v, lib_n = SIN_DATO, "Se calcula al armar el paquete"
    if sim and sim.get("ok") is not None:
        sim_v = "%d de %d" % (sim["ok"], sim["jobs"])
        sim_n = "jobs OK en la última simulación (%s%s, %s)" % (
            sim.get("donde") or "", (" · env %s" % sim["env"]) if sim.get("env") else "", sim["fecha"])
    elif sim:
        sim_v, sim_n = "%d de %d" % (sim["con_salida"], sim["jobs"]), "jobs con filas escritas en la última simulación (%s)" % sim["fecha"]
    else:
        sim_v, sim_n = SIN_DATO, "Aún no hay una simulación registrada"
    kpis = [(_fmt(m["jobs"]), "Jobs empaquetados", jobs_nota),
            (tam, "Tamaño del paquete", "con PySpark incluido / sin PySpark (usa el del servidor)"),
            (lib_v, "Librerías del banco", lib_n),
            (sim_v, "Simulación por job", sim_n)]
    necesita = [
        "Versiones completas de las librerías del banco que hoy se parchean%s." % (
            ": " + ", ".join(pendientes) if pendientes else ""),
        "Una ventana para validar con datos reales en el servidor RHEL 8 (local o YARN).",
        "Confirmar Python disponible en los workers, porque las UDFs lo requieren, o aprobar convertirlas a PySpark nativo.",
    ]
    pie1 = "Cifras reales calculadas al armar el paquete%s. Fecha de corte: %s" % (
        " (%s)" % m["generado"] if m["generado"] else "", fecha_corte)
    s1 = {"n": 1, "titulo": "Mensaje ejecutivo", "pie": pie1,
          "prims": _ejecutiva(titulo, titular, bajada, kpis, necesita, pie1)}

    P = []
    _cabecera(P, titulo + " · Cómo lo logramos y riesgos")
    tec = ["Empaqueta los modelos y jobs del banco para RHEL 8 con Python 3.11, sin conexión: PySpark 3.5.6, numpy 1.26 y las librerías del banco desde el repo privado.",
           "PySpark incluido o el del servidor; ejecución local o en YARN con los recursos del spark.json del banco.",
           "Simulación por job en Mac y en contenedor Linux RHEL 8, con monitoreo de CPU y memoria.",
           "Diagnóstico y parches de librerías, con aviso de qué falta y dónde cargarlo.",
           "Conversión de pandas a PySpark nativo."]
    _caja(P, 40, 82, 270, 244, "Tecnología ya construida", tec, COL_ACENTO, 12, 9)
    P.append(_txt(326, 82, 300, 20, "Librerías del banco (estado)", 14, COL_FONDO, True))
    if libs:
        filas = [[l["libreria"], l["version"], l["estado"]] for l in libs[:9]]
        if len(libs) > 9:
            filas.append(["(+%d más)" % (len(libs) - 9), "", ""])
        _tabla(P, 326, 108, 310, {"cols": ["Librería", "Versión", "Estado"], "pesos": [2.6, 1, 1.5], "filas": filas}, 21, 10)
    else:
        P.append(_txt(326, 112, 310, 40, "Estado: " + SIN_DATO + ". Arma el paquete desde la pestaña para calcularlo.", 12, COL_TEXTO))
    riesgos = ["Librerías del banco incompletas: %s parcheable(s). Los parches no están validados contra la salida original; hay que pedir las versiones completas." % (
                   _fmt(res.get("PARCHEABLE")) if res else SIN_DATO),
               "Sin validación con datos reales: la simulación usa datos de relleno; falta correr en el servidor.",
               "Las UDFs requieren Python en los workers."]
    _caja(P, 652, 82, 268, 244, "Riesgos y decisiones", riesgos, "#d64545", 12, 9)
    pasos = [("Librerías", "Recibir las versiones completas y volver a analizar el paquete hasta no tener parches."),
             ("Simulación", "Simular los %s jobs y revisar CPU y memoria de cada uno." % _fmt(m["jobs"])),
             ("Servidor", "Validar con datos reales en el servidor RHEL 8, local o en YARN."),
             ("Cierre", "Resolver Python en workers o convertir las UDFs a PySpark nativo.")]
    _pasos(P, 340, 144, pasos)
    pie2 = ("Fuente: análisis del paquete generado desde el repositorio%s y última simulación registrada. Un dato ausente se muestra como «%s». Fecha de corte: %s"
            % (" (%s)" % m["generado"] if m["generado"] else "", SIN_DATO, fecha_corte))
    _pie(P, pie2)
    s2 = {"n": 2, "titulo": "Cómo lo logramos y riesgos", "pie": pie2, "prims": P}
    return [s1, s2]


# ---- dibujo ---------------------------------------------------------------
def _lineas(texto, size, ancho):
    cpl = max(1, int(ancho / (size * 0.52)))
    return max(1, int(math.ceil(len(texto) / float(cpl))))


def _ajustar(textos, ancho, alto, maximo=18, minimo=10, interlineado=1.3, sep=6):
    """Mayor tamano de letra (maximo..minimo) con el que los parrafos caben en alto."""
    s = maximo
    while s > minimo:
        h = sum(_lineas(t, s, ancho) * s * interlineado + sep for t in textos)
        if h <= alto:
            break
        s -= 1
    return s


def _txt(x, y, w, h, texto, size, color=COL_TEXTO, bold=False, align="l", bullets=False):
    return {"k": "text", "x": x, "y": y, "w": w, "h": h, "paras": texto if isinstance(texto, list) else [texto],
            "size": size, "color": color, "bold": bold, "align": align, "bullets": bullets}


def _rect(x, y, w, h, fill, line=None):
    return {"k": "rect", "x": x, "y": y, "w": w, "h": h, "fill": fill, "line": line}


def _tabla(prims, x, y, w, t, fila_h=26, size=11):
    tot = float(sum(t["pesos"]))
    xs, acc = [], x
    for pz in t["pesos"]:
        xs.append((acc, w * pz / tot))
        acc += w * pz / tot
    prims.append(_rect(x, y, w, fila_h, COL_FONDO))
    for (cx, cw), c in zip(xs, t["cols"]):
        prims.append(_txt(cx + 6, y + 5, cw - 8, fila_h - 6, c, size, "#ffffff", True))
    for i, fila in enumerate(t["filas"]):
        yy = y + fila_h * (i + 1)
        ultima = i == len(t["filas"]) - 1 and str(fila[0]).startswith("Total")
        prims.append(_rect(x, yy, w, fila_h, "#dbe7f3" if ultima else (COL_SUAVE if i % 2 == 0 else "#ffffff"), "#d5dde6"))
        for j, ((cx, cw), c) in enumerate(zip(xs, fila)):
            s = str(c)
            maxc = max(4, int((cw - 8) / (size * 0.52)))
            if len(s) > maxc:
                s = s[:maxc - 1] + "…"
            prims.append(_txt(cx + 6, yy + 5, cw - 8, fila_h - 6, s, size, COL_TEXTO, ultima))
    return y + fila_h * (len(t["filas"]) + 1)


def _barras(prims, x, y, w, h, b):
    prims.append(_txt(x, y, w, 18, "Horas por nivel", 12, COL_TEXTO, True))
    maxv = max([v for _c, vs in b["categorias"] for v in vs] + [1])
    y0 = y + 26
    # leyenda
    lx = x
    for nombre, col in b["series"]:
        prims.append(_rect(lx, y0 + 2, 10, 10, col))
        prims.append(_txt(lx + 14, y0, 100, 16, nombre, 10))
        lx += 112
    y0 += 24
    bloque = (h - 50) / float(len(b["categorias"]))
    ancho = w - 70
    for i, (cat, vals) in enumerate(b["categorias"]):
        yy = y0 + i * bloque
        prims.append(_txt(x, yy, 60, 16, cat, 11, COL_TEXTO, True))
        for j, v in enumerate(vals):
            bw = max(1.0, ancho * v / maxv) if v else 1.0
            by = yy + 16 + j * 18
            prims.append(_rect(x, by, bw, 14, b["series"][j][1]))
            prims.append(_txt(x + bw + 4, by - 1, 70, 16, _num(v) + " h", 10))


# ---------------------------------------------------------------------------
# Generacion de archivos
# ---------------------------------------------------------------------------
def texto_plano(laminas):
    """Todo el texto visible de las laminas (para pruebas y busquedas)."""
    out = []
    for s in laminas:
        for pr in s["prims"]:
            if pr["k"] == "text":
                out.extend(pr["paras"])
    return "\n".join(out)


def _rgb(h):
    h = h.lstrip("#")
    return int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)


def generar_pptx(laminas):
    try:
        from pptx import Presentation
        from pptx.dml.color import RGBColor
        from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
        from pptx.util import Pt
    except ImportError:
        raise PresentacionError("Falta la libreria python-pptx. Instalala con: "
                                ".venv/bin/pip install python-pptx")
    pr = Presentation()
    pr.slide_width, pr.slide_height = Pt(W), Pt(H)
    blank = pr.slide_layouts[6]
    for s in laminas:
        sl = pr.slides.add_slide(blank)
        for p in s["prims"]:
            if p["k"] == "rect":
                sh = sl.shapes.add_shape(1, Pt(p["x"]), Pt(p["y"]), Pt(p["w"]), Pt(p["h"]))
                sh.shadow.inherit = False
                sh.fill.solid()
                sh.fill.fore_color.rgb = RGBColor(*_rgb(p["fill"]))
                if p["line"]:
                    sh.line.color.rgb = RGBColor(*_rgb(p["line"]))
                    sh.line.width = Pt(0.75)
                else:
                    sh.line.fill.background()
            elif p["k"] == "text":
                tb = sl.shapes.add_textbox(Pt(p["x"]), Pt(p["y"]), Pt(p["w"]), Pt(p["h"]))
                tf = tb.text_frame
                tf.word_wrap = True
                tf.vertical_anchor = MSO_ANCHOR.TOP
                tf.margin_left = tf.margin_right = tf.margin_top = tf.margin_bottom = 0
                for i, txt in enumerate(p["paras"]):
                    par = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
                    r = par.add_run()
                    r.text = ("• " + txt) if p["bullets"] else txt
                    r.font.size = Pt(p["size"])
                    r.font.bold = bool(p["bold"])
                    r.font.name = "Calibri"
                    r.font.color.rgb = RGBColor(*_rgb(p["color"]))
                    par.alignment = PP_ALIGN.CENTER if p["align"] == "c" else PP_ALIGN.LEFT
                    if p["bullets"]:
                        par.space_after = Pt(6)
    buf = io.BytesIO()
    pr.save(buf)
    return buf.getvalue()


def generar_pdf(laminas, titulo="Presentacion ejecutiva"):
    try:
        from reportlab.pdfgen import canvas
        from reportlab.lib.colors import Color
        from reportlab.lib.utils import simpleSplit
    except ImportError:
        raise PresentacionError("Falta la libreria reportlab. Instalala con: "
                                ".venv/bin/pip install reportlab")

    def col(h):
        r, g, b = _rgb(h)
        return Color(r / 255.0, g / 255.0, b / 255.0)

    def pdf_txt(t):  # Helvetica estandar no trae estos simbolos
        return (t.replace("→", "->").replace("↔", "<->").replace("…", "...")
                .replace("·", "-").replace("•", "-"))

    buf = io.BytesIO()
    c = canvas.Canvas(buf, pagesize=(W, H))
    c.setTitle(titulo.replace("→", "a"))
    for s in laminas:
        for p in s["prims"]:
            if p["k"] == "rect":
                c.setFillColor(col(p["fill"]))
                if p["line"]:
                    c.setStrokeColor(col(p["line"]))
                    c.setLineWidth(0.75)
                c.rect(p["x"], H - p["y"] - p["h"], p["w"], p["h"], stroke=1 if p["line"] else 0, fill=1)
            elif p["k"] == "text":
                font = "Helvetica-Bold" if p["bold"] else "Helvetica"
                c.setFillColor(col(p["color"]))
                c.setFont(font, p["size"])
                y = H - p["y"] - p["size"]
                lead = p["size"] * 1.2
                for txt in p["paras"]:
                    t = pdf_txt(("• " + txt) if p["bullets"] else txt)
                    for ln in simpleSplit(t, font, p["size"], p["w"]):
                        if p["align"] == "c":
                            c.drawCentredString(p["x"] + p["w"] / 2.0, y, ln)
                        else:
                            c.drawString(p["x"], y, ln)
                        y -= lead
                    if p["bullets"]:
                        y -= 6
        c.showPage()
    c.save()
    return buf.getvalue()


def librerias():
    out = {}
    for k, mod, pip in (("pptx", "pptx", "python-pptx"), ("pdf", "reportlab", "reportlab")):
        try:
            __import__(mod)
            out[k] = {"ok": True}
        except ImportError:
            out[k] = {"ok": False, "instalar": ".venv/bin/pip install %s" % pip}
    return out



# ---------------------------------------------------------------------------
# API
# ---------------------------------------------------------------------------
TIPOS = {
    "grafos": {"titulo": "Migración de grafos Ab Initio → PySpark", "archivo": "migracion_grafos_pyspark"},
    "mlops": {"titulo": "Framework MLOps v2", "archivo": "framework_mlops_v2"},
}


def _fecha(v):
    if not v:
        return date.today().isoformat()
    try:
        return datetime.strptime(str(v), "%Y-%m-%d").date().isoformat()
    except ValueError:
        raise PresentacionError("fecha de corte invalida (use AAAA-MM-DD)")


def preparar(data):
    """(tipo, datos, params, estimacion, fecha, laminas). 2 laminas como maximo."""
    tipo = str(data.get("tipo") or "grafos")
    if tipo not in TIPOS:
        raise PresentacionError("presentacion invalida: %s (grafos o mlops)" % tipo)
    fecha = _fecha(data.get("fecha_corte"))
    if tipo == "grafos":
        datos = recolectar(data.get("proyectos"))
        p = normalizar_params(data.get("params"), datos["total"])
        est = estimar(p)
        return tipo, datos, p, est, fecha, laminas_grafos(datos, est, p, fecha)
    datos = recolectar_mlops()
    return tipo, datos, None, None, fecha, laminas_mlops(datos, fecha)


def _dir_salida():
    return os.environ.get("BNX_PRESENTACION_DIR") or os.path.join(_ROOT, "data", "presentacion")


ACCIONES_ESCRITURA = ("descargar", "actualizar_mlops")


def handle(action, data):
    """(status, dict). Errores de uso -> (400, {ok: False, error})."""
    data = data if isinstance(data, dict) else {}
    try:
        if action == "proyectos":
            return 200, {"ok": True, "proyectos": proyectos_disponibles(), "librerias": librerias(),
                         "params_base": PARAMS_BASE, "fecha_hoy": date.today().isoformat(),
                         "tipos": TIPOS, "mlops": {"fuentes": fuentes_mlops(), "datos": recolectar_mlops()}}
        if action == "vista":
            tipo, datos, p, est, fecha, laminas = preparar(data)
            return 200, {"ok": True, "tipo": tipo, "fecha_corte": fecha, "datos": datos, "params": p,
                         "estimacion": est, "laminas": laminas, "librerias": librerias()}
        if action == "actualizar_mlops":
            fuente = str(data.get("fuente") or (fuentes_mlops() or [""])[0])
            return 200, {"ok": True, "datos": actualizar_mlops(fuente) and recolectar_mlops()}
        if action == "descargar":
            fmt = str(data.get("fmt") or "").lower()
            if fmt not in ("pptx", "pdf"):
                raise PresentacionError("formato invalido: %s (pptx o pdf)" % fmt)
            tipo, _d, _p, _e, fecha, laminas = preparar(data)
            cont = generar_pptx(laminas) if fmt == "pptx" else generar_pdf(laminas, TIPOS[tipo]["titulo"])
            nombre = "%s_%s.%s" % (TIPOS[tipo]["archivo"], fecha, fmt)
            try:  # copia local fuera de git
                os.makedirs(_dir_salida(), exist_ok=True)
                with open(os.path.join(_dir_salida(), nombre), "wb") as f:
                    f.write(cont)
            except OSError:
                pass
            ctype = ("application/vnd.openxmlformats-officedocument.presentationml.presentation"
                     if fmt == "pptx" else "application/pdf")
            return 200, {"ok": True, "binario": (cont, nombre, ctype)}
        return 404, {"ok": False, "error": "accion desconocida: %s" % action}
    except PresentacionError as e:
        return 400, {"ok": False, "error": str(e)}
