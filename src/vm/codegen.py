def emit_spark(ctx):

    header = [
        "from pyspark.sql import SparkSession",
        "spark = SparkSession.builder.appName('CATASTAL_VM').getOrCreate()\n"
    ]

    return "\n".join(header + ctx.code)