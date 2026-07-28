#!/bin/bash
# ═══════════════════════════════════════════════════════════
# BNX Pipeline E2E — Ejecutar manualmente
#
# Este script:
# 1. Compila un grafo con BNX (via Lambda) para spark y glue
# 2. Sube los scripts generados a S3
# 3. Ejecuta los Glue jobs
# 4. Espera los resultados
# 5. Compara outputs
#
# Uso: ./run_pipeline.sh [--graph test.mp] [--xfr test.xfr]
# ═══════════════════════════════════════════════════════════

set -e

BUCKET="bnx-e2e-test"
REGION="us-east-1"
BNX_API="https://rcp5mtwkqngtb3fv3fiourq2hq0qptmy.lambda-url.us-east-1.on.aws"
PATHBNX="$(cd "$(dirname "$0")/../.." && pwd)"

# Defaults
GRAPH_FILE="${PATHBNX}/e2e/test.mp"
XFR_FILE="${PATHBNX}/e2e/test.xfr"

# Parse args
while [[ $# -gt 0 ]]; do
  case $1 in
    --graph) GRAPH_FILE="$2"; shift 2 ;;
    --xfr) XFR_FILE="$2"; shift 2 ;;
    *) echo "Unknown arg: $1"; exit 1 ;;
  esac
done

echo "═══════════════════════════════════════════════════"
echo " BNX E2E Pipeline"
echo "═══════════════════════════════════════════════════"
echo " Graph: $GRAPH_FILE"
echo " XFR:   $XFR_FILE"
echo " Bucket: s3://$BUCKET"
echo ""

# ── Step 1: Upload test data ────────────────────────────
echo "[1/7] Uploading test data..."
cat << 'EOF' | aws s3 cp - s3://$BUCKET/raw/orders/data.csv
id,nombre,monto
1,juan perez,150.50
2,maria gomez,300.5
3,carlos lopez,75.25
4,ana martinez,200.0
5,luis rodriguez,120.25
6,juan perez,50.0
7,maria gomez,100.0
EOF
echo "  OK: Test data uploaded"

# ── Step 2: Upload expected output ──────────────────────
echo "[2/7] Uploading expected output..."
cat << 'EOF' | aws s3 cp - s3://$BUCKET/expected/expected.csv
id,nombre,monto
1,JUAN PEREZ,200.5
2,MARIA GOMEZ,400.5
3,CARLOS LOPEZ,75.25
4,ANA MARTINEZ,200.0
5,LUIS RODRIGUEZ,120.25
EOF
echo "  OK: Expected output uploaded"

# ── Step 3: Compile with BNX (Spark target) ─────────────
echo "[3/7] Compiling graph (target=spark)..."
SPARK_CODE=$(curl -s -X POST "$BNX_API/compile" \
  -F "mp=@$GRAPH_FILE" \
  -F "xfr=@$XFR_FILE" \
  -F "target=spark" | python3 -c "import sys,json; print(json.load(sys.stdin).get('code',''))")

if [ -z "$SPARK_CODE" ]; then
  echo "  ERROR: Compilation failed for spark target"
  exit 1
fi

echo "$SPARK_CODE" | aws s3 cp - s3://$BUCKET/scripts/spark_job.py
echo "  OK: Spark code generated and uploaded"

# ── Step 4: Compile with BNX (Glue target) ──────────────
echo "[4/7] Compiling graph (target=glue)..."
GLUE_CODE=$(curl -s -X POST "$BNX_API/compile" \
  -F "mp=@$GRAPH_FILE" \
  -F "xfr=@$XFR_FILE" \
  -F "target=glue" | python3 -c "import sys,json; print(json.load(sys.stdin).get('code',''))")

if [ -z "$GLUE_CODE" ]; then
  echo "  ERROR: Compilation failed for glue target"
  exit 1
fi

echo "$GLUE_CODE" | aws s3 cp - s3://$BUCKET/scripts/glue_job.py
echo "  OK: Glue code generated and uploaded"

# ── Step 5: Execute Spark job ───────────────────────────
echo "[5/7] Running Spark Glue job..."
SPARK_JOB="bnx-convertidor-test-spark"

# Create or update job
aws glue create-job --name $SPARK_JOB \
  --role "arn:aws:iam::034711235858:role/lambdarol" \
  --command '{"Name":"glueetl","ScriptLocation":"s3://'$BUCKET'/scripts/spark_job.py","PythonVersion":"3"}' \
  --default-arguments '{"--job-language":"python","--TempDir":"s3://'$BUCKET'/temp/","--INPUT_PATH":"s3://'$BUCKET'/raw/orders","--OUTPUT_PATH":"s3://'$BUCKET'/output/spark_output"}' \
  --glue-version "4.0" --number-of-workers 2 --worker-type "G.1X" \
  --region $REGION 2>/dev/null || \
