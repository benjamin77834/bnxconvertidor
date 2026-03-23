from collections import defaultdict


class IRBuilder:
    """
    BNX IR Builder - DAG → Expression Compiler
    """

    def __init__(self, dag):
        self.dag = dag
        self.nodes = {n["id"]: n for n in dag["nodes"]}
        self.edges = dag["edges"]

        self.graph = defaultdict(list)

        for e in self.edges:
            if isinstance(e, (tuple, list)) and len(e) == 2:
                src, dst = e
                self.graph[dst].append(src)

        self.expr_cache = {}

    def build_expr(self, node_id):

        if node_id in self.expr_cache:
            return self.expr_cache[node_id]

        parents = self.graph.get(node_id, [])

        # INPUT NODE
        if len(parents) == 0:
            self.expr_cache[node_id] = node_id
            return node_id

        # SINGLE PARENT
        if len(parents) == 1:
            expr = self.build_expr(parents[0])
            self.expr_cache[node_id] = expr
            return expr

        # MULTI PARENT (JOIN)
        base = self.build_expr(parents[0])

        for p in parents[1:]:
            base = f"{base}.join({self.build_expr(p)}, 'inner')"

        self.expr_cache[node_id] = base
        return base

    def build(self):

        ir = {}

        for node_id in self.nodes:
            ir[node_id] = {
                "id": node_id,
                "type": self.nodes[node_id]["type"],
                "expr": self.build_expr(node_id)
            }

        return ir