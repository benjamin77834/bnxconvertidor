class DAGValidator:

    def validate(self, graph):

        print("[?] Validating DAG...")

        errors = []

        # detect orphan nodes
        connected = set()
        for s, d in graph.edges:
            connected.add(s)
            connected.add(d)

        for n in graph.nodes:
            if n not in connected and graph.nodes[n].type != "input":
                errors.append(f"Orphan node: {n}")

        # detect cycles (simple check)
        visited = set()
        stack = set()

        def dfs(node):
            if node in stack:
                return True
            if node in visited:
                return False

            visited.add(node)
            stack.add(node)

            for s, d in graph.edges:
                if s == node:
                    if dfs(d):
                        return True

            stack.remove(node)
            return False

        for n in graph.nodes:
            if dfs(n):
                errors.append("Cycle detected in DAG")
                break

        if errors:
            for e in errors:
                print("?", e)
            raise Exception("DAG validation failed")

        print("[ok] DAG valid")