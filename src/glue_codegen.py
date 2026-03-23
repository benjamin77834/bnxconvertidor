def generate_glue(dag, order):

    code = []

    code.append("from pyspark.sql import SparkSession")
    code.append("from pyspark.sql import functions as F\n")
    code.append('spark = SparkSession.builder.appName("ENTERPRISE_GLUE").getOrCreate()\n')

    dfs = {}

    for node_id in order:

        node = dag.nodes[node_id]
        ntype = node.type

        # =====================
        # INPUT
        # =====================
        if ntype == "input":

            df = node_id.lower()

            code.append(
                f'{df} = spark.read.parquet("s3://input/{df}")'
            )

            dfs[node_id] = df

        # =====================
        # JOIN (ENTERPRISE READY)
        # =====================
        elif ntype == "join":

            parents = list(dfs.values())

            left = parents[0]
            right = parents[1]

            keys = node.attrs.get("keys", ["id"])

            df = node_id.lower()

            code.append(
                f'{df} = {left}.join({right}, {keys})'
            )

            dfs[node_id] = df

        # =====================
        # OUTPUT
        # =====================
        elif ntype == "output":

            last = list(dfs.values())[-1]

            code.append(
                f'{last}.write.mode("overwrite").parquet("s3://output/final")'
            )

    return "\n".join(code)