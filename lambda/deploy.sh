#!/bin/bash
# Deploy BNX Lambda function
# Usage: ./lambda/deploy.sh <function-name> <region>

FUNCTION_NAME=${1:-bnx-compiler}
REGION=${2:-us-east-1}
ZIP_FILE="lambda_package.zip"

echo "📦 Packaging Lambda..."

# Clean
rm -f $ZIP_FILE

# Package source code
zip -r $ZIP_FILE lambda/handler.py src/ -x "src/__pycache__/*" "src/**/__pycache__/*"

echo "🚀 Deploying to $FUNCTION_NAME in $REGION..."

# Check if function exists
if aws lambda get-function --function-name $FUNCTION_NAME --region $REGION 2>/dev/null; then
    # Update existing
    aws lambda update-function-code \
        --function-name $FUNCTION_NAME \
        --zip-file fileb://$ZIP_FILE \
        --region $REGION
    echo "✅ Updated $FUNCTION_NAME"
else
    # Create new
    echo "Creating new function..."
    echo "⚠️  You need to create the function first:"
    echo ""
    echo "aws lambda create-function \\"
    echo "  --function-name $FUNCTION_NAME \\"
    echo "  --runtime python3.11 \\"
    echo "  --handler lambda.handler.handler \\"
    echo "  --zip-file fileb://$ZIP_FILE \\"
    echo "  --role arn:aws:iam::<ACCOUNT_ID>:role/<LAMBDA_ROLE> \\"
    echo "  --timeout 30 \\"
    echo "  --memory-size 256 \\"
    echo "  --region $REGION"
    echo ""
    echo "Then enable Function URL:"
    echo ""
    echo "aws lambda create-function-url-config \\"
    echo "  --function-name $FUNCTION_NAME \\"
    echo "  --auth-type NONE \\"
    echo "  --cors '{\"AllowOrigins\":[\"*\"],\"AllowMethods\":[\"POST\"],\"AllowHeaders\":[\"Content-Type\"]}' \\"
    echo "  --region $REGION"
fi

rm -f $ZIP_FILE
echo "🏁 Done"
