class GraphIR:

    def __init__(self):
        self.nodes = {}

    def add_node(self, node):
        self.nodes[node.id] = node

    # ? TOPOLOGICAL SORT (CR?TICO BNX v9)
    def topological_sort(self):

        visited = set()
        order = []

        def visit(nid):

            if nid in visited:
                return

            visited.add(nid)

            node = self.nodes[nid]

            for i in node.inputs:
                visit(i)

            order.append(node)

        for nid in self.nodes:
            visit(nid)

        return order

    # ? EDGES (LINEAGE GRAPH)
    def build_edges(self):
        return [
            (i, n.id)
            for n in self.nodes.values()
            for i in n.inputs
        ]

    # ? LINEAGE PRINT
    def print_lineage(self, edges):

        lineage = {}

        for s, d in edges:
            lineage.setdefault(d, []).append(s)

        for k, v in lineage.items():
            print(f"[~] {k} <- {v}")