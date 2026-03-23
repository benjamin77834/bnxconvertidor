from collections import defaultdict, deque


def build_dag(ir):

    print("📊 Building DAG...")

    nodes = ir["nodes"]
    edges = ir["edges"]

    graph = defaultdict(list)
    indegree = {n: 0 for n in nodes}

    for s, t in edges:
        graph[s].append(t)
        indegree[t] += 1

    queue = deque([n for n in nodes if indegree[n] == 0])
    order = []

    while queue:
        n = queue.popleft()
        order.append(n)

        for neigh in graph[n]:
            indegree[neigh] -= 1
            if indegree[neigh] == 0:
                queue.append(neigh)

    print("📊 DAG ORDER:", order)

    return {
        "order": order,
        "edges": edges,
        "mappings": ir["mappings"],
        "schema": ir["schema"]
    }