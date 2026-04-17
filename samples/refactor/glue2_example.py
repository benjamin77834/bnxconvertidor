#!/usr/bin/env python
# Example Glue 2.0 code for refactoring test
import sys
from awsglue.transforms import *
from awsglue.utils import getResolvedOptions
from pyspark.context import SparkContext
from awsglue.context import GlueContext
from awsglue.dynamicframe import DynamicFrame

args = getResolvedOptions(sys.argv, ['JOB_NAME'])

sc = SparkContext()
glueContext = GlueContext(sc)
spark = glueContext.spark_session

# Read from catalog
datasource = glueContext.create_dynamic_frame.from_catalog(
    database="mydb", table_name="orders"
)

# Convert to DataFrame
df = datasource.toDF()
df.registerTempTable("orders")

# Query with SQLContext
sqlContext = SQLContext(sc)
result = sqlContext.sql("SELECT * FROM orders WHERE amount > 100")

# Union deprecated
combined = df.unionAll(result)

# Write
output = DynamicFrame.fromDF(combined, glueContext, "output")
glueContext.write_dynamic_frame.from_options(
    frame=output,
    connection_type="s3",
    connection_options={"path": "s3://output/data"},
    format="parquet"
)
