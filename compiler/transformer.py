def apply_transform(node, source, rule):

    select_expr = rule.get("select", "*")
    where_expr = rule.get("where")

    code = f"{node} = {source}.selectExpr(\"{select_expr}\")"

    if where_expr:
        code += f".where(\"{where_expr}\")"

    return code