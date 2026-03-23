def export_dot(nodes, edges):

    dot = []
    dot.append("digraph BNX {")
    dot.append("rankdir=LR;")

    for n in nodes:
        dot.append(f'"{n}" [shape=box];')

    for s, d in edges:
        dot.append(f'"{s}" -> "{d}";')

    dot.append("}")

    return "\n".join(dot)


def save_dot(path, content):
    with open(path, "w") as f:
        f.write(content)
