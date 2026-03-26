def apply_rules(df):

    df = df.withColumn(
        "risk_score",
        (df["amount"] * 0.4) + (df["txn_count"] * 0.6)
    )

    df = df.withColumn(
        "fraud_flag",
        df["risk_score"] > 0.75
    )

    return df