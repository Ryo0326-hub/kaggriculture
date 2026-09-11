"""Archive conditional continuation evidence and source-matched forecast comparisons."""

import argparse
import json
import runpy
from pathlib import Path
from tempfile import TemporaryDirectory

from baselines import cycle_3
from evaluate import sha256
from scripts.benchmark_continuation import verify_sources
from scripts.make_wheat_conservation_control import build as build_conservation


def forecasts(case, corrected):
    replay = json.loads(Path(case["replay"]).read_text())
    i, seat = case["observation"], case["seat"]
    obs = dict(replay["steps"][i][seat]["observation"])
    obs["step"] = replay["steps"][i][0]["observation"]["step"]
    result = {}
    for name, fn in (
        ("original", cycle_3.expansion_turn),
        ("wheat_corrected", corrected["expansion_turn"]),
    ):
        action, detail = fn(obs, replay["configuration"])
        if name == "original" and action != replay["steps"][i + 1][seat]["action"]:
            raise ValueError("Forecast does not reproduce the incumbent's branch decision")
        expansion = detail["expansion"]
        chosen = expansion["chosen"]
        result[name] = {
            "chosen_orders": chosen["orders"] if chosen else [],
            "chosen_marginal_value": chosen["marginal_value"] if chosen else 0,
            "one_crop_options": [
                {
                    k: o[k]
                    for k in (
                        "orders",
                        "cost_now",
                        "marginal_value",
                        "min_cash",
                        "route_feasible",
                        "affordable",
                    )
                }
                for o in expansion["alternatives"]
                if o["orders"] in ([["BUY_SEED", "WHEAT", 1]], [["BUY_SEED", "MELON", 1]])
            ],
        }
    return result


def liquidity_check(case, row, replay_path, audit_path):
    replay = json.loads(replay_path.read_text())
    seat, start = case["seat"], case["observation"]
    steps = replay["steps"]
    minimum = min(
        range(start, len(steps)),
        key=lambda i: steps[i][seat]["observation"]["farms"][seat]["money"],
    )
    result = {
        "minimum_cash": steps[minimum][seat]["observation"]["farms"][seat]["money"],
        "minimum_observation": minimum,
    }
    previous = [t for t in row["capital_trace"] if t["submitted"] and t["observation"] < minimum]
    if previous:
        last = previous[-1]
        obs = dict(steps[last["observation"]][seat]["observation"])
        obs["step"] = last["observation"]
        action, detail = cycle_3.expansion_turn(obs, replay["configuration"])
        chosen = detail["expansion"]["chosen"]
        # Only call it a matched forecast when the unmodified incumbent chose it.
        if not last["overridden"] and action == steps[obs["step"] + 1][seat]["action"]:
            result["last_purchase_forecast"] = {
                "observation": obs["step"],
                "orders": chosen["orders"],
                "min_cash": chosen["min_cash"],
                "current_day": chosen["projection"]["daily"][0],
            }
            audit = json.loads(audit_path.read_text())
            result["transactions_through_cash_minimum"] = [
                t
                for t in audit["players"][seat]["transactions"]
                if obs["step"] <= t["step"] < minimum
            ]
    return result


def build(root):
    report = json.loads((root / "report.json").read_text())
    manifest = report["manifest"]
    spec = manifest["specification"]
    verify_sources(spec)
    report["reporter_sha256"] = sha256(__file__)
    if len(report["results"]) != len(spec["cases"]):
        raise ValueError("Missing cases")
    with TemporaryDirectory() as temp:
        source = Path(temp) / "main.py"
        build_conservation(cycle_3.__file__, source)
        report["corrected_forecast_source_sha256"] = sha256(source)
        corrected = runpy.run_path(str(source))
        for item, case in zip(report["results"], spec["cases"]):
            if item["case"] != case or len(item["continuations"]) != len(case["variants"]):
                raise ValueError("Case grid differs from the frozen specification")
            item["forecasts"] = forecasts(case, corrected)
            starts = set()
            for row, variant in zip(item["continuations"], case["variants"]):
                if row["variant"] != variant:
                    raise ValueError("Variant ordering mismatch")
                directory = root / case["name"]
                path = directory / f"{variant['name']}.json"
                if (
                    sha256(path) != row["replay_sha256"]
                    or sha256(directory / f"analysis-{variant['name']}.json") != row["audit_sha256"]
                ):
                    raise ValueError("Continuation evidence changed")
                if row["statuses"] != ["DONE", "DONE"] or not all(
                    p["cash_reconciled"] for p in row["players"]
                ):
                    raise ValueError("Failed continuation or cash reconciliation")
                row["liquidity_check"] = liquidity_check(
                    case, row, path, directory / f"analysis-{variant['name']}.json"
                )
                starts.add(row["start_state_sha256"])
            if len(starts) != 1:
                raise ValueError("Unmatched starting states")
    report["interpretation"] = (
        "Two selected states on consumed seed 17; six conditional continuations, not six "
        "independent games. Both unchanged controls reproduce every future action and game "
        "state, excluding runtime overage bookkeeping. Both sides continue reactively and "
        "may reinvest. Branch-specific occupancy can change future shops. Recorded future "
        "actions are used only to check controls and identify divergences. These results "
        "diagnose forecasts, not out-of-sample performance or optimal information value. "
        "No live-policy promotion, fresh seed use or new upload."
    )
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    report = build(args.root)
    with args.output.open("x") as file:
        json.dump(report, file, separators=(",", ":"))
        file.write("\n")
    for item in report["results"]:
        print(item["case"]["name"], item["forecasts"])
        for row in item["continuations"]:
            print(
                row["variant"]["name"],
                row["outcome"],
                row["margin"],
                row.get("difference_from_control", {}),
            )


if __name__ == "__main__":
    main()
