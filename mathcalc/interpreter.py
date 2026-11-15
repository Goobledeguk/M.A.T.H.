"""Tree-walk interpreter (stage 4): evaluates the AST from the root down."""

import math
from fractions import Fraction

from . import ast_nodes as ast
from .errors import SemanticError
from .parser import parse

# Safety limits so a typo can't hang the interpreter or break printing.
MAX_FACTORIAL = 1000
MAX_DOUBLE_FACTORIAL = 2000
MAX_POWER_BITS = 100_000
MAX_RANGE = 1_000_000


# ---------------------------------------------------------------------------
# value helpers
# ---------------------------------------------------------------------------
def _type_name(v):
    if isinstance(v, bool):
        return "boolean"
    if isinstance(v, list):
        return "array"
    return "number"


def _num(v):
    if isinstance(v, bool) or not isinstance(v, (int, float, Fraction)):
        raise SemanticError(f"expected a number but got {_type_name(v)}")
    return v


def _int(v, what):
    """Return `v` as an int if it holds a whole number, else raise."""
    _num(v)
    if isinstance(v, int):
        return v
    if isinstance(v, float) and v.is_integer():
        return int(v)
    if isinstance(v, Fraction) and v.denominator == 1:
        return int(v)
    raise SemanticError(f"{what} requires a whole number, got {format_value(v)}")


def _fraction(v):
    _num(v)
    if isinstance(v, float):
        return Fraction(repr(v))     # 0.1 -> 1/10, not the binary approximation
    return Fraction(v)


def format_value(v):
    """Render a result the way the console shows it."""
    if isinstance(v, bool):
        return "true" if v else "false"
    if isinstance(v, Fraction):
        return str(v.numerator) if v.denominator == 1 else f"{v.numerator}/{v.denominator}"
    if isinstance(v, list):
        return "[" + ", ".join(format_value(x) for x in v) + "]"
    return repr(v)


# ---------------------------------------------------------------------------
# operator implementations (scalar level)
# ---------------------------------------------------------------------------
def _neg(a):
    return -_num(a)


def _sqrt(a):
    a = _num(a)
    if a < 0:
        raise SemanticError("square root of a negative number")
    return math.sqrt(a)


def _cbrt(a):
    a = _num(a)
    if hasattr(math, "cbrt"):
        root = math.cbrt(a)
    else:
        root = math.copysign(abs(a) ** (1 / 3), a)
    rounded = round(root)
    # snap perfect cubes (27 -> 3.0) so float error never leaks into the result
    return float(rounded) if rounded ** 3 == a else root


def _factorial(a):
    n = _int(a, "factorial")
    if n < 0:
        raise SemanticError("factorial of a negative number")
    if n > MAX_FACTORIAL:
        raise SemanticError(f"factorial argument too large (max {MAX_FACTORIAL})")
    return math.factorial(n)


def _double_factorial(a):
    n = _int(a, "double factorial")
    if n < 0:
        raise SemanticError("double factorial of a negative number")
    if n > MAX_DOUBLE_FACTORIAL:
        raise SemanticError(f"double factorial argument too large (max {MAX_DOUBLE_FACTORIAL})")
    result = 1
    for k in range(n, 0, -2):         # 7!! = 7 * 5 * 3 * 1
        result *= k
    return result


def _power(a, b):
    a, b = _num(a), _num(b)
    if isinstance(a, int) and isinstance(b, int):
        if b >= 0:
            if abs(a) > 1 and b * math.log2(abs(a)) > MAX_POWER_BITS:
                raise SemanticError("result of ** is too large")
            return a ** b
        if a == 0:
            raise SemanticError("zero cannot be raised to a negative power")
        return Fraction(1, a ** -b) if a > 0 or b % 2 == 0 else Fraction(-1, (-a) ** -b)
    if a == 0 and b < 0:
        raise SemanticError("zero cannot be raised to a negative power")
    result = a ** b
    if isinstance(result, complex):
        raise SemanticError("result is not a real number (negative base with fractional exponent)")
    return result


def _check_divisor(b, what):
    if b == 0:
        raise SemanticError(f"{what} by zero")


def _floor_div(a, b):
    a, b = _num(a), _num(b)
    _check_divisor(b, "division")
    return a // b


