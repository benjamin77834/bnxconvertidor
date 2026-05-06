"""
🌊 BNX V54 GENERATED PYFLINK JOB
📅 Generated at: 2026-05-06 16:39:05.637094
📊 Nodes: 7
"""

from pyflink.table import EnvironmentSettings, TableEnvironment
from pyflink.datastream import StreamExecutionEnvironment
from pyflink.table import StreamTableEnvironment

# Initialize Flink environment
env = StreamExecutionEnvironment.get_execution_environment()
t_env = StreamTableEnvironment.create(env)

print("🌊 BNX PyFlink Job Started")

# =========================
# DAG EXECUTION V54 — FLINK
# =========================

# 🟢 SOURCE: ScanTransactions
t_env.execute_sql("""
  CREATE TABLE `ScanTransactions_source` (
    `data` STRING
  ) WITH (
    'connector' = 'filesystem',
    'path' = 's3://datalake/raw/transactions',
    'format' = 'parquet'
  )
""")
ScanTransactions = t_env.from_path("`ScanTransactions_source`")
t_env.create_temporary_view("`ScanTransactions`", ScanTransactions)
print("📂 SOURCE: ScanTransactions")

# 🟢 SOURCE: ScanCustomers
t_env.execute_sql("""
  CREATE TABLE `ScanCustomers_source` (
    `data` STRING
  ) WITH (
    'connector' = 'filesystem',
    'path' = 's3://datalake/raw/customers',
    'format' = 'csv',
    'csv.field-delimiter' = ',',
    'csv.ignore-parse-errors' = 'true'
  )
""")
ScanCustomers = t_env.from_path("`ScanCustomers_source`")
t_env.create_temporary_view("`ScanCustomers`", ScanCustomers)
print("📂 SOURCE: ScanCustomers")

# 🔹 TRANSFORM: CleanDates
t_env.execute_sql("""
  CREATE TEMPORARY VIEW `CleanDates` AS
  SELECT customer_id, amount, date_to_string(tx_date, "yyyy-MM-dd") as tx_str, year_of(tx_date) as tx_year, month_of(tx_date) as tx_month, date_diff(today(), tx_date) as days_ago FROM `ScanTransactions`
  WHERE amount > 0
""")
print("🔄 TRANSFORM: CleanDates")

# 🔗 JOIN: JoinData
t_env.execute_sql("""
  CREATE TEMPORARY VIEW `JoinData` AS
  SELECT * FROM `ScanCustomers` INNER JOIN `CleanDates`
  ON `ScanCustomers`.`customer_id` = `CleanDates`.`customer_id`
""")
print("🔗 JOIN: JoinData")

# 🔹 TRANSFORM: AggMonthly
t_env.execute_sql("""
  CREATE TEMPORARY VIEW `AggMonthly` AS
  SELECT customer_id, tx_year, tx_month, SUM(`amount`) AS `total_spent`, COUNT(`customer_id`) AS `tx_count`
  FROM `JoinData`
  GROUP BY customer_id, tx_year, tx_month
""")
print("🔄 TRANSFORM: AggMonthly")

# 🔀 PARTITION: PartByRegion
# Flink partitioning: configured via parallelism and key-by
# Partition keys: `region, tx_year`, num_partitions: 8
t_env.execute_sql("""CREATE TEMPORARY VIEW `PartByRegion` AS SELECT * FROM `AggMonthly`""")
print("🔀 PARTITION: PartByRegion")

# 🏁 SINK: WriteReport
t_env.execute_sql("""
  CREATE TABLE `WriteReport_sink` (
    `data` STRING
  ) WITH (
    'connector' = 'filesystem',
    'path' = 's3://datalake/curated/monthly_report',
    'format' = 'parquet'
  )
""")
t_env.execute_sql("INSERT INTO `WriteReport_sink` SELECT * FROM `PartByRegion`")
print("💾 SINK: WriteReport")

print("✅ BNX PyFlink Job Finished")
