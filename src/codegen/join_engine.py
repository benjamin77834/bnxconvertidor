def build_join(node, inputs):

    left = inputs[0]
    right = inputs[1]

    return f"{node.id} = {left}.join({right}, 'id', 'inner')"