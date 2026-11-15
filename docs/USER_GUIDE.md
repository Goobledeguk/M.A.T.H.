# M.A.T.H. (`mathcalc`) — User Guide

**M.A.T.H.** stands for *Mathematical Analyzer and Token Handler*. It is a small domain-specific
language (DSL) for computational math, with its own operator symbols such as `:/` (square root)
and `///` (ceiling division). This project implements it in Python as a library named
**`mathcalc`**, plus a command-line program.

---

## 1. What you need

| Requirement | Details |
|---|---|
| Python | Version **3.10 or newer** (check with `python --version`) |
| Extra packages | **None.** The project uses only the Python standard library |
| Editor (optional) | VS Code or any text editor |

> On some computers the command is `python3` instead of `python` (common on macOS/Linux).
> On Windows, `py` also works. Use whichever one prints a version number.

---

## 2. Get the project ready

1. **Unzip** `mathcalc_project.zip`. You get a folder named `mathcalc_project`.
2. **Open a terminal inside that folder.**
   - VS Code: *File → Open Folder…*, choose `mathcalc_project`, then *Terminal → New Terminal*.
   - Windows: open the folder in File Explorer, click the address bar, type `cmd`, press Enter.
3. **Confirm you are in the right place.** Listing the folder should show `mathcalc`, `tests`,
   `examples`, `docs`, and `pyproject.toml`.

Folder layout:

```
mathcalc_project/
├── mathcalc/            <- the library (this is what you import)
│   ├── __init__.py      public API: evaluate, run, Interpreter, ...
│   ├── tokens.py        token types and the operator table
│   ├── lexer.py         stage 1: text -> tokens (DFA)
│   ├── parser.py        stage 2: tokens -> syntax tree (grammar)
│   ├── ast_nodes.py     the syntax tree node classes
│   ├── interpreter.py   stage 3: evaluates the tree
│   ├── errors.py        LexicalError, MathSyntaxError, SemanticError
│   ├── cli.py           command-line interface
│   └── __main__.py      makes `python -m mathcalc` work
├── tests/               unit tests (unittest)
├── examples/
│   ├── demo.math        a sample M.A.T.H. script
│   └── use_as_library.py  a sample Python program that imports mathcalc
├── docs/USER_GUIDE.md   this file
├── pyproject.toml       packaging info (for pip install)
└── README.md            short overview
```

### Optional: install it so `import mathcalc` works from anywhere

Without installing, `import mathcalc` only works when your terminal is **inside
`mathcalc_project`**. If you want to use it from any folder, install it once:

```
python -m venv .venv                 # create an isolated environment (recommended)
.venv\Scripts\activate               # Windows
source .venv/bin/activate            # macOS / Linux
pip install -e .                     # install mathcalc in "editable" mode
```

After this, `import mathcalc` works from any folder (while the environment is active), and a
`mathcalc` command is available in the terminal. "Editable" means changes you make to the
source files take effect immediately.

---

## 3. Three ways to run it

Run all commands from inside `mathcalc_project`.

### A) Interactive prompt (REPL)

```
python -m mathcalc
```

You will see `math>`. Type expressions and press Enter. Variables are remembered.

```
math> :/ 16
4.0
math> x = 5
5
math> x :/!
120
math> exit
```

Type `exit` or `quit` (or press Ctrl+D / Ctrl+Z then Enter) to leave. Errors are printed and the
prompt keeps going.

### B) Run a script file

Write your statements in a text file (any extension, `.math` is used in the example), one per
line or separated by `;`, then:

```
python -m mathcalc examples/demo.math
```

Each statement prints its result on its own line.

### C) One-off expression

```
python -m mathcalc -e "3 :/+ 4"
```

> **Windows tip:** wrap the expression in double quotes, as above. In PowerShell, characters such
> as `;` and `$` can be special; if something behaves oddly, use the interactive prompt instead.

### Debug options

See what the lexer and parser produce instead of running the code:

```
python -m mathcalc --tokens -e ":/ 9 + 1"
python -m mathcalc --ast    -e ":/ 9 + 1"
```

---

## 4. Using it as a library in your own Python code

Create a Python file (for example `my_program.py`) in the project folder, or anywhere if you ran
`pip install -e .`:

```python
from mathcalc import evaluate, run, Interpreter

print(evaluate(":/ 16"))             # 4.0
print(evaluate("5 :/!"))             # 120
print(run("a = 5; b = 12; a :/+ b")) # [5, 12, 13.0]  (one value per statement)

calc = Interpreter()                 # keeps variables between calls
calc.evaluate("x = 10")
print(calc.evaluate("x :/!"))        # 3628800
```

Run it with `python my_program.py`. A ready-made version is in `examples/use_as_library.py`.

