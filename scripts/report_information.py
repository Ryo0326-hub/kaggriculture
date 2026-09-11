"""Archive the complete Cycle 6 screen; exclude superseded partial engineering runs."""

import argparse
import json
import runpy
from pathlib import Path

from baselines import cycle_3
from compare_results import compare
from evaluate import sha256
from scripts.make_demand_control import BASELINE_SHA256
from scripts.report_demand import development_gate
from scripts.report_spatial import run_report


def compact_option(option):
    if option is None:
        return None
    keys = (
        "orders",
        "cost_now",
        "buy_day",
        "marginal_value",
        "min_cash",
        "branch_values",
        "branch_feasible",
        "branch_min_cash",
        "affordable",
    )
    result = {k: option[k] for k in keys if k in option}
    result["plots"] = len(option["columns"])
    if "buy_day" in option:
        result["assumed_installation_day"] = option["buy_day"] + 1
    return result


def build(root, source):
    paths = {
        "candidate": root / "cycle-6-final-development",
        "reference": root / "cycle-6-reference-development",
    }
    runs = {name: run_report(path) for name, path in paths.items()}
    if runs["candidate"]["manifest"]["candidate"]["sha256"] != sha256(source):
        raise ValueError("Source does not match candidate experiment")
    if (
        sha256(cycle_3.__file__) != BASELINE_SHA256
        or runs["reference"]["manifest"]["candidate"]["sha256"] != BASELINE_SHA256
    ):
        raise ValueError("Reference is not frozen Cycle 3")
    policy = runpy.run_path(str(source))
    result = {
        "reporter_sha256": sha256(__file__),
        "runs": runs,
        "comparison": compare(paths["candidate"], paths["reference"]),
        "development_gate": development_gate(runs["candidate"], runs["reference"]),
        "excluded_partial_runs": [],
        "diagnostics": [],
    }
    for name, reason in (
        (
            "cycle-6-information-development",
            "Inherited rival wheat was counted as both feed and sale.",
        ),
        (
            "cycle-6-information-corrected-development",
            "Superseded by equivalent labor-cache optimization before selection.",
        ),
    ):
        path = root / name
        result["excluded_partial_runs"].append(
            {
                "reason": reason,
                "manifest": json.loads((path / "manifest.json").read_text()),
                "completed_records": [
                    json.loads(s) for s in (path / "matches.jsonl").read_text().splitlines()
                ],
                "included_in_comparison": False,
            }
        )
    for index in ("0001", "0017"):
        replays, audits = {}, {}
        for name, path in paths.items():
            replay_path = path / f"replay-{index}.json"
            replay = json.loads(replay_path.read_text())
            directory = (
                "cycle-6-reference-audit"
                if name == "reference"
                else (
                    "cycle-6-final-audit-first" if index == "0001" else "cycle-6-final-audit-strong"
                )
            )
            audit_path = root / directory / f"analysis-replay-{index}.json"
            audit = json.loads(audit_path.read_text())
            if audit["source_sha256"] != sha256(replay_path) or audit["state_mismatches"]:
                raise ValueError("Replay audit does not reconcile")
            if not all(p["cash_reconciliation_passed"] for p in audit["players"]):
                raise ValueError("Cash audit failed")
            audits[name] = {
                "replay_sha256": sha256(replay_path),
                "audit_sha256": sha256(audit_path),
                "shops": audit["shops"],
                "players": [
                    {k: v for k, v in p.items() if k not in ("transactions", "daily")}
                    for p in audit["players"]
                ],
            }
            replays[name] = replay
        a, b = replays["candidate"], replays["reference"]
        first = next(
            i for i in range(1, 720) if a["steps"][i][0]["action"] != b["steps"][i][0]["action"]
        )
        obs = a["steps"][first - 1][0]["observation"]
        if obs != b["steps"][first - 1][0]["observation"]:
            raise ValueError("First decision inputs are not identical")
        action, detail = policy["expansion_turn"](obs, a["configuration"])
        old_action, old_detail = cycle_3.expansion_turn(obs, b["configuration"])
        if action != a["steps"][first][0]["action"] or old_action != b["steps"][first][0]["action"]:
            raise ValueError("Diagnostic source does not match action")
        report = detail["expansion"]
        result["diagnostics"].append(
            {
                "replay_index": index,
                "seed": a["info"]["seed"],
                "seat": 0,
                "observation_index": first - 1,
                "internal_day": obs["day"],
                "hour": obs["hour"],
                "recorded_actions_match": True,
                "decision": report["decision"],
                "candidate_action": action,
                "reference_action": old_action,
                "reference_chosen": compact_option(old_detail["expansion"]["chosen"]),
                "immediate": compact_option(
                    policy["best_information_option"](report["alternatives"])
                ),
                "wait_value": report["wait_value"],
                "immediate_value": report["immediate_value"],
                "next_day": report["information"]["next_day"],
                "shop_branches": [b["shop"] for b in report["information"]["branches"]],
                "supply_cases": report["information"]["supply_cases"],
                "wait_choices": [compact_option(o) for o in report["wait_choices"]],
                "first_town_difference_index": next(
                    (
                        i
                        for i, (left, right) in enumerate(zip(a["steps"], b["steps"]))
                        if left[0]["observation"]["town"] != right[0]["observation"]["town"]
                    ),
                    None,
                ),
                "audits": audits,
            }
        )
    result["interpretation"] = (
        "Consumed development seeds, not a holdout or leaderboard estimate. Partial engineering "
        "runs are excluded; repeat results add no independent evidence. Initial-seed matching "
        "does not fix future shops. Recorded-action audits are descriptive, "
        "not counterfactual play."
    )
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path("artifacts"))
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    result = build(args.root, args.source)
    with args.output.open("x") as file:
        json.dump(result, file, separators=(",", ":"))
        file.write("\n")
    print(json.dumps(result["development_gate"], indent=2))


if __name__ == "__main__":
    main()
