class DAG:
    def __init__(self, nodes, edges):
        self.nodes = nodes
        self.edges = edges

    def is_valid(self):
        # aquí puedes meter cycle detection después
        return True


def build_dag(nodes, edges):
    return DAG(nodes, edges)