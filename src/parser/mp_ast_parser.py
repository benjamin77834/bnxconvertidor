import re
from dataclasses import dataclass, field


@dataclass
class ASTNode:
    name: str
    type: str
    inputs: list = field(default_factory=list)
    props: dict = field(default_factory=dict)


def parse_mp_ast(file_path: str):

    with open(file_path, "r") as f:
        raw = f.read()

    blocks = [b.strip() for b in raw.split("end") if "component" in b]

    ast_nodes = []

    for b in blocks:

        name = re.search(r"component (\w+)", b)
        type_ = re.search(r"type:\s*(\w+)", b)

        if not name or not type_:
            continue

        name = name.group(1)
        type_ = type_.group(1)

        inputs = []

        inputs_m = re.findall(r"inputs:\s*(.*)", b)
        input_m = re.findall(r"input:\s*(.*)", b)

        if inputs_m:
            inputs = [x.strip() for x in inputs_m[0].split(",")]
        elif input_m:
            inputs = [input_m[0].strip()]

        props = {}

        path = re.findall(r"path:\s*(.*)", b)
        keys = re.findall(r"keys:\s*(.*)", b)

        if path:
            props["path"] = path[0].strip()

        if keys:
            props["keys"] = keys[0].strip()

        ast_nodes.append(ASTNode(
            name=name,
            type=type_,
            inputs=inputs,
            props=props
        ))

    return ast_nodes