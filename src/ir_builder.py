def build_ir(nodes, edges, xfr):

    ir = []

    for node in nodes:

        if node in ["customers", "transactions1", "transactions2", "consumerinfo"]:
            ir.append({
                "id": node,
                "type": "source"
            })

        elif node == "rollup_household":
            ir.append({
                "id": node,
                "type": "aggregate",
                "group_by": ["customer_id"],
                "metrics": ["count"]
            })

        elif node == "reformat_consumer":
            ir.append({
                "id": node,
                "type": "map",
                "expressions": xfr.get(node, [])
            })

        elif node == "join_final":
            ir.append({
                "id": node,
                "type": "join",
                "inputs": [
                    "rollup_household",
                    "transactions2",
                    "reformat_consumer"
                ],
                "keys": ["customer_id"]
            })

        elif node == "select_output":
            ir.append({
                "id": node,
                "type": "sink"
            })

    return ir
