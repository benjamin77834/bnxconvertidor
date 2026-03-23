from .base import Operator


class InputOperator(Operator):

    def execute(self, node, inputs, ctx):

        df = node.id.lower()
        path = node.attrs["path"]

        ctx.code.append(
            f'{df} = spark.read.parquet("{path}")'
        )

        ctx.dfs[node.id] = df