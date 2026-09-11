"""Passive analysis of recorded states only. Never invokes an agent or game engine."""

import argparse
import hashlib
import json
from collections import Counter, defaultdict
from pathlib import Path

ANIMALS = {"COW": "MILK", "SHEEP": "WOOL", "GOOSE": "EGG"}


def fib(index):
    a, b = 1, 1
    for _ in range(index):
        a, b = b, a + b
    return a


def market_comparison(steps):
    identical_units = identical_purchases = 0
    held = [0, 0]
    for state in steps:
        for side in (0, 1):
            held[side] += sum(
                state[side]["observation"]["private"]["shed"].get(c, 0)
                for c in ("MILK", "WOOL", "EGG", "MELON", "STRAWBERRY", "CARROT", "TOMATO")
            )
    for state in steps[1:]:
        actions = [s.get("action") or {} for s in state]
        identical_units += all(actions[0].get(k) == actions[1].get(k) for k in ("farmer", "hands"))
        purchases = [[o for o in a.get("market", []) if o and o[0] != "SELL"] for a in actions]
        identical_purchases += purchases[0] == purchases[1]
    return {
        "decisions": len(steps) - 1,
        "identical_unit_decisions": identical_units,
        "identical_non_sale_order_sequences": identical_purchases,
        "product_stock_unit_turns_by_seat": held,
        "stock_metric_excludes_wheat_fertilizer_and_animals": True,
    }


def study(path, name="Majkel1337"):
    data = json.loads(Path(path).read_text())
    names = data["info"]["TeamNames"]
    seat = names.index(name)
    steps = data["steps"]
    operations, orders, planted, harvest, ages = (Counter() for _ in range(5))
    daily_hires, land, cash_curve = defaultdict(int), [], []
    wages = peak = escaped = weeds = conflicts = overnight_hires = 0
    duplicates = 0
    peak_types = Counter()
    for before, after in zip(steps, steps[1:]):
        old, new = before[seat]["observation"], after[seat]["observation"]
        farm, following = old["farms"][seat], new["farms"][seat]
        day, hour = old["day"], old["hour"]
        action = after[seat].get("action") or {}
        if hour == 0:
            cash_curve.append({"day": day, "cash": [f["money"] for f in old["farms"]]})
        counts = Counter(
            t.get("animal") or t.get("crop")
            for row in following["tiles"]
            for t in row
            if isinstance(t, dict) and (t.get("animal") or t.get("crop"))
        )
        peak = max(peak, sum(counts.values()))
        for item, n in counts.items():
            peak_types[item] = max(peak_types[item], n)
        for order in action.get("market", []):
            if not order:
                continue
            orders[":".join(order[:2]) if len(order) > 1 else order[0]] += (
                order[2] if len(order) > 2 else 1
            )
        if new["day"] == day:
            gained = following["hires_today"] - farm["hires_today"]
            wages += sum(fib(i) for i in range(farm["hires_today"], following["hires_today"]))
            daily_hires[day] += gained
        else:
            overnight_hires += sum(bool(o) and o[0] == "HIRE" for o in action.get("market", []))
        if len(following["unlocked_quadrants"]) > len(farm["unlocked_quadrants"]):
            land.append(
                {
                    "decision_step": day * 24 + hour,
                    "quadrants": len(following["unlocked_quadrants"]),
                }
            )
        positions = [farm["farmer"], *farm["hands"]]
        commands = [action.get("farmer", ["PASS"]), *action.get("hands", [])]
        requests = Counter(op[1] for op in commands if op and op[0] == "PLANT")
        conflicts += sum(n > old["private"]["seeds"].get(c, 0) for c, n in requests.items())
        touched = set()
        for i, (p, op) in enumerate(zip(positions, commands)):
            if not op:
                continue
            operations[op[0]] += 1
            x, y = p
            tile, nxt = farm["tiles"][y][x], following["tiles"][y][x]
            key = (x, y, op[0])
            if key in touched:
                duplicates += 1
                continue
            touched.add(key)
            if op[0] == "PLANT" and not isinstance(tile, dict) and isinstance(nxt, dict):
                if nxt.get("crop") == op[1] and nxt["planted_day"] == day:
                    planted[op[1]] += 1
            if op[0] == "HARVEST" and isinstance(tile, dict) and tile.get("yield_units", 0):
                item = tile.get("crop") or ANIMALS.get(tile.get("animal"))
                # Within-day carry changes verify output without executing recorded actions.
                # A night refresh resets carries: those requests are reported separately.
                if new["day"] == day and item:
                    inv = old["private"]["inventories"][i]
                    inv2 = new["private"]["inventories"][i]
                    units = max(0, inv2.get(item, 0) - inv.get(item, 0))
                    harvest[item] += units
                    if tile.get("crop") and units:
                        ages[f"{item}:age{day - tile['planted_day']}:yield{units}"] += 1
        for y, row in enumerate(farm["tiles"]):
            for x, tile in enumerate(row):
                nxt = following["tiles"][y][x]
                if isinstance(tile, dict) and tile.get("animal"):
                    escaped += not isinstance(nxt, dict) or not nxt.get("animal")
                if isinstance(tile, dict) and tile.get("crop"):
                    weeds += isinstance(nxt, dict) and nxt.get("kind") == "WEED"
    last = steps[-1][seat]["observation"]
    return {
        "episode": data["info"]["EpisodeId"],
        "source_sha256": hashlib.sha256(Path(path).read_bytes()).hexdigest(),
        "player": name,
        "seat": seat,
        "opponent": names[1 - seat],
        "cash": [f["money"] for f in last["farms"]],
        "statuses": data["statuses"],
        "margin": last["farms"][seat]["money"] - last["farms"][1 - seat]["money"],
        "peak_productive": peak,
        "peak_by_type_not_simultaneous": dict(peak_types),
        "confirmed_planted": dict(planted),
        "confirmed_daytime_harvest_lower_bound": dict(harvest),
        "confirmed_harvest_ages": dict(sorted(ages.items())),
        "land": land,
        "accepted_daytime_hires": sum(daily_hires.values()),
        "accepted_hires_by_day": dict(daily_hires),
        "confirmed_wages": wages * data["configuration"].get("farmHandCostMult", 1),
        "unresolved_overnight_hire_requests": overnight_hires,
        "requested_orders_not_fills": dict(orders),
        "requested_operations": dict(operations),
        "seed_oversubscription_turn_products": conflicts,
        "duplicate_same_operation_coordinates": duplicates,
        "observed_animal_disappearances": escaped,
        "crop_to_weed_including_exhausted": weeds,
        "daily_cash": cash_curve,
        "terminal_shed": last["private"]["shed"],
        "terminal_carries": last["private"]["inventories"],
        "terminal_seeds": last["private"]["seeds"],
        "town": last["town"],
        "within_game_comparison": market_comparison(steps),
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("replays", nargs="+", type=Path)
    parser.add_argument("--name", default="Majkel1337")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    reports = [study(path, args.name) for path in args.replays]
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(
            {"method": "passive state differences; no simulator", "games": reports}, indent=2
        )
        + "\n"
    )
    for r in reports:
        print(
            r["episode"],
            r["margin"],
            "peak",
            r["peak_productive"],
            "wages",
            r["confirmed_wages"],
            "hires",
            r["accepted_daytime_hires"],
        )


if __name__ == "__main__":
    main()
