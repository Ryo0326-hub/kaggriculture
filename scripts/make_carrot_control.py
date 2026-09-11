"""Bundle a demand-gated carrot extension or its related supply-pressure opponent."""

# Exact source-replacement literals retain the frozen source's formatting.
# ruff: noqa: E501

import argparse
import ast
from hashlib import sha256
from pathlib import Path

from scripts.make_demand_control import BASELINE_SHA256, ROOT, replace_once
from scripts.make_opening_control import SCALED_SHA256, replace_function


def edit_function(code, name, before, after):
    node = next(
        n for n in ast.parse(code).body if isinstance(n, ast.FunctionDef) and n.name == name
    )
    function = "\n".join(code.splitlines()[node.lineno - 1 : node.end_lineno])
    return replace_function(code, name, replace_once(function, before, after))


def build(source, output, pressure=False):
    code = Path(source).read_text()
    if sha256(code.encode()).hexdigest() != (SCALED_SHA256 if pressure else BASELINE_SHA256):
        raise ValueError("Expected the frozen source hash")
    if pressure:
        code = replace_once(
            code,
            "    if day < 4:\n",
            '    if index % 3 == 2:\n        return "CARROT" if day + 3 <= final else None\n    if day < 4:\n',
        )
        code = edit_function(
            code,
            "crop_job",
            "    last = {",
            '    if crop == "CARROT":\n'
            '        ready = age >= 2 and tile["yield_units"] > 0\n'
            '        if ready and (age >= 3 or day == final) and (tile["watered_today"] or tile["yield_units"] >= 4):\n'
            '            return 1000, "HARVEST"\n'
            '        bonus = 2 <= age <= 3 and tile["yield_units"] < 4\n'
            '        if not tile["watered_today"] and (age == 0 or tile["consecutive_unwatered"] or bonus):\n'
            "            if day < final or ready and bonus:\n"
            '                if fertilizer and bonus and tile["fertilized_until_day"] < day and tile["yield_units"] + 4 - age < 4:\n'
            '                    return 920, "FERTILIZE"\n'
            '                return 930, "WATER"\n'
            "        if ready and (age >= 3 or day == final):\n"
            '            return 950, "HARVEST"\n'
            "        return None\n"
            "    last = {",
        )
        code = replace_once(
            code,
            '["BUY_SEED", "MELON", 6],\n            ["BUY_SEED", "WHEAT", 9]',
            '["BUY_SEED", "MELON", 4],\n            ["BUY_SEED", "WHEAT", 6],\n            ["BUY_SEED", "CARROT", 5]',
        )
        code = replace_once(code, "cash -= 2370", "cash -= 2280")
        code = replace_once(
            code,
            '{"WHEAT": 10, "STRAWBERRY": 100, "MELON": 80}',
            '{"WHEAT": 10, "STRAWBERRY": 100, "MELON": 80, "CARROT": 20}',
        )
    else:
        node = next(
            n
            for n in ast.parse(code).body
            if isinstance(n, ast.Assign)
            and any(isinstance(t, ast.Name) and t.id == "CROPS" for t in n.targets)
        )
        lines = code.splitlines(keepends=True)
        lines.insert(
            node.end_lineno - 1,
            '    "CARROT": {"seed": 20, "first": 2, "harvest": 3, "interval": 0, "events": 1, "units": 3},\n',
        )
        code = "".join(lines)
        helpers = (ROOT / "experiments/carrots.py").read_text()
        first = next(n for n in ast.parse(helpers).body if isinstance(n, ast.FunctionDef))
        helpers = "\n".join(helpers.splitlines()[first.lineno - 1 :])
        code = replace_once(code, "def crop_flows(", helpers + "\n\n\ndef crop_flows(")
        code = edit_function(
            code,
            "crop_flows",
            "    if crop not in CROPS:",
            '    if crop == "CARROT":\n        col = carrot_column(tile["planted_day"], final_day, False, tile, day)\n        return col["outputs"] if col else {}\n    if crop not in CROPS:',
        )
        code = edit_function(
            code,
            "crop_column",
            "    spec = CROPS[crop]",
            '    if crop == "CARROT":\n        return carrot_column(planted, final, fertilized, tile, today)\n    spec = CROPS[crop]',
        )
        code = edit_function(
            code,
            "crop_job",
            "    if not isinstance(tile, dict)",
            '    if isinstance(tile, dict) and tile.get("crop") == "CARROT":\n        return carrot_job(tile, day, final_day)\n    if not isinstance(tile, dict)',
        )
        code = edit_function(
            code,
            "fertilizer_value",
            '    day = obs["day"]',
            '    if tile.get("crop") == "CARROT":\n        return carrot_fertilizer_value(tile, obs, cfg, params)\n    day = obs["day"]',
        )
        code = edit_function(
            code,
            "farm_service",
            '    if "install" in tile:',
            '    if tile.get("crop") == "CARROT":\n        age = day - tile["planted_day"]\n        return 3 if age <= 0 else 2 if age == 3 or age == 2 and tile.get("fertilized", True) else 1\n    if "install" in tile:',
        )
        code = edit_function(
            code,
            "planning_snapshot",
            '                        6, tile["yield_units"]',
            '                        4 if tile["crop"] == "CARROT" else 6, tile["yield_units"]',
        )
        code = edit_function(
            code, "planning_snapshot", '("WHEAT", "MELON")', '("WHEAT", "MELON", "CARROT")'
        )
        for function, indent in (("production_orders", 8), ("expansion_investment", 12)):
            before = " " * indent + "for crop in CROPS:\n"
            after = (
                before
                + " " * (indent + 4)
                + 'if crop == "CARROT" and not carrot_demand_visible(obs):\n'
                + " " * (indent + 8)
                + "continue\n"
            )
            code = edit_function(code, function, before, after)
        before = """                additions = [
                    dict(crop=crop, planted_day=day + 1, site=p, fertilized=True)
                    for p in possible[:count]
                ]
                orders = ([["BUY_LAND"]] if extra else []) + [["BUY_SEED", crop, count]]
                options.append((land, orders, additions))"""
        after = '                for use_fert in (False, True) if crop == "CARROT" else (True,):\n'
        after += "\n".join(
            "    " + line
            for line in before.replace("fertilized=True", "fertilized=use_fert").splitlines()
        )
        code = edit_function(code, "expansion_investment", before, after)
    compile(code, "<Cycle 11 control>", "exec")
    output = Path(output)
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("x") as file:
        file.write(code)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--pressure", action="store_true")
    args = parser.parse_args()
    source = args.source or ROOT / (
        "opponents/scaled_mixed.py" if args.pressure else "baselines/cycle_3.py"
    )
    build(source, args.output, args.pressure)


if __name__ == "__main__":
    main()
