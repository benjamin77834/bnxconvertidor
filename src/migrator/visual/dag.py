def export_dot(nodes, edges):

    d = "digraph BNX {\n"

    for n in nodes:
        d += f'  "{n}";\n'

    for s, t in edges:
        d += f'  "{s}" -> "{t}";\n'

    d += "}"

    return d


def save_dot(path, content):
    open(path, "w").write(content)