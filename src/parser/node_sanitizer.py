import re

def normalize_node(name: str) -> str | None:

    if not name:
        return None

    name = name.strip()

    # fix split corruption
    name = re.sub(r"[^A-Za-z0-9_]", "", name)

    if len(name) < 3:
        return None

    # reject fragments
    blacklist = {
        "mers", "mer", "cus", "tx", "acc", "ry"
    }

    if name.lower() in blacklist:
        return None

    return name