from src.vm.operators.base import VMOperator


class OutputOp(VMOperator):

    def execute(self, instr, ctx):

        parent = ctx.stack[instr.inputs[0]]
        path = instr.attrs["path"]

        ctx.code.append(
            f'{parent}.write.mode("overwrite").parquet("{path}")'
        )