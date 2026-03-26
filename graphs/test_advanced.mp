# ============================================================
# BNX TEST GRAPH - Full E-Commerce Analytics Pipeline
# ============================================================

# --- SOURCES ---
NODE Orders      : SOURCE
NODE Customers   : SOURCE
NODE Products    : SOURCE
NODE Payments    : SOURCE
NODE Returns     : SOURCE
NODE Campaigns   : SOURCE
NODE Inventory   : SOURCE
NODE Reviews     : SOURCE

# ============================================================
SUBGRAPH Ingestion {
  NODE CleanOrders            : TRANSFORM
  NODE CleanCustomers         : TRANSFORM
  NODE CleanProducts          : TRANSFORM
  NODE CleanPayments          : TRANSFORM
  NODE CleanReturns           : TRANSFORM
  NODE CleanCampaigns         : TRANSFORM
  NODE CleanInventory         : TRANSFORM
  NODE CleanReviews           : TRANSFORM
}

# ============================================================
SUBGRAPH CustomerPipeline {
  NODE FilterActiveCustomers  : TRANSFORM
  NODE CustomerRegion         : JOIN
  NODE CustomerTotals         : TRANSFORM
  NODE CustomerTxCount        : TRANSFORM
  NODE CustomerMetrics        : JOIN
}

# ============================================================
SUBGRAPH OrderPipeline {
  NODE FilterPaidOrders       : TRANSFORM
  NODE OrderTotals            : TRANSFORM
  NODE OrderWithCustomer      : JOIN
  NODE OrderWithProduct       : JOIN
  NODE OrderWithPayment       : JOIN
}

# ============================================================
SUBGRAPH ProductPipeline {
  NODE FilterActiveProducts   : TRANSFORM
  NODE ProductRevenue         : TRANSFORM
  NODE ProductRating          : JOIN
  NODE LowStockAlert          : TRANSFORM
  NODE TopProducts            : TRANSFORM
}

# ============================================================
SUBGRAPH ReturnsPipeline {
  NODE FilterReturns          : TRANSFORM
  NODE ReturnRate             : TRANSFORM
  NODE HighReturnCustomers    : TRANSFORM
  NODE ReturnByProduct        : JOIN
}

# ============================================================
SUBGRAPH CampaignPipeline {
  NODE FilterActiveCampaigns  : TRANSFORM
  NODE CampaignWithCustomer   : JOIN
  NODE CampaignConversion     : TRANSFORM
  NODE RegionalCampaignCount  : TRANSFORM
}

# ============================================================
SUBGRAPH FinalReport {
  NODE FullOrder              : JOIN
  NODE EnrichWithReturns      : JOIN
  NODE EnrichWithCampaign     : JOIN
  NODE FlagHighValue          : TRANSFORM
  NODE FlagChurned            : TRANSFORM
  NODE FlagAtRisk             : TRANSFORM
  NODE MasterReport           : JOIN
}

# ============================================================
# SINKS
NODE Write_HighValue          : SINK
NODE Write_Churned            : SINK
NODE Write_AtRisk             : SINK
NODE Write_MasterReport       : SINK
NODE Write_TopProducts        : SINK
NODE Write_ReturnAlerts       : SINK
NODE Write_CampaignReport     : SINK

# ============================================================
# EDGES - Ingestion
# ============================================================
Orders      -> CleanOrders
Customers   -> CleanCustomers
Products    -> CleanProducts
Payments    -> CleanPayments
Returns     -> CleanReturns
Campaigns   -> CleanCampaigns
Inventory   -> CleanInventory
Reviews     -> CleanReviews

# ============================================================
# EDGES - CustomerPipeline
# ============================================================
CleanCustomers          -> FilterActiveCustomers
FilterActiveCustomers   -> CustomerRegion
CleanOrders             -> CustomerRegion
CustomerRegion          -> CustomerTotals
CustomerRegion          -> CustomerTxCount
CustomerTotals          -> CustomerMetrics
CustomerTxCount         -> CustomerMetrics

# ============================================================
# EDGES - OrderPipeline
# ============================================================
CleanOrders             -> FilterPaidOrders
FilterPaidOrders        -> OrderTotals
OrderTotals             -> OrderWithCustomer
CustomerMetrics         -> OrderWithCustomer
OrderWithCustomer       -> OrderWithProduct
FilterPaidOrders        -> OrderWithProduct
OrderWithProduct        -> OrderWithPayment
CleanPayments           -> OrderWithPayment

# ============================================================
# EDGES - ProductPipeline
# ============================================================
CleanProducts           -> FilterActiveProducts
FilterPaidOrders        -> ProductRevenue
FilterActiveProducts    -> ProductRevenue
CleanReviews            -> ProductRating
ProductRevenue          -> ProductRating
CleanInventory          -> LowStockAlert
ProductRating           -> TopProducts
LowStockAlert           -> TopProducts

# ============================================================
# EDGES - ReturnsPipeline
# ============================================================
CleanReturns            -> FilterReturns
FilterReturns           -> ReturnRate
ReturnRate              -> HighReturnCustomers
FilterReturns           -> ReturnByProduct
CleanProducts           -> ReturnByProduct

# ============================================================
# EDGES - CampaignPipeline
# ============================================================
CleanCampaigns          -> FilterActiveCampaigns
FilterActiveCampaigns   -> CampaignWithCustomer
FilterActiveCustomers   -> CampaignWithCustomer
CampaignWithCustomer    -> CampaignConversion
OrderWithPayment        -> CampaignConversion
CampaignConversion      -> RegionalCampaignCount

# ============================================================
# EDGES - FinalReport
# ============================================================
OrderWithPayment        -> FullOrder
ReturnRate              -> FullOrder
FullOrder               -> EnrichWithReturns
HighReturnCustomers     -> EnrichWithReturns
EnrichWithReturns       -> EnrichWithCampaign
CampaignConversion      -> EnrichWithCampaign
EnrichWithCampaign      -> FlagHighValue
EnrichWithCampaign      -> FlagChurned
EnrichWithCampaign      -> FlagAtRisk
FlagHighValue           -> MasterReport
FlagChurned             -> MasterReport
FlagAtRisk              -> MasterReport
TopProducts             -> MasterReport
RegionalCampaignCount   -> MasterReport

# ============================================================
# EDGES - Sinks
# ============================================================
FlagHighValue           -> Write_HighValue
FlagChurned             -> Write_Churned
FlagAtRisk              -> Write_AtRisk
MasterReport            -> Write_MasterReport
TopProducts             -> Write_TopProducts
ReturnByProduct         -> Write_ReturnAlerts
RegionalCampaignCount   -> Write_CampaignReport
