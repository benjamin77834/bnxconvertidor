# src/visualizer.py
"""
Visualizador de grafos BNX en Python puro.
Genera un HTML interactivo con el DAG y el flujo de ejecución.
No requiere React ni Node.js — solo Python + browser.
"""
import os
from datetime import datetime


TYPE_COLOR = {
    'SOURCE': '#22c55e', 'TRANSFORM': '#6366f1', 'JOIN': '#f59e0b',
    'DEDUP': '#06b6d4', 'NORMALIZE': '#a855f7', 'LOOKUP': '#ec4899',
    'CONCATENATE': '#14b8a6', 'GATHER': '#8b5cf6', 'PARTITION': '#f97316',
    'FILTER': '#eab308', 'SINK': '#ef4444', 'XFR': '#6366f1',
}

TYPE_ICON = {
    'SOURCE': '📂', 'TRANSFORM': '🔄', 'JOIN': '🔗', 'DEDUP': '🧹',
    'NORMALIZE': '📐', 'LOOKUP': '🔍', 'CONCATENATE': '🔗', 'GATHER': '📥',
    'PARTITION': '🔀', 'FILTER': '🔽', 'SINK': '💾', 'XFR': '🔄',
}


def visualize_dag(dag, output_path="dag_view.html", xfr_rules=None, target="glue"):
    """Generate an interactive HTML visualization of the DAG."""
    xfr_rules = xfr_rules or {}
    nodes = dag.execution_order
    
    # Build level map for layout
    level_map = {}
    for node in nodes:
        depth = 0
        for pid in node.parents:
            if pid in level_map:
                depth = max(depth, level_map[pid] + 1)
        level_map[node.id] = depth

    # Group by level
    levels = {}
    for node in nodes:
        d = level_map[node.id]
        if d not in levels:
            levels[d] = []
        levels[d].append(node)

    # Generate node positions
    node_positions = {}
    for depth, level_nodes in levels.items():
        for i, node in enumerate(level_nodes):
            x = depth * 250 + 50
            y = i * 100 + 50 + (200 - len(level_nodes) * 50)
            node_positions[node.id] = (x, y)

    # Build HTML
    html = f"""<!DOCTYPE html>
<html>
<head>
<title>BNX DAG Viewer — {len(nodes)} nodes</title>
<style>
body {{ margin: 0; background: #0a1628; color: #e8edf5; font-family: -apple-system, sans-serif; }}
.header {{ padding: 16px 24px; background: #122448; border-bottom: 1px solid #1e3a6e; display: flex; align-items: center; gap: 16px; }}
.header h1 {{ margin: 0; font-size: 20px; }}
.badge {{ font-size: 12px; padding: 3px 10px; border-radius: 99px; background: #1a73e820; color: #1a73e8; border: 1px solid #1a73e840; }}
.container {{ display: flex; height: calc(100vh - 60px); }}
.canvas {{ flex: 1; position: relative; overflow: auto; }}
.sidebar {{ width: 350px; background: #0f1f3d; border-left: 1px solid #1e3a6e; overflow-y: auto; padding: 16px; }}
.node {{ position: absolute; padding: 10px 16px; border-radius: 8px; text-align: center; cursor: pointer; min-width: 120px; font-size: 13px; transition: transform 0.2s; }}
.node:hover {{ transform: scale(1.05); z-index: 10; }}
.node-name {{ font-weight: 600; margin-top: 4px; }}
.node-type {{ font-size: 10px; font-weight: 600; opacity: 0.8; }}
svg {{ position: absolute; top: 0; left: 0; width: 100%; height: 100%; pointer-events: none; }}
.edge {{ stroke-width: 2; fill: none; marker-end: url(#arrow); }}
.section {{ margin-bottom: 20px; }}
.section-title {{ font-size: 13px; color: #8fa3c4; text-transform: uppercase; letter-spacing: 1px; margin-bottom: 8px; }}
.exec-item {{ padding: 8px 10px; border-radius: 6px; margin-bottom: 4px; font-size: 12px; display: flex; align-items: center; gap: 8px; }}
.exec-num {{ width: 24px; height: 24px; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-size: 11px; font-weight: 700; }}
.code-block {{ background: #081220; border: 1px solid #1e3a6e; border-radius: 8px; padding: 12px; font-family: monospace; font-size: 11px; white-space: pre-wrap; overflow-x: auto; color: #8fa3c4; max-height: 300px; overflow-y: auto; }}
.target-badge {{ padding: 4px 12px; border-radius: 6px; font-size: 12px; font-weight: 600; }}
</style>
</head>
<body>
<div class="header">
  <h1>🚀 BNX DAG Viewer</h1>
  <span class="badge">V54</span>
  <span class="badge">{len(nodes)} nodes · {sum(len(n.children) for n in nodes)} edges</span>
  <span class="target-badge" style="background: {'#22c55e20' if target == 'glue' else '#6366f120' if target == 'spark' else '#06b6d420'}; color: {'#22c55e' if target == 'glue' else '#6366f1' if target == 'spark' else '#06b6d4'};">
    {'🔧 Glue' if target == 'glue' else '⚡ Spark' if target == 'spark' else '🌊 Flink'}
  </span>
  <span class="badge">Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}</span>
</div>
<div class="container">
  <div class="canvas">
    <svg>
      <defs><marker id="arrow" markerWidth="10" markerHeight="7" refX="10" refY="3.5" orient="auto"><polygon points="0 0, 10 3.5, 0 7" fill="#475569"/></marker></defs>
"""

    # Draw edges
    for node in nodes:
        x1, y1 = node_positions[node.id]
        for child_id in node.children:
            if child_id in node_positions:
                x2, y2 = node_positions[child_id]
                html += f'      <line class="edge" x1="{x1+60}" y1="{y1+20}" x2="{x2}" y2="{y2+20}" stroke="#475569"/>\n'

    html += "    </svg>\n"

    # Draw nodes
    for node in nodes:
        x, y = node_positions[node.id]
        color = TYPE_COLOR.get(node.type.upper(), '#64748b')
        icon = TYPE_ICON.get(node.type.upper(), '📦')
        html += f'    <div class="node" style="left:{x}px; top:{y}px; background:{color}22; border:2px solid {color}; color:{color};">\n'
        html += f'      <div class="node-type">{icon} {node.type}</div>\n'
        html += f'      <div class="node-name" style="color:#e8edf5;">{node.name}</div>\n'
        html += f'    </div>\n'

    html += "  </div>\n"

    # Sidebar — execution order + code snippet
    html += '  <div class="sidebar">\n'
    html += '    <div class="section">\n'
    html += '      <div class="section-title">📊 Execution Order</div>\n'
    
    for i, node in enumerate(nodes, 1):
        color = TYPE_COLOR.get(node.type.upper(), '#64748b')
        icon = TYPE_ICON.get(node.type.upper(), '📦')
        rule = xfr_rules.get(node.id.lower()) or xfr_rules.get(node.name.lower()) or {}
        detail = ""
        if rule.get("select") and rule["select"] != "*":
            detail = f' → SELECT {rule["select"][:40]}'
        elif rule.get("join_key"):
            detail = f' → JOIN ON {rule["join_key"]}'
        elif rule.get("source_type"):
            detail = f' → {rule["source_type"].upper()}'
        html += f'      <div class="exec-item" style="background:{color}15; border:1px solid {color}30;">\n'
        html += f'        <div class="exec-num" style="background:{color}; color:#fff;">{i}</div>\n'
        html += f'        <div><span style="color:{color}; font-weight:600;">{icon} {node.name}</span><br/><span style="color:#5a7399; font-size:11px;">{node.type}{detail}</span></div>\n'
        html += f'      </div>\n'

    html += '    </div>\n'

    # Code flow section
    html += '    <div class="section">\n'
    html += f'      <div class="section-title">🔧 Flow in {target.upper()}</div>\n'
    html += '      <div class="code-block">'
    
    for node in nodes:
        ntype = node.type.upper()
        if target == "glue" or target == "spark":
            if ntype == "SOURCE":
                html += f'{node.id}_df = spark.read.format("parquet").load("s3://...")\n'
            elif ntype == "TRANSFORM":
                html += f'{node.id}_df = {node.parents[0] + "_df" if node.parents else "None"}.selectExpr("*")\n'
            elif ntype == "JOIN":
                if len(node.parents) >= 2:
                    html += f'{node.id}_df = {node.parents[0]}_df.join({node.parents[1]}_df, on="key")\n'
            elif ntype == "SINK":
                html += f'{node.parents[0] + "_df" if node.parents else "None"}.write.parquet("s3://...")\n'
            else:
                html += f'{node.id}_df = ...  # {ntype}\n'
        elif target == "flink":
            if ntype == "SOURCE":
                html += f'CREATE TABLE `{node.id}` WITH (\'connector\'=\'filesystem\')\n'
            elif ntype == "TRANSFORM":
                html += f'CREATE TEMPORARY VIEW `{node.id}` AS SELECT * FROM `{node.parents[0] if node.parents else "?"}`\n'
            elif ntype == "JOIN":
                if len(node.parents) >= 2:
                    html += f'CREATE TEMPORARY VIEW `{node.id}` AS SELECT * FROM `{node.parents[0]}` JOIN `{node.parents[1]}`\n'
            elif ntype == "SINK":
                html += f'INSERT INTO `{node.id}_sink` SELECT * FROM `{node.parents[0] if node.parents else "?"}`\n'
            else:
                html += f'-- {ntype}: {node.id}\n'

    html += '</div>\n'
    html += '    </div>\n'
    html += '  </div>\n'
    html += '</div>\n</body>\n</html>'

    with open(output_path, "w") as f:
        f.write(html)

    return output_path
