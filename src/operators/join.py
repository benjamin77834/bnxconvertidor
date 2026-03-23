class JoinOp:

    def compile(self, node):

        left, right = node.inputs
        key = node.attrs.get("keys", ["id"])[0]

        return f"""
df_{node.id} = df_{left}.join(df_{right}, df_{left}.{key} == df_{right}.{key}, 'inner')
"""