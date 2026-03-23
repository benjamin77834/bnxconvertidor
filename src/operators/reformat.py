class ReformatOp:

    def compile(self, node):

        src = node.inputs[0]
        exprs = node.attrs.get("expressions", [])

        spark_exprs = []

        for e in exprs:

            # XFR BASIC TRANSLATION
            e = e.replace("UPPER(", "upper(")
            e = e.replace("LOWER(", "lower(")
            e = e.replace("TRIM(", "trim(")

            spark_exprs.append(e)

        expr_str = ", ".join(spark_exprs)

        return f"""
df_{node.id} = df_{src}.select({expr_str})
"""