# grafo_visual.py
import re
from graphviz import Digraph

# Ruta al glue job que quieres analizar
GLUE_JOB_PATH = "glue_job.py"
OUTPUT_FILE = "glue_job_dag"

# Regex para capturar nodos y sus dependencias
node_regex = re.compile(r"^(\w+)_df\s*=\s*(.*)")  # captura "Nodo_df = ..."

nodes = {}
with open(GLUE_JOB_PATH, "r") as f:
    for line in f:
        line = line.strip()
        m = node_regex.match(line)
        if m:
            node_name = m.group(1)
            rhs = m.group(2)
            # Buscar dependencias: nombres de variables que aparecen en RHS
            deps = re.findall(r"(\w+)_df", rhs)
            nodes[node_name] = deps

# Crear gráfico
dot = Digraph(comment="DAG de glue_job.py", format="png")
for node in nodes:
    dot.node(node, node)

for node, deps in nodes.items():
    for dep in deps:
        dot.edge(dep, node)

# Guardar y renderizar
dot.render(OUTPUT_FILE, view=True)
print(f"DAG generado: {OUTPUT_FILE}.png")
