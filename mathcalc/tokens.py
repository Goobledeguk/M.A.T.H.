"""Token definitions for the M.A.T.H. language."""

from dataclasses import dataclass
from enum import Enum, auto


class TokenType(Enum):
    # literals / names
    NUMBER = auto()
    IDENT = auto()
    # M.A.T.H. operators
    SQRT = auto()       # :/
    CBRT = auto()       # ::/
    FACT = auto()       # :/!
    DFACT = auto()      # ://!
    HYPOT = auto()      # :/+
    CEILDIV = auto()    # ///
    FLOORDIV = auto()   # //
    MOD = auto()        # //:
    FRAC = auto()       # /:
    POW = auto()        # **
    # basic arithmetic
    PLUS = auto()
    MINUS = auto()
    STAR = auto()
    # relational + ranges
    EQ = auto()
    NE = auto()
    LT = auto()
    LE = auto()
    GT = auto()
    GE = auto()
    RANGE = auto()
    # punctuation
    ASSIGN = auto()
    LPAREN = auto()
    RPAREN = auto()
    LBRACKET = auto()
    RBRACKET = auto()
    COMMA = auto()
    SEP = auto()        # newline or ';'
    EOF = auto()


# Every operator lexeme. The lexer's DFA is generated from this table.
# Order matters only for CANONICAL below (first lexeme listed per type wins).
OPERATOR_LEXEMES = {
    ":/": TokenType.SQRT,
    "::/": TokenType.CBRT,      # slide 7 table
    "://": TokenType.CBRT,      # slide 9 automaton (state q4) -- accepted as an alias
    ":/!": TokenType.FACT,
    "://!": TokenType.DFACT,
    ":/+": TokenType.HYPOT,
    "///": TokenType.CEILDIV,
    "//": TokenType.FLOORDIV,
    "//:": TokenType.MOD,
    "/:": TokenType.FRAC,
    "**": TokenType.POW,
    "+": TokenType.PLUS,
    "-": TokenType.MINUS,
    "*": TokenType.STAR,
    "==": TokenType.EQ,
    "!=": TokenType.NE,
    "<": TokenType.LT,
    "<=": TokenType.LE,
    ">": TokenType.GT,
    ">=": TokenType.GE,
    "..": TokenType.RANGE,
    "=": TokenType.ASSIGN,
    "(": TokenType.LPAREN,
    ")": TokenType.RPAREN,
    "[": TokenType.LBRACKET,
    "]": TokenType.RBRACKET,
    ",": TokenType.COMMA,
    ";": TokenType.SEP,
}

# TokenType -> the one symbol used for it in the AST and in error messages.
CANONICAL = {}
for _lexeme, _type in OPERATOR_LEXEMES.items():
    CANONICAL.setdefault(_type, _lexeme)


@dataclass(frozen=True)
class Token:
    type: TokenType
    lexeme: str
    value: object = None
    line: int = 1
    column: int = 1

    def __str__(self):
        return f"{self.type.name}({self.lexeme!r})"
