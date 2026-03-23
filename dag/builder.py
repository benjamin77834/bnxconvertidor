class Node:
    def __init__(self, id, type, inputs=None):
        self.id = id
        self.type = type
        self.inputs = inputs or []


class DAG:
    def __init__(self):
        self.nodes = {}

    def add(self, node):
        self.nodes[node.id] = node

    def topo_sort(self):
        return list(self.nodes.keys())


def build_dag(mp_path):
    dag = DAG()

    dag.add(Node("Customers", "source"))
    dag.add(Node("Transactions", "source"))
    dag.add(Node("CleanCustomers", "transform", ["Customers"]))
    dag.add(Node("FilterTx", "transform", ["Transactions"]))
    dag.add(Node("Join1", "join", ["CleanCustomers", "FilterTx"]))
    dag.add(Node("FINAL", "sink", ["Join1"]))

    return dag