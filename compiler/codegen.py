def generate_glue(plan, lineage):
    lines = []
    lines.append("from pyspark.sql import SparkSession")
    lines.append("from pyspark.sql.functions import *")
    lines.append("spark = SparkSession.builder.getOrCreate()\n")

    created = set()

    for node in plan:
        name = node["id"]

        inputs = lineage.get(name, [])

        if len(inputs) == 0:
            lines.append(f"{name} = spark.read.table('input_{name.lower()}')")
        elif len(inputs) == 1:
            lines.append(f"{name} = {inputs[0]}")
        elif len(inputs) == 2:
            lines.append(f"{name} = {inputs[0]}.join({inputs[1]}, 'id', 'inner')")
        else:
            lines.append(f"{name} = None  # complex transform")

        created.add(name)

    final = plan[-1]["id"]
    lines.append(f"\nFINAL = {final}")
    lines.append("FINAL.write.mode('overwrite').saveAsTable('output_final')")

    return "\n".join(lines)