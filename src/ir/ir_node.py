class IRNode:

    def __init__(self, node_id, node_type, attrs=None):
        self.id = node_id
        self.type = node_type
        self.attrs = attrs or {}

    def __repr__(self):
        return f"IRNode(id={self.id}, type={self.type})"