### Public functions and classes

| Name | What it does |
|---|---|
| `evaluate(source, env=None)` | Runs the source and returns the **last** statement's value. `env` is an optional dict of starting variables |
| `run(source, env=None)` | Runs the source and returns a **list** with one value per statement |
| `Interpreter()` | An object that **remembers variables** across calls (`.evaluate()`, `.run()`, `.env`) |
| `tokenize(source)` | Lexer only: returns a list of `Token` objects |
| `parse(source)` | Lexer + parser: returns the syntax tree (`Program`) |
| `format_ast(tree)` | Turns a syntax tree into readable text |
| `format_value(value)` | Formats a result the way the console shows it (`Fraction(1, 2)` becomes `1/2`, `True` becomes `true`) |
| `MathError` | Base class of all errors below |
| `LexicalError` | Unknown character or symbol |
| `MathSyntaxError` | Symbols in the wrong order (grammar violation) |
| `SemanticError` | Well-formed but impossible to compute (e.g. `:/ -4`, `5 //: 0`) |

Return types: whole-number results are Python `int`, root/hypotenuse results are `float`,
`/:` results are `fractions.Fraction`, ranges and arrays are `list`, comparisons are `bool`.

### Handling errors

```python
from mathcalc import evaluate, MathError

try:
    evaluate(":/ -4")
except MathError as err:
    print(err)   # SemanticError at line 1, column 1: square root of a negative number
```

Every error message includes the **line and column** where the problem is.

---

## 5. Language reference

### 5.1 M.A.T.H. operators

| Operation | Symbol | Position | Example | Result |
|---|---|---|---|---|
| Square root | `:/` | before the number | `:/ 16` | `4.0` |
| Cube root | `::/` (or `://`) | before the number | `::/ 27` | `3.0` |
| Factorial | `:/!` | after the number | `5 :/!` | `120` |
| Double factorial | `://!` | after the number | `7 ://!` | `105` (7·5·3·1) |
| Ceiling division | `///` | between two numbers | `7 /// 2` | `4` |
| Floor division | `//` | between two numbers | `7 // 2` | `3` |
| Modulo | `//:` | between two numbers | `7 //: 3` | `1` |
| Exact fraction | `/:` | between two numbers | `1 /: 3` | `1/3` |
| Pythagorean hypotenuse | `:/+` | between two numbers | `3 :/+ 4` | `5.0` |
| Exponentiation | `**` | between two numbers | `2 ** 3` | `8` |

### 5.2 Other features

| Feature | Syntax | Example |
|---|---|---|
| Basic arithmetic | `+  -  *`, unary `-` | `(1 + 2) * 3` gives `9` |
| Parentheses | `( )` | `(1 + 2) * 3` |
| Variables | `name = expression` | `val = ::/ 27 + (1 /: 3)` |
| Several statements | newline or `;` | `a = 5; b = 12; a :/+ b` |
| Comments | `#` to end of line | `5 :/!  # factorial` |
| Arrays | `[a, b, c]` | `[1, 2, 3]` |
| Ranges (inclusive) | `a .. b` | `1 .. 5` gives `[1, 2, 3, 4, 5]` |
| Comparisons | `==  !=  <  <=  >  >=` | `2 < 3` gives `true` |

Operators work **element by element on arrays**, and a single number is repeated to match:

```
(1 .. 5) ** 2        ->  [1, 4, 9, 16, 25]
:/ [4, 9, 16]        ->  [2.0, 3.0, 4.0]
[1, 5, 3] >= 3       ->  [false, true, true]
```

### 5.3 Order of evaluation (lowest to highest priority)

1. `=` assignment
2. comparisons `== != < <= > >=`
3. range `..`
4. `+  -`
5. `*  //  ///  //:  /:  :/+`
6. prefix `-  :/  ::/`
7. `**` (right-to-left: `2 ** 3 ** 2` is `2 ** 9` = `512`)
8. postfix `:/!  ://!`

Use parentheses whenever you want to be explicit. Note that `-2 ** 2` is `-4`, and
`:/ 16 + 9` is `13.0` (the root applies to `16` only).

### 5.4 Safety limits

To prevent freezing or unprintable results: factorial input is capped at 1000, double factorial
at 2000, ranges at 1,000,000 elements, and absurdly large powers are rejected with a
`SemanticError`. These are constants at the top of `mathcalc/interpreter.py`.

### 5.5 Common errors

| You typed | Error |
|---|---|
| `3 $ 4` | `LexicalError`: unexpected character `'$'` |
| `3 +` | `SyntaxError`: unexpected end of input |
| `3 4` | `SyntaxError`: expected end of statement but found `'4'` |
| `:/ -4` | `SemanticError`: square root of a negative number |
| `5 //: 0` | `SemanticError`: modulo by zero |
| `x` (never assigned) | `SemanticError`: undefined variable `'x'` |
| `2.5 :/!` | `SemanticError`: factorial requires a whole number |

