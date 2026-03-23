from pyspark.sql.functions import col, upper, lower, trim, when


class XFREngine:

    def compile_expr(self, expr):

        expr = expr.strip()

        # BASIC FUNCTIONS
        expr = expr.replace("UPPER(", "upper(")
        expr = expr.replace("LOWER(", "lower(")
        expr = expr.replace("TRIM(", "trim(")

        return expr


    def compile_case_when(self, cond, then_val, else_val):

        return f"when({cond}, {then_val}).otherwise({else_val})"