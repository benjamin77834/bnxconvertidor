# Ab Initio → AWS Glue Migration Engine

🚀 ETL Compiler that converts Ab Initio graphs into PySpark (AWS Glue)

## Features


bnxconvertidor/
│
├── main.py
├── src/
│   ├── ir/
│   │   ├── graphir.py        # (2)
│   │   └── node.py           # (3)
│   │
│   ├── parser/
│   │   └── mp_parser.py      # (4)
│   │
│   ├── dag/
│   │   └── builder.py        # (5)
│   │
│   ├── lineage/
│   │   └── tracker.py       # (6)
│   │
│   ├── optimizer/
│   │   └── optimizer.py      # (7)
│   │
│   └── codegen/
│       └── spark_codegen.py  # (8)

## Usage

```bash
python src/migrator/main.py \
  --mp examples/customer_pipeline.mp \
  --xfr xfr/ \
  --dml dml/ \
  --output output/glue_job.py
