# py2spark.cli — interfaz de linea de comandos del conversor Python->PySpark 3.
#
# Uso:
#   py2spark convert entrada.py                 # imprime el PySpark a stdout
#   py2spark convert entrada.py -o salida.py    # escribe a archivo
#   py2spark convert entrada.py --json          # salida JSON {code,warnings,unsupported}
#   py2spark convert -   < entrada.py           # lee de stdin
#   cat script.py | py2spark convert            # (equivalente)
#
# Codigos de salida:
#   0  conversion realizada (aunque haya TODOs/unsupported)
#   1  el codigo de entrada no es Python valido
#   2  error de uso (argumentos)

import argparse
import json
import sys

from .converter import convert_code
from . import __version__


def _read_input(path):
    if path in (None, "-"):
        return sys.stdin.read()
    with open(path, "r", encoding="utf-8", errors="replace") as f:
        return f.read()


def _cmd_convert(args):
    try:
        src = _read_input(args.input)
    except OSError as e:
        print(f"error: no se pudo leer '{args.input}': {e}", file=sys.stderr)
        return 2

    result = convert_code(src, add_preamble=not args.no_preamble)

    if args.json:
        out = json.dumps(result, ensure_ascii=False, indent=2)
        _emit(out, args.output)
        return 0 if result["ok"] else 1

    if not result["ok"]:
        for u in result["unsupported"]:
            print(f"error: {u}", file=sys.stderr)
        return 1

    # Avisos a stderr (no ensucian el codigo de stdout).
    for w in result["warnings"]:
        print(f"warning: {w}", file=sys.stderr)
    for u in result["unsupported"]:
        print(f"revisar: {u}", file=sys.stderr)

    _emit(result["code"], args.output)
    return 0


def _emit(text, output):
    if output and output != "-":
        with open(output, "w", encoding="utf-8") as f:
            f.write(text if text.endswith("\n") else text + "\n")
        print(f"[py2spark] escrito: {output}", file=sys.stderr)
    else:
        sys.stdout.write(text if text.endswith("\n") else text + "\n")


def build_parser():
    p = argparse.ArgumentParser(
        prog="py2spark",
        description="Convierte codigo Python (pandas) a PySpark 3.",
    )
    p.add_argument("--version", action="version", version=f"py2spark {__version__}")
    sub = p.add_subparsers(dest="command")

    conv = sub.add_parser("convert", help="Convierte un archivo/stdin Python a PySpark.")
    conv.add_argument("input", nargs="?", default="-",
                      help="Archivo .py de entrada (o '-' / omitido para stdin).")
    conv.add_argument("-o", "--output", default="-",
                      help="Archivo de salida (o '-' / omitido para stdout).")
    conv.add_argument("--json", action="store_true",
                      help="Emitir JSON con code/warnings/unsupported.")
    conv.add_argument("--no-preamble", action="store_true",
                      help="No agregar el preambulo SparkSession/imports.")
    conv.set_defaults(func=_cmd_convert)
    return p


def main(argv=None):
    parser = build_parser()
    args = parser.parse_args(argv)
    if not getattr(args, "command", None):
        parser.print_help(sys.stderr)
        return 2
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
