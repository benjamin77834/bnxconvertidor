"""
🚀 BNX V54 GENERATED GLUE JOB
📅 Generated at: 2026-04-08 10:49:35.017963
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

# 🟢 SOURCE: RawOrdersS3
RawOrdersS3_df = spark.read.format("parquet").load("s3://datalake/raw/orders")
print("📂 SOURCE: RawOrdersS3")

# 🟢 SOURCE: RawCustomersDB
RawCustomersDB_df = spark.read.format("jdbc").option("url", "jdbc:postgresql://db-master:5432/core_banking").option("dbtable", "customers").load()
print("📂 SOURCE: RawCustomersDB")

# 🟢 SOURCE: RawProductsDB
RawProductsDB_df = spark.read.format("jdbc").option("url", "jdbc:mysql://catalog-db:3306/product_catalog").option("dbtable", "products").load()
print("📂 SOURCE: RawProductsDB")

# 🟢 SOURCE: RawPaymentsKafka
RawPaymentsKafka_df = spark.readStream.format("kafka").option("kafka.bootstrap.servers", "kafka1:9092,kafka2:9092,kafka3:9092").option("subscribe", "payments.realtime").load()
RawPaymentsKafka_df = RawPaymentsKafka_df.selectExpr("CAST(value AS STRING) as json_value")
print("📂 SOURCE: RawPaymentsKafka")

# 🟢 SOURCE: RawEventsKafka
RawEventsKafka_df = spark.readStream.format("kafka").option("kafka.bootstrap.servers", "kafka1:9092,kafka2:9092,kafka3:9092").option("subscribe", "user.events.clickstream").load()
RawEventsKafka_df = RawEventsKafka_df.selectExpr("CAST(value AS STRING) as json_value")
print("📂 SOURCE: RawEventsKafka")

# 🟢 SOURCE: RawInventoryS3
RawInventoryS3_df = spark.read.format("csv").load("s3://datalake/raw/inventory")
print("📂 SOURCE: RawInventoryS3")

# 🟢 SOURCE: RawFXRatesAPI
RawFXRatesAPI_df = spark.read.format("json").load("s3://datalake/raw/fx_rates")
print("📂 SOURCE: RawFXRatesAPI")

# 🔹 TRANSFORM: CleanOrders
CleanOrders_df = RawOrdersS3_df.selectExpr("order_id", "customer_id", "product_id", "amount", "currency", "status", "region", "order_date").where("amount > 0 AND status IN ('completed', 'shipped')")
print("🔄 TRANSFORM: CleanOrders")

# 🔹 TRANSFORM: CleanCustomers
CleanCustomers_df = RawCustomersDB_df.selectExpr("customer_id", "name", "email", "region", "segment", "created_at").where("customer_id IS NOT NULL")
print("🔄 TRANSFORM: CleanCustomers")

# 🔹 TRANSFORM: CleanProducts
CleanProducts_df = RawProductsDB_df.selectExpr("product_id", "name", "category", "price", "supplier_id").where("product_id IS NOT NULL AND price > 0")
print("🔄 TRANSFORM: CleanProducts")

# 🔹 TRANSFORM: CleanPayments
CleanPayments_df = RawPaymentsKafka_df.selectExpr("payment_id", "order_id", "amount", "method", "payment_date", "confirmed").where("confirmed = true")
print("🔄 TRANSFORM: CleanPayments")

# 🔹 TRANSFORM: CleanEvents
CleanEvents_df = RawEventsKafka_df.selectExpr("event_id", "user_id", "event_type", "page", "action", "tags", "event_date").where("event_id IS NOT NULL")
print("🔄 TRANSFORM: CleanEvents")

# 🔹 TRANSFORM: CleanInventory
CleanInventory_df = RawInventoryS3_df.selectExpr("product_id", "warehouse_id", "stock", "reorder_level", "last_updated").where("product_id IS NOT NULL")
print("🔄 TRANSFORM: CleanInventory")

# 🔹 TRANSFORM: CleanFXRates
CleanFXRates_df = RawFXRatesAPI_df.selectExpr("currency", "rate_to_usd", "rate_date").where("currency IS NOT NULL")
print("🔄 TRANSFORM: CleanFXRates")

# 🧹 DEDUP: DedupOrders
from pyspark.sql.window import Window
_w_DedupOrders = Window.partitionBy("order_id").orderBy(col("order_date").desc())
DedupOrders_df = CleanOrders_df.withColumn("_rn", row_number().over(_w_DedupOrders)).where("_rn = 1").drop("_rn")
print("🧹 DEDUP: DedupOrders")

# 🧹 DEDUP: DedupPayments
from pyspark.sql.window import Window
_w_DedupPayments = Window.partitionBy("payment_id").orderBy(col("payment_date").desc())
DedupPayments_df = CleanPayments_df.withColumn("_rn", row_number().over(_w_DedupPayments)).where("_rn = 1").drop("_rn")
print("🧹 DEDUP: DedupPayments")

# 🔗 JOIN: OrderWithCustomer
OrderWithCustomer_df = DedupOrders_df.join(CleanCustomers_df, on="customer_id", how="inner")
print("🔗 JOIN: OrderWithCustomer")

# 🔗 JOIN: OrderWithProduct
OrderWithProduct_df = OrderWithCustomer_df.join(CleanProducts_df, on="product_id", how="left")
print("🔗 JOIN: OrderWithProduct")

# 🔗 JOIN: OrderWithPayment
OrderWithPayment_df = OrderWithProduct_df.join(DedupPayments_df, on="order_id", how="left")
print("🔗 JOIN: OrderWithPayment")

# 🔍 LOOKUP: OrderWithFX
from pyspark.sql.functions import broadcast
_lookup_OrderWithFX = broadcast(CleanFXRates_df.select("currency", "rate_to_usd"))
OrderWithFX_df = OrderWithPayment_df.join(_lookup_OrderWithFX, on="currency", how="left")
print("🔍 LOOKUP: OrderWithFX")

# 🔗 JOIN: FullOrder
FullOrder_df = OrderWithFX_df.join(CleanInventory_df, on="product_id", how="left")
print("🔗 JOIN: FullOrder")

# 🔹 TRANSFORM: DailyRevenue
DailyRevenue_df = FullOrder_df.groupBy("order_date").agg(sum("amount").alias("daily_revenue"), count("order_id").alias("order_count"), col("SUM(amount * rate_to_usd) as daily_revenue_usd"))
print("🔄 TRANSFORM: DailyRevenue")

# 🔹 TRANSFORM: RevenueByRegion
RevenueByRegion_df = FullOrder_df.groupBy("region", "order_date").agg(sum("amount").alias("region_revenue"), count("order_id").alias("region_orders"))
print("🔄 TRANSFORM: RevenueByRegion")

# 🔹 TRANSFORM: RevenueByProduct
RevenueByProduct_df = FullOrder_df.groupBy("product_id", "name", "category").agg(sum("amount").alias("product_revenue"), count("order_id").alias("product_orders"))
print("🔄 TRANSFORM: RevenueByProduct")

# 🔹 TRANSFORM: InventoryAlert
InventoryAlert_df = CleanInventory_df.selectExpr("*").where("stock < reorder_level")
print("🔄 TRANSFORM: InventoryAlert")

# 🔹 TRANSFORM: CustomerSpend
CustomerSpend_df = FullOrder_df.groupBy("customer_id", "name", "region").agg(sum("amount").alias("total_spent"), count("order_id").alias("total_orders"), max("order_date").alias("last_order"))
print("🔄 TRANSFORM: CustomerSpend")

# 📐 NORMALIZE: NormalizeEvents
NormalizeEvents_df = CleanEvents_df.withColumn("tags", explode(split(col("tags"), ",")))
print("📐 NORMALIZE: NormalizeEvents")

# 🔹 TRANSFORM: EventsByType
EventsByType_df = NormalizeEvents_df.groupBy("event_type").agg(count("event_id").alias("event_count"), col("COUNT(DISTINCT user_id) as unique_users"))
print("🔄 TRANSFORM: EventsByType")

# 🏁 SINK: Write_DailyRevenue
DailyRevenue_df.write.mode("overwrite").format("parquet").save("s3://datalake/curated/daily_revenue")
print("💾 SINK: Write_DailyRevenue")

# 🏁 SINK: Write_RevenueByRegion
RevenueByRegion_df.write.mode("overwrite").format("parquet").save("s3://datalake/curated/revenue_by_region")
print("💾 SINK: Write_RevenueByRegion")

# 🏁 SINK: Write_RevenueByProduct
RevenueByProduct_df.write.mode("overwrite").format("parquet").save("s3://datalake/curated/revenue_by_product")
print("💾 SINK: Write_RevenueByProduct")

# 🏁 SINK: Write_InventoryAlert
InventoryAlert_df.write.format("jdbc").mode("append").option("url", "jdbc:postgresql://db-master:5432/operations").option("dbtable", "inventory_alerts").save()
print("💾 SINK: Write_InventoryAlert")

# 🏁 SINK: Write_CustomerSpend
CustomerSpend_df.write.mode("overwrite").format("parquet").save("s3://datalake/curated/customer_spend")
print("💾 SINK: Write_CustomerSpend")

# 🏁 SINK: Write_EventsByType
EventsByType_df.write.mode("overwrite").format("parquet").save("s3://datalake/curated/events_by_type")
print("💾 SINK: Write_EventsByType")

# 🏁 SINK: Write_FullOrderKafka
FullOrder_df.selectExpr("to_json(struct(*)) AS value").write.format("kafka").option("kafka.bootstrap.servers", "kafka1:9092,kafka2:9092,kafka3:9092").option("topic", "orders.enriched").save()
print("💾 SINK: Write_FullOrderKafka")

print("✅ BNX Glue Job V54 Finished")
