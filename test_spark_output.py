"""
Test del código generado por BNX codegen (target=spark)
Adaptado para correr local con CSV en vez de S3/parquet
"""
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
#Filter_by_Expression_df = Input_File_df.withColumn("_seq", monotonically_increasing_id() + 1)

####Filter_by_Expression_df.coalesce(1).write.mode("overwrite").option("header", "true").csv("s3://bnx-e2e-test/output/spark_output2")
Filter_by_Expression_df =Input_File_df 

#Filter_by_Expression_df = Filter_by_Expression_df.where("_seq > 1").drop("_seq")
print(f"[~] FILTER: Filter_by_Expression ({Filter_by_Expression_df.count()} rows)")

# [.] TRANSFORM: Reformat
Reformat_df = Filter_by_Expression_df.selectExpr("*")
print(f"[~] TRANSFORM: Reformat ({Reformat_df.count()} rows)")

# [.] TRANSFORM: Rollup
Rollup_df = Reformat_df.groupBy("nombre", "id").agg(sum("monto").alias("monto"))
#Rollup_df = Reformat_df.groupBy("nombre").agg(sum("monto").alias("monto"))

print(f"[~] TRANSFORM: Rollup ({Rollup_df.count()} rows)")

# [*] SINK: Output_File
Rollup_df.coalesce(1).write.mode("overwrite").option("header", "false").csv("s3://bnx-e2e-test/output/spark_output")
print("[>] SINK: Output_File")

# Show results
print("\n--- RESULTADO ---")
Rollup_df.orderBy("id").show(truncate=False)

spark.stop()
print("[ok] BNX PySpark Job Finished")