---

## 6. How it works internally

Every piece of source text goes through the same pipeline, matching the system flow in the
project proposal:

```
 source text ──► LEXER ──► tokens ──► PARSER ──► syntax tree ──► INTERPRETER ──► result
                  │                      │                           │
            LexicalError          MathSyntaxError              SemanticError
```

Example: `:/ 9 + 1`

**Step 1 — Lexer** (`lexer.py`). Reads characters left to right and groups them into tokens.
Operators are recognised by a **finite automaton** built from the operator table: it keeps walking
while the next character continues a valid operator and remembers the longest match, so `://!` is
one token rather than `:/`, `/`, `!`. Numbers and names use regular expressions. Anything else
raises `LexicalError`.

```
1:1   SQRT      ':/'
1:4   NUMBER    '9'
1:6   PLUS      '+'
1:8   NUMBER    '1'
1:9   EOF       ''
```
(`python -m mathcalc --tokens -e ":/ 9 + 1"`)

**Step 2 — Parser** (`parser.py`). Checks the tokens against the grammar and builds a tree that
records which operation happens first. The grammar is written as BNF at the top of the file.
Wrong token order raises `MathSyntaxError`.

```
Program
  BinaryOp(+)
    UnaryOp(:/)
      Number(9)
    Number(1)
```
(`python -m mathcalc --ast -e ":/ 9 + 1"`)

**Step 3 — Interpreter** (`interpreter.py`). Walks the tree from the bottom up: `Number(9)` is
`9`, `UnaryOp(:/)` turns that into `3.0`, `BinaryOp(+)` adds `1`, giving `4.0`. Impossible
operations (division by zero, negative square root, undefined variable) raise `SemanticError`.

**Step 4 — Output.** `evaluate()` returns the value to your code; the command line prints it
with `format_value()`.

### Where to change things

| I want to… | Edit |
|---|---|
| Add a new operator symbol | `tokens.py` (add to `OPERATOR_LEXEMES` and `TokenType`), then `parser.py` (place it in the grammar), then `interpreter.py` (add its function to `UNARY`, `POSTFIX` or `BINARY`) |
| Change precedence | the rule methods in `parser.py` |
| Change error wording or limits | `interpreter.py` / `errors.py` |

---

## 7. File-by-file reference

The files are grouped by role. For the library, the order follows how data moves through it:
text becomes tokens, tokens become a tree, and the tree becomes a result.

### 7.1 The library (`mathcalc/`)

**`tokens.py`** defines the vocabulary and has no logic. It contains:

- `TokenType`, an enum of every kind of token (`NUMBER`, `SQRT`, `FACT`, `PLUS`, ...).
- `OPERATOR_LEXEMES`, the table mapping each symbol to its type (`":/"` maps to `SQRT`,
  `"//:"` maps to `MOD`, ...). The lexer's automaton is built from this table, so adding an
  operator starts here.
- `CANONICAL`, which gives each type one official symbol, so the alias `://` is stored as `::/`
  in the tree.
- `Token`, a small record holding the type, the text, the numeric value (for numbers), and the
  line and column.

**`errors.py`** defines the error types. `MathError` is the base class and carries a message plus
line and column. Its `__str__` produces messages like
`SemanticError at line 1, column 7: modulo by zero`. The three subclasses are `LexicalError`,
`MathSyntaxError`, and `SemanticError`, one per stage.

**`lexer.py`** is stage 1, turning text into tokens. It has three parts:

- `build_dfa()` generates the automaton (states and transitions) from `OPERATOR_LEXEMES`.
- `Lexer._scan_operator()` walks that automaton and keeps the longest match.
- `Lexer.tokenize()` is the main loop. It skips spaces and `#` comments, turns newlines into
  statement separators (except inside `()` or `[]`), matches numbers and names with regular
  expressions, and raises `LexicalError` for anything unknown.

`tokenize(source)` at the bottom is the shortcut function.

**`ast_nodes.py`** defines the shapes of the syntax tree:

- `Number`, `Name`, `Assign`, `UnaryOp`, `PostfixOp`, `BinaryOp`, `ArrayLiteral`, and `Program`.
- Each node remembers its line and column so errors can point to the right place.
- `format_ast()` prints a tree as indented text, and the `--ast` option uses it.

**`parser.py`** is stage 2, turning tokens into the tree. The `Parser` class has one method per
grammar rule: `statement`, `comparison`, `range_expr`, `additive`, `term`, `unary`, `power`,
`postfix`, `primary`. The order in which they call each other sets operator precedence. Small
helpers (`_peek`, `_advance`, `_match`, `_expect`) look at and consume tokens, and `_expect`
raises `MathSyntaxError` when the next token is wrong. The grammar is written in BNF in the
file's docstring.

