"""Archive Cycle 12, keeping the incumbent and carrot ablation comparisons distinct."""

import argparse
import json
import runpy
from collections import Counter
from hashlib import sha256 as digest
from pathlib import Path

from compare_results import compare
from evaluate import sha256
from scripts.report_opening import opening_gate
from scripts.report_spatial import release_gate, run_report


def carrot_applications(replay, seat):
    """Observed successful expiry changes, not merely requested action counts."""
    counts = Counter()
    for before, after in zip(replay["steps"], replay["steps"][1:]):
        obs = before[seat]["observation"]
        farm = obs["farms"][seat]
        action = after[seat]["action"]
        for p, inv, op in zip(
            [farm["farmer"], *farm["hands"]],
            obs["private"]["inventories"],
            [action["farmer"], *action["hands"]],
        ):
            x, y = p
            tile = farm["tiles"][y][x]
            post = after[seat]["observation"]["farms"][seat]["tiles"][y][x]
            if (
                op == ["FERTILIZE"]
                and inv.get("FERTILIZER", 0)
                and isinstance(tile, dict)
                and tile.get("crop") == "CARROT"
                and isinstance(post, dict)
                and post.get("crop") == "CARROT"
                and post["fertilized_until_day"] == obs["day"] + 2
                and tile["fertilized_until_day"] < post["fertilized_until_day"]
            ):
                counts["applications"] += 1
                counts["before_water"] += int(not tile["watered_today"])
    return dict(counts)


