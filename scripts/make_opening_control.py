"""Generate the frozen opening challenger or its related wheat-supply stress control."""

import argparse
import ast
from hashlib import sha256
from pathlib import Path

from scripts.make_demand_control import BASELINE_SHA256, ROOT, replace_once

SCALED_SHA256 = "af20c4596a72ce4dc81977220a39329146db7ef27d8d7d48cbd45a7799616590"


def replace_function(code, name, replacement):
    node = next(
        n for n in ast.parse(code).body if isinstance(n, ast.FunctionDef) and n.name == name
    )
    lines = code.splitlines(keepends=True)
    return (
        "".join(lines[: node.lineno - 1])
        + replacement.rstrip()
        + "\n"
        + "".join(lines[node.end_lineno :])
    )


def build(source, output, wheat_opponent=False):
    code = Path(source).read_text()
    expected = SCALED_SHA256 if wheat_opponent else BASELINE_SHA256
    if sha256(code.encode()).hexdigest() != expected:
        raise ValueError("Expected the frozen source hash")
    if wheat_opponent:
        code = replace_function(
            code,
            "crop_choice",
            "def crop_choice(day, index, final):\n"
            '    return "WHEAT" if day + 4 <= final else None\n',
        )
        code = replace_once(
            code,
            '["BUY_SEED", "MELON", 6],\n            ["BUY_SEED", "WHEAT", 9]',
            '["BUY_SEED", "WHEAT", 15]',
        )
        code = replace_once(code, "cash -= 2370", "cash -= 1950")
    else:
        helpers = (ROOT / "experiments/wheat_opening.py").read_text()
        first = next(n for n in ast.parse(helpers).body if isinstance(n, ast.FunctionDef))
        replacement = "\n".join(helpers.splitlines()[first.lineno - 1 :])
        code = replace_function(code, "opening_portfolios", replacement)
        code = replace_once(
            code,
            '            if chosen["melons"]:\n',
            '            if chosen["wheat"]:\n'
            '                market.append(["BUY_SEED", "WHEAT", chosen["wheat"]])\n'
            '            if chosen["melons"]:\n',
        )
    compile(code, "<Cycle 10 control>", "exec")
    output = Path(output)
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("x") as file:
        file.write(code)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--wheat-opponent", action="store_true")
    args = parser.parse_args()
    source = args.source or ROOT / (
        "opponents/scaled_mixed.py" if args.wheat_opponent else "baselines/cycle_3.py"
    )
    build(source, args.output, args.wheat_opponent)


if __name__ == "__main__":
    main()
