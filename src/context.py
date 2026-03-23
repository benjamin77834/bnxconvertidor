class ExecutionContext:
    def __init__(self):
        self.dfs = {}      # node_id → dataframe variable name
        self.code = []     # spark code output