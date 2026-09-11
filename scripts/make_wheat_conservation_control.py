"""Correct double-counted rival wheat only in Cycle 3's expansion forecast."""

import argparse
from hashlib import sha256
from pathlib import Path

from scripts.make_demand_control import BASELINE_SHA256, ROOT, replace_once


def build(source, output):
    code = Path(source).read_text()
    if sha256(code.encode()).hexdigest() != BASELINE_SHA256:
        raise ValueError("Expected the frozen Cycle 3 source")
    start, end = code.index("def production_projection("), code.index("def opening_portfolios(")
    projection = code[start:end]
    projection = replace_once(
        projection,
        "stress=0, routed=False, land_cost=0\n",
        "stress=0, routed=False, land_cost=0,\n    net_rival_wheat=False\n",
    )
    projection = replace_once(
        projection,
        "            rival = flows[1 - own][date].get(c, 0)\n",
        "            rival = flows[1 - own][date].get(c, 0)\n"
        '            if net_rival_wheat and c == "WHEAT" and date < final:\n'
        "                # Only the surplus after feed enters the market.\n"
        "                rival = max(0, rival - counts[1 - own])\n",
    )
    code = code[:start] + projection + code[end:]
    start = code.index("def expansion_investment(")
    expansion = code[start:]
    expansion = replace_once(
        expansion,
        "production_projection(planned, cfg, params, routed=True)",
        "production_projection(planned, cfg, params, routed=True, net_rival_wheat=True)",
    )
    expansion = replace_once(
        expansion,
        "planned, cfg, params, additions, routed=True, land_cost=land\n",
        "planned, cfg, params, additions, routed=True, land_cost=land, net_rival_wheat=True\n",
    )
    code = code[:start] + expansion
    compile(code, "<wheat conservation challenger>", "exec")
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
