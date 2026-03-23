def build_ir(mp_graph, xfr, dml):

    print("\n🧠 Building IR layer...")

    ir = []

    for node in mp_graph:

        ir_node = {
            "id": node.get("id"),
            "type": node.get("type", "unknown"),
            "inputs": node.get("inputs", [])
        }

        print(f"🧩 IR node: {ir_node}")

        ir.append(ir_node)

    return ir