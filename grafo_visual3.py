# grafo_visual3.py
import argparse
from graphviz import Digraph
from src.mp_parser import parse_mp_ast
from src.dag.builder import build_dag

TYPE_STYLE = {
    "SOURCE":    {"shape": "ellipse",   "color": "#90EE90"},  # verde
    "TRANSFORM": {"shape": "box",       "color": "#ADD8E6"},  # azul
    "XFR":       {"shape": "box",       "color": "#ADD8E6"},  # azul
    "JOIN":      {"shape": "diamond",   "color": "#FFD700"},  # amarillo
    "SINK":      {"shape": "ellipse",   "color": "#FFA07A"},  # salm?n
}
DEFAULT_STYLE = {"shape": "box", "color": "#EEEEEE"}

SUBGRAPH_COLORS = {
    "Ingestion":        "#FFF9C4",
    "CustomerPipeline": "#E3F2FD",
    "OrderPipeline":    "#F3E5F5",
    "ProductPipeline":  "#E8F5E9",
    "ReturnsPipeline":  "#FCE4EC",
    "CampaignPipeline": "#FFF3E0",
    "FinalReport":      "#ECEFF1",
}


def build_visual(mp_path, output_file):
    ast = parse_mp_ast(mp_path)
    dag = build_dag(ast)
    subgraphs = ast.get("subgraphs", {})

    # Mapa node_id -> subgraph
    node_subgraph = {}
    for sg_name, node_ids in subgraphs.items():
        for nid in node_ids:
            node_subgraph[nid] = sg_name

    dot = Digraph("BNX_DAG", format="png")
    dot.attr(rankdir="LR")
    dot.attr(size="36,20")
    dot.attr(dpi="180")
    dot.attr(nodesep="0.5")
    dot.attr(ranksep="1.4")
    dot.attr(splines="ortho")
    dot.attr(fontname="Helvetica")

    # Nodos sin subgraph (sources y sinks)
    for node in dag.execution_order:
        if node.id not in node_subgraph:
            ntype = node.type.upper()
            style = TYPE_STYLE.get(ntype, DEFAULT_STYLE)
            dot.node(
                node.id, node.name,
                shape=style["shape"],
                style="filled",
                fillcolor=style["color"],
                fontname="Helvetica",
                fontsize="11",
            )

    # Subgraphs como clusters
    for sg_name, node_ids in subgraphs.items():
        bg = SUBGRAPH_COLORS.get(sg_name, "#F5F5F5")
        with dot.subgraph(name=f"cluster_{sg_name}") as sg:
            sg.attr(label=sg_name, style="filled", fillcolor=bg,
                    fontname="Helvetica Bold", fontsize="13", color="#999999")
            for nid in node_ids:
                if nid not in dag.nodes:
                    continue
                node = dag.nodes[nid]
                ntype = node.type.upper()
                style = TYPE_STYLE.get(ntype, DEFAULT_STYLE)
                sg.node(
                    node.id, node.name,
                    shape=style["shape"],
                    style="filled",
                    fillcolor=style["color"],
                    fontname="Helvetica",
                    fontsize="11",
                )

    # Edges reales del DAG
    for node in dag.execution_order:
        for child_id in node.children:
            dot.edge(node.id, child_id)

    dot.render(output_file, view=True)
    print(f"? DAG generado: {output_file}.png")
    print(f"   Nodos : {len(dag.nodes)}")
    print(f"   Edges : {sum(len(n.children) for n in dag.execution_order)}")
    print(f"   Clusters: {list(subgraphs.keys())}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--mp", required=True)
    parser.add_argument("--output", default="BNX_GlueJob_DAG")
    args = parser.parse_args()
    build_visual(args.mp, args.output)
