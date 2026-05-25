import pandas as pd


def run_engine(plan, xfr):

    data_store = {}

    print("\n[*] EXECUTING DATA PIPELINE\n")

    for node in plan:

        node_id = node["id"]

        print(f"[>] Running: {node_id}")

        # ? INPUT NODES (mock data)
        if node["type"] == "input":

            data_store[node_id] = pd.DataFrame([
                {"id": 1, "name": "demo", "amount": 100}
            ])

        # ? TRANSFORM NODES
        else:

            # buscar XFR asociado
            for tname, spec in xfr.items():

                if spec["input"] == node_id:

                    df = data_store.get(node_id)

                    if df is None:
                        df = pd.DataFrame()

                    # aplicar reglas simuladas
                    for rule in spec.get("rules", []):

                        col = rule["out"]

                        expr = rule["expr"]

                        df[col] = f"eval({expr})"

                    data_store[node_id] = df

        print(f"? Done: {node_id}")

    return data_store