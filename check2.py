import re
with open('DR_BASIC_COUNT.mp','r') as f:
    c = f.read()

# vertex_vertex entries
print("=== COMPONENTS (XXGgraph_vertex_vertex) ===")
for m in re.finditer(r'XXGgraph_vertex_vertex\|\d+\|\d+\|\d+\|\d+\|\{([^|]+)\|(\d+)\|(\d+)\|', c):
    print(f"  name={m.group(1)}, vid1={m.group(2)}, vid2={m.group(3)}")

# port vertex IDs
print("\n=== PORT VERTEX IDs ===")
oports = set()
for m in re.finditer(r'XXGvertex_oport_oport\|\d+\|\d+\|\d+\|\d+\|\{\d+\|[^|]+\|\}(\d+)\|(\d+)\|', c):
    oports.add(m.group(1))
print(f"  Output port vertices: {sorted(oports, key=int)}")

iports = set()
for m in re.finditer(r'XXGvertex_iport\|\d+\|\d+\|\d+\|\d+\|\{\d+\|[^|]+\|\}(\d+)\|(\d+)\|', c):
    iports.add(m.group(1))
print(f"  Input port vertices: {sorted(iports, key=int)}")
