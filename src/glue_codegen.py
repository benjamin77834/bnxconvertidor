def generate_glue(ir):

    code = []

    code.append("from pyspark.sql import SparkSession")
    code.append("from pyspark.sql.functions import *")
    code.append("")
    code.append("spark = SparkSession.builder.getOrCreate()")
    code.append("")

    for node in ir:

        if node["type"] == "source":
            code.append(f'{node["id"]} = spark.read.table("{node["id"]}")')

        elif node["type"] == "aggregate":
            code.append("""
rollup_household = customers.groupBy("customer_id") \\
    .agg(count("*").alias("cnt"))
""".strip())

        elif node["type"] == "map":
            for expr in node["expressions"]:
                if expr["op"] == "concat":
                    code.append("""
reformat_consumer = consumerinfo.withColumn(
    "full_name",
    concat(col("first_name"), lit(" "), col("last_name"))
)
""".strip())

        elif node["type"] == "join":
            code.append("""
join_final = rollup_household \\
    .join(transactions2, "customer_id") \\
    .join(reformat_consumer, "customer_id")
""".strip())

        elif node["type"] == "sink":
            code.append("""
join_final.write.mode("overwrite") \\
    .saveAsTable("select_output")
""".strip())

    return "\n".join(code)
