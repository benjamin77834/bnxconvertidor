class DAGEngine:

    def sort(self, ir):

        # 🔥 soporta IRGraph tipo dict container
        if hasattr(ir, "nodes"):
            nodes = ir.nodes
        else:
            nodes = ir

        # si ya es dict
        if isinstance(nodes, dict):
            node_list = list(nodes.values())
        else:
            node_list = list(nodes)

        print("🧪 DAG ENGINE DEBUG")
        print("NODES INPUT:", len(node_list))

        # 🟢 MVP: no ordenar aún, solo pasar limpio
        class DAG:
            def __init__(self, nodes):
                self.nodes = {n.id: n for n in node_list}

        return DAG(node_list)