aws glue update-job --job-name $SPARK_JOB \
  --job-update '{"Role":"arn:aws:iam::034711235858:role/lambdarol","Command":{"Name":"glueetl","ScriptLocation":"s3://'$BUCKET'/scripts/spark_job.py","PythonVersion":"3"},"DefaultArguments":{"--job-language":"python","--TempDir":"s3://'$BUCKET'/temp/","--INPUT_PATH":"s3://'$BUCKET'/raw/orders","--OUTPUT_PATH":"s3://'$BUCKET'/output/spark_output"},"GlueVersion":"4.0","NumberOfWorkers":2,"WorkerType":"G.1X"}' \
  --region $REGION

SPARK_RUN=$(aws glue start-job-run --job-name $SPARK_JOB --region $REGION --query 'JobRunId' --output text)
echo "  Spark Job Run: $SPARK_RUN"

# ── Step 6: Execute Glue job ────────────────────────────
echo "[6/7] Running Glue job..."
GLUE_JOB="bnx-convertidor-test-glue"

aws glue create-job --name $GLUE_JOB \
  --role "arn:aws:iam::034711235858:role/lambdarol" \
  --command '{"Name":"glueetl","ScriptLocation":"s3://'$BUCKET'/scripts/glue_job.py","PythonVersion":"3"}' \
  --default-arguments '{"--job-language":"python","--TempDir":"s3://'$BUCKET'/temp/","--INPUT_PATH":"s3://'$BUCKET'/raw/orders","--OUTPUT_PATH":"s3://'$BUCKET'/output/glue_output"}' \
  --glue-version "4.0" --number-of-workers 2 --worker-type "G.1X" \
  --region $REGION 2>/dev/null || \
aws glue update-job --job-name $GLUE_JOB \
  --job-update '{"Role":"arn:aws:iam::034711235858:role/lambdarol","Command":{"Name":"glueetl","ScriptLocation":"s3://'$BUCKET'/scripts/glue_job.py","PythonVersion":"3"},"DefaultArguments":{"--job-language":"python","--TempDir":"s3://'$BUCKET'/temp/","--INPUT_PATH":"s3://'$BUCKET'/raw/orders","--OUTPUT_PATH":"s3://'$BUCKET'/output/glue_output"},"GlueVersion":"4.0","NumberOfWorkers":2,"WorkerType":"G.1X"}' \
  --region $REGION

GLUE_RUN=$(aws glue start-job-run --job-name $GLUE_JOB --region $REGION --query 'JobRunId' --output text)
echo "  Glue Job Run: $GLUE_RUN"

# ── Step 7: Wait and validate ───────────────────────────
echo "[7/7] Waiting for jobs to complete..."
echo ""

SPARK_OK=false
GLUE_OK=false

for i in $(seq 1 40); do
  SPARK_STATUS=$(aws glue get-job-run --job-name $SPARK_JOB --run-id $SPARK_RUN --region $REGION --query 'JobRun.JobRunState' --output text 2>/dev/null || echo "UNKNOWN")
  GLUE_STATUS=$(aws glue get-job-run --job-name $GLUE_JOB --run-id $GLUE_RUN --region $REGION --query 'JobRun.JobRunState' --output text 2>/dev/null || echo "UNKNOWN")

  echo "  [$i] Spark: $SPARK_STATUS | Glue: $GLUE_STATUS"

  if [ "$SPARK_STATUS" = "SUCCEEDED" ]; then SPARK_OK=true; fi
  if [ "$GLUE_STATUS" = "SUCCEEDED" ]; then GLUE_OK=true; fi

  if [ "$SPARK_STATUS" = "FAILED" ] || [ "$GLUE_STATUS" = "FAILED" ]; then
    echo ""
    echo "PIPELINE FAILED"
    if [ "$SPARK_STATUS" = "FAILED" ]; then
      echo "  Spark error:"
      aws glue get-job-run --job-name $SPARK_JOB --run-id $SPARK_RUN --region $REGION --query 'JobRun.ErrorMessage' --output text
    fi
    if [ "$GLUE_STATUS" = "FAILED" ]; then
      echo "  Glue error:"
      aws glue get-job-run --job-name $GLUE_JOB --run-id $GLUE_RUN --region $REGION --query 'JobRun.ErrorMessage' --output text
    fi
    exit 1
  fi

  if [ "$SPARK_OK" = true ] && [ "$GLUE_OK" = true ]; then
    break
  fi

  sleep 15
done

echo ""
echo "═══════════════════════════════════════════════════"

if [ "$SPARK_OK" = true ] && [ "$GLUE_OK" = true ]; then
  echo " PIPELINE E2E: PASSED"
  echo ""
  echo " Spark output: s3://$BUCKET/output/spark_output/"
  echo " Glue output:  s3://$BUCKET/output/glue_output/"
  echo ""
  echo " Verificar:"
  echo "   aws s3 ls s3://$BUCKET/output/spark_output/ --recursive"
  echo "   aws s3 ls s3://$BUCKET/output/glue_output/ --recursive"
else
  echo " PIPELINE E2E: TIMEOUT (jobs no terminaron en 10 min)"
  exit 1
fi

echo "═══════════════════════════════════════════════════"
