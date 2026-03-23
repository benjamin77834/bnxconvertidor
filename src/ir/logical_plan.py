class LogicalNode:
    def __init__(self, id, op_type, inputs=None, attrs=None):
        self.id = id
        self.type = op_type
        self.inputs = inputs or []
        self.attrs = attrs or {}

    def __repr__(self):
        return f"LogicalNode(id={self.id}, type={self.type}, inputs={self.inputs}, attrs={self.attrs})"