class Node:
    def __init__(self, id, type, inputs=None):
        self.id = id
        self.type = type
        self.inputs = inputs or []