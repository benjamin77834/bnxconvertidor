from src.operators.registry import OPERATORS


class GraphInterpreter:

    def __init__(self, plan):
        self.plan = plan

    def get_inputs(self, node_id):

        return [
            src for src, dsts in self.plan.edges.items()
            if node_id in dsts
        ]

    def run(self, order):

        from src.context import ExecutionContext

        ctx = ExecutionContext()

        for node_id in order:

            node = self.plan.nodes[node_id]

            operator = OPERATORS.get(node.type)

            if not operator:
                raise Exception(f"Unknown operator: {node.type}")

            inputs = self.get_inputs(node_id)

            operator.execute(node, inputs, ctx)

        return ctx