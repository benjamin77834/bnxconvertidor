def build_execution_plan(mp_data):
    """
    Simula parsing de grafo Ab Initio
    """
    nodes = mp_data.get("nodes", [])

    plan = []
    for n in nodes:
        plan.append({
            "id": n["id"],
            "type": n.get("type", "transform"),
            "inputs": n.get("inputs", [])
        })

    return plan