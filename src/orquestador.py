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
            elif st["action"]["type"] == "script" and st["action"]["status"] == "ok":
                # El .ksh se ejecuta/regenera por ruta: la del archivo en la carpeta Ab Initio
                # (relativa a la raiz del proyecto si esta dentro), no el nombre suelto.
                fp = os.path.abspath(os.path.join(ab_folder, m["nodes"][st["action"]["target"]]["file"]))
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

def ejecutar(o, real=False, modo=None, base_path=None, _nivel=0, _pila=()):
    validar_plan(o)
    ej = _ej(o, modo, base_path)
    order = topo_order(o["steps"])
    by_id = {s["id"]: s for s in o["steps"]}
    enlaces = [e for e in (o.get("enlaces") or []) if e.get("habilitado", True)]
    done, failed, faltantes = set(), set(), []
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
        if a["type"] == "noop" or (not a.get("target") and a["type"] not in TIPOS_NUEVOS):
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
        if a["type"] == "plan":
            # Paso = otra orquestacion completa. Se ejecuta en este mismo proceso (el
            # dry-run se ve anidado). base_path y --modo del plan de planes, si se dan,
            # se comparten con todos los sub-planes; si no, cada uno usa el suyo.
            fp = _ruta_plan(a["target"])
            print(f"{sangria}[>] {sid} {s['name']}: plan {a['target']}")
            if os.path.realpath(fp) in _pila or _nivel >= 3:
                print(f"{sangria}[x] {sid}: plan anidado en ciclo o demasiado profundo")
                failed.add(sid)
                continue
            try:
                with open(fp, "r", encoding="utf-8") as f:
                    sub = json.load(f)
                kw = dict(real=real, modo=modo, base_path=(_base_efectiva(ej) or None),
                          _nivel=_nivel + 1, _pila=_pila + (os.path.realpath(fp),))
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
                done.add(sid)
            elif not real:
                # dry-run: avisar y seguir, para ver tambien el detalle de los siguientes
                print(f"{sangria}[!] {sid} {s['name']}: este plan tiene faltantes (ver arriba)")
                faltantes.append(f"{sid} {s['name']} -> plan con faltantes")
                done.add(sid)
            else:
                print(f"{sangria}[x] {sid} {s['name']}: el plan termino con fallos o faltantes")
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
                failed.add(sid)
                continue
            print(f"[>] {sid} {s['name']} [{ubicacion_de(a)}/{a['type']}]: {shlex.join(cmd)}")
            if a["type"] == "http" and a.get("token_env"):
                print(f"    (header Authorization desde ${a['token_env']}, por stdin)")
            if not real:
                done.add(sid)
                continue
            try:
                rc = subprocess.run(cmd, env=_job_env(ej), input=entrada, text=entrada is not None,
                                    cwd=_ROOT if a["type"] == "esperar_archivo" else None).returncode
            except OSError as e:
                print(f"[x] {sid}: no se pudo lanzar {cmd[0]}: {e}")
                rc = 127
            if rc == 0:
                done.add(sid)
            else:
                print(f"[x] {sid} termino con codigo {rc}")
                if not s["continue_on_error"]:
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


_nivel_datos = [0]   # profundidad de recursion (plan de planes) en generar_datos
_spark_datos = [None]  # SparkSession reutilizada si no hay pyarrow/fastparquet


def escribir_parquet(dest, columnas, filas):
    """Escribe un dataset parquet (carpeta con part-00000.parquet) con el primer motor
    disponible: pyarrow -> fastparquet -> PySpark local. Antes solo pyarrow, y en
    servidores sin pyarrow fallaba con "No module named 'pyarrow'".
    Devuelve el nombre del motor usado; RuntimeError si no hay ninguno."""
    datos = {c: [r.get(c) for r in filas] for c in columnas}
    try:
        import pyarrow as pa
        import pyarrow.parquet as pq
        os.makedirs(dest, exist_ok=True)
        pq.write_table(pa.table(datos), os.path.join(dest, "part-00000.parquet"))
        return "pyarrow"
    except ImportError:
        pass
    try:
        import pandas as pd
        import fastparquet  # noqa: F401  (solo para saber si esta)
        os.makedirs(dest, exist_ok=True)
        pd.DataFrame(datos, columns=columnas).to_parquet(
            os.path.join(dest, "part-00000.parquet"), engine="fastparquet", index=False)
        return "fastparquet"
    except ImportError:
        pass
    try:
        from pyspark.sql import SparkSession
        from pyspark.sql.types import StructType, StructField, StringType, LongType, DoubleType
    except ImportError:
        raise RuntimeError("no hay como escribir parquet: instala pyarrow "
                           "(pip install pyarrow) o pyspark en el servidor del portal")
    if _spark_datos[0] is None:
        _spark_datos[0] = (SparkSession.builder.master("local[1]").appName("bnx_datos_sinteticos")
                           .config("spark.ui.enabled", "false").getOrCreate())
    spark = _spark_datos[0]

    def _tipo(vals):
        vs = [v for v in vals if v is not None]
        if vs and all(isinstance(v, bool) for v in vs):
            return StringType()
        if vs and all(isinstance(v, int) for v in vs):
            return LongType()
        if vs and all(isinstance(v, (int, float)) for v in vs):
            return DoubleType()
        return StringType()
    esquema = StructType([StructField(c, _tipo(datos[c]), True) for c in columnas])
    conv = []
    for r in filas:
        fila = []
        for c, f in zip(columnas, esquema.fields):
            v = r.get(c)
            if v is not None:
                v = (float(v) if isinstance(f.dataType, DoubleType) else
                     int(v) if isinstance(f.dataType, LongType) else str(v))
            fila.append(v)
        conv.append(tuple(fila))
    spark.createDataFrame(conv, esquema).coalesce(1).write.mode("overwrite").parquet(dest)
    return "pyspark"


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
        if s["id"] in on and a["type"] == "plan" and _nivel_datos[0] < 3:
            # Plan de planes: los datos de cada sub-plan van al MISMO base_path (es el
            # que se comparte al ejecutar el plan de planes).
            try:
                with open(_ruta_plan(a["target"]), "r", encoding="utf-8") as f:
                    sub = json.load(f)
                _nivel_datos[0] += 1
                for r in generar_datos(sub, base_path, n_rows=n_rows, seed=seed, sobrescribir=sobrescribir):
                    rep.append({**r, "paso": f"{s['id']}/{r['paso']}"})
            except (OSError, ValueError) as e:
                rep.append({"paso": s["id"], "ruta": a["target"], "estado": "error", "motivo": str(e)})
            finally:
                _nivel_datos[0] = max(0, _nivel_datos[0] - 1)
            continue
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
            if os.path.isdir(dest):
                shutil.rmtree(dest)
            elif os.path.exists(dest):
                os.remove(dest)
            try:
                motor = escribir_parquet(dest, nombres, gen["rows"])
            except RuntimeError as e:
                rep.append({**item, "estado": "error", "motivo": str(e)})
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
