"""
🚀 BNX V54 GENERATED PYSPARK JOB
📅 Generated at: 2026-04-07 21:02:34.246741
"""

from pyspark.sql import SparkSession
from pyspark.sql.functions import *
from pyspark.sql.window import Window

spark = SparkSession.builder.appName("BNX_Pipeline").getOrCreate()

print("🚀 BNX PySpark Job Started")

# 🟢 SOURCE: ingest_customers
ingest_customers_df = spark.read.parquet("s3://bank-datalake/raw/ingest_customers")
print("📂 SOURCE: ingest_customers")

# 🟢 SOURCE: ingest_transactions
ingest_transactions_df = spark.read.parquet("s3://bank-datalake/raw/ingest_transactions")
print("📂 SOURCE: ingest_transactions")

# 🟢 SOURCE: ingest_accounts
ingest_accounts_df = spark.read.parquet("s3://bank-datalake/raw/ingest_accounts")
print("📂 SOURCE: ingest_accounts")

# 🟢 SOURCE: ingest_cards
ingest_cards_df = spark.read.parquet("s3://bank-datalake/raw/ingest_cards")
print("📂 SOURCE: ingest_cards")

# 🟢 SOURCE: ingest_fx_rates
ingest_fx_rates_df = spark.read.parquet("s3://bank-datalake/raw/ingest_fx_rates")
print("📂 SOURCE: ingest_fx_rates")

# 🔹 TRANSFORM: clean_customers
clean_customers_df = ingest_customers_df.selectExpr("*")
print("🔄 TRANSFORM: clean_customers")

# 🔹 TRANSFORM: clean_transactions
clean_transactions_df = ingest_transactions_df.selectExpr("*")
print("🔄 TRANSFORM: clean_transactions")

# 🔹 TRANSFORM: clean_accounts
clean_accounts_df = ingest_accounts_df.selectExpr("*")
print("🔄 TRANSFORM: clean_accounts")

# 🧹 DEDUP: dedup_transactions
_w_dedup_transactions = Window.partitionBy("tx_id").orderBy(col("tx_date").desc())
dedup_transactions_df = clean_transactions_df.withColumn("_rn", row_number().over(_w_dedup_transactions)).where("_rn = 1").drop("_rn")
print("🧹 DEDUP: dedup_transactions")

# 🔗 JOIN: enrich_tx_with_customer
enrich_tx_with_customer_df = dedup_transactions_df.join(clean_customers_df, on="customer_id", how="left")
print("🔗 JOIN: enrich_tx_with_customer")

# 🔗 JOIN: enrich_tx_with_account
enrich_tx_with_account_df = enrich_tx_with_customer_df.join(clean_accounts_df, on="customer_id", how="left")
print("🔗 JOIN: enrich_tx_with_account")

# 🔗 JOIN: enrich_tx_with_fx
enrich_tx_with_fx_df = enrich_tx_with_account_df.join(ingest_fx_rates_df, on="customer_id", how="left")
print("🔗 JOIN: enrich_tx_with_fx")

# 🔹 TRANSFORM: agg_daily_totals
agg_daily_totals_df = enrich_tx_with_fx_df.selectExpr("*")
print("🔄 TRANSFORM: agg_daily_totals")

# 🔹 TRANSFORM: agg_customer_balance
agg_customer_balance_df = enrich_tx_with_fx_df.selectExpr("*")
print("🔄 TRANSFORM: agg_customer_balance")

# 🔹 TRANSFORM: agg_product_revenue
agg_product_revenue_df = enrich_tx_with_fx_df.selectExpr("*")
print("🔄 TRANSFORM: agg_product_revenue")

# 🔹 TRANSFORM: risk_scoring
risk_scoring_df = agg_customer_balance_df.selectExpr("*")
print("🔄 TRANSFORM: risk_scoring")

# 🔹 TRANSFORM: aml_detection
aml_detection_df = enrich_tx_with_fx_df.selectExpr("*")
print("🔄 TRANSFORM: aml_detection")

# 🏁 SINK: report_regulatory
agg_daily_totals_df.write.mode("overwrite").parquet("s3://bank-datalake/curated/report_regulatory")
print("💾 SINK: report_regulatory")

# 🏁 SINK: report_finance
agg_daily_totals_df.write.mode("overwrite").parquet("s3://bank-datalake/curated/report_finance")
print("💾 SINK: report_finance")

# 🏁 SINK: report_risk_dashboard
risk_scoring_df.write.mode("overwrite").parquet("s3://bank-datalake/curated/report_risk_dashboard")
print("💾 SINK: report_risk_dashboard")

# 🏁 SINK: notify_completion
report_regulatory_df.write.mode("overwrite").parquet("s3://bank-datalake/curated/notify_completion")
print("💾 SINK: notify_completion")

spark.stop()
print("✅ BNX PySpark Job Finished")
