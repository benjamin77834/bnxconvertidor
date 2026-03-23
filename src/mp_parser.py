from src.ir.graph import GraphIR
from src.ir.node import Node

def parse_mp(path):

    print(f"📦 Parsing Ab Initio graph: {path}")

    ir = GraphIR()

    # demo graph (luego reemplazas por parser real)
    raw = Node("RawCustomers", "input", [])
    tx = Node("RawTransactions", "input", [])

    stage = Node("StageCustomers", "reformat", ["RawCustomers"])
    clean = Node("CleanCustomers", "reformat", ["StageCustomers"])
    valid = Node("ValidCustomers", "filter", ["CleanCustomers"])

    join = Node("JoinAll", "join", ["ValidCustomers", "RawTransactions"])
    final = Node("Final", "reformat", ["JoinAll"])

    for n in [raw, tx, stage, clean, valid, join, final]:
        ir.add_node(n)

    return ir