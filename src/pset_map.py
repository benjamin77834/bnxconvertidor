# src/pset_map.py
"""
Mapa de relaciones entre artefactos Ab Initio (equivalente al mapa de COBOL).

Escanea una carpeta con .pset / .mp / .plan / .xfr / .dml y construye:
  - pset  --instancia-->  grafo|plan      (por la linea !prototype del pset)
  - plan|grafo --usa-->   mp|pset|plan|xfr|dml|dbc  (rutas $AI_* dentro del archivo)
  - pset  --datos-->      pset            (OUTPUT de uno coincide con INPUT de otro)

Los archivos descargados suelen venir con prefijo numerico ("1_data_x.mp"); el
prefijo se ignora al resolver nombres. Lo que se referencia pero no esta en la
carpeta se marca como "faltante" (asi se ve que hay que pedir/descargar).

Uso:
    python -m src.pset_map <carpeta> [--out <dir>]
Genera pset_map.json, pset_map.md (con diagrama Mermaid) en --out (default: <carpeta>).
"""
import argparse
import json
import os
import re
from collections import defaultdict

EXT_KIND = {".pset": "pset", ".mp": "graph", ".plan": "plan",
            ".xfr": "xfr", ".dml": "dml", ".dbc": "dbc", ".ksh": "ksh"}

# Rutas $AI_XXX/...archivo.ext (con o sin llaves, con ${VAR} anidadas)
_REF_RE = re.compile(r"\$\{?AI_[A-Z_]+\}?/[A-Za-z0-9_./${}\-]+\.(?:mp|pset|plan|xfr|dml|dbc|ksh)")
_PROTO_RE = re.compile(r"^!prototype\|[^|]*\|{3}(.+)$")
_PARAM_RE = re.compile(r"^(\w+)\|[^|]?\|{3}(.*)$|^(\w+)\|{4}(.*)$")
_PREFIX_RE = re.compile(r"^\d+_")

_INPUT_KEYS = ("INPUT_FILE", "INPUT_INTERFACE_FILE")
_OUTPUT_KEYS = ("OUTPUT_FILE", "OUTPUT_NAME")


def _norm_name(path_or_ref):
    """Nombre base sin prefijo numerico de descarga: '1_foo.mp' -> 'foo.mp'."""
    return _PREFIX_RE.sub("", os.path.basename(path_or_ref))


def _kind_of(name):
    return EXT_KIND.get(os.path.splitext(name)[1].lower())


def _read(path):
    with open(path, "r", encoding="utf-8", errors="replace") as f:
        return f.read()


def parse_pset_file(path):
    """Devuelve {prototype, params} de un pset nativo (!prototype + NOMBRE|F|||VAL)."""
    proto, params = None, {}
    for line in _read(path).splitlines():
        line = line.strip()
        if not line:
            continue
        m = _PROTO_RE.match(line)
        if m:
            proto = m.group(1).strip()
            continue
        m = _PARAM_RE.match(line)
        if m:
            key = m.group(1) or m.group(3)
            val = m.group(2) if m.group(1) else m.group(4)
            params[key] = (val or "").strip()
    return {"prototype": proto, "params": params}


def parse_eme_refs(path):
    """Para .mp/.plan en formato EME-flatten: tipo real y referencias $AI_* unicas."""
    text = _read(path)
    m = re.search(r"Primary_Name\|(XX\w+)", text[:600])
    eme_type = m.group(1) if m else None
    refs = sorted(set(_REF_RE.findall(text)))
    return {"eme_type": eme_type, "refs": refs}


_ENT_RE = re.compile(r"^\{(\d+)\|(XXG\w+)\|(\d+)\|")
_REL_RE = re.compile(r"^\{(\d+)\|(XXG\w+_\w+_\w+)\|(\d+)\|[^{]*\{(.*?)\}(\d+)\|(\d+)\|\}\s*$")
_RUN_REF_RE = re.compile(r"[A-Za-z0-9_$\{\}/.\-]+\.(?:mp|pset|plan|ksh)\b")


