from collections import defaultdict

def build_subgraphs(order, graph):

    visited = set()
    subgraphs = []

    def dfs(node, current):
        if node in visited:
            return
        visited.add(node)
        current.append(node)

        for nxt in graph.get(node, []):
            dfs(nxt, current)

    for node in order:
        if node not in visited:
            current = []
            dfs(node, current)
            subgraphs.append(current)

    return subgraphs