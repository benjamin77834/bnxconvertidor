from src.transforms.registry import register

@register("join")
def join(node, inputs):

    left = inputs[0]
    right = inputs[1]

    key = node.expr.get("key", "id") if node.expr else "id"

    return f"{left}.join({right}, '{key}', 'inner')"