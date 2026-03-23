def build_dag(project_path):

    nodes = [
        {"id": "Customers", "type": "input"},
        {"id": "Transactions", "type": "input"},

        # 🔥 ahora es declarativo
        {"id": "Join", "type": "join", "keys": ["id"]},

        {"id": "Output", "type": "output"},
    ]

    edges = [
        ("Customers", "Join"),
        ("Transactions", "Join"),
        ("Join", "Output"),
    ]

    return nodes, edges