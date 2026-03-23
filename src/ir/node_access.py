def get_id(n):
    return n["id"] if isinstance(n, dict) else n.id


def get_type(n):
    return n["type"] if isinstance(n, dict) else n.type


def get_inputs(n):
    return n["inputs"] if isinstance(n, dict) else n.inputs


def get_attrs(n):
    return n["attrs"] if isinstance(n, dict) else n.attrs


# =========================
# SAFE OPTIONAL FIELDS
# =========================

def get_expr(n):
    if isinstance(n, dict):
        return n.get("expr", [])
    return getattr(n, "expr", []) or []


def get_safe_attrs(n):
    if isinstance(n, dict):
        return n
    return getattr(n, "attrs", {}) or {}