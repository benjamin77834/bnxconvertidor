from src.vm.operators.base import VMOperator


class JoinOp(VMOperator):

    def execute(self, instr, ctx):

        left = ctx.stack[instr.inputs[0]]
        right = ctx.stack[instr.inputs[1]]

        keys = instr.attrs.get("keys", ["id"])

        df = instr.id.lower()

        ctx.code.append(
            f"{df} = {left}.join({right}, {keys})"
        )

        ctx.stack[instr.id] = df