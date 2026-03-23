def generate_spark(dag):

    code = []

    code.append("from pyspark.sql import SparkSession")
    code.append("from pyspark.sql.functions import *\n")
    code.append("spark = SparkSession.builder.getOrCreate()\n")

    # sources
    for n in dag["order"]:
        if "input" in n.lower():
            code.append(f"{n} = spark.read.table('input_{n}')")

    code.append("")

    # simple flow (solo 1 transformación tipo reformat)
    last = dag["order"][0]

    for n in dag["order"][1:]:
        last = n

    code.append(f"{last}.write.mode('overwrite').saveAsTable('output_{last}')")

    code.append("\nspark.stop()")

    return "\n".join(code)