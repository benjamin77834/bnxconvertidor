import re

def parse_xfr(path):

    with open(path) as f:
        content = f.read()

    transforms = {}

    current = None

    for line in content.splitlines():

        line = line.strip()

        if line.startswith("TRANSFORM"):
            current = line.split()[1]
            transforms[current] = {"maps": [], "filters": []}

        elif "=" in line and current:
            left, right = line.split("=")
            transforms[current]["maps"].append((left.strip(), right.strip()))

        elif line.startswith("FILTER") and current:
            transforms[current]["filters"].append(line.replace("FILTER", "").strip())

    return transforms