def _ceil_div(a, b):
    a, b = _num(a), _num(b)
    _check_divisor(b, "division")
    return -((-a) // b)


def _mod(a, b):
    a, b = _num(a), _num(b)
    _check_divisor(b, "modulo")
    return a % b


def _frac(a, b):
    fa, fb = _fraction(a), _fraction(b)
    _check_divisor(fb, "fraction")
    return fa / fb


def _hypot(a, b):
    return math.hypot(_num(a), _num(b))


def _compare(op):
    def fn(a, b):
        a, b = _num(a), _num(b)
        return {"==": a == b, "!=": a != b, "<": a < b,
                "<=": a <= b, ">": a > b, ">=": a >= b}[op]
    return fn


UNARY = {"-": _neg, ":/": _sqrt, "::/": _cbrt}
POSTFIX = {":/!": _factorial, "://!": _double_factorial}
BINARY = {
    "+": lambda a, b: _num(a) + _num(b),
    "-": lambda a, b: _num(a) - _num(b),
    "*": lambda a, b: _num(a) * _num(b),
    "**": _power,
    "//": _floor_div,
    "///": _ceil_div,
    "//:": _mod,
    "/:": _frac,
    ":/+": _hypot,
    **{op: _compare(op) for op in ("==", "!=", "<", "<=", ">", ">=")},
}


def _lift_unary(fn, v):
    """Apply a scalar operator element-wise when the operand is an array."""
    if isinstance(v, list):
        return [_lift_unary(fn, x) for x in v]
    return fn(v)


def _lift_binary(fn, a, b):
    """Element-wise application with scalar broadcasting."""
    if isinstance(a, list) and isinstance(b, list):
        if len(a) != len(b):
            raise SemanticError(f"array length mismatch ({len(a)} vs {len(b)})")
        return [_lift_binary(fn, x, y) for x, y in zip(a, b)]
    if isinstance(a, list):
        return [_lift_binary(fn, x, b) for x in a]
    if isinstance(b, list):
        return [_lift_binary(fn, a, y) for y in b]
    return fn(a, b)


def _range(a, b):
    lo, hi = _int(a, "range"), _int(b, "range")
    if abs(hi - lo) + 1 > MAX_RANGE:
        raise SemanticError(f"range too large (max {MAX_RANGE} elements)")
    return list(range(lo, hi + 1)) if lo <= hi else list(range(lo, hi - 1, -1))


# ---------------------------------------------------------------------------
# the interpreter
# ---------------------------------------------------------------------------
class Interpreter:
    """Evaluates M.A.T.H. source. Variables persist between calls."""

    def __init__(self, env=None):
        self.env = dict(env or {})

    def run(self, source):
        """Execute `source`; returns one value per statement."""
        tree = parse(source)
        return [self.visit(stmt) for stmt in tree.statements]

    def evaluate(self, source):
        """Execute `source`; returns the value of the last statement (None if empty)."""
        results = self.run(source)
        return results[-1] if results else None

    # -- visitor -----------------------------------------------------------
    def visit(self, node):
        return getattr(self, f"visit_{type(node).__name__}")(node)

    def visit_Number(self, node):
        return node.value

    def visit_Name(self, node):
        if node.name not in self.env:
            raise SemanticError(f"undefined variable '{node.name}'", node.line, node.column)
        return self.env[node.name]

    def visit_Assign(self, node):
        value = self.visit(node.value)
        self.env[node.name] = value
        return value

    def visit_ArrayLiteral(self, node):
        return [self.visit(e) for e in node.elements]

    def visit_UnaryOp(self, node):
        value = self.visit(node.operand)
        return self._apply(node, lambda: _lift_unary(UNARY[node.op], value))

    def visit_PostfixOp(self, node):
        value = self.visit(node.operand)
        return self._apply(node, lambda: _lift_unary(POSTFIX[node.op], value))

    def visit_BinaryOp(self, node):
        left = self.visit(node.left)
        right = self.visit(node.right)
        if node.op == "..":
            return self._apply(node, lambda: _range(left, right))
        return self._apply(node, lambda: _lift_binary(BINARY[node.op], left, right))

    @staticmethod
    def _apply(node, thunk):
        """Run an operator, attaching the node's position to any semantic error."""
        try:
            return thunk()
        except SemanticError as err:
            raise err.at(node)
        except OverflowError:
            raise SemanticError("number too large to compute", node.line, node.column)
        except ZeroDivisionError:
            raise SemanticError("division by zero", node.line, node.column)
