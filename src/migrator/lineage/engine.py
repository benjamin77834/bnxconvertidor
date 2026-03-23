from collections import defaultdict


class LineageEngine:

    def __init__(self):
        self.map = defaultdict(list)

    def add_mapping(self, target_col, source_cols):
        if isinstance(source_cols, str):
            source_cols = [source_cols]

        self.map[target_col].extend(source_cols)

    def propagate(self, target, parents, schema):
        for col in schema.get(target, []):
            for p in parents:
                self.map[f"{target}.{col}"].append(f"{p}.{col}")

    def get(self):
        return dict(self.map)
