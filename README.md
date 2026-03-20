# Ab Initio → AWS Glue Migration Engine

🚀 ETL Compiler that converts Ab Initio graphs into PySpark (AWS Glue)

## Features

- Parse Ab Initio MP graphs
- Convert to Intermediate Representation (IR)
- Apply transformation rules (XFR)
- Generate PySpark code for AWS Glue

## Architecture

MP → Parser → IR → Optimizer → Glue Codegen

## Usage

```bash
python src/migrator/main.py \
  --mp examples/customer_pipeline.mp \
  --xfr xfr/ \
  --dml dml/ \
  --output output/glue_job.py
