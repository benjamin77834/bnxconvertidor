from src.dag.engine import DAGEngine
from src.operators.join import JoinOp
from src.operators.write import WriteOp
from src.operators.filter import FilterOp
from src.operators.dedup import DedupOp
from src.operators.reformat import ReformatOp


class GlueV3Compiler:

    def __init__(self):

        self.dag = DAGEngine()

        self.ops = {
            "join": JoinOp(),
            "write": WriteOp(),
            "filter": FilterOp(),
            "dedup": DedupOp(),
            "reformat": ReformatOp()
        }

    def generate(self, nodes):

        ordered = self.dag.sort(nodes)

        code = []
        code.append("from pyspark.sql import SparkSession")
        code.append("from pyspark.sql.functions import *\n")
        code.append("spark = SparkSession.builder.appName('BNX_MVP').getOrCreate()\n")

        for n in ordered:

            if n.type == "scan":
                code.append(f"df_{n.id} = spark.read.parquet('{n.attrs['path']}')")

            elif n.type in self.ops:
                code.append(self.ops[n.type].compile(n))

            elif n.type == "write":
                code.append(f"df_{n.inputs[0]}.write.mode('overwrite').parquet('{n.attrs['path']}')")

        code.append("\nspark.stop()")

        return "\n".join(code)