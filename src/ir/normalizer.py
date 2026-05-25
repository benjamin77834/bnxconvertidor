from src.ir.node import Node


def normalize(graph):
    """
    Convierte dict / mixed input ? strict Node IR
    """

    normalized = []

    for n in graph:

        if isinstance(n, dict):
            normalized.append(Node(
                id=n.get("id"),
                type=n.get("type"),
                inputs=n.get("inputs", []),
                expr=n.get("expr"),
                attrs=n.get("attrs", {})
            ))
        else:
            normalized.append(n)

    return normalized