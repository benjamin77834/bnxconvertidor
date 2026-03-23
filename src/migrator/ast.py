import re


class ASTNode:
    def __init__(self, op, args=None):
        self.op = op
        self.args = args or []


def parse_xfr(expr):
    """
    Minimal SQL/XFR parser:
    supports:
    - UPPER(col)
    - LOWER(col)
    - CASE WHEN
    - col expressions
    """

    expr = expr.strip()

    # UPPER
    if expr.startswith("UPPER"):
        col = re.findall(r"\((.*?)\)", expr)[0]
        return ASTNode("UPPER", [col])

    # LOWER
    if expr.startswith("LOWER"):
        col = re.findall(r"\((.*?)\)", expr)[0]
        return ASTNode("LOWER", [col])

    # CASE WHEN (very simplified)
    if "CASE" in expr:
        return ASTNode("CASE", [expr])

    # direct column
    return ASTNode("COL", [expr])