import argparse
from graph_engine import run


def main():
    print("[*] BNX STARTED")

    parser = argparse.ArgumentParser()

    parser.add_argument("--mp", required=True)
    parser.add_argument("--xfr", required=True)
    parser.add_argument("--dml", required=True)
    parser.add_argument("--output", default="glue_job.py")

    args = parser.parse_args()

    # ? NO SQL HERE
    code, lineage = run(args.mp, args.xfr, args.dml)

    with open(args.output, "w") as f:
        f.write(code)

    print("[*] GRAPH MODE (MP/XFR/DML)")
    print("? lineage built")

    for k, v in lineage.items():
        print(f"{k} ? {v}")

    print(f"[ok] Generated: {args.output}")
    print("[*] DONE")


if __name__ == "__main__":
    main()