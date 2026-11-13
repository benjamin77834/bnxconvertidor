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
    python -m src.orquestador componer  A.json B.json [C.json ...] --nombre X [--sin-cadena]
                                        (plan de planes: cada paso es otra orquestacion)
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
    python -m src.orquestador nueva     NOMBRE --proyecto P [--out DIR]
                                        (orquestacion desde cero, sin .plan: origen "manual")
    python -m src.orquestador paso-add  orquestacion_X.json --tipo T --nombre N
                                        [--despues-de OTRO ...] [--campo clave=valor ...]
    python -m src.orquestador paso-rm   orquestacion_X.json PASO
    python -m src.orquestador esperar   RUTA [--timeout S] [--intervalo S]   (sensor)
PASO se indica por id (t17) o por nombre exacto si es unico.

Tipos de paso (ubicacion): graph/script (local, desde planes) y, para orquestaciones
manuales o editadas a mano: python, shell, spark_submit, esperar_archivo (local);
ssh, http (remoto); glue_job, emr_step, lambda, s3_copy (nube AWS, via `aws` CLI).
Todos se ejecutan SIN shell (lista argv); nunca se guardan credenciales: ssh usa
clave/agent (BatchMode), http toma el token de una variable de entorno (token_env),
aws usa su cadena de credenciales (--profile/--region opcionales).

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

def _ckey(name):
    """Clave de comparacion: sin ruta (/ o \\), sin prefijo numerico, sin mayusculas."""
    return pm._norm_name(name).lower()


def _index_converted(converted_dir):
    """{nombre_normalizado.mp: ruta_py} a partir de '<base>_<target>.py'.
    Las claves son minusculas y sin prefijo numerico ('2_T002_x_spark.py' -> 't002_x.mp');
    se consulta con _ckey()."""
    idx = {}
    if not converted_dir or not os.path.isdir(converted_dir):
        return idx
    for f in sorted(os.listdir(converted_dir)):
        m = re.match(r"^(.*)_(?:spark|glue|flink|python)\.py$", f, re.I)
        if m:
            idx.setdefault(_ckey(m.group(1) + ".mp"), os.path.join(converted_dir, f))
    return idx


def _nodo(nodes, name):
    """Nodo por nombre sin distinguir mayusculas."""
    if name in nodes:
        return nodes[name]
    low = name.lower()
    return next((n for k, n in nodes.items() if k.lower() == low), None)


def _resolve_action(refs, nodes, converted):
    """Decide que hace un paso segun los archivos que referencia.

    Estados de un grafo/pset: ok (hay .py convertido), sin_convertir (el .mp esta pero
    no hay .py) y faltante (no esta el .mp). Para un pset el archivo que importa es el
    .mp de su !prototype: 'source' lo nombra (no al pset)."""
    converted = {k.lower(): v for k, v in converted.items()}
    for r in refs:
        kind = pm._kind_of(r)
        node = _nodo(nodes, r)
        if kind == "graph":
            if _ckey(r) in converted:
                return {"type": "graph", "target": converted[_ckey(r)], "source": r, "status": "ok"}
            st = "sin_convertir" if node and node.get("present") else "faltante"
            return {"type": "graph", "target": None, "source": r, "status": st}
        if kind == "pset":
            proto = (node or {}).get("prototype")
            g = _ckey(proto) if proto else None
            if g and g in converted:
                return {"type": "graph", "target": converted[g], "source": r, "status": "ok"}
            # el .py puede llamarse como el pset (T002_..._D_spark.py)
            alt = _ckey(os.path.splitext(r)[0] + ".mp")
            if alt in converted:
                return {"type": "graph", "target": converted[alt], "source": r, "status": "ok"}
            if proto:
                src = pm._norm_name(proto)
                gn = _nodo(nodes, src)
                st = "sin_convertir" if gn and gn.get("present") else "faltante"
                return {"type": "graph", "target": None, "source": src, "status": st,
                        "pset": r}
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
            elif st["action"]["type"] == "script" and st["action"]["status"] == "ok":
                # El .ksh se ejecuta/regenera por ruta: la del archivo en la carpeta Ab Initio
                # (relativa a la raiz del proyecto si esta dentro), no el nombre suelto.
                fp = os.path.abspath(os.path.join(ab_folder, _nodo(m["nodes"], st["action"]["target"])["file"]))
                st["action"]["target"] = fp if os.path.relpath(fp, _ROOT).startswith("..") else os.path.relpath(fp, _ROOT)
        topo_order(steps)  # valida que no haya ciclos
        stem = os.path.splitext(name)[0]
        base = {"plan": name, "nombre": stem, "direccion": "prior",
                "ejecucion": json.loads(json.dumps(EJECUCION_DEFECTO)),
                "steps": steps, "enlaces": sugerir_enlaces(steps)}
        result[stem] = base
        # Una orquestacion POR CADA pset que instancia este plan, con sus parametros
        # aplicados como variables de entorno de los jobs (los jobs leen PARAMS.X de
        # os.environ, asi el valor del pset gana sobre el default del grafo).
        for pset in sorted(m["instances"].get(name, [])):
            pn = m["nodes"].get(pset) or {}
            if not pn.get("present"):
                continue
            aplicados, pendientes = params_a_env(pn.get("params") or {})
            pstem = os.path.splitext(pset)[0]
            # Si el pset repite el nombre del plan (plan_x_2.pset), solo el sufijo: plan_x__2
            sufijo = pstem[len(stem):].strip("_-.") if pstem.lower().startswith(stem.lower()) else pstem
            nombre = f"{stem}__{sufijo or 'pset'}"
            v = json.loads(json.dumps(base))
            v["nombre"] = nombre
            v["pset"] = pset
            v["ejecucion"]["env"] = aplicados
            v["params_pendientes"] = pendientes
            result[nombre] = v
    return result


_ENV_NAME = re.compile(r"^[A-Za-z_]\w*$")


def params_a_env(params):
    """Parametros de un pset -> (env aplicable, {param: motivo} no aplicados).
    Solo valores LITERALES: los que aun son expresiones de Ab Initio ($VAR, ${VAR},
    $[...]) no se pueden resolver aqui y se reportan."""
    env, pend = {}, {}
    for k, v in (params or {}).items():
        v = "" if v is None else str(v)
        if not _ENV_NAME.match(k):
            pend[k] = "nombre no valido como variable de entorno"
        elif "$" in v:
            pend[k] = "expresion de Ab Initio sin resolver: " + v[:80]
        elif any(c in v for c in "\x00\r\n"):
            pend[k] = "valor con caracteres de control"
        else:
            env[k] = v
    return env, pend


def _ruta_plan(target):
    """Ruta absoluta de una sub-orquestacion (las rutas se guardan relativas al proyecto)."""
    return target if os.path.isabs(target) else os.path.join(_ROOT, target)


def componer(nombre, planes, en_cadena=True):
    """Plan de PLANES: una orquestacion cuyos pasos son otras orquestaciones.
    planes: rutas de orquestacion_*.json (relativas a la raiz del proyecto o absolutas).
    en_cadena=True: cada plan depende del anterior (el orden dado); luego se acomoda
    en el diagrama igual que cualquier plan."""
    if not re.fullmatch(r"[A-Za-z0-9][\w.\-]{0,80}", nombre or ""):
        raise ValueError("nombre invalido (letras, numeros, . _ -)")
    if len(planes or []) < 2:
        raise ValueError("un plan de planes necesita al menos 2 planes")
    if len(set(planes)) != len(planes):
        raise ValueError("hay planes repetidos")
    steps = []
    for i, ruta in enumerate(planes, 1):
        fp = _ruta_plan(ruta)
        with open(fp, "r", encoding="utf-8") as f:
            sub = json.load(f)
        if sub.get("tipo") == "plan_de_planes":
            raise ValueError(f"{os.path.basename(fp)} ya es un plan de planes (no se anidan)")
        validar_plan(sub)
        rel = os.path.relpath(fp, _ROOT) if not os.path.relpath(fp, _ROOT).startswith("..") else fp
        steps.append({
            "id": f"p{i}", "name": sub.get("nombre") or os.path.splitext(sub.get("plan", "plan"))[0],
            "action": {"type": "plan", "target": rel, "source": sub.get("plan"),
                       "status": "ok", "pset": sub.get("pset"),
                       "pasos": len(sub.get("steps") or [])},
            "depends_on": [f"p{i-1}"] if (en_cadena and i > 1) else [],
            "dep_flags": {}, "solo_en_fallo": False, "enabled": True, "continue_on_error": False,
        })
    o = {"tipo": "plan_de_planes", "plan": nombre + ".planes", "nombre": "PLANES_" + nombre,
         "direccion": "prior", "ejecucion": json.loads(json.dumps(EJECUCION_DEFECTO)),
         "steps": steps, "enlaces": []}
    validar_plan(o)
    return o


def save_all(orchs, out_dir):
    os.makedirs(out_dir, exist_ok=True)
    paths = []
    for name, o in orchs.items():
        p = os.path.join(out_dir, "orquestacion_" + (o.get("nombre") or os.path.splitext(name)[0]) + ".json")
        with open(p, "w", encoding="utf-8") as f:
            json.dump(o, f, indent=2, ensure_ascii=False)
        paths.append(p)
    return paths


def refrescar_acciones(almacenado, nuevo):
    """Copia a `almacenado` la accion de cada paso de `nuevo` (mismo id y nombre),
    conservando todo lo editado (dependencias, flags, enlaces, ejecucion). Solo planes
    generados desde .plan; las orquestaciones manuales y planes de planes no se tocan."""
    if almacenado.get("origen") == "manual" or almacenado.get("tipo") == "plan_de_planes":
        return almacenado
    por_id = {s["id"]: s for s in nuevo.get("steps", [])}
    for s in almacenado.get("steps", []):
        n = por_id.get(s["id"])
        if n and n["name"] == s["name"] and s.get("action", {}).get("type") in ("graph", "script", "noop"):
            s["action"] = n["action"]
    return almacenado


def pendientes_de_convertir(ab_folder, converted_dir):
    """Archivos .mp presentes en la carpeta que aun no tienen <grafo>_<target>.py."""
    conv = _index_converted(converted_dir)
    return sorted(f for f in os.listdir(ab_folder)
                  if f.lower().endswith(".mp") and _ckey(f) not in conv)


def convertir_pendientes(ab_folder, out_dir, solo=None, target="spark", timeout=900):
    """Convierte (con scripts/convertir_lote.convertir) los .mp sin convertir.
    solo: nombre de un .mp (con o sin prefijo/ruta/mayusculas) para convertir uno solo.
    Devuelve la lista de resultados de convertir()."""
    import importlib.util
    spec = importlib.util.spec_from_file_location(
        "convertir_lote", os.path.join(_ROOT, "scripts", "convertir_lote.py"))
    cl = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(cl)
    os.makedirs(out_dir, exist_ok=True)
    quiero = _ckey(solo) if solo else None
    filas = []
    for f in pendientes_de_convertir(ab_folder, out_dir):
        if quiero and _ckey(f) != quiero:
            continue
        filas.append(cl.convertir(os.path.join(ab_folder, f), out_dir, target, timeout))
    return filas


