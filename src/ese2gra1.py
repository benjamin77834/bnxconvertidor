#!/bin/bash
# BNX End-to-End Test on AWS Glue
# Usage: ./e2e/run_e2e.sh

BUCKET="bnx-e2e-test"
REGION="us-east-1"
GLUE_ROLE="arn:aws:iam::034711235858:role/lambdarol"
JOB_NAME="bnx-e2e-testg1"
PATHBNX="/Users/benjamingarcia/sam/bnxconvertidor"
echo " BNX End-to-End Test"
echo "======================"

# Step 1: Create S3 bucket
echo " Step 1: Creating S3 bucket..."
aws s3 mb s3://$BUCKET --region $REGION 2>/dev/null || true

# Step 2: Upload test data
echo " Step 2: Uploading test data..."
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


# Step 3: Generate Glue code
echo " Step 3: Generating Glue code..."

##python3 $PATHBNX/main.py --project $PATHBNX/e2e/test.mp --xfr $PATHBNX/e2e/test.xfr --target glue --output $PATHBNX/e2e/glue_job.py

# Step 4: Upload script to S3
echo " Step 4: Uploading Glue script..."
aws s3 cp $PATHBNX/job3.py s3://$BUCKET/scripts/glue_job.py

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
