def build_lineage(dag):

    print("? Building lineage...")

    lineage = {}

    schema = dag["schema"]
    mappings = dag["mappings"]

    # base
    for col in schema:
        lineage[f"in.{col}"] = [f"in.{col}"]

    # mappings
    for out_col, in_col in mappings.items():
        lineage[f"out.{out_col}"] = [f"in.{in_col}"]

    return lineage