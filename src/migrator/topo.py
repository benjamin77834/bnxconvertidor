from collections import defaultdict, deque

def topo_sort(nodes, edges):

    g = defaultdict(list)
    indeg = {n: 0 for n in nodes}

    for s, t in edges:
        g[s].append(t)
        indeg[t] += 1

    q = deque([n for n in nodes if indeg[n] == 0])
    order = []

    while q:
        n = q.popleft()
        order.append(n)

        for nxt in g[n]:
            indeg[nxt] -= 1
            if indeg[nxt] == 0:
                q.append(nxt)

    return order