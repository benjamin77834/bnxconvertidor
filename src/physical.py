def build_physical_plan(logical_plan):

    print("\n⚙️ Building Physical Plan (Spark strategy selection)")

    # aquí decides estrategias futuras:
    # - broadcast join
    # - shuffle join
    # - parquet scan pushdown

    return logical_plan