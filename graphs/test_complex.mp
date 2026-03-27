# ============================================================
# BNX Complex Test - DEDUP, NORMALIZE, LOOKUP
# Simulates Ab Initio Complex profile
# ============================================================

NODE RawTransactions  : SOURCE
NODE RawCustomers     : SOURCE
NODE RawProducts      : SOURCE
NODE RawCategories    : SOURCE
NODE RawTags          : SOURCE

SUBGRAPH Ingestion {
  NODE CleanTransactions : TRANSFORM
  NODE CleanCustomers    : TRANSFORM
  NODE CleanProducts     : TRANSFORM
}

SUBGRAPH Dedup {
  NODE DedupTransactions : DEDUP
  NODE DedupCustomers    : DEDUP
}

SUBGRAPH Normalize {
  NODE NormalizeTags     : NORMALIZE
  NODE NormalizeProducts : NORMALIZE
}

SUBGRAPH Lookup {
  NODE LookupCategory    : LOOKUP
  NODE LookupCustomer    : LOOKUP
}

SUBGRAPH Process {
  NODE EnrichedTx        : JOIN
  NODE TotalByCustomer   : TRANSFORM
  NODE TotalByCategory   : TRANSFORM
}

NODE Write_Enriched     : SINK
NODE Write_ByCustomer   : SINK
NODE Write_ByCategory   : SINK

# EDGES - Ingestion
RawTransactions  -> CleanTransactions
RawCustomers     -> CleanCustomers
RawProducts      -> CleanProducts

# EDGES - Dedup
CleanTransactions -> DedupTransactions
CleanCustomers    -> DedupCustomers

# EDGES - Normalize
RawTags           -> NormalizeTags
CleanProducts     -> NormalizeProducts

# EDGES - Lookup (main -> lookup ref)
DedupTransactions -> LookupCategory
RawCategories     -> LookupCategory
DedupTransactions -> LookupCustomer
DedupCustomers    -> LookupCustomer

# EDGES - Process
LookupCategory    -> EnrichedTx
LookupCustomer    -> EnrichedTx
EnrichedTx        -> TotalByCustomer
EnrichedTx        -> TotalByCategory

# EDGES - Sinks
EnrichedTx        -> Write_Enriched
TotalByCustomer   -> Write_ByCustomer
TotalByCategory   -> Write_ByCategory
