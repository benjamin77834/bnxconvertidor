def topo_sort(dag):

    graph = {n: [] for n in dag.nodes}
    visited = set()
    order = []

    # build graph from EDGES
    for src, dst in dag.edges:
        if src in graph:
            graph[src].append(dst)

    def visit(node):
        if node in visited:
            return
        visited.add(node)

        for neigh in graph.get(node, []):
            visit(neigh)

        order.append(node)

    for node in dag.nodes:
        visit(node)

    return order