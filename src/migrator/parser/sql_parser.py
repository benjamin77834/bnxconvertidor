import re

def parse_sql(sql: str):
    sql = sql.strip().replace("\n", " ")
    sql = re.sub(r"\s+", " ", sql)

    result = {
        "columns": [],
        "tables": [],
        "joins": [],
        "where": None
    }

    select = re.search(r"select (.*?) from", sql, re.IGNORECASE)
    if select:
        result["columns"] = [c.strip() for c in select.group(1).split(",")]

    from_ = re.search(r"from ([a-zA-Z0-9_]+)", sql, re.IGNORECASE)
    if from_:
        result["tables"].append(from_.group(1))

    joins = re.findall(
        r"join ([a-zA-Z0-9_]+) on (.+?)(?: join| where|$)",
        sql,
        re.IGNORECASE
    )

    for t, c in joins:
        result["joins"].append({"table": t, "condition": c})

    where = re.search(r"where (.+)$", sql, re.IGNORECASE)
    if where:
        result["where"] = where.group(1)

    return result