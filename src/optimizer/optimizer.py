def optimize_plan(dag):

    print("\n⚡ OPTIMIZER START")

    nodes = dag.get("nodes", {})
    graph = dag.get("graph", {})

    # -----------------------------------
    # SIMPLE OPTIMIZATION RULES (BNX MVP)
    # -----------------------------------

    optimized_graph = {}

    # Rule 1: remove self loops
    for src, targets in graph.items():
        optimized_targets = []

        for t in targets:
            if t != src:
                optimized_targets.append(t)

        optimized_graph[src] = optimized_targets

    # Rule 2: remove empty nodes
    optimized_nodes = {
        k: v for k, v in nodes.items()
    }

    print(f"✔ nodes optimized: {len(optimized_nodes)}")
    print(f"✔ edges optimized: {sum(len(v) for v in optimized_graph.values())}")

    return {
        "nodes": optimized_nodes,
        "graph": optimized_graph
    }