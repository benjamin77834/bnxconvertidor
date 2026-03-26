from collections import defaultdict, deque


def topo_sort(nodes, edges):
    graph = defaultdict(list)
    indegree = defaultdict(int)

    for n in nodes:
        indegree[n["id"]] = 0

    for s, d in edges:
        graph[s].append(d)
        indegree[d] += 1

    queue = deque([n for n in indegree if indegree[n] == 0])
    order = []

    visited = set()

    while queue:
        node = queue.popleft()
        order.append(node)
        visited.add(node)

        for neigh in graph[node]:
            indegree[neigh] -= 1
            if indegree[neigh] == 0:
                queue.append(neigh)

    # 🔥 FIX: agregar nodos perdidos (por ciclos)
    missing = [n["id"] for n in nodes if n["id"] not in visited]

    if missing:
        print(f"⚠️ Nodos fuera de DAG (posible ciclo): {missing}")
        order.extend(missing)

    return order