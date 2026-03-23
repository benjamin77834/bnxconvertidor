def generate_spark(dag):
    return """
from pyspark.sql import SparkSession
spark = SparkSession.builder.getOrCreate()

customers = spark.read.table("input_customers")
transactions = spark.read.table("input_transactions")

FINAL = customers.join(transactions, "id", "inner")

FINAL.write.mode("overwrite").saveAsTable("output_final")

spark.stop()
"""