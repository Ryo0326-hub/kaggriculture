"""Archive a complete staffing development screen, with compact executed-work evidence."""

import argparse
import json
from pathlib import Path
from statistics import mean

from compare_results import read_run
from evaluate import sha256

RUNS = ("incumbent", "open", "dated-closed", "dated-open", "forecast", "open-forecast", "combined")
LOSSES = (
    "unfed_days",
    "escapes",
    "decayed_units",
    "explicit_overflow",
    "overnight_overflow",
    "final_stock",
)
TRACE_COLUMNS = (
    "day",
    "hour",
    "workers_present",
    "worker_target",
    "hire_orders",
    "crop_work_bound",
    "dated_crop_jobs",
    "dated_crop_routes",
    "max_route_steps",
    "route_feasible",
)


def compact_player(player):
    result = {k: v for k, v in player.items() if k != "staffing_trace"}
    result["staffing_trace"] = []
    for row in player["staffing_trace"]:
        routes = row["crop_routes"]
        result["staffing_trace"].append(
            [row[k] for k in TRACE_COLUMNS[:6]]
            + (
                [
                    len(routes["nodes"]),
                    len(routes["routes"]),
                    max(routes["steps"], default=0),
                    routes["feasible"],
                ]
                if routes is not None
                else [None] * 4
            )
        )
    return result


def build(artifacts):
    installed = artifacts / "cycle-2-installed-v1"
    raw = installed / "matches.jsonl"
    fixtures = [json.loads(line) for line in raw.read_text().splitlines()]
    expected = {
        (mode, q, seed, seat)
        for mode in ("open_routes", "dated_closed", "dated_open")
        for q in (1, 2, 3)
        for seed in (17, 43)
        for seat in (0, 1)
    }
    keys = {(r["mode"], r["quadrants"], r["seed"], r["candidate_seat"]) for r in fixtures}
    if keys != expected or len(fixtures) != len(expected):
        raise ValueError("Installed-portfolio screen is incomplete or duplicated")
    for row in fixtures:
        if row["statuses"] != ["DONE", "DONE"]:
            raise ValueError("Resolve fixture errors first")
        for side in ("candidate", "reference"):
            if not row[side]["cash_reconciled"]:
                raise ValueError("Fixture cash must reconcile before comparison")
    groups = []
    for mode in ("open_routes", "dated_closed", "dated_open"):
        for q in (1, 2, 3):
            rows = [r for r in fixtures if r["mode"] == mode and r["quadrants"] == q]
            products = sorted(
                {p for r in rows for s in ("candidate", "reference") for p in r[s]["outputs"]}
            )
            groups.append(
                {
                    "mode": mode,
                    "quadrants": q,
                    "games": len(rows),
                    "mean_cash_difference": mean(r["cash_difference"] for r in rows),
                    "mean_wage_saving": mean(r["wage_saving"] for r in rows),
                    "mean_output_difference": {
                        p: mean(
                            r["candidate"]["outputs"].get(p, 0)
                            - r["reference"]["outputs"].get(p, 0)
                            for r in rows
                        )
                        for p in products
                    },
                    "losses": {
                        s: {k: sum(r[s][k] for r in rows) for k in LOSSES}
                        for s in ("candidate", "reference")
                    },
                }
            )
    runs = {}
    reference_manifest, reference = read_run(artifacts / "cycle-2-incumbent-dev")
    for label in RUNS:
        path = artifacts / f"cycle-2-{label}-dev"
        manifest, rows = read_run(path)
        for key in (
            "environment",
            "configuration",
            "seeds",
            "seats",
            "opponents",
            "runner_sha256",
            "lock_sha256",
            "evaluation_workers",
        ):
            if manifest[key] != reference_manifest[key]:
                raise ValueError(f"Unmatched development run {label}: {key}")
        runs[label] = {
            "manifest": manifest,
            "summary": json.loads((path / "summary.json").read_text()),
            "matches": list(rows.values()),
            "mean_cash_change_from_reference": mean(
                r["candidate_cash"] - reference[k]["candidate_cash"] for k, r in rows.items()
            ),
        }
    return {
        "purpose": "Development only; no untouched holdout or leaderboard inference",
        "decision": "Reject all six release candidates; preserve the submitted Step 8 artifact",
        "fixture_manifest": json.loads((installed / "manifest.json").read_text()),
        "raw_fixture_sha256": sha256(raw),
        "fixture_trace_columns": TRACE_COLUMNS,
        "fixture_summary": groups,
        "fixtures": [
            {
                **r,
                "candidate": compact_player(r["candidate"]),
                "reference": compact_player(r["reference"]),
            }
            for r in fixtures
        ],
        "standard_start_runs": runs,
        "initial_projection_probe": json.loads(
            (artifacts / "cycle-2-projection-probe.json").read_text()
        ),
        "limitations": [
            "Only two development seeds, multiple candidates, related opponent families.",
            "Different actions change shared prices, rival behavior and subsequent investments.",
            "No statistical superiority claim; new validation seeds were not consumed.",
            "Heuristic route rejection does not prove that no feasible schedule exists.",
            "Fixture outputs use inventory gains; standard output counters are diagnostics.",
        ],
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--artifacts", type=Path, default=Path("artifacts"))
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    report = build(args.artifacts)
    with args.output.open("x") as file:
        json.dump(report, file, separators=(",", ":"))
        file.write("\n")


if __name__ == "__main__":
    main()
