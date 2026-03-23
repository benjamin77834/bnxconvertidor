from src.transforms.registry import register

@register("aggregate")
def aggregate(node, inputs):

    df = inputs[0]

    return f"{df}.groupBy().agg(*)"