import re


def parse_xfr(path):

    xfr = {}
    current = None

    with open(path, "r", encoding="utf-8", errors="replace") as f:
        lines = f.readlines()

    for line in lines:
        line = line.strip()

        if not line:
            continue

        # Detect transform block
        if line.startswith("Reformat"):
            current = line
            xfr[current] = {
                "name": current,
                "input": None,
                "rules": [],
                "filter": None
            }

        # input
        elif line.startswith("input:"):
            xfr[current]["input"] = line.split("input:")[1].strip()

        # filter
        elif line.startswith("filter:"):
            xfr[current]["filter"] = line.split("filter:")[1].strip()

        # rule mapping
        elif "out:" in line and "expr:" in line:

            parts = line.split("expr:")

            left = parts[0].replace("out:", "").strip()
            right = parts[1].strip()

            xfr[current]["rules"].append({
                "out": left,
                "expr": right
            })

    return xfr