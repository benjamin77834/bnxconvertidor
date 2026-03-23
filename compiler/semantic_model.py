def build_semantic_model(plan, xfr, dml):

    model = {}

    for node in plan:

        nid = node["id"]

        model[nid] = {
            "type": node["type"],
            "xfr": xfr.get(nid, {}),
            "dml": dml
        }

    return model