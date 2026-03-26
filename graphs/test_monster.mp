# ============================================================
# BNX MONSTER GRAPH - Enterprise Data Platform
# 12 dominios, 8 subgraphs, ~80 nodos, ~100 edges
# ============================================================

# --- SOURCES (16) ---
NODE RawOrders          : SOURCE
NODE RawCustomers       : SOURCE
NODE RawProducts        : SOURCE
NODE RawPayments        : SOURCE
NODE RawReturns         : SOURCE
NODE RawCampaigns       : SOURCE
NODE RawInventory       : SOURCE
NODE RawReviews         : SOURCE
NODE RawShipments       : SOURCE
NODE RawSuppliers       : SOURCE
NODE RawStores          : SOURCE
NODE RawEmployees       : SOURCE
NODE RawWebEvents       : SOURCE
NODE RawAppEvents       : SOURCE
NODE RawSupportTickets  : SOURCE
NODE RawFraudSignals    : SOURCE

# ============================================================
SUBGRAPH Ingestion {
  NODE CleanOrders          : TRANSFORM
  NODE CleanCustomers       : TRANSFORM
  NODE CleanProducts        : TRANSFORM
  NODE CleanPayments        : TRANSFORM
  NODE CleanReturns         : TRANSFORM
  NODE CleanCampaigns       : TRANSFORM
  NODE CleanInventory       : TRANSFORM
  NODE CleanReviews         : TRANSFORM
  NODE CleanShipments       : TRANSFORM
  NODE CleanSuppliers       : TRANSFORM
  NODE CleanStores          : TRANSFORM
  NODE CleanEmployees       : TRANSFORM
  NODE CleanWebEvents       : TRANSFORM
  NODE CleanAppEvents       : TRANSFORM
  NODE CleanSupportTickets  : TRANSFORM
  NODE CleanFraudSignals    : TRANSFORM
}

# ============================================================
SUBGRAPH CustomerDomain {
  NODE FilterActiveCustomers    : TRANSFORM
  NODE CustomerSegment          : TRANSFORM
  NODE CustomerLifetimeValue    : TRANSFORM
  NODE CustomerChurnScore       : TRANSFORM
  NODE CustomerSupportHistory   : JOIN
  NODE CustomerWebBehavior      : JOIN
  NODE CustomerAppBehavior      : JOIN
  NODE CustomerProfile          : JOIN
}

# ============================================================
SUBGRAPH OrderDomain {
  NODE FilterPaidOrders         : TRANSFORM
  NODE OrderTotals              : TRANSFORM
  NODE OrderTxCount             : TRANSFORM
  NODE OrderWithCustomer        : JOIN
  NODE OrderWithProduct         : JOIN
  NODE OrderWithPayment         : JOIN
  NODE OrderWithShipment        : JOIN
  NODE OrderFraudCheck          : JOIN
  NODE OrderEnriched            : JOIN
}

# ============================================================
SUBGRAPH ProductDomain {
  NODE FilterActiveProducts     : TRANSFORM
  NODE ProductRevenue           : TRANSFORM
  NODE ProductReturnRate        : TRANSFORM
  NODE ProductRating            : JOIN
  NODE ProductWithSupplier      : JOIN
  NODE ProductWithInventory     : JOIN
  NODE TopProducts              : TRANSFORM
  NODE LowStockAlert            : TRANSFORM
}

# ============================================================
SUBGRAPH ReturnsDomain {
  NODE FilterReturns            : TRANSFORM
  NODE ReturnRate               : TRANSFORM
  NODE ReturnByProduct          : JOIN
  NODE ReturnByRegion           : JOIN
  NODE HighReturnCustomers      : TRANSFORM
  NODE ReturnFraudFlag          : JOIN
}

# ============================================================
SUBGRAPH CampaignDomain {
  NODE FilterActiveCampaigns    : TRANSFORM
  NODE CampaignWithCustomer     : JOIN
  NODE CampaignConversion       : JOIN
  NODE CampaignROI              : TRANSFORM
  NODE RegionalCampaignCount    : TRANSFORM
  NODE CampaignFraudFilter      : JOIN
}

