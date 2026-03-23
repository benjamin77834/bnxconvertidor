from src.operators.input import InputOperator
from src.operators.join import JoinOperator
from src.operators.filter import FilterOperator
from src.operators.output import OutputOperator


OPERATORS = {
    "input": InputOperator(),
    "join": JoinOperator(),
    "filter": FilterOperator(),
    "output": OutputOperator()
}