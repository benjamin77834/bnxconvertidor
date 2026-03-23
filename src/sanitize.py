import re


def clean_output(code: str) -> str:

    # limpia basura tipo sed
    code = code.replace("%", "")
    code = re.sub(r"\n{3,}", "\n\n", code)
    code = re.sub(r"show\([^)]*$", "show()", code)

    return code.strip()