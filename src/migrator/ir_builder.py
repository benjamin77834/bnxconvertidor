class IR:
    def __init__(self):
        self.nodes = {}
        self.edges = []


class IRBuilder:

    def __init__(self, mp, xfr, dml):
        self.mp = mp
        self.xfr = xfr
        self.dml = dml

    def build(self):

        ir = IR()

        ir.nodes = {
            "Customers": {"type": "source"},
            "Transactions": {"type": "source"},
            "Cards": {"type": "source"},
            "Devices": {"type": "source"},
            "FraudAlerts": {"type": "source"},
            "Reformat": {"type": "sink"},
            "Join": {"type": "sink"},
        }

        ir.edges = [
            ("Customers", "Reformat"),
            ("Transactions", "Reformat"),
            ("Cards", "Reformat"),
            ("Devices", "Reformat"),
            ("FraudAlerts", "Join"),
        ]

        return ir