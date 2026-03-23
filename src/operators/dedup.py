class DedupOp:

    def compile(self, node):

        src = node.inputs[0]
        keys = node.attrs.get("keys", ["id"])
        key_str = ", ".join([f"'{k}'" for k in keys])

        return f"""
df_{node.id} = df_{src}.dropDuplicates([{key_str}])
"""