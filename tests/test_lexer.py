import unittest

from mathcalc import LexicalError, tokenize
from mathcalc.lexer import build_dfa
from mathcalc.tokens import TokenType as T


def types(source):
    return [t.type for t in tokenize(source)][:-1]       # drop EOF


class OperatorTokens(unittest.TestCase):
    """Each operator from the proposal's tables must lex as ONE token."""

    def test_every_operator_symbol(self):
        cases = {
            ":/": T.SQRT, "::/": T.CBRT, "://": T.CBRT, ":/!": T.FACT, "://!": T.DFACT,
            "///": T.CEILDIV, "//:": T.MOD, ":/+": T.HYPOT, "**": T.POW,
            "//": T.FLOORDIV, "/:": T.FRAC,
        }
        for symbol, expected in cases.items():
            with self.subTest(symbol=symbol):
                toks = tokenize(symbol)
                self.assertEqual([t.type for t in toks], [expected, T.EOF])
                self.assertEqual(toks[0].lexeme, symbol)

    def test_maximal_munch(self):
        self.assertEqual(types("7 ://! 2"), [T.NUMBER, T.DFACT, T.NUMBER])
        self.assertEqual(types("5:/!"), [T.NUMBER, T.FACT])
        self.assertEqual(types("2***3"), [T.NUMBER, T.POW, T.STAR, T.NUMBER])

    def test_dfa_start_state_and_accepting_states(self):
        transitions, accepting = build_dfa()
        self.assertIn(0, transitions)
        self.assertNotIn(0, accepting)                   # q0 accepts nothing
        # ':' alone is not an operator (slide 9: q1 is not accepting)
        q1 = transitions[0][":"]
        self.assertNotIn(q1, accepting)


class LiteralsAndLayout(unittest.TestCase):
    def test_numbers(self):
        toks = tokenize("12 3.5")
        self.assertEqual(toks[0].value, 12)
        self.assertIsInstance(toks[0].value, int)
        self.assertEqual(toks[1].value, 3.5)

    def test_range_does_not_swallow_decimal_point(self):
        self.assertEqual(types("1..5"), [T.NUMBER, T.RANGE, T.NUMBER])

    def test_identifiers_and_assignment(self):
        self.assertEqual(types("val = 1"), [T.IDENT, T.ASSIGN, T.NUMBER])

    def test_comments_and_whitespace_ignored(self):
        self.assertEqual(types("1 + 2  # note"), [T.NUMBER, T.PLUS, T.NUMBER])

    def test_newlines_separate_statements_except_inside_brackets(self):
        self.assertEqual(types("1\n2"), [T.NUMBER, T.SEP, T.NUMBER])
        self.assertEqual(types("(1\n+ 2)"), [T.LPAREN, T.NUMBER, T.PLUS, T.NUMBER, T.RPAREN])

    def test_positions(self):
        toks = tokenize("1\n  22")
        self.assertEqual((toks[2].line, toks[2].column), (2, 3))


class LexicalErrors(unittest.TestCase):
    def test_unknown_character(self):
        with self.assertRaises(LexicalError) as cm:
            tokenize("3 $ 4")
        self.assertEqual((cm.exception.line, cm.exception.column), (1, 3))

    def test_lone_colon_and_bang(self):
        for bad in (":", "5 !", "1 . 2"):
            with self.subTest(bad=bad), self.assertRaises(LexicalError):
                tokenize(bad)


if __name__ == "__main__":
    unittest.main()
