"""Archive the frozen cash-admission development comparison and first changed choices."""

import argparse
import json
import runpy
from pathlib import Path

from baselines import cycle_3
from compare_results import compare
from evaluate import sha256
from scripts.report_demand import development_gate
from scripts.report_spatial import run_report


def build(root, source):
    candidate_path = root / "cycle-9-cash-development"
    reference_path = root / "cycle-6-reference-development"
    candidate, reference = run_report(candidate_path), run_report(reference_path)
    if candidate["manifest"]["candidate"]["sha256"] != sha256(source):
        raise ValueError("Candidate source changed")
    if reference["manifest"]["candidate"]["sha256"] != sha256(cycle_3.__file__):
        raise ValueError("Incumbent source changed")
    policy = runpy.run_path(str(source))["expansion_turn"]
    changes = []
    for index, (row, old_row) in enumerate(zip(candidate["matches"], reference["matches"]), 1):
        if tuple(row[k] for k in ("seed", "seat", "opponent")) != tuple(
            old_row[k] for k in ("seed", "seat", "opponent")
        ):
            raise ValueError("Match ordering differs")
        a_path, b_path = [p / f"replay-{index:04d}.json" for p in (candidate_path, reference_path)]
        a, b = [json.loads(p.read_text()) for p in (a_path, b_path)]
        seat = row["seat"]
        different = [
            i
            for i in range(1, 720)
            if a["steps"][i][seat]["action"] != b["steps"][i][seat]["action"]
        ]
        change = {
            "index": index,
            "seed": row["seed"],
            "seat": seat,
            "opponent": row["opponent"],
            "candidate_replay_sha256": sha256(a_path),
            "reference_replay_sha256": sha256(b_path),
            "own_changed_decisions": len(different),
            "own_cash_difference": row["candidate_cash"] - old_row["candidate_cash"],
            "margin_difference": row["margin"] - old_row["margin"],
            "old_outcome": old_row["outcome"],
            "new_outcome": row["outcome"],
        }
        if different:
            i = different[0] - 1
            obs, old_obs = [dict(r["steps"][i][seat]["observation"]) for r in (a, b)]
            for r, o in ((a, obs), (b, old_obs)):
                o.pop("remainingOverageTime", None)
                o["step"] = r["steps"][i][0]["observation"]["step"]
            if obs != old_obs:
                raise ValueError("Inputs already differ before the first changed decision")
            action, detail = policy(obs, a["configuration"])
            old_action, old_detail = cycle_3.expansion_turn(obs, b["configuration"])
            if (
                action != a["steps"][i + 1][seat]["action"]
                or old_action != b["steps"][i + 1][seat]["action"]
            ):
                raise ValueError("First changed action does not match source")
            old_choice = old_detail["expansion"]["chosen"]
            new_choice = detail["expansion"]["chosen"]
            old_in_new = next(
                o
                for o in detail["expansion"]["alternatives"]
                if o["orders"] == old_choice["orders"]
            )
            change["first_changed_decision"] = {
                "observation": i,
                "original_orders": old_choice["orders"],
                "original_min_cash": old_choice["min_cash"],
                "corrected_bound_for_original": old_in_new["current_day_cash"],
                "new_orders": new_choice["orders"] if new_choice else [],
                "unit_commands_unchanged": (action["farmer"], action["hands"])
                == (old_action["farmer"], old_action["hands"]),
            }
        changes.append(change)
    diagnostics = []
    for index in (5, 13):
        item = {"index": index, "audits": {}}
        replays = []
        for name, folder, run in (
            ("candidate", "cycle-9-cash-audit", candidate_path),
            ("reference", "cycle-9-reference-audit", reference_path),
        ):
            path = root / folder / f"analysis-replay-{index:04d}.json"
            replay_path = run / f"replay-{index:04d}.json"
            audit = json.loads(path.read_text())
            if audit["source_sha256"] != sha256(replay_path) or audit["state_mismatches"]:
                raise ValueError("Diagnostic audit does not reproduce its replay")
            if not all(p["cash_reconciliation_passed"] for p in audit["players"]):
                raise ValueError("Diagnostic cash reconciliation failed")
            item["audits"][name] = {
                "sha256": sha256(path),
                "players": [
                    {
                        k: v
                        for k, v in p.items()
                        if k not in ("transactions", "daily", "installations")
                    }
                    for p in audit["players"]
                ],
                "purchase_window": [
                    e
                    for e in audit["players"][0]["transactions"]
                    if 193 <= e["step"] < 216 and e["op"] in ("BUY_SEED", "HIRE")
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
    return {
        "reporter_sha256": sha256(__file__),
        "candidate": candidate,
        "reference": reference,
        "comparison": compare(candidate_path, reference_path),
        "development_gate": development_gate(candidate, reference),
        "changes": changes,
        "diagnostics": diagnostics,
        "interpretation": (
            "Three consumed seeds, both seats and three frozen reactive controls. Reuses one "
            "existing incumbent run, not new independent reference evidence. No Ace Team "
            "source is available; recorded rival future actions are never a reactive benchmark."
        ),
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path("artifacts"))
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    report = build(args.root, args.source)
    with args.output.open("x") as file:
        json.dump(report, file, separators=(",", ":"))
        file.write("\n")
    print(json.dumps(report["development_gate"], indent=2))


if __name__ == "__main__":
    main()
