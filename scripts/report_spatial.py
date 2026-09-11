"""Archive matched spatial-admission experiments and evaluate the frozen release gate."""

import argparse
import json
from pathlib import Path
from statistics import mean

from compare_results import compare, read_run
from evaluate import sha256, summarize


def run_report(path):
    manifest, records = read_run(path)
    rows = list(records.values())
    return {
        "manifest": manifest,
        "matches": rows,
        "summary": summarize(rows),
        "mean_wages": mean(r["economics"]["candidate"]["hire_order_cost"] for r in rows),
        "mean_peak_productive_tiles": mean(
            r["economics"]["candidate"]["peak_productive_tiles"] for r in rows
        ),
        "mean_land_purchases": mean(r["economics"]["candidate"]["land_purchases"] for r in rows),
        "mean_strawberries": mean(
            r["economics"]["candidate"]["harvested_units"].get("STRAWBERRY", 0) for r in rows
        ),
        "operational_totals": {
            key: sum(r["economics"]["candidate"][key] for r in rows)
            for key in (
                "unplanned_crop_losses",
                "seed_overrequests",
                "duplicate_crop_targets",
                "animals_escaped",
                "animal_days_unfed",
            )
        },
        "terminal_units": sum(
            r["unsold_shed_units"] + r["unsold_carried_units"] + r["unused_seeds"] for r in rows
        ),
    }


def release_gate(comparison, candidate):
    reasons = []
    if comparison["bootstrap_95_percentile_interval"][0] <= 0:
        reasons.append("Paired score improvement interval is not strictly positive")
    if any(
        p["candidate_match_score"] < p["reference_match_score"]
        for p in comparison["by_opponent"].values()
    ):
        reasons.append("An opponent class regressed in aggregate match score")
    if candidate["summary"]["errors"]:
        reasons.append("Candidate has execution errors")
    if candidate["terminal_units"] or any(candidate["operational_totals"].values()):
        reasons.append("Candidate has an unresolved operational regression requiring investigation")
    return {"passes_recorded_gate": not reasons, "reasons": reasons}


def build(root, protocol):
    result = {"protocol": json.loads(protocol.read_text()), "reporter_sha256": sha256(__file__)}
    for phase, suffix in (("development", "development"), ("fresh", "eval")):
        new = root / f"cycle-4-spatial-{suffix}"
        old = root / f"cycle-4-reference-{suffix}"
        comparison = compare(new, old)
        runs = {"candidate": run_report(new), "reference": run_report(old)}
        if phase == "fresh":
            for label, run in runs.items():
                manifest = run["manifest"]
                for field in (
                    "environment",
                    "runner_sha256",
                    "lock_sha256",
                    "configuration",
                    "opponents",
                    "episode_steps",
                    "seats",
                    "seeds",
                    "evaluation_workers",
                ):
                    if manifest[field] != result["protocol"][field]:
                        raise ValueError(f"Frozen protocol differs: {field}")
                if manifest["candidate"] != result["protocol"][label]:
                    raise ValueError(f"Frozen policy differs: {label}")
        result[phase] = {"comparison": comparison, **runs}
    result["gate"] = release_gate(result["fresh"]["comparison"], result["fresh"]["candidate"])
    result["audits"] = []
    for label in ("spatial", "reference"):
        directory = root / f"cycle-4-{label}-audit"
        for index in ("0001", "0009"):
            path = directory / f"analysis-replay-{index}.json"
            audit = json.loads(path.read_text())
            replay = root / f"cycle-4-{label}-development" / f"replay-{index}.json"
            if audit["source_sha256"] != sha256(replay) or audit["state_mismatches"]:
                raise ValueError("Local audit does not match replay")
            if not all(p["cash_reconciliation_passed"] for p in audit["players"]):
                raise ValueError("Local cash audit failed")
            result["audits"].append(
                {
                    "policy": label,
                    "replay_index": index,
                    "audit_sha256": sha256(path),
                    "replay_sha256": sha256(replay),
                    "players": [
                        {
                            k: v
                            for k, v in p.items()
                            if k not in ("transactions", "daily", "installations", "final_carried")
                        }
                        for p in audit["players"]
                    ],
                }
            )
    result["interpretation"] = (
        "Local selection gate only; related internal controls and two development seeds "
        "do not establish leaderboard strength. Fresh seeds become consumed evidence. "
        "Exact artifact validation and review of runtime/operational limits are still required."
    )
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path("artifacts"))
    parser.add_argument(
        "--protocol", type=Path, default=Path("docs/benchmarks/cycle-4-protocol.json")
    )
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    result = build(args.root, args.protocol)
    with args.output.open("x") as file:
        json.dump(result, file, separators=(",", ":"))
        file.write("\n")
    print(
        json.dumps({"comparison": result["fresh"]["comparison"], "gate": result["gate"]}, indent=2)
    )


if __name__ == "__main__":
    main()
