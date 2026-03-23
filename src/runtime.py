def get_inputs(plan, node_id):
    return [
        src for src, dsts in plan.edges.items()
        if node_id in dsts
    ]