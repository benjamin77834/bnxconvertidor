"""
🚀 BNX V54 GENERATED PYSPARK JOB
📅 Generated at: 2026-04-07 21:08:25.759229
"""

from pyspark.sql import SparkSession
from pyspark.sql.functions import *
from pyspark.sql.window import Window

spark = SparkSession.builder.appName("BNX_Pipeline").getOrCreate()

print("🚀 BNX PySpark Job Started")

# 🟢 SOURCE: ingest_transactions
ingest_transactions_df = spark.read.parquet("s3://bank-cc-datalake/raw/ingest_transactions")
print("📂 SOURCE: ingest_transactions")

# 🟢 SOURCE: ingest_cardholders
ingest_cardholders_df = spark.read.parquet("s3://bank-cc-datalake/raw/ingest_cardholders")
print("📂 SOURCE: ingest_cardholders")

# 🟢 SOURCE: ingest_merchants
ingest_merchants_df = spark.read.parquet("s3://bank-cc-datalake/raw/ingest_merchants")
print("📂 SOURCE: ingest_merchants")

# 🟢 SOURCE: ingest_fx_rates
ingest_fx_rates_df = spark.read.parquet("s3://bank-cc-datalake/raw/ingest_fx_rates")
print("📂 SOURCE: ingest_fx_rates")

# 🟢 SOURCE: ingest_limits
ingest_limits_df = spark.read.parquet("s3://bank-cc-datalake/raw/ingest_limits")
print("📂 SOURCE: ingest_limits")

# 🔹 TRANSFORM: clean_transactions
clean_transactions_df = ingest_transactions_df.selectExpr("*")
print("🔄 TRANSFORM: clean_transactions")

# 🔹 TRANSFORM: clean_cardholders
clean_cardholders_df = ingest_cardholders_df.selectExpr("*")
print("🔄 TRANSFORM: clean_cardholders")

# 🧹 DEDUP: dedup_transactions
_w_dedup_transactions = Window.partitionBy("tx_id").orderBy(col("tx_date").desc())
dedup_transactions_df = clean_transactions_df.withColumn("_rn", row_number().over(_w_dedup_transactions)).where("_rn = 1").drop("_rn")
print("🧹 DEDUP: dedup_transactions")

# 🔗 JOIN: enrich_tx_cardholder
enrich_tx_cardholder_df = dedup_transactions_df.join(clean_cardholders_df, on="customer_id", how="left")
print("🔗 JOIN: enrich_tx_cardholder")

# 🔗 JOIN: enrich_tx_merchant
enrich_tx_merchant_df = enrich_tx_cardholder_df.join(ingest_merchants_df, on="customer_id", how="left")
print("🔗 JOIN: enrich_tx_merchant")

# 🔗 JOIN: enrich_tx_fx
enrich_tx_fx_df = enrich_tx_merchant_df.join(ingest_fx_rates_df, on="customer_id", how="left")
print("🔗 JOIN: enrich_tx_fx")

# 🔗 JOIN: enrich_tx_limits
enrich_tx_limits_df = enrich_tx_fx_df.join(ingest_limits_df, on="customer_id", how="left")
print("🔗 JOIN: enrich_tx_limits")

# 🔹 TRANSFORM: agg_daily_spend
agg_daily_spend_df = enrich_tx_limits_df.selectExpr("*")
print("🔄 TRANSFORM: agg_daily_spend")

# 🔹 TRANSFORM: agg_merchant_volume
agg_merchant_volume_df = enrich_tx_limits_df.selectExpr("*")
print("🔄 TRANSFORM: agg_merchant_volume")

# 🔹 TRANSFORM: risk_overlimit
risk_overlimit_df = enrich_tx_limits_df.selectExpr("*")
print("🔄 TRANSFORM: risk_overlimit")

# 🔹 TRANSFORM: fraud_detection
fraud_detection_df = enrich_tx_limits_df.selectExpr("*")
print("🔄 TRANSFORM: fraud_detection")

# 🔹 TRANSFORM: aml_screening
aml_screening_df = fraud_detection_df.selectExpr("*")
print("🔄 TRANSFORM: aml_screening")

# 🏁 SINK: report_daily_summary
agg_daily_spend_df.write.mode("overwrite").parquet("s3://bank-cc-datalake/curated/report_daily_summary")
print("💾 SINK: report_daily_summary")

# 🏁 SINK: report_fraud_alerts
fraud_detection_df.write.mode("overwrite").parquet("s3://bank-cc-datalake/curated/report_fraud_alerts")
print("💾 SINK: report_fraud_alerts")

# 🏁 SINK: report_cardholder_statements
agg_daily_spend_df.write.mode("overwrite").parquet("s3://bank-cc-datalake/curated/report_cardholder_statements")
print("💾 SINK: report_cardholder_statements")

# 🏁 SINK: report_regulatory
aml_screening_df.write.mode("overwrite").parquet("s3://bank-cc-datalake/curated/report_regulatory")
print("💾 SINK: report_regulatory")

# 🏁 SINK: notify_completion
report_daily_summary_df.write.mode("overwrite").parquet("s3://bank-cc-datalake/curated/notify_completion")
print("💾 SINK: notify_completion")

spark.stop()
print("✅ BNX PySpark Job Finished")