def build(root, summary_only=False):
    source = root / "cycle-12-input-dev/main.py"
    paths = {
        "candidate": root / "cycle-12-input-development",
        "ablation": root / "cycle-11-carrot-development",
        "incumbent": root / "cycle-11-reference-development",
    }
    freeze = json.loads((root / "cycle-12-freeze.json").read_text())
    runs = {name: run_report(path) for name, path in paths.items()}
    if freeze["plan_sha256"] != sha256(
        Path(__file__).resolve().parents[1] / "docs/CYCLE_12_PLAN.md"
    ):
        raise ValueError("Preregistered plan changed")
    sources = {
        "candidate": source,
        "ablation": root / "cycle-11-carrot-dev/main.py",
        "incumbent": Path(__file__).resolve().parents[1] / "baselines/cycle_3.py",
    }
    for name, run in runs.items():
        m = run["manifest"]
        if (
            m["candidate"]["sha256"] != freeze[name + "_sha256"]
            or sha256(sources[name]) != freeze[name + "_sha256"]
        ):
            raise ValueError("Source differs from freeze or evaluated source")
        if (
            m["seeds"] != freeze["seeds"]
            or m["seats"] != freeze["seats"]
            or m["evaluation_workers"] != 2
        ):
            raise ValueError("Development grid differs from plan")
        if not any(o["sha256"] == freeze["pressure_sha256"] for o in m["opponents"]):
            raise ValueError("Pressure opponent missing")
    archived = json.loads(
        (Path(__file__).resolve().parents[1] / "docs/benchmarks/cycle-11-carrots.json").read_text()
    )
    for name, label, historical in (
        ("incumbent", "reference", "reference"),
        ("ablation", "ablation", "candidate"),
    ):
        recorded = archived["runs"][historical]["manifest"]
        original_bytes = (json.dumps(recorded, indent=2) + "\n").encode()
        if digest(original_bytes).hexdigest() != freeze[label + "_manifest_sha256"]:
            raise ValueError("Archived reference differs from frozen provenance")
        # A new reproduction gets its real timestamp. Every substantive field
        # must still match the original evaluated reference; do not forge dates.
        if {k: v for k, v in recorded.items() if k != "created_at"} != {
            k: v for k, v in runs[name]["manifest"].items() if k != "created_at"
        }:
            raise ValueError("Reused or reproduced reference protocol changed")
    comparisons = {
        name: compare(paths["candidate"], paths[name]) for name in ("ablation", "incumbent")
    }
    changes = []
    for index, (new, old) in enumerate(
        zip(runs["candidate"]["matches"], runs["ablation"]["matches"]), 1
    ):
        if tuple(new[k] for k in ("seed", "seat", "opponent")) != tuple(
            old[k] for k in ("seed", "seat", "opponent")
        ):
            raise ValueError("Ordering differs")
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
    selected = sorted(
        {
            min(changes, key=lambda c: c["margin_difference"])["index"],
            max(changes, key=lambda c: c["margin_difference"])["index"],
        }
    )
    result = {
        "reporter_sha256": sha256(__file__),
        "freeze": freeze,
        "runs": runs,
        "comparisons": comparisons,
        "gate": opening_gate(runs["candidate"], runs["incumbent"], comparisons["incumbent"]),
        "changes_vs_cycle_11": changes,
        "diagnostic_indices": selected,
    }
    if summary_only:
        return result
    result["application_counts"] = {}
    for name in ("candidate", "ablation"):
        result["application_counts"][name] = []
        for index, row in enumerate(runs[name]["matches"], 1):
            replay = json.loads((paths[name] / f"replay-{index:04d}.json").read_text())
            result["application_counts"][name].append(
                {"index": index, **carrot_applications(replay, row["seat"])}
            )
    policies = {
        name: runpy.run_path(str(sources[name]))["expansion_turn"]
        for name in ("candidate", "ablation")
    }
    diagnostics = []
    for index in selected:
        item = {"comparison": changes[index - 1], "audits": {}}
        seat = item["comparison"]["seat"]
        replays = {}
        for name in ("candidate", "ablation"):
            path = paths[name] / f"replay-{index:04d}.json"
            audit_path = root / f"cycle-12-{name}-audit" / f"analysis-replay-{index:04d}.json"
            audit = json.loads(audit_path.read_text())
            if (
                audit["source_sha256"] != sha256(path)
                or audit["state_mismatches"]
                or not all(p["cash_reconciliation_passed"] for p in audit["players"])
            ):
                raise ValueError("Economic state/cash audit failed")
            replays[name] = json.loads(path.read_text())
            item["audits"][name] = {
                "replay_sha256": sha256(path),
                "audit_sha256": sha256(audit_path),
                "players": [
                    {
                        k: v
                        for k, v in p.items()
                        if k not in ("transactions", "daily", "installations")
                    }
                    for p in audit["players"]
                ],
            }
            # Actual input trading is distinct from crop production receipts.
            transactions = audit["players"][seat]["transactions"]
            item["audits"][name]["fertilizer_transactions"] = [
                t for t in transactions if t["item"] == "FERTILIZER"
            ]
        a, b = replays["candidate"], replays["ablation"]
        first = next(
            (
                i
                for i in range(1, len(a["steps"]))
                if a["steps"][i][seat]["action"] != b["steps"][i][seat]["action"]
            ),
            None,
        )
        item["first_changed_action"] = first
        if first:
            observations = []
            for r in (a, b):
                obs = dict(r["steps"][first - 1][seat]["observation"])
                obs.pop("remainingOverageTime", None)
                obs["step"] = r["steps"][first - 1][0]["observation"]["step"]
                observations.append(obs)
            if observations[0] != observations[1]:
                raise ValueError("Observations differ before first changed action")
            item["first_decision"] = {
                "observation": first - 1,
                "day": observations[0]["day"],
                "hour": observations[0]["hour"],
                "shops": observations[0]["town"],
            }
            for name in ("candidate", "ablation"):
                action, detail = policies[name](observations[0], replays[name]["configuration"])
                if action != replays[name]["steps"][first][seat]["action"]:
                    raise ValueError("Decision source does not reproduce action")
                chosen = detail.get("expansion", {}).get("chosen")
                item["first_decision"][name] = {
                    "action": action,
                    "source_matched": True,
                    "chosen": {k: v for k, v in chosen.items() if k != "projection"}
                    if chosen
                    else None,
                    "carrot_inputs": detail["mixed"].get("carrot_inputs"),
                }
        item["first_town_difference"] = next(
            (
                i
                for i, (x, y) in enumerate(zip(a["steps"], b["steps"]))
                if x[0]["observation"]["town"] != y[0]["observation"]["town"]
            ),
            None,
        )
        diagnostics.append(item)
    result["diagnostics"] = diagnostics
    return result


