def build_execution_plan(ir):

    visited = set()
    order = []

    def dfs(node_id):
        if node_id in visited:
            return

        visited.add(node_id)

        node = ir.nodes.get(node_id)
        if not node:
            return

        for inp in node.inputs:
            dfs(inp)

        order.append(node_id)

    for node_id in ir.nodes:
        dfs(node_id)

    return order