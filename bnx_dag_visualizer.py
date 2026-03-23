# BNX DAG Visualizer
# Generates a visual DAG from execution plan

from graphviz import Digraph


def build_dag(plan):
    """
    plan: list of dict nodes like:
    {'id': 'Customers', 'inputs': []}
    """

    dot = Digraph()

    # Add nodes
    for node in plan:
        dot.node(node['id'])

    # Add edges
    for node in plan:
        for inp in node.get('inputs', []):
            dot.edge(inp, node['id'])

    return dot


def save_dag(plan, output_file="dag.gv"):
    dot = build_dag(plan)
    dot.render(output_file, format='png', cleanup=True)
    print(f"DAG generated: {output_file}.png")


if __name__ == "__main__":
    # Example execution plan (replace with your BNX output)
    execution_plan = [
        {'id': 'Customers', 'inputs': []},
        {'id': 'Transactions', 'inputs': []},
        {'id': 'Cards', 'inputs': ['Customers']},
        {'id': 'Devices', 'inputs': ['Customers']},
        {'id': 'FinalJoin', 'inputs': ['Transactions', 'Cards', 'Devices']}
    ]

    save_dag(execution_plan)

