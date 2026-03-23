def validate_dag(nodes, edges):

    print("🧪 VALIDATING DAG")

    if isinstance(nodes, dict):
        node_ids = set(nodes.keys())
    else:
        node_ids = set(n["id"] for n in nodes)

    for src, dst in edges:

        src = str(src).strip()
        dst = str(dst).strip()

        if src not in node_ids:
            raise Exception(f"❌ missing node: {src}")

        if dst not in node_ids:
            raise Exception(f"❌ missing node: {dst}")

    print("✔ DAG VALID")