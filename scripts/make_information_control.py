"""Build the isolated Cycle 6 information-value investment challenger."""

import argparse
import ast
from hashlib import sha256
from pathlib import Path
from textwrap import indent

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
        "stress=0, routed=False, land_cost=0,\n"
        "    demand_path=None, rival_additions=(), land_day=None, quotes=None,\n"
        "    net_rival_wheat=False, work_cache=None\n",
    )
    projection = replace_once(
        projection,
        "    costs = {day: land_cost} if land_cost else {}",
        "    for item in rival_additions:\n"
        '        if "animal" in item:\n'
        "            animals[1 - own].append(dict(item))\n"
        "        else:\n"
        '            column = crop_column(item["crop"], item["planted_day"],\n'
        "                                 final, False, today=day)\n"
        "            if column is not None:\n"
        "                crops[1 - own].append(column)\n"
        "    costs = {day if land_day is None else land_day: land_cost} if land_cost else {}",
    )
    projection = replace_once(
        projection,
        "    for date in range(day, final + 1):\n        for c in inventory:",
        "    for date in range(day, final + 1):\n"
        "        if demand_path is not None:\n"
        "            demand = demand_path[date]\n"
        "        for c in inventory:",
    )
    projection = replace_once(
        projection,
        "            rival = flows[1 - own][date].get(c, 0)\n",
        "            rival = flows[1 - own][date].get(c, 0)\n"
        '            if net_rival_wheat and c == "WHEAT" and date < final:\n'
        "                # Feed uses rival wheat once; only its surplus is sold.\n"
        "                rival = max(0, rival - counts[1 - own])\n",
    )
    for before, after in (
        (
            "price_at(product, inventory[product], params)",
            "forecast_quote(product, inventory[product], params, quotes)",
        ),
        ("price_at(c, inventory[c], params)", "forecast_quote(c, inventory[c], params, quotes)"),
        (
            "batch_revenue(c, inventory[c] + rival / 2, units, params)",
            "forecast_sale(c, inventory[c] + rival / 2, units, params, quotes)",
        ),
    ):
        projection = replace_once(projection, before, after)
    # All shop/supply cases share this option's own work and wages. Cache only
    # within one continuation call, never between different purchases or states.
    work_start = projection.index("        producing = sum(")
    work_end = projection.index("        spending = costs.get(date, 0) + wage")
    work = projection[work_start:work_end]
    failure = 'return {"value": -1e9, "min_cash": -1e9, "daily": [], "route_feasible": False}'
    work = replace_once(
        work,
        "                " + failure,
        "                if work_cache is not None:\n"
        "                    work_cache[date] = None\n"
        "                " + failure,
    )
    projection = (
        projection[:work_start] + "        if work_cache is not None and date in work_cache:\n"
        "            if work_cache[date] is None:\n"
        "                " + failure + "\n"
        "            workers, wage = work_cache[date]\n"
        "        else:\n" + indent(work, "    ") + "            if work_cache is not None:\n"
        "                work_cache[date] = workers, wage\n" + projection[work_end:]
    )
    code = code[:start] + projection + code[end:]
    start, end = code.index("def expansion_investment("), code.index("def expansion_turn(")
    expansion = code[start:end]
    expansion = replace_once(
        expansion,
        "    baseline = production_projection(planned, cfg, params, routed=True)\n"
        '    report["baseline"] = baseline\n',
        "",
    )
    prefix = expansion[: expansion.index("    for land, orders, additions in options:")]
    expansion = (
        prefix
        + "    return information_investment(planned, cfg, params, options, market, report)\n\n\n"
    )
    helpers = (ROOT / "experiments/information_value.py").read_text()
    first = next(n for n in ast.parse(helpers).body if isinstance(n, ast.FunctionDef))
    helpers = "\n".join(helpers.splitlines()[first.lineno - 1 :])
    code = code[:start] + helpers + "\n\n\n" + expansion + code[end:]
    compile(code, "<information challenger>", "exec")
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
