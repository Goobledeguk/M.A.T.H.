"""Command-line front end: REPL, script files, and one-off expressions."""

import argparse
import sys

from .ast_nodes import format_ast
from .errors import MathError
from .interpreter import Interpreter, format_value
from .lexer import tokenize
from .parser import parse


def _process(source, interpreter, show_tokens=False, show_ast=False):
    if show_tokens:
        for t in tokenize(source):
            print(f"{t.line}:{t.column:<3} {t.type.name:<9} {t.lexeme!r}")
        return
    if show_ast:
        print(format_ast(parse(source)))
        return
    for value in interpreter.run(source):
        print(format_value(value))


def _repl(interpreter, show_tokens, show_ast):
    print("M.A.T.H. interpreter -- type 'exit' to quit")
    while True:
        try:
            line = input("math> ")
        except (EOFError, KeyboardInterrupt):
            print()
            return 0
        if line.strip() in ("exit", "quit"):
            return 0
        if not line.strip():
            continue
        try:
            _process(line, interpreter, show_tokens, show_ast)
        except MathError as err:
            print(err)


def main(argv=None):
    ap = argparse.ArgumentParser(prog="mathcalc",
                                 description="M.A.T.H. - Mathematical Analyzer and Token Handler")
    ap.add_argument("file", nargs="?", help="script to run (omit for an interactive prompt)")
    ap.add_argument("-e", "--expr", help="evaluate a single expression and exit")
    ap.add_argument("--tokens", action="store_true", help="print the token stream instead of running")
    ap.add_argument("--ast", action="store_true", help="print the syntax tree instead of running")
    args = ap.parse_args(argv)

    interpreter = Interpreter()
    try:
        if args.expr is not None:
            _process(args.expr, interpreter, args.tokens, args.ast)
        elif args.file:
            with open(args.file, encoding="utf-8") as fh:
                _process(fh.read(), interpreter, args.tokens, args.ast)
        else:
            return _repl(interpreter, args.tokens, args.ast)
    except MathError as err:
        print(err, file=sys.stderr)
        return 1
    except OSError as err:
        print(f"cannot read file: {err}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
