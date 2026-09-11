"""Bundle a cash-admission-only challenger; keep all original profit coefficients."""

import argparse
import ast
from hashlib import sha256
from pathlib import Path

from scripts.make_demand_control import BASELINE_SHA256, ROOT, replace_once


def build(source, output):
    code = Path(source).read_text()
    if sha256(code.encode()).hexdigest() != BASELINE_SHA256:
        raise ValueError("Expected the frozen Cycle 3 source")
    start = code.index("def expansion_investment(")
    before, expansion = code[:start], code[start:]
    expansion = replace_once(
        expansion,
        '    report["baseline"] = baseline\n',
        '    report["baseline"] = baseline\n'
        '    report["baseline_cash_bound"] = current_day_cash_bound(\n'
        "        planned, cfg, params, (), baseline\n    )\n",
    )
    expansion = replace_once(
        expansion,
        "        option = {\n",
        "        liquidity = current_day_cash_bound(planned, cfg, params, additions, projection)\n"
        "        option = {\n",
    )
    expansion = replace_once(
        expansion,
        '            "min_cash": projection["min_cash"],\n',
        '            "min_cash": liquidity["min_cash"],\n'
        '            "current_day_cash": liquidity,\n',
    )
    expansion = replace_once(
        expansion,
        '            and projection["min_cash"] >= 150,\n',
        '            and liquidity["min_cash"] >= 150,\n',
    )
    helpers = (ROOT / "experiments/current_day_cash.py").read_text()
    first = next(n for n in ast.parse(helpers).body if isinstance(n, ast.FunctionDef))
    helpers = "\n".join(helpers.splitlines()[first.lineno - 1 :])
    code = before + helpers + "\n\n\n" + expansion
    compile(code, "<current-day cash challenger>", "exec")
    output = Path(output)
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("x") as file:
        file.write(code)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, default=ROOT / "baselines/cycle_3.py")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    build(args.source, args.output)


if __name__ == "__main__":
    main()
