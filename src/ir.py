class Node:
    def __init__(self, node_id, node_type, attrs=None):
        self.id = node_id
        self.type = node_type
        self.attrs = attrs or {}


class DAG:
    def __init__(self):
        self.nodes = {}
        self.edges = {}

    def add_node(self, node):
        self.nodes[node.id] = node
        self.edges[node.id] = []

    def add_edge(self, src, dst):
        self.edges[src].append(dst)