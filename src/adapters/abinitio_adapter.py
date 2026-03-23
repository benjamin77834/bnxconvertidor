from src.ir.semantic_ir import SemanticNode


class AbInitioAdapter:

    def convert(self, graph):

        nodes = []

        for n in graph:

            if n["type"] == "input":
                nodes.append(
                    SemanticNode(
                        id=n["id"],
                        type="scan",
                        attrs={"path": n.get("path")}
                    )
                )

            elif n["type"] == "join":
                nodes.append(
                    SemanticNode(
                        id=n["id"],
                        type="join",
                        inputs=n["inputs"],
                        attrs={"keys": n.get("keys", ["id"])}
                    )
                )

            elif n["type"] == "output":
                nodes.append(
                    SemanticNode(
                        id=n["id"],
                        type="write",
                        inputs=n["inputs"],
                        attrs={"path": n.get("path")}
                    )
                )

        return nodes