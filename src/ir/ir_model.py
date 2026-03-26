class Node:
    def __init__(self, name, op_type="pass", attrs=None):
        self.name = name
        self.op_type = op_type   # source, transform, join, agg, sink
        self.attrs = attrs or {}

class Edge:
    def __init__(self, src, dst):
        self.src = src
        self.dst = dst