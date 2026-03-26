class SubgraphResolver:

    def __init__(self):
        self.subgraphs = {}

    def register(self, name, graph):
        self.subgraphs[name] = graph

    def expand(self, nodes):
        expanded = {}

        for k, v in nodes.items():
            if v.type == "subgraph":
                sub = self.subgraphs[v.ref]

                for sk, sv in sub.nodes.items():
                    expanded[f"{k}.{sk}"] = sv
            else:
                expanded[k] = v

        return expanded