import re

def parse_xfr(path):
    """
    Parsea archivos .xfr con formato:
        NodeName:
          select col1, col2, ...
          where condition
    Retorna dict: { "nodename": { "select": "...", "where": "..." } }
    """
    xfr_map = {}
    current = None

    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            stripped = line.strip()

            if not stripped or stripped.startswith("#"):
                continue

            # Detecta cabecera de nodo: "NodeName:"
            if re.match(r"^\w+\s*:$", stripped):
                current = stripped.rstrip(":").strip().lower()
                xfr_map[current] = {"select": "*", "where": None}
                continue

            if current is None:
                continue

            m_select = re.match(r"(?i)^select\s+(.+)$", stripped)
            if m_select:
                xfr_map[current]["select"] = m_select.group(1).strip()
                continue

            m_where = re.match(r"(?i)^where\s+(.+)$", stripped)
            if m_where:
                xfr_map[current]["where"] = m_where.group(1).strip()
                continue

            m_group = re.match(r"(?i)^group_by\s+(.+)$", stripped)
            if m_group:
                xfr_map[current]["group_by"] = [c.strip() for c in m_group.group(1).split(",")]
                continue

            m_jkey = re.match(r"(?i)^join_key\s+(.+)$", stripped)
            if m_jkey:
                xfr_map[current]["join_key"] = m_jkey.group(1).strip()
                continue

            m_jtype = re.match(r"(?i)^join_type\s+(.+)$", stripped)
            if m_jtype:
                xfr_map[current]["join_type"] = m_jtype.group(1).strip()

    return xfr_map