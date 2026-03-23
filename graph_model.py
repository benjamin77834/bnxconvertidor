# graph_model.py

from collections import defaultdict, deque


class Node:
    def __init__(self, node_id, node_type, config=None):
        self.id = node_id
        self.type = node_type
        self.config = config or {}
        self.inputs = []
        self.outputs = []


class DAG:
    def __init__(self):
        self.nodes = {}
        self.edges = defaultdict(list)

    def add_node(self, node_id, node_type, config=None):
        self.nodes[node_id] = Node(node_id, node_type, config)

    def add_edge(self, src, dst):
        self.edges[src].append(dst)
        self.nodes[src].outputs.append(dst)
        self.nodes[dst].inputs.append(src)

    def topological_sort(self):
        indegree = {n: 0 for n in self.nodes}
        for src in self.edges:
            for dst in self.edges[src]:
                indegree[dst] += 1

        q = deque([n for n in self.nodes if indegree[n] == 0])
        order = []

        while q:
            node = q.popleft()
            order.append(node)

            for nxt in self.edges[node]:
                indegree[nxt] -= 1
                if indegree[nxt] == 0:
                    q.append(nxt)

        return order