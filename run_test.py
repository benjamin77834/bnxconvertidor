import sys
from pathlib import Path

# =========================
# ROOT PATH FIX
# =========================
ROOT = Path(__file__).resolve().parent
sys.path.append(str(ROOT))

# =========================
# IMPORT GRAPH
# =========================
from graphs.test_pipeline import graph

# =========================
# IMPORT CODEGEN
# =========================
from src.codegen.glue_codegen import GlueCodeGen


def main():

    print("\n🚀 BNX ENTERPRISE COMPILER TEST\n")

    gen = GlueCodeGen()

    code = gen.generate(graph)

    output_file = "glue_job.py"

    with open(output_file, "w") as f:
        f.write(code)

    print("\n🔥 GENERATED GLUE JOB SUCCESSFULLY\n")
    print(f"📄 Output: {output_file}\n")

    print("========== GENERATED CODE ==========\n")
    print(code)
    print("\n====================================\n")


if __name__ == "__main__":
    main()