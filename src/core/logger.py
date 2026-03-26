import time

class Logger:
    def __init__(self, name="BNX"):
        self.name = name

    def info(self, msg):
        print(f"[INFO][{self.name}] {msg}")

    def warn(self, msg):
        print(f"[WARN][{self.name}] {msg}")

    def error(self, msg):
        print(f"[ERROR][{self.name}] {msg}")

    def stage(self, msg):
        print(f"\n=== {msg} ===")

    def timing(self, start, end, stage):
        print(f"[TIMER] {stage}: {end - start:.3f}s")