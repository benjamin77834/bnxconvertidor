"""
🚀 BNX V54 GENERATED PYSPARK JOB
📅 Generated at: 2026-04-07 21:14:45.886172
"""

from pyspark.sql import SparkSession
from pyspark.sql.functions import *
from pyspark.sql.window import Window

spark = SparkSession.builder.appName("BNX_Pipeline").getOrCreate()

print("🚀 BNX PySpark Job Started")

# 🟢 SOURCE: RawOrders
RawOrders_df = spark.read.parquet("s3a://bnx/raw/raworders")
print("📂 SOURCE: RawOrders")

# 🟢 SOURCE: RawCustomers
RawCustomers_df = spark.read.parquet("s3a://bnx/raw/rawcustomers")
print("📂 SOURCE: RawCustomers")

# 🔹 TRANSFORM: CleanOrders
CleanOrders_df = RawOrders_df.selectExpr("order_id", "customer_id", "amount", "status", "order_date").where("amount > 0 AND status = 'completed'")
print("🔄 TRANSFORM: CleanOrders")

# 🔹 TRANSFORM: CleanCustomers
CleanCustomers_df = RawCustomers_df.selectExpr("customer_id", "name", "email", "region").where("customer_id IS NOT NULL")
print("🔄 TRANSFORM: CleanCustomers")

# 🔗 JOIN: OrdersWithCustomer
OrdersWithCustomer_df = CleanOrders_df.join(CleanCustomers_df, on="customer_id", how="inner")
print("🔗 JOIN: OrdersWithCustomer")

# 🔹 TRANSFORM: TotalByCustomer
TotalByCustomer_df = OrdersWithCustomer_df.groupBy("customer_id", "name", "region").agg(sum("amount").alias("total_spent"), count("order_id").alias("order_count")).where("total_spent > 0")
print("🔄 TRANSFORM: TotalByCustomer")

# 🏁 SINK: WriteReport
TotalByCustomer_df.write.mode("overwrite").parquet("s3a://bnx/output/writereport")
print("💾 SINK: WriteReport")

spark.stop()
print("✅ BNX PySpark Job Finished")
