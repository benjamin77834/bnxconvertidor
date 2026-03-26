"""
🚀 BNX V54 GENERATED GLUE JOB
📅 Generated at: 2026-03-26 11:39:15.125394
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

# 🟢 SOURCE: Orders
Orders_df = spark.read.format("parquet").load("s3://bnx/raw/orders")
print("📂 SOURCE: Orders")

# 🟢 SOURCE: Customers
Customers_df = spark.read.format("parquet").load("s3://bnx/raw/customers")
print("📂 SOURCE: Customers")

# 🟢 SOURCE: Products
Products_df = spark.read.format("parquet").load("s3://bnx/raw/products")
print("📂 SOURCE: Products")

# 🟢 SOURCE: Payments
Payments_df = spark.read.format("parquet").load("s3://bnx/raw/payments")
print("📂 SOURCE: Payments")

# 🟢 SOURCE: Returns
Returns_df = spark.read.format("parquet").load("s3://bnx/raw/returns")
print("📂 SOURCE: Returns")

# 🟢 SOURCE: Campaigns
Campaigns_df = spark.read.format("parquet").load("s3://bnx/raw/campaigns")
print("📂 SOURCE: Campaigns")

# 🟢 SOURCE: Inventory
Inventory_df = spark.read.format("parquet").load("s3://bnx/raw/inventory")
print("📂 SOURCE: Inventory")

# 🟢 SOURCE: Reviews
Reviews_df = spark.read.format("parquet").load("s3://bnx/raw/reviews")
print("📂 SOURCE: Reviews")

# 🔹 TRANSFORM: CleanOrders
CleanOrders_df = Orders_df.selectExpr("order_id", "customer_id", "product_id", "payment_id", "amount", "status", "order_date").where("order_id IS NOT NULL AND amount > 0")
print("🔄 TRANSFORM: CleanOrders")

# 🔹 TRANSFORM: CleanCustomers
CleanCustomers_df = Customers_df.selectExpr("customer_id", "name", "email", "region", "segment", "created_at").where("customer_id IS NOT NULL")
print("🔄 TRANSFORM: CleanCustomers")

# 🔹 TRANSFORM: CleanProducts
CleanProducts_df = Products_df.selectExpr("product_id", "name", "category", "price", "stock").where("product_id IS NOT NULL AND price > 0")
print("🔄 TRANSFORM: CleanProducts")

# 🔹 TRANSFORM: CleanPayments
CleanPayments_df = Payments_df.selectExpr("payment_id", "customer_id", "amount", "method", "payment_date", "confirmed").where("confirmed = true")
print("🔄 TRANSFORM: CleanPayments")

# 🔹 TRANSFORM: CleanReturns
CleanReturns_df = Returns_df.selectExpr("return_id", "order_id", "customer_id", "reason", "return_date").where("return_id IS NOT NULL")
print("🔄 TRANSFORM: CleanReturns")

# 🔹 TRANSFORM: CleanCampaigns
CleanCampaigns_df = Campaigns_df.selectExpr("campaign_id", "customer_id", "region", "active", "start_date", "end_date").where("campaign_id IS NOT NULL")
print("🔄 TRANSFORM: CleanCampaigns")

# 🔹 TRANSFORM: CleanInventory
CleanInventory_df = Inventory_df.selectExpr("product_id", "warehouse_id", "stock", "reorder_level").where("product_id IS NOT NULL")
print("🔄 TRANSFORM: CleanInventory")

# 🔹 TRANSFORM: CleanReviews
CleanReviews_df = Reviews_df.selectExpr("review_id", "product_id", "customer_id", "rating", "review_date").where("rating IS NOT NULL")
print("🔄 TRANSFORM: CleanReviews")

# 🔹 TRANSFORM: FilterActiveCustomers
FilterActiveCustomers_df = CleanCustomers_df.selectExpr("*").where("segment != 'inactive'")
print("🔄 TRANSFORM: FilterActiveCustomers")

# 🔗 JOIN: CustomerRegion
CustomerRegion_df = FilterActiveCustomers_df.join(CleanOrders_df, on="customer_id", how="inner")
print("🔗 JOIN: CustomerRegion")

# 🔹 TRANSFORM: CustomerTotals
CustomerTotals_df = CustomerRegion_df.groupBy("customer_id").agg(sum("amount").alias("customer_total"), count("order_id").alias("total_orders"))
print("🔄 TRANSFORM: CustomerTotals")

# 🔹 TRANSFORM: CustomerTxCount
CustomerTxCount_df = CustomerRegion_df.groupBy("customer_id").agg(count("order_id").alias("tx_count"), max("order_date").alias("last_order_date"))
print("🔄 TRANSFORM: CustomerTxCount")

# 🔗 JOIN: CustomerMetrics
CustomerMetrics_df = CustomerTotals_df.join(CustomerTxCount_df, on="customer_id", how="inner")
print("🔗 JOIN: CustomerMetrics")

# 🔹 TRANSFORM: FilterPaidOrders
FilterPaidOrders_df = CleanOrders_df.selectExpr("*").where("status = 'paid'")
print("🔄 TRANSFORM: FilterPaidOrders")

# 🔹 TRANSFORM: OrderTotals
OrderTotals_df = FilterPaidOrders_df.groupBy("customer_id", "product_id").agg(sum("amount").alias("total_spent"), count("order_id").alias("order_count")).where("total_spent > 0")
print("🔄 TRANSFORM: OrderTotals")

# 🔗 JOIN: OrderWithCustomer
OrderWithCustomer_df = OrderTotals_df.join(CustomerMetrics_df, on="customer_id", how="inner")
print("🔗 JOIN: OrderWithCustomer")

# 🔗 JOIN: OrderWithProduct
OrderWithProduct_df = OrderWithCustomer_df.join(FilterPaidOrders_df, on="product_id", how="left")
print("🔗 JOIN: OrderWithProduct")

# 🔗 JOIN: OrderWithPayment
OrderWithPayment_df = OrderWithProduct_df.join(CleanPayments_df, on="customer_id", how="left")
print("🔗 JOIN: OrderWithPayment")

# 🔹 TRANSFORM: FilterActiveProducts
FilterActiveProducts_df = CleanProducts_df.selectExpr("*").where("stock > 0")
print("🔄 TRANSFORM: FilterActiveProducts")

# 🔹 TRANSFORM: ProductRevenue
ProductRevenue_df = FilterPaidOrders_df.groupBy("product_id").agg(sum("amount").alias("revenue"), count("order_id").alias("units_sold")).where("revenue > 0")
print("🔄 TRANSFORM: ProductRevenue")

# 🔗 JOIN: ProductRating
ProductRating_df = CleanReviews_df.join(ProductRevenue_df, on="product_id", how="left")
print("🔗 JOIN: ProductRating")

# 🔹 TRANSFORM: LowStockAlert
LowStockAlert_df = CleanInventory_df.selectExpr("*").where("stock < reorder_level")
print("🔄 TRANSFORM: LowStockAlert")

# 🔹 TRANSFORM: TopProducts
TopProducts_df = ProductRating_df.selectExpr("*").where("units_sold > 10")
print("🔄 TRANSFORM: TopProducts")

# 🔹 TRANSFORM: FilterReturns
FilterReturns_df = CleanReturns_df.selectExpr("return_id", "order_id", "customer_id", "reason", "return_date").where("return_date IS NOT NULL")
print("🔄 TRANSFORM: FilterReturns")

# 🔹 TRANSFORM: ReturnRate
ReturnRate_df = FilterReturns_df.groupBy("customer_id").agg(count("return_id").alias("return_count")).where("return_count > 0")
print("🔄 TRANSFORM: ReturnRate")

# 🔹 TRANSFORM: HighReturnCustomers
HighReturnCustomers_df = ReturnRate_df.selectExpr("*").where("return_count > 3")
print("🔄 TRANSFORM: HighReturnCustomers")

# 🔗 JOIN: ReturnByProduct
ReturnByProduct_df = FilterReturns_df.join(CleanProducts_df, on="product_id", how="left")
print("🔗 JOIN: ReturnByProduct")

# 🔹 TRANSFORM: FilterActiveCampaigns
FilterActiveCampaigns_df = CleanCampaigns_df.selectExpr("*").where("active = true")
print("🔄 TRANSFORM: FilterActiveCampaigns")

# 🔗 JOIN: CampaignWithCustomer
CampaignWithCustomer_df = FilterActiveCampaigns_df.join(FilterActiveCustomers_df, on="customer_id", how="inner")
print("🔗 JOIN: CampaignWithCustomer")

# 🔹 TRANSFORM: CampaignConversion
CampaignConversion_df = CampaignWithCustomer_df.selectExpr("*").where("order_count > 0")
print("🔄 TRANSFORM: CampaignConversion")

# 🔹 TRANSFORM: RegionalCampaignCount
RegionalCampaignCount_df = CampaignConversion_df.groupBy("region").agg(count("campaign_id").alias("campaign_count"), sum("customer_total").alias("regional_revenue"))
print("🔄 TRANSFORM: RegionalCampaignCount")

# 🔗 JOIN: FullOrder
FullOrder_df = OrderWithPayment_df.join(ReturnRate_df, on="customer_id", how="left")
print("🔗 JOIN: FullOrder")

# 🔗 JOIN: EnrichWithReturns
EnrichWithReturns_df = FullOrder_df.join(HighReturnCustomers_df, on="customer_id", how="left")
print("🔗 JOIN: EnrichWithReturns")

# 🔗 JOIN: EnrichWithCampaign
EnrichWithCampaign_df = EnrichWithReturns_df.join(CampaignConversion_df, on="customer_id", how="left")
print("🔗 JOIN: EnrichWithCampaign")

# 🔹 TRANSFORM: FlagHighValue
FlagHighValue_df = EnrichWithCampaign_df.selectExpr("*").where("total_spent > 1000")
print("🔄 TRANSFORM: FlagHighValue")

# 🔹 TRANSFORM: FlagChurned
FlagChurned_df = EnrichWithCampaign_df.selectExpr("*").where("order_count < 2 AND return_count > 1")
print("🔄 TRANSFORM: FlagChurned")

# 🔹 TRANSFORM: FlagAtRisk
FlagAtRisk_df = EnrichWithCampaign_df.selectExpr("*").where("customer_total < 200 AND tx_count < 3")
print("🔄 TRANSFORM: FlagAtRisk")

# 🔗 JOIN: MasterReport
MasterReport_df = FlagHighValue_df.join(FlagChurned_df, on="customer_id", how="left")
print("🔗 JOIN: MasterReport")

# 🏁 SINK: Write_HighValue
FlagHighValue_df.write.mode("overwrite").format("parquet").save("s3://bnx/output/write_highvalue")
print("💾 SINK: Write_HighValue")

# 🏁 SINK: Write_Churned
FlagChurned_df.write.mode("overwrite").format("parquet").save("s3://bnx/output/write_churned")
print("💾 SINK: Write_Churned")

# 🏁 SINK: Write_AtRisk
FlagAtRisk_df.write.mode("overwrite").format("parquet").save("s3://bnx/output/write_atrisk")
print("💾 SINK: Write_AtRisk")

# 🏁 SINK: Write_MasterReport
MasterReport_df.write.mode("overwrite").format("parquet").save("s3://bnx/output/write_masterreport")
print("💾 SINK: Write_MasterReport")

# 🏁 SINK: Write_TopProducts
TopProducts_df.write.mode("overwrite").format("parquet").save("s3://bnx/output/write_topproducts")
print("💾 SINK: Write_TopProducts")

# 🏁 SINK: Write_ReturnAlerts
ReturnByProduct_df.write.mode("overwrite").format("parquet").save("s3://bnx/output/write_returnalerts")
print("💾 SINK: Write_ReturnAlerts")

# 🏁 SINK: Write_CampaignReport
RegionalCampaignCount_df.write.mode("overwrite").format("parquet").save("s3://bnx/output/write_campaignreport")
print("💾 SINK: Write_CampaignReport")

print("✅ BNX Glue Job V54 Finished")