def regenerar(ab_folder, out_dir):
    """Reconstruye las orquestaciones de la carpeta. Las que ya existen conservan lo
    editado (solo se refresca la accion de cada paso); las nuevas se crean. Devuelve rutas."""
    orchs = build(ab_folder, out_dir)
    rutas = []
    for name, o in orchs.items():
        p = os.path.join(out_dir, "orquestacion_" + (o.get("nombre") or os.path.splitext(name)[0]) + ".json")
        if os.path.isfile(p):
            try:
                with open(p, "r", encoding="utf-8") as f:
                    o = refrescar_acciones(json.load(f), o)
                validar_plan(o)
            except (ValueError, OSError, KeyError):
                pass  # almacenado ilegible/invalido: se reemplaza por el recien generado
        rutas += save_all({name: o}, out_dir)
    return rutas



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
        nombre, resuelto = _resolver_nombre(nombre, defaults)
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
        out[kind].append({"ruta": f"{zona}/{nombre}", "resuelto": resuelto})
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
    if not isinstance(steps, list) or (not steps and o.get("origen") != "manual"):
        raise ValueError("plan sin pasos")
    ids = [s.get("id") for s in steps]
    if not all(isinstance(i, str) for i in ids) or len(set(ids)) != len(ids):
        raise ValueError("ids de pasos invalidos o repetidos")
    for s in steps:
        if not isinstance(s.get("depends_on"), list) or any(d not in ids for d in s["depends_on"]):
            raise ValueError(f"dependencias invalidas en {s.get('id')}")
        act = s.get("action")
        if isinstance(act, dict) and act.get("type") in TIPOS_NUEVOS:
            try:
                normalizar_accion(act)
            except ValueError as e:
                raise ValueError(f"{s['id']}: {e}")
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
        if ej.get("aws") is not None:
            aws = ej["aws"]
            if not isinstance(aws, dict) or set(aws) - {"profile", "region"}:
                raise ValueError("ejecucion.aws solo admite profile y region")
            _perfil_region(aws)


def _fusionar_pasos_planes(almacenado, entrante):
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
    return nuevo


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
    if almacenado.get("origen") == "manual":
        # Orquestacion creada desde cero: ademas se pueden agregar, editar y borrar pasos
        # (cada accion se normaliza con la lista blanca de campos de su tipo).
        nuevo = json.loads(json.dumps(almacenado))
        nuevo["steps"] = _pasos_manuales(almacenado, entrante.get("steps"))
        vivos = {s["id"] for s in nuevo["steps"]}
        nuevo["enlaces"] = [e for e in (nuevo.get("enlaces") or [])
                            if e.get("desde") in vivos and e.get("hacia") in vivos]
    else:
        nuevo = _fusionar_pasos_planes(almacenado, entrante)
    if entrante.get("direccion") in ("prior", "inversa"):
        nuevo["direccion"] = entrante["direccion"]
    ej_in = entrante.get("ejecucion")
    if isinstance(ej_in, dict):
        ej = nuevo.setdefault("ejecucion", json.loads(json.dumps(EJECUCION_DEFECTO)))
        for k in ("modo", "base_path", "spark_args"):
            if k in ej_in:
                ej[k] = ej_in[k]
        if isinstance(ej_in.get("aws"), dict):
            ej["aws"] = {k: v for k, v in ej_in["aws"].items() if k in ("profile", "region") and v}
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


_WIN_ABS = re.compile(r"^(?:[A-Za-z]:[\\/]|\\\\|//[^/])")   # C:\x  C:/x  \\srv\share  //srv/share


def normalizar_base_path(bp):
    """Deja el base_path en una forma unica, sin separador final.

    - s3://bucket/prefijo/ -> s3://bucket/prefijo
    - Windows ('C:\\Users\\X\\', 'C:/Users/X/', '"C:\\Users\\X"') -> 'C:/Users/X' (barras
      normales: las entienden Windows, Python y Spark y no se rompen al escapar JSON/f-strings)
    - POSIX -> os.path.normpath
    Funciona igual en Mac que en Windows (usa ntpath explicito para rutas de Windows)."""
    import ntpath
    bp = (bp or "").strip().strip('"').strip("'").strip()
    if not bp:
        return ""
    if "://" in bp:
        return bp.rstrip("/")
    if _WIN_ABS.match(bp):
        n = ntpath.normpath(bp).replace("\\", "/")
        return n if len(n) <= 3 and n.endswith(":/") else n.rstrip("/")
    return os.path.normpath(os.path.expanduser(bp))


def validar_base_path(bp, crear=True, windows=None):
    """Valida el base_path de una ejecucion REAL. Devuelve (ruta_normalizada, error|None).

    Debe ser s3://bucket[/prefijo] o una ruta local ABSOLUTA de este sistema (no la raiz).
    Local: se crea si no existe (crear=True) y se comprueba que se pueda escribir.
    `windows` fuerza el sistema (por defecto os.name == 'nt'); sirve para pruebas."""
    windows = (os.name == "nt") if windows is None else windows
    n = normalizar_base_path(bp)
    if not n:
        return "", "indica el base_path (ruta local absoluta o s3://bucket/prefijo)"
    if any(c in n for c in "\x00\r\n"):
        return n, "el base_path tiene caracteres de control"
    if "://" in n:
        return (n, None) if _S3_URL.match(n) else (n, "base_path s3:// invalido (use s3://bucket/prefijo)")
    es_win = bool(_WIN_ABS.match(n))
    if es_win != windows:
        return n, ("la ruta es de Windows pero el servidor no corre en Windows"
                   if es_win else "ruta absoluta de Windows requerida (ej. C:/Users/usuario/bnx)")
    if not es_win and not os.path.isabs(n):
        return n, "el base_path debe ser una ruta absoluta (no relativa)"
    if n in ("/", "") or (es_win and re.fullmatch(r"[A-Za-z]:/?", n)):
        return n, "el base_path no puede ser la raiz del disco"
    if crear:
        try:
            os.makedirs(n, exist_ok=True)
        except OSError as e:
            return n, f"no se pudo crear {n}: {e}"
    if os.path.isdir(n) and not os.access(n, os.W_OK):
        return n, f"sin permiso de escritura en {n}"
    return n, None


def _ej(o, modo=None, base_path=None, spark_args=None):
    """Configuracion de ejecucion efectiva (defecto + JSON + overrides de CLI)."""
    ej = {**EJECUCION_DEFECTO, **(o.get("ejecucion") or {})}
    if modo:
        ej["modo"] = modo
    if base_path is not None:  # "" limpia el valor
        ej["base_path"] = base_path
    if spark_args is not None:
        ej["spark_args"] = list(spark_args)
    return ej


def _spark_submit_bin(ej):
    """spark-submit: el configurado / del PATH (en Windows spark-submit.cmd), el del venv o
    Anaconda, el del paquete pyspark (pyspark/bin) o SPARK_HOME."""
    exe = ej.get("spark_submit") or "spark-submit"
    w = shutil.which(exe)
    if w:
        # Ruta COMPLETA que resolvio which (en Windows incluye la extension .cmd/.bat via
        # PATHEXT). Devolver el nombre pelado ('spark-submit') hace que subprocess falle con
        # [WinError 2] aunque which lo encontrara: CreateProcess no aplica PATHEXT.
        return w if os.name == "nt" else exe
    nombres = [os.path.basename(exe)] + ([os.path.basename(exe) + ".cmd"] if os.name == "nt" else [])
    dirs = [os.path.dirname(sys.executable), os.path.join(os.path.dirname(sys.executable), "Scripts")]
    try:
        import importlib.util as _iu
        spec = _iu.find_spec("pyspark")
        if spec and spec.origin:
            dirs.append(os.path.join(os.path.dirname(spec.origin), "bin"))
    except (ImportError, ValueError):
        pass
    if os.environ.get("SPARK_HOME"):
        dirs.append(os.path.join(os.environ["SPARK_HOME"], "bin"))
    for d in dirs:
        for n in nombres:
            cand = os.path.join(d, n)
            if os.path.exists(cand):
                return cand
    return exe


# ---------------------------------------------------------------------------
# Pasos por ubicacion: local / remoto / nube (orquestaciones manuales o editadas)
# ---------------------------------------------------------------------------

# tipo -> ubicacion y campos. Todo se ejecuta como lista argv (sin shell); nada de
# credenciales en el JSON: ssh usa clave/agent, http toma el token de una variable de
# entorno (token_env) y aws usa su cadena de credenciales (profile/region opcionales).
TIPOS_NUEVOS = {
    "python": {"ubic": "local", "req": ["target"], "opt": ["args"]},
    "shell": {"ubic": "local", "req": ["comando"], "opt": []},
    "spark_submit": {"ubic": "local", "req": ["target"], "opt": ["master", "spark_args", "args"]},
    "esperar_archivo": {"ubic": "local", "req": ["ruta"],       # nube si la ruta es s3://
                        "opt": ["timeout_s", "intervalo_s", "profile", "region"]},
    "ssh": {"ubic": "remoto", "req": ["host", "comando"], "opt": ["usuario", "puerto", "identidad"]},
    "http": {"ubic": "remoto", "req": ["url"],
             "opt": ["metodo", "body", "headers", "token_env", "timeout_s"]},
    "glue_job": {"ubic": "nube", "req": ["job_name"], "opt": ["args", "profile", "region"]},
    "emr_step": {"ubic": "nube", "req": ["cluster_id", "script"],
                 "opt": ["args", "nombre", "action_on_failure", "profile", "region"]},
    "lambda": {"ubic": "nube", "req": ["function_name"], "opt": ["payload", "profile", "region"]},
    "s3_copy": {"ubic": "nube", "req": ["origen", "destino"], "opt": ["recursivo", "profile", "region"]},
}
_CTRL = re.compile(r"[\x00-\x1f\x7f]")
_S3_URL = re.compile(r"^s3://[A-Za-z0-9][\w.\-]*(/[^\x00-\x20\x7f]*)?$")
_HTTP_URL = re.compile(r"^https?://[^\s\x00-\x1f\x7f]+$")
_HOST = re.compile(r"^[A-Za-z0-9][A-Za-z0-9.\-]{0,252}$")
_USER = re.compile(r"^[A-Za-z_][\w.\-]{0,63}$")
_HDR_NAME = re.compile(r"^[A-Za-z0-9][A-Za-z0-9\-]{0,63}$")
_HDR_SECRETO = re.compile(r"auth|token|secret|key|passw|cookie|credential", re.I)
_REGION = re.compile(r"^[a-z]{2}(-[a-z0-9]+)+-\d$")
_PERFIL = re.compile(r"^[\w.\-@]{1,128}$")
_METODOS = ("GET", "POST", "PUT", "PATCH", "DELETE")


def ubicacion_de(a):
    """'local' | 'remoto' | 'nube' de una accion."""
    if a.get("type") == "esperar_archivo" and str(a.get("ruta", "")).startswith("s3://"):
        return "nube"
    return TIPOS_NUEVOS.get(a.get("type"), {}).get("ubic", "local")


def _txt(v, campo, maxlen=4000):
    if not isinstance(v, str) or not v.strip():
        raise ValueError(f"{campo} es requerido (texto)")
    if len(v) > maxlen or _CTRL.search(v):
        raise ValueError(f"{campo}: demasiado largo o con caracteres de control")
    return v


def _ruta_txt(v, campo):
    v = _txt(v, campo)
    if v.startswith("-"):
        raise ValueError(f"{campo}: no puede empezar con '-'")
    return v


def _lista_txt(v, campo):
    if v is None:
        return []
    if not isinstance(v, list) or len(v) > 200:
        raise ValueError(f"{campo} debe ser una lista de textos")
    out = []
    for x in v:
        if isinstance(x, (int, float)) and not isinstance(x, bool):
            x = str(x)
        if not isinstance(x, str) or len(x) > 4000 or _CTRL.search(x):
            raise ValueError(f"{campo}: elemento invalido")
        out.append(x)
    return out


def _entero(v, campo, lo, hi, defecto):
    if v is None or v == "":
        return defecto
    if isinstance(v, bool) or not isinstance(v, (int, str)) or not re.fullmatch(r"\d+", str(v)):
        raise ValueError(f"{campo} debe ser un entero")
    n = int(v)
    if not lo <= n <= hi:
        raise ValueError(f"{campo} debe estar entre {lo} y {hi}")
    return n


def _perfil_region(src, out=None):
    """Valida profile/region (del paso o de ejecucion.aws); si out, los copia."""
    for k, rx in (("profile", _PERFIL), ("region", _REGION)):
        v = src.get(k)
        if v in (None, ""):
            continue
        if not isinstance(v, str) or not rx.match(v):
            raise ValueError(f"{k} invalido")
        if out is not None:
            out[k] = v


