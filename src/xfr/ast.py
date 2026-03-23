from dataclasses import dataclass
from typing import List, Union


@dataclass
class XFRNode:
    type: str
    value: Union[str, None] = None
    left: "XFRNode" = None
    right: "XFRNode" = None