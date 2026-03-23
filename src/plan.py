class LogicalNode:
    def __init__(self, id, type, attrs=None):
        self.id = id
        self.type = type
        self.attrs = attrs or {}


class LogicalPlan:
    def __init__(self):
        self.nodes = {}
        self.edges = {}

    def add_node(self, node):
        self.nodes[node.id] = node
        self.edges[node.id] = []

    def add_edge(self, src, dst):
        self.edges[src].append(dst)