def _rel_proyecto(p):
    if os.path.isabs(p):
        rel = os.path.relpath(p, _ROOT)
        return p if rel.startswith("..") else rel
    return p


def normalizar_accion(a, estricto=False):
    """Valida la accion de un paso y devuelve una copia limpia (solo campos de su tipo).

    Lanza ValueError con el motivo. estricto=True (ediciones desde la GUI): un paso
    "graph" solo puede apuntar a un <grafo>_<target>.py dentro de output/.
    """
    if not isinstance(a, dict):
        raise ValueError("accion invalida")
    t = a.get("type")
    if t not in TIPOS_NUEVOS and t != "graph":
        raise ValueError(f"tipo de paso no soportado: {t!r}")
    out = {"type": t, "status": "ok"}
    if t == "graph":
        tg = _ruta_txt(a.get("target"), "target")
        if not tg.endswith(".py"):
            raise ValueError("target debe ser un .py convertido")
        if estricto:
            base = os.path.realpath(os.path.join(_ROOT, "output"))
            real = os.path.realpath(_ruta_plan(tg))
            if not real.startswith(base + os.sep) or not re.fullmatch(
                    r"[\w.\-]+_(?:spark|glue|flink|python)\.py", os.path.basename(real)):
                raise ValueError("target debe ser un <grafo>_spark.py dentro de output/")
        out["target"] = _rel_proyecto(tg)
        out["source"] = os.path.basename(tg)
        if os.path.isfile(_ruta_plan(out["target"])):
            out["io"] = parse_job_io(_ruta_plan(out["target"]))
        else:
            out["status"] = "faltante"
        out["ubicacion"] = "local"
        return out
    if t in ("python", "spark_submit"):
        out["target"] = _ruta_txt(a.get("target"), "target")
        out["args"] = _lista_txt(a.get("args"), "args")
        if t == "spark_submit":
            if a.get("master"):
                out["master"] = _ruta_txt(a["master"], "master")
            out["spark_args"] = _lista_txt(a.get("spark_args"), "spark_args")
    elif t == "shell":
        out["comando"] = _txt(a.get("comando"), "comando")
        try:
            if not shlex.split(out["comando"]):
                raise ValueError
        except ValueError:
            raise ValueError("comando: texto vacio o con comillas sin cerrar")
    elif t == "esperar_archivo":
        r = _txt(a.get("ruta"), "ruta")
        if r.startswith("-") or ("://" in r and not _S3_URL.match(r)):
            raise ValueError("ruta: use una ruta local o s3://bucket/clave")
        out["ruta"] = r
        out["timeout_s"] = _entero(a.get("timeout_s"), "timeout_s", 1, 86400, 300)
        out["intervalo_s"] = _entero(a.get("intervalo_s"), "intervalo_s", 1, 3600, 10)
    elif t == "ssh":
        h = _txt(a.get("host"), "host", 253)
        if not _HOST.match(h):
            raise ValueError("host invalido")
        out["host"] = h
        if a.get("usuario"):
            if not isinstance(a["usuario"], str) or not _USER.match(a["usuario"]):
                raise ValueError("usuario invalido")
            out["usuario"] = a["usuario"]
        if a.get("puerto") not in (None, ""):
            out["puerto"] = _entero(a["puerto"], "puerto", 1, 65535, None)
        if a.get("identidad"):
            idt = _ruta_txt(a["identidad"], "identidad")
            if "PRIVATE KEY" in idt:
                raise ValueError("identidad: es la RUTA de la clave, nunca su contenido")
            out["identidad"] = idt
        out["comando"] = _txt(a.get("comando"), "comando")
    elif t == "http":
        m = str(a.get("metodo") or "GET").upper()
        if m not in _METODOS:
            raise ValueError("metodo debe ser " + "/".join(_METODOS))
        out["metodo"] = m
        u = _txt(a.get("url"), "url", 2000)
        if not _HTTP_URL.match(u):
            raise ValueError("url debe empezar con http:// o https://")
        out["url"] = u
        body = a.get("body")
        if body not in (None, ""):
            if isinstance(body, str) and body.lstrip().startswith("@"):
                raise ValueError("body no puede empezar con '@' (curl lo leeria como archivo)")
            try:
                json.dumps(body)
            except (TypeError, ValueError):
                raise ValueError("body debe ser JSON")
            out["body"] = body
        hd = a.get("headers") or {}
        if not isinstance(hd, dict):
            raise ValueError("headers debe ser objeto")
        out["headers"] = {}
        for k, v in hd.items():
            if not isinstance(k, str) or not _HDR_NAME.match(k):
                raise ValueError(f"header invalido: {k!r}")
            if _HDR_SECRETO.search(k):
                raise ValueError(f"header {k!r} parece un secreto: use token_env (variable de entorno)")
            out["headers"][k] = _txt(str(v), f"header {k}", 1000)
        if a.get("token_env"):
            if not isinstance(a["token_env"], str) or not _ENV_NAME.match(a["token_env"]):
                raise ValueError("token_env debe ser el NOMBRE de una variable de entorno")
            out["token_env"] = a["token_env"]
        out["timeout_s"] = _entero(a.get("timeout_s"), "timeout_s", 1, 3600, 30)
    elif t == "glue_job":
        n = _txt(a.get("job_name"), "job_name", 255)
        if not re.fullmatch(r"[\w.\-]{1,255}", n):
            raise ValueError("job_name invalido")
        out["job_name"] = n
        ar = a.get("args") or {}
        if not isinstance(ar, dict):
            raise ValueError("args de glue debe ser objeto {\"--clave\": \"valor\"}")
        out["args"] = {}
        for k, v in ar.items():
            if not isinstance(k, str) or not re.fullmatch(r"--[\w.\-]{1,100}", k):
                raise ValueError(f"argumento de glue invalido: {k!r} (debe empezar con --)")
            out["args"][k] = _txt(str(v), f"args[{k}]", 2000)
    elif t == "emr_step":
        c = a.get("cluster_id")
        if not isinstance(c, str) or not re.fullmatch(r"j-[A-Z0-9]{1,30}", c):
            raise ValueError("cluster_id invalido (ej. j-ABC123XYZ)")
        out["cluster_id"] = c
        sc = _txt(a.get("script"), "script", 1000)
        if not _S3_URL.match(sc):
            raise ValueError("script debe ser s3://bucket/clave")
        out["script"] = sc
        out["args"] = _lista_txt(a.get("args"), "args")
        nm = a.get("nombre") or "bnx-step"
        if not isinstance(nm, str) or not re.fullmatch(r"[\w .\-]{1,256}", nm):
            raise ValueError("nombre invalido")
        out["nombre"] = nm
        af = a.get("action_on_failure") or "CONTINUE"
        if af not in ("CONTINUE", "CANCEL_AND_WAIT", "TERMINATE_CLUSTER"):
            raise ValueError("action_on_failure debe ser CONTINUE, CANCEL_AND_WAIT o TERMINATE_CLUSTER")
        out["action_on_failure"] = af
    elif t == "lambda":
        fn = a.get("function_name")
        if not isinstance(fn, str) or not re.fullmatch(r"[A-Za-z0-9][\w:.\-]{0,139}", fn):
            raise ValueError("function_name invalido (nombre o ARN)")
        out["function_name"] = fn
        pl = a.get("payload")
        if pl not in (None, ""):
            try:
                json.dumps(pl)
            except (TypeError, ValueError):
                raise ValueError("payload debe ser JSON")
            out["payload"] = pl
    elif t == "s3_copy":
        o_, d_ = _ruta_txt(a.get("origen"), "origen"), _ruta_txt(a.get("destino"), "destino")
        for nom, v in (("origen", o_), ("destino", d_)):
            if "://" in v and not _S3_URL.match(v):
                raise ValueError(f"{nom}: use una ruta local o s3://bucket/clave")
        if not (o_.startswith("s3://") or d_.startswith("s3://")):
            raise ValueError("s3_copy necesita que origen o destino sea s3://")
        out["origen"], out["destino"] = o_, d_
        if a.get("recursivo") is not None and not isinstance(a["recursivo"], bool):
            raise ValueError("recursivo debe ser booleano")
        out["recursivo"] = bool(a.get("recursivo"))
    if t in ("esperar_archivo", "glue_job", "emr_step", "lambda", "s3_copy"):
        _perfil_region(a, out)
    out["ubicacion"] = ubicacion_de(out)
    return out


def resumen_accion(a):
    """Texto corto de lo que hace un paso (para mostrar/GUI)."""
    t = a.get("type")
    if t in ("python", "spark_submit"):
        return a.get("target", "")
    if t in ("shell", "ssh"):
        pre = f"{a.get('usuario') + '@' if a.get('usuario') else ''}{a['host']}: " if t == "ssh" else ""
        return pre + a.get("comando", "")
    if t == "http":
        return f"{a.get('metodo', 'GET')} {a.get('url', '')}"
    if t == "esperar_archivo":
        return a.get("ruta", "")
    if t == "glue_job":
        return a.get("job_name", "")
    if t == "emr_step":
        return f"{a.get('cluster_id', '')} {a.get('script', '')}"
    if t == "lambda":
        return a.get("function_name", "")
    if t == "s3_copy":
        return f"{a.get('origen', '')} -> {a.get('destino', '')}"
    return ""


def _aws_argv(a, ej, *resto):
    aws = ej.get("aws") or {}
    pre = ["aws"]
    prof, reg = a.get("profile") or aws.get("profile"), a.get("region") or aws.get("region")
    if prof:
        pre += ["--profile", prof]
    if reg:
        pre += ["--region", reg]
    return pre + list(resto)


def _cmd_nuevo(a, ej, portable):
    """argv del paso. portable=True: nombres de binario (python3/spark-submit) para Airflow."""
    t = a["type"]
    py = "python3" if portable else sys.executable
    if t == "python":
        return [py, a["target"], *a.get("args", [])]
    if t == "spark_submit":
        sb = os.path.basename(ej.get("spark_submit") or "spark-submit") if portable else _spark_submit_bin(ej)
        m = ["--master", a["master"]] if a.get("master") else []
        return [sb, *m, *a.get("spark_args", []), a["target"], *a.get("args", [])]
    if t == "shell":
        argv = shlex.split(a["comando"])
        ext = os.path.splitext(argv[0])[1].lower()
        if ext == ".ksh":
            return ["ksh", *argv]
        if ext == ".sh":
            return ["bash", *argv]
        return argv
    if t == "esperar_archivo":
        c = [py, "-m", "src.orquestador", "esperar", a["ruta"], "--timeout", str(a.get("timeout_s", 300)),
             "--intervalo", str(a.get("intervalo_s", 10))]
        aws = ej.get("aws") or {}
        for k in ("profile", "region"):
            v = a.get(k) or aws.get(k)
            if v and a["ruta"].startswith("s3://"):
                c += [f"--{k}", v]
        return c
    if t == "ssh":
        dest = f"{a['usuario']}@{a['host']}" if a.get("usuario") else a["host"]
        c = ["ssh", "-o", "BatchMode=yes", "-o", "ConnectTimeout=15"]
        if a.get("puerto"):
            c += ["-p", str(a["puerto"])]
        if a.get("identidad"):
            c += ["-i", a["identidad"]]
        return c + [dest, a["comando"]]
    if t == "http":
        c = ["curl", "-sS", "--fail", "--max-time", str(a.get("timeout_s", 30)), "-X", a.get("metodo", "GET")]
        hd = dict(a.get("headers") or {})
        body = a.get("body")
        if body not in (None, ""):
            body = body if isinstance(body, str) else json.dumps(body, ensure_ascii=False)
            if not any(k.lower() == "content-type" for k in hd):
                hd["Content-Type"] = "application/json"
        for k, v in hd.items():
            c += ["-H", f"{k}: {v}"]
        if a.get("token_env"):
            c += ["-H", "@-"]            # el header Authorization llega por stdin, no en argv
        if body not in (None, ""):
            c += ["--data-binary", body]
        return c + [a["url"]]
    if t == "glue_job":
        c = _aws_argv(a, ej, "glue", "start-job-run", "--job-name", a["job_name"])
        return c + (["--arguments", json.dumps(a["args"], ensure_ascii=False)] if a.get("args") else [])
    if t == "emr_step":
        paso = {"Type": "Spark", "Name": a.get("nombre", "bnx-step"),
                "ActionOnFailure": a.get("action_on_failure", "CONTINUE"),
                "Args": ["--deploy-mode", "cluster", a["script"], *a.get("args", [])]}
        return _aws_argv(a, ej, "emr", "add-steps", "--cluster-id", a["cluster_id"],
                         "--steps", json.dumps([paso], ensure_ascii=False))
    if t == "lambda":
        return _aws_argv(a, ej, "lambda", "invoke", "--function-name", a["function_name"],
                         "--cli-binary-format", "raw-in-base64-out",
                         "--payload", json.dumps(a.get("payload") if a.get("payload") not in (None, "") else {},
                                                 ensure_ascii=False), os.devnull)
    if t == "s3_copy":
        return _aws_argv(a, ej, "s3", "cp", *(["--recursive"] if a.get("recursivo") else []),
                         a["origen"], a["destino"])
    raise ValueError(f"tipo de paso no soportado: {t!r}")


