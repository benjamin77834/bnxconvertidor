class IRBuilder:

    def __init__(self, dag):
        self.dag = dag

    def build(self):

        ir = {}

        for n in self.dag["nodes"]:
            ir[n["id"]] = {
                "id": n["id"],
                "type": n["type"],
                "expr": n["id"]  # base simple expression
            }

        return ir