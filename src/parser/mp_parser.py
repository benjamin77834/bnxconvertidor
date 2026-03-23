import re
from src.ir.model import Node


def parse_mp(file_path):

    with open(file_path, "r") as f:
        content = f.read()

    blocks = content.split("end")

    nodes = []

    for b in blocks:

        if "component" not in b:
            continue

        name_m = re.search(r"component (\w+)", b)
        type_m = re.search(r"type:\s*(\w+)", b)

        if not name_m or not type_m:
            continue

        name = name_m.group(1)
        type_ = type_m.group(1)

        # ✅ FIX IMPORTANTE: soporta input e inputs
        inputs = []

        inputs_m = re.findall(r"inputs:\s*(.*)", b)
        input_m = re.findall(r"input:\s*(.*)", b)

        if inputs_m:
            inputs = [x.strip() for x in inputs_m[0].split(",")]
        elif input_m:
            inputs = [input_m[0].strip()]

        path = re.findall(r"path:\s*(.*)", b)
        keys = re.findall(r"keys:\s*(.*)", b)

        nodes.append(Node(
            id=name,
            type=type_,
            inputs=inputs,
            props={
                "path": path[0].strip() if path else None,
                "keys": keys[0].strip() if keys else None
            }
        ))

    print(f"✔ NODES FOUND: {len(nodes)}")

    return nodes