from pyspark.sql import SparkSession
from pyspark.sql.functions import *
from pyspark.sql.window import Window

spark = SparkSession.builder.appName("BNX_Pipeline").getOrCreate()
spark.sparkContext.setLogLevel("ERROR")

print("[*] BNX PySpark Job Started")

# [+] SOURCE: Input_File
Input_File_df = spark.read.option("header", "true").option("inferSchema", "true").csv("s3://bnx-e2e-test/raw/orders")
print(f"[>] SOURCE: Input_File ({Input_File_df.count()} rows)")

# [-] FILTER: Filter_by_Expression
# next_in_sequence() filter: no-op for structured formats (CSV/parquet with header)
Filter_by_Expression_df = Input_File_df
print(f"[~] FILTER: Filter_by_Expression ({Filter_by_Expression_df.count()} rows)")

# [.] TRANSFORM: Reformat
Reformat_df = Filter_by_Expression_df
Reformat_df = Reformat_df.withColumn("nombre", expr("upper(nombre)"))
print(f"[~] TRANSFORM: Reformat ({Reformat_df.count()} rows)")

# [.] TRANSFORM: Rollup
Rollup_df = Reformat_df.groupBy("nombre").agg(sum("monto").alias("monto"), first("id").alias("id"))
print(f"[~] TRANSFORM: Rollup ({Rollup_df.count()} rows)")

# [*] SINK: Output_File
Rollup_df.select("id", "nombre", "monto").write.mode("overwrite").parquet("s3://bnx-e2e-test/output/spark_output")
print("[>] SINK: Output_File")

# Show results
print("\n--- RESULTADO ---")
Rollup_df.select("id", "nombre", "monto").orderBy("id").show(truncate=False)

spark.stop()
print("[ok] BNX PySpark Job Finished")
