from pyspark.sql import SparkSession
from pyspark.sql.functions import *

spark = SparkSession.builder.appName('BNX_V12').getOrCreate()

customers = spark.read.parquet('customers.parquet')
select_node = None.selectExpr(['id', 'name'])
filter_node = customers.filter("age > 18")

# BNX V12 COMPLETE