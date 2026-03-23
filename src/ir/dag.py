from collections import defaultdict, deque

class DAG:

    def __init__(self, nodes):
        self.nodes = {n.id: n for n in nodes}
        self.graph = defaultdict(list)
        self.indegree = defaultdict(int)

        self._build()

    def _build(self):

        for node in self.nodes.values():
            for inp in node.inputs:
                self.graph[inp].append(node.id)
                self.indegree[node.id] += 1

        for n in self.nodes:
            self.indegree.setdefault(n, 0)

    def topological_sort(self):

        q = deque([n for n in self.nodes if self.indegree[n] == 0])
        result = []

        while q:

            current = q.popleft()
            result.append(self.nodes[current])

            for neigh in self.graph[current]:
                self.indegree[neigh] -= 1
                if self.indegree[neigh] == 0:
                    q.append(neigh)

        return result