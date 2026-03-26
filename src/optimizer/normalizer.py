def normalize_graph(nodes):

    print("[OPT] V28 graph normalization + lineage-ready")

    for n in nodes:
        n["cost"] = {
            "INPUT": 1,
            "TRANSFORM": 3,
            "JOIN": 10,
            "ROLLUP": 8,
            "OUTPUT": 1
        }.get(n["type"], 5)

    return nodes