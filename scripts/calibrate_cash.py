"""Compare admission cash estimates with recorded no-receipt intervals, offline only."""

import argparse
import json
import runpy
from pathlib import Path
from statistics import mean

from baselines import cycle_3
from evaluate import sha256

CASES = [
    (
        "cycle8_wait",
        "artifacts/cycle-8-continuation/early_wait/wait_for_shop.json",
        "artifacts/cycle-8-continuation/early_wait/analysis-wait_for_shop.json",
    ),
    (
        "cycle8_early",
        "artifacts/cycle-8-continuation/early_wait/control.json",
        "artifacts/cycle-8-continuation/early_wait/analysis-control.json",
    ),
    (
        "cycle8_late",
        "artifacts/cycle-8-continuation/late_crop/control.json",
        "artifacts/cycle-8-continuation/late_crop/analysis-control.json",
    ),
    (
        "server_107928511",
        "/Users/ryokitano/Downloads/107928511.json",
        "artifacts/cycle-9-server-audit-fixed/analysis-107928511.json",
    ),
]
CAPITAL = {"BUY_SEED", "BUY_ANIMAL", "BUY_LAND"}


def build(source):
    candidate = runpy.run_path(str(source))["expansion_turn"]
    cases = []
    for name, replay_path, audit_path in CASES:
        replay = json.loads(Path(replay_path).read_text())
        audit = json.loads(Path(audit_path).read_text())
        if audit["source_sha256"] != sha256(replay_path) or audit["state_mismatches"]:
            raise ValueError("Audit/replay mismatch")
        if not all(p["cash_reconciliation_passed"] for p in audit["players"]):
            raise ValueError("Cash audit failed")
        cfg = replay["configuration"]
        events = audit["players"][0]["transactions"]
        rows = []
        for i, states in enumerate(replay["steps"][:-1]):
            obs = states[0]["observation"]
            recorded = replay["steps"][i + 1][0]["action"]
            if obs["day"] < 2 or not any(o and o[0] in CAPITAL for o in recorded["market"]):
                continue
            old_action, old = cycle_3.expansion_turn(obs, cfg)
            if old_action != recorded:
                raise ValueError(f"Own investment action does not match Cycle 3 at {name}:{i}")
            chosen = old["expansion"]["chosen"]
            new_action, new = candidate(obs, cfg)
            revised = next(
                o for o in new["expansion"]["alternatives"] if o["orders"] == chosen["orders"]
            )
            if chosen["projection"] != revised["projection"]:
                raise ValueError("Cash-only candidate changed the profit projection")
            sales = [e["step"] for e in events if e["op"] == "SELL" and e["step"] >= i]
            # Stop before a later capital decision, which this quote could not predict.
            purchases = [e["step"] for e in events if e["op"] in CAPITAL and e["step"] > i]
            end = min(
                (obs["day"] + 1) * cfg["turnsPerDay"],
                len(replay["steps"]) - 1,
                min(sales, default=720),
                min(purchases, default=720),
            )
            actual = min(
                replay["steps"][j][0]["observation"]["farms"][0]["money"] for j in range(i, end + 1)
            )
            bound = revised["current_day_cash"]
            extra = bound["extra_feed_cash"] + bound["extra_wage_cash"]
            original_floor = bound["before_receipts_cash"] + extra
            rows.append(
                {
                    "observation": i,
                    "day": obs["day"],
                    "hour": obs["hour"],
                    "orders": chosen["orders"],
                    "observed_minimum": actual,
                    "interval_end_observation": end,
                    "has_no_receipt_interval": end > i,
                    "original_before_receipts_cash": original_floor,
                    "new_before_receipts_cash": bound["before_receipts_cash"],
                    "original_full_projection_minimum": chosen["min_cash"],
                    "new_admission_minimum": revised["min_cash"],
                    "old_error": original_floor - actual,
                    "new_error": bound["before_receipts_cash"] - actual,
                    "bound": bound,
                    "still_affordable": revised["affordable"],
                    "candidate_action_on_recorded_state": new_action,
                    "same_action": new_action == recorded,
                }
            )
        cases.append(
            {
                "name": name,
                "replay_sha256": sha256(replay_path),
                "audit_sha256": sha256(audit_path),
                "rows": rows,
            }
        )
    rows = [r for c in cases for r in c["rows"] if r["has_no_receipt_interval"]]
    return {
        "source_sha256": sha256(source),
        "reference_sha256": sha256(cycle_3.__file__),
        "reporter_sha256": sha256(__file__),
        "cases": cases,
        "summary": {
            "eligible_intervals": len(rows),
            "old_mean_absolute_error": mean(abs(r["old_error"]) for r in rows),
            "new_mean_absolute_error": mean(abs(r["new_error"]) for r in rows),
            "old_optimistic_intervals": sum(r["old_error"] > 0 for r in rows),
            "new_optimistic_intervals": sum(r["new_error"] > 0 for r in rows),
            "recorded_purchases_rejected": sum(not r["still_affordable"] for r in rows),
        },
        "interpretation": (
            "Already observed trajectories; estimates are evaluated on recorded states, not "
            "counterfactual outcomes. Intervals end before the first sale or later capital "
            "purchase, or at the day boundary. Full-day obligations can overstate costs before "
            "an early sale. Errors are diagnostic, not independent performance evidence."
        ),
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    result = build(args.source)
    with args.output.open("x") as file:
        json.dump(result, file, separators=(",", ":"))
        file.write("\n")
    print(json.dumps(result["summary"], indent=2))


if __name__ == "__main__":
    main()
