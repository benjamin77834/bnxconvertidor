# src/orquestador.py
"""
Orquestador de planes Ab Initio ya convertidos, con orquestacion editable.

Flujo:
  1) generar   : lee los .plan (via pset_map) + los .py convertidos y escribe un
                 orquestacion_<plan>.json por plan (pasos, dependencias, accion).
  2) acomodar  : editas el JSON a mano o con los comandos dep-add / dep-rm /
                 deshabilitar / habilitar / invertir.
  3) ejecutar  : corre los pasos en orden topologico. Por defecto es DRY-RUN;
                 solo ejecuta de verdad con --ejecutar.

Sentido de las dependencias: en el .plan, la relacion task_prior_task (a -> b)
se interpreta como "b es prior de a" (b corre ANTES que a). Es una inferencia a
partir de los planes del lote (da cadenas coherentes p1_enable -> ... -> Run
pset -> Update_last_run_date), no una regla documentada: si un plan sale al
reves, usa el comando `invertir`.
Todas las aristas son dependencias duras; el flag (0,1,2,3...) del .plan se
conserva en "dep_flags" por si importa (no esta documentado que significa).
Los pasos cuyo nombre contiene "fail" se marcan "solo_en_fallo" (heuristica por
nombre): en la ejecucion solo corren si algun paso previo fallo.

Uso:
    python -m src.orquestador generar <carpeta_ab> <carpeta_convertida> [--out DIR]
    python -m src.orquestador mostrar   orquestacion_X.json
    python -m src.orquestador dep-add   orquestacion_X.json PASO --despues-de OTRO
    python -m src.orquestador dep-rm    orquestacion_X.json PASO --despues-de OTRO
    python -m src.orquestador deshabilitar|habilitar orquestacion_X.json PASO
    python -m src.orquestador invertir  orquestacion_X.json
    python -m src.orquestador ejecutar  orquestacion_X.json [--ejecutar]
    python -m src.orquestador config    orquestacion_X.json [--modo python|spark-submit]
                                        [--base-path RUTA] [--spark-args "--master local[2]"]
    python -m src.orquestador enlaces   orquestacion_X.json
    python -m src.orquestador sugerir   orquestacion_X.json
    python -m src.orquestador enlace-add orquestacion_X.json --desde T --salida zona/nombre
                                         --hacia T --entrada zona/nombre
    python -m src.orquestador enlace-rm orquestacion_X.json ID
    python -m src.orquestador airflow   orquestacion_X.json [--out dag.py]
    python -m src.orquestador datos     orquestacion_X.json [--base-path DIR] [--filas 20]
                                        [--seed 42] [--sobrescribir]
PASO se indica por id (t17) o por nombre exacto si es unico.

Ejecucion (bloque "ejecucion" del JSON):
  modo "python"       -> python <job>.py
  modo "spark-submit" -> spark-submit <spark_args> <job>.py
  base_path           -> se exporta como BNX_BASE_PATH a cada job. La ejecucion REAL lo
                         exige (si no, los jobs usarian el bucket S3 por defecto).
Enlaces ("enlaces"): conectan la SALIDA de un job con la ENTRADA de uno posterior.
Los jobs generados leen <base>/raw/<x> y escriben <base>/output/<y>; el orquestador no
puede cambiar esos paths, asi que antes del job destino COPIA <base>/<salida> a
<base>/<entrada> (cp local o `aws s3 sync`). Los enlaces se sugieren solo cuando el
nombre del dataset coincide; el resto se define a mano.
"""
import argparse
import json
import os
import re
import shlex
import shutil
import subprocess
import sys
from collections import defaultdict

from src import pset_map as pm


# ---------------------------------------------------------------------------
# Construccion
# ---------------------------------------------------------------------------

def _index_converted(converted_dir):
    """{nombre_mp_normalizado: ruta_py} a partir de '<base>_<target>.py'."""
    idx = {}
    if not converted_dir or not os.path.isdir(converted_dir):
        return idx
    for f in sorted(os.listdir(converted_dir)):
        m = re.match(r"^(.*)_(?:spark|glue|flink|python)\.py$", f)
        if m:
            idx[pm._norm_name(m.group(1) + ".mp")] = os.path.join(converted_dir, f)
    return idx


def _resolve_action(refs, nodes, converted):
    """Decide que hace un paso segun los archivos que referencia."""
    for r in refs:
        kind = pm._kind_of(r)
        node = nodes.get(r)
        if kind == "graph":
            if r in converted:
                return {"type": "graph", "target": converted[r], "source": r, "status": "ok"}
            st = "sin_convertir" if node and node.get("present") else "faltante"
            return {"type": "graph", "target": None, "source": r, "status": st}
        if kind == "pset":
            proto = nodes.get(r, {}).get("prototype")
            g = pm._norm_name(proto) if proto else None
            if g and g in converted:
                return {"type": "graph", "target": converted[g], "source": r, "status": "ok"}
            return {"type": "graph", "target": None, "source": r, "status": "faltante"}
        if kind == "ksh":
            present = bool(node and node.get("present"))
            return {"type": "script", "target": r, "source": r,
                    "status": "ok" if present else "faltante"}
    return {"type": "noop", "target": None, "source": None, "status": "no_traducido",
            "nota": "tarea de programa/script de Ab Initio sin traduccion automatica"}


def _flatten(tasks, order):
    """Aplana subplans: devuelve (hard, flags, is_container) con ids de hojas.

    hard[a] = {b,...}: a depende de b (b corre antes). flags[(a,b)] = flag != "0".
    """
    kids = defaultdict(list)
    for t in tasks.values():
        if t["parent"] in tasks:
            kids[t["parent"]].append(t["id"])
    is_container = lambda x: bool(kids.get(x))

    raw = defaultdict(set)
    raw_flag = {}
    for o in order:
        a, b = o["from"], o["to"]  # a tiene a b como prior -> b corre antes
        if a not in tasks or b not in tasks:
            continue
        raw[a].add(b)
        if str(o["flag"]) != "0":
            raw_flag[(a, b)] = str(o["flag"])

    def exits(c):
        sib = set(kids[c])
        depended = {d for s in sib for d in raw.get(s, ()) if d in sib}
        out = []
        for ch in sorted(sib - depended):
            out += exits(ch) if is_container(ch) else [ch]
        return out

    def entries(c):
        sib = set(kids[c])
        out = []
        for ch in sorted(s for s in sib if not (raw.get(s, set()) & sib)):
            out += entries(ch) if is_container(ch) else [ch]
        return out

    as_target = lambda x: exits(x) if is_container(x) else [x]
    as_dependent = lambda x: entries(x) if is_container(x) else [x]

    hard, flags = defaultdict(set), {}
    for x in tasks:
        for dep in raw.get(x, ()):
            fl = raw_flag.get((x, dep))
            for leaf in as_dependent(x):
                for t in as_target(dep):
                    hard[leaf].add(t)
                    if fl:
                        flags[(leaf, t)] = fl
    return hard, flags, is_container


