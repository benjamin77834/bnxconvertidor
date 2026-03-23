class IRNode:
    def __init__(self, node_id, node_type, inputs=None, props=None):
        self.id = node_id
        self.type = node_type
        self.inputs = inputs or []
        self.props = props or {}


class IR:
    def __init__(self):
        self.nodes = {}
        self.edges = []


def build_ir(nodes, edges):

    print("\n🧬 IR BUILDER STARTED")

    ir = IR()

    # -------------------------
    # build nodes
    # -------------------------
    for node_id, attrs in nodes.items():

        ir.nodes[node_id] = IRNode(
            node_id=node_id,
            node_type=attrs.get("type", "transform"),
            inputs=attrs.get("inputs", []),
            props=attrs.get("props", {})
        )

    ir.edges = edges

    print(f"✔ IR NODES: {len(ir.nodes)}")
    print(f"✔ IR EDGES: {len(ir.edges)}")

    return ir