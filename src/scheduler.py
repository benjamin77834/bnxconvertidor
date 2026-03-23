from collections import defaultdict, deque


def topo_sort(plan):

    indegree = defaultdict(int)

    for src in plan.edges:
        for dst in plan.edges[src]:
            indegree[dst] += 1

    q = deque([n for n in plan.nodes if indegree[n] == 0])

    order = []

    while q:
        n = q.popleft()
        order.append(n)

        for nei in plan.edges.get(n, []):
            indegree[nei] -= 1
            if indegree[nei] == 0:
                q.append(nei)

    return order