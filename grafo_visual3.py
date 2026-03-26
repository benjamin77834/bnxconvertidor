# generate_dag.py
import re
from graphviz import Digraph

# -------------------------
# Config
# -------------------------
glue_file = "glue_job.py"
output_file = "BNX_GlueJob_DAG"

# -------------------------
# Leer nodos del Glue Job
# -------------------------
with open(glue_file, "r") as f:
    content = f.read()

# Regex para capturar nodos DML y XFR
pattern = r"# 🔹 (DML|XFR) Node: (\w+)"
matches = re.findall(pattern, content)

nodes = []
for typ, name in matches:
    nodes.append( (name, typ) )

# Separar por tipo
xfr_nodes = [n for n,t in nodes if t=="XFR"]
dml_nodes = [n for n,t in nodes if t=="DML"]

# -------------------------
# Crear el DAG Graphviz
# -------------------------
dot = Digraph("BNX_GlueJob", format="png")

# Layout y tamaño
dot.attr(rankdir='LR')           # Left -> Right
dot.attr(size='20,20')           # tamaño grande
dot.attr(dpi='300')              # alta resolución
dot.attr(nodesep='0.8')          # separación entre nodos
dot.attr(ranksep='1')            # separación entre niveles
dot.attr(splines='ortho')        # líneas ortogonales
dot.attr(concentrate='true')     # combina líneas

# -------------------------
# Agregar nodos
# -------------------------
for n in xfr_nodes:
    dot.node(n, n, shape='box', style='filled', color='lightblue')

for n in dml_nodes:
    color = "lightgreen" if n != "MasterReport" else "orange"
    dot.node(n, n, shape='ellipse', style='filled', color=color)

# -------------------------
# Conexiones inferidas
# -------------------------

# 1️⃣ Raw/XFR -> DML (Clean)
for raw in xfr_nodes:
    matches = [c for c in dml_nodes if c.startswith(raw[3:] if raw.startswith("Raw") else raw)]
    for c in matches:
        dot.edge(raw, c)

# 2️⃣ Clean -> Joins/Agg
joins_aggs = [n for n in dml_nodes if n not in [*xfr_nodes, *[c for c in dml_nodes if c.startswith("Clean")]]]
cleans = [c for c in dml_nodes if c.startswith("Clean")]
for c in cleans:
    for j in joins_aggs:
        # Si el nombre de Clean aparece en el Join/Agg
        if c.replace("Clean", "") in j:
            dot.edge(c, j)

# 3️⃣ Todos los Agg -> MasterReport
agg_nodes = [n for n in joins_aggs if n != "MasterReport"]
for a in agg_nodes:
    dot.edge(a, "MasterReport")

# -------------------------
# Guardar gráfico
# -------------------------
dot.render(output_file, view=True)
print(f"✅ DAG generado y guardado como {output_file}.png")