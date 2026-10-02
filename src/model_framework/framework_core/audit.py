from pathlib import Path
from datetime import datetime, timezone
import json, time, traceback

class AuditLogger:
    def __init__(self, path):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
    def event(self, execution_id, model, component, status, message, duration_ms=None):
        rec = {
            "timestamp_utc": datetime.now(timezone.utc).isoformat(),
            "execution_id": execution_id, "model": model,
            "component": component, "status": status,
            "message": message, "duration_ms": duration_ms
        }
        with self.path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")
    def run(self, execution_id, model, component, fn, context):
        start = time.perf_counter()
        self.event(execution_id, model, component, "STARTED", "started")
        try:
            out = fn(context)
            self.event(execution_id, model, component, "SUCCEEDED",
                       "completed", round((time.perf_counter()-start)*1000,3))
            return out
        except Exception as e:
            self.event(execution_id, model, component, "FAILED",
                       str(e), round((time.perf_counter()-start)*1000,3))
            raise
