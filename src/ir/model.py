# src/ir/model.py

class Node:
    def __init__(self, id, type, inputs=None, props=None):
        self.id = id
        self.type = type
        self.inputs = inputs or []
        self.props = props or {}

    def __repr__(self):
        return f"Node({self.id}, {self.type})"