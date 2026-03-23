import re

def normalize(s):
    return s.strip().lower()


def parse_xfr(path):
    with open(path, "r") as f:
        lines = f.readlines()

    rules = {}
    current = None
    buffer = []

    for line in lines:
        line = line.strip()

        if not line:
            continue

        if ":" in line:
            if current:
                rules[current] = "\n".join(buffer)

            current = normalize(line.split(":")[0])
            buffer = []
        else:
            buffer.append(line)

    if current:
        rules[current] = "\n".join(buffer)

    parsed = {}

    for node, body in rules.items():

        select = re.search(r"select\s+(.*?)\s*(where|$)", body, re.I | re.S)
        where = re.search(r"where\s+(.*)", body, re.I | re.S)

        parsed[node] = {
            "select": select.group(1).strip() if select else "*",
            "where": where.group(1).strip() if where else None
        }

    return parsed