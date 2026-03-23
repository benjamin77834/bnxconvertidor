class RollupOp:

    def compile(self, node):

        src = node.inputs[0]
        keys = node.attrs.get("group_by", [])
        aggs = node.attrs.get("aggs", [])

        group = ", ".join([f"'{k}'" for k in keys])

        agg_expr = ", ".join([
            f"{a['func']}('{a['col']}').alias('{a['alias']}')"
            for a in aggs
        ])

        return f"""
df_{node.id} = df_{src}.groupBy({group}).agg({agg_expr})
"""