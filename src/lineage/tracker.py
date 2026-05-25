def build_lineage(nodes, edges):

    print("? LINEAGE TRACE")

    lineage = {}

    # [ok] correcto: src -> dst
    for src, dst in edges:

        if dst not in lineage:
            lineage[dst] = []

        lineage[dst].append(src)

    for k, v in lineage.items():
        print(f"[~] {k} <- {v}")

    return lineage