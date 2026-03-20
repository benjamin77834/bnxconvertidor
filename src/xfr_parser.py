def parse_xfr(path):

    # Simulación tipo Ab Initio XFR realista
    return {
        "reformat_consumer": [
            {
                "target": "full_name",
                "op": "concat",
                "args": ["first_name", "last_name"]
            }
        ]
    }
