def parse_mp_file(path):

    print("\n🔥 PARSER STARTED")

    nodes = {}
    edges = []

    with open(path, "r") as f:
        lines = [l.strip() for l in f.readlines() if l.strip()]

    print(f"📄 LINES: {len(lines)}")

    for line in lines:

        # ---------------------------
        # CLEAN LINE (REMOVE KEYWORDS)
        # ---------------------------
        line = line.replace("connect", "").strip()
        line = line.replace("link", "").strip()

        # ---------------------------
        # EDGE DETECTION
        # ---------------------------
        if "->" in line:

            parts = line.split("->")

            if len(parts) != 2:
                continue

            src = parts[0].strip()
            dst = parts[1].strip()

            edges.append((src, dst))

            # ensure nodes exist
            if src not in nodes:
                nodes[src] = {
                    "id": src,
                    "type": "transform",
                    "inputs": [],
                    "props": {}
                }

            if dst not in nodes:
                nodes[dst] = {
                    "id": dst,
                    "type": "transform",
                    "inputs": [],
                    "props": {}
                }

            nodes[dst]["inputs"].append(src)

        # ---------------------------
        # NODE DETECTION
        # ---------------------------
        else:

            node = line.strip()

            if node and node not in nodes:
                nodes[node] = {
                    "id": node,
                    "type": "transform",
                    "inputs": [],
                    "props": {}
                }

    print(f"🔗 EDGES: {len(edges)}")
    print(f"🧠 NODES: {len(nodes)}")

    return nodes, edges