def parse_expr(expr_dict):

    cols = []

    for k, v in expr_dict.items():

        if not v:
            continue

        cols.append(f"{v} as {k}")

    return cols