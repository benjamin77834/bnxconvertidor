from .base import Operator


class OutputOperator(Operator):

    def execute(self, node, inputs, ctx):

        parent = ctx.dfs[inputs[0]]
        path = node.attrs["path"]

        ctx.code.append(
            f'{parent}.write.mode("overwrite").parquet("{path}")'
        )