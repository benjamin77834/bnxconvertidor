# src/mp_parser.py
import re

def normalize_id(name):
    safe = re.sub(r"[^\w]", "_", name.strip())
    return safe

def parse_mp_ast(file_path):
    nodes = []
    edges = []
    subgraphs = {}   # { subgraph_name: [node_ids] }

    current_subgraph = None

    with open(file_path, "r") as f:
        for line in f:
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