import subprocess


def dot_to_png(dot_path, output_png):
    """
    Requires graphviz installed:
    brew install graphviz
    """

    subprocess.run([
        "dot",
        "-Tpng",
        dot_path,
        "-o",
        output_png
    ])
