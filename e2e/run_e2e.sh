#!/bin/bash
# BNX End-to-End Test on AWS Glue
# Usage: ./e2e/run_e2e.sh

BUCKET="bnx-e2e-test"
REGION="us-east-1"
GLUE_ROLE="arn:aws:iam::034711235858:role/lambdarol"
JOB_NAME="bnx-e2e-test"

echo " BNX End-to-End Test"
echo "======================"

# Step 1: Create S3 bucket
echo " Step 1: Creating S3 bucket..."
aws s3 mb s3://$BUCKET --region $REGION 2>/dev/null || true

# Step 2: Upload test data
echo " Step 2: Uploading test data..."
cat << 'EOF' | aws s3 cp - s3://$BUCKET/raw/orders/data.csv
order_id,customer_id,amount,status,order_date
ORD001,C001,150.00,completed,2026-01-15
ORD002,C002,250.50,completed,2026-01-16
ORD003,C001,75.00,cancelled,2026-01-17
ORD004,C003,500.00,completed,2026-01-18
ORD005,C002,120.00,completed,2026-01-19
ORD006,C001,300.00,completed,2026-01-20
EOF

cat << 'EOF' | aws s3 cp - s3://$BUCKET/raw/customers/data.csv
customer_id,name,email,region
C001,Juan Garcia,juan@test.com,MX-NORTH
C002,Maria Lopez,maria@test.com,MX-SOUTH
C003,Carlos Ruiz,carlos@test.com,MX-CENTER
EOF

# Step 3: Generate Glue code
echo " Step 3: Generating Glue code..."
python3 main.py --project e2e/test.mp --xfr e2e/test.xfr --target glue --output e2e/glue_job.py

# Step 4: Upload script to S3
echo " Step 4: Uploading Glue script..."
aws s3 cp e2e/glue_job.py s3://$BUCKET/scripts/glue_job.py

# Step 5: Create or update Glue job
echo " Step 5: Creating Glue job..."
aws glue create-job --name $JOB_NAME --role $GLUE_ROLE --command '{"Name":"glueetl","ScriptLocation":"s3://'$BUCKET'/scripts/glue_job.py","PythonVersion":"3"}' --default-arguments '{"--job-language":"python","--TempDir":"s3://'$BUCKET'/temp/"}' --glue-version "4.0" --number-of-workers 2 --worker-type "G.1X" --region $REGION 2>/dev/null || \
aws glue update-job --job-name $JOB_NAME --job-update '{"Role":"'$GLUE_ROLE'","Command":{"Name":"glueetl","ScriptLocation":"s3://'$BUCKET'/scripts/glue_job.py","PythonVersion":"3"},"DefaultArguments":{"--job-language":"python","--TempDir":"s3://'$BUCKET'/temp/"},"GlueVersion":"4.0","NumberOfWorkers":2,"WorkerType":"G.1X"}' --region $REGION

# Step 6: Run the job
echo "🚀 Step 6: Running Glue job..."
RUN_ID=$(aws glue start-job-run --job-name $JOB_NAME --region $REGION --query 'JobRunId' --output text)
echo "   Job Run ID: $RUN_ID"

# Step 7: Wait for completion
echo " Step 7: Waiting for job to complete..."
while true; do
    STATUS=$(aws glue get-job-run --job-name $JOB_NAME --run-id $RUN_ID --region $REGION --query 'JobRun.JobRunState' --output text)
    echo "   Status: $STATUS"
    if [ "$STATUS" = "SUCCEEDED" ]; then
        echo " Job completed successfully!"
        break
    elif [ "$STATUS" = "FAILED" ] || [ "$STATUS" = "STOPPED" ]; then
        echo "❌ Job failed!"
        aws glue get-job-run --job-name $JOB_NAME --run-id $RUN_ID --region $REGION --query 'JobRun.ErrorMessage' --output text
        break
    fi
    sleep 15
done

# Step 8: Check output
echo "📊Step 8: Checking output..."
aws s3 ls s3://$BUCKET/output/report/ --recursive

echo ""
echo " E2E Test Complete!"
echo "   Input:  s3://$BUCKET/raw/"
echo "   Output: s3://$BUCKET/output/report/"
echo "   To view: aws s3 ls s3://$BUCKET/output/report/"
