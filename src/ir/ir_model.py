from dataclasses import dataclass, field
from typing import List, Dict, Any


@dataclass
class Node:
    id: str
    type: str
    inputs: List[str] = field(default_factory=list)
    props: Dict[str, Any] = field(default_factory=dict)


@dataclass
class IR:
    nodes: Dict[str, Node]