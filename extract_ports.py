import re
import sys

filename = sys.argv[1] if len(sys.argv) > 1 else "uif_ingestion_proto_frauds_ftracct.mp"

with open(filename, "rb") as f:
    data = f.read()

text = data.decode("latin-1").replace("\x00", "")

print("=== OUTPUT PORTS ===")
for m in re.finditer(r'XXGvertex_oport\|(\d+)\|(\d+)\|(\d+)\|(\d+)\|\{0\|out\d*\|\}(\d+)\|(\d+)\|', text):
    print("OPORT:", m.groups())

print("\n=== INPUT PORTS ===")
for m in re.finditer(r'XXGvertex_iport\|(\d+)\|(\d+)\|(\d+)\|(\d+)\|\{0\|in\d*\|\}(\d+)\|(\d+)\|', text):
    print("IPORT:", m.groups())

print("\n=== FLOWS (iport_src_flow) ===")
for m in re.finditer(r'XXGiport_src_flow\|(\d+)\|(\d+)\|(\d+)\|(\d+)\|\{0\|\}(\d+)\|(\d+)\|', text):
    print("FLOW_IN:", m.groups())

print("\n=== FLOWS (oport_dst_flow) ===")
for m in re.finditer(r'XXGoport_dst_flow\|(\d+)\|(\d+)\|(\d+)\|(\d+)\|\{0\|\}(\d+)\|(\d+)\|', text):
    print("FLOW_OUT:", m.groups())
