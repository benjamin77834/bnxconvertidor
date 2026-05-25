from graphviz import Digraph


def save_dag(plan, output_file="dag"):

    dot = Digraph()

    # nodes
    for node in plan:
        dot.node(node["id"], node["id"])

    # edges
    for node in plan:
        for inp in node.get("inputs", []):
            dot.edge(inp, node["id"])

    dot.render(output_file, format="png", cleanup=True)

    print(f"[>] DAG GENERATED: {output_file}.png")