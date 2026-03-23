def build_dag(ast_nodes):

    dag = {}
    lookup = {n.name: n for n in ast_nodes}

    for node in ast_nodes:
        dag[node.name] = {
            "node": node,
            "inputs": node.inputs
        }

    return dag