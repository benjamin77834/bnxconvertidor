class Node:

    def __init__(self, id, type, inputs=None, expr=None):

        self.id = id
        self.type = type
        self.inputs = inputs or []
        self.expr = expr or {}