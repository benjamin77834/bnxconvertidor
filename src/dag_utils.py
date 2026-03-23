def build_graph(plan):

    graph = {}

    for node in plan:
        node_id = node["id"]
        inputs = node.get("inputs", [])

        graph[node_id] = inputs

    return graph


def topological_sort(graph):

    visited = set()
    order = []

    def dfs(node):
        if node in visited:
            return
        visited.add(node)

        for dep in graph.get(node, []):
            dfs(dep)

        order.append(node)

    for node in graph:
        dfs(node)

    return order