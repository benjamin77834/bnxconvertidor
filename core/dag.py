from collections import defaultdict, deque

class Node:
    def __init__(self, id, type):
        self.id = id
        self.type = type
        self.inputs = []
        self.outputs = []

class DAG:
    def __init__(self):
        self.nodes = {}
        self.edges = defaultdict(list)

    def add_node(self, id, type):
        self.nodes[id] = Node(id, type)

    def add_edge(self, src, dst):
        self.edges[src].append(dst)
        self.nodes[src].outputs.append(dst)
        self.nodes[dst].inputs.append(src)

    def topo_sort(self):
        indegree = {n: 0 for n in self.nodes}
        for s in self.edges:
            for d in self.edges[s]:
                indegree[d] += 1

        q = deque([n for n in self.nodes if indegree[n] == 0])
        order = []

        while q:
            n = q.popleft()
            order.append(n)
            for nxt in self.edges[n]:
                indegree[nxt] -= 1
                if indegree[nxt] == 0:
                    q.append(nxt)

        return order