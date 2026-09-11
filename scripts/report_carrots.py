"""Verify and archive the frozen carrot experiment and source-matched decisions."""

import argparse
import json
import runpy
from pathlib import Path

from baselines import cycle_3
from compare_results import compare
from evaluate import sha256
from scripts.report_opening import opening_gate
from scripts.report_spatial import release_gate, run_report


def compact_option(option):
    return (
        None
        if option is None
        else {
            k: option[k]
            for k in (
                "orders",
                "columns",
                "marginal_value",
                "min_cash",
                "cost_now",
                "route_feasible",
                "affordable",
            )
        }
    )


def build(root, source, phase="development"):
    paths = {
        name: root / f"cycle-11-{label}-{phase}"
        for name, label in (
            ("candidate", "carrot"),
            ("reference", "reference"),
        )
    }
    runs = {name: run_report(path) for name, path in paths.items()}
    freeze = json.loads((root / "cycle-11-freeze.json").read_text())
    if freeze["candidate_sha256"] != sha256(source) or freeze["incumbent_sha256"] != sha256(
        cycle_3.__file__
    ):
        raise ValueError("Frozen policy source changed")
    if freeze["plan_sha256"] != sha256(
        Path(__file__).resolve().parents[1] / "docs/CYCLE_11_PLAN.md"
    ):
        raise ValueError("Preregistered plan changed")
    for name, source_hash in (
        ("candidate", freeze["candidate_sha256"]),
        ("reference", freeze["incumbent_sha256"]),
    ):
        manifest = runs[name]["manifest"]
        if manifest["candidate"]["sha256"] != source_hash:
            raise ValueError("Evaluated source changed")
        if not any(o["sha256"] == freeze["pressure_sha256"] for o in manifest["opponents"]):
            raise ValueError("Carrot supply control missing")
        expected_seeds = freeze["seeds"] if phase == "development" else list(range(9401, 9421))
        if manifest["seeds"] != expected_seeds or manifest["seats"] != [0, 1]:
            raise ValueError("Wrong seeds or seats for this phase")
        if manifest["evaluation_workers"] != (2 if phase == "development" else 4):
            raise ValueError("Wrong benchmark parallelism")
    comparison = compare(paths["candidate"], paths["reference"])
    gate = (
        opening_gate(runs["candidate"], runs["reference"], comparison)
        if phase == "development"
        else release_gate(comparison, runs["candidate"])
    )
    if phase != "development" and runs["candidate"]["summary"]["decision_max_seconds"] >= 1:
        gate["reasons"].append("Decision runtime reaches one second")
        gate["passes_recorded_gate"] = False
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
                "old_outcome": old["outcome"],
                "new_outcome": new["outcome"],
                "own_cash_difference": new["candidate_cash"] - old["candidate_cash"],
                "margin_difference": new["margin"] - old["margin"],
            }
        )
    diagnostics = []
    if phase == "development":
        policy = runpy.run_path(str(source))["expansion_turn"]
        selected = {
            min(changes, key=lambda c: c["margin_difference"])["index"],
            max(changes, key=lambda c: c["margin_difference"])["index"],
        }
        for index in sorted(selected):
            row = changes[index - 1]
            item = {"comparison": row, "audits": {}}
            replays = []
            for name, path in paths.items():
                replay_path = path / f"replay-{index:04d}.json"
                audit_path = root / f"cycle-11-{name}-audit" / f"analysis-replay-{index:04d}.json"
                audit = json.loads(audit_path.read_text())
                if audit["source_sha256"] != sha256(replay_path) or audit["state_mismatches"]:
                    raise ValueError("Audit does not reproduce benchmark states")
                if not all(p["cash_reconciliation_passed"] for p in audit["players"]):
                    raise ValueError("Cash audit failed")
                item["audits"][name] = {
                    "replay_sha256": sha256(replay_path),
                    "audit_sha256": sha256(audit_path),
                    "players": [
                        {k: v for k, v in p.items() if k != "transactions"}
                        for p in audit["players"]
                    ],
                }
                if name == "candidate":
                    candidate_transactions = audit["players"][row["seat"]]["transactions"]
                replays.append(json.loads(replay_path.read_text()))
            a, b = replays
            seat = row["seat"]
            first = next(
                (
                    i
                    for i in range(1, len(a["steps"]))
                    if a["steps"][i][seat]["action"] != b["steps"][i][seat]["action"]
                ),
                None,
            )
            if a["steps"][1][seat]["action"] != b["steps"][1][seat]["action"]:
                raise ValueError("Opening changed")
            item["first_changed_action"] = first
            if first:
                observations = []
                for replay in replays:
                    obs = dict(replay["steps"][first - 1][seat]["observation"])
                    obs.pop("remainingOverageTime", None)
                    obs["step"] = replay["steps"][first - 1][0]["observation"]["step"]
                    observations.append(obs)
                if observations[0] != observations[1]:
                    raise ValueError("Inputs differ before first changed decision")
                obs = observations[0]
                details = {}
                for name, function, replay in (
                    ("candidate", policy, a),
                    ("reference", cycle_3.expansion_turn, b),
                ):
                    action, detail = function(obs, replay["configuration"], timing=1)
                    if action != replay["steps"][first][seat]["action"]:
                        raise ValueError("Source does not reproduce first changed action")
                    report = detail["expansion"]
                    details[name] = {
                        "action": action,
                        "chosen": compact_option(report["chosen"]),
                        "alternatives": [compact_option(o) for o in report["alternatives"]],
                    }
                item["decision"] = {
                    "observation": first - 1,
                    "day": obs["day"],
                    "hour": obs["hour"],
                    "shops": obs["town"],
                    "source_matched": True,
                    **details,
                }
            item["first_town_difference"] = next(
                (
                    i
                    for i, (x, y) in enumerate(zip(a["steps"], b["steps"]))
                    if x[0]["observation"]["town"] != y[0]["observation"]["town"]
                ),
                None,
            )
            # Follow-up diagnosis after the frozen screen, not another selection run.
            if index == 14:
                trace = []
                for observation in (481, 482, 625, 627):
                    obs = dict(a["steps"][observation][seat]["observation"])
                    obs["step"] = a["steps"][observation][0]["observation"]["step"]
                    action, detail = policy(obs, a["configuration"], timing=1)
                    if action != a["steps"][observation + 1][seat]["action"]:
                        raise ValueError("Fertilizer trace does not match source")
                    tiles = obs["farms"][seat]["tiles"]
                    carrot_jobs = []
                    for job in detail["mixed"]["crop_actions"]:
                        x, y = job["target"]
                        tile = tiles[y][x]
                        if isinstance(tile, dict) and tile.get("crop") == "CARROT":
                            carrot_jobs.append(job)
                    trace.append(
                        {
                            "observation": observation,
                            "shed_fertilizer": obs["private"]["shed"]["FERTILIZER"],
                            "carried_fertilizer": sum(
                                v.get("FERTILIZER", 0) for v in obs["private"]["inventories"]
                            ),
                            "retained_fertilizer": detail["mixed"]["retained_fertilizer"],
                            "positive_crop_values": detail["mixed"]["fertilizer_values"],
                            "carrot_jobs": carrot_jobs,
                            "action": action,
                            "source_matched": True,
                        }
                    )
                item["fertilizer_followup"] = {
                    "trace": trace,
                    "executed_trade_pair": [
                        e
                        for e in candidate_transactions
                        if e["step"] in (481, 482) and e["item"] == "FERTILIZER"
                    ],
                    "interpretation": (
                        "Urgent watering bypasses carrot fertilizer; purchase-induced price "
                        "changes can also cancel the next-turn fertilizer target."
                    ),
                }
            diagnostics.append(item)
    return {
        "reporter_sha256": sha256(__file__),
        "freeze": freeze,
        "phase": phase,
        "runs": runs,
        "comparison": comparison,
        "gate": gate,
        "changes": changes,
        "diagnostics": diagnostics,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path("artifacts"))
    parser.add_argument(
        "--source", type=Path, default=Path("artifacts/cycle-11-carrot-dev/main.py")
    )
    parser.add_argument("--phase", choices=("development", "evaluation"), default="development")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    report = build(args.root, args.source, args.phase)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("x") as file:
        json.dump(report, file, indent=2)
        file.write("\n")
    print(json.dumps(report["gate"], indent=2))


if __name__ == "__main__":
    main()
