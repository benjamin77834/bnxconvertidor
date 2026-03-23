from src.transforms.registry import register

@register("reformat")
def reformat(node, inputs):

    df = inputs[0]

    expr = node.expr or {}

    cols = [
        f"{v} as {k}"
        for k, v in expr.items()
    ]

    return f"{df}.select({', '.join(cols)})"