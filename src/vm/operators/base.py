class VMOperator:
    def execute(self, instr, ctx):
        raise NotImplementedError("VMOperator must implement execute()")