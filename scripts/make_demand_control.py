"""Build the standalone Cycle 5 future-demand investment challenger."""

import argparse
import ast
from hashlib import sha256
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BASELINE_SHA256 = "47c281bfb4118a9755f1759930b162de007efdfef3b23144457eccbaac42da0c"


def replace_once(code, before, after):
    if code.count(before) != 1:
        raise ValueError("Expected exactly one frozen forecast expression")
    return code.replace(before, after)


def build(source, output):
    code = Path(source).read_text()
    if sha256(code.encode()).hexdigest() != BASELINE_SHA256:
        raise ValueError("Expected the frozen Cycle 3 source")
    code = replace_once(
        code,
        "stress=0, routed=False, land_cost=0\n",
        "stress=0, routed=False, land_cost=0,\n    demand_path=None\n",
    )
    code = replace_once(
        code,
        "    for date in range(day, final + 1):\n        for c in inventory:",
        "    for date in range(day, final + 1):\n"
        "        if demand_path is not None:\n"
        "            demand = demand_path[date]\n"
        "        for c in inventory:",
    )
    start = code.index("def expansion_investment(")
    before, expansion = code[:start], code[start:]
    expansion = replace_once(
        expansion,
        "    baseline = production_projection(planned, cfg, params, routed=True)",
        "    paths = future_demand_paths(planned, cfg)\n"
        '    report["demand_scenarios"] = paths\n'
        "    baseline = investment_projection(planned, cfg, params, paths)",
    )
    expansion = replace_once(
        expansion,
        "        projection = production_projection(\n"
        "            planned, cfg, params, additions, routed=True, land_cost=land\n"
        "        )",
        "        projection = investment_projection(\n"
        "            planned, cfg, params, paths, additions, land_cost=land\n"
        "        )\n"
        "        marginal_values = [\n"
        '            p["value"] - b["value"]\n'
        '            for p, b in zip(projection["scenarios"], baseline["scenarios"])\n'
        "        ]",
    )
    expansion = replace_once(
        expansion,
        '            "marginal_value": projection["value"] - baseline["value"],',
        '            "marginal_value": sum(marginal_values) / len(marginal_values),\n'
        '            "scenario_marginal_values": marginal_values,',
    )
    helpers = (ROOT / "experiments/future_demand.py").read_text()
    # Drop the module docstring; retain only the helper definitions.
    first = next(n for n in ast.parse(helpers).body if isinstance(n, ast.FunctionDef))
    helpers = "\n".join(helpers.splitlines()[first.lineno - 1 :])
    code = before + helpers + "\n\n\n" + expansion
    compile(code, "<demand challenger>", "exec")
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
