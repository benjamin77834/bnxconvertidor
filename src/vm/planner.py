from src.vm.instruction import Instruction

def build_instructions(plan, order):

    instructions = []

    for node_id in order:

        node = plan.nodes[node_id]

        inputs = [
            src for src, dsts in plan.edges.items()
            if node_id in dsts
        ]

        instructions.append(
            Instruction(
                id=node.id,
                op_type=node.type,
                attrs=node.attrs,
                inputs=inputs
            )
        )

    return instructions