class LookupOp:

    def compile(self, node):

        left, right = node.inputs
        keys = node.attrs["keys"]

        cond = " AND ".join([
            f"df_{left}.{k} == df_{right}.{k}"
            for k in keys
        ])

        return f"""
df_{node.id} = df_{left}.join(df_{right}, {cond}, 'left')
"""