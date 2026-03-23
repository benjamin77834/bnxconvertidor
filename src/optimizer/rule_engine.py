class Rule:

    def apply(self, node):
        return node


class PredicatePushdown(Rule):

    def apply(self, node):
        if node.type == "FILTER":
            node.attrs["pushed"] = True
        return node


class RuleEngine:

    def __init__(self):
        self.rules = [
            PredicatePushdown()
        ]

    def optimize(self, nodes):

        changed = True

        while changed:
            changed = False

            new_nodes = []

            for n in nodes:
                original = repr(n)

                for rule in self.rules:
                    n = rule.apply(n)

                new_nodes.append(n)

                if repr(n) != original:
                    changed = True

            nodes = new_nodes

        return nodes