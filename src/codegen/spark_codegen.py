from collections import defaultdict, deque

def generate_glue(nodes, edges, output_path):

    print("⚙️ CODEGEN START (BNX V9)")

    code = []
    code.append("from pyspark.sql import SparkSession")
    code.append("from pyspark.sql.functions import *")
    code.append("")
    code.append("spark = SparkSession.builder.appName('BNX_V9').getOrCreate()")
    code.append("")

    # -------------------------
    # GRAPH BUILD
    # -------------------------
    graph = defaultdict(list)
    indegree = {n: 0 for n in nodes}

    for src, dst in edges:
        graph[src].append(dst)
        indegree[dst] += 1

    # -------------------------
    # TOPO SORT
    # -------------------------
    q = deque([n for n in nodes if indegree[n] == 0])
    order = []

    while q:
        n = q.popleft()
        order.append(n)

        for nxt in graph[n]:
            indegree[nxt] -= 1
            if indegree[nxt] == 0:
                q.append(nxt)

    # -------------------------
    # EXECUTION BUILD
    # -------------------------
    resolved = {}

    for node in order:
        obj = nodes[node]

        if obj.type == "input":
            expr = f"spark.read.parquet('{node}.parquet')"

        elif obj.type == "transform":
            parent = obj.inputs[0]
            expr = f"{resolved[parent]}.select('*')"

        elif obj.type == "join":
            left = obj.inputs[0]
            right = obj.inputs[1]
            expr = f"{resolved[left]}.join({resolved[right]}, 'id', 'inner')"

        else:
            expr = "None"

        resolved[node] = expr

    # -------------------------
    # EMIT CODE
    # -------------------------
    for node in order:
        code.append(f"{node} = {resolved[node]}")

    code.append("\n# BNX V9 PIPELINE COMPLETE")

    with open(output_path, "w") as f:
        f.write("\n".join(code))

    print("🔥 CODEGEN DONE:", output_path)