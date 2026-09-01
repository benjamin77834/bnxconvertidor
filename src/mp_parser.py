# src/mp_parser.py
import re

def normalize_id(name):
    safe = re.sub(r"[^\w]", "_", name.strip())
    return safe


def _detect_native_abinitio(content):
    """Detect if file is native Ab Initio format (XXGpvertex/XXGedge)."""
    return "XXGpvertex" in content or "XXGedge" in content


def _map_abinitio_type(component_name):
    """Map Ab Initio component names to BNX node types."""
    name = component_name.lower()
    if any(k in name for k in ["read", "input", "scan", "source", "extract"]):
        return "SOURCE"
    if any(k in name for k in ["write", "output", "sink", "load"]):
        return "SINK"
    if any(k in name for k in ["merge", "join", "lookup"]):
        return "JOIN"
    if any(k in name for k in ["rollup", "aggregate", "summary"]):
        return "TRANSFORM"
    if any(k in name for k in ["reformat", "transform", "compute", "normalize"]):
        return "TRANSFORM"
    if any(k in name for k in ["sort"]):
        return "TRANSFORM"
    if any(k in name for k in ["dedup", "deduplicate", "remove duplicate"]):
        return "DEDUP"
    if any(k in name for k in ["partition", "repartition"]):
        return "PARTITION"
    if any(k in name for k in ["filter", "select", "where"]):
        return "FILTER"
    if any(k in name for k in ["concatenate", "gather", "combine"]):
        return "CONCATENATE"
    return "TRANSFORM"


def _parse_native_abinitio(content):
    """Parse native Ab Initio .mp format (XXGpvertex/XXGedge)."""
    nodes = []
    edges = []
    params = {}
    node_map = {}  # vertex_id ? node info

    for line in content.split("\n"):
        line = line.strip()
        if not line:
            continue

        # Parse vertex (component): {timestamp|XXGpvertex|id|...|name|...}
        m = re.match(r'\{[^|]*\|XXGpvertex\|(\d+)\|', line)
        if m:
            vid = m.group(1)
            # Extract component name ? it's after @1| in the line
            name_match = re.search(r'@1\|([^|]+)\|', line)
            if name_match:
                comp_name = name_match.group(1).strip()
            else:
                # Fallback: try to find a readable name
                parts = line.split("|")
                comp_name = f"Component_{vid}"
                for p in parts:
                    p = p.strip()
                    if len(p) > 3 and not p.isdigit() and not p.startswith("{") and not p.startswith("@") and "XXG" not in p and "Ab Initio" not in p and "Built-in" not in p:
                        comp_name = p
                        break

            ntype = _map_abinitio_type(comp_name)
            nid = normalize_id(comp_name)

            # Handle duplicate names
            if nid in node_map:
                nid = f"{nid}_{vid}"

            node_map[vid] = {"id": nid, "name": comp_name, "type": ntype}
            nodes.append({
                "id": nid,
                "name": comp_name,
                "type": ntype,
                "params": "",
                "subgraph": None,
            })
            continue

        # Parse edge: {timestamp|XXGedge|from_id|to_id|...}
        m = re.match(r'\{[^|]*\|XXGedge\|(\d+)\|(\d+)\|', line)
        if m:
            from_vid = m.group(1)
            to_vid = m.group(2)
            if from_vid in node_map and to_vid in node_map:
                edges.append({
                    "from": node_map[from_vid]["id"],
                    "to": node_map[to_vid]["id"],
                })
            continue

        # Parse parameters: {id|XXparameter|name|value|...}
        m = re.match(r'\{[^|]*\|XXparameter\|([^|]+)\|([^|]*)\|', line)
        if m:
            params[m.group(1).strip()] = m.group(2).strip()
            continue

    return {"nodes": nodes, "edges": edges, "subgraphs": {}, "abinitio_params": params}


def parse_mp_ast(file_path):
    with open(file_path, "r", errors="replace") as f:
        content = f.read()

    # Auto-detect native Ab Initio format
    if _detect_native_abinitio(content):
        return _parse_native_abinitio(content)

    # BNX format
    nodes = []
    edges = []
    subgraphs = {}
    current_subgraph = None

    for line in content.split("\n"):
        line = line.strip()
        if not line or line.startswith("#"):
            continue

        # SUBGRAPH inicio: SUBGRAPH NombreSub {
        m = re.match(r"(?i)SUBGRAPH\s+(\w+)\s*\{", line)
        if m:
            current_subgraph = m.group(1)
            subgraphs[current_subgraph] = []
            continue

        # Cierre de subgraph
        if line == "}":
            current_subgraph = None
            continue

        # Formato: NODE NombreNodo : tipo
        m = re.match(r"(?i)NODE\s+(\w+)\s*:\s*(\w+)", line)
        if m:
            nid = normalize_id(m.group(1))
            nodes.append({
                "id": nid,
                "name": m.group(1),
                "type": m.group(2).upper(),
                "params": "",
                "subgraph": current_subgraph
            })
            if current_subgraph:
                subgraphs[current_subgraph].append(nid)
            continue

        # Formato: A -> B  (edge)
        m = re.match(r"(\w+)\s*->\s*(\w+)", line)
        if m:
            edges.append({"from": normalize_id(m.group(1)), "to": normalize_id(m.group(2))})
            continue

        # Formato legacy: NombreNodo:TIPO:params
        parts = line.split(":")
        name = parts[0].strip()
        node_type = parts[1].strip() if len(parts) > 1 else "XFR"
        params = ":".join(parts[2:]).strip() if len(parts) > 2 else ""
        nid = normalize_id(name)
        nodes.append({
            "id": nid,
            "name": name,
            "type": node_type.upper(),
            "params": params,
            "subgraph": current_subgraph
        })
        if current_subgraph:
            subgraphs[current_subgraph].append(nid)

    return {"nodes": nodes, "edges": edges, "subgraphs": subgraphs}