def parse_mp(mp_path):

    nodes = [
        "customers",
        "transactions1",
        "transactions2",
        "consumerinfo",
        "rollup_household",
        "reformat_consumer",
        "join_final",
        "select_output"
    ]

    edges = [
        ("customers", "rollup_household"),
        ("transactions1", "rollup_household"),
        ("rollup_household", "join_final"),
        ("transactions2", "join_final"),
        ("consumerinfo", "reformat_consumer"),
        ("reformat_consumer", "join_final"),
        ("join_final", "select_output")
    ]

    return nodes, edges
