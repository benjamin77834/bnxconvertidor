class FilterOp:

    def compile(self, node):

        src = node.inputs[0]
        cond = node.attrs.get("condition")

        return f"""
df_{node.id} = df_{src}.filter({cond})
"""