def topo_order(steps):
    """Orden topologico estable sobre pasos habilitados. Lanza ValueError si hay ciclo."""
    by_id = {s["id"]: s for s in steps}
    indeg = {s["id"]: 0 for s in steps}
    rev = defaultdict(list)
    for s in steps:
        for d in s["depends_on"]:
            if d in by_id:
                indeg[s["id"]] += 1
                rev[d].append(s["id"])
    ready = sorted((i for i, n in indeg.items() if n == 0), key=_num)
    out = []
    while ready:
        cur = ready.pop(0)
        out.append(cur)
        for nxt in sorted(rev[cur], key=_num):
            indeg[nxt] -= 1
            if indeg[nxt] == 0:
                ready.append(nxt)
        ready.sort(key=_num)
    if len(out) != len(steps):
        raise ValueError("ciclo de dependencias en: " +
                         ", ".join(sorted(set(by_id) - set(out))))
    return out


def _num(step_id):
    m = re.search(r"\d+", step_id)
    return int(m.group()) if m else 0


def build(ab_folder, converted_dir):
    """Un dict de orquestacion por cada .plan de la carpeta."""
    m = pm.scan(ab_folder)
    converted = _index_converted(converted_dir)
    result = {}
    for name, node in m["nodes"].items():
        info = node.get("plan_info")
        if not info or not info["tasks"]:
            continue
        tasks = info["tasks"]
        hard, flags, is_container = _flatten(tasks, info["order"])
        steps = []
        for tid in sorted(tasks):
            t = tasks[tid]
            if is_container(tid):
                continue
            deps = sorted(hard.get(tid, ()))
            steps.append({
                "id": f"t{tid}", "name": t["name"],
                "action": _resolve_action(t["refs"], m["nodes"], converted),
                "depends_on": sorted((f"t{d}" for d in deps), key=_num),
                "dep_flags": {f"t{d}": flags[(tid, d)] for d in deps if (tid, d) in flags},
                "solo_en_fallo": bool(re.search(r"fail", t["name"], re.I)),
                "enabled": True,
                "continue_on_error": False,
            })
        for st in steps:
            if st["action"].get("target") and st["action"]["type"] == "graph":
                st["action"]["io"] = parse_job_io(st["action"]["target"])
        result[name] = {"plan": name, "direccion": "prior",
                        "ejecucion": json.loads(json.dumps(EJECUCION_DEFECTO)),
                        "steps": steps, "enlaces": sugerir_enlaces(steps)}
        topo_order(steps)  # valida que no haya ciclos
    return result


def save_all(orchs, out_dir):
    os.makedirs(out_dir, exist_ok=True)
    paths = []
    for name, o in orchs.items():
        p = os.path.join(out_dir, "orquestacion_" + os.path.splitext(name)[0] + ".json")
        with open(p, "w", encoding="utf-8") as f:
            json.dump(o, f, indent=2, ensure_ascii=False)
        paths.append(p)
    return paths



# ---------------------------------------------------------------------------
# E/S de los jobs, enlaces y configuracion de ejecucion
# ---------------------------------------------------------------------------

EJECUCION_DEFECTO = {"modo": "python", "spark_submit": "spark-submit",
                     "spark_args": ["--master", "local[*]"], "base_path": "", "env": {}}

_BASE_F = re.compile(r'f"\{PARAMS\.BASE_PATH\}/([^/"]+)/([^"]*)"')
_PARAM_DEF = re.compile(r'^\s+(\w+)\s*=\s*os\.environ\.get\("\w+",\s*(?:"([^"]*)"|\'([^\']*)\')\)', re.M)


def parse_job_io(py_path):
    """Datasets que lee y escribe un job generado (bajo {PARAMS.BASE_PATH}/<zona>/<nombre>).

    Resuelve {PARAMS.X} con el valor por defecto de la clase PARAMS cuando es literal;
    si no (vacio o con $VAR) deja la plantilla y marca resuelto=False.
    """
    out = {"lee": [], "escribe": []}
    try:
        with open(py_path, "r", encoding="utf-8", errors="replace") as f:
            text = f.read()
    except (OSError, TypeError):
        return out
    defaults = {m.group(1): (m.group(2) if m.group(2) is not None else m.group(3))
                for m in _PARAM_DEF.finditer(text)}
    seen = set()
    for line in text.splitlines():
        m = _BASE_F.search(line)
        if not m:
            continue
        zona, nombre = m.group(1), m.group(2)
        if "$[" in nombre or not nombre:   # rutas PDL de log/error sin resolver
            continue
        resuelto = [True]

        def sub(mm):
            v = defaults.get(mm.group(1))
            if v and "$" not in v:
                return v
            resuelto[0] = False
            return mm.group(0)
        nombre = re.sub(r"\{PARAMS\.(\w+)\}", sub, nombre)
        if ".write" in line or ".save(" in line:
            kind = "escribe"
        elif "read" in line or ".load(" in line:
            kind = "lee"
        else:
            continue
        key = (kind, zona, nombre)
        if key in seen:
            continue
        seen.add(key)
        out[kind].append({"ruta": f"{zona}/{nombre}", "resuelto": resuelto[0]})
    return out


def _ancestros(steps):
    """{id: set(ids de todos los pasos que corren antes, transitivamente)}."""
    by_id = {s["id"]: s for s in steps}
    memo = {}

    def anc(i, seen=()):
        if i in memo:
            return memo[i]
        r = set()
        for d in by_id[i]["depends_on"]:
            if d in by_id and d not in seen:
                r.add(d)
                r |= anc(d, seen + (i,))
        memo[i] = r
        return r
    return {i: anc(i) for i in by_id}