def parse_plan_tasks(path):
    """Estructura interna de un .plan EME-flatten.

    Devuelve {"tasks": {id: {name, parent, type, refs}}, "order": [...]} donde
    order son aristas (desde -> hacia, flag) de las relaciones task_prior_task,
    tal cual vienen. El sentido (cual tarea corre primero) no esta verificado;
    'flag' es el primer campo numerico de la relacion (sin documentar).
    """
    ents, names, parent, order = {}, {}, {}, []
    refs = defaultdict(set)
    current = None
    for line in _read(path).splitlines():
        m = _ENT_RE.match(line)
        if m:
            eid, etype = int(m.group(3)), m.group(2)
            ents[eid] = etype
            # Metodos/objetos de soporte cuelgan de la tarea en curso
            if etype in ("XXGtask", "XXGconditionaltask", "XXGplan"):
                current = eid
        if current is not None:
            for r in _RUN_REF_RE.findall(line):
                if r.startswith("$AI_") or "${AI_" in r:
                    refs[current].add(_norm_name(r))
        m = _REL_RE.match(line)
        if not m:
            continue
        rtype, label, a, b = m.group(2), m.group(4), int(m.group(5)), int(m.group(6))
        if rtype == "XXGplan_task_task":
            names[b] = label.split("|")[0]
            parent[b] = a
        elif rtype == "XXGtask_prior_task":
            parts = label.split("|")
            order.append({"from": a, "to": b, "flag": parts[0] if parts else ""})
    tasks = {}
    for tid, nm in names.items():
        tasks[tid] = {"id": tid, "name": nm, "parent": parent.get(tid),
                      "type": ents.get(tid), "refs": sorted(refs.get(tid, []))}
    return {"tasks": tasks, "order": order}


def plan_tree_md(plan_name, info):
    """Arbol indentado de tareas + orden de ejecucion para un plan."""
    tasks, order = info["tasks"], info["order"]
    kids = defaultdict(list)
    for t in tasks.values():
        kids[t["parent"]].append(t)
    roots = [t for t in tasks.values() if t["parent"] not in tasks]
    lines = [f"### {plan_name}", ""]

    def walk(t, depth):
        refs = f"  -> {', '.join('`'+r+'`' for r in t['refs'])}" if t["refs"] else ""
        lines.append("  " * depth + f"- {t['name']} (id {t['id']}){refs}")
        for c in sorted(kids.get(t["id"], []), key=lambda x: x["id"]):
            walk(c, depth + 1)

    for r in sorted(roots, key=lambda x: x["id"]):
        walk(r, 0)
    lines += ["", "Relaciones task_prior_task tal cual vienen en el archivo (a -> b). "
              "El sentido exacto (cual corre primero) NO esta verificado contra Ab Initio:", ""]
    for o in order:
        a, b = tasks.get(o["from"]), tasks.get(o["to"])
        if a and b:
            lines.append(f"- {a['name']} (id {a['id']}) -> {b['name']} (id {b['id']}) [flag {o['flag']}]")
    return "\n".join(lines) + "\n"