# ============================================================
SUBGRAPH OperationsDomain {
  NODE ShipmentDelay            : TRANSFORM
  NODE SupplierPerformance      : TRANSFORM
  NODE StoreRevenue             : JOIN
  NODE EmployeeSales            : JOIN
  NODE OperationsReport         : JOIN
}

# ============================================================
SUBGRAPH FinalReport {
  NODE FullOrderBase            : JOIN
  NODE EnrichWithReturns        : JOIN
  NODE EnrichWithCampaign       : JOIN
  NODE EnrichWithOperations     : JOIN
  NODE EnrichWithFraud          : JOIN
  NODE FlagHighValue            : TRANSFORM
  NODE FlagChurned              : TRANSFORM
  NODE FlagAtRisk               : TRANSFORM
  NODE FlagFraud                : TRANSFORM
  NODE MasterReport             : JOIN
}

# ============================================================
# SINKS (10)
NODE Write_MasterReport         : SINK
NODE Write_HighValue            : SINK
NODE Write_Churned              : SINK
NODE Write_AtRisk               : SINK
NODE Write_FraudAlerts          : SINK
NODE Write_TopProducts          : SINK
NODE Write_LowStock             : SINK
NODE Write_ReturnAlerts         : SINK
NODE Write_CampaignReport       : SINK
NODE Write_OperationsReport     : SINK
NODE Write_ShipmentDelay        : SINK
NODE Write_SupplierPerformance  : SINK

# ============================================================
# EDGES - Ingestion
# ============================================================
RawOrders           -> CleanOrders
RawCustomers        -> CleanCustomers
RawProducts         -> CleanProducts
RawPayments         -> CleanPayments
RawReturns          -> CleanReturns
RawCampaigns        -> CleanCampaigns
RawInventory        -> CleanInventory
RawReviews          -> CleanReviews
RawShipments        -> CleanShipments
RawSuppliers        -> CleanSuppliers
RawStores           -> CleanStores
RawEmployees        -> CleanEmployees
RawWebEvents        -> CleanWebEvents
RawAppEvents        -> CleanAppEvents
RawSupportTickets   -> CleanSupportTickets
RawFraudSignals     -> CleanFraudSignals

# ============================================================
# EDGES - CustomerDomain
# ============================================================
CleanCustomers          -> FilterActiveCustomers
FilterActiveCustomers   -> CustomerSegment
CustomerSegment         -> CustomerLifetimeValue
CustomerSegment         -> CustomerChurnScore
CleanSupportTickets     -> CustomerSupportHistory
CustomerSegment         -> CustomerSupportHistory
CleanWebEvents          -> CustomerWebBehavior
CustomerSegment         -> CustomerWebBehavior
CleanAppEvents          -> CustomerAppBehavior
CustomerSegment         -> CustomerAppBehavior
CustomerLifetimeValue   -> CustomerProfile
CustomerChurnScore      -> CustomerProfile
CustomerSupportHistory  -> CustomerProfile
CustomerWebBehavior     -> CustomerProfile
CustomerAppBehavior     -> CustomerProfile

# ============================================================
# EDGES - OrderDomain
# ============================================================
CleanOrders             -> FilterPaidOrders
FilterPaidOrders        -> OrderTotals
FilterPaidOrders        -> OrderTxCount
OrderTotals             -> OrderWithCustomer
CustomerProfile         -> OrderWithCustomer
OrderWithCustomer       -> OrderWithProduct
CleanProducts           -> OrderWithProduct
OrderWithProduct        -> OrderWithPayment
CleanPayments           -> OrderWithPayment
OrderWithPayment        -> OrderWithShipment
CleanShipments          -> OrderWithShipment
OrderWithShipment       -> OrderFraudCheck
CleanFraudSignals       -> OrderFraudCheck
OrderFraudCheck         -> OrderEnriched
OrderTxCount            -> OrderEnriched

