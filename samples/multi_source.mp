# ============================================================
# BNX Multi-Source Pipeline
# Sources: S3, JDBC (PostgreSQL, MySQL), Kafka
# Partitioned output
# ============================================================

# --- SOURCES ---
NODE RawOrdersS3        : SOURCE
NODE RawCustomersDB     : SOURCE
NODE RawProductsDB      : SOURCE
NODE RawPaymentsKafka   : SOURCE
NODE RawEventsKafka     : SOURCE
NODE RawInventoryS3     : SOURCE
NODE RawFXRatesAPI      : SOURCE

# ============================================================
SUBGRAPH Ingestion {
  NODE CleanOrders       : TRANSFORM
  NODE CleanCustomers    : TRANSFORM
  NODE CleanProducts     : TRANSFORM
  NODE CleanPayments     : TRANSFORM
  NODE CleanEvents       : TRANSFORM
  NODE CleanInventory    : TRANSFORM
  NODE CleanFXRates      : TRANSFORM
}

# ============================================================
SUBGRAPH Dedup {
  NODE DedupOrders       : DEDUP
  NODE DedupPayments     : DEDUP
}

# ============================================================
SUBGRAPH Enrich {
  NODE OrderWithCustomer : JOIN
  NODE OrderWithProduct  : JOIN
  NODE OrderWithPayment  : JOIN
  NODE OrderWithFX       : LOOKUP
  NODE FullOrder         : JOIN
}

# ============================================================
SUBGRAPH Aggregate {
  NODE DailyRevenue      : TRANSFORM
  NODE RevenueByRegion   : TRANSFORM
  NODE RevenueByProduct  : TRANSFORM
  NODE InventoryAlert    : TRANSFORM
  NODE CustomerSpend     : TRANSFORM
}

# ============================================================
SUBGRAPH Output {
  NODE NormalizeEvents   : NORMALIZE
  NODE EventsByType      : TRANSFORM
}

# --- SINKS ---
NODE Write_DailyRevenue     : SINK
NODE Write_RevenueByRegion  : SINK
NODE Write_RevenueByProduct : SINK
NODE Write_InventoryAlert   : SINK
NODE Write_CustomerSpend    : SINK
NODE Write_EventsByType     : SINK
NODE Write_FullOrderKafka   : SINK

# ============================================================
# EDGES - Ingestion
# ============================================================
RawOrdersS3       -> CleanOrders
RawCustomersDB    -> CleanCustomers
RawProductsDB     -> CleanProducts
RawPaymentsKafka  -> CleanPayments
RawEventsKafka    -> CleanEvents
RawInventoryS3    -> CleanInventory
RawFXRatesAPI     -> CleanFXRates

# ============================================================
# EDGES - Dedup
# ============================================================
CleanOrders   -> DedupOrders
CleanPayments -> DedupPayments

# ============================================================
# EDGES - Enrich
# ============================================================
DedupOrders       -> OrderWithCustomer
CleanCustomers    -> OrderWithCustomer
OrderWithCustomer -> OrderWithProduct
CleanProducts     -> OrderWithProduct
OrderWithProduct  -> OrderWithPayment
DedupPayments     -> OrderWithPayment
OrderWithPayment  -> OrderWithFX
CleanFXRates      -> OrderWithFX
OrderWithFX       -> FullOrder
CleanInventory    -> FullOrder

# ============================================================
# EDGES - Aggregate
# ============================================================
FullOrder      -> DailyRevenue
FullOrder      -> RevenueByRegion
FullOrder      -> RevenueByProduct
CleanInventory -> InventoryAlert
FullOrder      -> CustomerSpend

# ============================================================
# EDGES - Output
# ============================================================
CleanEvents    -> NormalizeEvents
NormalizeEvents -> EventsByType

# ============================================================
# EDGES - Sinks
# ============================================================
DailyRevenue      -> Write_DailyRevenue
RevenueByRegion   -> Write_RevenueByRegion
RevenueByProduct  -> Write_RevenueByProduct
InventoryAlert    -> Write_InventoryAlert
CustomerSpend     -> Write_CustomerSpend
EventsByType      -> Write_EventsByType
FullOrder         -> Write_FullOrderKafka
