import unittest

from mathcalc import MathSyntaxError, parse
from mathcalc import ast_nodes as ast


def expr(source):
    """Parse a single expression and return its AST node."""
    return parse(source).statements[0]


class Precedence(unittest.TestCase):
    def test_multiplicative_binds_tighter_than_additive(self):
        node = expr("1 + 2 * 3")
        self.assertEqual(node.op, "+")
        self.assertEqual(node.right.op, "*")

    def test_power_is_right_associative(self):
        node = expr("2 ** 3 ** 2")
        self.assertEqual(node.op, "**")
        self.assertEqual(node.right.op, "**")

    def test_root_binds_tighter_than_addition(self):
        node = expr(":/ 16 + 9")
        self.assertEqual(node.op, "+")
        self.assertIsInstance(node.left, ast.UnaryOp)

    def test_unary_minus_looser_than_power(self):
        node = expr("-2 ** 2")
        self.assertIsInstance(node, ast.UnaryOp)
        self.assertEqual(node.operand.op, "**")

    def test_postfix_factorial(self):
        node = expr("5 :/!")
        self.assertIsInstance(node, ast.PostfixOp)
        self.assertEqual(node.op, ":/!")

    def test_cube_root_alias_normalises(self):
        self.assertEqual(expr("://27").op, "::/")


class Structure(unittest.TestCase):
    def test_assignment_is_an_expression(self):
        node = expr("(val = ::/ 27 + (1 /: 3))")
        self.assertIsInstance(node, ast.Assign)
        self.assertEqual(node.name, "val")

    def test_multiple_statements(self):
        self.assertEqual(len(parse("1\n2; 3").statements), 3)

    def test_empty_program(self):
        self.assertEqual(parse("  # nothing\n").statements, ())

    def test_arrays(self):
        node = expr("[1, 2 + 3, []]")
        self.assertEqual(len(node.elements), 3)


class SyntaxErrors(unittest.TestCase):
    def test_bad_programs(self):
        for bad in ("3 +", "(1 + 2", "3 4", "* 3", "[1, 2", "3 = 4", ")", "1 :/+"):
            with self.subTest(bad=bad), self.assertRaises(MathSyntaxError):
                parse(bad)

    def test_error_position(self):
        with self.assertRaises(MathSyntaxError) as cm:
            parse("1\n3 + * 2")
        self.assertEqual(cm.exception.line, 2)


if __name__ == "__main__":
    unittest.main()
