from collections import defaultdict, deque


def build_dag(nodes_list, edges):

    node_names = [n["name"] for n in nodes_list if isinstance(n, dict)]

    graph = defaultdict(list)
    indegree = {n: 0 for n in node_names}

    clean_edges = []

    for e in edges:
        if isinstance(e, (list, tuple)) and len(e) == 2:
            clean_edges.append((e[0], e[1]))

    for s, d in clean_edges:

        if s in indegree and d in indegree:
            graph[s].append(d)
            indegree[d] += 1

    roots = [n for n in node_names if indegree[n] == 0]

    if not roots:
        raise Exception("NO ROOT NODE")

    q = deque(roots)
    order = []

    while q:
        n = q.popleft()
        order.append(n)

        for nxt in graph[n]:
            indegree[nxt] -= 1
            if indegree[nxt] == 0:
                q.append(nxt)

    if len(order) != len(node_names):
        raise Exception("CYCLE DETECTED")

    return order