def fresh_report(root, development):
    paths = {
        "candidate": root / "cycle-12-input-evaluation",
        "incumbent": root / "cycle-12-reference-evaluation",
    }
    runs = {name: run_report(path) for name, path in paths.items()}
    comparison = compare(paths["candidate"], paths["incumbent"])
    for name, run in runs.items():
        manifest = run["manifest"]
        if manifest["candidate"]["sha256"] != development["freeze"][name + "_sha256"]:
            raise ValueError("Fresh policy differs from development freeze")
        if (
            manifest["seeds"] != list(range(9401, 9421))
            or manifest["seats"] != [0, 1]
            or manifest["evaluation_workers"] != 4
        ):
            raise ValueError("Fresh grid differs from preregistration")
        for field in (
            "environment",
            "configuration",
            "opponents",
            "runner_sha256",
            "lock_sha256",
            "episode_steps",
        ):
            if manifest[field] != development["runs"][name]["manifest"][field]:
                raise ValueError("Fresh environment or controls differ from development")
    gate = release_gate(comparison, runs["candidate"])
    if not development["gate"]["advance_to_fresh_evaluation"]:
        gate["reasons"].append("Development gate failed")
    if runs["candidate"]["summary"]["decision_max_seconds"] >= 1:
        gate["reasons"].append("Fresh runtime reaches one second")
    gate["passes_recorded_gate"] = not gate["reasons"]
    return {"runs": runs, "comparison": comparison, "gate": gate}


def server_handoff(root):
    """Read existing evidence only; never complete or extrapolate an interrupted run."""
    partial = root / "cycle-12-reference-evaluation"
    manifest = json.loads((partial / "manifest.json").read_text())
    rows = [json.loads(line) for line in (partial / "matches.jsonl").read_text().splitlines()]
    return {
        "user_direction": "Stop local simulations; user uploads to Kaggle and supplies game logs.",
        "completed_candidate_run": run_report(root / "cycle-12-input-evaluation"),
        "interrupted_reference": {
            "manifest": manifest,
            "completed_games": len(rows),
            "planned_games": len(manifest["seeds"])
            * len(manifest["seats"])
            * len(manifest["opponents"]),
            "matches": rows,
            "matches_file_sha256": sha256(partial / "matches.jsonl"),
            "complete": False,
        },
        "final_paired_comparison_claimed": False,
        "local_release_gate_claimed_passed": False,
        "packaging": json.loads(
            (root / "submission-cycle-12-carrot-inputs/packaging.json").read_text()
        ),
        "next_evidence": "Kaggle server validation and user-supplied ladder replays.",
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path("artifacts"))
    parser.add_argument("--summary-only", action="store_true")
    parser.add_argument("--fresh", action="store_true")
    parser.add_argument("--server-handoff", action="store_true")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.fresh and args.server_handoff:
        parser.error("Choose complete fresh reporting or interrupted server handoff, not both")
    report = build(args.root, args.summary_only)
    if args.fresh:
        report["fresh"] = fresh_report(args.root, report)
    if args.server_handoff:
        report["server_handoff"] = server_handoff(args.root)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("x") as file:
        json.dump(report, file, indent=2)
        file.write("\n")
    print(
        json.dumps(
            {
                "gate": report["gate"],
                "diagnostic_indices": report["diagnostic_indices"],
                "fresh_gate": report.get("fresh", {}).get("gate"),
            }
        )
    )


if __name__ == "__main__":
    main()
