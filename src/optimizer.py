class Rule:
    def apply(self, plan):
        return plan


# =========================
# RULE 1: FILTER PUSHDOWN
# =========================
class FilterPushDown(Rule):

    def apply(self, plan):

        print("🔥 Applying Filter Pushdown")

        # simplificado: hook real futuro
        return plan


# =========================
# RULE 2: PROJECT PRUNING
# =========================
class ColumnPruning(Rule):

    def apply(self, plan):

        print("🔥 Applying Column Pruning")

        return plan


# =========================
# OPTIMIZER ENGINE
# =========================
class Optimizer:

    def __init__(self):
        self.rules = [
            FilterPushDown(),
            ColumnPruning()
        ]

    def optimize(self, plan):

        for rule in self.rules:
            plan = rule.apply(plan)

        return plan