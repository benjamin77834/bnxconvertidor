def optimize(ir, edges):

    print("🧠 OPTIMIZER STARTED")

    optimized_edges = []
    seen = set()

    # 1. remove duplicates
    for e in edges:
        if e not in seen:
            optimized_edges.append(e)
            seen.add(e)

    # 2. fusion simple chain
    # A → B → C = collapse possible chains later

    return ir, optimized_edges