from typing import Dict, List
from src.ir.node import Node

class GraphIR:

    def __init__(self):
        self.nodes: Dict[str, Node] = {}

    def add_node(self, node: Node):
        self.nodes[node.id] = node

    def get(self, node_id: str):
        return self.nodes.get(node_id)

    def items(self):
        return self.nodes.items()