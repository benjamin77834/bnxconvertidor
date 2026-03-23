class IRNode:

    def __init__(self, node_id, node_type, attrs=None):
        self.id = node_id
        self.type = node_type
        self.attrs = attrs or {}

    def __repr__(self):
        return f"IRNode(id={self.id}, type={self.type})"


def build_ir(mp_graph):

    nodes = mp_graph.get("nodes", [])
    edges = mp_graph.get("edges", [])

    print("\n🧠 IR BUILDER START")

    ir_nodes = {}

    # -----------------------------
    # BUILD NODES
    # -----------------------------
    for n in nodes:
        node = IRNode(n["id"], n["type"])
        ir_nodes[n["id"]] = node

    # -----------------------------
    # BUILD GRAPH
    # -----------------------------
    graph = {}

    for e in edges:
        src = e["from"]
        dst = e["to"]

        if src not in graph:
            graph[src] = []

        graph[src].append(dst)

    print(f"✔ IR nodes: {len(ir_nodes)}")
    print(f"✔ IR edges: {len(edges)}")

    return {
        "nodes": ir_nodes,
        "graph": graph
    }