# src/dag/builder.py

class Node:
    def __init__(self, node_id, node_type, params):
        self.id = node_id
        self.name = node_id
        self.type = node_type
        self.params = params
        self.parents = []
        self.children = []
        self.db_source = None  # For Input_Table nodes (Teradata, Oracle, etc.)
        self.data_path = None  # For file-based SOURCE/SINK nodes

class DAG:
    def __init__(self, nodes_list, edges_list, exclude_edges=None):
        # crear dict de nodos usando ID seguro
        self.nodes = {n["id"]: Node(n["id"], n["type"], n.get("params", "")) for n in nodes_list}
        
        # Propagate db_source and data_path to Node objects
        for n in nodes_list:
            node_obj = self.nodes.get(n["id"])
            if node_obj:
                if "db_source" in n:
                    node_obj.db_source = n["db_source"]
                if "data_path" in n:
                    node_obj.data_path = n["data_path"]

        # Mega-DAG metadata (populated by build_mega_dag)
        self.cross_graph_edges = []
        self.retroceso_edges = []
        self.graph_boundaries = {}

        # Set of edge tuples to exclude from parent/child (retrocesos)
        self._exclude = set()
        if exclude_edges:
            for e in exclude_edges:
                self._exclude.add((e["from"], e["to"]))

        # asignar relaciones padre-hijo
        for e in edges_list:
            parent_id = e["from"]
            child_id = e["to"]
            if parent_id not in self.nodes or child_id not in self.nodes:
                continue
            if (parent_id, child_id) in self._exclude:
                continue
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
            # Visit parents first (ensure all dependencies are processed)
            for p in self.nodes[node_id].parents:
                visit(p)
            order.append(self.nodes[node_id])

        # Sort nodes by vertex_id (numeric) for stable ordering that respects
        # the visual layout of the Ab Initio graph (lower vertex IDs first)
        sorted_ids = sorted(self.nodes.keys(), key=lambda x: (
            # Extract numeric suffix for stable sort
            int(''.join(c for c in x if c.isdigit()) or '0'),
            x
        ))
        for n in sorted_ids:
            visit(n)
        return order

def build_dag(ast):
    return DAG(ast["nodes"], ast["edges"])


def build_mega_dag(merged_ast):
    """Build a DAG from a merged multi-graph AST, excluding retroceso edges from topo sort."""
    retroceso_edges = merged_ast.get("retroceso_edges", [])

    dag = DAG(merged_ast["nodes"], merged_ast["edges"], exclude_edges=retroceso_edges)

    dag.cross_graph_edges = merged_ast.get("cross_graph_edges", [])
    dag.retroceso_edges = retroceso_edges
    dag.graph_boundaries = merged_ast.get("subgraphs", {})

    return dag