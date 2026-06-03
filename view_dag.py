"""
Genera un HTML interactivo del DAG sin dependencias externas.
Uso: py -3 view_dag.py Fallas_diferencia.mp
Abre dag_view.html en el navegador.
"""
import sys
from main import parse_project
from src.dag.builder import build_dag

filename = sys.argv[1] if len(sys.argv) > 1 else "Fallas_diferencia.mp"

ast = parse_project(filename)
dag = build_dag(ast)

# Build nodes and edges for HTML
nodes_js = []
for i, node in enumerate(dag.execution_order):
    x = 100 + (i % 6) * 200
    y = 50 + (i // 6) * 100
    color = {"JOIN": "#f59e0b", "SINK": "#ef4444", "SOURCE": "#22c55e", "FILTER": "#06b6d4",
             "PARTITION": "#8b5cf6", "CONCATENATE": "#ec4899", "DEDUP": "#14b8a6"}.get(node.type, "#6366f1")
    nodes_js.append(f'{{id:"{node.id}",name:"{node.name}",type:"{node.type}",x:{x},y:{y},color:"{color}"}}')

edges_js = []
for node in dag.execution_order:
    for p in node.parents:
        edges_js.append(f'{{from:"{p}",to:"{node.id}"}}')

html = f"""<!DOCTYPE html>
<html><head><title>BNX DAG - {filename}</title>
<style>
body {{ margin:0; background:#0a1628; font-family:monospace; }}
svg {{ width:100vw; height:100vh; }}
.node {{ cursor:pointer; }}
.node rect {{ rx:6; ry:6; stroke-width:2; }}
.node text {{ fill:#fff; font-size:10px; text-anchor:middle; }}
.edge {{ stroke:#334155; stroke-width:1.5; fill:none; marker-end:url(#arrow); }}
#info {{ position:fixed; top:10px; left:10px; color:#e2e8f0; font-size:13px; background:#1e2433; padding:10px 16px; border-radius:8px; border:1px solid #334155; }}
</style></head><body>
<div id="info">DAG: {filename} | Nodes: {len(dag.execution_order)} | Edges: {len(edges_js)}</div>
<svg id="svg">
<defs><marker id="arrow" viewBox="0 0 10 10" refX="10" refY="5" markerWidth="6" markerHeight="6" orient="auto"><path d="M 0 0 L 10 5 L 0 10 z" fill="#64748b"/></marker></defs>
</svg>
<script>
const nodes = [{",".join(nodes_js)}];
const edges = [{",".join(edges_js)}];

// Zoom and pan
let scale = 1, panX = 0, panY = 0, dragging = false, lastX = 0, lastY = 0;
const svg = document.getElementById('svg');
const container = document.createElementNS('http://www.w3.org/2000/svg', 'g');
container.setAttribute('id', 'container');
svg.appendChild(container);

svg.addEventListener('wheel', e => {{
  e.preventDefault();
  const delta = e.deltaY > 0 ? 0.9 : 1.1;
  scale *= delta;
  scale = Math.max(0.05, Math.min(20, scale));
  container.setAttribute('transform', `translate(${{panX}},${{panY}}) scale(${{scale}})`);
}});
svg.addEventListener('mousedown', e => {{ dragging = true; lastX = e.clientX; lastY = e.clientY; }});
svg.addEventListener('mousemove', e => {{
  if (!dragging) return;
  panX += e.clientX - lastX;
  panY += e.clientY - lastY;
  lastX = e.clientX; lastY = e.clientY;
  container.setAttribute('transform', `translate(${{panX}},${{panY}}) scale(${{scale}})`);
}});
svg.addEventListener('mouseup', () => {{ dragging = false; }});
svg.addEventListener('mouseleave', () => {{ dragging = false; }});

// Auto-layout: topological layers
const layers = {{}};
const visited = new Set();
function getLayer(id, depth) {{
  if (visited.has(id)) return layers[id] || 0;
  visited.add(id);
  const parents = edges.filter(e => e.to === id).map(e => e.from);
  let maxParent = -1;
  parents.forEach(p => {{ maxParent = Math.max(maxParent, getLayer(p, depth+1)); }});
  layers[id] = maxParent + 1;
  return layers[id];
}}
nodes.forEach(n => getLayer(n.id, 0));

// Position by layer
const layerNodes = {{}};
nodes.forEach(n => {{
  const l = layers[n.id] || 0;
  if (!layerNodes[l]) layerNodes[l] = [];
  layerNodes[l].push(n);
}});
Object.keys(layerNodes).forEach(l => {{
  const ln = layerNodes[l];
  ln.forEach((n, i) => {{
    n.x = 80 + i * 180;
    n.y = 60 + parseInt(l) * 90;
  }});
}});

const maxX = Math.max(...nodes.map(n => n.x)) + 200;
const maxY = Math.max(...nodes.map(n => n.y)) + 100;
svg.setAttribute('viewBox', `0 0 ${{maxX}} ${{maxY}}`);
svg.setAttribute('width', '100%');
svg.setAttribute('height', '100%');

// Draw edges
edges.forEach(e => {{
  const from = nodes.find(n => n.id === e.from);
  const to = nodes.find(n => n.id === e.to);
  if (from && to) {{
    const path = document.createElementNS('http://www.w3.org/2000/svg', 'path');
    const x1 = from.x + 60, y1 = from.y + 20;
    const x2 = to.x + 60, y2 = to.y;
    path.setAttribute('d', `M${{x1}},${{y1}} C${{x1}},${{(y1+y2)/2}} ${{x2}},${{(y1+y2)/2}} ${{x2}},${{y2}}`);
    path.setAttribute('class', 'edge');
    container.appendChild(path);
  }}
}});

// Draw nodes
nodes.forEach(n => {{
  const g = document.createElementNS('http://www.w3.org/2000/svg', 'g');
  g.setAttribute('class', 'node');
  g.setAttribute('transform', `translate(${{n.x}},${{n.y}})`);
  const rect = document.createElementNS('http://www.w3.org/2000/svg', 'rect');
  rect.setAttribute('width', '120');
  rect.setAttribute('height', '36');
  rect.setAttribute('fill', n.color + '40');
  rect.setAttribute('stroke', n.color);
  g.appendChild(rect);
  const text = document.createElementNS('http://www.w3.org/2000/svg', 'text');
  text.setAttribute('x', '60');
  text.setAttribute('y', '15');
  text.textContent = n.name.substring(0, 16);
  g.appendChild(text);
  const text2 = document.createElementNS('http://www.w3.org/2000/svg', 'text');
  text2.setAttribute('x', '60');
  text2.setAttribute('y', '28');
  text2.setAttribute('fill', '#94a3b8');
  text2.setAttribute('font-size', '9');
  text2.textContent = n.type;
  g.appendChild(text2);
  container.appendChild(g);
}});
</script></body></html>"""

with open('dag_view.html', 'w') as f:
    f.write(html)

print(f"[ok] Generado: dag_view.html")
print(f"     Nodos: {len(dag.execution_order)}, Edges: {len(edges_js)}")
print(f"     Abre dag_view.html en el navegador")
