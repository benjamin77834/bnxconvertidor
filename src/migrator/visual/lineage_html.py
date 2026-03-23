def generate_lineage_html(lineage):

    rows = ""

    for k, v in lineage.items():
        rows += f"<tr><td>{k}</td><td>{v}</td></tr>"

    return f"""
    <html>
    <body>
    <h1>BNX Lineage</h1>
    <table border="1">
        <tr><th>Target</th><th>Sources</th></tr>
        {rows}
    </table>
    </body>
    </html>
    """


def save_html(path, html):
    open(path, "w").write(html)