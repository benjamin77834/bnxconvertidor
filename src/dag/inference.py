def infer_type(node_name):

    name = node_name.lower()

    if "raw" in name:
        return "input"

    if "stage" in name:
        return "filter"

    if "clean" in name:
        return "filter"

    if "valid" in name:
        return "filter"

    if "join" in name:
        return "join"

    if "dq" in name or "check" in name:
        return "filter"

    if "aggregate" in name or "metrics" in name:
        return "aggregate"

    if "feature" in name:
        return "transform"

    if "ml" in name or "model" in name:
        return "transform"

    if "output" in name or "dashboard" in name:
        return "output"

    return "transform"