"""Resimulate a trusted Kaggriculture replay and reconcile executed transactions."""

import argparse
import copy
import hashlib
import json
from collections import Counter, defaultdict
from pathlib import Path

from kaggle_environments import make
from kaggle_environments.envs.kaggriculture import kaggriculture as engine

ORIGINAL = {
    name: getattr(engine, name)
    for name in [
        "_process_market",
        "_commit_unit",
        "_do_hire",
        "_do_buy_land",
        "_apply_unit_action",
        "_drop_inventories_to_shed",
        "_decay_plants",
        "_daily_refresh_animals",
    ]
}
context = {}


def on_market(state, env):
    context["farm_ids"] = {id(f): i for i, f in enumerate(state[0].observation.farms)}
    return ORIGINAL["_process_market"](state, env)


def on_commit(op, item, price, farm, private, market, capacity=100):
    result = ORIGINAL["_commit_unit"](op, item, price, farm, private, market, capacity)
    if result:
        seat = context["farm_ids"][id(farm)]
        context["transactions"].append(
            {
                "step": context["step"],
                "seat": seat,
                "op": op,
                "item": item,
                "quantity": 1,
                "cash": price,
            }
        )
    return result


def on_hire(farm, private, size, mult=1):
    before = farm["money"]
    ORIGINAL["_do_hire"](farm, private, size, mult)
    if before != farm["money"]:
        seat = context["farm_ids"][id(farm)]
        context["transactions"].append(
            {
                "step": context["step"],
                "seat": seat,
                "op": "HIRE",
                "item": "LABOR",
                "quantity": 1,
                "cash": before - farm["money"],
            }
        )


def on_land(farm, size):
    before = farm["money"]
    ORIGINAL["_do_buy_land"](farm, size)
    if before != farm["money"]:
        seat = context["farm_ids"][id(farm)]
        context["transactions"].append(
            {
                "step": context["step"],
                "seat": seat,
                "op": "BUY_LAND",
                "item": "LAND",
                "quantity": 1,
                "cash": before - farm["money"],
            }
        )


def on_unit(farm, private, idx, action, size, day, tpd, capacity=100):
    p = engine._farmer_position(farm, idx)
    if p is None:
        return ORIGINAL["_apply_unit_action"](farm, private, idx, action, size, day, tpd, capacity)
    seat = next(i for i, f in enumerate(context["unit_farms"]) if farm is f)
    p = tuple(p)
    tile = copy.deepcopy(farm["tiles"][p[1]][p[0]])
    inv = dict(engine._farmer_inventory(private, idx))
    shed = dict(private["shed"])
    seeds = dict(private["seeds"])
    ORIGINAL["_apply_unit_action"](farm, private, idx, action, size, day, tpd, capacity)
    new_p = tuple(engine._farmer_position(farm, idx))
    new_inv = engine._farmer_inventory(private, idx)
    new_tile = farm["tiles"][p[1]][p[0]]
    changed = (
        p != new_p
        or tile != new_tile
        or inv != new_inv
        or shed != private["shed"]
        or seeds != private["seeds"]
    )
    op = action[0] if isinstance(action, list) and action else "PASS"
    event = {
        "step": context["step"],
        "seat": seat,
        "worker": idx,
        "position": p,
        "op": op,
        "changed": changed,
    }
    if isinstance(tile, dict):
        event["tile_type"] = tile.get("animal", tile.get("crop", tile.get("kind")))
        event["animal"] = tile.get("animal")
        event["crop"] = tile.get("crop")
        if op == "FERTILIZE" and changed:
            event["age"] = day - tile["planted_day"]
    gains = {k: v - inv.get(k, 0) for k, v in new_inv.items() if v > inv.get(k, 0)}
    if gains:
        event["inventory_gains"] = gains
    if op == "PLANT" and changed:
        event["crop"] = action[1]
    if op == "PLACE" and len(action) > 1 and action[1] in engine.ANIMALS and changed:
        event["installed"] = action[1]
    if op == "DROP" or (op == "PLACE" and len(action) > 1 and action[1] in engine.PRODUCTS):
        losses = {
            k: inv.get(k, 0) + shed.get(k, 0) - new_inv.get(k, 0) - private["shed"].get(k, 0)
            for k in engine.PRODUCTS
        }
        event["overflow"] = {k: v for k, v in losses.items() if v > 0}
    context["unit_events"].append(event)


