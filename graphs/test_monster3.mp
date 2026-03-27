# ============================================================
# BNX MONSTER 3 - Banking Analytics Platform
# 12 sources, 10 subgraphs, DEDUP + NORMALIZE + LOOKUP
# ============================================================

# --- SOURCES (12) ---
NODE RawAccounts        : SOURCE
NODE RawTransactions    : SOURCE
NODE RawCards           : SOURCE
NODE RawLoans           : SOURCE
NODE RawPayments        : SOURCE
NODE RawCustomers       : SOURCE
NODE RawBranches        : SOURCE
NODE RawProducts        : SOURCE
NODE RawFXRates         : SOURCE
NODE RawRiskScores      : SOURCE
NODE RawAlerts          : SOURCE
NODE RawAuditLog        : SOURCE

# ============================================================
SUBGRAPH Ingestion {
  NODE CleanAccounts      : TRANSFORM
  NODE CleanTransactions  : TRANSFORM
  NODE CleanCards         : TRANSFORM
  NODE CleanLoans         : TRANSFORM
  NODE CleanPayments      : TRANSFORM
  NODE CleanCustomers     : TRANSFORM
  NODE CleanBranches      : TRANSFORM
  NODE CleanProducts      : TRANSFORM
  NODE CleanFXRates       : TRANSFORM
  NODE CleanRiskScores    : TRANSFORM
  NODE CleanAlerts        : TRANSFORM
  NODE CleanAuditLog      : TRANSFORM
}

# ============================================================
SUBGRAPH Deduplication {
  NODE DedupTransactions  : DEDUP
  NODE DedupPayments      : DEDUP
  NODE DedupAlerts        : DEDUP
  NODE DedupAuditLog      : DEDUP
}

# ============================================================
SUBGRAPH Normalization {
  NODE NormAlertTags      : NORMALIZE
  NODE NormProductFeatures : NORMALIZE
  NODE NormCardBenefits   : NORMALIZE
}

# ============================================================
SUBGRAPH Lookups {
  NODE LookupBranch       : LOOKUP
  NODE LookupProduct      : LOOKUP
  NODE LookupFXRate       : LOOKUP
  NODE LookupRisk         : LOOKUP
}

# ============================================================
SUBGRAPH CustomerDomain {
  NODE FilterActiveCustomers : TRANSFORM
  NODE CustomerWithAccount   : JOIN
  NODE CustomerWithCards     : JOIN
  NODE CustomerRiskProfile   : JOIN
  NODE CustomerProfile       : JOIN
}

# ============================================================
SUBGRAPH TransactionDomain {
  NODE FilterSettledTx       : TRANSFORM
  NODE TxWithCustomer        : JOIN
  NODE TxWithFX              : JOIN
  NODE TxNormalized          : TRANSFORM
  NODE TxEnriched            : JOIN
}

# ============================================================
SUBGRAPH LoanDomain {
  NODE FilterActiveLoans     : TRANSFORM
  NODE LoanWithCustomer      : JOIN
  NODE LoanWithRisk          : JOIN
  NODE LoanAggByCustomer     : TRANSFORM
  NODE LoanDefaultRisk       : TRANSFORM
}

# ============================================================
SUBGRAPH PaymentDomain {
  NODE FilterConfirmedPay    : TRANSFORM
  NODE PayWithCustomer       : JOIN
  NODE PayByMethod           : TRANSFORM
  NODE PayByBranch           : TRANSFORM
}

# ============================================================
SUBGRAPH AMLDomain {
  NODE SuspiciousTx          : TRANSFORM
  NODE HighRiskCustomers     : TRANSFORM
  NODE AlertWithTx           : JOIN
  NODE AMLReport             : JOIN
}

# ============================================================
SUBGRAPH FinalReport {
  NODE FullCustomerBase      : JOIN
  NODE EnrichWithLoans       : JOIN
  NODE EnrichWithPayments    : JOIN
  NODE EnrichWithAML         : JOIN
  NODE FlagHighValue         : TRANSFORM
  NODE FlagDefaultRisk       : TRANSFORM
  NODE FlagSuspicious        : TRANSFORM
  NODE FlagInactive          : TRANSFORM
  NODE MasterReport          : JOIN
}

# ============================================================
# SINKS (10)
NODE Write_MasterReport     : SINK
NODE Write_HighValue        : SINK
NODE Write_DefaultRisk      : SINK
NODE Write_Suspicious       : SINK
NODE Write_Inactive         : SINK
NODE Write_AMLReport        : SINK
NODE Write_LoanReport       : SINK
NODE Write_PaymentReport    : SINK
NODE Write_NormAlerts       : SINK
NODE Write_AuditTrail       : SINK

