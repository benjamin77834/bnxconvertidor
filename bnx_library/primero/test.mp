NODE RawOrders    : SOURCE
NODE RawCustomers : SOURCE
NODE CleanOrders   : TRANSFORM
NODE OrderJoin     : JOIN
NODE TotalSpend    : TRANSFORM
NODE WriteReport   : SINK

RawOrders     -> CleanOrders
RawCustomers  -> OrderJoin
CleanOrders   -> OrderJoin
OrderJoin     -> TotalSpend
TotalSpend    -> WriteReport