def on_drop(private, capacity):
    old = Counter(private["shed"])
    for inv in private["inventories"]:
        old.update(inv)
    ORIGINAL["_drop_inventories_to_shed"](private, capacity)
    new = Counter(private["shed"])
    for inv in private["inventories"]:
        new.update(inv)
    lost = old - new
    if lost:
        seat = context["drop_seat"]
        context["overflow"].append({"step": context["step"], "seat": seat, "items": dict(lost)})
    context["drop_seat"] += 1


def on_decay(farm, step):
    seat = context["decay_seat"]
    old = {
        (x, y): (t["crop"], t["yield_units"])
        for y, row in enumerate(farm["tiles"])
        for x, t in enumerate(row)
        if isinstance(t, dict) and t.get("kind") == "PLANT"
    }
    ORIGINAL["_decay_plants"](farm, step)
    for (x, y), (crop, units) in old.items():
        tile = farm["tiles"][y][x]
        new = tile.get("yield_units", 0) if isinstance(tile, dict) else 0
        if new < units:
            context["decay"].append(
                {"step": step, "seat": seat, "crop": crop, "units": units - new}
            )
    context["decay_seat"] += 1


def on_animals(farm, day):
    old = {
        (x, y): t["animal"]
        for y, row in enumerate(farm["tiles"])
        for x, t in enumerate(row)
        if isinstance(t, dict) and "animal" in t
    }
    seat = context["animal_seat"]
    ORIGINAL["_daily_refresh_animals"](farm, day)
    for (x, y), animal in old.items():
        new = farm["tiles"][y][x]
        if "animal" not in new:
            context["escapes"].append({"day": day, "seat": seat, "animal": animal})
        elif new["consecutive_unfed"]:
            context["missed_feed"].append({"day": day, "seat": seat, "animal": animal})
    context["animal_seat"] += 1


