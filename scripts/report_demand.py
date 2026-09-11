"""Archive the bounded Cycle 5 screen and source-matched diagnostic decisions."""

import argparse
import json
import runpy
from pathlib import Path

from baselines import cycle_3
from compare_results import compare
from evaluate import sha256
from scripts.make_demand_control import BASELINE_SHA256
from scripts.report_spatial import run_report


def development_gate(candidate, reference):
    reasons = []
    if candidate["summary"]["match_score"] <= reference["summary"]["match_score"]:
        reasons.append("Development match score did not improve")
    if candidate["summary"]["errors"]:
        reasons.append("Candidate execution error")
    if candidate["terminal_units"] or any(candidate["operational_totals"].values()):
        reasons.append("Unresolved operational diagnostic")
    if candidate["summary"]["decision_max_seconds"] >= 1:
        reasons.append("Observed decision time reaches the configured one-second budget")
    return {"advance_to_fresh_evaluation": not reasons, "reasons": reasons}


def compact_decision(policy, obs, cfg, recorded):
    action, detail = policy(obs, cfg)
    if action != recorded:
        raise ValueError("Diagnostic source does not reproduce recorded action")
    report = detail["expansion"]
    keys = (
        "orders",
        "marginal_value",
        "scenario_marginal_values",
        "min_cash",
        "cost_now",
        "route_feasible",
        "affordable",
    )
    return {
        "recorded_action_matches": True,
        "action": action,
        "chosen": report["chosen"]
        and {k: report["chosen"][k] for k in keys if k in report["chosen"]},
        "alternatives": [{k: o[k] for k in keys if k in o} for o in report["alternatives"]],
        "shop_scenarios": [p["unlocks"] for p in report.get("demand_scenarios", [])],
    }


def build(root, source):
    paths = {name: root / f"cycle-5-{name}-development" for name in ("demand", "reference")}
    runs = {name: run_report(path) for name, path in paths.items()}
    if runs["demand"]["manifest"]["candidate"]["sha256"] != sha256(source):
        raise ValueError("Challenger source differs from development run")
    if sha256(cycle_3.__file__) != BASELINE_SHA256:
        raise ValueError("Incumbent changed")
    if runs["reference"]["manifest"]["candidate"]["sha256"] != BASELINE_SHA256:
        raise ValueError("Reference run differs from incumbent")
    candidate = runpy.run_path(str(source))["expansion_turn"]
    result = {
        "reporter_sha256": sha256(__file__),
        "comparison": compare(paths["demand"], paths["reference"]),
        "runs": runs,
        "development_gate": development_gate(runs["demand"], runs["reference"]),
        "diagnostics": [],
    }
    for index, seat in (("0004", 1), ("0011", 0)):
        replays, audits = {}, {}
        for name, path in paths.items():
            replay_path = path / f"replay-{index}.json"
            replays[name] = json.loads(replay_path.read_text())
            audit_path = root / f"cycle-5-{name}-audit" / f"analysis-replay-{index}.json"
            audit = json.loads(audit_path.read_text())
            if audit["source_sha256"] != sha256(replay_path) or audit["state_mismatches"]:
                raise ValueError("Audit does not reconcile replay")
            if not all(p["cash_reconciliation_passed"] for p in audit["players"]):
                raise ValueError("Cash audit failed")
            audits[name] = {
                "audit_sha256": sha256(audit_path),
                "replay_sha256": sha256(replay_path),
                "shops": audit["shops"],
                "players": [
                    {
                        k: v
                        for k, v in p.items()
                        if k not in ("transactions", "daily", "installations")
                    }
                    for p in audit["players"]
                ],
            }
        a, b = replays["demand"], replays["reference"]
        first = next(
            i
            for i in range(1, len(a["steps"]))
            if a["steps"][i][seat]["action"] != b["steps"][i][seat]["action"]
        )
        prior = first - 1
        obs = dict(a["steps"][prior][seat]["observation"])
        if obs != b["steps"][prior][seat]["observation"]:
            raise ValueError("First diagnostic observations differ")
        obs["step"] = a["steps"][prior][0]["observation"]["step"]
        town_difference = next(
            (
                i
                for i, (left, right) in enumerate(zip(a["steps"], b["steps"]))
                if left[0]["observation"]["town"] != right[0]["observation"]["town"]
            ),
            None,
        )
        result["diagnostics"].append(
            {
                "replay_index": index,
                "seat": seat,
                "seed": a["info"]["seed"],
                "observation_index": prior,
                "internal_day": obs["day"],
                "hour": obs["hour"],
                "first_town_difference_index": town_difference,
                "demand_decision": compact_decision(
                    candidate, obs, a["configuration"], a["steps"][first][seat]["action"]
                ),
                "reference_decision": compact_decision(
                    cycle_3.expansion_turn,
                    obs,
                    b["configuration"],
                    b["steps"][first][seat]["action"],
                ),
                "audits": audits,
            }
        )
    result["interpretation"] = (
        "Two development seeds, not an independent leaderboard estimate. The comparison interval "
        "is descriptive only. Matched initial seeds do not fix future shop paths. "
        "Diagnostic recorded-action audits establish execution, not counterfactual outcomes."
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
