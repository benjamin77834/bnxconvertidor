# BNX Convertidor — Muestras de Prueba

## Archivos disponibles:

### 1. Grafo simple (.mp + .xfr + .dml)
- `simple.mp` — 6 nodos, 2 sources, 1 join, 1 transform, 1 sink
- `simple.xfr` — reglas de transformación
- `simple.dml` — schema de datos

### 2. Ab Initio PLAN + PSET
- `credit_card.plan` — 22 grafos, 5 fases
- `credit_card.pset` — parámetros S3, Kafka, DB

### 3. COBOL
- `banking_batch.cbl` — proceso batch con EBCDIC/COMP-3

## Cómo probar:

### En la UI (Compiler):
1. Sube `simple.mp` + `simple.xfr` + `simple.dml`
2. Click Compile

### En la UI (PLAN):
1. Sube `credit_card.plan` con botón "📄 .plan"

### En la UI (COBOL):
1. Sube `banking_batch.cbl` con botón "📋 Upload .cbl"

### Por CLI:
```bash
python3 main.py --project samples/simple.mp --xfr samples/simple.xfr --dml samples/simple.dml --target spark --output output_spark.py
python3 main.py --project samples/simple.mp --xfr samples/simple.xfr --dml samples/simple.dml --target glue --output output_glue.py
```
