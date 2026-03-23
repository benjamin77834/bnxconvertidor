from src.ir.component import Component


class AbInitioParser:

    def parse(self, graph):

        return [
            Component(
                id=node["id"],
                type=node["type"],
                inputs=node.get("inputs", []),
                attrs=node.get("attrs", {})
            )
            for node in graph
        ]