from src.models.node import Node


def parse_sql(sql):

    sql = sql.lower()

    # ? MUY SIMPLE (puedes extender)
    select_part = sql.split("from")[0].replace("select", "").strip()
    from_part = sql.split("from")[1]

    table = from_part.split()[0]

    where = None
    if "where" in sql:
        where = sql.split("where")[1].strip()

    nodes = {}

    # input
    nodes[table] = Node(table, "input")

    # select
    nodes["select_node"] = Node(
        "select_node",
        "select",
        inputs=[table],
        columns=[c.strip() for c in select_part.split(",")]
    )

    # filter
    if where:
        nodes["filter_node"] = Node(
            "filter_node",
            "filter",
            inputs=["select_node"],
            condition=where
        )

    return nodes