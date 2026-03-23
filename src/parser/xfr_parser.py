import re


class XFRParser:

    def parse_expr(self, expr):

        expr = expr.strip()

        # CASE WHEN simple
        if "CASE WHEN" in expr:

            cond = re.search(r'CASE WHEN (.*?) THEN', expr)
            then_val = re.search(r'THEN (.*?) ELSE', expr)
            else_val = re.search(r'ELSE (.*?) END', expr)

            return {
                "type": "case_when",
                "condition": cond.group(1) if cond else "",
                "then": then_val.group(1) if then_val else "",
                "else": else_val.group(1) if else_val else ""
            }

        return {"type": "expr", "value": expr}


    def parse(self, file_path):

        with open(file_path) as f:
            lines = f.readlines()

        expressions = []

        for line in lines:
            if "=" in line:
                expressions.append(line.strip())

        return expressions