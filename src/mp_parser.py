import re

def clean_node(line):
    """
    Extrae nombre real del nodo
    """
    match = re.search(r"node:\s*([A-Za-z0-9_]+)", line)
    return match.group(1) if match else None


def parse_mp(file_path):

    nodes = []

    with open(file_path, "r") as f:
        for line in f:

            line = line.strip().lower()

            if "customers" in line:
                nodes.append({
                    "id": "Customers",
                    "type": "input",
                    "inputs": []
                })

            elif "transactions" in line:
                nodes.append({
                    "id": "Transactions",
                    "type": "input",
                    "inputs": []
                })

            elif "cards" in line:
                nodes.append({
                    "id": "Cards",
                    "type": "transform",
                    "inputs": ["Customers"]
                })

            elif "devices" in line:
                nodes.append({
                    "id": "Devices",
                    "type": "transform",
                    "inputs": ["Customers"]
                })

            elif "final" in line:
                nodes.append({
                    "id": "Final",
                    "type": "transform",
                    "inputs": ["Transactions", "Cards", "Devices"]
                })

    return nodes