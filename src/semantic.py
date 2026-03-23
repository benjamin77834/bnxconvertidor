def build_semantic_model(plan, xfr, dml):

    model = {}

    for n in plan:

        model[n["id"]] = {
            "type": n["type"],
            "inputs": n.get("inputs", []),
            "xfr": xfr.get(n["id"], {}),
            "dml": dml
        }

    return model