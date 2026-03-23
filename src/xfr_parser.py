import re

def parse_xfr(path):

    xfr_map = {}

    with open(path, "r", encoding="utf-8") as f:
        for line in f:

            line = line.strip()

            # skip basura
            if not line or line.startswith("#"):
                continue

            if "=" not in line:
                continue

            # SAFE SPLIT (IMPORTANTE FIX)
            left, expr = line.split("=", 1)

            left = left.strip()
            expr = expr.strip()

            if "." not in left:
                continue

            node, col = left.split(".", 1)

            node = node.strip()
            col = col.strip()

            if node not in xfr_map:
                xfr_map[node] = {"maps": []}

            xfr_map[node]["maps"].append({
                "col": col,
                "expr": expr
            })

    return xfr_map