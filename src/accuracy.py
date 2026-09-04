# src/accuracy.py
"""
Mide la exactitud de la transformaci?n del grafo original al c?digo generado.
Compara nodos, edges, reglas XFR y join keys.
"""


def compute_accuracy(dag, xfr_rules, dml_schema=None):
    """
    Retorna un dict con m?tricas de exactitud:
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

    # Nombres de componente Ab Initio que son PASSTHROUGH por diseno: no
    # transforman valores (copian el registro tal cual o solo redefinen el
    # formato/comprimen). No deben penalizar el accuracy de transforms: no
    # tienen logica que traducir. Se detectan por el nombre del nodo.
    _PASSTHROUGH_HINTS = (
        "redefine", "replicate", "gzip", "gunzip", "compress", "gather",
        "concatenate", "copy", "broadcast", "partition", "interleave", "merge",
    )

    def _is_passthrough_transform(node, rule):
        # Un transform sin regla y cuyo nombre es un componente de copia/formato
        # es passthrough legitimo (equivalente a select *), no un transform fallido.
        if rule:
            return False
        name = (node.name or "").lower()
        return any(h in name for h in _PASSTHROUGH_HINTS)

    def _rule_has_logic(rule):
        """True si la regla XFR contiene logica de transformacion real traducible.

        Antes solo se contaba select/group_by, dejando fuera los Reformat con DML
        embebido (raw_transform/dml_fields), los generadores (literals/
        transform_exprs), los Sort (sort_by) y los filtros (where) — que SI se
        traducen a codigo. Esto subvaloraba el accuracy de grafos en formato GDE
        nativo (donde el DML viene embebido, no en un .xfr externo).
        """
        if not rule:
            return False
        for key in ("select", "group_by", "raw_transform", "dml_fields",
                    "transform_exprs", "literals", "sort_by", "where",
                    "record_fields", "transform"):
            v = rule.get(key)
            if v:
                # 'select' == '*' es passthrough, no cuenta como logica.
                if key == "select" and str(v).strip() == "*":
                    continue
                return True
        return False

    for node in dag.execution_order:
        ntype = node.type.upper()
        rule = xfr_rules.get(node.id.lower()) or xfr_rules.get(node.name.lower())
        issues = []

        # Nodo resuelto = tiene padre (o es SOURCE) y tiene regla (si aplica)
        if ntype == "SOURCE":
            resolved_nodes += 1

        elif ntype in ("TRANSFORM", "XFR"):
            # Passthrough por diseno (Redefine/Replicate/GZip/Copy/Gather...):
            # nodo funcional que no transforma valores. Cuenta como nodo resuelto
            # pero NO entra al denominador de transforms-con-logica (no hay nada
            # que traducir, penalizarlo distorsiona la metrica).
            if _is_passthrough_transform(node, rule):
                if node.parents:
                    resolved_nodes += 1
                else:
                    issues.append("passthrough sin padre")
            else:
                total_transforms += 1
                if not node.parents and not _rule_has_logic(rule):
                    # Sin padre y sin logica autocontenida: huerfano real.
                    issues.append("no parent")
                elif _rule_has_logic(rule):
                    # Tiene DML/sort/filtro/generador traducido: transform resuelto.
                    resolved_transforms += 1
                    resolved_nodes += 1
                elif node.parents:
                    # Tiene padre pero sin regla -> selectExpr("*") (passthrough
                    # implicito). Funcional, pero no cuenta como logica traducida.
                    issues.append("no XFR rule -> passthrough")
                    resolved_nodes += 1
                else:
                    issues.append("orphan node")

        elif ntype == "JOIN":
            total_joins += 1
            if len(node.parents) >= 2:
                if rule and rule.get("join_key"):
                    resolved_joins += 1
                    resolved_nodes += 1
                else:
                    issues.append("no join_key ? using default 'id'")
                    resolved_nodes += 1  # funcional pero con default
            else:
                issues.append(f"needs 2+ parents, has {len(node.parents)}")

        elif ntype == "SINK":
            if node.parents:
                resolved_nodes += 1
            else:
                issues.append("no parent ? nothing to write")

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
                issues.append(f"edge to '{child_id}' ? target not found")

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
