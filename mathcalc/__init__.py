"""M.A.T.H. -- Mathematical Analyzer and Token Handler.

A small domain-specific language for computational mathematics, built as the
pipeline  source -> Lexer -> Parser (CFG) -> AST -> tree-walk Interpreter.

    >>> from mathcalc import evaluate
    >>> evaluate(":/ 16")
    4.0
    >>> evaluate("3 :/+ 4")
    5.0
"""

from .ast_nodes import format_ast
from .errors import LexicalError, MathError, MathSyntaxError, SemanticError
from .interpreter import Interpreter, format_value
from .lexer import tokenize
from .parser import parse

__version__ = "0.1.0"

__all__ = [
    "evaluate", "run", "Interpreter", "tokenize", "parse", "format_ast", "format_value",
    "MathError", "LexicalError", "MathSyntaxError", "SemanticError",
]


def evaluate(source, env=None):
    """Evaluate M.A.T.H. source and return the value of its last statement."""
    return Interpreter(env).evaluate(source)


def run(source, env=None):
    """Evaluate M.A.T.H. source and return a list with one value per statement."""
    return Interpreter(env).run(source)
