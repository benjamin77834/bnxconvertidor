from src.ir.graphir import GraphIR
from src.ir.node import Node

def parse_mp(path):

    ir = GraphIR()

    # 🔹 INPUT NODES
    ir.add_node(Node("RawCustomers", "input"))
    ir.add_node(Node("RawTransactions", "input"))

    # 🔹 TRANSFORMS
    ir.add_node(Node("CleanCustomers", "transform", ["RawCustomers"]))
    ir.add_node(Node("JoinAll", "join", ["CleanCustomers", "RawTransactions"]))
    ir.add_node(Node("Final", "transform", ["JoinAll"]))

    # 🔹 EDGES
    ir.add_edge("RawCustomers", "CleanCustomers")
    ir.add_edge("CleanCustomers", "JoinAll")
    ir.add_edge("RawTransactions", "JoinAll")
    ir.add_edge("JoinAll", "Final")

    return ir