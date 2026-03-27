# src/accuracy.py
"""
Mide la exactitud de la transformación del grafo original al código generado.
Compara nodos, edges, reglas XFR y join keys.
"""


def compute_accuracy(dag, xfr_rules, dml_schema=None):
    """
    Retorna un dict con métricas de exactitud:
    - total_nodes, resolved_nodes, node_accuracy
    - total_edges, resolved_edges, edge_accuracy
    - total_transforms, resolved_transforms, transform_accuracy
    - total_joins, resolved_joins, join_accuracy
    - overall_accuracy
    - details: lista de issues por nodo
    """
    details = []
    total_nodes = len(dag.execution_order)
    resolved_nodes = 0
    total_edges = 0
    resolved_edges = 0
    total_transforms = 0
    resolved_transforms = 0
    total_joins = 0
    resolved_joins = 0

    for node in dag.execution_order:
        ntype = node.type.upper()
        rule = xfr_rules.get(node.id.lower()) or xfr_rules.get(node.name.lower())
        issues = []

        # Nodo resuelto = tiene padre (o es SOURCE) y tiene regla (si aplica)
        if ntype == "SOURCE":
            resolved_nodes += 1

        elif ntype in ("TRANSFORM", "XFR"):
            total_transforms += 1
            if not node.parents:
                issues.append("no parent")
            elif rule and (rule.get("select") or rule.get("group_by")):
                resolved_transforms += 1
                resolved_nodes += 1
            elif node.parents:
                # Tiene padre pero sin regla → selectExpr("*")
                issues.append("no XFR rule — passthrough")
                resolved_nodes += 1  # funcional pero sin lógica
            else:
                issues.append("orphan node")

        elif ntype == "JOIN":
            total_joins += 1
            if len(node.parents) >= 2:
                if rule and rule.get("join_key"):
                    resolved_joins += 1
                    resolved_nodes += 1
                else:
                    issues.append("no join_key — using default 'id'")
                    resolved_nodes += 1  # funcional pero con default
            else:
                issues.append(f"needs 2+ parents, has {len(node.parents)}")

        elif ntype == "SINK":
            if node.parents:
                resolved_nodes += 1
            else:
                issues.append("no parent — nothing to write")

        else:
            if node.parents:
                resolved_nodes += 1
            else:
                issues.append("unknown type, no parents")

        # Edges: contar children resueltos
        for child_id in node.children:
            total_edges += 1
            if child_id in dag.nodes:
                resolved_edges += 1
            else:
                issues.append(f"edge to '{child_id}' — target not found")

        if issues:
            details.append({"node": node.name, "type": ntype, "issues": issues})

    # Calcular porcentajes
    node_acc = (resolved_nodes / total_nodes * 100) if total_nodes else 100
    edge_acc = (resolved_edges / total_edges * 100) if total_edges else 100
    xfr_acc = (resolved_transforms / total_transforms * 100) if total_transforms else 100
    join_acc = (resolved_joins / total_joins * 100) if total_joins else 100

    # Overall: promedio ponderado
    weights = [
        (node_acc, 0.3),
        (edge_acc, 0.2),
        (xfr_acc, 0.3),
        (join_acc, 0.2),
    ]
    overall = sum(v * w for v, w in weights)

    return {
        "total_nodes": total_nodes,
        "resolved_nodes": resolved_nodes,
        "node_accuracy": round(node_acc, 1),
        "total_edges": total_edges,
        "resolved_edges": resolved_edges,
        "edge_accuracy": round(edge_acc, 1),
        "total_transforms": total_transforms,
        "resolved_transforms": resolved_transforms,
        "transform_accuracy": round(xfr_acc, 1),
        "total_joins": total_joins,
        "resolved_joins": resolved_joins,
        "join_accuracy": round(join_acc, 1),
        "overall_accuracy": round(overall, 1),
        "details": details,
    }
