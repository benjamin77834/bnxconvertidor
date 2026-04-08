# BNX Sample — Simple ETL Pipeline

NODE RawOrders    : SOURCE
NODE RawCustomers : SOURCE

SUBGRAPH Clean {
  NODE CleanOrders    : TRANSFORM
  NODE CleanCustomers : TRANSFORM
}

SUBGRAPH Process {
  NODE OrdersWithCustomer : JOIN
  NODE TotalByCustomer    : TRANSFORM
}

NODE WriteReport : SINK

RawOrders     -> CleanOrders
RawCustomers  -> CleanCustomers
CleanOrders   -> OrdersWithCustomer
CleanCustomers -> OrdersWithCustomer
OrdersWithCustomer -> TotalByCustomer
TotalByCustomer -> WriteReport
