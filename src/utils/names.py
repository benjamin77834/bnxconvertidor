from __future__ import annotations  # Python 3.8 (host del portal)
def norm(layer: str | None, name: str) -> str:
    if layer:
        return f"{layer}.{name}"
    return name


def strip_layer(name: str) -> str:
    return name.split(".")[-1]