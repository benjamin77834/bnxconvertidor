from dataclasses import dataclass

@dataclass
class Instruction:
    id: str
    op_type: str
    attrs: dict
    inputs: list