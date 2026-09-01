import re

def parse_mp(path):
    nodes = {}
    edges = []

    with open(path, "r", errors="replace") as f:
        for line in f:
            line = line.strip()

            if not line or line.startswith("#"):
                continue

            # [.] NODE formats supported:
            # NODE name input
            # name:input
            node_match = re.match(r"NODE\s+(\w+)\s+(\w+)", line)
            alt_node_match = re.match(r"(\w+)\s*:\s*(\w+)", line)

            if node_match:
                name, ntype = node_match.groups()
                nodes[name] = {"type": ntype}

            elif alt_node_match:
                name, ntype = alt_node_match.groups()
                nodes[name] = {"type": ntype}

            # [.] EDGE formats supported:
            # EDGE a b
            # a -> b
            edge_match = re.match(r"EDGE\s+(\w+)\s+(\w+)", line)
            arrow_match = re.match(r"(\w+)\s*->\s*(\w+)", line)

            if edge_match:
                src, dst = edge_match.groups()
                edges.append((src, dst))

            elif arrow_match:
                src, dst = arrow_match.groups()
                edges.append((src, dst))

    return {
        "nodes": nodes,
        "edges": edges
    }