def validate_dag(ir, schema_registry):

    for node_id, node in ir.nodes.items():

        if node.type == "join":

            left, right = node.inputs

            key = node.props.get("keys", ["id"])[0]

            if not schema_registry.has_column(left, key):
                print(f"❌ ERROR: {left} missing join key {key}")

            if not schema_registry.has_column(right, key):
                print(f"❌ ERROR: {right} missing join key {key}")