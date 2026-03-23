def parse_dml(path):

    # versión base (puedes expandir después)
    return {
        "keys": {
            "Customers": "customer_id",
            "Transactions": "transaction_id",
            "Cards": "card_id",
            "Devices": "device_id"
        }
    }