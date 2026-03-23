import os

def parse_dml(folder):
    schemas = {}

    if not os.path.exists(folder):
        return schemas

    for file in os.listdir(folder):
        if not file.endswith(".dml"):
            continue

        table = file.replace(".dml", "")
        schema = []

        with open(os.path.join(folder, file), "r") as f:
            for line in f:
                parts = line.strip().split()

                if len(parts) >= 2:
                    schema.append({
                        "column": parts[0],
                        "type": parts[1]
                    })

        schemas[table] = schema

    return schemas