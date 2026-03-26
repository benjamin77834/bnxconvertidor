def optimize_dag(dag):

    if dag is None:
        return {}

    optimized = {}

    for k, v in dag.items():
        clean_key = k.replace(";", "").strip()
        optimized[clean_key] = v

    return optimized