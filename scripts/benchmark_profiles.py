"""Extract comparable production and scheduling profiles from reconciled replays.

Run audit_replay.py first. Recorded-action resimulation verifies observations;
these descriptive profiles never substitute for reactive opponent matches.
"""

import argparse
import hashlib
import json
from pathlib import Path


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def product_flows(player):
    """Separate physical output from gross trading volume and cash contribution."""
    quantities, cash = player["executed_quantities"], player["cash_by_operation"]
    products = set(player["harvested_or_collected"]) | set(player["sales_by_product"])
    products |= {key.split(" ", 1)[1] for key in quantities if key.startswith("BUY_PRODUCT ")}
    return {
        item: {
            "harvested_or_collected": player["harvested_or_collected"].get(item, 0),
            "bought": quantities.get(f"BUY_PRODUCT {item}", 0),
            "sold": quantities.get(f"SELL {item}", 0),
            "sales_cash": cash.get(f"SELL {item}", 0),
            "purchase_cash": cash.get(f"BUY_PRODUCT {item}", 0),
            "sales_less_product_purchases": cash.get(f"SELL {item}", 0)
            - cash.get(f"BUY_PRODUCT {item}", 0),
        }
        for item in sorted(products)
    }


def overnight_work(replay, seat):
    distances = []
    shifts = {"NORTH": (0, -1), "SOUTH": (0, 1), "EAST": (1, 0), "WEST": (-1, 0)}
    tpd = replay["configuration"]["turnsPerDay"]
    for before, after in zip(replay["steps"], replay["steps"][1:]):
        obs = before[seat]["observation"]
        if obs["hour"] != tpd - 1 or after[seat]["observation"]["day"] == obs["day"]:
            continue
        farm = obs["farms"][seat]
        half = len(farm["tiles"]) // 2
        access = [(x, y) for x in (half - 1, half) for y in (half - 1, half)]
        action = after[seat]["action"]
        positions = [farm["farmer"], *farm["hands"]]
        commands = [action.get("farmer", ["PASS"]), *action.get("hands", [])]
        for i, (x, y) in enumerate(positions):
            op = commands[i][0] if i < len(commands) else "PASS"
            dx, dy = shifts.get(op, (0, 0))
            nx, ny = x + dx, y + dy
            if 0 <= nx < 2 * half and 0 <= ny < 2 * half and farm["tiles"][ny][nx] != "LOCKED":
                x, y = nx, ny
            distances.append(min(abs(x - a) + abs(y - b) for a, b in access))
    return {
        "worker_days": len(distances),
        "ending_away_from_shed": sum(d > 0 for d in distances),
        "away_fraction": sum(d > 0 for d in distances) / max(1, len(distances)),
        "mean_end_distance": sum(distances) / max(1, len(distances)),
    }


def profile(replay_path, audit_directory):
    replay = json.loads(replay_path.read_text())
    episode = replay["info"].get("EpisodeId", replay_path.stem)
    audit_path = audit_directory / f"analysis-{episode}.json"
    audit = json.loads(audit_path.read_text())
    if audit["source_sha256"] != digest(replay_path) or audit["state_mismatches"]:
        raise ValueError("Profiles require a matching, reconciled replay audit")
    if not audit["recorded_actions_resimulated"]:
        raise ValueError("Replay must have been resimulated")
    players = []
    for player in audit["players"]:
        if not player["cash_reconciliation_passed"]:
            raise ValueError("Player cash does not reconcile")
        first_sales = {}
        for event in player["transactions"]:
            if event["op"] == "SELL":
                first_sales.setdefault(event["item"], event["step"])
        players.append(
            {
                "name": player["name"],
                "seat": player["seat"],
                "cash": player["cash"],
                "gross_sales": player["gross_sales"],
                "expenses": player["total_expenses"],
                "wages": player["cash_by_operation"].get("HIRE LABOR", 0),
                "peak_productive_tiles": player["max_productive_tiles"],
                "peak_hands": player["peak_hands"],
                "peak_assets": player["peak_assets"],
                "product_flows": product_flows(player),
                "first_sale_steps": first_sales,
                "land_purchase_steps": [
                    e["step"] for e in player["transactions"] if e["op"] == "BUY_LAND"
                ],
                "fertilizer_applications": player["fertilizer_applications"],
                "overnight": overnight_work(replay, player["seat"]),
                "ineffective_non_pass_ops": player["ineffective_non_pass_ops"],
                "unfed_animal_days": player["unfed_animal_days"],
                "escapes": len(player["escapes"]),
                "decayed_units": player["decayed_units"],
                "overnight_overflow_events": len(player["end_day_overflow"]),
                "final_stock_units": sum(player["final_shed"].values())
                + sum(sum(v.values()) for v in player["final_carried"]),
                "unused_seeds": sum(player["final_seeds"].values()),
            }
        )
    return {
        "episode_id": episode,
        "source_kind": audit["source_kind"],
        "source_sha256": digest(replay_path),
        "audit_sha256": digest(audit_path),
        "engine_sha256": audit["engine_sha256"],
        "players": players,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("replays", nargs="+", type=Path)
    parser.add_argument("--audit-directory", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    result = {
        "interpretation": (
            "Descriptive coverage evidence; selected losses are not a random ladder sample. "
            "Product cash excludes seeds, wages and feed opportunity cost. "
            "Overnight distance is not proof that all work was productive."
        ),
        "profiler_sha256": digest(Path(__file__)),
        "profiles": [profile(path, args.audit_directory) for path in args.replays],
    }
    with args.output.open("x") as file:
        json.dump(result, file, indent=2)
        file.write("\n")


if __name__ == "__main__":
    main()
