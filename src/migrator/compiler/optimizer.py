def optimize_edges(edges):

    # simple heuristic: sources first
    return sorted(edges, key=lambda x: x[0])