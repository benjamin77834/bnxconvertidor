from src.plan import LogicalPlan, LogicalNode


def build_ir(project_path):

    print("\n🧠 Building Logical Plan...")

    plan = LogicalPlan()

    plan.add_node(LogicalNode("Customers", "input", {
        "path": f"{project_path}/customers"
    }))

    plan.add_node(LogicalNode("Transactions", "input", {
        "path": f"{project_path}/transactions"
    }))

    plan.add_node(LogicalNode("Join", "join", {
        "keys": ["id"]
    }))

    plan.add_node(LogicalNode("Output", "output", {
        "path": "s3://output/final"
    }))

    plan.add_edge("Customers", "Join")
    plan.add_edge("Transactions", "Join")
    plan.add_edge("Join", "Output")

    return plan