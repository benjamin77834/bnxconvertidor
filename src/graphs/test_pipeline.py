from src.models.node import Node

graph = [

    Node(
        id="A",
        type="scan",
        attrs={"path": "input.parquet"}
    ),

    Node(
        id="R1",
        type="reformat",
        inputs=["A"],
        expr=[
            "id",
            "UPPER(name)",
            "TRIM(country)"
        ]
    ),

    Node(
        id="R2",
        type="rollup",
        inputs=["R1"],
        attrs={
            "group_by": ["country"],
            "aggregations": [
                {"type": "sum", "col": "amount", "alias": "total_amount"},
                {"type": "count", "col": "*", "alias": "cnt"}
            ]
        }
    ),

    Node(
        id="OUT",
        type="write",
        inputs=["R2"],
        attrs={"path": "s3://output/test/"}
    )
]