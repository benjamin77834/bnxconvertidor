#!/usr/bin/env python
# Example Spark 2.x code for refactoring test
from pyspark import SparkContext
from pyspark.sql import SQLContext

sc = SparkContext()
sqlContext = SQLContext(sc)

# Read data
df = sqlContext.read.json("s3://data/input.json")
df2 = sqlContext.read.parquet("s3://data/customers")

# Register temp table (deprecated in Spark 3)
df.registerTempTable("orders")
df2.registerTempTable("customers")

# Query
result = sqlContext.sql("SELECT * FROM orders JOIN customers ON orders.cid = customers.id")

# Union (deprecated name)
combined = df.unionAll(df2)

# Write
result.write.mode("overwrite").parquet("s3://data/output")
