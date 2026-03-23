import re

def clean_id(node_id: str) -> str:
    """
    Limpia IDs basura como:
    'StageCustomers;' o '#'
    """
    if node_id is None:
        return None

    node_id = node_id.strip()

    # eliminar ;
    node_id = node_id.replace(";", "")

    # eliminar comentarios raros
    if node_id in ["#", "", "node", "graph", "subgraph"]:
        return None

    return node_id


def clean_type(node_type: str) -> str:
    if node_type is None:
        return None
    return node_type.replace(";", "").strip()


def is_valid_node(node_id: str) -> bool:
    if not node_id:
        return False
    if node_id.startswith("connect_"):
        return False
    if node_id in ["#", "graph", "subgraph"]:
        return False
    return True