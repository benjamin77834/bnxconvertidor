# Auto-generated from COBOL

NODE Raw_CUSTOMER_FILE : SOURCE
NODE Raw_TRANSACTION_FILE : SOURCE
NODE Raw_ACCOUNT_FILE : SOURCE

SUBGRAPH Ingestion {
  NODE Clean_CUSTOMER_FILE : TRANSFORM
  NODE Clean_TRANSACTION_FILE : TRANSFORM
  NODE Clean_ACCOUNT_FILE : TRANSFORM
}

SUBGRAPH Process {
  NODE filter_active_customers : TRANSFORM
  NODE filter_valid_transactions : TRANSFORM
  NODE join_customer_tx : JOIN
  NODE compute_totals : TRANSFORM
}

NODE Write_REPORT_FILE : SINK
NODE Write_ERROR_FILE : SINK

Raw_CUSTOMER_FILE -> Clean_CUSTOMER_FILE
Raw_TRANSACTION_FILE -> Clean_TRANSACTION_FILE
Raw_ACCOUNT_FILE -> Clean_ACCOUNT_FILE
Clean_CUSTOMER_FILE -> filter_active_customers
Clean_TRANSACTION_FILE -> filter_active_customers
Clean_ACCOUNT_FILE -> filter_active_customers
filter_active_customers -> filter_valid_transactions
filter_valid_transactions -> join_customer_tx
join_customer_tx -> compute_totals
compute_totals -> Write_REPORT_FILE
compute_totals -> Write_ERROR_FILE