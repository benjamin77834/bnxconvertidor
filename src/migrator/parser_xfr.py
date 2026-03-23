import os
import json

def parse_xfr(folder):
    transforms = []

    if not os.path.exists(folder):
        return transforms

    for file in os.listdir(folder):
        if not file.endswith(".xfr"):
            continue

        with open(os.path.join(folder, file), "r") as f:
            for line in f:
                parts = line.strip().split()

                # format:
                # TRANSFORM target type column
                if len(parts) >= 3 and parts[0] == "TRANSFORM":
                    transforms.append({
                        "target": parts[1],
                        "type": parts[2],
                        "column": parts[3] if len(parts) > 3 else None
                    })

    return transforms