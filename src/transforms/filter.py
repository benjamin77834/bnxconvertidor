from src.transforms.registry import register

@register("filter")
def filter(node, inputs):

    df = inputs[0]

    condition = node.expr.get("condition", "1==1")

    return f"{df}.filter({condition})"