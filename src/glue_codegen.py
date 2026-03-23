from pyspark.sql import SparkSession
from pyspark.sql.functions import *


def generate_glue(ir, order):

    print("\n⚙️ GENERATING GLUE CODE")

    code = []

    code.append("from pyspark.sql import SparkSession")
    code.append("from pyspark.sql.functions import *\n")
    code.append("spark = SparkSession.builder.appName('BNX').getOrCreate()\n")

    for node_id in order:

        node = ir[node_id]   # ✅ DICT MODE

        t = node.get("type")
        inputs = node.get("inputs", [])

        if t == "input":
            path = node.get("path") or f"s3://data/{node_id}"
            code.append(f"{node_id} = spark.read.parquet('{path}')\n")

        elif t == "filter":
            src = inputs[0] if inputs else "df"
            expr = node.get("expr") or "1=1"
            code.append(f"{node_id} = {src}.filter(\"{expr}\")\n")

        elif t == "join":
            l = inputs[0] if len(inputs) > 0 else "df"
            r = inputs[1] if len(inputs) > 1 else "df"
            keys = node.get("keys") or "id"
            code.append(f"{node_id} = {l}.join({r}, '{keys}')\n")

        elif t == "aggregate":
            src = inputs[0] if inputs else "df"
            gb = node.get("group_by") or "id"
            code.append(f"{node_id} = {src}.groupBy('{gb}').agg(count('*'))\n")

        elif t == "transform":
            src = inputs[0] if inputs else "df"
            code.append(f"{node_id} = {src}.withColumn('flag', lit(1))\n")

        elif t == "output":
            src = inputs[0] if inputs else "df"
            path = node.get("path") or "output/"
            code.append(f"{src}.write.mode('overwrite').parquet('{path}')\n")

        else:
            code.append(f"# UNKNOWN NODE {node_id}\n")

    return "\n".join(code)