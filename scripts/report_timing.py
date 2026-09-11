"""Archive the complete Cycle 3 screen and optional matched fresh-seed evaluation."""

import argparse
import json
from collections import Counter, defaultdict
from pathlib import Path
from statistics import mean

from compare_results import compare, read_run
from evaluate import sha256

LOSSES = (
    "unfed_days",
    "escapes",
    "decayed_units",
    "explicit_overflow",
    "overnight_overflow",
    "final_stock",
)


def compact_player(player):
    kept = {
        k: v
        for k, v in player.items()
        if k not in ("staffing_trace", "timing_events", "crop_sales")
    }
    work = defaultdict(lambda: {"actions": 0, "units": 0})
    for event in player["timing_events"]:
        key = (event["step"] // 24, event["op"], event["crop"])
        work[key]["actions"] += 1
        work[key]["units"] += sum(event.get("inventory_gains", {}).values())
    kept["dated_crop_work"] = [
        {"day": d, "operation": op, "crop": crop, **values}
        for (d, op, crop), values in sorted(work.items())
    ]
    sales = defaultdict(lambda: {"units": 0, "cash": 0})
    for event in player["crop_sales"]:
        key = (event["step"] // 24, event["item"])
        sales[key]["units"] += event["quantity"]
        sales[key]["cash"] += event["cash"]
    kept["dated_crop_sales"] = [
        {"day": d, "crop": crop, **values} for (d, crop), values in sorted(sales.items())
    ]
    return kept


def build(root, candidate=None, reference=None):
    fixtures = root / "cycle-3-installed-v1"
    raw = fixtures / "matches.jsonl"
    rows = [json.loads(line) for line in raw.read_text().splitlines()]
    expected = {
        (mode, q, seed, seat)
        for mode in ("fertilizer", "harvest", "combined")
        for q in (1, 2, 3)
        for seed in (17, 43)
        for seat in (0, 1)
    }
    keys = {(r["mode"], r["quadrants"], r["seed"], r["candidate_seat"]) for r in rows}
    if keys != expected or len(rows) != len(expected):
        raise ValueError("Incomplete or duplicate fixture screen")
    if any(r["statuses"] != ["DONE", "DONE"] or r["states"] != 720 for r in rows):
        raise ValueError("Resolve fixture execution errors before comparing economics")
    if any(not r[side]["cash_reconciled"] for r in rows for side in ("candidate", "reference")):
        raise ValueError("Fixture cash must reconcile")
    groups = []
    for mode in ("fertilizer", "harvest", "combined"):
        for q in (1, 2, 3):
            group = [r for r in rows if r["mode"] == mode and r["quadrants"] == q]
            groups.append(
                {
                    "mode": mode,
                    "quadrants": q,
                    "games": len(group),
                    "mean_cash_difference": mean(r["cash_difference"] for r in group),
                    "mean_wage_saving": mean(r["wage_saving"] for r in group),
                    "mean_strawberry_gain": mean(
                        r["candidate"]["outputs"].get("STRAWBERRY", 0)
                        - r["reference"]["outputs"].get("STRAWBERRY", 0)
                        for r in group
                    ),
                    "losses": {
                        side: {key: sum(r[side][key] for r in group) for key in LOSSES}
                        for side in ("candidate", "reference")
                    },
                }
            )
    runs = {}
    for label in ("reference", "fertilizer", "harvest", "combined"):
        path = root / ("cycle-2-incumbent-dev" if label == "reference" else f"cycle-3-{label}-dev")
        manifest, records = read_run(path)
        runs[label] = {
            "manifest": manifest,
            "matches": list(records.values()),
            "summary": json.loads((path / "summary.json").read_text()),
        }
        if label != "reference":
            # Validate every environment, source, seed, seat and opponent matching field.
            compare(path, root / "cycle-2-incumbent-dev")
    report = {
        "kind": "Cycle 3 development evidence; modified fixtures are not competition games",
        "fixture_manifest": json.loads((fixtures / "manifest.json").read_text()),
        "raw_fixture_sha256": sha256(raw),
        "fixture_summary": groups,
        "fixture_statuses": dict(Counter(" / ".join(r["statuses"]) for r in rows)),
        "fixtures": [
            {
                **r,
                "candidate": compact_player(r["candidate"]),
                "reference": compact_player(r["reference"]),
            }
            for r in rows
        ],
        "development_runs": runs,
    }
    if bool(candidate) != bool(reference):
        raise ValueError("Supply both frozen evaluation runs or neither")
    if candidate:
        protocol = json.loads(Path("docs/benchmarks/cycle-3-protocol.json").read_text())
        report["protocol"] = protocol
        report["fresh_comparison"] = compare(candidate, reference)
        report["fresh_runs"] = {}
        for label, path in (("candidate", candidate), ("reference", reference)):
            manifest, records = read_run(path)
            for key in (
                "environment",
                "runner_sha256",
                "seeds",
                "seats",
                "opponents",
                "evaluation_workers",
            ):
                if manifest[key] != protocol[key]:
                    raise ValueError(f"Frozen protocol mismatch: {label} {key}")
            if manifest["candidate"] != protocol[label]:
                raise ValueError(f"Frozen policy mismatch: {label}")
            report["fresh_runs"][label] = {"manifest": manifest, "matches": list(records.values())}
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--artifacts", type=Path, default=Path("artifacts"))
    parser.add_argument("--candidate", type=Path)
    parser.add_argument("--reference", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    report = build(args.artifacts, args.candidate, args.reference)
    with args.output.open("x") as file:
        json.dump(report, file, separators=(",", ":"))
        file.write("\n")


if __name__ == "__main__":
    main()
