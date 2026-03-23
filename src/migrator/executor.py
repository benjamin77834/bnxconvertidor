from collections import defaultdict
from migrator.dag import topo_sort, find_sinks
from migrator.lineage import LineageGraph
from migrator.optimizer import DAGOptimizer


def generate(ir):

    print("⚙️ BNX v7.1 COMPILER START")

    optimizer = DAGOptimizer(ir.nodes, ir.edges)
    edges = optimizer.prune()
    edges = optimizer.reorder()

    nodes = list(ir.nodes.keys())
    order = topo_sort(nodes, edges)
    sinks = find_sinks(nodes, edges)

    incoming = defaultdict(list)
    outgoing = defaultdict(list)

    for s, d in edges:
        incoming[d].append(s)
        outgoing[s].append(d)

    datasets = {}
    lineage = LineageGraph()

    code = []
    code.append("from pyspark.sql import SparkSession")
    code.append("from pyspark.sql.functions import *\n")
    code.append("spark = SparkSession.builder.getOrCreate()\n")

    # SOURCE NODES
    for node in nodes:
        if len(incoming[node]) == 0:
            datasets[node] = f"spark.read.table('input_{node}')"
            code.append(f"{node} = {datasets[node]}")
            lineage.add(f"{node}.*", f"{node}.*")

    # PROCESS DAG
    for node in order:

        if node in datasets:
            continue

        parents = incoming[node]

        # SINGLE INPUT
        if len(parents) == 1:
            src = parents[0]
            datasets[node] = src
            code.append(f"{node} = {src}")
            lineage.merge(node, [src])

        # MULTI INPUT JOIN
        elif len(parents) > 1:
            base = parents[0]
            expr = base

            for p in parents[1:]:
                expr = f"{expr}.join({p}, 'customer_id', 'left')"

            datasets[node] = expr
            code.append(f"{node} = {expr}")
            lineage.merge(node, parents)

    # SINKS
    for sink in sinks:
        code.append(f"\n{sink}.write.mode('overwrite').saveAsTable('output_{sink}')")

    code.append("\nspark.stop()\n")

    return "\n".join(code), lineage.get()