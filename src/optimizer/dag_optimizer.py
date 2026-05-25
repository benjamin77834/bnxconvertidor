def validate_join_inputs(dag):

    for node in dag.nodes.values():

        if node.op == "join":

            if not node.inputs or len(node.inputs) < 2:
                raise Exception(f"[JOIN INVALID] {node.name}")

            if len(node.inputs) > 2:
                print(f"[WARN] {node.name} multi-input join ? collapsing to binary model")

    return dag


def optimize_dag(dag):

    print("\n? BNX OPTIMIZER START")

    dag = validate_join_inputs(dag)

    print("? BNX OPTIMIZER END\n")

    return dag