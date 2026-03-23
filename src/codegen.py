def emit_glue(ctx):

    header = [
        "from pyspark.sql import SparkSession",
        "spark = SparkSession.builder.appName('GRAPH_VM').getOrCreate()\n"
    ]

    return "\n".join(header + ctx.code)