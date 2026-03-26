def clean_nodes(nodes):

    cleaned = {}

    for k, v in nodes.items():

        # 🔥 remove subgraph prefix (fraud_layer.X → X)
        name = k.split(".")[-1]

        v.name = name
        cleaned[name] = v

    return cleaned