class GraphIR:
    def __init__(self):
        self.nodes = {}   # id -> Node
        self.edges = []   # (src, dst)

    def add_node(self, node):
        self.nodes[node.id] = node

    def add_edge(self, src, dst):
        self.edges.append((src, dst))