from dag.builder import build_dag
from parsers.xfr_parser import parse_xfr
from compiler.transformer import apply_transform
from compiler.lineage import build_lineage


def compile_graph(mp, xfr, dml):

    dag = build_dag(mp)
    xfr_rules = parse_xfr(xfr)

    order = dag.topo_sort()

    code = []
    code.append("from pyspark.sql import SparkSession")
    code.append("from pyspark.sql.functions import *")
    code.append("spark = SparkSession.builder.getOrCreate()\n")

    print("\n🧬 EXECUTION PLAN:")

    for node_id in order:
        node = dag.nodes[node_id]

        print("NODE:", node_id)

        # SOURCE
        if node.type == "source":
            code.append(f"{node_id} = spark.read.table('input_{node_id.lower()}')")

        # TRANSFORM
        elif node.type == "transform":
            src = node.inputs[0]

            rule = xfr_rules.get(node_id.strip().lower())

            if rule:
                print(f"✔ XFR (advanced): {node_id}")
                code.append(apply_transform(node_id, src, rule))
            else:
                print(f"❌ NO XFR: {node_id}")
                code.append(f"{node_id} = {src}")

        # JOIN
        elif node.type == "join":
            l, r = node.inputs
            code.append(f"{node_id} = {l}.join({r}, 'id', 'inner')")

        # SINK
        elif node.type == "sink":
            src = node.inputs[0]
            code.append(f"{node_id} = {src}")
            code.append(
                f"{node_id}.write.mode('overwrite').saveAsTable('output_{node_id.lower()}')"
            )

    lineage = build_lineage(dag)

    print("\n🧬 FINAL LINEAGE:")
    for k, v in lineage.items():
        print(k, "<-", v)

    return "\n".join(code), lineage