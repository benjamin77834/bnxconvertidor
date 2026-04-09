"""
Creates small test Parquet files in S3 for end-to-end Glue test.
Run: python3 e2e/create_test_data.py <bucket-name>
"""
import sys
import json

BUCKET = sys.argv[1] if len(sys.argv) > 1 else "bnx-e2e-test"

# Generate CSV data (Glue can read CSV without pandas)
orders_csv = """order_id,customer_id,amount,status,order_date
ORD001,C001,150.00,completed,2026-01-15
ORD002,C002,250.50,completed,2026-01-16
ORD003,C001,75.00,cancelled,2026-01-17
ORD004,C003,500.00,completed,2026-01-18
ORD005,C002,120.00,completed,2026-01-19
ORD006,C001,300.00,completed,2026-01-20
"""

customers_csv = """customer_id,name,email,region
C001,Juan Garcia,[email],MX-NORTH
C002,Maria Lopez,[email],MX-SOUTH
C003,Carlos Ruiz,[email],MX-CENTER
"""

print(f"Upload these files to S3:")
print(f"  aws s3 mb s3://{BUCKET}")
print(f"  echo '{orders_csv.strip()}' | aws s3 cp - s3://{BUCKET}/raw/orders/data.csv")
print(f"  echo '{customers_csv.strip()}' | aws s3 cp - s3://{BUCKET}/raw/customers/data.csv")
print(f"\nDone! Files ready in s3://{BUCKET}/raw/")