def sugerir_enlaces(steps, existentes=None):
    """Enlaces sugeridos: salida de un ancestro == entrada de un paso, por nombre de dataset.

    Si la ruta completa ya coincide (misma zona y nombre) no hace falta enlace. Respeta
    los enlaces manuales existentes y no duplica pares.
    """
    anc = _ancestros(steps)
    by_id = {s["id"]: s for s in steps}
    links = [dict(e) for e in (existentes or [])]
    have = {(e["desde"], e["salida"], e["hacia"], e["entrada"]) for e in links}
    n = max([_num(e["id"]) for e in links] + [0])
    for b in steps:
        io_b = (b["action"].get("io") or {}).get("lee", [])
        for a_id in sorted(anc.get(b["id"], ()), key=_num):
            io_a = (by_id[a_id]["action"].get("io") or {}).get("escribe", [])
            for w in io_a:
                for r in io_b:
                    if w["ruta"] == r["ruta"] or w["ruta"].split("/", 1)[1] != r["ruta"].split("/", 1)[1]:
                        continue
                    key = (a_id, w["ruta"], b["id"], r["ruta"])
                    if key in have:
                        continue
                    n += 1
                    have.add(key)
                    links.append({"id": f"e{n}", "desde": a_id, "salida": w["ruta"],
                                  "hacia": b["id"], "entrada": r["ruta"],
                                  "origen": "sugerido", "habilitado": True})
    return links


def _ruta_segura(r):
    """zona/nombre relativo, sin '..', sin absoluta ni backslash (se usa para copiar/borrar)."""
    return (isinstance(r, str) and r.count("/") >= 1 and not r.startswith("/")
            and "\\" not in r and ".." not in r.split("/") and "\x00" not in r
            and all(part for part in r.split("/")))


def validar_plan(o):
    """Lanza ValueError si el plan es inconsistente (ids, dependencias, ciclos, enlaces, ejecucion)."""
    steps = o.get("steps")
    if not isinstance(steps, list) or not steps:
        raise ValueError("plan sin pasos")
    ids = [s.get("id") for s in steps]
    if not all(isinstance(i, str) for i in ids) or len(set(ids)) != len(ids):
        raise ValueError("ids de pasos invalidos o repetidos")
    for s in steps:
        if not isinstance(s.get("depends_on"), list) or any(d not in ids for d in s["depends_on"]):
            raise ValueError(f"dependencias invalidas en {s.get('id')}")
    topo_order(steps)
    anc = _ancestros(steps)
    seen_ids = set()
    for e in o.get("enlaces", []) or []:
        if e.get("id") in seen_ids or not isinstance(e.get("id"), str):
            raise ValueError("ids de enlace invalidos o repetidos")
        seen_ids.add(e["id"])
        if e.get("desde") not in ids or e.get("hacia") not in ids:
            raise ValueError(f"enlace {e.get('id')}: paso inexistente")
        if e["desde"] not in anc[e["hacia"]]:
            raise ValueError(f"enlace {e['id']}: {e['hacia']} debe correr despues de {e['desde']}")
        if not _ruta_segura(e.get("salida")) or not _ruta_segura(e.get("entrada")):
            raise ValueError(f"enlace {e['id']}: ruta invalida (use zona/nombre sin '..')")
    ej = o.get("ejecucion")
    if ej is not None:
        if ej.get("modo", "python") not in ("python", "spark-submit"):
            raise ValueError("ejecucion.modo debe ser python o spark-submit")
        if not isinstance(ej.get("spark_args", []), list) or not all(isinstance(x, str) for x in ej.get("spark_args", [])):
            raise ValueError("ejecucion.spark_args debe ser lista de strings")
        if not isinstance(ej.get("base_path", ""), str):
            raise ValueError("ejecucion.base_path debe ser texto")
        textos = [ej.get("base_path", ""), *ej.get("spark_args", [])]
        if any("\x00" in x or "\n" in x or "\r" in x for x in textos):
            raise ValueError("ejecucion: caracteres de control no permitidos")
        if not isinstance(ej.get("env", {}), dict):
            raise ValueError("ejecucion.env debe ser objeto")


def fusionar_edicion(almacenado, entrante):
    """Aplica a una copia del plan guardado SOLO lo editable desde la GUI.

    Editable: enabled / solo_en_fallo / continue_on_error / depends_on / dep_flags por paso,
    direccion, ejecucion.{modo,base_path,spark_args} y enlaces. NO se aceptan cambios en
    action (que decide que se ejecuta), ni pasos nuevos o eliminados, ni ejecucion.env /
    ejecucion.spark_submit: quien edite el JSON a mano si necesita eso. Devuelve el plan
    validado o lanza ValueError.
    """
    if not isinstance(entrante, dict):
        raise ValueError("plan invalido")
    stored_ids = {s["id"] for s in almacenado["steps"]}
    inc = entrante.get("steps")
    if (not isinstance(inc, list) or not all(isinstance(s, dict) for s in inc)
            or len(inc) != len(stored_ids) or {s.get("id") for s in inc} != stored_ids):
        raise ValueError("los pasos no coinciden con el plan guardado")
    nuevo = json.loads(json.dumps(almacenado))
    byid = {s["id"]: s for s in nuevo["steps"]}
    for s in inc:
        t = byid[s["id"]]
        for k in ("enabled", "solo_en_fallo", "continue_on_error"):
            if k in s:
                if not isinstance(s[k], bool):
                    raise ValueError(f"{s['id']}.{k} debe ser booleano")
                t[k] = s[k]
        if "depends_on" in s:
            t["depends_on"] = list(s["depends_on"]) if isinstance(s["depends_on"], list) else None
        if isinstance(s.get("dep_flags"), dict):
            t["dep_flags"] = {str(k): str(v) for k, v in s["dep_flags"].items()
                              if k in (t["depends_on"] or [])}
    if entrante.get("direccion") in ("prior", "inversa"):
        nuevo["direccion"] = entrante["direccion"]
    ej_in = entrante.get("ejecucion")
    if isinstance(ej_in, dict):
        ej = nuevo.setdefault("ejecucion", json.loads(json.dumps(EJECUCION_DEFECTO)))
        for k in ("modo", "base_path", "spark_args"):
            if k in ej_in:
                ej[k] = ej_in[k]
    if "enlaces" in entrante:
        if not isinstance(entrante["enlaces"], list):
            raise ValueError("enlaces debe ser una lista")
        nuevo["enlaces"] = [{
            "id": e.get("id"), "desde": e.get("desde"), "salida": e.get("salida"),
            "hacia": e.get("hacia"), "entrada": e.get("entrada"),
            "origen": "manual" if e.get("origen") == "manual" else "sugerido",
            "habilitado": bool(e.get("habilitado", True))}
            for e in entrante["enlaces"] if isinstance(e, dict)]
    validar_plan(nuevo)
    return nuevo


