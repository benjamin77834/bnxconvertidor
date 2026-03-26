def parse_mp_ast(path):

    print("[MP_AST] loading file:", path)

    nodes = []
    edges = []
    metadata = {}

    with open(path, "r") as f:
        lines = f.readlines()

    for line in lines:
        line = line.strip()

        if not line:
            continue

        # =========================
        # SIMPLE EDGE DETECTION
        # =========================
        if "->" in line:

            parts = line.split("->")

            if len(parts) == 2:
                src = parts[0].strip()
                dst = parts[1].strip()

                nodes.append({"name": src})
                nodes.append({"name": dst})

                edges.append((src, dst))

        # =========================
        # NODE DECLARATION FALLBACK
        # =========================
        else:
            nodes.append({"name": line})

    # =========================
    # DEDUPLICATE NODES
    # =========================
    unique = {}

    for n in nodes:
        unique[n["name"]] = n

    nodes = list(unique.values())

    print(f"[MP_AST] nodes={len(nodes)} edges={len(edges)}")

    return nodes, edges, metadata