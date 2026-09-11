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

        # asignar relaciones padre-hijo.
        # Ademas guardamos el ORDINAL del puerto de entrada del hijo por el que
        # entra cada padre (e["to_port"]: in0=0, in1=1, ...). Para un JOIN de
        # Ab Initio, el cuerpo DML referencia inN posicionalmente (in0=current,
        # in1=previous, etc.), asi que el ORDEN de node.parents DEBE seguir el
        # ordinal del puerto, no el orden arbitrario de aparicion de las aristas
        # (que venia de un set y podia invertir in0/in1). Ver builder->codegen JOIN.
        parent_ports = {}  # child_id -> {parent_id: port_ordinal}
        for e in edges_list:
            parent_id = e["from"]
            child_id = e["to"]
            if parent_id not in self.nodes or child_id not in self.nodes:
                continue
            if (parent_id, child_id) in self._exclude:
                continue
            self.nodes[parent_id].children.append(child_id)
            self.nodes[child_id].parents.append(parent_id)
            _tp = e.get("to_port")
            if _tp is not None:
                parent_ports.setdefault(child_id, {})[parent_id] = _tp

        # Reordenar los padres de cada nodo por el ordinal de su puerto de entrada
        # cuando lo conocemos. Estable: los padres sin puerto conocido conservan su
        # posicion relativa (van al final, con clave grande). Solo afecta nodos con
        # multiples entradas (JOIN/MERGE); los demas quedan igual.
        for child_id, ports in parent_ports.items():
            if len(self.nodes[child_id].parents) <= 1:
                continue
            parents = self.nodes[child_id].parents
            self.nodes[child_id].parents = sorted(
                parents,
                key=lambda pid, _p=ports: (_p.get(pid, 1_000_000),),
            )

        self.execution_order = self.topo_sort()

    def topo_sort(self):
        # DFS con deteccion de ciclos por 3 estados (blanco/gris/negro):
        #  - blanco: sin visitar (no esta en done ni en on_stack)
        #  - gris: en la pila de recursion actual (on_stack) -> encontrar una arista
        #    hacia un gris significa CICLO
        #  - negro: procesado por completo (done)
        # Antes se usaba un unico set 'visited' que NO detectaba ciclos: un grafo
        # A->B->A incluia ambos nodos igualmente. Ahora, cuando una rama forma
        # parte de un ciclo, sus nodos se EXCLUYEN del orden de ejecucion (no se
        # pueden ordenar topologicamente) y se registran en self.cycle_nodes.
        done = set()          # negro
        on_stack = set()      # gris (pila de recursion)
        order = []
        cycle_nodes = set()

        def visit(node_id):
            if node_id in done:
                return True          # ya procesado, sin ciclo por esta via
            if node_id in on_stack:
                # Arista hacia un nodo en la pila actual -> CICLO.
                cycle_nodes.add(node_id)
                return False
            on_stack.add(node_id)
            in_cycle = False
            for p in self.nodes[node_id].parents:
                if not visit(p):
                    in_cycle = True
            on_stack.discard(node_id)
            if in_cycle:
                # Este nodo depende (transitivamente) de un ciclo: no se puede
                # ordenar; se excluye del execution_order.
                cycle_nodes.add(node_id)
                return False
            done.add(node_id)
            order.append(self.nodes[node_id])
            return True

        # Sort nodes by vertex_id (numeric) for stable ordering that respects
        # the visual layout of the Ab Initio graph (lower vertex IDs first)
        sorted_ids = sorted(self.nodes.keys(), key=lambda x: (
            # Extract numeric suffix for stable sort
            int(''.join(c for c in x if c.isdigit()) or '0'),
            x
        ))
        for n in sorted_ids:
            visit(n)
        # Exponer los nodos involucrados en ciclos para diagnostico.
        self.cycle_nodes = cycle_nodes
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