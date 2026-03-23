class PhysicalNode:

    def __init__(self, id, op_type, strategy=None, inputs=None, attrs=None):
        self.id = id
        self.op_type = op_type
        self.strategy = strategy
        self.inputs = inputs or []
        self.attrs = attrs or {}

    def __repr__(self):
        return f"PhysicalNode(id={self.id}, op_type={self.op_type}, strategy={self.strategy}, inputs={self.inputs}, attrs={self.attrs})"