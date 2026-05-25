# src/utils/normalizer.py

def clean_name(name):
    if not name:
        return None

    return (
        str(name)
        .replace("connect", "")
        .replace(";", "")
        .strip()
        .split(".")[-1]  # quita prefijos tipo layer.name
    )


def normalize_nodes(nodes):
    seen = {}
    normalized = []

    for n in nodes:
        if isinstance(n, dict):
            nid = n.get("id") or n.get("name")
        else:
            nid = n

        nid = clean_name(nid)

        if not nid:
            continue

        if nid not in seen:
            seen[nid] = True
            normalized.append({
                "id": nid,
                "type": infer_type(nid)
            })

    return normalized


def normalize_edges(edges):
    normalized = []

    for e in edges:
        s, d = e

        s = clean_name(s)
        d = clean_name(d)

        # ? FIX CLAVE
        if not s or not d:
            continue

        if s == d:
            continue  # ? elimina ciclos tipo A -> A

        normalized.append((s, d))

    return normalized


def infer_type(nid):
    if nid.startswith("Raw"):
        return "input"
    if nid.startswith("Stage"):
        return "stage"
    if "Join" in nid:
        return "join"
    if "Aggregate" in nid:
        return "aggregate"
    if "Report" in nid or "Dashboard" in nid:
        return "output"
    return "transform"