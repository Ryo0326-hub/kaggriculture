"""Build Cycle 13 from reproducible Cycle 12; packaging never runs a game."""

import argparse
import ast
from hashlib import sha256
from pathlib import Path
from tempfile import TemporaryDirectory

from scripts.make_carrot_control import edit_function
from scripts.make_carrot_input_control import build as build_inputs
from scripts.make_demand_control import ROOT, replace_once

CYCLE12_SHA256 = "555c312fc2c09c61c5f0081c4b4148446f5794eddaa1a71427a07b11d4057d34"


def build(output):
    with TemporaryDirectory() as temporary:
        source = Path(temporary) / "inputs.py"
        build_inputs(source)
        code = source.read_text()
    if sha256(code.encode()).hexdigest() != CYCLE12_SHA256:
        raise ValueError("Cycle 12 source changed")
    code = replace_once(code, "HERD_LIMIT = 10", "HERD_LIMIT = 12")
    for function in ("station_turn", "plan_turn"):
        code = edit_function(
            code,
            function,
            """    sites = sorted(
        [(x, y) for y in range(half) for x in range(half)],
        key=lambda p: (distance(p, access[0]), p),
    )[:herd_limit]""",
            "    sites = farm_sites(obs)[0][:herd_limit]",
        )
    code = replace_once(
        code,
        "CROPS = {",
        'CROPS = {\n    "TOMATO": {"seed": 50, '
        '"first": 8, "harvest": 8, "interval": 1, "events": 4, "units": 1},',
    )
    start = code.index(
        "    # Bound whole-day work, including individual crop trips, before sizing hires."
    )
    end = code.index("    extra_hires = 0", start)
    code = (
        code[:start]
        + (
            "    crop_work = sum(throughput_service(t, day, final) for _, t in plants)\n"
            '    livestock_workers = detail.get("routing", {}).get(\n'
            '        "target_hands", max(0, live - 1)) + 1\n'
            "    worker_target = throughput_staff(obs, cfg, livestock_workers, pending)\n"
        )
        + code[end:]
    )
    # Preserve the inherited no-fertilizer, terminal delivery and shared-ledger paths.
    for before, after in (
        ('tile["crop"] == "STRAWBERRY"', 'tile["crop"] in ("STRAWBERRY", "TOMATO")'),
        (
            'farm["tiles"][target[1]][target[0]]["crop"] == "STRAWBERRY"',
            'farm["tiles"][target[1]][target[0]]["crop"] in ("STRAWBERRY", "TOMATO")',
        ),
    ):
        code = edit_function(code, "mixed_turn", before, after)
    code = edit_function(
        code,
        "planning_snapshot",
        'tile["crop"] != "STRAWBERRY"',
        'tile["crop"] not in ("STRAWBERRY", "TOMATO")',
    )
    helpers = (ROOT / "experiments/throughput.py").read_text()
    first = next(n for n in ast.parse(helpers).body if isinstance(n, ast.FunctionDef))
    helpers = "\n".join(helpers.splitlines()[first.lineno - 1 :])
    bindings = """
inherited_crop_job = crop_job
inherited_crop_column = crop_column
inherited_timing_fertilizer = timing_fertilizer_value
inherited_production_orders = production_orders
crop_job = throughput_crop_job
crop_column = throughput_column
timing_fertilizer_value = throughput_fertilizer
route_cover = throughput_route_cover
production_orders = throughput_production
expansion_investment = throughput_investment
farm_sites = throughput_sites
"""
    code = replace_once(
        code,
        "def agent(obs, configuration=None):",
        helpers + "\n\n" + bindings + "\n\ndef agent(obs, configuration=None):",
    )
    compile(code, "<Cycle 13 throughput>", "exec")
    output = Path(output)
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("x") as file:
        file.write(code)
    return sha256(code.encode()).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    print(build(args.output))


if __name__ == "__main__":
    main()