def stdin_de(step):
    """Texto que el paso necesita por stdin (hoy: header Authorization de http con token_env),
    leido de la variable de entorno al ejecutar. None si no aplica."""
    a = step["action"]
    if a.get("type") == "http" and a.get("token_env"):
        v = os.environ.get(a["token_env"])
        if not v:
            raise ValueError(f"falta la variable de entorno {a['token_env']} (token del paso)")
        if _CTRL.search(v):
            raise ValueError(f"{a['token_env']} tiene caracteres de control")
        return f"Authorization: Bearer {v}\n"
    return None


def comando_airflow(step, ej, root):
    """Linea de bash equivalente para un BashOperator de Airflow (tipos nuevos)."""
    a = step["action"]
    c = shlex.join(_cmd_nuevo(a, ej, portable=True))
    if a["type"] == "http" and a.get("token_env"):
        c = f"printf 'Authorization: Bearer %s\\n' \"${{{a['token_env']}:?defina {a['token_env']}}}\" | " + c
    if a["type"] == "esperar_archivo":
        c = f"cd {shlex.quote(root)} && " + c
    # Airflow trata un bash_command que termina en .sh/.bash como plantilla de archivo
    return c + " " if c.endswith((".sh", ".bash", ".ksh")) else c


def esperar_archivo(ruta, timeout=300, intervalo=10, profile=None, region=None,
                    sleep=None, run=None):
    """Sensor: espera a que exista la ruta local (admite comodines) o el objeto/prefijo s3://.
    True si aparece antes de `timeout` segundos."""
    import glob as _glob
    import time as _time
    sleep = sleep or _time.sleep
    run = run or subprocess.run
    limite = _time.monotonic() + timeout

    def existe():
        if not ruta.startswith("s3://"):
            return bool(_glob.glob(ruta))
        pre = ["aws"] + (["--profile", profile] if profile else []) + (["--region", region] if region else [])
        bucket, _, key = ruta[5:].partition("/")
        if key and not key.endswith("/"):
            r = run(pre + ["s3api", "head-object", "--bucket", bucket, "--key", key],
                    capture_output=True, text=True)
            return r.returncode == 0
        r = run(pre + ["s3", "ls", ruta], capture_output=True, text=True)
        return r.returncode == 0 and bool((r.stdout or "").strip())

    while True:
        if existe():
            print(f"[ok] existe: {ruta}")
            return True
        if _time.monotonic() >= limite:
            print(f"[x] tiempo agotado esperando {ruta} ({timeout}s)")
            return False
        sleep(intervalo)


def _siguiente_id(o):
    return "t" + str(max([_num(s["id"]) for s in o["steps"]] + [0]) + 1)


def agregar_paso(o, tipo, nombre, depends_on=None, **campos):
    """Agrega un paso a una orquestacion (valida accion, dependencias y ciclos antes de devolver).
    Los campos son los del tipo (ver TIPOS_NUEVOS; "graph" usa target=<*_spark.py>)."""
    nombre = _txt(nombre, "nombre", 120)
    accion = normalizar_accion({"type": tipo, **campos})
    paso = {"id": _siguiente_id(o), "name": nombre, "action": accion,
            "depends_on": sorted(depends_on or [], key=_num), "dep_flags": {},
            "solo_en_fallo": False, "enabled": True, "continue_on_error": False}
    o["steps"].append(paso)
    try:
        validar_plan(o)
    except ValueError:
        o["steps"].pop()
        raise
    return paso


def quitar_paso(o, ref):
    s = _find(o, ref)
    o["steps"] = [x for x in o["steps"] if x["id"] != s["id"]]
    for x in o["steps"]:
        x["depends_on"] = [d for d in x["depends_on"] if d != s["id"]]
        x["dep_flags"] = {k: v for k, v in (x.get("dep_flags") or {}).items() if k != s["id"]}
    o["enlaces"] = [e for e in (o.get("enlaces") or []) if s["id"] not in (e["desde"], e["hacia"])]
    return s


def _pasos_manuales(almacenado, inc):
    """Pasos entrantes de una orquestacion manual -> lista normalizada (lista blanca de campos)."""
    if not isinstance(inc, list) or not all(isinstance(s, dict) for s in inc) or len(inc) > 300:
        raise ValueError("pasos invalidos")
    previos = {s["id"]: s for s in almacenado.get("steps", [])}
    out = []
    for s in inc:
        sid = s.get("id")
        if not isinstance(sid, str) or not re.fullmatch(r"[A-Za-z][A-Za-z0-9_]{0,30}", sid):
            raise ValueError("id de paso invalido")
        deps = s.get("depends_on", [])
        if not isinstance(deps, list) or not all(isinstance(d, str) for d in deps):
            raise ValueError(f"dependencias invalidas en {sid}")
        paso = {"id": sid, "name": _txt(s.get("name"), f"{sid}.name", 120),
                "action": normalizar_accion(s.get("action"), estricto=True),
                "depends_on": sorted(set(deps), key=_num),
                "dep_flags": {k: v for k, v in (previos.get(sid, {}).get("dep_flags") or {}).items()
                              if k in deps},
                "solo_en_fallo": False, "enabled": True, "continue_on_error": False}
        for k in ("enabled", "solo_en_fallo", "continue_on_error"):
            if k in s:
                if not isinstance(s[k], bool):
                    raise ValueError(f"{sid}.{k} debe ser booleano")
                paso[k] = s[k]
        out.append(paso)
    return out


def nueva(nombre, proyecto, base=None):
    """Crea una orquestacion VACIA desde cero (sin .plan), con el mismo esquema que las
    generadas desde planes, marcada origen="manual". Se guarda en
    <base>/<proyecto>/orquestacion_<nombre>.json (base por defecto: output/ del proyecto)
    y devuelve la ruta. No pisa una existente (ValueError)."""
    if not re.fullmatch(r"[A-Za-z0-9][\w.\-]{0,80}", nombre or ""):
        raise ValueError("nombre invalido (letras, numeros, . _ -)")
    if not re.fullmatch(r"[A-Za-z0-9][\w.\-]{0,63}", proyecto or ""):
        raise ValueError("proyecto invalido (letras, numeros, . _ -)")
    base = base or os.path.join(_ROOT, "output")
    destino = os.path.join(base, proyecto, f"orquestacion_{nombre}.json")
    if os.path.exists(destino):
        raise ValueError(f"ya existe {os.path.relpath(destino, _ROOT) if destino.startswith(_ROOT) else destino}")
    o = {"plan": nombre + ".manual", "nombre": nombre, "origen": "manual", "proyecto": proyecto,
         "direccion": "prior", "ejecucion": json.loads(json.dumps(EJECUCION_DEFECTO)),
         "steps": [], "enlaces": []}
    validar_plan(o)
    os.makedirs(os.path.dirname(destino), exist_ok=True)
    _write(destino, o)
    return destino


def build_command(step, ej, portable=False):
    a = step["action"]
    if a["type"] in TIPOS_NUEVOS:
        return _cmd_nuevo(a, ej, portable)
    if a["type"] == "graph":
        if ej.get("modo") == "spark-submit":
            return [_spark_submit_bin(ej), *ej.get("spark_args", []), a["target"]]
        return [sys.executable, a["target"]]
    return ["ksh", a["target"]]


def _job_env(ej):
    env = dict(os.environ)
    env.update({str(k): str(v) for k, v in (ej.get("env") or {}).items()})
    if ej.get("base_path"):
        env["BNX_BASE_PATH"] = _base_efectiva(ej)
    # Los jobs (y los workers de Spark) deben usar el MISMO Python que el orquestador
    # (en Windows, el python de Anaconda; si no, Spark busca "python3" y no lo encuentra)
    if os.name == "nt":
        env["PYSPARK_PYTHON"] = env["PYSPARK_DRIVER_PYTHON"] = sys.executable
    else:
        env.setdefault("PYSPARK_PYTHON", sys.executable)
        env.setdefault("PYSPARK_DRIVER_PYTHON", sys.executable)
    env.setdefault("PYTHONIOENCODING", "utf-8")   # consola cp1252: print('→') no debe reventar
    env.setdefault("PYTHONUTF8", "1")
    return env


def _base_efectiva(ej):
    return normalizar_base_path(ej.get("base_path") or "")


def _resolver_script(cmd):
    """['ksh', x.ksh] -> argv ejecutable en este equipo: ksh, o bash (Git Bash/WSL).
    None si no hay ninguno (p.ej. Windows sin Git Bash): el paso se omite en la ejecucion real."""
    if cmd and cmd[0] == "ksh":
        for sh in ("ksh", "bash"):
            if shutil.which(sh):
                return [sh, *cmd[1:]]
        return None
    if cmd and cmd[0] == "bash" and not shutil.which("bash"):
        return None
    return cmd


def materializar_enlace(link, ej, real, tolerante=False):
    """Copia <base>/<salida> a <base>/<entrada>. Devuelve True si ok (o dry-run).
    tolerante=True (origen fuera de la seleccion --paso/--desde): si la salida no existe
    se avisa y se sigue (la entrada puede venir de una corrida anterior o de datos sinteticos)."""
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
        if tolerante:
            print(f"[!] la salida {src} no existe (el paso origen no corre ahora); "
                  f"se usa {dst} tal como esta" + ("" if os.path.isdir(dst) else " (¡tampoco existe!)"))
            return True
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
        if a["type"] in TIPOS_NUEVOS:
            tgt = resumen_accion(a)
            print(f"{i:2}. {sid:<5} {s['name']:<32} <- {deps:<12} [{ubicacion_de(a)}] {a['type']}: {tgt}{flag}")
        else:
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

def _evento(ruta, estado):
    """Linea maquina-legible para la GUI (solo si BNX_EVENTOS=1): estado de cada paso."""
    if os.environ.get("BNX_EVENTOS") == "1":
        print("##BNX " + json.dumps({"ruta": ruta, "estado": estado}), flush=True)


def seleccion_pasos(o, solo=None, desde=None):
    """Conjunto de ids a correr: {solo}, {desde y todo lo que depende de el} o None (todos)."""
    ids = {s["id"] for s in o["steps"]}
    for x in (solo, desde):
        if x is not None and x not in ids:
            raise ValueError(f"paso inexistente: {x!r}")
    if solo is not None:
        return {solo}
    if desde is not None:
        sel, cambio = {desde}, True
        while cambio:
            cambio = False
            for s in o["steps"]:
                if s["id"] not in sel and any(d in sel for d in s["depends_on"]):
                    sel.add(s["id"])
                    cambio = True
        return sel
    return None


