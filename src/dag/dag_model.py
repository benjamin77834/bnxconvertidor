class Node:
    def __init__(self, name, op, inputs=None, params=None):
        self.name = name
        self.op = op
        self.inputs = inputs or []
        self.params = params or {}


class DAG:
    def __init__(self):
        self.nodes = {}
        self.edges = []
        self.lineage = {}   # ? FIX ADDED

    def add_node(self, node):
        self.nodes[node.name] = node

        # lineage init
        self.lineage[node.name] = node.inputs or []

    def add_edge(self, src, dst):
        self.edges.append((src, dst))

        # lineage tracking
        if dst not in self.lineage:
            self.lineage[dst] = []
        self.lineage[dst].append(src)