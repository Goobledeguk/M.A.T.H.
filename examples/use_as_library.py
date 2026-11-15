import sys
from pathlib import Path

# Lets this example run straight from the project folder without installing.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from mathcalc import (Interpreter, LexicalError, MathSyntaxError, SemanticError,
                      evaluate, format_value, run)

print(evaluate(":/ 16"))                 # 4.0
print(evaluate("5 :/!"))                 # 120
print(format_value(evaluate("(1 /: 3) + (1 /: 6)")))   # 1/2
print(run("a = 5; b = 12; a :/+ b"))     # [5, 12, 13.0]

calc = Interpreter()                     # remembers variables between calls
calc.evaluate("x = 10")
print(calc.evaluate("x :/!"))            # 3628800

# Catching the three kinds of error
for bad in ("3 $ 4", "3 +", ":/ -4"):
    try:
        evaluate(bad)
    except (LexicalError, MathSyntaxError, SemanticError) as err:
        print(err)