def _io_subplan(a):
    """({nombres que lee (raw/X -> X)}, {nombres que escribe}) de un paso `plan`, recursivo."""
    try:
        with open(_ruta_plan(a["target"]), "r", encoding="utf-8") as f:
            jobs = _jobs_del_plan(json.load(f), None, 1, _pila=(os.path.realpath(_ruta_plan(a["target"])),))
    except (OSError, ValueError, KeyError):
        return set(), set()
    lee = {_nombre_dataset(r) for j in jobs for _v, r, ok in j["lee"] if ok}
    esc = {_nombre_dataset(w) for j in jobs for w in j["escribe"]}
    return lee, esc


def _enlaces_implicitos(o, s, by_id, done, failed, enlaces, seleccion):
    """Enlaces output/X -> raw/X entre sub-planes del mismo plan cuando X lo escribe un sub-plan
    anterior y lo lee `s`, y ningun enlace explicito ya entrega esa entrada."""
    lee, _ = _io_subplan(s["action"])
    if not lee:
        return []
    anc = _ancestros(o["steps"]).get(s["id"], set())
    cubiertas = {e["entrada"] for e in enlaces if e["hacia"] == s["id"]}
    prod = {}
    for d in sorted(anc, key=_num):
        sd = by_id[d]
        if not sd["enabled"] or sd["action"]["type"] != "plan" or d not in done or d in failed:
            continue
        if seleccion is not None and d not in seleccion:
            continue
        for nombre in _io_subplan(sd["action"])[1]:
            prod[nombre] = d
    out = []
    for nombre in sorted(prod):
        if nombre in lee and "raw/" + nombre not in cubiertas:
            out.append({"id": f"i{len(out) + 1}", "desde": prod[nombre], "salida": "output/" + nombre,
                        "hacia": s["id"], "entrada": "raw/" + nombre, "origen": "implicito",
                        "habilitado": True})
    return out


def ejecutar(o, real=False, modo=None, base_path=None, _nivel=0, _pila=(),
             solo=None, desde=None, permitir_remotos=True, spark_args=None, _prefijo=""):
    """solo / desde: ejecutar un unico paso, o ese paso y sus descendientes (el resto se da por
    hecho). permitir_remotos=False: los pasos remotos/nube se OMITEN en la ejecucion real."""
    validar_plan(o)
    ej = _ej(o, modo, base_path, spark_args)
    order = topo_order(o["steps"])
    by_id = {s["id"]: s for s in o["steps"]}
    enlaces = [e for e in (o.get("enlaces") or []) if e.get("habilitado", True)]
    done, failed, faltantes, omitidos = set(), set(), [], []
    try:
        seleccion = seleccion_pasos(o, solo, desde)
    except ValueError as e:
        print(f"[x] {e}")
        return False
    es_planes = o.get("tipo") == "plan_de_planes"
    sangria = ""   # el sangrado de los sub-planes lo hace quien los llama
    print(f"{sangria}[*] {'Plan de planes' if es_planes else 'Plan'} {o['plan']}"
          + (f" (pset {o['pset']})" if o.get("pset") else "")
          + f" - {'EJECUCION REAL' if real else 'DRY-RUN'} - modo {ej['modo']}")
    # En un plan de planes cada sub-plan valida su propio base_path (si no se comparte uno)
    usa_jobs = o.get("origen") != "manual" or any(
        s["enabled"] and s["action"]["type"] == "graph" for s in o["steps"])
    if real and not es_planes and usa_jobs and not _base_efectiva(ej):
        print("[x] La ejecucion real exige base_path (ejecucion.base_path o --base-path): "
              "sin el, los jobs usarian el bucket S3 por defecto.")
        return False
    for sid in order:
        s = by_id[sid]
        a = s["action"]
        ruta_ev = _prefijo + sid
        if seleccion is not None and sid not in seleccion:
            print(f"[-] {sid} {s['name']}: fuera de la seleccion (no se ejecuta)")
            done.add(sid)  # se da por hecho para los dependientes
            continue
        if not s["enabled"]:
            print(f"[-] {sid} {s['name']}: deshabilitado")
            _evento(ruta_ev, "omitido")
            done.add(sid)  # no bloquea a los dependientes
            continue
        fallo_previo = [d for d in s["depends_on"] if d in failed]
        if s.get("solo_en_fallo"):
            if not fallo_previo:
                print(f"[-] {sid} {s['name']}: omitido (solo corre si algo falla)")
                _evento(ruta_ev, "omitido")
                done.add(sid)
                continue
        elif fallo_previo:
            print(f"[x] {sid} {s['name']}: omitido, fallo previo {fallo_previo}")
            _evento(ruta_ev, "omitido")
            failed.add(sid)
            continue
        if a["type"] == "noop" or (not a.get("target") and a["type"] not in TIPOS_NUEVOS):
            motivo = a.get("nota") or a["status"]
            print(f"[~] {sid} {s['name']}: sin accion ({motivo})")
            if a["status"] in ("faltante", "sin_convertir"):
                faltantes.append(f"{sid} {s['name']} -> {a.get('source')}")
                if real and not s["continue_on_error"]:
                    _evento(ruta_ev, "fallo")
                    failed.add(sid)
                    continue
            _evento(ruta_ev, "omitido")
            done.add(sid)
            continue
        # Pasos remotos / nube: solo con permiso explicito (si no, se omiten)
        if real and not permitir_remotos and (
                a["type"] in TIPOS_NUEVOS and ubicacion_de(a) != "local"):
            print(f"[-] {sid} {s['name']}: omitido ({ubicacion_de(a)}/{a['type']} sin permiso: "
                  f"marque 'permitir pasos remotos/nube' o quite --sin-remotos)")
            omitidos.append(f"{sid} {s['name']} ({ubicacion_de(a)})")
            _evento(ruta_ev, "omitido")
            done.add(sid)
            continue
        # Enlaces hacia este paso: se materializan antes de ejecutarlo
        enlace_ok = True
        for e in enlaces:
            if e["hacia"] == sid and e["desde"] in done and e["desde"] not in failed:
                fuera = seleccion is not None and e["desde"] not in seleccion
                enlace_ok = materializar_enlace(e, ej, real, tolerante=fuera) and enlace_ok
        if a["type"] == "plan":
            # Plan de planes: lo que un sub-plan anterior escribe (output/X) y este lee (raw/X) sin
            # enlace explicito se enlaza por coincidencia de nombre (sobrescribe el raw intermedio).
            for e in _enlaces_implicitos(o, s, by_id, done, failed, enlaces, seleccion):
                fuera = seleccion is not None and e["desde"] not in seleccion
                enlace_ok = materializar_enlace(e, ej, real, tolerante=fuera) and enlace_ok
        if not enlace_ok and not s["continue_on_error"]:
            print(f"[x] {sid} {s['name']}: fallo el enlace de entrada, no se ejecuta")
            _evento(ruta_ev, "fallo")
            failed.add(sid)
            continue
        if a["type"] == "plan":
            # Paso = otra orquestacion completa. Se ejecuta en este mismo proceso (el
            # dry-run se ve anidado). base_path y --modo del plan de planes, si se dan,
            # se comparten con todos los sub-planes; si no, cada uno usa el suyo.
            fp = _ruta_plan(a["target"])
            print(f"{sangria}[>] {sid} {s['name']}: plan {a['target']}")
            if os.path.realpath(fp) in _pila or _nivel >= 3:
                print(f"{sangria}[x] {sid}: plan anidado en ciclo o demasiado profundo")
                _evento(ruta_ev, "fallo")
                failed.add(sid)
                continue
            _evento(ruta_ev, "corriendo")
            try:
                with open(fp, "r", encoding="utf-8") as f:
                    sub = json.load(f)
                kw = dict(real=real, modo=modo, base_path=(_base_efectiva(ej) or None),
                          _nivel=_nivel + 1, _pila=_pila + (os.path.realpath(fp),),
                          permitir_remotos=permitir_remotos, spark_args=spark_args,
                          _prefijo=ruta_ev + "/")
                if real:
                    ok_sub = ejecutar(sub, **kw)          # logs en vivo
                else:
                    # dry-run: todo el detalle del sub-plan sangrado bajo su paso
                    import io as _io
                    import contextlib as _ctx
                    buf = _io.StringIO()
                    with _ctx.redirect_stdout(buf):
                        ok_sub = ejecutar(sub, **kw)
                    for ln in buf.getvalue().splitlines():
                        print("    " + ln)
            except (OSError, ValueError, KeyError) as e:
                print(f"{sangria}[x] {sid}: no se pudo leer/validar el plan: {e}")
                ok_sub = False
            if ok_sub:
                _evento(ruta_ev, "ok")
                done.add(sid)
            elif not real:
                # dry-run: avisar y seguir, para ver tambien el detalle de los siguientes
                print(f"{sangria}[!] {sid} {s['name']}: este plan tiene faltantes (ver arriba)")
                faltantes.append(f"{sid} {s['name']} -> plan con faltantes")
                done.add(sid)
            else:
                print(f"{sangria}[x] {sid} {s['name']}: el plan termino con fallos o faltantes")
                _evento(ruta_ev, "fallo")
                if not s["continue_on_error"]:
                    failed.add(sid)
                else:
                    done.add(sid)
            continue
        if a["type"] in TIPOS_NUEVOS:
            # local / remoto / nube: argv exacto; dry-run solo lo muestra
            try:
                cmd = build_command(s, ej)
                entrada = stdin_de(s) if real else None
            except ValueError as e:
                print(f"[x] {sid} {s['name']}: {e}")
                _evento(ruta_ev, "fallo")
                failed.add(sid)
                continue
            if real:
                cmd = _resolver_script(cmd)
                if cmd is None:
                    print(f"[-] {sid} {s['name']}: omitido (no hay ksh ni bash en este equipo; "
                          f"instale Git Bash/WSL para correr scripts .ksh/.sh)")
                    omitidos.append(f"{sid} {s['name']} (sin ksh/bash)")
                    _evento(ruta_ev, "omitido")
                    done.add(sid)
                    continue
            print(f"[>] {sid} {s['name']} [{ubicacion_de(a)}/{a['type']}]: {shlex.join(cmd)}")
            if a["type"] == "http" and a.get("token_env"):
                print(f"    (header Authorization desde ${a['token_env']}, por stdin)")
            if not real:
                done.add(sid)
                continue
            _evento(ruta_ev, "corriendo")
            try:
                rc = subprocess.run(cmd, env=_job_env(ej), input=entrada, text=entrada is not None,
                                    cwd=_ROOT if a["type"] == "esperar_archivo" else None).returncode
            except OSError as e:
                print(f"[x] {sid}: no se pudo lanzar {cmd[0]}: {e}")
                rc = 127
            if rc == 0:
                _evento(ruta_ev, "ok")
                done.add(sid)
            else:
                print(f"[x] {sid} termino con codigo {rc}")
                _evento(ruta_ev, "fallo")
                if not s["continue_on_error"]:
                    failed.add(sid)
            continue
        cmd = build_command(s, ej)
        print(f"[>] {sid} {s['name']}: {' '.join(cmd)}")
        if a["status"] in ("faltante", "sin_convertir"):
            faltantes.append(f"{sid} {s['name']} -> {a.get('source')}")
            if real and not s["continue_on_error"]:
                print(f"[x] {sid}: archivo faltante, no se ejecuta")
                _evento(ruta_ev, "fallo")
                failed.add(sid)
                continue
        if not real:
            done.add(sid)
            continue
        if a["type"] != "graph":      # script .ksh de Ab Initio: ksh, o bash (Git Bash/WSL)
            cmd = _resolver_script(cmd)
            if cmd is None:
                print(f"[-] {sid} {s['name']}: omitido (no hay ksh ni bash en este equipo; "
                      f"instale Git Bash/WSL para correr scripts .ksh)")
                omitidos.append(f"{sid} {s['name']} (sin ksh/bash)")
                _evento(ruta_ev, "omitido")
                done.add(sid)
                continue
        _evento(ruta_ev, "corriendo")
        try:
            rc = subprocess.run(cmd, env=_job_env(ej)).returncode
        except OSError as e:
            print(f"[x] {sid}: no se pudo lanzar {cmd[0]}: {e}")
            rc = 127
        if rc == 0:
            _evento(ruta_ev, "ok")
            done.add(sid)
        else:
            print(f"[x] {sid} termino con codigo {rc}")
            _evento(ruta_ev, "fallo")
            if not s["continue_on_error"]:
                failed.add(sid)
    if faltantes:
        print("[!] Archivos faltantes (no se pueden ejecutar):")
        for f in faltantes:
            print("    -", f)
    if omitidos:
        print("[!] Pasos omitidos en la ejecucion real:")
        for f in omitidos:
            print("    -", f)
    print(f"[ok] completados={len(done)} fallidos/omitidos={len(failed)} faltantes={len(faltantes)}")
    return not failed and not faltantes


