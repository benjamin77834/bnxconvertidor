"""
🚀 BNX V54 GENERATED GLUE JOB
📅 Generated at: 2026-03-26 12:18:00.262860
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
RawOrders_df = spark.read.format("parquet").load("s3://bnx/raw/raworders")
print("📂 SOURCE: RawOrders")

# 🟢 SOURCE: RawCustomers
RawCustomers_df = spark.read.format("parquet").load("s3://bnx/raw/rawcustomers")
print("📂 SOURCE: RawCustomers")

# 🟢 SOURCE: RawProducts
RawProducts_df = spark.read.format("parquet").load("s3://bnx/raw/rawproducts")
print("📂 SOURCE: RawProducts")

# 🟢 SOURCE: RawPayments
RawPayments_df = spark.read.format("parquet").load("s3://bnx/raw/rawpayments")
print("📂 SOURCE: RawPayments")

# 🟢 SOURCE: RawReturns
RawReturns_df = spark.read.format("parquet").load("s3://bnx/raw/rawreturns")
print("📂 SOURCE: RawReturns")

# 🟢 SOURCE: RawCampaigns
RawCampaigns_df = spark.read.format("parquet").load("s3://bnx/raw/rawcampaigns")
print("📂 SOURCE: RawCampaigns")

# 🟢 SOURCE: RawInventory
RawInventory_df = spark.read.format("parquet").load("s3://bnx/raw/rawinventory")
print("📂 SOURCE: RawInventory")

# 🟢 SOURCE: RawReviews
RawReviews_df = spark.read.format("parquet").load("s3://bnx/raw/rawreviews")
print("📂 SOURCE: RawReviews")

# 🟢 SOURCE: RawShipments
RawShipments_df = spark.read.format("parquet").load("s3://bnx/raw/rawshipments")
print("📂 SOURCE: RawShipments")

# 🟢 SOURCE: RawSuppliers
RawSuppliers_df = spark.read.format("parquet").load("s3://bnx/raw/rawsuppliers")
print("📂 SOURCE: RawSuppliers")

# 🟢 SOURCE: RawStores
RawStores_df = spark.read.format("parquet").load("s3://bnx/raw/rawstores")
print("📂 SOURCE: RawStores")

# 🟢 SOURCE: RawEmployees
RawEmployees_df = spark.read.format("parquet").load("s3://bnx/raw/rawemployees")
print("📂 SOURCE: RawEmployees")

# 🟢 SOURCE: RawWebEvents
RawWebEvents_df = spark.read.format("parquet").load("s3://bnx/raw/rawwebevents")
print("📂 SOURCE: RawWebEvents")

# 🟢 SOURCE: RawAppEvents
RawAppEvents_df = spark.read.format("parquet").load("s3://bnx/raw/rawappevents")
print("📂 SOURCE: RawAppEvents")

# 🟢 SOURCE: RawSupportTickets
RawSupportTickets_df = spark.read.format("parquet").load("s3://bnx/raw/rawsupporttickets")
print("📂 SOURCE: RawSupportTickets")

# 🟢 SOURCE: RawFraudSignals
RawFraudSignals_df = spark.read.format("parquet").load("s3://bnx/raw/rawfraudsignals")
print("📂 SOURCE: RawFraudSignals")

# 🔹 TRANSFORM: CleanOrders
CleanOrders_df = RawOrders_df.selectExpr("order_id", "customer_id", "product_id", "payment_id", "amount", "status", "order_date", "store_id").where("order_id IS NOT NULL AND amount > 0")
print("🔄 TRANSFORM: CleanOrders")

# 🔹 TRANSFORM: CleanCustomers
CleanCustomers_df = RawCustomers_df.selectExpr("customer_id", "name", "email", "region", "segment", "created_at").where("customer_id IS NOT NULL")
print("🔄 TRANSFORM: CleanCustomers")

# 🔹 TRANSFORM: CleanProducts
CleanProducts_df = RawProducts_df.selectExpr("product_id", "name", "category", "price", "supplier_id", "stock").where("product_id IS NOT NULL AND price > 0")
print("🔄 TRANSFORM: CleanProducts")

# 🔹 TRANSFORM: CleanPayments
CleanPayments_df = RawPayments_df.selectExpr("payment_id", "customer_id", "order_id", "amount", "method", "payment_date", "confirmed").where("confirmed = true")
print("🔄 TRANSFORM: CleanPayments")

# 🔹 TRANSFORM: CleanReturns
CleanReturns_df = RawReturns_df.selectExpr("return_id", "order_id", "product_id", "customer_id", "reason", "return_date").where("return_id IS NOT NULL")
print("🔄 TRANSFORM: CleanReturns")

# 🔹 TRANSFORM: CleanCampaigns
CleanCampaigns_df = RawCampaigns_df.selectExpr("campaign_id", "customer_id", "region", "active", "start_date", "end_date", "budget").where("campaign_id IS NOT NULL")
print("🔄 TRANSFORM: CleanCampaigns")

# 🔹 TRANSFORM: CleanInventory
CleanInventory_df = RawInventory_df.selectExpr("product_id", "warehouse_id", "stock", "reorder_level", "last_updated").where("product_id IS NOT NULL")
print("🔄 TRANSFORM: CleanInventory")

# 🔹 TRANSFORM: CleanReviews
CleanReviews_df = RawReviews_df.selectExpr("review_id", "product_id", "customer_id", "rating", "review_date").where("rating IS NOT NULL")
print("🔄 TRANSFORM: CleanReviews")

# 🔹 TRANSFORM: CleanShipments
CleanShipments_df = RawShipments_df.selectExpr("shipment_id", "order_id", "carrier", "shipped_date", "delivered_date", "status").where("shipment_id IS NOT NULL")
print("🔄 TRANSFORM: CleanShipments")

# 🔹 TRANSFORM: CleanSuppliers
CleanSuppliers_df = RawSuppliers_df.selectExpr("supplier_id", "name", "country", "rating", "lead_time_days").where("supplier_id IS NOT NULL")
print("🔄 TRANSFORM: CleanSuppliers")

# 🔹 TRANSFORM: CleanStores
CleanStores_df = RawStores_df.selectExpr("store_id", "name", "region", "city", "manager_id").where("store_id IS NOT NULL")
print("🔄 TRANSFORM: CleanStores")

# 🔹 TRANSFORM: CleanEmployees
CleanEmployees_df = RawEmployees_df.selectExpr("employee_id", "name", "store_id", "role", "hire_date").where("employee_id IS NOT NULL")
print("🔄 TRANSFORM: CleanEmployees")

# 🔹 TRANSFORM: CleanWebEvents
CleanWebEvents_df = RawWebEvents_df.selectExpr("event_id", "customer_id", "page", "action", "event_date").where("event_id IS NOT NULL")
print("🔄 TRANSFORM: CleanWebEvents")

# 🔹 TRANSFORM: CleanAppEvents
CleanAppEvents_df = RawAppEvents_df.selectExpr("event_id", "customer_id", "screen", "action", "event_date").where("event_id IS NOT NULL")
print("🔄 TRANSFORM: CleanAppEvents")

# 🔹 TRANSFORM: CleanSupportTickets
CleanSupportTickets_df = RawSupportTickets_df.selectExpr("ticket_id", "customer_id", "issue_type", "status", "created_at", "resolved_at").where("ticket_id IS NOT NULL")
print("🔄 TRANSFORM: CleanSupportTickets")

# 🔹 TRANSFORM: CleanFraudSignals
CleanFraudSignals_df = RawFraudSignals_df.selectExpr("signal_id", "customer_id", "order_id", "score", "flagged", "detected_at").where("signal_id IS NOT NULL")
print("🔄 TRANSFORM: CleanFraudSignals")

# 🔹 TRANSFORM: FilterActiveCustomers
FilterActiveCustomers_df = CleanCustomers_df.selectExpr("*").where("segment != 'inactive'")
print("🔄 TRANSFORM: FilterActiveCustomers")

# 🔹 TRANSFORM: CustomerSegment
CustomerSegment_df = FilterActiveCustomers_df.selectExpr("*").where("segment IN ('premium', 'standard', 'new')")
print("🔄 TRANSFORM: CustomerSegment")

# 🔹 TRANSFORM: CustomerLifetimeValue
CustomerLifetimeValue_df = CustomerSegment_df.groupBy("customer_id").agg(sum("amount").alias("ltv"), count("order_id").alias("total_orders")).where("ltv > 0")
print("🔄 TRANSFORM: CustomerLifetimeValue")

# 🔹 TRANSFORM: CustomerChurnScore
CustomerChurnScore_df = CustomerSegment_df.groupBy("customer_id").agg(count("ticket_id").alias("support_count"), max("created_at").alias("last_contact")).where("support_count >= 0")
print("🔄 TRANSFORM: CustomerChurnScore")

# 🔗 JOIN: CustomerSupportHistory
CustomerSupportHistory_df = CleanSupportTickets_df.join(CustomerSegment_df, on="customer_id", how="left")
print("🔗 JOIN: CustomerSupportHistory")

# 🔗 JOIN: CustomerWebBehavior
CustomerWebBehavior_df = CleanWebEvents_df.join(CustomerSegment_df, on="customer_id", how="left")
print("🔗 JOIN: CustomerWebBehavior")

# 🔗 JOIN: CustomerAppBehavior
CustomerAppBehavior_df = CleanAppEvents_df.join(CustomerSegment_df, on="customer_id", how="left")
print("🔗 JOIN: CustomerAppBehavior")

# 🔗 JOIN: CustomerProfile
CustomerProfile_df = CustomerLifetimeValue_df.join(CustomerChurnScore_df, on="customer_id", how="left")
CustomerProfile_df = CustomerProfile_df.join(CustomerSupportHistory_df, on="customer_id", how="left")
CustomerProfile_df = CustomerProfile_df.join(CustomerWebBehavior_df, on="customer_id", how="left")
CustomerProfile_df = CustomerProfile_df.join(CustomerAppBehavior_df, on="customer_id", how="left")
print("🔗 JOIN: CustomerProfile")

# 🔹 TRANSFORM: FilterPaidOrders
FilterPaidOrders_df = CleanOrders_df.selectExpr("*").where("status = 'paid'")
print("🔄 TRANSFORM: FilterPaidOrders")

# 🔹 TRANSFORM: OrderTotals
OrderTotals_df = FilterPaidOrders_df.groupBy("customer_id", "product_id", "order_id", "store_id").agg(sum("amount").alias("total_spent"), count("order_id").alias("order_count")).where("total_spent > 0")
print("🔄 TRANSFORM: OrderTotals")

# 🔹 TRANSFORM: OrderTxCount
OrderTxCount_df = FilterPaidOrders_df.groupBy("customer_id").agg(count("order_id").alias("tx_count"), max("order_date").alias("last_order_date"))
print("🔄 TRANSFORM: OrderTxCount")

# 🔗 JOIN: OrderWithCustomer
OrderWithCustomer_df = OrderTotals_df.join(CustomerProfile_df, on="customer_id", how="inner")
print("🔗 JOIN: OrderWithCustomer")

# 🔗 JOIN: OrderWithProduct
OrderWithProduct_df = OrderWithCustomer_df.join(CleanProducts_df, on="product_id", how="left")
print("🔗 JOIN: OrderWithProduct")

# 🔗 JOIN: OrderWithPayment
OrderWithPayment_df = OrderWithProduct_df.join(CleanPayments_df, on="order_id", how="left")
print("🔗 JOIN: OrderWithPayment")

# 🔗 JOIN: OrderWithShipment
OrderWithShipment_df = OrderWithPayment_df.join(CleanShipments_df, on="order_id", how="left")
print("🔗 JOIN: OrderWithShipment")

# 🔗 JOIN: OrderFraudCheck
OrderFraudCheck_df = OrderWithShipment_df.join(CleanFraudSignals_df, on="order_id", how="left")
print("🔗 JOIN: OrderFraudCheck")

# 🔗 JOIN: OrderEnriched
OrderEnriched_df = OrderFraudCheck_df.join(OrderTxCount_df, on="customer_id", how="left")
print("🔗 JOIN: OrderEnriched")

# 🔹 TRANSFORM: FilterActiveProducts
FilterActiveProducts_df = CleanProducts_df.selectExpr("*").where("stock > 0")
print("🔄 TRANSFORM: FilterActiveProducts")

# 🔹 TRANSFORM: ProductRevenue
ProductRevenue_df = FilterPaidOrders_df.groupBy("product_id", "supplier_id").agg(sum("amount").alias("revenue"), count("order_id").alias("units_sold")).where("revenue > 0")
print("🔄 TRANSFORM: ProductRevenue")

# 🔹 TRANSFORM: FilterReturns
FilterReturns_df = CleanReturns_df.selectExpr("return_id", "order_id", "product_id", "customer_id", "reason", "return_date").where("return_date IS NOT NULL")
print("🔄 TRANSFORM: FilterReturns")

# 🔹 TRANSFORM: ProductReturnRate
ProductReturnRate_df = FilterReturns_df.groupBy("product_id").agg(count("return_id").alias("return_count")).where("return_count >= 0")
print("🔄 TRANSFORM: ProductReturnRate")

# 🔗 JOIN: ProductRating
ProductRating_df = CleanReviews_df.join(ProductRevenue_df, on="product_id", how="left")
print("🔗 JOIN: ProductRating")

# 🔗 JOIN: ProductWithSupplier
ProductWithSupplier_df = ProductRating_df.join(CleanSuppliers_df, on="supplier_id", how="left")
print("🔗 JOIN: ProductWithSupplier")

# 🔗 JOIN: ProductWithInventory
ProductWithInventory_df = ProductWithSupplier_df.join(CleanInventory_df, on="product_id", how="left")
print("🔗 JOIN: ProductWithInventory")

# 🔹 TRANSFORM: TopProducts
TopProducts_df = ProductWithInventory_df.selectExpr("*").where("units_sold > 10")
print("🔄 TRANSFORM: TopProducts")

# 🔹 TRANSFORM: LowStockAlert
LowStockAlert_df = ProductWithInventory_df.selectExpr("*").where("stock < reorder_level")
print("🔄 TRANSFORM: LowStockAlert")

# 🔹 TRANSFORM: ReturnRate
ReturnRate_df = FilterReturns_df.groupBy("customer_id").agg(count("return_id").alias("return_count")).where("return_count > 0")
print("🔄 TRANSFORM: ReturnRate")

# 🔗 JOIN: ReturnByProduct
ReturnByProduct_df = FilterReturns_df.join(CleanProducts_df, on="product_id", how="left")
print("🔗 JOIN: ReturnByProduct")

# 🔗 JOIN: ReturnByRegion
ReturnByRegion_df = ReturnByProduct_df.join(CleanOrders_df, on="order_id", how="left")
print("🔗 JOIN: ReturnByRegion")

# 🔹 TRANSFORM: HighReturnCustomers
HighReturnCustomers_df = ReturnRate_df.selectExpr("*").where("return_count > 3")
print("🔄 TRANSFORM: HighReturnCustomers")

# 🔗 JOIN: ReturnFraudFlag
ReturnFraudFlag_df = ReturnByProduct_df.join(CleanFraudSignals_df, on="order_id", how="left")
print("🔗 JOIN: ReturnFraudFlag")

# 🔹 TRANSFORM: FilterActiveCampaigns
FilterActiveCampaigns_df = CleanCampaigns_df.selectExpr("*").where("active = true")
print("🔄 TRANSFORM: FilterActiveCampaigns")

# 🔗 JOIN: CampaignWithCustomer
CampaignWithCustomer_df = FilterActiveCampaigns_df.join(CustomerProfile_df, on="customer_id", how="inner")
print("🔗 JOIN: CampaignWithCustomer")

# 🔗 JOIN: CampaignConversion
CampaignConversion_df = CampaignWithCustomer_df.join(OrderEnriched_df, on="customer_id", how="left")
print("🔗 JOIN: CampaignConversion")

# 🔹 TRANSFORM: CampaignROI
CampaignROI_df = CampaignConversion_df.groupBy("campaign_id", "region", "customer_id").agg(sum("total_spent").alias("campaign_revenue"), count("customer_id").alias("converted_customers")).where("campaign_revenue > 0")
print("🔄 TRANSFORM: CampaignROI")

# 🔹 TRANSFORM: RegionalCampaignCount
RegionalCampaignCount_df = CampaignConversion_df.groupBy("region").agg(count("campaign_id").alias("campaign_count"), sum("campaign_revenue").alias("regional_revenue"))
print("🔄 TRANSFORM: RegionalCampaignCount")

# 🔗 JOIN: CampaignFraudFilter
CampaignFraudFilter_df = CampaignROI_df.join(CleanFraudSignals_df, on="customer_id", how="left")
print("🔗 JOIN: CampaignFraudFilter")

# 🔹 TRANSFORM: ShipmentDelay
ShipmentDelay_df = CleanShipments_df.selectExpr("*").where("delivered_date > shipped_date AND status = 'delayed'")
print("🔄 TRANSFORM: ShipmentDelay")

# 🔹 TRANSFORM: SupplierPerformance
SupplierPerformance_df = CleanSuppliers_df.groupBy("supplier_id").agg(avg("lead_time_days").alias("avg_lead_time"), count("product_id").alias("product_count")).where("avg_lead_time > 0")
print("🔄 TRANSFORM: SupplierPerformance")

# 🔗 JOIN: StoreRevenue
StoreRevenue_df = CleanStores_df.join(OrderEnriched_df, on="store_id", how="left")
print("🔗 JOIN: StoreRevenue")

# 🔗 JOIN: EmployeeSales
EmployeeSales_df = CleanEmployees_df.join(OrderEnriched_df, on="store_id", how="left")
print("🔗 JOIN: EmployeeSales")

# 🔗 JOIN: OperationsReport
OperationsReport_df = StoreRevenue_df.join(EmployeeSales_df, on="store_id", how="left")
print("🔗 JOIN: OperationsReport")

# 🔗 JOIN: FullOrderBase
FullOrderBase_df = OrderEnriched_df.join(ReturnRate_df, on="customer_id", how="left")
print("🔗 JOIN: FullOrderBase")

# 🔗 JOIN: EnrichWithReturns
EnrichWithReturns_df = FullOrderBase_df.join(HighReturnCustomers_df, on="customer_id", how="left")
EnrichWithReturns_df = EnrichWithReturns_df.join(ReturnFraudFlag_df, on="customer_id", how="left")
print("🔗 JOIN: EnrichWithReturns")

# 🔗 JOIN: EnrichWithCampaign
EnrichWithCampaign_df = EnrichWithReturns_df.join(CampaignFraudFilter_df, on="customer_id", how="left")
print("🔗 JOIN: EnrichWithCampaign")

# 🔗 JOIN: EnrichWithOperations
EnrichWithOperations_df = EnrichWithCampaign_df.join(OperationsReport_df, on="order_id", how="left")
print("🔗 JOIN: EnrichWithOperations")

# 🔗 JOIN: EnrichWithFraud
EnrichWithFraud_df = EnrichWithOperations_df.join(CleanFraudSignals_df, on="customer_id", how="left")
print("🔗 JOIN: EnrichWithFraud")

# 🔹 TRANSFORM: FlagHighValue
FlagHighValue_df = EnrichWithFraud_df.selectExpr("*").where("total_spent > 5000")
print("🔄 TRANSFORM: FlagHighValue")

# 🔹 TRANSFORM: FlagChurned
FlagChurned_df = EnrichWithFraud_df.selectExpr("*").where("order_count < 2 AND return_count > 2")
print("🔄 TRANSFORM: FlagChurned")

# 🔹 TRANSFORM: FlagAtRisk
FlagAtRisk_df = EnrichWithFraud_df.selectExpr("*").where("total_spent < 500 AND tx_count < 3")
print("🔄 TRANSFORM: FlagAtRisk")

# 🔹 TRANSFORM: FlagFraud
FlagFraud_df = EnrichWithFraud_df.selectExpr("*").where("score > 0.8 AND flagged = true")
print("🔄 TRANSFORM: FlagFraud")

# 🔗 JOIN: MasterReport
MasterReport_df = FlagHighValue_df.join(FlagChurned_df, on="customer_id", how="left")
MasterReport_df = MasterReport_df.join(FlagAtRisk_df, on="customer_id", how="left")
MasterReport_df = MasterReport_df.join(FlagFraud_df, on="customer_id", how="left")
print("🔗 JOIN: MasterReport")

# 🏁 SINK: Write_MasterReport
MasterReport_df.write.mode("overwrite").format("parquet").save("s3://bnx/output/write_masterreport")
print("💾 SINK: Write_MasterReport")

# 🏁 SINK: Write_HighValue
FlagHighValue_df.write.mode("overwrite").format("parquet").save("s3://bnx/output/write_highvalue")
print("💾 SINK: Write_HighValue")

# 🏁 SINK: Write_Churned
FlagChurned_df.write.mode("overwrite").format("parquet").save("s3://bnx/output/write_churned")
print("💾 SINK: Write_Churned")

# 🏁 SINK: Write_AtRisk
FlagAtRisk_df.write.mode("overwrite").format("parquet").save("s3://bnx/output/write_atrisk")
print("💾 SINK: Write_AtRisk")

# 🏁 SINK: Write_FraudAlerts
FlagFraud_df.write.mode("overwrite").format("parquet").save("s3://bnx/output/write_fraudalerts")
print("💾 SINK: Write_FraudAlerts")

# 🏁 SINK: Write_TopProducts
TopProducts_df.write.mode("overwrite").format("parquet").save("s3://bnx/output/write_topproducts")
print("💾 SINK: Write_TopProducts")

# 🏁 SINK: Write_LowStock
LowStockAlert_df.write.mode("overwrite").format("parquet").save("s3://bnx/output/write_lowstock")
print("💾 SINK: Write_LowStock")

# 🏁 SINK: Write_ReturnAlerts
ReturnByProduct_df.write.mode("overwrite").format("parquet").save("s3://bnx/output/write_returnalerts")
print("💾 SINK: Write_ReturnAlerts")

# 🏁 SINK: Write_CampaignReport
CampaignFraudFilter_df.write.mode("overwrite").format("parquet").save("s3://bnx/output/write_campaignreport")
print("💾 SINK: Write_CampaignReport")

# 🏁 SINK: Write_OperationsReport
OperationsReport_df.write.mode("overwrite").format("parquet").save("s3://bnx/output/write_operationsreport")
print("💾 SINK: Write_OperationsReport")

# 🏁 SINK: Write_ShipmentDelay
ShipmentDelay_df.write.mode("overwrite").format("parquet").save("s3://bnx/output/write_shipmentdelay")
print("💾 SINK: Write_ShipmentDelay")

# 🏁 SINK: Write_SupplierPerformance
SupplierPerformance_df.write.mode("overwrite").format("parquet").save("s3://bnx/output/write_supplierperformance")
print("💾 SINK: Write_SupplierPerformance")

print("✅ BNX Glue Job V54 Finished")
