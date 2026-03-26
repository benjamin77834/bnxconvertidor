"""
🚀 BNX V54 GENERATED GLUE JOB
📅 Generated at: 2026-03-26 09:08:08.420379
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

# 🔹 DML Node: RawCustomers_______Read__s3
RawCustomers_______Read__s3_df = None  # no parents
print("🔄 DML: RawCustomers_______Read__s3")

# 🔹 DML Node: RawTransactions____Read__s3
RawTransactions____Read__s3_df = None  # no parents
print("🔄 DML: RawTransactions____Read__s3")

# 🔹 DML Node: RawProducts________Read__s3
RawProducts________Read__s3_df = None  # no parents
print("🔄 DML: RawProducts________Read__s3")

# 🔹 DML Node: RawRegions_________Read__s3
RawRegions_________Read__s3_df = None  # no parents
print("🔄 DML: RawRegions_________Read__s3")

# 🔹 DML Node: RawCampaigns_______Read__s3
RawCampaigns_______Read__s3_df = None  # no parents
print("🔄 DML: RawCampaigns_______Read__s3")

# 🔹 XFR Node: CleanCustomers___Transform_RawCustomers__rules__
CleanCustomers___Transform_RawCustomers__rules___df = spark.read.format("parquet").load("s3://bnx/raw/cleancustomers___transform_rawcustomers__rules__")
print("📥 XFR: CleanCustomers___Transform_RawCustomers__rules__")

# 🔹 XFR Node: _trim_fields__
_trim_fields___df = spark.read.format("parquet").load("s3://bnx/raw/_trim_fields__")
print("📥 XFR: _trim_fields__")

# 🔹 XFR Node: _fill_missing_country__MX____
_fill_missing_country__MX_____df = spark.read.format("parquet").load("s3://bnx/raw/_fill_missing_country__mx____")
print("📥 XFR: _fill_missing_country__MX____")

# 🔹 XFR Node: _uppercase_name__
_uppercase_name___df = spark.read.format("parquet").load("s3://bnx/raw/_uppercase_name__")
print("📥 XFR: _uppercase_name__")

# 🔹 XFR Node: __
___df = spark.read.format("parquet").load("s3://bnx/raw/__")
print("📥 XFR: __")

# 🔹 XFR Node: CleanTransactions___Transform_RawTransactions__rules__
CleanTransactions___Transform_RawTransactions__rules___df = spark.read.format("parquet").load("s3://bnx/raw/cleantransactions___transform_rawtransactions__rules__")
print("📥 XFR: CleanTransactions___Transform_RawTransactions__rules__")

# 🔹 XFR Node: _parse_dates_transaction_date___
_parse_dates_transaction_date____df = spark.read.format("parquet").load("s3://bnx/raw/_parse_dates_transaction_date___")
print("📥 XFR: _parse_dates_transaction_date___")

# 🔹 XFR Node: _filter_amount___0__
_filter_amount___0___df = spark.read.format("parquet").load("s3://bnx/raw/_filter_amount___0__")
print("📥 XFR: _filter_amount___0__")

# 🔹 XFR Node: CleanProducts___Transform_RawProducts__rules__
CleanProducts___Transform_RawProducts__rules___df = spark.read.format("parquet").load("s3://bnx/raw/cleanproducts___transform_rawproducts__rules__")
print("📥 XFR: CleanProducts___Transform_RawProducts__rules__")

# 🔹 XFR Node: _standardize_category__
_standardize_category___df = spark.read.format("parquet").load("s3://bnx/raw/_standardize_category__")
print("📥 XFR: _standardize_category__")

# 🔹 XFR Node: _uppercase_product_name__
_uppercase_product_name___df = spark.read.format("parquet").load("s3://bnx/raw/_uppercase_product_name__")
print("📥 XFR: _uppercase_product_name__")

# 🔹 XFR Node: CustomersWithRegion___Join_CleanCustomers__RawRegions__keys___region_id___
CustomersWithRegion___Join_CleanCustomers__RawRegions__keys___region_id____df = spark.read.format("parquet").load("s3://bnx/raw/customerswithregion___join_cleancustomers__rawregions__keys___region_id___")
print("📥 XFR: CustomersWithRegion___Join_CleanCustomers__RawRegions__keys___region_id___")

# 🔹 XFR Node: CustomerAggregates___SubGraph__CustomerAggregates____
CustomerAggregates___SubGraph__CustomerAggregates_____df = spark.read.format("parquet").load("s3://bnx/raw/customeraggregates___subgraph__customeraggregates____")
print("📥 XFR: CustomerAggregates___SubGraph__CustomerAggregates____")

# 🔹 DML Node: TotalSpent___Aggregate_CleanTransactions__group_by___customer_id____agg___amount_
TotalSpent___Aggregate_CleanTransactions__group_by___customer_id____agg___amount__df = None  # no parents
print("🔄 DML: TotalSpent___Aggregate_CleanTransactions__group_by___customer_id____agg___amount_")

# 🔹 DML Node: TxCount_____Aggregate_CleanTransactions__group_by___customer_id____agg___transaction_id_
TxCount_____Aggregate_CleanTransactions__group_by___customer_id____agg___transaction_id__df = None  # no parents
print("🔄 DML: TxCount_____Aggregate_CleanTransactions__group_by___customer_id____agg___transaction_id_")

# 🔹 XFR Node: MonthlyAvg___SubGraph__MonthlyAvg____
MonthlyAvg___SubGraph__MonthlyAvg_____df = spark.read.format("parquet").load("s3://bnx/raw/monthlyavg___subgraph__monthlyavg____")
print("📥 XFR: MonthlyAvg___SubGraph__MonthlyAvg____")

# 🔹 XFR Node: TxByMonth___Transform_CleanTransactions__rules___extract_month_transaction_date____
TxByMonth___Transform_CleanTransactions__rules___extract_month_transaction_date_____df = spark.read.format("parquet").load("s3://bnx/raw/txbymonth___transform_cleantransactions__rules___extract_month_transaction_date____")
print("📥 XFR: TxByMonth___Transform_CleanTransactions__rules___extract_month_transaction_date____")

# 🔹 DML Node: AvgMonthly___Aggregate_TxByMonth__group_by___customer_id___month____agg___amount_
AvgMonthly___Aggregate_TxByMonth__group_by___customer_id___month____agg___amount__df = None  # no parents
print("🔄 DML: AvgMonthly___Aggregate_TxByMonth__group_by___customer_id___month____agg___amount_")

# 🔹 XFR Node: Output___AvgMonthly
Output___AvgMonthly_df = spark.read.format("parquet").load("s3://bnx/raw/output___avgmonthly")
print("📥 XFR: Output___AvgMonthly")

# 🔹 XFR Node: _
__df = spark.read.format("parquet").load("s3://bnx/raw/_")
print("📥 XFR: _")

# 🔹 XFR Node: MergeAgg1___Join_TotalSpent__TxCount__keys___customer_id___
MergeAgg1___Join_TotalSpent__TxCount__keys___customer_id____df = spark.read.format("parquet").load("s3://bnx/raw/mergeagg1___join_totalspent__txcount__keys___customer_id___")
print("📥 XFR: MergeAgg1___Join_TotalSpent__TxCount__keys___customer_id___")

# 🔹 XFR Node: MergeAgg2___Join_MergeAgg1__MonthlyAvg_Output__keys___customer_id____join_type__left__
MergeAgg2___Join_MergeAgg1__MonthlyAvg_Output__keys___customer_id____join_type__left___df = spark.read.format("parquet").load("s3://bnx/raw/mergeagg2___join_mergeagg1__monthlyavg_output__keys___customer_id____join_type__left__")
print("📥 XFR: MergeAgg2___Join_MergeAgg1__MonthlyAvg_Output__keys___customer_id____join_type__left__")

# 🔹 XFR Node: Output___MergeAgg2
Output___MergeAgg2_df = spark.read.format("parquet").load("s3://bnx/raw/output___mergeagg2")
print("📥 XFR: Output___MergeAgg2")

# 🔹 XFR Node: TopProducts___SubGraph__TopProducts____
TopProducts___SubGraph__TopProducts_____df = spark.read.format("parquet").load("s3://bnx/raw/topproducts___subgraph__topproducts____")
print("📥 XFR: TopProducts___SubGraph__TopProducts____")

# 🔹 DML Node: ProductSales___Aggregate_CleanTransactions__group_by___product_id____agg___amount_
ProductSales___Aggregate_CleanTransactions__group_by___product_id____agg___amount__df = None  # no parents
print("🔄 DML: ProductSales___Aggregate_CleanTransactions__group_by___product_id____agg___amount_")

# 🔹 XFR Node: ProductInfo____Join_ProductSales__CleanProducts__keys___product_id___
ProductInfo____Join_ProductSales__CleanProducts__keys___product_id____df = spark.read.format("parquet").load("s3://bnx/raw/productinfo____join_productsales__cleanproducts__keys___product_id___")
print("📥 XFR: ProductInfo____Join_ProductSales__CleanProducts__keys___product_id___")

# 🔹 XFR Node: FilterTop______Transform_ProductInfo__rules___top_n_10__amount_____
FilterTop______Transform_ProductInfo__rules___top_n_10__amount______df = spark.read.format("parquet").load("s3://bnx/raw/filtertop______transform_productinfo__rules___top_n_10__amount_____")
print("📥 XFR: FilterTop______Transform_ProductInfo__rules___top_n_10__amount_____")

# 🔹 XFR Node: CategorySplit___SubGraph__CategorySplit____
CategorySplit___SubGraph__CategorySplit_____df = spark.read.format("parquet").load("s3://bnx/raw/categorysplit___subgraph__categorysplit____")
print("📥 XFR: CategorySplit___SubGraph__CategorySplit____")

# 🔹 XFR Node: SplitByCategory___Transform_FilterTop__rules___split_by_category____
SplitByCategory___Transform_FilterTop__rules___split_by_category_____df = spark.read.format("parquet").load("s3://bnx/raw/splitbycategory___transform_filtertop__rules___split_by_category____")
print("📥 XFR: SplitByCategory___Transform_FilterTop__rules___split_by_category____")

# 🔹 XFR Node: Output___SplitByCategory
Output___SplitByCategory_df = spark.read.format("parquet").load("s3://bnx/raw/output___splitbycategory")
print("📥 XFR: Output___SplitByCategory")

# 🔹 XFR Node: Output___CategorySplit_Output
Output___CategorySplit_Output_df = spark.read.format("parquet").load("s3://bnx/raw/output___categorysplit_output")
print("📥 XFR: Output___CategorySplit_Output")

# 🔹 XFR Node: ActiveCampaigns___SubGraph__ActiveCampaigns____
ActiveCampaigns___SubGraph__ActiveCampaigns_____df = spark.read.format("parquet").load("s3://bnx/raw/activecampaigns___subgraph__activecampaigns____")
print("📥 XFR: ActiveCampaigns___SubGraph__ActiveCampaigns____")

# 🔹 XFR Node: FilterCampaigns___Transform_RawCampaigns__rules___filter_active_true____
FilterCampaigns___Transform_RawCampaigns__rules___filter_active_true_____df = spark.read.format("parquet").load("s3://bnx/raw/filtercampaigns___transform_rawcampaigns__rules___filter_active_true____")
print("📥 XFR: FilterCampaigns___Transform_RawCampaigns__rules___filter_active_true____")

# 🔹 XFR Node: JoinWithCustomers___Join_FilterCampaigns__CleanCustomers__keys___customer_id___
JoinWithCustomers___Join_FilterCampaigns__CleanCustomers__keys___customer_id____df = spark.read.format("parquet").load("s3://bnx/raw/joinwithcustomers___join_filtercampaigns__cleancustomers__keys___customer_id___")
print("📥 XFR: JoinWithCustomers___Join_FilterCampaigns__CleanCustomers__keys___customer_id___")

# 🔹 XFR Node: RegionalCount___SubGraph__RegionalCount____
RegionalCount___SubGraph__RegionalCount_____df = spark.read.format("parquet").load("s3://bnx/raw/regionalcount___subgraph__regionalcount____")
print("📥 XFR: RegionalCount___SubGraph__RegionalCount____")

# 🔹 DML Node: CountByRegion___Aggregate_JoinWithCustomers__group_by___region_id____agg___campaign_id_
CountByRegion___Aggregate_JoinWithCustomers__group_by___region_id____agg___campaign_id__df = None  # no parents
print("🔄 DML: CountByRegion___Aggregate_JoinWithCustomers__group_by___region_id____agg___campaign_id_")

# 🔹 XFR Node: Output___CountByRegion
Output___CountByRegion_df = spark.read.format("parquet").load("s3://bnx/raw/output___countbyregion")
print("📥 XFR: Output___CountByRegion")

# 🔹 XFR Node: Output___RegionalCount_Output
Output___RegionalCount_Output_df = spark.read.format("parquet").load("s3://bnx/raw/output___regionalcount_output")
print("📥 XFR: Output___RegionalCount_Output")

# 🔹 XFR Node: CustomerReport___Join_CustomersWithRegion__CustomerAggregates_Output__keys___customer_id___
CustomerReport___Join_CustomersWithRegion__CustomerAggregates_Output__keys___customer_id____df = spark.read.format("parquet").load("s3://bnx/raw/customerreport___join_customerswithregion__customeraggregates_output__keys___customer_id___")
print("📥 XFR: CustomerReport___Join_CustomersWithRegion__CustomerAggregates_Output__keys___customer_id___")

# 🔹 XFR Node: CustomerReport2___Join_CustomerReport__TopProducts_Output__keys___product_id____join_type__left__
CustomerReport2___Join_CustomerReport__TopProducts_Output__keys___product_id____join_type__left___df = spark.read.format("parquet").load("s3://bnx/raw/customerreport2___join_customerreport__topproducts_output__keys___product_id____join_type__left__")
print("📥 XFR: CustomerReport2___Join_CustomerReport__TopProducts_Output__keys___product_id____join_type__left__")

# 🔹 XFR Node: FinalReport___Join_CustomerReport2__ActiveCampaigns_Output__keys___region_id____join_type__left__
FinalReport___Join_CustomerReport2__ActiveCampaigns_Output__keys___region_id____join_type__left___df = spark.read.format("parquet").load("s3://bnx/raw/finalreport___join_customerreport2__activecampaigns_output__keys___region_id____join_type__left__")
print("📥 XFR: FinalReport___Join_CustomerReport2__ActiveCampaigns_Output__keys___region_id____join_type__left__")

# 🔹 DML Node: Write_FinalReport___s3
Write_FinalReport___s3_df = None  # no parents
print("🔄 DML: Write_FinalReport___s3")

# 🔹 DML Node: Write_TopProducts_Output___s3
Write_TopProducts_Output___s3_df = None  # no parents
print("🔄 DML: Write_TopProducts_Output___s3")

# 🔹 DML Node: Write_ActiveCampaigns_Output___s3
Write_ActiveCampaigns_Output___s3_df = None  # no parents
print("🔄 DML: Write_ActiveCampaigns_Output___s3")

print("✅ BNX Glue Job V54 Finished")