def analyze(path, output):
    replay = json.loads(path.read_text())
    context.clear()
    context.update(
        transactions=[], unit_events=[], overflow=[], decay=[], escapes=[], missed_feed=[]
    )
    env = make(
        "kaggriculture", configuration={**replay["configuration"], "seed": replay["info"]["seed"]}
    )
    mismatches = Counter()
    # Register the actual farm references passed by the interpreter each step.
    base_interpreter = env.interpreter

    def interpret(state, environment):
        context["unit_farms"] = state[0].observation.farms
        return base_interpreter(state, environment)

    env.interpreter = interpret
    for step, states in enumerate(replay["steps"][1:]):
        context.update(step=step, drop_seat=0, decay_seat=0, animal_seat=0)
        env.step([s["action"] for s in states])
        for seat in range(2):
            for field in ["farms", "private", "market", "day", "hour", "town"]:
                if states[seat]["observation"].get(field) != env.state[seat].observation.get(field):
                    mismatches[field] += 1
    assert not mismatches, mismatches
    result = {
        "episode_id": replay["info"].get("EpisodeId", path.stem),
        "source_kind": "server" if "EpisodeId" in replay["info"] else "local",
        "source_sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
        "engine_sha256": hashlib.sha256(Path(engine.__file__).read_bytes()).hexdigest(),
        "module_version": replay["module_version"],
        "configuration": replay["configuration"],
        "recorded_actions_resimulated": True,
        "state_mismatches": dict(mismatches),
        "players": [],
        "shops": [],
    }
    for state in replay["steps"]:
        o = state[0]["observation"]
        if o["hour"] == 0:
            result["shops"].append(
                {
                    "day": o["day"],
                    "shops": o["town"]["unlocked_shops"],
                    "prices": o["market"]["prices"],
                }
            )
    agents = replay["info"].get("Agents", [{"Name": "Player 0"}, {"Name": "Player 1"}])
    for seat, meta in enumerate(agents):
        events = [t for t in context["transactions"] if t["seat"] == seat]
        units = [u for u in context["unit_events"] if u["seat"] == seat]
        quantities = Counter()
        cash = Counter()
        # Keep per-turn/product exact fills, not one record per individual unit.
        grouped = defaultdict(lambda: {"quantity": 0, "cash": 0})
        for e in events:
            key = e["op"] + " " + e["item"]
            quantities[key] += e["quantity"]
            cash[key] += e["cash"]
            g = grouped[(e["step"], e["op"], e["item"])]
            g["quantity"] += e["quantity"]
            g["cash"] += e["cash"]
        sales = sum(v for k, v in cash.items() if k.startswith("SELL "))
        expenses = sum(v for k, v in cash.items() if not k.startswith("SELL "))
        final = replay["steps"][-1][seat]["observation"]
        assert (
            replay["configuration"]["startingMoney"] + sales - expenses
            == final["farms"][seat]["money"]
        )
        daily = []
        peak = Counter()
        max_occupied = 0
        requests = Counter()
        unsupported = Counter()
        for j, states in enumerate(replay["steps"]):
            s = states[seat]
            o = s["observation"]
            f = o["farms"][seat]
            counts = Counter(
                t.get("animal", t.get("crop", t.get("kind")))
                for row in f["tiles"]
                for t in row
                if isinstance(t, dict)
            )
            for k, n in counts.items():
                peak[k] = max(peak[k], n)
            max_occupied = max(
                max_occupied,
                sum(n for k, n in counts.items() if k in engine.CROPS or k in engine.ANIMALS),
            )
            action = s.get("action") or {}
            for order in action.get("market", [])[
                : replay["configuration"]["maxMarketOrdersPerTurn"]
            ]:
                if not order:
                    continue  # The interpreter accepts and ignores empty market orders.
                key = " ".join(map(str, order[:2]))
                requests[key] += 1
                if order[0] == "BUY_PRODUCT" and order[1] not in ("WHEAT", "FERTILIZER"):
                    unsupported[key] += 1
            if o["hour"] == 0:
                day = o["day"]
                dd = [u for u in units if u["step"] // 24 == day]
                daily.append(
                    {
                        "day": day,
                        "opening_cash": f["money"],
                        "portfolio": dict(counts),
                        "land_tiles": 25 * len(f["unlocked_quadrants"]),
                        "hands_hired": sum(
                            t["quantity"]
                            for t in events
                            if t["op"] == "HIRE" and t["step"] // 24 == day
                        ),
                        "wages": sum(
                            t["cash"]
                            for t in events
                            if t["op"] == "HIRE" and t["step"] // 24 == day
                        ),
                        "sales": sum(
                            t["cash"]
                            for t in events
                            if t["op"] == "SELL" and t["step"] // 24 == day
                        ),
                        "unit_ops": dict(Counter(u["op"] for u in dd)),
                    }
                )
        roles = defaultdict(lambda: {"animals": set(), "crops": set()})
        for u in units:
            if u["changed"] and u["op"] in (
                "FEED",
                "CARE",
                "HARVEST",
                "COLLECT_FERTILIZER",
                "WATER",
                "PLANT",
                "FERTILIZE",
            ):
                role = roles[(u["step"] // 24, u["worker"])]
                if u.get("animal"):
                    role["animals"].add(tuple(u["position"]))
                if u.get("crop"):
                    role["crops"].add(tuple(u["position"]))
        produces = Counter()
        fertilizes = Counter()
        plantings = Counter()
        installation = []
        for u in units:
            if u["op"] in ("HARVEST", "COLLECT_FERTILIZER"):
                produces.update(u.get("inventory_gains", {}))
            if u["op"] == "FERTILIZE" and u["changed"]:
                fertilizes[u["crop"]] += 1
            if u["op"] == "PLANT" and u["changed"]:
                plantings[u["crop"]] += 1
            if u.get("installed"):
                installation.append({k: u[k] for k in ["step", "installed", "position"]})
        bank_gaps = [
            f["observation"]["farms"][seat]["money"]
            for states in replay["steps"]
            for f in [states[seat]]
        ]
        item_sales = {}
        for product in engine.PRODUCTS:
            fills = [t for t in events if t["op"] == "SELL" and t["item"] == product]
            if fills:
                item_sales[product] = {
                    "units": len(fills),
                    "revenue": sum(t["cash"] for t in fills),
                    "mean_price": sum(t["cash"] for t in fills) / len(fills),
                    "min_price": min(t["cash"] for t in fills),
                    "max_price": max(t["cash"] for t in fills),
                    "floor_units": sum(t["cash"] == 1 for t in fills),
                }
        item = {
            "name": meta["Name"],
            "seat": seat,
            "cash": final["farms"][seat]["money"],
            "gross_sales": sales,
            "total_expenses": expenses,
            "cash_reconciliation_passed": True,
            "executed_quantities": dict(quantities),
            "cash_by_operation": dict(cash),
            "sales_by_product": item_sales,
            "requested_order_counts": dict(requests),
            "unsupported_buy_orders": dict(unsupported),
            "ops": dict(Counter(u["op"] for u in units)),
            "ineffective_non_pass_ops": dict(
                Counter(u["op"] for u in units if not u["changed"] and u["op"] != "PASS")
            ),
            "harvested_or_collected": dict(produces),
            "fertilizer_applications": dict(fertilizes),
            "planted_lots": dict(plantings),
            "peak_assets": dict(peak),
            "max_productive_tiles": max_occupied,
            "peak_hands": max(
                len(s[seat]["observation"]["farms"][seat]["hands"]) for s in replay["steps"]
            ),
            "minimum_cash": min(bank_gaps),
            "daily": daily,
            "installations": installation,
            "productive_worker_days": len(roles),
            "multi_animal_worker_days": sum(len(v["animals"]) > 1 for v in roles.values()),
            "mixed_crop_animal_worker_days": sum(
                bool(v["animals"]) and bool(v["crops"]) for v in roles.values()
            ),
            "escapes": [x for x in context["escapes"] if x["seat"] == seat],
            "unfed_animal_days": len([x for x in context["missed_feed"] if x["seat"] == seat]),
            "decayed_units": dict(
                Counter(
                    {
                        c: sum(
                            e["units"]
                            for e in context["decay"]
                            if e["seat"] == seat and e["crop"] == c
                        )
                        for c in engine.CROPS
                    }
                )
            ),
            "end_day_overflow": [x for x in context["overflow"] if x["seat"] == seat],
            "explicit_overflow": [u for u in units if u.get("overflow")],
            "final_shed": final["private"]["shed"],
            "final_carried": final["private"]["inventories"],
            "final_seeds": final["private"]["seeds"],
            "transactions": [
                {"step": key[0], "op": key[1], "item": key[2], **g}
                for key, g in sorted(grouped.items())
            ],
        }
        result["players"].append(item)
    (output / f"analysis-{result['episode_id']}.json").write_text(
        json.dumps(result, indent=2) + "\n"
    )
    # Compact successful work events support timing/resource analyses without raw replay copies.
    (output / f"work-{result['episode_id']}.json").write_text(
        json.dumps(context["unit_events"]) + "\n"
    )
    print(
        "Analyzed",
        result["episode_id"],
        [(p["name"], p["cash"], p["gross_sales"], p["total_expenses"]) for p in result["players"]],
        flush=True,
    )

    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("replays", nargs="+", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=False)
    try:
        engine._process_market = on_market
        engine._commit_unit = on_commit
        engine._do_hire = on_hire
        engine._do_buy_land = on_land
        engine._apply_unit_action = on_unit
        engine._drop_inventories_to_shed = on_drop
        engine._decay_plants = on_decay
        engine._daily_refresh_animals = on_animals
        for path in args.replays:
            analyze(path, args.output)
    finally:
        for name, function in ORIGINAL.items():
            setattr(engine, name, function)


if __name__ == "__main__":
    main()
