"""Error types for the M.A.T.H. interpreter.

They mirror the three failure points in the proposal's system flow:
    "Throw lexical error"            -> LexicalError
    "Throw syntax or grammar error"  -> MathSyntaxError
    "Throw semantic validation error"-> SemanticError
"""


class MathError(Exception):
    """Base class for every error raised by the M.A.T.H. interpreter."""

    kind = "MathError"

    def __init__(self, message, line=None, column=None):
        super().__init__(message)
        self.message = message
        self.line = line
        self.column = column

    def at(self, node):
        """Attach the position of `node` if this error has none yet."""
        if self.line is None:
            self.line = getattr(node, "line", None)
            self.column = getattr(node, "column", None)
        return self

    def __str__(self):
        if self.line is not None:
            return f"{self.kind} at line {self.line}, column {self.column}: {self.message}"
        return f"{self.kind}: {self.message}"


class LexicalError(MathError):
    """Raised when the lexer meets a character or symbol that is not part of the language."""

    kind = "LexicalError"


class MathSyntaxError(MathError):
    """Raised when the token stream does not match the grammar."""

    kind = "SyntaxError"


class SemanticError(MathError):
    """Raised when a well-formed expression cannot be evaluated (e.g. sqrt of -1, 5 //: 0)."""

    kind = "SemanticError"