# ---------------------------------------------------------------------------
# Datos sinteticos de entrada para los jobs del plan
# ---------------------------------------------------------------------------

_READ_VAR = re.compile(
    r'^\s*(\w+?)(?:_df)?\s*=\s*spark\.read\.parquet\(f"\{PARAMS\.BASE_PATH\}/raw/([^"]*)"\)', re.M)


_RAW_NAME = re.compile(r"\{_bnx_raw_name\('((?:[^'\\]|\\.)*)',\s*'([^']*)'\)\}")


def _resolver_nombre(nombre, defaults):
    """Resuelve el nombre de un dataset de entrada: {_bnx_raw_name('<ruta>', '<nodo>')} con el
    MISMO algoritmo del job (params_runtime) y {PARAMS.X} por su default literal.
    Devuelve (nombre, resuelto)."""
    from src.codegen.params_runtime import resolve_raw_name
    nombre = _RAW_NAME.sub(lambda mm: resolve_raw_name(mm.group(1), mm.group(2), defaults)[0], nombre)
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
    r"partitionBy|withColumnRenamed)\(|(?:F\.)?(?:col|expr)\(|_bnx_safe_col\(")


# Helpers del job que reciben (df, "columna", ...): la columna es de la entrada. Los demas
# helpers `_bnx_*`/split reciben nombres de columnas CREADAS o expresiones, no se consideran.
_HELPER_COL = re.compile(r'(?<![\w.])([A-Za-z_]\w*)\(\s*(\w+_df)\s*,\s*"([A-Za-z_]\w*)"')
_HELPER_SKIP = {"output_indexes_split", "is_valid_record", "col", "lit", "expr", "F", "withColumn"}
_HDR_TRL = re.compile(
    r'filter_by_expression_hdr_trl\(\s*(\w+_df)\s*,\s*"(\w+)"\s*,\s*(\d+)\s*,\s*(\d+)\s*,\s*\[([^\]]*)\]')
_DF_INDEX = re.compile(r'(\w+_df)\s*\[\s*"([A-Za-z_]\w*)"\s*\]')


_WHERE_LIT = re.compile(r'\.(?:where|filter)\(\s*"((?:[^"\\]|\\.)*)"')
_ATOMO = re.compile(r"^\(*\s*([A-Za-z_]\w*)\s*(==|=|!=|<>|>=|<=|>|<)\s*('(?:[^']*)'|-?\d+(?:\.\d+)?)\s*\)*$")
_ATOMO_IN = re.compile(r"^\(*\s*([A-Za-z_]\w*)\s+IN\s*\(([^)]*)\)\s*\)*$", re.I)


def _condiciones_and(expr):
    """[(columna, op, literal)] de una expresion SQL de filtro formada solo por condiciones
    unidas con AND (sin OR ni NOT: no se pueden satisfacer de forma independiente).
    literal: str para 'texto', int/float para numeros, lista para IN (...)."""
    if re.match(r"\s*NOT\b", expr, re.I) or re.search(r"\bOR\b|\|\|", expr, re.I):
        return []
    out = []
    for atomo in re.split(r"\s+AND\s+|\s*&&\s*", expr, flags=re.I):
        atomo = atomo.strip()
        m = _ATOMO.match(atomo)
        if m:
            lit = m.group(3)
            if lit.startswith("'"):
                lit = lit[1:-1]
            else:
                lit = float(lit) if "." in lit else int(lit)
            out.append((m.group(1), {"=": "==", "<>": "!="}.get(m.group(2), m.group(2)), lit))
            continue
        m = _ATOMO_IN.match(atomo)
        if m:
            vals = [v.strip() for v in m.group(2).split(",") if v.strip()]
            vals = [v[1:-1] if v.startswith("'") else (float(v) if "." in v else int(v))
                    for v in vals if re.fullmatch(r"'[^']*'|-?\d+(?:\.\d+)?", v)]
            if vals:
                out.append((m.group(1), "in", vals))
    return out


def _alias_creados(code):
    """Nombres de .alias("x") que CREAN una columna/alias de DataFrame. Un
    expr("`s0`.`x`").alias("x") solo la renombra a si misma: x es columna de entrada."""
    propios = {m.group(2) for m in re.finditer(
        r'expr\(\s*"((?:[^"\\]|\\.)*)"\s*\)\.alias\(\s*"(\w+)"\s*\)', code)
        if re.search(rf"\b{re.escape(m.group(2))}\b", m.group(1))}
    return set(re.findall(r'\.alias\(\s*"(\w+)"\s*\)', code)) - propios


def _columnas_por_fuente(code, fuentes, marcas=None, filtros=None):
    """{fuente_lower: {columna: tipo}} siguiendo el linaje de DataFrames del job.

    Cada asignacion `A_df = B_df.op(...)` atribuye las columnas citadas en sus literales
    de expresion a las fuentes raiz de B (el PRIMER DataFrame del lado derecho). En los
    joins, las claves `on=[...]` van a las raices de todos los lados. Se excluyen las
    columnas que el propio job crea (withColumn / alias / AS). Tipo: numerico si la
    columna se castea a numero o se compara con un literal numerico; fecha si va en
    to_date; si no, string. Es una heuristica sobre el codigo generado por BNX.
    Tambien cuenta: helpers tipo filter_by_expression_hdr_trl(df, "Campo", ...), df["X"],
    on="X". `marcas` (dict opcional) recibe {fuente: {columna: (inicio, largo, [valores])}}
    para los filtros HDR/TRL (el generador de datos incluye esas filas). `filtros` (dict
    opcional) recibe {fuente: {columna: [(op, literal)]}} con las condiciones AND de los
    .where/.filter con literal (==, !=, IN, <, >...) para generar filas que las cumplan.
    """
    raices = {f.lower() + "_df": {f.lower()} for f in fuentes}
    creadas = set(re.findall(r'withColumn\(\s*"(\w+)"', code))
    creadas |= _alias_creados(code)
    for sm in re.finditer(r'_bnx_safe_col\(\s*\w+\s*,\s*"(\w+)"\s*,\s*"((?:[^"\\]|\\.)*)"', code):
        # una columna que se reescribe a partir de si misma (trim(x)) es ENTRADA, no creada
        if not re.search(rf"\b{re.escape(sm.group(1))}\b", sm.group(2)):
            creadas.add(sm.group(1))
    creadas |= set(re.findall(r'_bnx_safe_col\(\s*\w+\s*,\s*"(\w+)"\s*\)', code))
    # prefijos de tabla/alias de join dentro de expresiones: `s0`.`col`, s1.col
    for lit in _STR_LIT.findall(code):
        creadas |= set(re.findall(r"`?\b([A-Za-z_]\w*)`?\s*\.\s*`?[A-Za-z_]", lit))
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
        # aritmetica (c * 100, a / c) y agregaciones numericas (sum/avg de la columna)
        if re.search(rf"\b{e}\b\s*[*/+-]\s*[\w(]", txt) or re.search(rf"[\w)]\s*[*/+-]\s*\(?\b{e}\b", txt) \
                or re.search(rf"\b(?:sum|avg|mean)\(\s*(?:_bnx_aggcol\(\s*\w+\s*,\s*)?[\"']?{e}\b", txt, re.I):
            return "int"
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
        on1 = re.search(r'\bon\s*=\s*"([A-Za-z_]\w*)"', rhs)
        if on1:
            agregar(todos, [on1.group(1)], rhs)
        for hm in _HELPER_COL.finditer(rhs):
            if hm.group(1) not in _HELPER_SKIP and (
                    not hm.group(1).startswith("_bnx_") or hm.group(1) in ("_bnx_aggcol", "_bnx_safe_col")):
                agregar(raices.get(hm.group(2).lower(), set()), [hm.group(3)], rhs)
        for dm in _DF_INDEX.finditer(rhs):
            agregar(raices.get(dm.group(1).lower(), set()), [dm.group(2)], rhs)
        if marcas is not None:
            for hm in _HDR_TRL.finditer(rhs):
                vals = re.findall(r'"([^"]*)"', hm.group(5))
                for r in raices.get(hm.group(1).lower(), set()):
                    marcas.setdefault(r, {})[hm.group(2)] = (int(hm.group(3)), int(hm.group(4)), vals)
        if filtros is not None:
            for fm in _WHERE_LIT.finditer(rhs):
                for col, op, lit in _condiciones_and(fm.group(1)):
                    if col not in creadas:
                        for r in roots_first:
                            filtros.setdefault(r, {}).setdefault(col, []).append((op, lit))
        # literales de expresion en llamadas que referencian columnas
        if _COL_CALLS.search(rhs):
            for lit in _STR_LIT.findall(rhs):
                if on and f'"{lit}"' in on.group(1):
                    continue
                sin_textos = re.sub(r"'(?:[^'\\]|\\.)*'", "''", lit)  # quitar literales 'texto'
                agregar(roots_first, _IDENT.findall(sin_textos), lit)
    # lados de join: _bnx_ensure_side(X_df, ["col", ...]) lista las columnas que se leen de X
    for em in re.finditer(r'_bnx_ensure_side\(\s*(\w+_df)\s*,\s*\[([^\]]*)\]', code):
        agregar(raices.get(em.group(1).lower(), set()), re.findall(r'"(\w+)"', em.group(2)), "")
    return out


def escribir_parquet(dest, columnas, filas):
    """Escribe un dataset parquet (carpeta con part-00000.parquet) con el primer motor
    disponible: pyarrow -> fastparquet -> escritor puro-python (src.parquet_puro).
    NUNCA usa PySpark dentro del proceso del servidor: sin Java/winutils (Windows) Py4J
    se cuelga o tumba la conexion ("Failed to fetch" en la GUI).
    Devuelve el nombre del motor usado."""
    datos = {c: [r.get(c) for r in filas] for c in columnas}
    os.makedirs(dest, exist_ok=True)
    out = os.path.join(dest, "part-00000.parquet")
    try:
        import pyarrow as pa
        import pyarrow.parquet as pq
        pq.write_table(pa.table(datos), out)
        return "pyarrow"
    except ImportError:
        pass
    try:
        import pandas as pd
        import fastparquet  # noqa: F401  (solo para saber si esta)
        pd.DataFrame(datos, columns=columnas).to_parquet(out, engine="fastparquet", index=False)
        return "fastparquet"
    except ImportError:
        pass
    from src import parquet_puro
    parquet_puro.escribir(out, columnas, filas)
    return "python-puro"


def _nombre_dataset(ruta):
    """'raw/banca/x.dat' / 'output/banca/x.dat' -> 'banca/x.dat' (sin zona)."""
    return ruta.split("/", 1)[1] if "/" in ruta else ruta


