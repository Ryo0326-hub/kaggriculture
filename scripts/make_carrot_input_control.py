"""Build Cycle 12 from the exact frozen Cycle 11 ablation."""

import argparse
import ast
from hashlib import sha256
from pathlib import Path
from tempfile import TemporaryDirectory

from scripts.make_carrot_control import build as build_carrots
from scripts.make_carrot_control import edit_function
from scripts.make_demand_control import ROOT, replace_once

CARROT_SHA256 = "16bb5ba43889df22d931383f84eb288b12380a66091be086ea3aa4dacf768415"


def build(output):
    with TemporaryDirectory() as temp:
        source = Path(temp) / "carrots.py"
        build_carrots(ROOT / "baselines/cycle_3.py", source)
        code = source.read_text()
    if sha256(code.encode()).hexdigest() != CARROT_SHA256:
        raise ValueError("Cycle 11 ablation changed")
    helpers = (ROOT / "experiments/carrot_inputs.py").read_text()
    first = next(n for n in ast.parse(helpers).body if isinstance(n, ast.FunctionDef))
    code = replace_once(
        code,
        "def carrot_demand_visible(",
        "\n".join(helpers.splitlines()[first.lineno - 1 :]) + "\n\n\ndef carrot_demand_visible(",
    )
    code = edit_function(
        code,
        "crop_column",
        "return carrot_column(planted, final, fertilized, tile, today)",
        "return carrot_column(planted, final, False, tile, today)",
    )
    code = edit_function(
        code,
        "expansion_investment",
        'for use_fert in (False, True) if crop == "CARROT" else (True,):',
        'for use_fert in (False,) if crop == "CARROT" else (True,):',
    )
    code = edit_function(
        code, "farm_service", 'tile.get("fertilized", True)', 'tile.get("fertilized", False)'
    )
    # Exclude carrots from the inherited scalar target and speculative buying;
    # their explicit bundles below own both the stock reservation and purchase.
    for function in ("production_orders", "expansion_investment"):
        code = edit_function(
            code,
            function,
            'if isinstance(t, dict) and t.get("crop") in CROPS',
            'if isinstance(t, dict) and t.get("crop") in CROPS and t["crop"] != "CARROT"',
        )
    code = edit_function(
        code,
        "mixed_turn",
        "    harvest_values = {",
        "    fertile = {p: v for p, v in fertile.items()\n"
        '               if farm["tiles"][p[1]][p[0]]["crop"] != "CARROT"}\n'
        "    harvest_values = {",
    )
    code = edit_function(
        code,
        "mixed_turn",
        "    reserved = set()\n    crop_actions = []",
        '    input_stock = dict(private["shed"])\n'
        "    for i, op in enumerate(commands):\n"
        '        if i not in available and op[:2] == ["PICKUP", "FERTILIZER"]:\n'
        '            input_stock["FERTILIZER"] -= op[2]\n'
        "    carrot_inputs = carrot_input_plan(\n"
        "        obs, cfg, params, available, newborn_workers, urgent_assignments,\n"
        "        input_stock, enabled=use_fertilizer and bool(expansion)\n"
        "    )\n"
        '    reserved = {b["target"] for b in carrot_inputs["bundles"].values()}\n'
        "    urgent_assignments = {i: job for i, job in urgent_assignments.items()\n"
        '                          if i not in carrot_inputs["bundles"]\n'
        "                          and job[0] not in reserved}\n"
        "    crop_actions = []",
    )
    code = edit_function(
        code,
        "mixed_turn",
        "        if i in urgent_assignments:\n",
        '        if i in carrot_inputs["bundles"]:\n'
        '            bundle = carrot_inputs["bundles"][i]\n'
        '            commands[i] = bundle["action"]\n'
        '            crop_actions.append({"worker": i, "target": bundle["target"],\n'
        '                                 "job": "CARROT_INPUT", "action": commands[i]})\n'
        "            continue\n"
        "        if i in urgent_assignments:\n",
    )
    code = edit_function(
        code,
        "mixed_turn",
        '    stock = dict(private["shed"])\n    harvest_room = (',
        '    stock = dict(private["shed"])\n'
        '    stock["FERTILIZER"] = stock.get("FERTILIZER", 0) - sum(\n'
        '        b["source"] == "shed" for b in carrot_inputs["bundles"].values()\n'
        "    )\n"
        "    harvest_room = (",
    )
    code = edit_function(
        code,
        "mixed_turn",
        "    market = []\n",
        '    fert_keep += carrot_inputs["keep"]\n    market = []\n',
    )
    code = edit_function(
        code,
        "mixed_turn",
        '        "active_crops": len(plants),',
        '        "carrot_inputs": carrot_inputs,\n        "active_crops": len(plants),',
    )
    code = edit_function(
        code,
        "mixed_turn",
        "    if expansion and day >= 2:\n",
        "    market = fund_carrot_inputs(obs, cfg, params, commands, market, carrot_inputs)\n"
        "    if expansion and day >= 2:\n",
    )
    compile(code, "<Cycle 12>", "exec")
    output = Path(output)
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("x") as file:
        file.write(code)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    build(args.output)


if __name__ == "__main__":
    main()
