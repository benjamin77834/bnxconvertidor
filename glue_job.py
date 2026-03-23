from pyspark.sql import SparkSession
spark = SparkSession.builder.appName('BNX').getOrCreate()

Customers = spark.read.parquet('customers.parquet')
Transactions = spark.read.parquet('transactions.parquet')
Join = Customers.join(Transactions, 'id')
Join.write.mode('overwrite').parquet('s3://output/final/')
