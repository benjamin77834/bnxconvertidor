# engine_v2.py

from dag_builder import build_dag


def compile_graph(mp, xfr, dml):
    dag = build_dag(mp, xfr, dml)

    order = dag.topological_sort()

    code = []
    lineage = {}

    code.append("from pyspark.sql import SparkSession\nspark = SparkSession.builder.getOrCreate()\n")

    for node_id in order:
        node = dag.nodes[node_id]

        if node.type == "source":
            code.append(f"{node_id} = spark.read.table('input_{node_id.lower()}')")

        elif node.type == "transform":
            code.append(f"{node_id} = {node.inputs[0]}  # transform placeholder")

        elif node.type == "join":
            left, right = node.inputs
            key = node.config.get("key", "id")
            code.append(f"{node_id} = {left}.join({right}, '{key}', 'inner')")

        elif node.type == "sink":
            src = node.inputs[0]
            code.append(f"{node_id} = {src}")
            code.append(f"{node_id}.write.mode('overwrite').saveAsTable('output_{node_id.lower()}')")

    # LINEAGE GRAPH
    for node_id in dag.nodes:
        node = dag.nodes[node_id]
        lineage[node_id] = node.inputs

    return "\n".join(code), lineage