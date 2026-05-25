from collections import defaultdict, deque


def topo(nodes, edges):

    graph = defaultdict(list)
    indeg = defaultdict(int)

    all_nodes = set(nodes.keys())

    # build graph
    for s, d in edges:
        graph[s].append(d)
        indeg[d] += 1
        all_nodes.add(s)
        all_nodes.add(d)

    # start nodes
    q = deque([n for n in all_nodes if indeg[n] == 0])

    order = []

    while q:

        n = q.popleft()
        order.append(n)

        for nxt in graph[n]:
            indeg[nxt] -= 1
            if indeg[nxt] == 0:
                q.append(nxt)

    # ? safety: append missing nodes
    for n in all_nodes:
        if n not in order:
            order.append(n)

    return order