def scan(folder):
    """Construye el mapa completo de una carpeta. Devuelve dict serializable."""
    nodes = {}  # clave = nombre normalizado
    for fname in sorted(os.listdir(folder)):
        kind = _kind_of(fname)
        if kind not in ("pset", "graph", "plan", "xfr", "dml"):
            continue
        key = _norm_name(fname)
        path = os.path.join(folder, fname)
        node = {"name": key, "file": fname, "kind": kind, "present": True}
        if kind == "pset":
            node.update(parse_pset_file(path))
        elif kind in ("graph", "plan"):
            node.update(parse_eme_refs(path))
            if kind == "plan":
                node["plan_info"] = parse_plan_tasks(path)
        # Si dos archivos colapsan al mismo nombre (duplicados "(1)"), se conserva el primero
        if key in nodes:
            nodes[key].setdefault("duplicates", []).append(fname)
        else:
            nodes[key] = node

    edges = []

    def ensure(name):
        """Registra un nodo faltante (referenciado pero no presente)."""
        if name not in nodes:
            nodes[name] = {"name": name, "file": None,
                           "kind": _kind_of(name) or "unknown", "present": False}
        return name

    for node in list(nodes.values()):
        if node["kind"] == "pset" and node.get("prototype"):
            tgt = ensure(_norm_name(node["prototype"]))
            edges.append({"from": node["name"], "to": tgt, "type": "instancia"})
            # Archivos de soporte referenciados desde los parametros del pset
            for k, v in node["params"].items():
                for ref in _REF_RE.findall(v):
                    edges.append({"from": node["name"], "to": ensure(_norm_name(ref)),
                                  "type": "param:" + k})
        elif node["kind"] in ("graph", "plan"):
            for ref in node.get("refs", []):
                edges.append({"from": node["name"], "to": ensure(_norm_name(ref)),
                              "type": "usa"})

    # Flujo de datos entre psets: OUTPUT de A == INPUT de B (comparando nombre base)
    def _tail(v):
        v = re.sub(r"\$\{?\w+\}?", "", v or "")
        return os.path.basename(v).strip()

    outs, ins = defaultdict(list), defaultdict(list)
    for n in nodes.values():
        if n["kind"] != "pset" or not n["present"]:
            continue
        for k in _OUTPUT_KEYS:
            t = _tail(n["params"].get(k))
            if t:
                outs[t].append(n["name"])
        for k in _INPUT_KEYS:
            t = _tail(n["params"].get(k))
            if t:
                ins[t].append(n["name"])
    for t, producers in outs.items():
        for p in producers:
            for c in ins.get(t, []):
                if p != c:
                    edges.append({"from": p, "to": c, "type": "datos:" + t})

    # Agrupacion por grafo/plan: que psets lo instancian (util para ver "familias")
    instances = defaultdict(list)
    for e in edges:
        if e["type"] == "instancia":
            instances[e["to"]].append(e["from"])

    missing = sorted(n["name"] for n in nodes.values() if not n["present"])
    orphans = sorted(n["name"] for n in nodes.values()
                     if n["present"] and n["kind"] in ("graph", "plan")
                     and n["name"] not in instances)
    return {"folder": os.path.abspath(folder), "nodes": nodes, "edges": edges,
            "instances": dict(instances), "missing": missing,
            "graphs_without_pset": orphans}


def find_psets_for_graph(graph_path, search_dir=None):
    """Psets de search_dir (default: carpeta del grafo) cuyo !prototype apunta a graph_path.

    Compara por nombre base sin prefijo numerico. Devuelve rutas ordenadas.
    """
    target = _norm_name(graph_path)
    folder = search_dir or os.path.dirname(os.path.abspath(graph_path))
    found = []
    for fname in sorted(os.listdir(folder)):
        if not fname.lower().endswith(".pset"):
            continue
        path = os.path.join(folder, fname)
        try:
            proto = parse_pset_file(path)["prototype"]
        except OSError:
            continue
        if proto and _norm_name(proto) == target:
            found.append(path)
    # Si el grafo viene como "13_x.mp", prefiere el pset "13_*.pset" (varios psets
    # pueden instanciar el mismo grafo con parametros distintos).
    pm = re.match(r"^(\d+)_", os.path.basename(graph_path))
    if pm:
        found.sort(key=lambda p: not os.path.basename(p).startswith(pm.group(1) + "_"))
    return found


def to_mermaid(m, include_support=False):
    """Diagrama Mermaid. Por defecto solo pset/graph/plan (sin xfr/dml/dbc)."""
    keep = {"pset", "graph", "plan"} | ({"xfr", "dml", "dbc"} if include_support else set())
    ids = {}

    def nid(name):
        return ids.setdefault(name, f"n{len(ids)}")

    lines = ["flowchart LR"]
    for name, n in m["nodes"].items():
        if n["kind"] not in keep:
            continue
        shape = {"pset": '(["%s"])', "graph": '["%s"]', "plan": '{{"%s"}}'}.get(n["kind"], '["%s"]')
        label = name if n["present"] else name + " (faltante)"
        lines.append(f"  {nid(name)}{shape % label}")
    for e in m["edges"]:
        a, b = m["nodes"].get(e["from"]), m["nodes"].get(e["to"])
        if not a or not b or a["kind"] not in keep or b["kind"] not in keep:
            continue
        label = e["type"].split(":")[0]
        if e["type"].startswith("datos:"):
            lines.append(f'  {nid(e["from"])} -.->|"{e["type"][6:]}"| {nid(e["to"])}')
        else:
            lines.append(f'  {nid(e["from"])} -->|{label}| {nid(e["to"])}')
    return "\n".join(lines)


