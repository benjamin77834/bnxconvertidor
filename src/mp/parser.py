from src.ir.node import Node

def parse_mp(path):

    # demo graph (Ab Initio style)
    nodes = {
        "RawCustomers": Node("RawCustomers", "input"),
        "RawTransactions": Node("RawTransactions", "input"),

        "CleanCustomers": Node(
            "CleanCustomers",
            "transform",
            inputs=["RawCustomers"],
            expr={"name": "upper(name)"}
        ),

        "JoinAll": Node(
            "JoinAll",
            "join",
            inputs=["CleanCustomers", "RawTransactions"]
        ),

        "Final": Node(
            "Final",
            "transform",
            inputs=["JoinAll"],
            expr={"customer_id": "id"}
        )
    }

    edges = [
        ("RawCustomers", "CleanCustomers"),
        ("CleanCustomers", "JoinAll"),
        ("RawTransactions", "JoinAll"),
        ("JoinAll", "Final")
    ]

    return nodes, edges