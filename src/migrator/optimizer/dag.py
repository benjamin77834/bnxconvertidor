from collections import defaultdict, deque


def topo_sort(nodes, edges):
    graph = defaultdict(list)
    indeg = defaultdict(int)

    for s, d in edges:
        graph[s].append(d)
        indeg[d] += 1
        indeg.setdefault(s, 0)

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


def find_sinks(nodes, edges):
    out = defaultdict(int)

    for s, d in edges:
        out[s] += 1

    return [n for n in nodes if out[n] == 0]
