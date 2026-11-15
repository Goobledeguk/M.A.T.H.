"""Abstract Syntax Tree node types."""

from dataclasses import dataclass, field


@dataclass(frozen=True, kw_only=True)
class Node:
    line: int = field(default=0, compare=False)
    column: int = field(default=0, compare=False)


@dataclass(frozen=True)
class Number(Node):
    value: object


@dataclass(frozen=True)
class Name(Node):
    name: str


@dataclass(frozen=True)
class Assign(Node):
    name: str
    value: Node


@dataclass(frozen=True)
class UnaryOp(Node):
    """Prefix operator: '-', ':/' (square root), '::/' (cube root)."""
    op: str
    operand: Node


@dataclass(frozen=True)
class PostfixOp(Node):
    """Postfix operator: ':/!' (factorial), '://!' (double factorial)."""
    op: str
    operand: Node


@dataclass(frozen=True)
class BinaryOp(Node):
    op: str
    left: Node
    right: Node


@dataclass(frozen=True)
class ArrayLiteral(Node):
    elements: tuple


@dataclass(frozen=True)
class Program(Node):
    statements: tuple


def format_ast(node, indent=0):
    """Readable multi-line dump of a tree (used by `--ast`)."""
    pad = "  " * indent
    if isinstance(node, Program):
        head, kids = "Program", node.statements
    elif isinstance(node, Number):
        head, kids = f"Number({node.value!r})", ()
    elif isinstance(node, Name):
        head, kids = f"Name({node.name})", ()
    elif isinstance(node, Assign):
        head, kids = f"Assign({node.name})", (node.value,)
    elif isinstance(node, (UnaryOp, PostfixOp)):
        head, kids = f"{type(node).__name__}({node.op})", (node.operand,)
    elif isinstance(node, BinaryOp):
        head, kids = f"BinaryOp({node.op})", (node.left, node.right)
    elif isinstance(node, ArrayLiteral):
        head, kids = "Array", node.elements
    else:  # pragma: no cover
        head, kids = repr(node), ()
    return "\n".join([pad + head] + [format_ast(k, indent + 1) for k in kids])