# ============================================================
# EDGES - Ingestion
# ============================================================
RawAccounts       -> CleanAccounts
RawTransactions   -> CleanTransactions
RawCards          -> CleanCards
RawLoans          -> CleanLoans
RawPayments       -> CleanPayments
RawCustomers      -> CleanCustomers
RawBranches       -> CleanBranches
RawProducts       -> CleanProducts
RawFXRates        -> CleanFXRates
RawRiskScores     -> CleanRiskScores
RawAlerts         -> CleanAlerts
RawAuditLog       -> CleanAuditLog

# ============================================================
# EDGES - Deduplication
# ============================================================
CleanTransactions -> DedupTransactions
CleanPayments     -> DedupPayments
CleanAlerts       -> DedupAlerts
CleanAuditLog     -> DedupAuditLog

# ============================================================
# EDGES - Normalization
# ============================================================
DedupAlerts       -> NormAlertTags
CleanProducts     -> NormProductFeatures
CleanCards        -> NormCardBenefits

# ============================================================
# EDGES - Lookups
# ============================================================
DedupTransactions -> LookupBranch
CleanBranches     -> LookupBranch
DedupTransactions -> LookupProduct
CleanProducts     -> LookupProduct
DedupTransactions -> LookupFXRate
CleanFXRates      -> LookupFXRate
CleanCustomers    -> LookupRisk
CleanRiskScores   -> LookupRisk

# ============================================================
# EDGES - CustomerDomain
# ============================================================
CleanCustomers        -> FilterActiveCustomers
FilterActiveCustomers -> CustomerWithAccount
CleanAccounts         -> CustomerWithAccount
CustomerWithAccount   -> CustomerWithCards
CleanCards            -> CustomerWithCards
CustomerWithCards     -> CustomerRiskProfile
LookupRisk            -> CustomerRiskProfile
CustomerRiskProfile   -> CustomerProfile
NormCardBenefits      -> CustomerProfile

# ============================================================
# EDGES - TransactionDomain
# ============================================================
DedupTransactions     -> FilterSettledTx
FilterSettledTx       -> TxWithCustomer
CustomerProfile       -> TxWithCustomer
TxWithCustomer        -> TxWithFX
LookupFXRate          -> TxWithFX
TxWithFX              -> TxNormalized
TxNormalized          -> TxEnriched
LookupBranch          -> TxEnriched

# ============================================================
# EDGES - LoanDomain
# ============================================================
CleanLoans            -> FilterActiveLoans
FilterActiveLoans     -> LoanWithCustomer
CustomerProfile       -> LoanWithCustomer
LoanWithCustomer      -> LoanWithRisk
LookupRisk            -> LoanWithRisk
LoanWithRisk          -> LoanAggByCustomer
LoanWithRisk          -> LoanDefaultRisk

# ============================================================
# EDGES - PaymentDomain
# ============================================================
DedupPayments         -> FilterConfirmedPay
FilterConfirmedPay    -> PayWithCustomer
CustomerProfile       -> PayWithCustomer
PayWithCustomer       -> PayByMethod
PayWithCustomer       -> PayByBranch

# ============================================================
# EDGES - AMLDomain
# ============================================================
TxEnriched            -> SuspiciousTx
LoanDefaultRisk       -> HighRiskCustomers
NormAlertTags         -> AlertWithTx
TxEnriched            -> AlertWithTx
SuspiciousTx          -> AMLReport
HighRiskCustomers     -> AMLReport
AlertWithTx           -> AMLReport

# ============================================================
# EDGES - FinalReport
# ============================================================
TxEnriched            -> FullCustomerBase
CustomerProfile       -> FullCustomerBase
FullCustomerBase      -> EnrichWithLoans
LoanAggByCustomer     -> EnrichWithLoans
EnrichWithLoans       -> EnrichWithPayments
PayByMethod           -> EnrichWithPayments
EnrichWithPayments    -> EnrichWithAML
AMLReport             -> EnrichWithAML
EnrichWithAML         -> FlagHighValue
EnrichWithAML         -> FlagDefaultRisk
EnrichWithAML         -> FlagSuspicious
EnrichWithAML         -> FlagInactive
FlagHighValue         -> MasterReport
FlagDefaultRisk       -> MasterReport
FlagSuspicious        -> MasterReport
FlagInactive          -> MasterReport

# ============================================================
# EDGES - Sinks
# ============================================================
MasterReport          -> Write_MasterReport
FlagHighValue         -> Write_HighValue
FlagDefaultRisk       -> Write_DefaultRisk
FlagSuspicious        -> Write_Suspicious
FlagInactive          -> Write_Inactive
AMLReport             -> Write_AMLReport
LoanAggByCustomer     -> Write_LoanReport
PayByBranch           -> Write_PaymentReport
NormAlertTags         -> Write_NormAlerts
DedupAuditLog         -> Write_AuditTrail
