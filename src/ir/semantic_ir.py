class IRNode:

    def __init__(self, id, op_type, inputs=None, attrs=None):

        self.id = id
        self.op_type = op_type
        self.inputs = inputs or []
        self.attrs = attrs or {}