import re


def parse_sql(sql: str):
    """
    Parses a simple SQL statement into a structured dictionary (IR).
    Supports:
      SELECT ... FROM ... JOIN ... ON ... WHERE ...
    """

    sql = sql.strip().replace("\n", " ")

    # Normalizar espacios
    sql = re.sub(r"\s+", " ", sql)

    result = {
        "type": "SELECT",
        "tables": [],
        "joins": [],
        "columns": [],
        "where": None
    }

    # SELECT
    select_match = re.search(r"select (.*?) from", sql, re.IGNORECASE)
    if select_match:
        cols = select_match.group(1)
        result["columns"] = [c.strip() for c in cols.split(",")]

    # FROM
    from_match = re.search(r"from ([a-zA-Z0-9_]+)", sql, re.IGNORECASE)
    if from_match:
        result["tables"].append(from_match.group(1))

    # JOIN
    join_matches = re.findall(
        r"join ([a-zA-Z0-9_]+) on (.+?)(?: join| where|$)",
        sql,
        re.IGNORECASE
    )

    for table, condition in join_matches:
        result["joins"].append({
            "table": table,
            "condition": condition.strip()
        })

    # WHERE
    where_match = re.search(r"where (.+)$", sql, re.IGNORECASE)
    if where_match:
        result["where"] = where_match.group(1).strip()

    return result