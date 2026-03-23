from pyspark.sql.functions import *

def generate_glue(plan, semantic):

    lines = []

    lines.append("from pyspark.sql import SparkSession")
    lines.append("from pyspark.sql.functions import *")
    lines.append("spark = SparkSession.builder.getOrCreate()\n")

    for node in plan:

        name = node["id"]
        meta = semantic.get(name, {})

        if node["type"] == "input":
            lines.append(f"{name} = spark.read.table('input_{name.lower()}')")

        elif meta.get("xfr"):

            lines.append(f"# TRANSFORM: {name}")
            lines.append(f"{name} = {apply_transforms(node['id'])}")

        else:
            inputs = node.get("inputs", [])
            if len(inputs) == 1:
                lines.append(f"{name} = {inputs[0]}")
            elif len(inputs) >= 2:
                lines.append(f"{name} = {inputs[0]}.join({inputs[1]}, 'id', 'inner')")

    final = plan[-1]["id"]
    lines.append(f"\nFINAL = {final}")
    lines.append("FINAL.write.mode('overwrite').saveAsTable('output_final')")

    return "\n".join(lines)