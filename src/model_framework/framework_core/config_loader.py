from pathlib import Path
import yaml

def load_config(path):
    with Path(path).open(encoding="utf-8") as f:
        return yaml.safe_load(f)

def validate_config(c):
    required = ["framework","model","artifact","data","features","algorithm",
                "reusable_libraries","pipeline","validation","notifications",
                "security","deployment"]
    missing = [x for x in required if x not in c]
    if missing:
        raise ValueError(f"Missing configuration sections: {missing}")
    if "train" in c["pipeline"]:
        raise ValueError("TRAIN is not part of operationalization.")
    if c["algorithm"]["type"] != "xgboost":
        raise ValueError("Demo supports XGBoost.")
