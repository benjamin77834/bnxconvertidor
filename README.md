# Ab Initio → AWS Glue Migration Engine

🚀 ETL Compiler that converts Ab Initio graphs into PySpark (AWS Glue)

## Features

- Parse Ab Initio MP graphs
- Convert to Intermediate Representation (IR)
- Apply transformation rules (XFR)
- Generate PySpark code for AWS Glue

1. Usuario define .mp (DSL Ab Initio)
2. Parser → AST
3. AST → DAG
4. Validator asegura consistencia
5. Lineage construye trazabilidad
6. Codegen genera PySpark
7. Se ejecuta en AWS Glue
## Architecture

Ab Initio (.mp DSL)
        ↓
   AST Parser
        ↓
   DAG Builder
        ↓
   DAG Validator
        ↓
   Lineage Engine
        ↓
   Code Generator
        ↓
 AWS Glue (PySpark Job)
## Usage

```bash
bnxconvertidor % python3 main.py --project /Users/benjamingarcia/sam/grafo1 --output glue_job.py


