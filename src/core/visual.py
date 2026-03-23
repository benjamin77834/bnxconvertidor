def export_html(lineage):

    html = """
    <html>
    <body>
    <h1>BNX v10 Lineage</h1>
    <table border="1">
        <tr><th>Target</th><th>Sources</th></tr>
    """

    for k, v in lineage.items():
        html += f"<tr><td>{k}</td><td>{v}</td></tr>"

    html += """
    </table>
    </body>
    </html>
    """

    with open("lineage.html", "w") as f:
        f.write(html)