def _jobs_del_plan(o, seleccion=None, _nivel=0, _cubiertas=frozenset(), _prefijo="", _pila=()):
    """Jobs (pasos graph con codigo) del plan y de sus sub-planes, en orden de ejecucion.

    Cada item: {paso, step, code, lee: [(var, ruta, resuelto)], escribe: {ruta_output},
    cubiertas: set de rutas de entrada que llegan por un enlace habilitado}.
    seleccion (ids del nivel superior): solo esos pasos cuentan; los sub-planes van completos."""
    out = []
    steps = {s["id"]: s for s in o["steps"]}
    on = {i for i, s in steps.items() if s["enabled"] and (seleccion is None or i in seleccion)}
    enlaces = [e for e in (o.get("enlaces") or []) if e.get("habilitado", True) and e["desde"] in on]
    try:
        orden = topo_order(o["steps"])
    except ValueError:
        orden = [s["id"] for s in o["steps"]]
    for sid in orden:
        s = steps[sid]
        a = s["action"]
        if sid not in on:
            continue
        cub = set(_cubiertas) | {e["entrada"] for e in enlaces if e["hacia"] == sid}
        if a["type"] == "plan" and _nivel < 3:
            try:
                fp = _ruta_plan(a["target"])
                if os.path.realpath(fp) in _pila:
                    continue
                with open(fp, "r", encoding="utf-8") as f:
                    sub = json.load(f)
                out += _jobs_del_plan(sub, None, _nivel + 1, frozenset(cub), f"{_prefijo}{sid}/",
                                      _pila + (os.path.realpath(fp),))
            except (OSError, ValueError, KeyError):
                pass
            continue
        if a["type"] != "graph" or not a.get("target") or a.get("status") != "ok":
            continue
        try:
            with open(a["target"], "r", encoding="utf-8", errors="replace") as f:
                code = f.read()
        except OSError:
            continue
        defaults = {m.group(1): (m.group(2) if m.group(2) is not None else m.group(3))
                    for m in _PARAM_DEF.finditer(code)}
        lee = []
        for m in _READ_VAR.finditer(code):
            nombre, resuelto = _resolver_nombre(m.group(2), defaults)
            lee.append((m.group(1), "raw/" + nombre.lstrip("/"), resuelto))
        escribe = {w["ruta"] for w in parse_job_io(a["target"])["escribe"] if w["resuelto"]}
        out.append({"paso": f"{_prefijo}{sid}", "step": s, "code": code, "lee": lee,
                    "escribe": escribe, "cubiertas": cub, "defaults": defaults})
    return out


def _clasificar_entradas(jobs):
    """Recorre los jobs en orden y devuelve [(job, var, ruta, resuelto, origen)] donde origen es
    None (entrada EXTERNA: la aporta el usuario), ('enlace', None) o ('intermedio', paso)
    cuando un job anterior del plan escribe ese mismo dataset (output/X -> raw/X)."""
    producido = {}   # nombre sin zona -> paso que lo escribe
    res = []
    for j in jobs:
        for var, ruta, resuelto in j["lee"]:
            nombre = _nombre_dataset(ruta)
            if ruta in j["cubiertas"]:
                origen = ("enlace", None)
            elif nombre in producido and producido[nombre] != j["paso"]:
                origen = ("intermedio", producido[nombre])
            else:
                origen = None
            res.append((j, var, ruta, resuelto, origen))
        for w in j["escribe"]:
            producido.setdefault(_nombre_dataset(w), j["paso"])
    return res


def entradas_faltantes(o, base_path, seleccion=None, _nivel=0):
    """Datasets <base>/raw/... EXTERNOS que los jobs del plan leen y NO existen. No cuenta los que
    llegan por un enlace ni los INTERMEDIOS (los escribe un paso anterior del plan o de un
    sub-plan: output/X -> raw/X, se materializan al ejecutar). Con seleccion (--paso/--desde)
    solo cuentan como productores los pasos seleccionados."""
    base = normalizar_base_path(base_path)
    falt = []
    for j, var, ruta, resuelto, origen in _clasificar_entradas(_jobs_del_plan(o, seleccion)):
        if origen is not None or not resuelto:
            continue
        if not os.path.exists(os.path.join(base, *ruta.split("/"))) and ruta not in falt:
            falt.append(ruta)
    return falt


def _valor_hdr_trl(i, n, ini, largo, vals, base):
    """Texto de la fila i de n para un campo cuyo substring(ini, largo) se compara con
    los marcadores `vals` (p.ej. ["HDR", "TRL"]): cabecera, cola o datos."""
    pre = "x" * (ini - 1)
    if i == 0 and vals:
        marca = vals[0]
    elif i == n - 1 and len(vals) > 1:
        marca = vals[1]
    else:
        marca = "DAT"
        while marca in vals:
            marca = "D" + marca
    return pre + marca[:largo].ljust(largo, "0") + "|" + str(base if base is not None else "")


# --- esquema desde el DML del .mp -------------------------------------------------------

def _tipo_dml(t):
    t = (t or "").lower()
    if t in ("integer", "int", "long", "bigint", "smallint", "number"):
        return "integer"
    if t in ("decimal", "real", "double", "float", "numeric"):
        return "decimal"
    if t in ("date", "datetime"):
        return t
    return "string"


_DML_CAMPO = re.compile(r"^\s*(\w+)\s*(?:\([^)]*\))?\s*(?:\([^)]*\))?\s+(\w+)\s*(?:=[^;]*)?;", re.M)


def _columnas_dml(texto):
    """[{name, type}] de un record DML (campos simples `tipo(n) nombre;`)."""
    cols, vistos = [], set()
    for m in _DML_CAMPO.finditer(texto):
        if m.group(1).lower() in ("record", "end", "begin", "type", "let", "if"):
            continue
        if m.group(2).lower() not in vistos:
            vistos.add(m.group(2).lower())
            cols.append({"name": m.group(2), "type": _tipo_dml(m.group(1))})
    return cols


def _dir_abinitio(target):
    """abinitio/<proyecto> hermano de output/<proyecto> del job (None si no existe)."""
    proj = os.path.basename(os.path.dirname(os.path.abspath(target)))
    for raiz in (os.getcwd(), _ROOT):
        d = os.path.join(raiz, "abinitio", proj)
        if os.path.isdir(d):
            return d
    return None


def _buscar_ci(d, nombre):
    try:
        for f in os.listdir(d):
            if f.lower() == nombre.lower():
                return os.path.join(d, f)
    except OSError:
        pass
    return None


def _leer(path):
    try:
        with open(path, "r", encoding="utf-8", errors="replace") as f:
            return f.read()
    except OSError:
        return ""


def _mp_del_paso(a, ab):
    cand = []
    src = a.get("source") or ""
    if src.lower().endswith(".pset"):
        ps = _buscar_ci(ab, src)
        m = re.search(r"^!prototype\|[^|]*\|[^|]*\|[^|]*\|\S*?([^/\\|\s]+\.mp)\s*$", _leer(ps) if ps else "", re.M)
        if m:
            cand.append(m.group(1))
    elif src.lower().endswith(".mp"):
        cand.append(src)
    stem = re.sub(r"_spark$", "", os.path.splitext(os.path.basename(a.get("target") or ""))[0])
    cand.append(stem + ".mp")
    for c in cand:
        p = _buscar_ci(ab, c)
        if p:
            return p
    return None


def _dml_de_entradas(a):
    """{'nodo': {nodo_lower: cols}, 'layout': {basename_layout: cols}} de los Input File del .mp
    del paso, con las columnas/tipos de su DML (metadata_file o record embebido)."""
    ab = _dir_abinitio(a.get("target") or "")
    res = {"nodo": {}, "layout": {}, "ab": ab}
    mp = _mp_del_paso(a, ab) if ab else None
    if not mp:
        return res
    for bloque in re.split(r"(?=\{2010503005\|XXGfvertex\|)", _leer(mp)):
        if "Datasets/Input_File" not in bloque:
            continue
        nom = re.findall(r"\}\}@([^|\n]+)\|@@", bloque)
        cols = []
        mf = re.search(r"\|metadata_file\|([^|]*)\|", bloque)
        if mf:
            p = _buscar_ci(ab, re.split(r"[/\\]", mf.group(1).strip())[-1])
            cols = _columnas_dml(_leer(p)) if p else []
        if not cols:
            rec = re.search(r"\|(?:out_metadata|in_metadata)\|(record.*?end;)", bloque, re.S)
            cols = _columnas_dml(rec.group(1)) if rec else []
        if not cols:
            continue
        if nom:
            res["nodo"][nom[-1].strip().lower()] = cols
        lay = re.search(r"\|Layout\|([^|]*)\|", bloque)
        if lay:
            res["layout"][os.path.basename(lay.group(1).strip()).lower()] = cols
    return res


def _columnas_de_fuente(var, ruta, dml, cols_codigo, cols_infer, alias):
    """Columnas finales de un dataset externo y la nota de origen.
    1) DML del .mp: EXACTAMENTE sus columnas/tipos (+ las que el codigo usa y el DML no trae).
    2) columnas detectadas en el codigo con tipo por uso.
    3) infer_input_schema, sin alias ni relleno col1..col3.  4) 'id'."""
    cols = dml["nodo"].get(var.lower()) or dml["layout"].get(os.path.basename(ruta).lower())
    if not cols and dml.get("ab"):
        p = _buscar_ci(dml["ab"], os.path.splitext(os.path.basename(ruta))[0] + ".dml")
        cols = _columnas_dml(_leer(p)) if p else []
    if cols:
        res = [dict(c) for c in cols]
        conocidas = {c["name"].lower() for c in res}
        for n, t in cols_codigo.items():
            if n.lower() not in conocidas and n not in alias:
                res.append({"name": n, "type": t})
        return res, "esquema tomado del DML"
    if cols_codigo:
        return [{"name": n, "type": t} for n, t in cols_codigo.items()], None
    inf = [c for c in cols_infer if c["name"] not in alias and not re.fullmatch(r"col[1-3]", c["name"])]
    if inf:
        return inf, None
    return [{"name": "id", "type": "string"}], "sin columnas detectadas: se uso 'id'"


def _cumple(v, op, lit):
    try:
        if op == "==":
            return v == lit
        if op == "!=":
            return v != lit
        if op == "in":
            return v in lit
        return {">": v > lit, ">=": v >= lit, "<": v < lit, "<=": v <= lit}[op]
    except TypeError:
        return False


def _aplicar_filtros(rows, cols, conds, hdr_trl=()):
    """Hace que ~80% de las filas cumplan las condiciones AND de los filtros del job (==, IN,
    <, >...) sobre cada columna, y deja el resto como las genero el generador (rechazos).
    Determinista: la fila i es de rechazo si i % 5 == 4. No toca columnas HDR/TRL."""
    tipo = {c["name"]: c["type"] for c in cols}
    n = len(rows)
    for col, lista in conds.items():
        if col not in tipo or col in hdr_trl:
            continue
        es_num = tipo[col] in ("integer", "decimal")
        lista = [(op, lit) for op, lit in lista if _lit_num(lit) == es_num]
        for i, row in enumerate(rows):
            if not lista or (i % 5 == 4 and n >= 5):
                continue
            if all(_cumple(row.get(col), op, lit) for op, lit in lista):
                continue
            nuevo = _valor_que_cumple(lista, es_num, tipo[col], i)
            if nuevo is not None:
                row[col] = nuevo


def _lit_num(lit):
    x = lit[0] if isinstance(lit, list) and lit else lit
    return isinstance(x, (int, float)) and not isinstance(x, bool)


def _valor_que_cumple(lista, es_num, tipo, i):
    eq = next((lit for op, lit in lista if op == "=="), None)
    if eq is None:
        ins = next((lit for op, lit in lista if op == "in"), None)
        if ins:
            eq = ins[i % len(ins)]
    if eq is not None:
        return eq
    if not es_num:
        return None
    lo = hi = None
    lo_incl = hi_incl = True
    for op, lit in lista:
        if not isinstance(lit, (int, float)) or isinstance(lit, bool):
            continue
        if op in (">", ">=") and (lo is None or lit >= lo):
            lo, lo_incl = lit, op == ">="
        elif op in ("<", "<=") and (hi is None or lit <= hi):
            hi, hi_incl = lit, op == "<="
    ent = tipo == "integer"
    paso = 1 if ent else 0.01
    if lo is not None and hi is not None:
        ini = lo if lo_incl else lo + paso
        fin = hi if hi_incl else hi - paso
        if fin < ini:
            return None
        v = ini + (fin - ini) * ((i * 37) % 101) / 100
    elif lo is not None:
        v = (lo if lo_incl else lo + paso) + (i * 37) % 500
    elif hi is not None:
        v = (hi if hi_incl else hi - paso) - (i * 37) % 500
    else:
        return None
    return int(v) if ent else round(float(v), 2)


