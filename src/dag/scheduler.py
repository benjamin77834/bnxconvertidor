from collections import defaultdict, deque

def topological_sort(dag):
    graph = defaultdict(list)
    indegree = defaultdict(int)

    nodes = set()

    for dst, sources in dag.items():
        nodes.add(dst)
        for s in sources:
            nodes.add(s)
            graph[s].append(dst)
            indegree[dst] += 1

    queue = deque([n for n in nodes if indegree[n] == 0])

    order = []

    while queue:
        node = queue.popleft()
        order.append(node)

        for neigh in graph[node]:
            indegree[neigh] -= 1
            if indegree[neigh] == 0:
                queue.append(neigh)

    return order