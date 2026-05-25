import os

PROJECT_ROOT = None


def init_project_root(path: str):
    global PROJECT_ROOT
    PROJECT_ROOT = os.path.abspath(path)


def resolve_path(p: str):
    if os.path.isabs(p):
        return p

    if PROJECT_ROOT is None:
        raise Exception("? PROJECT_ROOT not initialized")

    full = os.path.join(PROJECT_ROOT, p)

    if os.path.exists(full):
        return full

    raise FileNotFoundError(f"? NOT FOUND: {full}")