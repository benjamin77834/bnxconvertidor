def topological_sort(plan):

    graph = {n["id"]: n.get("inputs", []) for n in plan}

    visited = set()
    result = []

    def visit(node):
        if node in visited:
            return
        visited.add(node)

        for dep in graph.get(node, []):
            visit(dep)

        result.append(node)

    for node in graph:
        visit(node)

    return result


def execute_dag(plan):

    order = topological_sort(plan)

    print("\n🚀 EXECUTION ORDER:")

    for node in order:
        print(f"⚡ Running node: {node}")

    return order