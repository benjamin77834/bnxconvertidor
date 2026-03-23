from src.vm.operators.base import VMOperator
from src.vm.operators.input import InputOp
from src.vm.operators.join import JoinOp
from src.vm.operators.filter import FilterOp
from src.vm.operators.output import OutputOp


VM_OPERATORS = {
    "input": InputOp(),
    "join": JoinOp(),
    "filter": FilterOp(),
    "output": OutputOp()
}