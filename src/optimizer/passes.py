def remove_redundant_filters(ir):
    print("[>] OPTIMIZER: remove_redundant_filters")

    for node in ir.nodes.values():
        if node.type == "filter":
            expr = node.props.get("expr")
            if expr in [None, "1=1"]:
                node.type = "transform"

    return ir


def collapse_transforms(ir):
    print("[>] OPTIMIZER: collapse_transforms")

    for node in ir.nodes.values():
        if node.type == "transform" and not node.inputs:
            node.type = "noop"

    return ir