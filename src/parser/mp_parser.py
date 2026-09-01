import re
from collections import defaultdict

def clean_node(x):

    x = x.strip()

    # eliminar "connect "
    x = re.sub(r"^connect\s+", "", x)

    return x


def parse_mp_ast(path):

    dag = defaultdict(list)

    with open(path, "r", errors="replace") as f:

        for line in f:

            line = line.strip()

            if "->" not in line:
                continue

            left, right = line.split("->")

            src = clean_node(left)
            dst = clean_node(right)

            if not src or not dst:
                continue

            if src == dst:
                continue

            dag[dst].append(src)

    # normalizar nodos reales
    all_nodes = set(dag.keys())

    for v in dag.values():
        all_nodes.update(v)

    for n in all_nodes:
        dag.setdefault(n, [])

    return dict(dag)