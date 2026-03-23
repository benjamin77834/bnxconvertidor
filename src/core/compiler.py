def compile_spark(ir):

    nodes = ir["nodes"]
    edges = ir["edges"]
    ast = ir["ast"]

    code = []
    code.append("from pyspark.sql import SparkSession")
    code.append("spark = SparkSession.builder.getOrCreate()\n")

    # SOURCES
    for n, meta in nodes.items():
        if meta["type"] == "source":
            code.append(f"{n} = spark.read.table('input_{n}')")

    code.append("")

    # 🔥 REAL JOIN LOGIC
    if ast["joins"]:

        left = ast["from"]

        expr = left

        for j in ast["joins"]:
            expr = f"{expr}.join({j}, 'id', 'inner')"

        code.append(f"FINAL = {expr}")

    else:
        code.append(f"FINAL = {ast['from']}")

    code.append("\nFINAL.write.mode('overwrite').saveAsTable('output_FINAL')")
    code.append("spark.stop()")

    return "\n".join(code)
