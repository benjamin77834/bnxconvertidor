from src.ir.node import Node


def parse(graph):

    nodes = []

    for n in graph:

        if isinstance(n, dict):
            nodes.append(Node(
                id=n.get("id"),
                type=n.get("type"),
                inputs=n.get("inputs", []),
                expr=n.get("expr", []),
                attrs=n.get("attrs", {})
            ))
        else:
            nodes.append(n)

    return nodes