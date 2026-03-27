# ============================================================
# BNX Small Test - Simple ETL Pipeline
# ============================================================

NODE RawSales     : SOURCE
NODE RawClients   : SOURCE

SUBGRAPH Clean {
  NODE CleanSales   : TRANSFORM
  NODE CleanClients : TRANSFORM
}

SUBGRAPH Process {
  NODE SalesWithClient : JOIN
  NODE TotalByClient   : TRANSFORM
}

NODE Write_Report : SINK

RawSales    -> CleanSales
RawClients  -> CleanClients
CleanSales  -> SalesWithClient
CleanClients -> SalesWithClient
SalesWithClient -> TotalByClient
TotalByClient -> Write_Report
