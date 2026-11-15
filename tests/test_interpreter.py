import io
import unittest
from contextlib import redirect_stderr, redirect_stdout
from fractions import Fraction

from mathcalc import (Interpreter, LexicalError, MathSyntaxError, SemanticError,
                      evaluate, run)
from mathcalc.cli import main
from mathcalc.interpreter import format_value


class ProposalExamples(unittest.TestCase):
    """The worked examples from the operator tables (slides 7-8) and slide 10."""

    def test_table_examples(self):
        cases = [
            (":/ 16", 4.0),
            ("::/ 27", 3.0),
            ("5 :/!", 120),
            ("7 ://!", 105),
            ("7 /// 2", 4),
            ("7 //: 3", 1),
            ("3 :/+ 4", 5),
            ("2 ** 3", 8),
        ]
        for source, expected in cases:
            with self.subTest(source=source):
                self.assertEqual(evaluate(source), expected)

    def test_result_types_match_the_tables(self):
        self.assertIsInstance(evaluate(":/ 16"), float)
        self.assertIsInstance(evaluate("2 ** 3"), int)
        self.assertIsInstance(evaluate("7 /// 2"), int)

    def test_slide_10_example(self):
        self.assertAlmostEqual(evaluate("(val = ::/ 27 + (1 /: 3))"), 3 + 1 / 3)

    def test_cube_root_dfa_alias(self):
        self.assertEqual(evaluate("://64"), 4.0)


class Arithmetic(unittest.TestCase):
    def test_precedence_and_parentheses(self):
        self.assertEqual(evaluate("1 + 2 * 3"), 7)
        self.assertEqual(evaluate("(1 + 2) * 3"), 9)
        self.assertEqual(evaluate("2 ** 3 ** 2"), 512)
        self.assertEqual(evaluate("-2 ** 2"), -4)
        self.assertEqual(evaluate(":/ 16 + 9"), 13.0)

    def test_negative_roots_and_cubes(self):
        self.assertEqual(evaluate("::/ -27"), -3.0)

    def test_factorials(self):
        self.assertEqual(evaluate("0 :/!"), 1)
        self.assertEqual(evaluate("6 ://!"), 48)
        self.assertEqual(evaluate("0 ://!"), 1)
        self.assertEqual(evaluate("5.0 :/!"), 120)

    def test_division_family(self):
        self.assertEqual(evaluate("7 // 2"), 3)
        self.assertEqual(evaluate("-7 /// 2"), -3)
        self.assertEqual(evaluate("6 /// 3"), 2)
        self.assertEqual(evaluate("10 //: 4"), 2)

    def test_fractions_are_exact(self):
        self.assertEqual(evaluate("1 /: 3"), Fraction(1, 3))
        self.assertEqual(evaluate("(1 /: 3) + (1 /: 6)"), Fraction(1, 2))
        self.assertEqual(evaluate("0.1 /: 1"), Fraction(1, 10))
        self.assertEqual(format_value(evaluate("2 /: 4")), "1/2")
        self.assertEqual(format_value(evaluate("4 /: 2")), "2")

    def test_negative_exponent_is_exact(self):
        self.assertEqual(evaluate("2 ** -2"), Fraction(1, 4))
        self.assertEqual(evaluate("(-2) ** -3"), Fraction(-1, 8))


class Variables(unittest.TestCase):
    def test_assignment_and_reuse(self):
        self.assertEqual(run("a = 3\nb = 4\na :/+ b"), [3, 4, 5.0])

    def test_state_persists_in_interpreter(self):
        interp = Interpreter()
        interp.evaluate("x = 10")
        self.assertEqual(interp.evaluate("x * 2"), 20)

    def test_initial_env(self):
        self.assertEqual(evaluate("n :/!", env={"n": 4}), 24)


class ArraysAndRanges(unittest.TestCase):
    def test_ranges(self):
        self.assertEqual(evaluate("1 .. 5"), [1, 2, 3, 4, 5])
        self.assertEqual(evaluate("3 .. 1"), [3, 2, 1])
        self.assertEqual(evaluate("1 .. 2 + 2"), [1, 2, 3, 4])

    def test_elementwise_operators(self):
        self.assertEqual(evaluate("(1 .. 4) ** 2"), [1, 4, 9, 16])
        self.assertEqual(evaluate(":/ [4, 9, 16]"), [2.0, 3.0, 4.0])
        self.assertEqual(evaluate("[1, 2] + [10, 20]"), [11, 22])
        self.assertEqual(evaluate("(1 .. 4) :/!"), [1, 2, 6, 24])

    def test_relational_comparisons(self):
        self.assertEqual(evaluate("[1, 2, 3] >= 2"), [False, True, True])
        self.assertEqual(evaluate("[1, 5] == [1, 4]"), [True, False])
        self.assertIs(evaluate("2 < 3"), True)
        self.assertIs(evaluate("1 /: 2 == 0.5"), True)

    def test_formatting(self):
        self.assertEqual(format_value([1, Fraction(1, 2), True]), "[1, 1/2, true]")


class SemanticErrors(unittest.TestCase):
    def test_invalid_operations(self):
        bad = [
            ":/ -4", "5 //: 0", "5 // 0", "5 /// 0", "1 /: 0", "0 ** -1", "(-8) ** 0.5",
            "(-1) :/!", "2.5 :/!", "5000 :/!", "x", "[1, 2] + [1]", "(1 < 2) + 1",
            "1.5 .. 3", "2 ** 999999999", "[1] .. 3",
        ]
        for source in bad:
            with self.subTest(source=source), self.assertRaises(SemanticError):
                evaluate(source)

    def test_error_points_at_the_operator(self):
        with self.assertRaises(SemanticError) as cm:
            evaluate("1 + 5 //: 0")
        self.assertEqual((cm.exception.line, cm.exception.column), (1, 7))
        self.assertIn("SemanticError at line 1, column 7", str(cm.exception))


class Pipeline(unittest.TestCase):
    def test_each_stage_reports_its_own_error(self):
        with self.assertRaises(LexicalError):
            evaluate("3 @ 4")
        with self.assertRaises(MathSyntaxError):
            evaluate("3 +")
        with self.assertRaises(SemanticError):
            evaluate(":/ -1")

    def test_empty_source(self):
        self.assertIsNone(evaluate(""))


class CommandLine(unittest.TestCase):
    def call(self, *argv):
        out, err = io.StringIO(), io.StringIO()
        with redirect_stdout(out), redirect_stderr(err):
            code = main(list(argv))
        return code, out.getvalue(), err.getvalue()

    def test_expression(self):
        self.assertEqual(self.call("-e", "3 :/+ 4"), (0, "5.0\n", ""))

    def test_error_exit_code(self):
        code, out, err = self.call("-e", ":/ -1")
        self.assertEqual(code, 1)
        self.assertIn("SemanticError", err)

    def test_tokens_and_ast_flags(self):
        self.assertIn("SQRT", self.call("--tokens", "-e", ":/ 9")[1])
        self.assertIn("UnaryOp(:/)", self.call("--ast", "-e", ":/ 9")[1])


if __name__ == "__main__":
    unittest.main()
