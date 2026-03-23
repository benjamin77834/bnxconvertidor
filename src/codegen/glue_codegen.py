def generate_glue(dag, output_path):

    lines = []
    lines.append("from pyspark.sql import SparkSession\n")
    lines.append("spark = SparkSession.builder.appName('BNX').getOrCreate()\n\n")

    nodes = dag

    for name, data in nodes.items():

        node = data["node"]

        if node.type == "input":
            path = node.props.get("path")
            lines.append(f"{name} = spark.read.parquet('{path}')\n")

        elif node.type == "join":

            if len(node.inputs) < 2:
                continue

            left, right = node.inputs[:2]
            key = node.props.get("keys", "id")

            lines.append(f"{name} = {left}.join({right}, '{key}')\n")

        elif node.type == "output":

            inp = node.inputs[0] if node.inputs else None
            path = node.props.get("path", "s3://output")

            if inp:
                lines.append(f"{inp}.write.mode('overwrite').parquet('{path}')\n")

    with open(output_path, "w") as f:
        f.writelines(lines)

    print(f"🔥 Glue job generated: {output_path}")