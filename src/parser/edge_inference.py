def infer_edges(content, nodes):

    print("[EDGE] V28 cross-layer + subgraph inference")

    node_set = {n["id"] for n in nodes}
    edges = set()

    for dst, srcs in content["inputs"].items():
        for src in srcs:

            if src in node_set and dst in node_set and src != dst:
                edges.add((src, dst))

    return sorted(list(edges))