def _ej(o, modo=None, base_path=None):
    """Configuracion de ejecucion efectiva (defecto + JSON + overrides de CLI)."""
    ej = {**EJECUCION_DEFECTO, **(o.get("ejecucion") or {})}
    if modo:
        ej["modo"] = modo
    if base_path is not None:  # "" limpia el valor
        ej["base_path"] = base_path
    return ej


def _spark_submit_bin(ej):
    exe = ej.get("spark_submit") or "spark-submit"
    if shutil.which(exe):
        return exe
    cand = os.path.join(os.path.dirname(sys.executable), os.path.basename(exe))  # venv
    return cand if os.path.exists(cand) else exe


def build_command(step, ej):
    a = step["action"]
    if a["type"] == "graph":
        if ej.get("modo") == "spark-submit":
            return [_spark_submit_bin(ej), *ej.get("spark_args", []), a["target"]]
        return [sys.executable, a["target"]]
    return ["ksh", a["target"]]


def _job_env(ej):
    env = dict(os.environ)
    env.update({str(k): str(v) for k, v in (ej.get("env") or {}).items()})
    if ej.get("base_path"):
        env["BNX_BASE_PATH"] = ej["base_path"]
    return env


def _base_efectiva(ej):
    return (ej.get("base_path") or "").rstrip("/")


def materializar_enlace(link, ej, real):
    """Copia <base>/<salida> a <base>/<entrada>. Devuelve True si ok (o dry-run)."""
    base = _base_efectiva(ej)
    shown = base or "${BNX_BASE_PATH}"
    src, dst = f"{shown}/{link['salida']}", f"{shown}/{link['entrada']}"
    remoto = "://" in shown
    print(f"[=] enlace {link['id']}: {link['desde']} -> {link['hacia']}: "
          f"{'aws s3 sync' if remoto else 'copiar'} {src} -> {dst}")
    if not real:
        return True
    if not base:
        print("[x] enlace sin base_path: defina ejecucion.base_path (o --base-path)")
        return False
    if remoto:
        return subprocess.run(["aws", "s3", "sync", src, dst, "--delete"]).returncode == 0
    if not os.path.isdir(src):
        print(f"[x] la salida {src} no existe (el job origen no la produjo)")
        return False
    if os.path.isdir(dst):
        shutil.rmtree(dst)
    os.makedirs(os.path.dirname(dst), exist_ok=True)
    shutil.copytree(src, dst)
    return True


# ---------------------------------------------------------------------------
# Edicion
# ---------------------------------------------------------------------------

