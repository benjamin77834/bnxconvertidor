import argparse
#from mp_parser import parse_mp
#from xfr_parser import parse_xfr
#from ir_builder import build_ir
#from optimizer import optimize_ir
#from glue_codegen import generate_glue
from migrator.mp_parser import parse_mp
from migrator.xfr_parser import parse_xfr
from migrator.ir_builder import build_ir
from migrator.optimizer import optimize_ir
from migrator.glue_codegen import generate_glue
def main():

    parser = argparse.ArgumentParser()

    parser.add_argument("--mp", required=True)
    parser.add_argument("--xfr", required=True)
    parser.add_argument("--dml", required=True)
    parser.add_argument("--output", required=True)

    args = parser.parse_args()

    print(" v7 ENTERPRISE MIGRATION ENGINE STARTED\n")

    nodes, edges = parse_mp(args.mp)

    xfr_rules = parse_xfr(args.xfr)

    ir = build_ir(nodes, edges, xfr_rules)

    ir = optimize_ir(ir)

    glue_code = generate_glue(ir)

    #  CLEAN OUTPUT (CRITICAL FIX)
    glue_code = "\n".join(
        line.rstrip().replace("%", "")
        for line in glue_code.splitlines()
    )

    with open(args.output, "w") as f:
        f.write(glue_code + "\n")

    print(f"\n Glue Job generated: {args.output}")

if __name__ == "__main__":
    main()
