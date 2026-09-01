import re


def parse_mp(path):

    nodes = []

    with open(path, "r", errors="replace") as f:
        lines = f.readlines()

    for line in lines:
        line = line.strip()

        if not line or line.startswith("#"):
            continue

        node_match = re.search(r"node:\s*(\w+)", line)
        if not node_match:
            continue

        node_id = node_match.group(1)

        type_match = re.search(r"type:\s*(\w+)", line)
        inputs_match = re.search(r"input:\s*([\w,]+)", line)

        node_type = type_match.group(1) if type_match else "transform"

        inputs = []
        if inputs_match:
            inputs = inputs_match.group(1).split(",")

        nodes.append({
            "id": node_id,
            "type": node_type,
            "inputs": inputs
        })

    return nodes