from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional


@dataclass
class Node:
    id: str
    type: str
    inputs: List[str] = field(default_factory=list)

    # Ab Initio semantics
    expr: List[str] = field(default_factory=list)
    attrs: Dict[str, Any] = field(default_factory=dict)