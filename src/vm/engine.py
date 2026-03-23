from src.vm.operators.registry import VM_OPERATORS
from src.vm.context import VMContext


class GraphVM:

    def run(self, instructions):

        ctx = VMContext()

        for instr in instructions:

            op = VM_OPERATORS.get(instr.op_type)

            if not op:
                raise Exception(f"Unknown op: {instr.op_type}")

            op.execute(instr, ctx)

        return ctx