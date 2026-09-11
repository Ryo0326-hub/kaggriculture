"""Archive the matched Cycle 10 opening screen and executed diagnostic accounts."""

import argparse
import json
from pathlib import Path

from baselines import cycle_3
from compare_results import compare
from evaluate import sha256
from scripts.report_demand import development_gate
from scripts.report_spatial import run_report


def opening_gate(candidate, reference, comparison):
    gate = development_gate(candidate, reference)
    if any(
        p["candidate_match_score"] < p["reference_match_score"]
        for p in comparison["by_opponent"].values()
    ):
        gate["reasons"].append("An opponent stratum regressed in development match score")
    gate["advance_to_fresh_evaluation"] = not gate["reasons"]
    return gate


def build(root, source):
    paths = {
        "candidate": root / "cycle-10-opening-development",
        "reference": root / "cycle-10-reference-development",
    }
    runs = {name: run_report(path) for name, path in paths.items()}
    freeze = json.loads((root / "cycle-10-opening-freeze.json").read_text())
    if freeze["candidate_sha256"] != sha256(source):
        raise ValueError("Frozen candidate source changed")
    if freeze["plan_sha256"] != sha256(
        Path(__file__).resolve().parents[1] / "docs/CYCLE_10_PLAN.md"
    ):
        raise ValueError("Preregistered plan changed")
    for name, expected in (("candidate", sha256(source)), ("reference", sha256(cycle_3.__file__))):
        if runs[name]["manifest"]["candidate"]["sha256"] != expected:
            raise ValueError("Benchmark source does not match")
        if not any(
            o["sha256"] == freeze["opponent_sha256"] for o in runs[name]["manifest"]["opponents"]
        ):
            raise ValueError("Frozen wheat stress control is missing")
    comparison = compare(paths["candidate"], paths["reference"])
    changes = []
    for index, (new, old) in enumerate(
        zip(runs["candidate"]["matches"], runs["reference"]["matches"]), 1
    ):
        if tuple(new[k] for k in ("seed", "seat", "opponent")) != tuple(
            old[k] for k in ("seed", "seat", "opponent")
        ):
            raise ValueError("Match ordering differs")
        changes.append(
            {
                "index": index,
                "seed": new["seed"],
                "seat": new["seat"],
                "opponent": new["opponent"],
                "own_cash_difference": new["candidate_cash"] - old["candidate_cash"],
                "margin_difference": new["margin"] - old["margin"],
                "old_outcome": old["outcome"],
                "new_outcome": new["outcome"],
            }
        )
    selected = {
        min(changes, key=lambda c: c["margin_difference"])["index"],
        max(changes, key=lambda c: c["margin_difference"])["index"],
    }
    diagnostics = []
    for index in sorted(selected):
        row = changes[index - 1]
        item = {"comparison": row, "audits": {}}
        replays = []
        for name, run_path in paths.items():
            replay_path = run_path / f"replay-{index:04d}.json"
            audit_path = root / f"cycle-10-{name}-audit" / f"analysis-replay-{index:04d}.json"
            audit = json.loads(audit_path.read_text())
            if audit["source_sha256"] != sha256(replay_path) or audit["state_mismatches"]:
                raise ValueError("Audit does not reproduce benchmark states")
            if not all(p["cash_reconciliation_passed"] for p in audit["players"]):
                raise ValueError("Audit cash does not reconcile")
            item["audits"][name] = {
                "replay_sha256": sha256(replay_path),
                "audit_sha256": sha256(audit_path),
                "players": [
                    {k: v for k, v in p.items() if k != "transactions"} for p in audit["players"]
                ],
                "early_transactions": [
                    e for e in audit["players"][row["seat"]]["transactions"] if e["step"] < 144
                ],
            }
            replays.append(json.loads(replay_path.read_text()))
        item["first_town_difference"] = next(
            (
                i
                for i, (a, b) in enumerate(zip(replays[0]["steps"], replays[1]["steps"]))
                if a[0]["observation"]["town"] != b[0]["observation"]["town"]
            ),
            None,
        )
        diagnostics.append(item)
    freeze["alternatives"] = [
        {k: v for k, v in option.items() if k not in ("cash_schedule", "columns")}
        for option in freeze["alternatives"]
    ]
    return {
        "reporter_sha256": sha256(__file__),
        "freeze": freeze,
        "runs": runs,
        "comparison": comparison,
        "development_gate": opening_gate(runs["candidate"], runs["reference"], comparison),
        "changes": changes,
        "diagnostics": diagnostics,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path("artifacts"))
    parser.add_argument(
        "--source", type=Path, default=Path("artifacts/cycle-10-opening-dev/main.py")
    )
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    result = build(args.root, args.source)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("x") as file:
        json.dump(result, file, indent=2)
        file.write("\n")
    print(json.dumps(result["development_gate"], indent=2))


if __name__ == "__main__":
    main()
