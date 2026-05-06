"""
🚀 BNX V54 GENERATED PYSPARK JOB
📅 Generated at: 2026-05-06 16:47:58.909726
"""

from pyspark.sql import SparkSession
from pyspark.sql.functions import *
from pyspark.sql.window import Window

spark = SparkSession.builder.appName("BNX_Pipeline").getOrCreate()

print("🚀 BNX PySpark Job Started")

# 🟢 SOURCE: ScanTransactions
ScanTransactions_df = spark.read.parquet("s3://datalake/raw/transactions")
ScanTransactions_df = ScanTransactions_df.where("year = 2026 AND month = 10")
print("📂 SOURCE: ScanTransactions")

# 🟢 SOURCE: ScanCustomers
ScanCustomers_df = spark.read.option("header", "true").option("inferSchema", "true").csv("s3://datalake/raw/customers")
ScanCustomers_df = ScanCustomers_df.where("region = 'MX'")
print("📂 SOURCE: ScanCustomers")

# 🔹 TRANSFORM: CleanDates
CleanDates_df = ScanTransactions_df.selectExpr("customer_id", "amount", "date_format(tx_date", ""yyyy-MM-dd") as tx_str", "year(tx_date) as tx_year", "month(tx_date) as tx_month", "datediff(current_date()", "tx_date) as days_ago").where("amount > 0")
print("🔄 TRANSFORM: CleanDates")

# 🔗 JOIN: JoinData
JoinData_df = ScanCustomers_df.join(CleanDates_df, on="customer_id", how="inner")
print("🔗 JOIN: JoinData")

# 🔹 TRANSFORM: AggMonthly
AggMonthly_df = JoinData_df.groupBy("customer_id", "tx_year", "tx_month").agg(sum("amount").alias("total_spent"), count("customer_id").alias("tx_count"))
print("🔄 TRANSFORM: AggMonthly")

# 🔹 PARTITION: PartByRegion
PartByRegion_df = AggMonthly_df.selectExpr("*")
print("🔄 PARTITION: PartByRegion")

# 🏁 SINK: WriteReport
PartByRegion_df.write.mode("overwrite").parquet("s3://datalake/curated/monthly_report")
print("💾 SINK: WriteReport")

spark.stop()
print("✅ BNX PySpark Job Finished")
