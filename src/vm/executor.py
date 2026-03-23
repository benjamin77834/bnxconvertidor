class CatalystVM:

    def __init__(self, spark):
        self.spark = spark

    def execute(self, physical_plan):

        print("\n🚀 EXECUTING PHYSICAL PLAN...\n")

        for node in physical_plan:
            print(f"▶ Executing {node}")