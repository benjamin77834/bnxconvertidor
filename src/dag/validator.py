def validate_dag(nodes, edges):

    node_names = set(n["name"] if isinstance(n, dict) else n for n in nodes)

    for s, d in edges:

        if s not in node_names:
            raise Exception(f"Missing source: {s}")

        if d not in node_names:
            raise Exception(f"Missing target: {d}")

    print("✅ DAG VALID")