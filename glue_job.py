from pyspark.sql import SparkSession
from pyspark.sql.functions import *

spark = SparkSession.builder.appName('BNX_V9').getOrCreate()

RawCustomers = spark.read.parquet('RawCustomers.parquet')
RawTransactions = spark.read.parquet('RawTransactions.parquet')
CleanCustomers = spark.read.parquet('RawCustomers.parquet').select('*')
JoinAll = spark.read.parquet('RawCustomers.parquet').select('*').join(spark.read.parquet('RawTransactions.parquet'), 'id', 'inner')
Final = spark.read.parquet('RawCustomers.parquet').select('*').join(spark.read.parquet('RawTransactions.parquet'), 'id', 'inner').select('*')

# BNX V9 PIPELINE COMPLETE