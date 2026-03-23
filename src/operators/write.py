class WriteOp:

    def compile(self, node):

        src = node.inputs[0]
        path = node.attrs.get("path")

        return f"""
df_{src}.write.mode('overwrite').parquet('{path}')
"""