from src.vm.operators.base import VMOperator


class InputOp(VMOperator):

    def execute(self, instr, ctx):

        df = instr.id.lower()
        path = instr.attrs["path"]

        ctx.code.append(
            f'{df} = spark.read.parquet("{path}")'
        )

        ctx.stack[instr.id] = df