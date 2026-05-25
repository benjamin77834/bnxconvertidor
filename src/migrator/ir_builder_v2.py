from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional


# =========================
# SYMBOL TABLE
# =========================
class SymbolTable:
    def __init__(self):
        self.table = {}

    def register(self, raw_name: str, alias: str):
        self.table[raw_name] = alias

    def resolve(self, name: str) -> str:
        return self.table.get(name, name)


# =========================
# IR NODE (PORT-BASED)
# =========================
@dataclass
class Port:
    name: str
    schema: List[str]


@dataclass
class IRNode:
    id: str
    type: str
    inputs: List[str] = field(default_factory=list)
    outputs: List[Port] = field(default_factory=list)
    op: Optional[str] = None
    expression: Optional[str] = None
    group_by: Optional[List[str]] = None
    metrics: Optional[List[Dict[str, Any]]] = None
    join_type: Optional[str] = None
    keys: Optional[List[str]] = None
    source: Optional[str] = None


# =========================
# IR GRAPH
# =========================
class IRGraph:
    def __init__(self):
        self.nodes: Dict[str, IRNode] = {}
        self.edges: List[tuple] = []

    def add_node(self, node: IRNode):
        if node.id in self.nodes:
            raise Exception(f"Duplicate node id: {node.id}")
        self.nodes[node.id] = node

    def add_edge(self, src: str, dst: str):
        self.edges.append((src, dst))

    def get_node(self, node_id: str) -> IRNode:
        return self.nodes[node_id]


# =========================
# IR BUILDER v2
# =========================
class IRBuilderV2:
    def __init__(self):
        self.symbols = SymbolTable()
        self.graph = IRGraph()

    # -------------------------
    # Register inputs
    # -------------------------
    def register_input(self, raw_name: str, alias: str):
        self.symbols.register(raw_name, alias)

        node = IRNode(
            id=alias,
            type="input",
            source=raw_name,
            outputs=[Port(name="out", schema=["*"])]
        )

        self.graph.add_node(node)

    # -------------------------
    # Transform
    # -------------------------
    def add_transform(self, input_name: str, output_name: str, op: str = "select"):
        resolved_input = self.symbols.resolve(input_name)

        node = IRNode(
            id=output_name,
            type="transform",
            op=op,
            inputs=[f"{resolved_input}.out"],
            expression="*",
            outputs=[Port(name="out", schema=["*"])]
        )

        self.graph.add_node(node)
        self.graph.add_edge(resolved_input, output_name)

    # -------------------------
    # Aggregate
    # -------------------------
    def add_aggregate(self, input_name: str, output_name: str, group_by: List[str], metrics: List[Dict]):
        resolved_input = self.symbols.resolve(input_name)

        node = IRNode(
            id=output_name,
            type="aggregate",
            inputs=[f"{resolved_input}.out"],
            group_by=group_by,
            metrics=metrics,
            outputs=[Port(name="out", schema=["*"])]
        )

        self.graph.add_node(node)
        self.graph.add_edge(resolved_input, output_name)

    # -------------------------
    # Join
    # -------------------------
    def add_join(self, left: str, right: str, output_name: str, keys: List[str], join_type: str = "left"):
        l = self.symbols.resolve(left)
        r = self.symbols.resolve(right)

        node = IRNode(
            id=output_name,
            type="join",
            inputs=[f"{l}.out", f"{r}.out"],
            keys=keys,
            join_type=join_type,
            outputs=[Port(name="out", schema=["*"])]
        )

        self.graph.add_node(node)
        self.graph.add_edge(l, output_name)
        self.graph.add_edge(r, output_name)

    # -------------------------
    # VALIDATION (CR?TICO)
    # -------------------------
    def validate(self):
        # 1. no duplicates already handled
        # 2. check edges reference valid nodes
        for src, dst in self.graph.edges:
            if src not in self.graph.nodes:
                raise Exception(f"Invalid edge src: {src}")
            if dst not in self.graph.nodes:
                raise Exception(f"Invalid edge dst: {dst}")

        # 3. ensure DAG (basic check)
        visited = set()

        def visit(node):
            if node in visited:
                return
            visited.add(node)
            for s, d in self.graph.edges:
                if s == node:
                    visit(d)

        for n in self.graph.nodes:
            visit(n)

        return True

    # -------------------------
    # DEBUG PRINT
    # -------------------------
    def dump(self):
        print("\n=== IR NODES ===")
        for n in self.graph.nodes.values():
            print(n)

        print("\n=== EDGES ===")
        for e in self.graph.edges:
            print(e)