def generar_datos(o, base_path, n_rows=20, seed=42, sobrescribir=False, seleccion=None):
    """Escribe parquet sintetico en <base>/raw/<x> para cada ENTRADA EXTERNA de los jobs del plan.

    - Externa = dataset raw que ningun paso anterior del plan (ni de los sub-planes de un plan
      de planes) escribe como output/<mismo nombre> ni llega por un enlace. Los intermedios se
      materializan al ejecutar (enlaces) y NO se generan.
    - Esquema: si el .mp tiene DML para esa entrada (metadata_file o record embebido), sus
      columnas y tipos EXACTOS; si no, las columnas que el codigo usa de la fuente con tipo
      inferido por uso. Nunca alias de joins ni col1..col3 si hay columnas conocidas.
    - Valores: src.datagen.build_synthetic_data (PII redactada, claves de join compartidas) y
      ~80% de las filas cumplen los filtros con literales del job (el resto ejercita rechazos).
    - Se omiten los enlaces, las rutas con parametros sin resolver y las que ya existen (salvo
      sobrescribir=True). Solo base_path local; las rutas deben quedar dentro de base_path.
    Devuelve una lista de dicts {paso, ruta, estado, filas?, columnas?, motivo?}.
    """
    from src.py2spark import infer_input_schema
    from src.datagen import build_synthetic_data

    validar_plan(o)
    if not base_path or "://" in base_path:
        raise ValueError("generar datos requiere un base_path local (no s3://)")
    base = os.path.realpath(normalizar_base_path(base_path))
    hechos, rep = set(), []
    cache = {}
    for j, var, ruta, resuelto, origen in _clasificar_entradas(_jobs_del_plan(o, seleccion)):
        item = {"paso": j["paso"], "ruta": ruta}
        if not resuelto:
            rep.append({**item, "estado": "omitido",
                        "motivo": "parametro sin valor; defina la variable de entorno"})
            continue
        if origen is not None:
            rep.append({**item, "estado": "omitido",
                        "motivo": ("llega por un enlace" if origen[0] == "enlace"
                                   else f"intermedio: lo produce el paso {origen[1]}")})
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
        code, a = j["code"], j["step"]["action"]
        if j["paso"] not in cache:
            lecturas = [v for v, _r, _ok in j["lee"]]
            marcas, filtros = {}, {}
            linaje = _columnas_por_fuente(code, lecturas, marcas, filtros)
            alias = _alias_creados(code)
            for lit in _STR_LIT.findall(code):
                alias |= set(re.findall(r"`?\b([A-Za-z_]\w*)`?\s*\.\s*`?[A-Za-z_]", lit))
            try:
                infer = {x["node"].lower(): x["columns"] for x in infer_input_schema(code)}
            except Exception:
                infer = {}
            cache[j["paso"]] = (marcas, filtros, linaje, alias, infer, _dml_de_entradas(a))
        marcas, filtros, linaje, alias, infer, dml = cache[j["paso"]]
        cols, nota = _columnas_de_fuente(var, ruta, dml, linaje.get(var.lower(), {}),
                                         infer.get(var.lower(), []), alias)
        gen = build_synthetic_data(cols, n_rows=n_rows, fmt="json", seed=seed)
        nombres = [c["name"] for c in gen["columns"]]
        hdr_trl = marcas.get(var.lower()) or {}
        for cn, (ini, largo, vals) in hdr_trl.items():
            # filas HDR/TRL (primera/ultima) + filas de datos: el filtro tiene efecto
            n_f = len(gen["rows"])
            for i, row in enumerate(gen["rows"]):
                if cn in row:
                    row[cn] = _valor_hdr_trl(i, n_f, ini, largo, vals, row[cn])
        _aplicar_filtros(gen["rows"], gen["columns"], filtros.get(var.lower(), {}), hdr_trl)
        if os.path.isdir(dest):
            shutil.rmtree(dest)
        elif os.path.exists(dest):
            os.remove(dest)
        try:
            motor = escribir_parquet(dest, nombres, gen["rows"])
        except Exception as e:   # un dataset que falla no debe tumbar la respuesta
            rep.append({**item, "estado": "error",
                        "motivo": f"{type(e).__name__}: {str(e)[:300]}"})
            continue
        hechos.add(ruta)
        rep.append({**item, "estado": "generado", "filas": len(gen["rows"]), "motor": motor,
                    "columnas": [f"{c['name']}:{c['type']}" for c in gen["columns"]],
                    **({"motivo": nota} if nota else {})})
    return rep


# ---------------------------------------------------------------------------
# Generador de DAG de Airflow
# ---------------------------------------------------------------------------

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def dag_id_de(o):
    """dag_id unico por orquestacion (las variantes por pset tienen su propio nombre)."""
    return re.sub(r"\W", "_", "bnx_" + (o.get("nombre") or os.path.splitext(o.get("plan", "plan"))[0]))


def generar_airflow(o, root=None):
    """Texto de un DAG de Airflow equivalente a la orquestacion (solo pasos habilitados).

    - graph  -> BashOperator con `python3 job.py` o `spark-submit ... job.py` (segun modo)
    - script -> BashOperator `ksh <script>`
    - python/shell/spark_submit/ssh/http/esperar_archivo/glue_job/emr_step/lambda/s3_copy ->
      BashOperator con el mismo comando que muestra el dry-run (curl, ssh, aws ...); el worker
      debe tener esos binarios y credenciales (token_env como variable de entorno)
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
    dag_id = dag_id_de(o)
    es_planes = o.get("tipo") == "plan_de_planes"
    py = "python3"

    def cmd_for(s):
        a = s["action"]
        if a["type"] in TIPOS_NUEVOS:
            return comando_airflow(s, ej, root)
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
         "    from airflow.operators.empty import EmptyOperator", ""]
    if es_planes:
        L += ["try:  # Airflow 3.x",
              "    from airflow.providers.standard.operators.trigger_dagrun import TriggerDagRunOperator",
              "except ImportError:  # Airflow 2.x",
              "    from airflow.operators.trigger_dagrun import TriggerDagRunOperator",
              "# Requiere en Airflow el DAG de cada plan (boton 'DAG Airflow' en cada uno).", ""]
    L += [f"ENV = {env!r}", "",
         f"with DAG(dag_id={dag_id!r}, schedule=None, start_date=datetime(2024, 1, 1),",
         "         catchup=False, tags=['bnx', 'abinitio']) as dag:"]
    if not steps:
        L.append("    pass  # orquestacion sin pasos")

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
        if a["type"] == "plan":
            # Sub-plan = su propio DAG (genera tambien el DAG de cada plan); se dispara y
            # se espera a que termine para respetar el orden del plan de planes.
            try:
                with open(_ruta_plan(a["target"]), "r", encoding="utf-8") as f:
                    sub_id = dag_id_de(json.load(f))
            except (OSError, ValueError):
                sub_id = dag_id_de({"plan": a.get("source") or s["name"]})
            L.append(f"    {name} = TriggerDagRunOperator(task_id={name!r}, trigger_rule={rule!r},")
            L.append(f"        trigger_dag_id={sub_id!r}, wait_for_completion=True, poke_interval=30)")
            continue
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
    for _s in (sys.stdout, sys.stderr):  # Windows cp1252: nombres/rutas con acentos
        try:
            _s.reconfigure(encoding="utf-8", errors="replace")
        except (AttributeError, ValueError):
            pass
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
            p.add_argument("--paso", default=None, help="ejecutar SOLO este paso (id)")
            p.add_argument("--desde", default=None, help="ejecutar este paso y todos los que dependen de el")
            p.add_argument("--sin-remotos", action="store_true",
                           help="omitir pasos remotos/nube (ssh, http, glue, emr, lambda, s3) en la ejecucion real")
            p.add_argument("--spark-args-json", default=None,
                           help="lista JSON de args de spark-submit (reemplaza ejecucion.spark_args)")
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
    cp = sub.add_parser("componer", help="plan de planes con 2+ orquestaciones")
    cp.add_argument("planes", nargs="+", help="orquestacion_*.json en el orden en que corren")
    cp.add_argument("--nombre", required=True)
    cp.add_argument("--out", default=None, help="carpeta de salida (default: la del primer plan)")
    cp.add_argument("--sin-cadena", action="store_true",
                    help="sin dependencias entre planes (se acomodan despues)")
    nv = sub.add_parser("nueva", help="orquestacion vacia desde cero (sin .plan)")
    nv.add_argument("nombre")
    nv.add_argument("--proyecto", required=True)
    nv.add_argument("--out", default=None, help="carpeta base (default: output/)")
    pa = sub.add_parser("paso-add", help="agrega un paso (python, shell, ssh, http, glue_job ...)")
    pa.add_argument("json")
    pa.add_argument("--tipo", required=True, choices=["graph", *TIPOS_NUEVOS])
    pa.add_argument("--nombre", required=True)
    pa.add_argument("--despues-de", action="append", default=[], help="paso previo (repetible)")
    pa.add_argument("--campo", action="append", default=[], metavar="CLAVE=VALOR",
                    help="campo del tipo; el valor se lee como JSON si es valido (repetible)")
    pr = sub.add_parser("paso-rm", help="quita un paso y sus dependencias/enlaces")
    pr.add_argument("json")
    pr.add_argument("paso")
    es = sub.add_parser("esperar", help="sensor: espera a que exista un archivo local o s3://")
    es.add_argument("ruta")
    es.add_argument("--timeout", type=int, default=300)
    es.add_argument("--intervalo", type=int, default=10)
    es.add_argument("--profile", default=None)
    es.add_argument("--region", default=None)
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
    if a.cmd == "nueva":
        ruta = nueva(a.nombre, a.proyecto, base=a.out)
        print("[ok]", ruta)
        return 0
    if a.cmd == "esperar":
        return 0 if esperar_archivo(a.ruta, a.timeout, a.intervalo, a.profile, a.region) else 1
    if a.cmd == "componer":
        o = componer(a.nombre, a.planes, en_cadena=not a.sin_cadena)
        out = a.out or os.path.dirname(os.path.abspath(a.planes[0]))
        for p in save_all({o["nombre"]: o}, out):
            print("[ok]", p)
        mostrar(o)
        return 0
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
        if a.paso and a.desde:
            raise SystemExit("[x] use --paso o --desde, no ambos")
        sa = None
        if a.spark_args_json is not None:
            try:
                sa = json.loads(a.spark_args_json)
            except ValueError:
                sa = None
            if not isinstance(sa, list) or not all(isinstance(x, str) for x in sa):
                raise SystemExit("[x] --spark-args-json debe ser una lista JSON de strings")
        return 0 if ejecutar(o, real=a.ejecutar, modo=a.modo,
                             base_path=(normalizar_base_path(a.base_path) if a.base_path else a.base_path),
                             solo=a.paso, desde=a.desde, permitir_remotos=not a.sin_remotos,
                             spark_args=sa) else 1
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
                                    "dag_" + dag_id_de(o)[len("bnx_"):] + ".py")
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
    elif a.cmd == "paso-add":
        campos = {}
        for kv in a.campo:
            k, sep, v = kv.partition("=")
            if not sep or not k:
                raise SystemExit(f"[x] --campo espera CLAVE=VALOR: {kv!r}")
            try:
                campos[k] = json.loads(v)
            except ValueError:
                campos[k] = v
        deps = [_find(o, d)["id"] for d in a.despues_de]
        agregar_paso(o, a.tipo, a.nombre, deps, **campos)
    elif a.cmd == "paso-rm":
        quitar_paso(o, a.paso)
        validar_plan(o)
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