def _load(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def _write(path, o):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(o, f, indent=2, ensure_ascii=False)


def _find(o, ref):
    ids = [s for s in o["steps"] if s["id"] == ref]
    if ids:
        return ids[0]
    named = [s for s in o["steps"] if s["name"] == ref]
    if len(named) == 1:
        return named[0]
    if not named:
        raise SystemExit(f"[x] paso no encontrado: {ref!r}")
    raise SystemExit(f"[x] nombre ambiguo {ref!r}; usa el id: " + ", ".join(s["id"] for s in named))


def mostrar(o):
    order = topo_order([s for s in o["steps"]])
    by_id = {s["id"]: s for s in o["steps"]}
    print(f"Plan: {o['plan']}   (direccion: {o.get('direccion', 'prior')})")
    for i, sid in enumerate(order, 1):
        s = by_id[sid]
        deps = ",".join(s["depends_on"]) or "-"
        flag = ("" if s["enabled"] else "  [DESHABILITADO]") + ("  [solo en fallo]" if s.get("solo_en_fallo") else "")
        a = s["action"]
        tgt = os.path.basename(a["target"]) if a.get("target") else (a.get("source") or "-")
        print(f"{i:2}. {sid:<5} {s['name']:<32} <- {deps:<12} {a['type']}:{tgt} ({a['status']}){flag}")
        if s.get("dep_flags"):
            print(f"      flags de dependencia: {s['dep_flags']}")
    ej = _ej(o)
    print(f"Ejecucion: modo={ej['modo']} base_path={ej['base_path'] or '(sin definir)'} "
          f"spark_args={' '.join(ej['spark_args'])}")
    for e in o.get("enlaces", []) or []:
        print(f"Enlace {e['id']}: {e['desde']}:{e['salida']} -> {e['hacia']}:{e['entrada']} "
              f"({e.get('origen', 'manual')}{'' if e.get('habilitado', True) else ', deshabilitado'})")


def invertir(o):
    """Invierte todas las aristas (si la direccion inferida no era la correcta)."""
    rev = defaultdict(list)
    for s in o["steps"]:
        for d in s["depends_on"]:
            rev[d].append(s["id"])
    for s in o["steps"]:
        s["depends_on"] = sorted(rev.get(s["id"], []), key=_num)
    o["direccion"] = "inversa" if o.get("direccion", "prior") == "prior" else "prior"
    topo_order(o["steps"])
    # Los enlaces dependen del orden: se descartan los que dejan de ser validos
    anc = _ancestros(o["steps"])
    antes = o.get("enlaces") or []
    o["enlaces"] = [e for e in antes if e["desde"] in anc.get(e["hacia"], ())]
    if len(o["enlaces"]) != len(antes):
        print(f"[!] {len(antes) - len(o['enlaces'])} enlace(s) descartados por el nuevo orden")


# ---------------------------------------------------------------------------
# Ejecucion
# ---------------------------------------------------------------------------

def ejecutar(o, real=False, modo=None, base_path=None):
    validar_plan(o)
    ej = _ej(o, modo, base_path)
    order = topo_order(o["steps"])
    by_id = {s["id"]: s for s in o["steps"]}
    enlaces = [e for e in (o.get("enlaces") or []) if e.get("habilitado", True)]
    done, failed, faltantes = set(), set(), []
    print(f"[*] Plan {o['plan']} - {'EJECUCION REAL' if real else 'DRY-RUN'} - modo {ej['modo']}")
    if real and not _base_efectiva(ej):
        print("[x] La ejecucion real exige base_path (ejecucion.base_path o --base-path): "
              "sin el, los jobs usarian el bucket S3 por defecto.")
        return False
    for sid in order:
        s = by_id[sid]
        a = s["action"]
        if not s["enabled"]:
            print(f"[-] {sid} {s['name']}: deshabilitado")
            done.add(sid)  # no bloquea a los dependientes
            continue
        fallo_previo = [d for d in s["depends_on"] if d in failed]
        if s.get("solo_en_fallo"):
            if not fallo_previo:
                print(f"[-] {sid} {s['name']}: omitido (solo corre si algo falla)")
                done.add(sid)
                continue
        elif fallo_previo:
            print(f"[x] {sid} {s['name']}: omitido, fallo previo {fallo_previo}")
            failed.add(sid)
            continue
        if a["type"] == "noop" or not a.get("target"):
            motivo = a.get("nota") or a["status"]
            print(f"[~] {sid} {s['name']}: sin accion ({motivo})")
            if a["status"] in ("faltante", "sin_convertir"):
                faltantes.append(f"{sid} {s['name']} -> {a.get('source')}")
                if real and not s["continue_on_error"]:
                    failed.add(sid)
                    continue
            done.add(sid)
            continue
        # Enlaces hacia este paso: se materializan antes de ejecutarlo
        enlace_ok = True
        for e in enlaces:
            if e["hacia"] == sid and e["desde"] in done and e["desde"] not in failed:
                enlace_ok = materializar_enlace(e, ej, real) and enlace_ok
        if not enlace_ok and not s["continue_on_error"]:
            print(f"[x] {sid} {s['name']}: fallo el enlace de entrada, no se ejecuta")
            failed.add(sid)
            continue
        cmd = build_command(s, ej)
        print(f"[>] {sid} {s['name']}: {' '.join(cmd)}")
        if a["status"] in ("faltante", "sin_convertir"):
            faltantes.append(f"{sid} {s['name']} -> {a.get('source')}")
            if real and not s["continue_on_error"]:
                print(f"[x] {sid}: archivo faltante, no se ejecuta")
                failed.add(sid)
                continue
        if not real:
            done.add(sid)
            continue
        rc = subprocess.run(cmd, env=_job_env(ej)).returncode
        if rc == 0:
            done.add(sid)
        else:
            print(f"[x] {sid} termino con codigo {rc}")
            if not s["continue_on_error"]:
                failed.add(sid)
    if faltantes:
        print("[!] Archivos faltantes (no se pueden ejecutar):")
        for f in faltantes:
            print("    -", f)
    print(f"[ok] completados={len(done)} fallidos/omitidos={len(failed)} faltantes={len(faltantes)}")
    return not failed and not faltantes


# ---------------------------------------------------------------------------
# Datos sinteticos de entrada para los jobs del plan
# ---------------------------------------------------------------------------

_READ_VAR = re.compile(
    r'^\s*(\w+?)(?:_df)?\s*=\s*spark\.read\.parquet\(f"\{PARAMS\.BASE_PATH\}/raw/([^"]*)"\)', re.M)


def _resolver_nombre(nombre, defaults):
    """Sustituye {PARAMS.X} por su default literal. Devuelve (nombre, resuelto)."""
    ok = [True]

    def sub(mm):
        v = defaults.get(mm.group(1))
        if v and "$" not in v:
            return v
        ok[0] = False
        return mm.group(0)
    return re.sub(r"\{PARAMS\.(\w+)\}", sub, nombre), ok[0]


_ASSIGN = re.compile(r"^(\w+_df)\s*=\s*(.+)$", re.M)
_STR_LIT = re.compile(r'"((?:[^"\\]|\\.)*)"')
# \b al final evita que 'cast(' / 'NOT (' se corten en 'cas' / 'NO' al retroceder
_IDENT = re.compile(r"(?<![\w.$'])([A-Za-z_]\w*)\b(?!\s*\()(?!')")
_SQL_WORDS = {
    "and", "or", "not", "is", "null", "true", "false", "as", "in", "like", "rlike", "between",
    "case", "when", "then", "else", "end", "cast", "string", "int", "integer", "bigint", "long",
    "double", "float", "decimal", "date", "timestamp", "boolean", "asc", "desc", "nulls", "first",
    "last", "distinct", "over", "partition", "by", "order", "left", "right", "inner", "outer",
    "full", "semi", "anti", "cross", "on", "how", "lit", "col", "if", "row", "rows", "range",
    "interval", "current_date", "current_timestamp", "struct", "array", "map", "binary"}
_COL_CALLS = re.compile(
    r"\.(?:where|filter|orderBy|sort|groupBy|groupby|select|selectExpr|drop|dropDuplicates|"
    r"partitionBy|withColumnRenamed)\(|(?:F\.)?(?:col|expr)\(")


def _columnas_por_fuente(code, fuentes):
    """{fuente_lower: {columna: tipo}} siguiendo el linaje de DataFrames del job.

    Cada asignacion `A_df = B_df.op(...)` atribuye las columnas citadas en sus literales
    de expresion a las fuentes raiz de B (el PRIMER DataFrame del lado derecho). En los
    joins, las claves `on=[...]` van a las raices de todos los lados. Se excluyen las
    columnas que el propio job crea (withColumn / alias / AS). Tipo: numerico si la
    columna se castea a numero o se compara con un literal numerico; fecha si va en
    to_date; si no, string. Es una heuristica sobre el codigo generado por BNX.
    """
    raices = {f.lower() + "_df": {f.lower()} for f in fuentes}
    creadas = set(re.findall(r'withColumn\(\s*"(\w+)"', code))
    creadas |= set(re.findall(r'\.alias\(\s*"(\w+)"\s*\)', code))
    creadas |= set(re.findall(r"\bas\s+`?(\w+)`?\s*(?:,|$)", code, re.I))
    out = defaultdict(dict)

    def tipo(c, txt):
        e = re.escape(c)
        if re.search(rf"cast\([^\"]*?\b{e}\b[^\"]*?\)\s*as\s*(decimal|int|integer|bigint|long|double|float)", txt, re.I) \
                or re.search(rf"\b{e}\b\)?\s*(?:!=|<>|=|<=|>=|<|>)\s*-?\d", txt) \
                or re.search(rf"\d\s*(?:!=|<>|=|<=|>=|<|>)\s*\(?\b{e}\b", txt):
            return "int"
        if re.search(rf"to_date\(\s*(?:trim\()?\s*\b{e}\b", txt, re.I):
            return "date"
        return "string"

    def agregar(roots, cols, txt):
        for r in roots:
            for c in cols:
                if c not in creadas and c.lower() not in _SQL_WORDS and not c.startswith("_bnx"):
                    t = tipo(c, txt)
                    prev = out[r].get(c)
                    out[r][c] = t if prev in (None, "string") else prev

    for m in _ASSIGN.finditer(code):
        dst, rhs = m.group(1).lower(), m.group(2)
        padres = [p.lower() for p in re.findall(r"\b(\w+_df)\b", rhs)]
        if dst in raices and not padres:
            continue
        roots_first = set()
        if padres:
            roots_first = raices.get(padres[0], set())
        todos = set().union(*[raices.get(p, set()) for p in padres]) if padres else set()
        # linaje: el destino hereda las raices de todos sus padres
        raices[dst] = raices.get(dst, set()) | todos
        on = re.search(r"\bon\s*=\s*\[([^\]]*)\]", rhs)
        if on:
            agregar(todos, re.findall(r'"(\w+)"', on.group(1)), rhs)
        # literales de expresion en llamadas que referencian columnas
        if _COL_CALLS.search(rhs):
            for lit in _STR_LIT.findall(rhs):
                if on and f'"{lit}"' in on.group(1):
                    continue
                sin_textos = re.sub(r"'(?:[^'\\]|\\.)*'", "''", lit)  # quitar literales 'texto'
                agregar(roots_first, _IDENT.findall(sin_textos), lit)
    return out


def generar_datos(o, base_path, n_rows=20, seed=42, sobrescribir=False):
    """Escribe parquet sintetico en <base>/raw/<x> para cada lectura de los jobs del plan.

    - Esquema: columnas que el codigo PySpark usa de cada fuente (src.py2spark.infer_input_schema).
      Es una inferencia: si una fuente no tiene columnas detectables se usa una columna 'id'.
    - Valores: src.datagen.build_synthetic_data (mismo generador de la seccion Data Sintetica,
      con PII redactada). Fechas y decimales salen como texto/float.
    - Se omiten las entradas que llegan por un enlace habilitado (las produce el job anterior),
      las rutas con parametros sin resolver y las que ya existen (salvo sobrescribir=True).
    - Solo base_path local; las rutas resueltas deben quedar dentro de base_path.
    Devuelve una lista de dicts {paso, ruta, estado, filas?, columnas?, motivo?}.
    """
    import pyarrow as pa
    import pyarrow.parquet as pq
    from src.py2spark import infer_input_schema
    from src.datagen import build_synthetic_data

    validar_plan(o)
    if not base_path or "://" in base_path:
        raise ValueError("generar datos requiere un base_path local (no s3://)")
    base = os.path.realpath(base_path)
    on = {s["id"] for s in o["steps"] if s["enabled"]}
    por_enlace = {(e["hacia"], e["entrada"]): e["id"] for e in (o.get("enlaces") or [])
                  if e.get("habilitado", True) and e["desde"] in on}
    hechos, rep = set(), []
    for s in o["steps"]:
        a = s["action"]
        if s["id"] not in on or a["type"] != "graph" or not a.get("target") or a["status"] != "ok":
            continue
        try:
            with open(a["target"], "r", encoding="utf-8", errors="replace") as f:
                code = f.read()
        except OSError as e:
            rep.append({"paso": s["id"], "ruta": a["target"], "estado": "error", "motivo": str(e)})
            continue
        defaults = {m.group(1): (m.group(2) if m.group(2) is not None else m.group(3))
                    for m in _PARAM_DEF.finditer(code)}
        esquema = {x["node"].lower(): x["columns"] for x in infer_input_schema(code)}
        # Completar con las columnas que el job usa aguas abajo de cada fuente
        lecturas = [mm.group(1) for mm in _READ_VAR.finditer(code)]
        linaje = _columnas_por_fuente(code, lecturas)
        for fuente, cols in linaje.items():
            base_cols = {c["name"].lower(): c for c in esquema.get(fuente, [])}
            for nombre_c, tipo_c in cols.items():
                prev = base_cols.get(nombre_c.lower())
                if prev is None:
                    base_cols[nombre_c.lower()] = {"name": nombre_c, "type": tipo_c}
                elif tipo_c != "string":
                    prev["type"] = tipo_c
            esquema[fuente] = list(base_cols.values())
        for m in _READ_VAR.finditer(code):
            var, crudo = m.group(1), m.group(2)
            nombre, resuelto = _resolver_nombre(crudo, defaults)
            ruta = "raw/" + nombre.lstrip("/")
            item = {"paso": s["id"], "ruta": ruta}
            if not resuelto:
                rep.append({**item, "estado": "omitido",
                            "motivo": "parametro sin valor; defina la variable de entorno"})
                continue
            if (s["id"], ruta) in por_enlace:
                rep.append({**item, "estado": "omitido",
                            "motivo": f"llega por el enlace {por_enlace[(s['id'], ruta)]}"})
                continue
            if ruta in hechos:
                continue
            dest = os.path.realpath(os.path.join(base, ruta))
            if not dest.startswith(base + os.sep):
                rep.append({**item, "estado": "omitido", "motivo": "la ruta sale de base_path"})
                continue
            if os.path.exists(dest) and not sobrescribir:
                rep.append({**item, "estado": "existe", "motivo": "ya existe (use sobrescribir)"})
                hechos.add(ruta)
                continue
            cols = esquema.get(var.lower()) or []
            nota = None
            if not cols:
                cols, nota = [{"name": "id", "type": "string"}], "sin columnas detectadas: se uso 'id'"
            gen = build_synthetic_data(cols, n_rows=n_rows, fmt="json", seed=seed)
            nombres = [c["name"] for c in gen["columns"]]
            tabla = pa.table({c: [r.get(c) for r in gen["rows"]] for c in nombres})
            if os.path.isdir(dest):
                shutil.rmtree(dest)
            elif os.path.exists(dest):
                os.remove(dest)
            os.makedirs(dest, exist_ok=True)
            pq.write_table(tabla, os.path.join(dest, "part-00000.parquet"))
            hechos.add(ruta)
            rep.append({**item, "estado": "generado", "filas": len(gen["rows"]),
                        "columnas": [f"{c['name']}:{c['type']}" for c in gen["columns"]],
                        **({"motivo": nota} if nota else {})})
    return rep


# ---------------------------------------------------------------------------
# Generador de DAG de Airflow
# ---------------------------------------------------------------------------

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def generar_airflow(o, root=None):
    """Texto de un DAG de Airflow equivalente a la orquestacion (solo pasos habilitados).

    - graph  -> BashOperator con `python3 job.py` o `spark-submit ... job.py` (segun modo)
    - script -> BashOperator `ksh <script>`
    - noop   -> EmptyOperator (tarea Ab Initio sin traduccion)
    - faltante/sin_convertir -> BashOperator que FALLA con mensaje (no se omite en silencio)
    - enlaces -> BashOperator extra entre origen y destino (cp local o aws s3 sync)
    - solo_en_fallo -> trigger_rule one_failed; dependientes de ellos o de pasos
      continue_on_error -> none_failed_min_one_success / all_done
    Las rutas de los jobs se hacen absolutas respecto a la raiz del proyecto: el DAG debe
    correr en una maquina que tenga esos archivos (o ajusta las rutas).
    """
    validar_plan(o)
    root = root or _ROOT
    ej = _ej(o)
    steps = [s for s in o["steps"] if s["enabled"]]
    on = {s["id"] for s in steps}
    by_id = {s["id"]: s for s in o["steps"]}
    tid = {s["id"]: re.sub(r"\W", "_", f"{s['id']}_{s['name']}")[:200] for s in steps}
    env = {str(k): str(v) for k, v in (ej.get("env") or {}).items()}
    if ej.get("base_path"):
        env["BNX_BASE_PATH"] = ej["base_path"]
    dag_id = re.sub(r"\W", "_", "bnx_" + os.path.splitext(o["plan"])[0])
    py = "python3"

    def cmd_for(s):
        a = s["action"]
        if a["type"] == "noop" or not a.get("target"):
            return None
        tgt = a["target"] if os.path.isabs(a["target"]) else os.path.join(root, a["target"])
        if a["type"] == "graph":
            # En el DAG se usa el NOMBRE del binario (el host de Airflow puede ser otro)
            sb = os.path.basename(ej.get("spark_submit") or "spark-submit")
            c = ([sb, *ej.get("spark_args", []), tgt] if ej.get("modo") == "spark-submit" else [py, tgt])
        else:
            c = ["ksh", tgt]
        return shlex.join(c)

    L = ['"""DAG de Airflow generado por src/orquestador.py - plan %s.' % o["plan"],
         'Revisar rutas, conexiones y variables antes de usar en un ambiente real."""',
         "from datetime import datetime", "", "from airflow import DAG",
         "try:  # Airflow 3.x",
         "    from airflow.providers.standard.operators.bash import BashOperator",
         "    from airflow.providers.standard.operators.empty import EmptyOperator",
         "except ImportError:  # Airflow 2.x",
         "    from airflow.operators.bash import BashOperator",
         "    from airflow.operators.empty import EmptyOperator", "",
         f"ENV = {env!r}", "",
         f"with DAG(dag_id={dag_id!r}, schedule=None, start_date=datetime(2024, 1, 1),",
         "         catchup=False, tags=['bnx', 'abinitio']) as dag:"]

    for s in steps:
        a = s["action"]
        deps = [by_id[d] for d in s["depends_on"] if d in on]
        if s.get("solo_en_fallo"):
            rule = "one_failed"
        elif any(d.get("solo_en_fallo") for d in deps):
            rule = "none_failed_min_one_success"
        elif any(d.get("continue_on_error") for d in deps):
            rule = "all_done"
        else:
            rule = "all_success"
        name = tid[s["id"]]
        L.append(f"    # {s['name']} ({s['id']}) - {a['type']}/{a['status']}")
        if a["status"] in ("faltante", "sin_convertir"):
            msg = f"FALTANTE: {a.get('source')} ({a['status']})"
            L.append(f"    {name} = BashOperator(task_id={name!r}, trigger_rule={rule!r},")
            L.append(f"        bash_command={('echo ' + shlex.quote(msg) + ' >&2; exit 1')!r})")
        elif cmd_for(s) is None:
            L.append(f"    {name} = EmptyOperator(task_id={name!r}, trigger_rule={rule!r})")
        else:
            L.append(f"    {name} = BashOperator(task_id={name!r}, trigger_rule={rule!r},")
            L.append(f"        bash_command={cmd_for(s)!r}, env=ENV, append_env=True)")

    links = [e for e in (o.get("enlaces") or []) if e.get("habilitado", True)
             and e["desde"] in on and e["hacia"] in on]
    base = '"${BNX_BASE_PATH:?defina BNX_BASE_PATH}"'
    for e in links:
        src, dst = f"{base}/{e['salida']}", f"{base}/{e['entrada']}"
        lt = re.sub(r"\W", "_", f"enlace_{e['id']}_{e['desde']}_{e['hacia']}")
        if "://" in (ej.get("base_path") or ""):
            c = f"aws s3 sync {src} {dst} --delete"
        else:
            c = f"set -e; rm -rf {dst}; mkdir -p \"$(dirname {dst})\"; cp -R {src} {dst}"
        L.append(f"    # enlace {e['id']}: {e['salida']} -> {e['entrada']}")
        L.append(f"    {lt} = BashOperator(task_id={lt!r}, bash_command={c!r}, env=ENV, append_env=True)")
        L.append(f"    {tid[e['desde']]} >> {lt} >> {tid[e['hacia']]}")
    L.append("")
    for s in steps:
        for d in s["depends_on"]:
            if d in on:
                L.append(f"    {tid[d]} >> {tid[s['id']]}")
    return "\n".join(L) + "\n"


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main(argv=None):
    ap = argparse.ArgumentParser(description="Orquestador editable de planes Ab Initio")
    sub = ap.add_subparsers(dest="cmd", required=True)
    g = sub.add_parser("generar")
    g.add_argument("ab_folder")
    g.add_argument("converted_dir")
    g.add_argument("--out", default=None)
    for c in ("mostrar", "invertir", "ejecutar"):
        p = sub.add_parser(c)
        p.add_argument("json")
        if c == "ejecutar":
            p.add_argument("--ejecutar", action="store_true", help="ejecutar de verdad (default: dry-run)")
            p.add_argument("--modo", choices=["python", "spark-submit"], default=None)
            p.add_argument("--base-path", default=None)
    for c in ("dep-add", "dep-rm"):
        p = sub.add_parser(c)
        p.add_argument("json")
        p.add_argument("paso")
        p.add_argument("--despues-de", required=True)
    for c in ("deshabilitar", "habilitar"):
        p = sub.add_parser(c)
        p.add_argument("json")
        p.add_argument("paso")
    c = sub.add_parser("config")
    c.add_argument("json")
    c.add_argument("--modo", choices=["python", "spark-submit"], default=None)
    c.add_argument("--base-path", default=None)
    c.add_argument("--spark-args", default=None,
                   help='argumentos de spark-submit en una cadena, ej. "--master local[2] --conf spark.x=y" '
                        "(reemplaza la lista)")
    for c_ in ("enlaces", "sugerir"):
        sub.add_parser(c_).add_argument("json")
    ea = sub.add_parser("enlace-add")
    ea.add_argument("json")
    ea.add_argument("--desde", required=True)
    ea.add_argument("--salida", required=True, help="zona/nombre, ej. output/op_x")
    ea.add_argument("--hacia", required=True)
    ea.add_argument("--entrada", required=True, help="zona/nombre, ej. raw/input_y")
    er = sub.add_parser("enlace-rm")
    er.add_argument("json")
    er.add_argument("id")
    dt = sub.add_parser("datos", help="genera parquet sintetico de entrada en <base>/raw/")
    dt.add_argument("json")
    dt.add_argument("--base-path", default=None, help="default: ejecucion.base_path del JSON")
    dt.add_argument("--filas", type=int, default=20)
    dt.add_argument("--seed", type=int, default=42)
    dt.add_argument("--sobrescribir", action="store_true")
    af = sub.add_parser("airflow")
    af.add_argument("json")
    af.add_argument("--out", default=None)
    a = ap.parse_args(argv)
    try:
        return _run(a)
    except ValueError as e:  # ciclo de dependencias: el cambio no se guarda
        print(f"[x] {e}. Cambio NO guardado.")
        return 1


def _run(a):
    if a.cmd == "generar":
        orchs = build(a.ab_folder, a.converted_dir)
        paths = save_all(orchs, a.out or a.converted_dir)
        for p in paths:
            print("[ok]", p)
        return 0
    o = _load(a.json)
    if a.cmd == "mostrar":
        mostrar(o)
        return 0
    if a.cmd == "ejecutar":
        return 0 if ejecutar(o, real=a.ejecutar, modo=a.modo, base_path=a.base_path) else 1
    if a.cmd == "datos":
        base = a.base_path if a.base_path is not None else _ej(o)["base_path"]
        rep = generar_datos(o, base, n_rows=max(1, min(a.filas, 100000)), seed=a.seed,
                            sobrescribir=a.sobrescribir)
        for r in rep:
            extra = f" {r['filas']} filas {r['columnas']}" if r["estado"] == "generado" else ""
            print(f"[{r['estado']}] {r['paso']} {r['ruta']}{extra}"
                  + (f" - {r['motivo']}" if r.get("motivo") else ""))
        if not rep:
            print("[!] ningun paso con job convertido para generar datos")
        return 0
    if a.cmd == "airflow":
        txt = generar_airflow(o)
        out = a.out or os.path.join(os.path.dirname(os.path.abspath(a.json)),
                                    "dag_" + os.path.splitext(o["plan"])[0] + ".py")
        with open(out, "w", encoding="utf-8") as f:
            f.write(txt)
        print("[ok] DAG:", out)
        return 0
    if a.cmd == "enlaces":
        mostrar(o)
        return 0
    if a.cmd == "config":
        o["ejecucion"] = _ej(o, a.modo, a.base_path)
        if a.spark_args is not None:
            o["ejecucion"]["spark_args"] = shlex.split(a.spark_args)
        validar_plan(o)
    elif a.cmd == "sugerir":
        o["enlaces"] = sugerir_enlaces(o["steps"], o.get("enlaces"))
        validar_plan(o)
    elif a.cmd == "enlace-add":
        sd, sh = _find(o, a.desde), _find(o, a.hacia)
        ids = [_num(e["id"]) for e in o.get("enlaces", [])] + [0]
        o.setdefault("enlaces", []).append({
            "id": f"e{max(ids) + 1}", "desde": sd["id"], "salida": a.salida,
            "hacia": sh["id"], "entrada": a.entrada, "origen": "manual", "habilitado": True})
        validar_plan(o)
    elif a.cmd == "enlace-rm":
        n = len(o.get("enlaces", []))
        o["enlaces"] = [e for e in o.get("enlaces", []) if e["id"] != a.id]
        if len(o["enlaces"]) == n:
            raise SystemExit(f"[x] enlace no encontrado: {a.id}")
    elif a.cmd == "invertir":
        invertir(o)
    elif a.cmd in ("deshabilitar", "habilitar"):
        _find(o, a.paso)["enabled"] = a.cmd == "habilitar"
    else:
        s, d = _find(o, a.paso), _find(o, a.despues_de)
        if a.cmd == "dep-add" and d["id"] not in s["depends_on"]:
            s["depends_on"] = sorted(s["depends_on"] + [d["id"]], key=_num)
        elif a.cmd == "dep-rm":
            s["depends_on"] = [x for x in s["depends_on"] if x != d["id"]]
        validar_plan(o)  # rechaza ciclos y enlaces que dejen de ser validos (no se guarda)
    _write(a.json, o)
    mostrar(o)
    return 0


if __name__ == "__main__":
    sys.exit(main())
