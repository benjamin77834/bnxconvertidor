"""
? BNX V54 GENERATED GLUE JOB
? Generated at: 2026-05-06 16:37:24.956447
"""

from awsglue.context import GlueContext
from pyspark.context import SparkContext
from pyspark.sql.functions import *

sc = SparkContext()
glueContext = GlueContext(sc)
spark = glueContext.spark_session

print("? BNX Glue Job V54 Started")

# =========================
# DAG EXECUTION V54
# =========================

# ? SOURCE: ScanTransactions
ScanTransactions_df = spark.read.format("parquet").load("s3://datalake/raw/transactions")
ScanTransactions_df = ScanTransactions_df.where("year = 2026 AND month = 10")
print("? SOURCE: ScanTransactions")

# ? SOURCE: ScanCustomers
ScanCustomers_df = spark.read.format("csv").option("header", "true").option("inferSchema", "true").load("s3://datalake/raw/customers")
ScanCustomers_df = ScanCustomers_df.where("region = 'MX'")
print("? SOURCE: ScanCustomers")

# ? TRANSFORM: CleanDates
CleanDates_df = ScanTransactions_df.selectExpr("customer_id", "amount", "date_format(tx_date", ""yyyy-MM-dd") as tx_str", "year(tx_date) as tx_year", "month(tx_date) as tx_month", "datediff(current_date()", "tx_date) as days_ago").where("amount > 0")
print("? TRANSFORM: CleanDates")

# ? JOIN: JoinData
JoinData_df = ScanCustomers_df.join(CleanDates_df, on="customer_id", how="inner")
print("? JOIN: JoinData")

# ? TRANSFORM: AggMonthly
AggMonthly_df = JoinData_df.groupBy("customer_id", "tx_year", "tx_month").agg(sum("amount").alias("total_spent"), count("customer_id").alias("tx_count"))
print("? TRANSFORM: AggMonthly")

# ? PARTITION: PartByRegion
PartByRegion_df = AggMonthly_df.repartition(8, "region, tx_year")
print("? PARTITION: PartByRegion")

# ? SINK: WriteReport
PartByRegion_df.write.mode("overwrite").format("parquet").save("s3://datalake/curated/monthly_report")
print("? SINK: WriteReport")

print("? BNX Glue Job V54 Finished")
