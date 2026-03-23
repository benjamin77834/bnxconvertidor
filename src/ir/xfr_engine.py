class XfrEngine:

    def eval_expr(self, expr, input_alias="df"):

        """
        Convierte XFR simple → Spark expressions
        """

        if expr.startswith("UPPER"):
            col = expr.split("(")[1].replace(")", "")
            return f"upper({input_alias}.{col})"

        if expr.startswith("LOWER"):
            col = expr.split("(")[1].replace(")", "")
            return f"lower({input_alias}.{col})"

        if expr.startswith("TRIM"):
            col = expr.split("(")[1].replace(")", "")
            return f"trim({input_alias}.{col})"

        # fallback
        return expr