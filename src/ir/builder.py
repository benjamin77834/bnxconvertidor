class IRBuilder:

    def build(self, nodes):

        ir = []

        for n in nodes:

            ir.append({
                "id": n.id,
                "type": n.type,
                "inputs": n.inputs,
                "attrs": n.attrs
            })

        return ir