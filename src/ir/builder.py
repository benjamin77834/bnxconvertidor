class IR:
    def __init__(self):
        self.nodes = {}
        self.edges = []


def build_ir(nodes, edges):

    print("\n? IR BUILDER STARTED")

    ir = IR()

    # -------------------------
    # FIX: iterate dict correctly
    # -------------------------
    for node_id, attrs in nodes.items():

        ir.nodes[node_id] = {
            "id": node_id,
            "type": attrs.get("type", "transform"),
            "inputs": attrs.get("inputs", []),
            "props": attrs.get("props", {})
        }

    # -------------------------
    # edges
    # -------------------------
    ir.edges = edges

    print(f"? IR NODES: {len(ir.nodes)}")
    print(f"? IR EDGES: {len(ir.edges)}")

    return ir