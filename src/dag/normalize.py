# src/dag/normalize.py
def normalize_dag(raw_dag):
    nodes = []
    for node, deps in raw_dag.items():
        nodes.append({
            "name": node.replace(".", "_"),
            "type": "input" if not deps else "process",
            "inputs": deps,
            "params": {}
        })
    return {"nodes": nodes}