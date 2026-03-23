def normalize_id(x: str):
    if x is None:
        return None
    return (
        str(x)
        .strip()
        .replace(".", "_")
        .replace("-", "_")
        .replace(" ", "_")
    )