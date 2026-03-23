import json
import time
from datetime import datetime


class AuditLogger:
    def __init__(self):
        self.logs = []

    def log(self, event):
        event["timestamp"] = str(datetime.now())
        self.logs.append(event)

    def export(self, path="audit_log.json"):
        with open(path, "w") as f:
            json.dump(self.logs, f, indent=2)


class ReconciliationEngine:
    def __init__(self, spark):
        self.spark = spark
        self.results = {}

    def row_count_check(self, source_df, target_df, name):
        src = source_df.count()
        tgt = target_df.count()

        result = {
            "source": src,
            "target": tgt,
            "match": src == tgt
        }

        self.results[name] = result
        return result

    def export(self, path="reconciliation.json"):
        with open(path, "w") as f:
            json.dump(self.results, f, indent=2)


class DataQualityEngine:
    def __init__(self):
        self.issues = {}

    def not_null(self, df, col, name):
        nulls = df.filter(df[col].isNull()).count()

        self.issues.setdefault(name, {})
        self.issues[name][f"{col}_nulls"] = nulls

        return nulls == 0

    def export(self, path="data_quality.json"):
        with open(path, "w") as f:
            json.dump(self.issues, f, indent=2)


class Observability:
    def __init__(self):
        self.metrics = []

    def measure(self, name, func, *args, **kwargs):
        start = time.time()
        result = func(*args, **kwargs)
        end = time.time()

        self.metrics.append({
            "node": name,
            "duration_sec": round(end - start, 4)
        })

        return result

    def export(self, path="metrics.json"):
        with open(path, "w") as f:
            json.dump(self.metrics, f, indent=2)


# =========================
# 🏦 THIS IS THE IMPORTANT PART
# =========================

class BankingLayer:
    def __init__(self, spark):
        self.spark = spark
        self.audit = AuditLogger()
        self.recon = ReconciliationEngine(spark)
        self.dq = DataQualityEngine()
        self.obs = Observability()

    def start(self, job, inputs):
        self.audit.log({
            "event": "JOB_START",
            "job": job,
            "inputs": inputs
        })

    def end(self, job, output):
        self.audit.log({
            "event": "JOB_END",
            "job": job,
            "output": output
        })

    def validate(self, df, name, rules):
        results = {}

        for r in rules:
            if r["type"] == "not_null":
                results[r["column"]] = self.dq.not_null(df, r["column"], name)

        return results

    def reconcile(self, src, tgt, name):
        return self.recon.row_count_check(src, tgt, name)

    def export_all(self):
        self.audit.export()
        self.recon.export()
        self.dq.export()
        self.obs.export()