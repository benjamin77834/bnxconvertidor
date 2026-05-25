from collections import defaultdict, deque


# ----------------------------
# TOPO SORT
# ----------------------------
def topo_sort(nodes, edges):
    indegree = defaultdict(int)
    graph = defaultdict(list)

    for s, d in edges:
        graph[s].append(d)
        indegree[d] += 1
        indegree.setdefault(s, 0)

    q = deque([n for n in nodes if indegree[n] == 0])
    order = []

    while q:
        n = q.popleft()
        order.append(n)
        for nei in graph[n]:
            indegree[nei] -= 1
            if indegree[nei] == 0:
                q.append(nei)

    return order


# ----------------------------
# JOIN KEY INFERENCE
# ----------------------------
def infer_join_key(left_schema, right_schema):
    if not left_schema or not right_schema:
        return "customer_id"

    for k in ["customer_id", "id", "cust_id"]:
        if k in left_schema and k in right_schema:
            return k

    return "customer_id"


# ----------------------------
# CODEGEN V5 (FIXED RETURN)
# ----------------------------
def generate_glue_job(ir_graph):
    print("?? BNX v5 DAG Compiler running...")

    nodes = list(ir_graph.nodes.keys())
    edges = ir_graph.edges

    order = topo_sort(nodes, edges)

    incoming = defaultdict(list)
    outgoing = defaultdict(list)

    for s, d in edges:
        incoming[d].append(s)
        outgoing[s].append(d)

    code = []
    code.append("from pyspark.sql import SparkSession")
    code.append("from pyspark.sql.functions import *\n")
    code.append("spark = SparkSession.builder.getOrCreate()\n")

    datasets = {}
    lineage = defaultdict(list)

    # ----------------------------
    # EXECUTION
    # ----------------------------
    for node in order:

        meta = ir_graph.nodes.get(node, {})
        node_type = meta.get("type")
        schema = meta.get("schema", {})
        transform = meta.get("transform")

        # SOURCE
        if node_type == "source" or node not in incoming:
            datasets[node] = f"spark.read.table('input_{node}')"
            lineage[node] = [node]
            code.append(f"{node} = {datasets[node]}")
            continue

        sources = incoming[node]

        # SINGLE INPUT
        if len(sources) == 1:
            src = sources[0]
            datasets[node] = datasets.get(src, src)
            lineage[node] = lineage.get(src, [src])

            expr = datasets[node]

            if transform:
                expr = f"{expr}  # xfr applied: {transform.get('type','generic')}"

            code.append(f"{node} = {expr}")

        # MULTI INPUT (JOIN)
        else:
            base = sources[0]
            expr = datasets.get(base, base)

            lineage[node] = []

            code.append(f"{node} = {expr}")

            for s in sources[1:]:
                right = datasets.get(s, s)

                left_schema = ir_graph.nodes.get(base, {}).get("schema", {})
                right_schema = ir_graph.nodes.get(s, {}).get("schema", {})

                join_key = infer_join_key(left_schema, right_schema)

                expr = f"{node}.join({right}, '{join_key}', 'left')"

                code.append(f"{node} = {expr}")

                lineage[node].extend(lineage.get(s, []))

            datasets[node] = node

    # ----------------------------
    # SINK DETECTION
    # ----------------------------
    sinks = [n for n in nodes if n not in outgoing]
    sink = sinks[0] if sinks else order[-1]

    code.append(f"\n{sink}.write.mode('overwrite').saveAsTable('output_{sink}')")
    code.append("\nspark.stop()\n")

    # [ok] FIX PRINCIPAL (3 RETURNS ALWAYS)
    return "\n".join(code), sink, dict(lineage)