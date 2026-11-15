# M.A.T.H. — Mathematical Analyzer and Token Handler

A domain-specific language for computational math, implemented in Python.
Pipeline: **source → Lexer (DFA) → Parser (CFG, recursive descent) → AST → tree-walk Interpreter**.
No dependencies; Python 3.10+.

> **Step-by-step setup, full language reference, and troubleshooting: see [`docs/USER_GUIDE.md`](docs/USER_GUIDE.md).**

## Use it as a library

```python
from mathcalc import evaluate, run, Interpreter

evaluate(":/ 16")                      # 4.0
evaluate("3 :/+ 4")                    # 5.0
evaluate("(1 /: 3) + (1 /: 6)")        # Fraction(1, 2)
run("a = 5; b = 12; a :/+ b")          # [5, 12, 13.0]

calc = Interpreter()                   # keeps variables between calls
calc.evaluate("x = 10")
calc.evaluate("x :/!")                 # 3628800
```

Each stage is also importable on its own: `tokenize(src)`, `parse(src)`, `format_ast(tree)`.
Errors: `LexicalError`, `MathSyntaxError`, `SemanticError` (all subclass `MathError`).

## Use it from the terminal

```
python -m mathcalc                     # interactive prompt
python -m mathcalc examples/demo.math  # run a script
python -m mathcalc -e "7 //: 3"        # one expression
python -m mathcalc --tokens -e ":/ 9"  # show the token stream
python -m mathcalc --ast -e ":/ 9 + 1" # show the syntax tree
```

Optional: `pip install -e .` then call `mathcalc` or `import mathcalc` from anywhere.

## Tests

```
python -m unittest discover -s tests -v
```

## Operators

| Operator | Symbol | Kind | Example | Result |
|---|---|---|---|---|
| Square root | `:/` | prefix | `:/ 16` | `4.0` |
| Cube root | `::/` (also `://`) | prefix | `::/ 27` | `3.0` |
| Factorial | `:/!` | postfix | `5 :/!` | `120` |
| Double factorial | `://!` | postfix | `7 ://!` | `105` |
| Ceiling division | `///` | infix | `7 /// 2` | `4` |
| Floor division | `//` | infix | `7 // 2` | `3` |
| Modulo | `//:` | infix | `7 //: 3` | `1` |
| Fraction (exact) | `/:` | infix | `1 /: 3` | `1/3` |
| Hypotenuse | `:/+` | infix | `3 :/+ 4` | `5.0` |
| Exponentiation | `**` | infix, right-assoc | `2 ** 3` | `8` |

Also: `+ - *`, parentheses, variables (`x = 3`), arrays (`[1, 2, 3]`), ranges (`1 .. 5`),
and relational operators (`== != < <= > >=`). Arithmetic and comparisons work element-wise on
arrays, with scalars broadcast (`[1, 5, 3] >= 3` → `[false, true, true]`).

Precedence, lowest to highest: `=`, comparisons, `..`, `+ -`, `* // /// //: /: :/+`,
prefix `- :/ ::/`, `**`, postfix `:/! ://!`. The full BNF is in `mathcalc/parser.py`.
