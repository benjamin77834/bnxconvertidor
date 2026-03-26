# src/mp_parser.py

def normalize_id(name):
    """Genera un ID seguro para Python: elimina espacios, paréntesis, comillas y signos"""
    import re
    safe = re.sub(r"[^\w]", "_", name.strip())
    return safe

def parse_mp_ast(file_path):
    nodes = []
    edges = []

    with open(file_path, "r") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue

            parts = line.split(":")
            name = parts[0].strip()
            node_type = parts[1].strip() if len(parts) > 1 else "XFR"
            params = ":".join(parts[2:]).strip() if len(parts) > 2 else ""

            nodes.append({
                "id": normalize_id(name),  # ID seguro para variable
                "name": name,              # nombre original para logs
                "type": node_type,
                "params": params
            })
    return {"nodes": nodes, "edges": edges}