from collections import defaultdict, deque
from migrator.lineage import LineageTracker
from migrator.optimizer import DAGOptimizer


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
def infer_join_key():
    return "customer_id"


# ----------------------------
# V6 CODEGEN
# ----------------------------
def generate_glue_job(ir_graph):

    print("⚙️ BNX v6 Enterprise Optimizer running...")

    # ----------------------------
    # OPTIMIZER STEP
    # ----------------------------
    optimizer = DAGOptimizer(ir_graph.nodes, ir_graph.edges)
    optimizer.prune_passthrough()
    optimizer.fuse_linear_chains()

    nodes = list(ir_graph.nodes.keys())
    edges = optimizer.edges

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
    lineage = LineageTracker()

    # ----------------------------
    # EXECUTION ENGINE
    # ----------------------------
    for node in order:

        meta = ir_graph.nodes.get(node, {})
        node_type = meta.get("type")
        transform = meta.get("transform")

        # --------------------
        # SOURCE
        # --------------------
        if node_type == "source" or node not in incoming:
            datasets[node] = f"spark.read.table('input_{node}')"
            lineage.add_source(node)
            code.append(f"{node} = {datasets[node]}")
            continue

        sources = incoming[node]

        # --------------------
        # SINGLE INPUT
        # --------------------
        if len(sources) == 1:
            src = sources[0]
            datasets[node] = datasets.get(src, src)

            code.append(f"{node} = {datasets[node]}")

            # LINEAGE PROPAGATION
            lineage.merge(node, [src])

        # --------------------
        # JOIN
        # --------------------
        else:
            base = sources[0]
            expr = datasets.get(base, base)

            code.append(f"{node} = {expr}")

            for s in sources[1:]:
                right = datasets.get(s, s)

                join_key = infer_join_key()

                expr = f"{node}.join({right}, '{join_key}', 'left')"

                code.append(f"{node} = {expr}")

                lineage.merge(node, [base, s])

            datasets[node] = node

        # --------------------
        # TRANSFORM (XFR HOOK)
        # --------------------
        if transform:
            code.append(f"# XFR applied on {node}: {transform.get('type','generic')}")

    # ----------------------------
    # SINK DETECTION
    # ----------------------------
    sinks = [n for n in nodes if n not in outgoing]
    sink = sinks[0] if sinks else order[-1]

    code.append(f"\n{sink}.write.mode('overwrite').saveAsTable('output_{sink}')")
    code.append("\nspark.stop()\n")

    return "\n".join(code), sink, lineage.get()