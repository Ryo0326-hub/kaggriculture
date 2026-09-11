"""Summarize crop timing and cash leadership from a reconciled replay audit."""

import argparse
import hashlib
import json
from collections import Counter, defaultdict
from pathlib import Path


def summarize(replay_path, audit_directory):
    replay = json.loads(replay_path.read_text())
    episode = replay["info"]["EpisodeId"]
    audit = json.loads((audit_directory / f"analysis-{episode}.json").read_text())
    work = json.loads((audit_directory / f"work-{episode}.json").read_text())
    digest = hashlib.sha256(replay_path.read_bytes()).hexdigest()
    if digest != audit["source_sha256"] or audit["state_mismatches"]:
        raise ValueError("Timing requires a matching, reconciled replay audit")
    tpd = replay["configuration"]["turnsPerDay"]
    players = []
    for player in audit["players"]:
        seat = player["seat"]
        plant_days, harvest_ages, harvest_sizes, fertilizer_ages = (
            defaultdict(Counter) for _ in range(4)
        )
        animal_work = defaultdict(Counter)
        for event in work:
            if event["seat"] != seat or not event["changed"]:
                continue
            step, op = event["step"], event["op"]
            if event.get("animal"):
                animal_work[(step // tpd, event["animal"])][op] += 1
            crop = event.get("crop")
            if not crop:
                continue
            if op == "PLANT":
                plant_days[crop][step // tpd + 1] += 1
            elif op == "FERTILIZE":
                fertilizer_ages[crop][event["age"]] += 1
            elif op == "HARVEST":
                x, y = event["position"]
                tile = replay["steps"][step][seat]["observation"]["farms"][seat]["tiles"][y][x]
                if not isinstance(tile, dict) or tile.get("crop") != crop:
                    raise ValueError("Crop harvest has no matching pre-action plant")
                harvest_ages[crop][step // tpd - tile["planted_day"]] += 1
                harvest_sizes[crop][event["inventory_gains"][crop]] += 1
        for crop, counts in plant_days.items():
            if sum(counts.values()) != player["planted_lots"][crop]:
                raise ValueError("Planting totals differ from the audit")
        for crop, counts in harvest_sizes.items():
            if (
                sum(size * count for size, count in counts.items())
                != player["harvested_or_collected"][crop]
            ):
                raise ValueError("Harvest quantities differ from the audit")
        sales = defaultdict(list)
        for transaction in player["transactions"]:
            if transaction["op"] == "SELL":
                sales[transaction["item"]].append(
                    {
                        "step": transaction["step"],
                        "day_number": transaction["step"] // tpd + 1,
                        "hour_zero_based": transaction["step"] % tpd,
                        "units": transaction["quantity"],
                        "cash": transaction["cash"],
                    }
                )
        players.append(
            {
                "name": player["name"],
                "seat": seat,
                "plantings_by_day_number": dict(plant_days),
                "harvests_by_age": dict(harvest_ages),
                "harvest_sizes": dict(harvest_sizes),
                "fertilizer_by_age": dict(fertilizer_ages),
                "daily_animal_work": [
                    {"day_number": d + 1, "animal": animal, "actions": dict(actions)}
                    for (d, animal), actions in sorted(animal_work.items())
                ],
                "sales": dict(sales),
                "pass_fraction": player["ops"].get("PASS", 0) / sum(player["ops"].values()),
                "last_hour_sales_fraction": sum(
                    t["cash"]
                    for t in player["transactions"]
                    if t["op"] == "SELL" and t["step"] % tpd == tpd - 1
                )
                / max(1, player["gross_sales"]),
            }
        )
    gaps = [
        s[0]["observation"]["farms"][0]["money"] - s[0]["observation"]["farms"][1]["money"]
        for s in replay["steps"]
    ]
    return {
        "episode_id": episode,
        "source_sha256": digest,
        "audit_sha256": hashlib.sha256(
            (audit_directory / f"analysis-{episode}.json").read_bytes()
        ).hexdigest(),
        "work_sha256": hashlib.sha256(
            (audit_directory / f"work-{episode}.json").read_bytes()
        ).hexdigest(),
        "day_convention": "day_number is one-based; crop ages and hours are zero-based",
        "players": players,
        "seat_0_cash_lead": {
            "maximum": max(gaps),
            "maximum_state": gaps.index(max(gaps)),
            "minimum": min(gaps),
            "minimum_state": gaps.index(min(gaps)),
            "last_trailing_state": max((i for i, gap in enumerate(gaps) if gap < 0), default=None),
            "final": gaps[-1],
        },
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("replays", nargs="+", type=Path)
    parser.add_argument("--audit-directory", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    results = [summarize(path, args.audit_directory) for path in args.replays]
    with args.output.open("x") as file:
        json.dump(results, file, indent=2)
        file.write("\n")


if __name__ == "__main__":
    main()