def to_markdown(m):
    """Reporte legible: tabla de psets, familias por grafo, faltantes y diagrama."""
    out = ["# Mapa de relaciones Ab Initio", "", f"Carpeta: `{m['folder']}`", ""]
    by_kind = defaultdict(int)
    for n in m["nodes"].values():
        if n["present"]:
            by_kind[n["kind"]] += 1
    out.append("Archivos: " + ", ".join(f"{k}={v}" for k, v in sorted(by_kind.items())))
    out += ["", "## Psets y lo que instancian", "",
            "| Pset | Instancia | Estado | Parametros |", "|---|---|---|---|"]
    for n in m["nodes"].values():
        if n["kind"] != "pset" or not n["present"]:
            continue
        proto = _norm_name(n["prototype"]) if n.get("prototype") else "(sin prototype)"
        tgt = m["nodes"].get(proto)
        estado = "presente" if tgt and tgt["present"] else "FALTANTE"
        out.append(f"| {n['name']} | {proto} | {estado} | {len(n['params'])} |")
    out += ["", "## Grafos/planes y quien los instancia", ""]
    for name, n in m["nodes"].items():
        if n["kind"] in ("graph", "plan"):
            psets = m["instances"].get(name, [])
            tag = "" if n["present"] else " (faltante)"
            out.append(f"- `{name}`{tag} [{n.get('eme_type') or n['kind']}]: "
                       + (", ".join(f"`{p}`" for p in psets) if psets else "sin pset"))
    plans = [(n["name"], n["plan_info"]) for n in m["nodes"].values() if n.get("plan_info")]
    if plans:
        out += ["", "## Tareas y orden de los planes", ""]
        out += [plan_tree_md(nm, info) for nm, info in plans]
    flows = [e for e in m["edges"] if e["type"].startswith("datos:")]
    out += ["", "## Flujo de datos entre psets", ""]
    out += [f"- `{e['from']}` -> `{e['to']}` ({e['type'][6:]})" for e in flows] or ["- (ninguno detectado)"]
    out += ["", "## Faltantes (referenciados, no estan en la carpeta)", ""]
    out += [f"- `{x}`" for x in m["missing"] if m["nodes"][x]["kind"] in ("graph", "plan", "pset")] or ["- ninguno"]
    out += ["", "## Soporte faltante (xfr/dml/dbc)", ""]
    sup = [x for x in m["missing"] if m["nodes"][x]["kind"] not in ("graph", "plan", "pset")]
    out += [f"- `{x}`" for x in sup] or ["- ninguno"]
    out += ["", "## Diagrama", "", "```mermaid", to_mermaid(m), "```", ""]
    return "\n".join(out)


def main(argv=None):
    ap = argparse.ArgumentParser(description="Mapa de relaciones pset/grafo/plan")
    ap.add_argument("folder")
    ap.add_argument("--out", default=None)
    args = ap.parse_args(argv)
    m = scan(args.folder)
    out_dir = args.out or args.folder
    os.makedirs(out_dir, exist_ok=True)
    with open(os.path.join(out_dir, "pset_map.json"), "w", encoding="utf-8") as f:
        json.dump(m, f, indent=2, ensure_ascii=False)
    with open(os.path.join(out_dir, "pset_map.md"), "w", encoding="utf-8") as f:
        f.write(to_markdown(m))
    print(f"[ok] {len(m['nodes'])} nodos, {len(m['edges'])} relaciones, "
          f"{len(m['missing'])} faltantes -> {out_dir}")
    return m


if __name__ == "__main__":
    main()
