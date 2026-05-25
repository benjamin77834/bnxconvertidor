class SinkResolver:

    def resolve(self, graph):

        print("? Resolving sinks...")

        outgoing = set()
        incoming = set()

        for s, d in graph.edges:
            outgoing.add(s)
            incoming.add(d)

        candidates = []

        for node in graph.nodes:

            node_type = graph.nodes[node].type

            if node not in outgoing and node_type in ["transform", "aggregate", "join"]:
                score = 0

                # scoring rules
                if node_type == "join":
                    score += 3
                if node_type == "aggregate":
                    score += 2
                if node_type == "transform":
                    score += 1

                candidates.append((node, score))

        if not candidates:
            raise Exception("No valid sinks found")

        # sort by score
        candidates.sort(key=lambda x: x[1], reverse=True)

        sinks = [c[0] for c in candidates]

        print("SINKS:", sinks)

        return sinks