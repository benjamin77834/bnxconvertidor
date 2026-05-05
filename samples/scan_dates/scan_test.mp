NODE ScanTransactions : SOURCE
NODE ScanCustomers : SOURCE
NODE CleanDates : TRANSFORM
NODE JoinData : JOIN
NODE AggMonthly : TRANSFORM
NODE PartByRegion : PARTITION
NODE WriteReport : SINK

ScanTransactions -> CleanDates
ScanCustomers -> JoinData
CleanDates -> JoinData
JoinData -> AggMonthly
AggMonthly -> PartByRegion
PartByRegion -> WriteReport
