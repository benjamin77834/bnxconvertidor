from core.dag import DAG

def build_dag(mp, xfr, dml):
    dag = DAG()

    dag.add_node("Customers", "source")
    dag.add_node("Transactions", "source")

    dag.add_node("CleanCustomers", "transform")
    dag.add_node("FilterTx", "transform")

    dag.add_node("Join1", "join")
    dag.add_node("FINAL", "sink")

    dag.add_edge("Customers", "CleanCustomers")
    dag.add_edge("Transactions", "FilterTx")

    dag.add_edge("CleanCustomers", "Join1")
    dag.add_edge("FilterTx", "Join1")

    dag.add_edge("Join1", "FINAL")

    return dag