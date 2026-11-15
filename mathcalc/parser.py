"""Syntactic analysis (stage 3): recursive descent parser.

Context-free grammar (BNF), lowest precedence first:

    program     ::= SEP* ( statement ( SEP+ statement )* )? SEP* EOF
    statement   ::= IDENT '=' statement
                  | comparison
    comparison  ::= range ( ( '==' | '!=' | '<' | '<=' | '>' | '>=' ) range )*
    range       ::= additive ( '..' additive )?
    additive    ::= term ( ( '+' | '-' ) term )*
    term        ::= unary ( ( '*' | '//' | '///' | '//:' | '/:' | ':/+' ) unary )*
    unary       ::= ( '-' | ':/' | '::/' ) unary
                  | power
    power       ::= postfix ( '**' unary )?
    postfix     ::= primary ( ':/!' | '://!' )*
    primary     ::= NUMBER | IDENT
                  | '(' statement ')'
                  | '[' ( statement ( ',' statement )* )? ']'

SEP is a newline or ';'. '**' is right-associative.
"""

from . import ast_nodes as ast
from .errors import MathSyntaxError
from .lexer import tokenize
from .tokens import CANONICAL, TokenType as T

_RELATIONAL = (T.EQ, T.NE, T.LT, T.LE, T.GT, T.GE)
_TERM_OPS = (T.STAR, T.FLOORDIV, T.CEILDIV, T.MOD, T.FRAC, T.HYPOT)


def _describe(token):
    if token.type is T.EOF:
        return "end of input"
    if token.type is T.SEP:
        return "end of line"
    return repr(token.lexeme)


class Parser:
    def __init__(self, tokens):
        self.tokens = tokens
        self.pos = 0

    # -- helpers ---------------------------------------------------------
    def _peek(self, offset=0):
        return self.tokens[min(self.pos + offset, len(self.tokens) - 1)]

    def _check(self, *types):
        return self._peek().type in types

    def _advance(self):
        tok = self._peek()
        if tok.type is not T.EOF:
            self.pos += 1
        return tok

    def _match(self, *types):
        return self._advance() if self._check(*types) else None

    def _expect(self, token_type, what):
        if self._check(token_type):
            return self._advance()
        tok = self._peek()
        raise MathSyntaxError(f"expected {what} but found {_describe(tok)}", tok.line, tok.column)

    def _skip_seps(self):
        while self._check(T.SEP):
            self._advance()

    # -- grammar rules -----------------------------------------------------
    def parse(self):
        statements = []
        self._skip_seps()
        while not self._check(T.EOF):
            statements.append(self.statement())
            if not self._check(T.EOF):
                self._expect(T.SEP, "end of statement")
            self._skip_seps()
        return ast.Program(tuple(statements), line=1, column=1)

    def statement(self):
        if self._check(T.IDENT) and self._peek(1).type is T.ASSIGN:
            name = self._advance()
            self._advance()
            value = self.statement()
            return ast.Assign(name.lexeme, value, line=name.line, column=name.column)
        node = self.comparison()
        if self._check(T.ASSIGN):
            tok = self._peek()
            raise MathSyntaxError("cannot assign to this expression; the left side must be a name",
                                  tok.line, tok.column)
        return node

    def comparison(self):
        node = self.range_expr()
        while self._check(*_RELATIONAL):
            op = self._advance()
            right = self.range_expr()
            node = ast.BinaryOp(CANONICAL[op.type], node, right, line=op.line, column=op.column)
        return node

    def range_expr(self):
        node = self.additive()
        if self._check(T.RANGE):
            op = self._advance()
            right = self.additive()
            node = ast.BinaryOp("..", node, right, line=op.line, column=op.column)
        return node

    def additive(self):
        node = self.term()
        while self._check(T.PLUS, T.MINUS):
            op = self._advance()
            right = self.term()
            node = ast.BinaryOp(CANONICAL[op.type], node, right, line=op.line, column=op.column)
        return node

    def term(self):
        node = self.unary()
        while self._check(*_TERM_OPS):
            op = self._advance()
            right = self.unary()
            node = ast.BinaryOp(CANONICAL[op.type], node, right, line=op.line, column=op.column)
        return node

    def unary(self):
        if self._check(T.MINUS, T.SQRT, T.CBRT):
            op = self._advance()
            operand = self.unary()
            return ast.UnaryOp(CANONICAL[op.type], operand, line=op.line, column=op.column)
        return self.power()

    def power(self):
        base = self.postfix()
        if self._check(T.POW):
            op = self._advance()
            exponent = self.unary()          # right-associative, allows 2 ** -1
            return ast.BinaryOp("**", base, exponent, line=op.line, column=op.column)
        return base

    def postfix(self):
        node = self.primary()
        while self._check(T.FACT, T.DFACT):
            op = self._advance()
            node = ast.PostfixOp(CANONICAL[op.type], node, line=op.line, column=op.column)
        return node

    def primary(self):
        tok = self._peek()
        if tok.type is T.NUMBER:
            self._advance()
            return ast.Number(tok.value, line=tok.line, column=tok.column)
        if tok.type is T.IDENT:
            self._advance()
            return ast.Name(tok.lexeme, line=tok.line, column=tok.column)
        if tok.type is T.LPAREN:
            self._advance()
            node = self.statement()
            self._expect(T.RPAREN, "')'")
            return node
        if tok.type is T.LBRACKET:
            self._advance()
            elements = []
            if not self._check(T.RBRACKET):
                elements.append(self.statement())
                while self._match(T.COMMA):
                    elements.append(self.statement())
            self._expect(T.RBRACKET, "']' or ','")
            return ast.ArrayLiteral(tuple(elements), line=tok.line, column=tok.column)
        raise MathSyntaxError(f"unexpected {_describe(tok)}; expected a number, name, '(' or '['",
                              tok.line, tok.column)


def parse(source):
    """Source text -> Program AST."""
    return Parser(tokenize(source)).parse()
