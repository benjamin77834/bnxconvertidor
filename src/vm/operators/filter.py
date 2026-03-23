from src.vm.operators.base import VMOperator


class FilterOp(VMOperator):

    def execute(self, instr, ctx):

        parent = ctx.stack[instr.inputs[0]]
        expr = instr.attrs.get("expr", "1=1")

        df = instr.id.lower()

        ctx.code.append(
            f'{df} = {parent}.filter("{expr}")'
        )

        ctx.stack[instr.id] = df