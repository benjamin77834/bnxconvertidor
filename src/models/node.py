class Node:

    def __init__(self, id, type, inputs=None, attrs=None, expr=None):

        self.id = id
        self.type = type
        self.inputs = inputs or []
        self.attrs = attrs or {}

        # 🔥 NEW: XFR EXPRESSION SUPPORT
        self.expr = expr or []

        # 🔥 NEW: ROLLUP SUPPORT
        self.group_by = self.attrs.get("group_by", [])
        self.aggregations = self.attrs.get("aggs", [])