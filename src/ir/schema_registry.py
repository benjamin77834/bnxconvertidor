class SchemaRegistry:

    def __init__(self):
        self.schemas = {}

    def register(self, node_id, schema):
        self.schemas[node_id] = schema or {}

    def get(self, node_id):
        return self.schemas.get(node_id, {})

    def has_column(self, node_id, col):
        return col in self.schemas.get(node_id, {})