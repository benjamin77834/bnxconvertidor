import re
from src.xfr.ast import XFRNode


class XFRParser:

    def parse(self, expr: str):

        expr = expr.strip()

        # CASE WHEN
        if expr.upper().startswith("CASE"):
            return self._parse_case(expr)

        # FUNCTION CALL
        match = re.match(r"(\w+)\((.*)\)", expr)
        if match:
            func = match.group(1)
            args = match.group(2).split(",")
            return XFRNode(
                type="FUNC",
                value=func,
                left=self.parse(args[0]) if args else None
            )

        # FIELD or CONST
        return XFRNode(type="FIELD", value=expr)

    def _parse_case(self, expr):
        return XFRNode(type="CASE", value=expr)