**`interpreter.py`** is stage 3, computing the result. It has three parts:

- Scalar operator functions such as `_sqrt`, `_factorial`, `_floor_div` and `_frac`. Each checks
  its own inputs and raises `SemanticError` if the math is impossible.
- Lookup tables `UNARY`, `POSTFIX`, and `BINARY` that map a symbol to its function.
- The `Interpreter` class, which has a `visit_` method per node type, keeps variables in
  `self.env`, and has `run()` and `evaluate()`.

This file also holds the array handling (applying an operator to each element), the safety
limits (`MAX_FACTORIAL` and others), and `format_value()` for printing results.

**`__init__.py`** is the front door. It re-exports the public names and defines the two
shortcuts, `evaluate()` and `run()`, so `from mathcalc import evaluate` works. Everything else is
internal detail.

**`cli.py`** is the command-line program. It uses `argparse` to read `-e`, `--tokens`, `--ast`,
and an optional filename. It runs the interactive prompt, a script file, or a single expression,
prints errors, and returns an exit code.

**`__main__.py`** is three lines that call `cli.main()`. Its only job is to make
`python -m mathcalc` work.

### 7.2 Tests (`tests/`)

These use Python's built-in `unittest`.

- **`test_lexer.py`** checks that every operator lexes as one token, longest-match behavior,
  number and range handling, line and column numbers, and lexical errors.
- **`test_parser.py`** checks precedence, that `**` is right-associative, assignment, arrays, and
  syntax errors with their positions.
- **`test_interpreter.py`** is the largest. It checks every example from the proposal tables,
  exact fractions, arrays and ranges, variables, every semantic error, error positions, and the
  command-line interface.

### 7.3 Examples (`examples/`)

- **`demo.math`** is a sample M.A.T.H. script, run with `python -m mathcalc examples/demo.math`.
- **`use_as_library.py`** is a sample Python program that imports `mathcalc`, calls `evaluate`,
  `run` and `Interpreter`, and catches the three error types.

### 7.4 Project files

- **`pyproject.toml`** is the packaging info (name, version, minimum Python 3.10, and the
  `mathcalc` command). `pip install -e .` reads it.
- **`README.md`** is the short overview with the operator table.
- **`docs/USER_GUIDE.md`** is this guide.

### 7.5 How the stages fit together

`lexer.py`, `parser.py`, and `interpreter.py` each take the previous stage's output and either
pass it on or raise their own error type. To change the language, edit `tokens.py`, `parser.py`,
and `interpreter.py`; the rest rarely change.

---

## 8. Testing

```
python -m unittest discover -s tests -v
```

Expected ending: `Ran 47 tests ... OK`. The tests cover:
- `test_lexer.py`: every operator symbol, longest-match behavior, positions, lexical errors
- `test_parser.py`: precedence, grammar structure, syntax errors
- `test_interpreter.py`: every example from the proposal tables, fractions, arrays, ranges,
  variables, all semantic errors, and the command-line interface

---

## 9. Troubleshooting

| Problem | Fix |
|---|---|
| `python` is not recognised | Try `python3` or `py`; install Python 3.10+ from python.org if none works |
| `No module named mathcalc` | Your terminal is not in `mathcalc_project`. `cd` into it, or run `pip install -e .` |
| `SyntaxError` on `kw_only` or other Python errors on startup | Python is older than 3.10; upgrade |
| `LexicalError` on something that looks fine | Check for stray characters, smart quotes, or a lone `:` / `!` / `.` (they are not operators on their own) |
| `5 :/!` fails with a syntax error | Keep `:/!` together with no space inside it (`5 :/!`, not `5 :/ !`) |
| Windows PowerShell mangles `-e "..."` | Use the interactive prompt (`python -m mathcalc`) |
| Console prints `true` / `false` but Python gives `True` / `False` | Expected: the console uses M.A.T.H. formatting; `evaluate()` returns real Python values |

---

## 10. Design decisions beyond the proposal

The proposal did not specify everything, so these choices were made and are easy to change:

- Cube root is accepted as both `::/` (operator table) and `://` (automaton diagram).
- `/:` is the exact-fraction operator; floats are converted by decimal value (`0.1 /: 1` is `1/10`).
- `//` is floor division (the unlabeled accepting state in the automaton).
- Arrays, ranges (`a .. b`) and relational operators use the syntax listed above; the proposal
  names these features but gives no symbols.
- The "operand valid and unique" check in the flowchart is not implemented, because rejecting
  repeated operands would make expressions like `2 + 2` invalid.
