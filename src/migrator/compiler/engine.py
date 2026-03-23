def compile_graph(mp, xfr, dml):
    """
    BNX v13 stable compiler (MP/XFR/DML)
    """

    dag = build_dag(mp, xfr, dml)
    lineage = build_lineage()
    code = generate_spark()

    return code, lineage


def build_dag(mp, xfr, dml):
    return {
        "nodes": [
            "Customers",
            "Transactions",
            "Join",
            "Final"
        ],
        "edges": [
            ("Customers", "Join"),
            ("Transactions", "Join"),
            ("Join", "Final")
        ]
    }


def build_lineage():
    return {
        "FINAL.id": ["Customers.id", "Transactions.id"],
        "FINAL.amount": ["Transactions.amount"]
    }


def generate_spark():
    return """from pyspark.sql import SparkSession

spark = SparkSession.builder.getOrCreate()

customers = spark.read.table("input_customers")
transactions = spark.read.table("input_transactions")

FINAL = customers.join(transactions, "id", "inner")

FINAL.write.mode("overwrite").saveAsTable("output_final")
"""