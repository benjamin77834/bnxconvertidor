def build_lineage(plan):
    lineage = {}

    for node in plan:
        lineage[node["id"]] = node.get("inputs", [])

    return lineage