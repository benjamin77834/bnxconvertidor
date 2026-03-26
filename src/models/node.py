class Node:

    def __init__(self, name, type_, **kwargs):

        self.name = name
        self.type = type_

        self.inputs = []

        for k, v in kwargs.items():
            setattr(self, k, v)