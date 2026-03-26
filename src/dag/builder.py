# src/dag/builder.py

class Node:
    def __init__(self, node_id, node_type, params):
        self.id = node_id
        self.name = node_id
        self.type = node_type
        self.params = params
        self.parents = []
        self.children = []

class DAG:
    def __init__(self, nodes_list, edges_list):
        # crear dict de nodos usando ID seguro
        self.nodes = {n["id"]: Node(n["id"], n["type"], n["params"]) for n in nodes_list}
        
        # asignar relaciones padre-hijo
        for e in edges_list:
            parent_id = e["from"]
            child_id = e["to"]
            self.nodes[parent_id].children.append(child_id)
            self.nodes[child_id].parents.append(parent_id)
        
        self.execution_order = self.topo_sort()

    def topo_sort(self):
        visited = set()
        order = []

        def visit(node_id):
            if node_id in visited:
                return
            visited.add(node_id)
            for p in self.nodes[node_id].parents:
                visit(p)
            order.append(self.nodes[node_id])

        for n in self.nodes:
            visit(n)
        return order

def build_dag(ast):
    return DAG(ast["nodes"], ast["edges"])