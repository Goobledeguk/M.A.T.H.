"""Lexical analysis (stage 2 of the pipeline).

Operators are recognised by a deterministic finite automaton (DFA). It is
generated from `OPERATOR_LEXEMES`, so it contains the states q0..qN of the
automaton on slide 9 plus the extra operators this implementation adds. The
lexer walks the DFA as far as it can and keeps the last accepting state
("maximal munch"), so `://!` is one token, not `:/` `/` `!`.

Numbers and identifiers are matched with regular expressions.
"""

import re

from .errors import LexicalError
from .tokens import OPERATOR_LEXEMES, Token, TokenType

_NUMBER = re.compile(r"\d+(?:\.\d+)?")
_IDENT = re.compile(r"[A-Za-z_][A-Za-z0-9_]*")


def build_dfa(lexemes=OPERATOR_LEXEMES):
    """Build the operator DFA. Returns (transitions, accepting).

    transitions: {state: {char: next_state}}, state 0 is the start state (q0)
    accepting:   {state: TokenType} for states that end a complete operator
    """
    transitions = {0: {}}
    accepting = {}
    for lexeme, token_type in lexemes.items():
        state = 0
        for ch in lexeme:
            nxt = transitions[state].get(ch)
            if nxt is None:
                nxt = len(transitions)
                transitions[nxt] = {}
                transitions[state][ch] = nxt
            state = nxt
        accepting[state] = token_type
    return transitions, accepting


_TRANSITIONS, _ACCEPTING = build_dfa()


class Lexer:
    def __init__(self, source):
        self.source = source

    def _scan_operator(self, start):
        """Run the DFA from `start`. Returns (token_type, length) or (None, 0)."""
        state, i = 0, start
        best_type, best_len = None, 0
        src = self.source
        while i < len(src):
            state = _TRANSITIONS[state].get(src[i])
            if state is None:
                break
            i += 1
            if state in _ACCEPTING:
                best_type, best_len = _ACCEPTING[state], i - start
        return best_type, best_len

    def tokenize(self):
        src, n = self.source, len(self.source)
        tokens = []
        i, line, line_start, depth = 0, 1, 0, 0

        def add_sep(lexeme, ln, col):
            # collapse repeated separators and ignore leading ones
            if tokens and tokens[-1].type is not TokenType.SEP:
                tokens.append(Token(TokenType.SEP, lexeme, None, ln, col))

        while i < n:
            ch = src[i]
            col = i - line_start + 1

            if ch in " \t\r":
                i += 1
                continue
            if ch == "#":                       # comment to end of line
                while i < n and src[i] != "\n":
                    i += 1
                continue
            if ch == "\n":
                if depth == 0:                  # newlines inside ( ) or [ ] are ignored
                    add_sep("\n", line, col)
                i += 1
                line += 1
                line_start = i
                continue

            m = _NUMBER.match(src, i)
            if m:
                text = m.group()
                value = float(text) if "." in text else int(text)
                tokens.append(Token(TokenType.NUMBER, text, value, line, col))
                i = m.end()
                continue

            m = _IDENT.match(src, i)
            if m:
                tokens.append(Token(TokenType.IDENT, m.group(), None, line, col))
                i = m.end()
                continue

            token_type, length = self._scan_operator(i)
            if token_type is None:
                raise LexicalError(f"unexpected character {ch!r}", line, col)

            lexeme = src[i:i + length]
            if token_type is TokenType.SEP:     # ';'
                add_sep(lexeme, line, col)
            else:
                tokens.append(Token(token_type, lexeme, None, line, col))
                if token_type in (TokenType.LPAREN, TokenType.LBRACKET):
                    depth += 1
                elif token_type in (TokenType.RPAREN, TokenType.RBRACKET):
                    depth = max(0, depth - 1)
            i += length

        tokens.append(Token(TokenType.EOF, "", None, line, n - line_start + 1))
        return tokens


def tokenize(source):
    """Convenience wrapper: source text -> list of Tokens (ending with EOF)."""
    return Lexer(source).tokenize()
