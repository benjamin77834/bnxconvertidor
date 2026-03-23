from collections import defaultdict, deque


def topo_sort(dag):

    indegree = defaultdict(int)

    for src in dag.edges:
        for dst in dag.edges[src]:
            indegree[dst] += 1

    q = deque([n for n in dag.nodes if indegree[n] == 0])

    order = []

    while q:
        n = q.popleft()
        order.append(n)

        for nei in dag.edges.get(n, []):
            indegree[nei] -= 1
            if indegree[nei] == 0:
                q.append(nei)

    return order