import re


class MPParser:

    def parse(self, mp_path):

        with open(mp_path, "r") as f:
            content = f.read()

        print("\n🧪 RAW FILE CONTENT:")
        print(content)
        print("SIZE:", len(content))

        nodes = []
        edges = []

        lines = content.splitlines()

        for line in lines:
            line = line.strip()

            if not line:
                continue

            # -----------------------------------------
            # FORMATO 1: NODE A:input
            # -----------------------------------------
            m = re.match(r"(?i)NODE\s+(\w+)\s*:\s*(\w+)", line)
            if m:
                nodes.append({
                    "id": m.group(1),
                    "type": m.group(2)
                })
                continue

            # -----------------------------------------
            # FORMATO 2: A(input)
            # -----------------------------------------
            m = re.match(r"(\w+)\s*\(\s*(\w+)\s*\)", line)
            if m:
                nodes.append({
                    "id": m.group(1),
                    "type": m.group(2)
                })
                continue

            # -----------------------------------------
            # FORMATO 3: EDGE A -> B
            # -----------------------------------------
            m = re.match(r"(\w+)\s*->\s*(\w+)", line)
            if m:
                edges.append({
                    "from": m.group(1),
                    "to": m.group(2)
                })
                continue

            # -----------------------------------------
            # FORMATO 4: JOIN / SPLIT estilo simple
            # JOIN(A,B)
            # -----------------------------------------
            m = re.match(r"(?i)JOIN\s*\(\s*(\w+)\s*,\s*(\w+)\s*\)", line)
            if m:
                join_node = f"JOIN_{m.group(1)}_{m.group(2)}"

                nodes.append({
                    "id": join_node,
                    "type": "join"
                })

                edges.append({"from": m.group(1), "to": join_node})
                edges.append({"from": m.group(2), "to": join_node})
                continue

        print(f"\n✔ NODES FOUND: {len(nodes)}")
        print(f"✔ EDGES FOUND: {len(edges)}")

        if len(nodes) == 0:
            print("\n⚠️ WARNING: No nodes detected. Check MP format.")

        return {
            "nodes": nodes,
            "edges": edges,
            "raw": content
        }
