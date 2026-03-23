from src.migrator.compiler.engine import compile_graph


def run(mp, xfr, dml):
    return compile_graph(mp, xfr, dml)