def topo_sort(nodes, edges):
    from collections import defaultdict, deque

    indeg = defaultdict(int)
    graph = defaultdict(list)

    for s, t in edges:
        graph[s].append(t)
        indeg[t] += 1

    q = deque([n for n in nodes if indeg[n] == 0])
    order = []

    while q:
        n = q.popleft()
        order.append(n)
        for nei in graph[n]:
            indeg[nei] -= 1
            if indeg[nei] == 0:
                q.append(nei)

    return order
