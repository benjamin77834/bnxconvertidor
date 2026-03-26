from collections import defaultdict, deque


def topological_sort(dag):

    graph = defaultdict(list)
    indegree = defaultdict(int)
    nodes = set()

    for node, inputs in dag.items():

        nodes.add(node)

        for i in inputs:
            nodes.add(i)
            graph[i].append(node)
            indegree[node] += 1

    for n in nodes:
        indegree.setdefault(n, 0)

    q = deque([n for n in nodes if indegree[n] == 0])

    order = []

    while q:

        n = q.popleft()
        order.append(n)

        for neigh in graph[n]:
            indegree[neigh] -= 1
            if indegree[neigh] == 0:
                q.append(neigh)

    if len(order) != len(nodes):
        raise Exception("❌ Cycle detected in DAG")

    return order