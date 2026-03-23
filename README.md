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
bnxconvertidor % python3 main.py --project /Users/benjamingarcia/sam/grafo1 --output glue_job.py


