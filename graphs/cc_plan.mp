# Auto-generated from Ab Initio PLAN: credit_card_daily

SUBGRAPH Phase_0 {
  NODE ingest_transactions : SOURCE
  NODE ingest_cardholders : SOURCE
  NODE ingest_merchants : SOURCE
  NODE ingest_fx_rates : SOURCE
  NODE ingest_limits : SOURCE
}

SUBGRAPH Phase_1 {
  NODE clean_transactions : TRANSFORM
  NODE clean_cardholders : TRANSFORM
}

SUBGRAPH Phase_2 {
  NODE dedup_transactions : DEDUP
}

SUBGRAPH Phase_3 {
  NODE enrich_tx_cardholder : JOIN
}

SUBGRAPH Phase_4 {
  NODE enrich_tx_merchant : JOIN
}

SUBGRAPH Phase_5 {
  NODE enrich_tx_fx : JOIN
}

SUBGRAPH Phase_6 {
  NODE enrich_tx_limits : JOIN
}

SUBGRAPH Phase_7 {
  NODE agg_daily_spend : TRANSFORM
  NODE agg_merchant_volume : TRANSFORM
  NODE risk_overlimit : TRANSFORM
  NODE fraud_detection : TRANSFORM
}

SUBGRAPH Phase_8 {
  NODE aml_screening : TRANSFORM
  NODE report_daily_summary : SINK
  NODE report_fraud_alerts : SINK
  NODE report_cardholder_statements : SINK
}

SUBGRAPH Phase_9 {
  NODE report_regulatory : SINK
  NODE notify_completion : SINK
}

ingest_transactions -> clean_transactions
ingest_cardholders -> clean_cardholders
clean_transactions -> dedup_transactions
dedup_transactions -> enrich_tx_cardholder
clean_cardholders -> enrich_tx_cardholder
enrich_tx_cardholder -> enrich_tx_merchant
ingest_merchants -> enrich_tx_merchant
enrich_tx_merchant -> enrich_tx_fx
ingest_fx_rates -> enrich_tx_fx
enrich_tx_fx -> enrich_tx_limits
ingest_limits -> enrich_tx_limits
enrich_tx_limits -> agg_daily_spend
enrich_tx_limits -> agg_merchant_volume
enrich_tx_limits -> risk_overlimit
agg_daily_spend -> risk_overlimit
enrich_tx_limits -> fraud_detection
agg_daily_spend -> fraud_detection
fraud_detection -> aml_screening
agg_daily_spend -> report_daily_summary
agg_merchant_volume -> report_daily_summary
fraud_detection -> report_fraud_alerts
aml_screening -> report_fraud_alerts
aml_screening -> report_regulatory
risk_overlimit -> report_regulatory
agg_daily_spend -> report_cardholder_statements
enrich_tx_limits -> report_cardholder_statements
report_daily_summary -> notify_completion
report_fraud_alerts -> notify_completion
report_regulatory -> notify_completion
report_cardholder_statements -> notify_completion