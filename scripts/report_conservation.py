"""Compare the isolated wheat correction and verify whether recorded decisions changed."""

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


def build(root, source):
    new_path, old_path = root / "cycle-7-wheat-development", root / "cycle-6-reference-development"
    new, old = run_report(new_path), run_report(old_path)
    if new["manifest"]["candidate"]["sha256"] != sha256(source):
        raise ValueError("Candidate source mismatch")
    if (
        sha256(cycle_3.__file__) != BASELINE_SHA256
        or old["manifest"]["candidate"]["sha256"] != BASELINE_SHA256
    ):
        raise ValueError("Reference source mismatch")
    result = {
        "reporter_sha256": sha256(__file__),
        "candidate": new,
        "reference": old,
        "comparison": compare(new_path, old_path),
        "development_gate": development_gate(new, old),
        "action_comparisons": [],
        "forecast_examples": [],
    }
    policy = runpy.run_path(str(source))
    for index, (row, reference) in enumerate(zip(new["matches"], old["matches"]), 1):
        # run_report preserves the runner's opponent/seed/seat order.
        if tuple(row[k] for k in ("seed", "seat", "opponent")) != tuple(
            reference[k] for k in ("seed", "seat", "opponent")
        ):
            raise ValueError("Replay ordering mismatch")
        paths = [p / f"replay-{index:04d}.json" for p in (new_path, old_path)]
        a, b = [json.loads(p.read_text()) for p in paths]
        own = row["seat"]
        changed = [
            i for i in range(1, 720) if a["steps"][i][own]["action"] != b["steps"][i][own]["action"]
        ]
        joint = sum(
            any(left[p]["action"] != right[p]["action"] for p in (0, 1))
            for left, right in zip(a["steps"][1:], b["steps"][1:])
        )
        result["action_comparisons"].append(
            {
                "seed": row["seed"],
                "seat": own,
                "opponent": row["opponent"],
                "candidate_replay_sha256": sha256(paths[0]),
                "reference_replay_sha256": sha256(paths[1]),
                "own_changed_decisions": len(changed),
                "joint_changed_turns": joint,
                "first_changed_action_index": changed[0] if changed else None,
                "own_cash_difference": row["candidate_cash"] - reference["candidate_cash"],
            }
        )
        if changed:
            first = changed[0]
            obs = dict(a["steps"][first - 1][own]["observation"])
            if obs != b["steps"][first - 1][own]["observation"]:
                raise ValueError("First changed decision inputs differ")
            obs["step"] = a["steps"][first - 1][0]["observation"]["step"]
            action, detail = policy["expansion_turn"](obs, a["configuration"])
            old_action, old_detail = cycle_3.expansion_turn(obs, a["configuration"])
            if (
                action != a["steps"][first][own]["action"]
                or old_action != b["steps"][first][own]["action"]
            ):
                raise ValueError("Changed decision source mismatch")
            decision = {
                "observation_index": first - 1,
                "internal_day": obs["day"],
                "hour": obs["hour"],
                "corrected_action": action,
                "original_action": old_action,
            }
            for name, info in (("corrected", detail), ("original", old_detail)):
                chosen = info["expansion"]["chosen"]
                decision[name + "_chosen"] = chosen and {
                    k: chosen[k] for k in ("orders", "marginal_value", "min_cash", "cost_now")
                }
            result["action_comparisons"][-1]["first_changed_decision"] = decision
            audits = {}
            for name, directory, replay_path in zip(
                ("candidate", "reference"),
                ("cycle-7-wheat-audit", "cycle-7-reference-audit"),
                paths,
            ):
                path = root / directory / f"analysis-replay-{index:04d}.json"
                audit = json.loads(path.read_text())
                if audit["source_sha256"] != sha256(replay_path) or audit["state_mismatches"]:
                    raise ValueError("Changed replay audit mismatch")
                if not all(p["cash_reconciliation_passed"] for p in audit["players"]):
                    raise ValueError("Changed replay cash does not reconcile")
                audits[name] = {
                    "audit_sha256": sha256(path),
                    "players": [
                        {
                            k: v
                            for k, v in p.items()
                            if k not in ("transactions", "daily", "installations")
                        }
                        for p in audit["players"]
                    ],
                }
            result["action_comparisons"][-1]["audits"] = audits
        if (
            row["opponent"].startswith("scaled_mixed")
            and own == 0
            and not result["forecast_examples"]
        ):
            for i in range(48, 719, 24):
                obs = dict(a["steps"][i][own]["observation"])
                obs["step"] = a["steps"][i][0]["observation"]["step"]
                action, detail = policy["expansion_turn"](obs, a["configuration"])
                old_action, old_detail = cycle_3.expansion_turn(obs, a["configuration"])
                if action != a["steps"][i + 1][own]["action"]:
                    raise ValueError("Candidate decision does not reproduce replay")
                choices = detail.get("expansion", {}).get("alternatives", [])
                original = old_detail.get("expansion", {}).get("alternatives", [])
                differences = []
                for option, previous in zip(choices, original):
                    if option["orders"] != previous["orders"]:
                        raise ValueError("The accounting patch changed candidate generation")
                    if option["marginal_value"] != previous["marginal_value"]:
                        differences.append(
                            {
                                "orders": option["orders"],
                                "corrected_marginal": option["marginal_value"],
                                "original_marginal": previous["marginal_value"],
                                "affordable": option["affordable"],
                                "route_feasible": option["route_feasible"],
                            }
                        )
                if differences:
                    result["forecast_examples"].append(
                        {
                            "replay_index": index,
                            "observation_index": i,
                            "internal_day": obs["day"],
                            "same_action": action == old_action,
                            "candidate_action": action,
                            "reference_action_on_same_observation": old_action,
                            "changed_marginal_forecasts": differences,
                        }
                    )
                    break
    result["interpretation"] = (
        "Three consumed development seeds. A tied score does not qualify a new upload. "
        "The reused reference is one existing run, not new independent evidence. "
        "Matching actions establish policy equivalence only on these observed trajectories."
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
