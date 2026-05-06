"""
🚀 BNX V54 GENERATED GLUE JOB
📅 Generated at: 2026-05-06 16:57:36.565317
"""

from awsglue.context import GlueContext
from pyspark.context import SparkContext
from pyspark.sql.functions import *

sc = SparkContext()
glueContext = GlueContext(sc)
spark = glueContext.spark_session

print("🚀 BNX Glue Job V54 Started")

# =========================
# DAG EXECUTION V54
# =========================

# 🟢 SOURCE: RawOrders
RawOrders_df = spark.read.format("csv").option("header", "true").option("inferSchema", "true").load("s3://bnx-e2e-test/raw/orders")
print("📂 SOURCE: RawOrders")

# 🟢 SOURCE: RawCustomers
RawCustomers_df = spark.read.format("csv").option("header", "true").option("inferSchema", "true").load("s3://bnx-e2e-test/raw/customers")
print("📂 SOURCE: RawCustomers")

# 🔹 TRANSFORM: CleanOrders
CleanOrders_df = RawOrders_df.selectExpr("order_id", "customer_id", "amount", "status", "order_date").where("status = 'completed'")
print("🔄 TRANSFORM: CleanOrders")

# 🔗 JOIN: OrderJoin
OrderJoin_df = RawCustomers_df.join(CleanOrders_df, on="customer_id", how="inner")
print("🔗 JOIN: OrderJoin")

# 🔹 TRANSFORM: TotalSpend
TotalSpend_df = OrderJoin_df.groupBy("customer_id", "name", "region").agg(sum("amount").alias("total_spent"), count("order_id").alias("order_count"))
print("🔄 TRANSFORM: TotalSpend")

# 🏁 SINK: WriteReport
TotalSpend_df.write.mode("overwrite").format("parquet").save("s3://bnx-e2e-test/output/report")
print("💾 SINK: WriteReport")

print("✅ BNX Glue Job V54 Finished")