# ============================================================
# EDGES - ProductDomain
# ============================================================
CleanProducts           -> FilterActiveProducts
FilterPaidOrders        -> ProductRevenue
FilterActiveProducts    -> ProductRevenue
FilterReturns           -> ProductReturnRate
FilterActiveProducts    -> ProductReturnRate
CleanReviews            -> ProductRating
ProductRevenue          -> ProductRating
ProductRating           -> ProductWithSupplier
CleanSuppliers          -> ProductWithSupplier
ProductWithSupplier     -> ProductWithInventory
CleanInventory          -> ProductWithInventory
ProductWithInventory    -> TopProducts
ProductWithInventory    -> LowStockAlert

# ============================================================
# EDGES - ReturnsDomain
# ============================================================
CleanReturns            -> FilterReturns
FilterReturns           -> ReturnRate
FilterReturns           -> ReturnByProduct
CleanProducts           -> ReturnByProduct
ReturnByProduct         -> ReturnByRegion
CleanOrders             -> ReturnByRegion
ReturnRate              -> HighReturnCustomers
ReturnByProduct         -> ReturnFraudFlag
CleanFraudSignals       -> ReturnFraudFlag

# ============================================================
# EDGES - CampaignDomain
# ============================================================
CleanCampaigns          -> FilterActiveCampaigns
FilterActiveCampaigns   -> CampaignWithCustomer
CustomerProfile         -> CampaignWithCustomer
CampaignWithCustomer    -> CampaignConversion
OrderEnriched           -> CampaignConversion
CampaignConversion      -> CampaignROI
CampaignConversion      -> RegionalCampaignCount
CampaignROI             -> CampaignFraudFilter
CleanFraudSignals       -> CampaignFraudFilter

# ============================================================
# EDGES - OperationsDomain
# ============================================================
CleanShipments          -> ShipmentDelay
CleanSuppliers          -> SupplierPerformance
CleanStores             -> StoreRevenue
OrderEnriched           -> StoreRevenue
CleanEmployees          -> EmployeeSales
OrderEnriched           -> EmployeeSales
StoreRevenue            -> OperationsReport
EmployeeSales           -> OperationsReport

# ============================================================
# EDGES - FinalReport
# ============================================================
OrderEnriched           -> FullOrderBase
ReturnRate              -> FullOrderBase
FullOrderBase           -> EnrichWithReturns
HighReturnCustomers     -> EnrichWithReturns
ReturnFraudFlag         -> EnrichWithReturns
EnrichWithReturns       -> EnrichWithCampaign
CampaignFraudFilter     -> EnrichWithCampaign
EnrichWithCampaign      -> EnrichWithOperations
OperationsReport        -> EnrichWithOperations
EnrichWithOperations    -> EnrichWithFraud
CleanFraudSignals       -> EnrichWithFraud
EnrichWithFraud         -> FlagHighValue
EnrichWithFraud         -> FlagChurned
EnrichWithFraud         -> FlagAtRisk
EnrichWithFraud         -> FlagFraud
FlagHighValue           -> MasterReport
FlagChurned             -> MasterReport
FlagAtRisk              -> MasterReport
FlagFraud               -> MasterReport

# ============================================================
# EDGES - Sinks
# ============================================================
MasterReport            -> Write_MasterReport
FlagHighValue           -> Write_HighValue
FlagChurned             -> Write_Churned
FlagAtRisk              -> Write_AtRisk
FlagFraud               -> Write_FraudAlerts
TopProducts             -> Write_TopProducts
LowStockAlert           -> Write_LowStock
ReturnByProduct         -> Write_ReturnAlerts
CampaignFraudFilter     -> Write_CampaignReport
OperationsReport        -> Write_OperationsReport
ShipmentDelay           -> Write_ShipmentDelay
SupplierPerformance     -> Write_SupplierPerformance
