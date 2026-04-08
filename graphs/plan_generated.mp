# Auto-generated from Ab Initio PLAN: daily_banking_batch

SUBGRAPH Phase_0 {
  NODE ingest_customers : SOURCE
  NODE ingest_transactions : SOURCE
  NODE ingest_accounts : SOURCE
  NODE ingest_cards : SOURCE
  NODE ingest_fx_rates : SOURCE
}

SUBGRAPH Phase_1 {
  NODE clean_customers : TRANSFORM
  NODE clean_transactions : TRANSFORM
  NODE clean_accounts : TRANSFORM
}

SUBGRAPH Phase_2 {
  NODE dedup_transactions : DEDUP
}

SUBGRAPH Phase_3 {
  NODE enrich_tx_with_customer : JOIN
}

SUBGRAPH Phase_4 {
  NODE enrich_tx_with_account : JOIN
}

SUBGRAPH Phase_5 {
  NODE enrich_tx_with_fx : JOIN
}

SUBGRAPH Phase_6 {
  NODE agg_daily_totals : TRANSFORM
  NODE agg_customer_balance : TRANSFORM
  NODE agg_product_revenue : TRANSFORM
  NODE aml_detection : TRANSFORM
}

SUBGRAPH Phase_7 {
  NODE risk_scoring : TRANSFORM
  NODE report_regulatory : SINK
  NODE report_finance : SINK
}

SUBGRAPH Phase_8 {
  NODE report_risk_dashboard : SINK
  NODE notify_completion : SINK
}

ingest_customers -> clean_customers
ingest_transactions -> clean_transactions
ingest_accounts -> clean_accounts
clean_transactions -> dedup_transactions
dedup_transactions -> enrich_tx_with_customer
clean_customers -> enrich_tx_with_customer
enrich_tx_with_customer -> enrich_tx_with_account
clean_accounts -> enrich_tx_with_account
enrich_tx_with_account -> enrich_tx_with_fx
ingest_fx_rates -> enrich_tx_with_fx
enrich_tx_with_fx -> agg_daily_totals
enrich_tx_with_fx -> agg_customer_balance
enrich_tx_with_fx -> agg_product_revenue
agg_customer_balance -> risk_scoring
enrich_tx_with_fx -> risk_scoring
enrich_tx_with_fx -> aml_detection
risk_scoring -> aml_detection
agg_daily_totals -> report_regulatory
aml_detection -> report_regulatory
agg_daily_totals -> report_finance
agg_customer_balance -> report_finance
agg_product_revenue -> report_finance
risk_scoring -> report_risk_dashboard
aml_detection -> report_risk_dashboard
report_regulatory -> notify_completion
report_finance -> notify_completion
report_risk_dashboard -> notify_completion