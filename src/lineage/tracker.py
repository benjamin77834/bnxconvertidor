def build_lineage(dag):

    lineage = {}

    for name, data in dag.items():

        node = data["node"]

        for inp in node.inputs:

            if inp not in lineage:
                lineage[inp] = []

            lineage[inp].append(name)

    print("\n🧬 LINEAGE MAP:")
    for k, v in lineage.items():
        print(f"{k} → {v}")

    return lineage