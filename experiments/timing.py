"""Step 8: conditional land investment and shared daily farm tours.

Standard-library, single-file agent. See docs/STEP_8_OPTIMIZATION.md.
"""

import math
from copy import deepcopy
from functools import lru_cache
from itertools import combinations, permutations

MARKET = {
    "WHEAT": {
        "base": 25,
        "I0": 10000,
        "T": 400,
        "below_func": "sqrt",
        "below_target": 0.8,
        "above_func": "log",
        "above_target": 0.2,
    },
    "CARROT": {
        "base": 35,
        "I0": 10000,
        "T": 450,
        "below_func": "hinge",
        "below_target": 1.0,
        "above_func": "sqrt",
        "above_target": 0.7,
    },
    "TOMATO": {
        "base": 60,
        "I0": 10000,
        "T": 200,
        "below_func": "hinge",
        "below_target": 0.4,
        "above_func": "sqrt",
        "above_target": 0.6,
    },
    "STRAWBERRY": {
        "base": 120,
        "I0": 10000,
        "T": 100,
        "below_func": "sqrt",
        "below_target": 0.7,
        "above_func": "linear",
        "above_target": 1.6,
    },
    "MELON": {
        "base": 250,
        "I0": 10000,
        "T": 300,
        "below_func": "log",
        "below_target": 0.2,
        "above_func": "sq",
        "above_target": 3.6,
    },
    "EGG": {
        "base": 50,
        "I0": 10000,
        "T": 332,
        "below_func": "hinge",
        "below_target": 0.4,
        "above_func": "log",
        "above_target": 0.2,
    },
    "MILK": {
        "base": 160,
        "I0": 10000,
        "T": 122,
        "below_func": "sqrt",
        "below_target": 0.6,
        "above_func": "linear",
        "above_target": 1.6,
    },
    "WOOL": {
        "base": 200,
        "I0": 10000,
        "T": 105,
        "below_func": "log",
        "below_target": 0.2,
        "above_func": "sq",
        "above_target": 3.2,
    },
    "FERTILIZER": {
        "base": 100,
        "I0": 10000,
        "T": 200,
        "below_func": "linear",
        "below_target": 0.4,
        "above_func": "linear",
        "above_target": 0.4,
    },
}

SHOP_PRODUCTS = {
    "BAKERY": ["EGG", "WHEAT"],
    "PIZZA_SHOP": ["MILK", "TOMATO", "WHEAT"],
    "BRUNCH_SPOT": ["EGG", "WHEAT", "STRAWBERRY"],
    "YARN_STORE": ["WOOL"],
    "ICE_CREAM_SHOP": ["STRAWBERRY", "MILK", "WHEAT"],
    "PET_CAFE": ["CARROT"],
    "SMOOTHIE_SHOP": ["STRAWBERRY", "MILK"],
    "FARMERS_MARKET": ["WHEAT", "CARROT", "TOMATO", "STRAWBERRY"],
}

ANIMALS = {
    "GOOSE": {
        "cost": 300,
        "structure": "COOP",
        "first_yield_day": 4,
        "interval": 1,
        "max_held": 4,
        "product": "EGG",
    },
    "COW": {
        "cost": 400,
        "structure": "PASTURE",
        "first_yield_day": 8,
        "interval": 2,
        "max_held": 6,
        "product": "MILK",
    },
    "SHEEP": {
        "cost": 500,
        "structure": "PASTURE",
        "first_yield_day": 6,
        "interval": 3,
        "max_held": 6,
        "product": "WOOL",
    },
}

HERD_LIMIT = 10


def shape(kind, x, scale):
    x = max(0.0, x)
    if kind == "sqrt":
        return math.sqrt(x)
    if kind == "log":
        return math.log(1 + x)
    if kind == "log10":
        return math.log10(1 + x)
    if kind == "sq":
        return x * x
    if kind == "hinge" and scale > 0:
        u = x / scale
        return u + 8 * max(0, u - 1) ** 2
    return x


def price_at(crop, inventory, params):
    """Pinned engine price formula, including integer rounding and the one-coin floor."""
    p = params[crop]
    side = "below" if inventory < p["I0"] else "above"
    change = (
        p[side + "_target"]
        * p["base"]
        * shape(p[side + "_func"], abs(inventory - p["I0"]), p["T"])
        / shape(p[side + "_func"], p["T"], p["T"])
    )
    return max(1, int(round(p["base"] + (change if side == "below" else -change))))


def batch_revenue(crop, inventory, amount, params):
    """Exact isolated sale proceeds; competing orders and future demand are separate."""
    revenue = 0
    for _ in range(amount):
        price = price_at(crop, inventory, params)
        revenue += price
        inventory += int(price > 1)
    return revenue


def distance(a, b):
    return abs(a[0] - b[0]) + abs(a[1] - b[1])


def move_toward(start, target):
    if start[0] != target[0]:
        return ["EAST" if target[0] > start[0] else "WEST"]
    if start[1] != target[1]:
        return ["SOUTH" if target[1] > start[1] else "NORTH"]
    return ["PASS"]


def hire_cost(index, multiplier):
    a, b = 1, 1
    for _ in range(index):
        a, b = b, a + b
    return multiplier * a


def observed_demand(obs, cfg):
    tpd = cfg.get("turnsPerDay", 24)
    demand = {c: tpd / max(1, cfg.get("townCenterSellInterval", 24)) for c in MARKET}
    demand["FERTILIZER"] = 0
    for shop in obs["town"].get("unlocked_shops", []):
        products = SHOP_PRODUCTS.get(shop, [])
        for c in products:
            demand[c] += (
                tpd / max(1, cfg.get("townShopSellInterval", 4)) * (2 if len(products) == 1 else 1)
            )
    return demand


def animal_output(tile, day, final_day):
    """Daily saleable units under daily feeding/care/collection, without new animals."""
    data = ANIMALS[tile["animal"]]
    output = []
    pending = tile.get("pending_care_bonus", 0)
    held = tile.get("yield_units", 0)
    for date in range(day, final_day + 1):
        # Installation may occur tomorrow; there is no output before placement.
        if date < tile["placed_day"]:
            output.append((0, 0))
            continue
        if date == day:
            output.append((held, int(tile.get("fertilizer_available", False))))
        elif date == tile["placed_day"]:
            output.append((0, 0))
        else:
            age = date - tile["placed_day"]
            production = (
                age >= data["first_yield_day"]
                and (age - data["first_yield_day"]) % data["interval"] == 0
            )
            units = min(data["max_held"], 1 + pending) if production else 0
            if production:
                pending = 0
            output.append((units, 1))
            # Production uses the previous pending bonus, then yesterday's care
            # is stored. The observed tile already includes earlier care.
            if date - 1 < final_day - 1:
                pending += 1
    return output


def livestock_value(obs, cfg, params, extra=None):
    """Projected own terminal receipts less feed and daily wages; not a game oracle.

    Prices follow daily aggregate flows of visible herds. Rival future investment,
    crop replenishment, and future shop unlocks are not observable and are omitted.
    """
    day = obs["day"]
    final_day = (cfg.get("episodeSteps", 720) - 2) // cfg.get("turnsPerDay", 24)
    horizon = final_day - day + 1
    groups = [[], []]
    for side, farm in enumerate(obs["farms"]):
        groups[side] = [
            t for row in farm["tiles"] for t in row if isinstance(t, dict) and "animal" in t
        ]
    own = obs["player"]
    if extra:
        groups[own].append({"animal": extra, "placed_day": day + 1})
    flows = [[{} for _ in range(horizon)] for _ in range(2)]
    for side, group in enumerate(groups):
        for tile in group:
            product = ANIMALS[tile["animal"]]["product"]
            for offset, (units, fertilizer) in enumerate(animal_output(tile, day, final_day)):
                flow = flows[side][offset]
                flow[product] = flow.get(product, 0) + units
                flow["FERTILIZER"] = flow.get("FERTILIZER", 0) + fertilizer
    inventory = dict(obs["market"]["inventory"])
    demand = observed_demand(obs, cfg)
    receipts = feed_cost = 0.0
    daily = []
    for offset in range(horizon):
        date = day + offset
        for c in inventory:
            inventory[c] -= demand[c]
        counts = [sum(t["placed_day"] <= date for t in group) for group in groups]
        if date < final_day:
            # Buyers pay the post-buy price. Midpoint approximates simultaneous rivals.
            for index in range(counts[own]):
                feed_cost += price_at(
                    "WHEAT", inventory["WHEAT"] - counts[1 - own] / 2 - index - 1, params
                )
            inventory["WHEAT"] -= sum(counts)
        today = 0
        for c in ("EGG", "MILK", "WOOL", "FERTILIZER"):
            ours = flows[own][offset].get(c, 0)
            rival = flows[1 - own][offset].get(c, 0)
            today += batch_revenue(c, inventory[c] + rival / 2, ours, params)
            for _ in range(ours + rival):
                inventory[c] += int(price_at(c, inventory[c], params) > 1)
        receipts += today
        daily.append(today)
    wage = sum(
        hire_cost(i, cfg.get("farmHandCostMult", 1)) for i in range(max(0, len(groups[own]) - 1))
    )
    wages = wage * horizon
    return {
        "receipts": receipts,
        "feed_cost": feed_cost,
        "wages": wages,
        "operating_value": receipts - feed_cost - wages,
        "daily_receipts": daily,
    }


def investment_plan(obs, cfg, params, allowed, herd_limit):
    """Compare no purchase with one indivisible animal, retaining feed/worker liquidity."""
    farm, private = obs["farms"][obs["player"]], obs["private"]
    live = [t for row in farm["tiles"] for t in row if isinstance(t, dict) and "animal" in t]
    pending = sum(private["shed"].get(a, 0) for a in ANIMALS) + sum(
        inv.get(a, 0) for inv in private["inventories"] for a in ANIMALS
    )
    final_day = (cfg.get("episodeSteps", 720) - 2) // cfg.get("turnsPerDay", 24)
    # One pending installation is an explicit work-in-progress limit.
    if pending or len(live) >= herd_limit or obs["hour"] > 6 or final_day - obs["day"] < 4:
        return {"animal": None, "alternatives": [], "live_animals": len(live), "pending": pending}
    baseline = livestock_value(obs, cfg, params)
    alternatives = []
    count = len(live) + 1
    wages = sum(hire_cost(i, cfg.get("farmHandCostMult", 1)) for i in range(count - 1))
    # Three days at a stress feed quote plus daily wages; held wheat remains available.
    feed_quote = price_at("WHEAT", obs["market"]["inventory"]["WHEAT"] - 3 * count, params)
    reserve = 3 * (count * feed_quote + wages)
    for animal in allowed:
        forecast = livestock_value(obs, cfg, params, animal)
        cost = ANIMALS[animal]["cost"]
        margin = forecast["operating_value"] - baseline["operating_value"] - cost
        alternatives.append(
            {
                "animal": animal,
                "purchase_cost": cost,
                "reserve": reserve,
                "affordable": farm["money"] >= cost + reserve,
                "marginal_value": margin,
                "projection": forecast,
            }
        )
    feasible = [a for a in alternatives if a["affordable"] and a["marginal_value"] > 0]
    best = max(feasible, key=lambda a: a["marginal_value"], default=None)
    return {
        "animal": best["animal"] if best else None,
        "alternatives": alternatives,
        "baseline": baseline,
        "live_animals": len(live),
        "pending": pending,
    }


def station_turn(obs, configuration=None, allowed_animals=("COW", "SHEEP"), herd_limit=HERD_LIMIT):
    """Assign one short livestock route per existing worker; reserve shared stock/cash."""
    cfg = configuration or {}
    farm, private = obs["farms"][obs["player"]], obs["private"]
    tpd = cfg.get("turnsPerDay", 24)
    last_step = cfg.get("episodeSteps", 720) - 2
    remaining = last_step - obs.get("step", obs["day"] * tpd + obs["hour"]) + 1
    final_day = last_step // tpd
    terminal_day = obs["day"] == final_day
    params = {c: dict(p) for c, p in MARKET.items()}
    for c in params:
        params[c].update(cfg.get("marketParams", {}).get(c, {}))
        params[c].update(obs["market"].get("params", {}).get(c, {}))
    half = len(farm["tiles"]) // 2
    access = [(x, y) for x in (half - 1, half) for y in (half - 1, half)]
    sites = sorted(
        [(x, y) for y in range(half) for x in range(half)],
        key=lambda p: (distance(p, access[0]), p),
    )[:herd_limit]
    live = [
        p
        for p in sites
        if isinstance(farm["tiles"][p[1]][p[0]], dict) and "animal" in farm["tiles"][p[1]][p[0]]
    ]
    positions = [tuple(p) for p in [farm["farmer"], *farm["hands"]]]
    inventories = private["inventories"]
    stock = dict(private["shed"])
    room = max(0, cfg.get("shedCapacity", 100) - sum(stock.values()))
    investment = investment_plan(obs, cfg, params, allowed_animals, len(sites))
    pending_type = next(
        (a for a in ANIMALS if stock.get(a, 0) or any(inv.get(a, 0) for inv in inventories)), None
    )
    new_type = pending_type or investment["animal"]
    build_site = next((p for p in sites if p not in live), None) if new_type else None
    assignments = list(live) + ([build_site] if build_site else [])
    # Existing animal carriers retain the installation task if workforce order changes.
    carrier = next(
        (i for i, inv in enumerate(inventories) if new_type and inv.get(new_type, 0)), None
    )
    if carrier is not None and carrier < len(assignments) and build_site:
        j = len(assignments) - 1
        assignments[carrier], assignments[j] = assignments[j], assignments[carrier]
    actions = [["PASS"] for _ in positions]
    explanation = []
    for i, p in enumerate(positions):
        inv = inventories[i]
        target = assignments[i] if i < len(assignments) else None
        shed = min(access, key=lambda a: (distance(p, a), a))
        goods = [c for c in MARKET if c != "WHEAT" and inv.get(c, 0)]
        return_now = terminal_day and remaining <= distance(p, shed) + 2
        if return_now or target is None:
            if sum(inv.values()):
                actions[i] = move_toward(p, shed) if p != shed else ["DROP"]
        else:
            tile = farm["tiles"][target[1]][target[0]]
            animal = tile.get("animal") if isinstance(tile, dict) else None
            installing = target == build_site
            need_food = bool(animal and not tile["fed_today"] and not terminal_day)
            serviced = (
                animal
                and not need_food
                and (tile["cared_today"] or obs["day"] >= final_day - 1)
                and not tile["fertilizer_available"]
                and not tile["yield_units"]
            )
            if serviced and goods:
                actions[i] = move_toward(p, shed) if p != shed else ["DROP"]
            elif need_food and inv.get("WHEAT", 0) == 0:
                if p != shed:
                    actions[i] = move_toward(p, shed)
                elif stock.get("WHEAT", 0):
                    actions[i] = ["PICKUP", "WHEAT", 1]
                    stock["WHEAT"] -= 1
            elif installing and not inv.get(new_type, 0):
                if p != shed:
                    actions[i] = move_toward(p, shed)
                elif stock.get(new_type, 0):
                    actions[i] = ["PICKUP", new_type, 1]
                    stock[new_type] -= 1
            elif p != target:
                actions[i] = move_toward(p, target)
            elif installing:
                if tile is None:
                    actions[i] = ["BUILD_" + ANIMALS[new_type]["structure"]]
                elif tile.get("kind") != ANIMALS[new_type]["structure"]:
                    actions[i] = ["DIG"]
                else:
                    actions[i] = ["PLACE", new_type]
            elif need_food:
                actions[i] = ["FEED"]
            elif not tile["cared_today"] and obs["day"] < final_day - 1:
                actions[i] = ["CARE"]
            elif tile["fertilizer_available"]:
                actions[i] = ["COLLECT_FERTILIZER"]
            elif tile["yield_units"]:
                actions[i] = ["HARVEST"]
            elif goods:
                actions[i] = move_toward(p, shed) if p != shed else ["DROP"]
        # Deposit/pickup ledger is applied in the same worker order as the engine.
        if actions[i][0] == "PICKUP":
            room += actions[i][2]
        if actions[i][0] == "DROP":
            if sum(inv.values()) <= room:
                for c, n in inv.items():
                    stock[c] = stock.get(c, 0) + n
                room -= sum(inv.values())
            else:
                c = max(goods or list(inv), key=lambda c: params.get(c, {}).get("base", 0))
                amount = min(room, inv[c])
                actions[i] = ["PLACE", c, amount] if amount else ["PASS"]
                stock[c] = stock.get(c, 0) + amount
                room -= amount
        explanation.append({"worker": i, "station": target, "action": actions[i]})
    limit = max(1, cfg.get("maxMarketOrdersPerTurn", 10))
    market = [["SELL", c, n] for c, n in stock.items() if c in MARKET and c != "WHEAT" and n]
    if terminal_day and stock.get("WHEAT", 0):
        market.append(["SELL", "WHEAT", stock["WHEAT"]])
    market = market[:limit]
    cash = farm["money"]
    # Current needs plus one day of stock smooth daily pickup timing.
    unfed = sum(not farm["tiles"][y][x]["fed_today"] for x, y in live)
    food_goal = unfed + len(assignments) if not terminal_day else 0
    held_food = sum(inv.get("WHEAT", 0) for inv in inventories)
    needed = max(0, food_goal - stock.get("WHEAT", 0) - held_food)
    if needed and len(market) < limit:
        quantity = 0
        # Reserve a conservative 2x quote against simultaneous rival purchases.
        quote = 2 * price_at("WHEAT", obs["market"]["inventory"]["WHEAT"] - needed - 20, params)
        quantity = min(needed, int(cash // max(1, quote)), room)
        if quantity:
            market.append(["BUY_PRODUCT", "WHEAT", quantity])
            cash -= quantity * quote
            room -= quantity
    chosen = investment["animal"]
    if chosen and cash >= ANIMALS[chosen]["cost"] and room and len(market) < limit:
        market.append(["BUY_ANIMAL", chosen, 1])
        cash -= ANIMALS[chosen]["cost"]
        room -= 1
    target_hands = max(0, len(assignments) - 1)
    if obs["hour"] <= 6:
        for index in range(len(farm["hands"]), target_hands):
            cost = hire_cost(
                farm["hires_today"] + index - len(farm["hands"]), cfg.get("farmHandCostMult", 1)
            )
            if cost > cash or len(market) >= limit:
                break
            market.append(["HIRE"])
            cash -= cost
    return {"farmer": actions[0], "hands": actions[1:], "market": market}, {
        "step": obs.get("step"),
        "investment": investment,
        "workers": explanation,
        "feed_target": food_goal,
        "cash_reserved_after_orders": cash,
        "policy": "Marginal projected cash with feed liquidity; forecasts are not LP dual prices.",
    }


@lru_cache(maxsize=64)
def route_geometry(sites, access):
    """Shortest tours for subsets of at most four sites, from any daily spawn.

    A worst-case shed-access start and the nearest return tile bound travel.
    Workers may share tiles and walk through locked quadrants in this engine.
    Cache keys contain all geometry; caching is optional for correctness.
    """
    options = []
    for count in range(1, min(4, len(sites)) + 1):
        for members in combinations(range(len(sites)), count):
            best = min(
                (
                    max(distance(a, sites[order[0]]) for a in access)
                    + sum(distance(sites[a], sites[b]) for a, b in zip(order, order[1:]))
                    + min(distance(sites[order[-1]], a) for a in access),
                    order,
                )
                for order in permutations(members)
            )
            options.append((sum(1 << i for i in members), best[1], best[0]))
    return tuple(options)


@lru_cache(maxsize=256)
def route_cover(sites, service_steps, access, capacity, dedicated=()):
    """Exact minimum route count over the bounded route menu, then total steps.

    Each tour reserves pickup/drop actions and conservative per-site service.
    The subset DP solves a set partition, not the full dynamic farming game.
    Singleton fallback keeps every site assigned if the budget is infeasible.
    """
    if not sites:
        return (), (), True
    options = []
    for mask, order, travel in route_geometry(sites, access):
        if len(order) > 1 and any(i in dedicated for i in order):
            continue
        duration = travel + 2 + sum(service_steps[i] for i in order)
        if duration <= capacity:
            options.append((mask, order, duration))
    by_first = [[] for _ in sites]
    for option in options:
        for i in option[1]:
            by_first[i].append(option)
    full = (1 << len(sites)) - 1
    dp = {0: (0, 0, ())}
    for mask in range(1, full + 1):
        first = (mask & -mask).bit_length() - 1
        choices = []
        for group, order, duration in by_first[first]:
            if mask & group == group and mask ^ group in dp:
                n, total, routes = dp[mask ^ group]
                choices.append((n + 1, total + duration, ((order, duration), *routes)))
        if choices:
            dp[mask] = min(choices)
    if full not in dp:
        durations = tuple(
            travel + 2 + service_steps[order[0]]
            for _, order, travel in route_geometry(sites, access)
            if len(order) == 1
        )
        return tuple((p,) for p in sites), durations, False
    selected = dp[full][2]
    return (
        tuple(tuple(sites[i] for i in order) for order, _ in selected),
        tuple(duration for _, duration in selected),
        True,
    )


def plan_turn(
    obs,
    configuration=None,
    allowed_animals=("COW", "SHEEP"),
    herd_limit=HERD_LIMIT,
    force_shared=False,
):
    """Cover the existing herd with shared-worker routes; reserve shared stock/cash."""
    cfg = configuration or {}
    farm, private = obs["farms"][obs["player"]], obs["private"]
    tpd = cfg.get("turnsPerDay", 24)
    last_step = cfg.get("episodeSteps", 720) - 2
    remaining = last_step - obs.get("step", obs["day"] * tpd + obs["hour"]) + 1
    final_day = last_step // tpd
    terminal_day = obs["day"] == final_day
    params = {c: dict(p) for c, p in MARKET.items()}
    for c in params:
        params[c].update(cfg.get("marketParams", {}).get(c, {}))
        params[c].update(obs["market"].get("params", {}).get(c, {}))
    half = len(farm["tiles"]) // 2
    access = [(x, y) for x in (half - 1, half) for y in (half - 1, half)]
    sites = sorted(
        [(x, y) for y in range(half) for x in range(half)],
        key=lambda p: (distance(p, access[0]), p),
    )[:herd_limit]
    live = [
        p
        for p in sites
        if isinstance(farm["tiles"][p[1]][p[0]], dict) and "animal" in farm["tiles"][p[1]][p[0]]
    ]
    positions = [tuple(p) for p in [farm["farmer"], *farm["hands"]]]
    inventories = private["inventories"]
    stock = dict(private["shed"])
    room = max(0, cfg.get("shedCapacity", 100) - sum(stock.values()))
    investment = investment_plan(obs, cfg, params, allowed_animals, len(sites))
    pending_type = next(
        (a for a in ANIMALS if stock.get(a, 0) or any(inv.get(a, 0) for inv in inventories)), None
    )
    new_type = pending_type or investment["animal"]
    # Keep the tested setup routine and use already-paid station crews. A shared
    # tour must not postpone an installation into a later production day.
    if new_type or (not force_shared and len(positions) >= len(live)):
        action, detail = station_turn(obs, cfg, allowed_animals, herd_limit)
        detail["routing"] = {
            "mode": "stations",
            "reason": "Installation pending or a full station crew is already available.",
            "target_hands": max(0, len(live) + int(bool(new_type)) - 1),
        }
        return action, detail
    assignments = list(live)
    # Scheduled production dates remain stable after harvest. Protect those
    # sites from delayed batch delivery even if their current quote is low.
    dedicated = []
    for i, (x, y) in enumerate(assignments):
        tile = farm["tiles"][y][x]
        spec = ANIMALS[tile["animal"]]
        age = obs["day"] - tile["placed_day"] - spec["first_yield_day"]
        if age >= 0 and age % spec["interval"] == 0:
            dedicated.append(i)
    # Full-day service bounds keep zones stable as tasks are completed.
    # Three turns of headroom include next-turn hire availability and repair.
    work = tuple(2 if terminal_day else 3 if obs["day"] == final_day - 1 else 4 for _ in live)
    zones, durations, cover_feasible = route_cover(
        tuple(assignments),
        work,
        tuple(access),
        min(tpd, remaining + obs["hour"]) - 3,
        tuple(dedicated),
    )
    if not cover_feasible:
        action, detail = station_turn(obs, cfg, allowed_animals, herd_limit)
        detail["routing"] = {"mode": "stations", "reason": "Route budget is infeasible."}
        return action, detail
    actions = [["PASS"] for _ in positions]
    explanation = []
    for i, p in enumerate(positions):
        inv = inventories[i]
        zone = zones[i] if i < len(zones) else ()
        target = None
        food_count = 0
        for site in zone:
            tile = farm["tiles"][site[1]][site[0]]
            animal = tile.get("animal") if isinstance(tile, dict) else None
            need_food = bool(not terminal_day and not tile["fed_today"])
            food_count += int(need_food)
            unfinished = animal and (
                need_food
                or (not tile["cared_today"] and obs["day"] < final_day - 1)
                or tile["fertilizer_available"]
                or tile["yield_units"]
            )
            if unfinished and target is None:
                target = site
        shed = min(access, key=lambda a: (distance(p, a), a))
        goods = [c for c in MARKET if c != "WHEAT" and inv.get(c, 0)]
        return_now = terminal_day and remaining <= distance(p, shed) + 2
        if return_now or target is None:
            if sum(inv.values()):
                actions[i] = move_toward(p, shed) if p != shed else ["DROP"]
        else:
            tile = farm["tiles"][target[1]][target[0]]
            animal = tile.get("animal") if isinstance(tile, dict) else None
            need_food = bool(animal and not tile["fed_today"] and not terminal_day)
            # Load the entire route's feed at the shed. Away from the shed, use
            # carried feed before returning for a shortfall.
            load_food = not terminal_day and inv.get("WHEAT", 0) < food_count
            if load_food and (p == shed or inv.get("WHEAT", 0) == 0):
                if p != shed:
                    actions[i] = move_toward(p, shed)
                elif stock.get("WHEAT", 0):
                    amount = min(food_count - inv.get("WHEAT", 0), stock["WHEAT"])
                    actions[i] = ["PICKUP", "WHEAT", amount]
                    stock["WHEAT"] -= amount
                elif goods:
                    # Do not wait for unaffordable feed while saleable goods
                    # remain carried at the shed. Deposit to restore liquidity.
                    actions[i] = ["DROP"]
            elif p != target:
                actions[i] = move_toward(p, target)
            elif need_food:
                actions[i] = ["FEED"]
            elif not tile["cared_today"] and obs["day"] < final_day - 1:
                actions[i] = ["CARE"]
            elif tile["fertilizer_available"]:
                actions[i] = ["COLLECT_FERTILIZER"]
            elif tile["yield_units"]:
                actions[i] = ["HARVEST"]
            elif goods:
                actions[i] = move_toward(p, shed) if p != shed else ["DROP"]
        # Deposit/pickup ledger is applied in the same worker order as the engine.
        if actions[i][0] == "PICKUP":
            room += actions[i][2]
        if actions[i][0] == "DROP":
            if sum(inv.values()) <= room:
                for c, n in inv.items():
                    stock[c] = stock.get(c, 0) + n
                room -= sum(inv.values())
            else:
                c = max(goods or list(inv), key=lambda c: params.get(c, {}).get("base", 0))
                amount = min(room, inv[c])
                actions[i] = ["PLACE", c, amount] if amount else ["PASS"]
                stock[c] = stock.get(c, 0) + amount
                room -= amount
        explanation.append({"worker": i, "route": zone, "station": target, "action": actions[i]})
    limit = max(1, cfg.get("maxMarketOrdersPerTurn", 10))
    market = [["SELL", c, n] for c, n in stock.items() if c in MARKET and c != "WHEAT" and n]
    if terminal_day and stock.get("WHEAT", 0):
        market.append(["SELL", "WHEAT", stock["WHEAT"]])
    market = market[:limit]
    cash = farm["money"]
    # Current needs plus one day of stock smooth daily pickup timing.
    unfed = sum(not farm["tiles"][y][x]["fed_today"] for x, y in live)
    food_goal = unfed + len(assignments) if not terminal_day else 0
    held_food = sum(inv.get("WHEAT", 0) for inv in inventories)
    needed = max(0, food_goal - stock.get("WHEAT", 0) - held_food)
    if needed and len(market) < limit:
        quantity = 0
        # Reserve a conservative 2x quote against simultaneous rival purchases.
        quote = 2 * price_at("WHEAT", obs["market"]["inventory"]["WHEAT"] - needed - 20, params)
        quantity = min(needed, int(cash // max(1, quote)), room)
        if quantity:
            market.append(["BUY_PRODUCT", "WHEAT", quantity])
            cash -= quantity * quote
            room -= quantity
    target_hands = max(0, len(zones) - 1)
    if obs["hour"] <= 6:
        for index in range(len(farm["hands"]), target_hands):
            cost = hire_cost(
                farm["hires_today"] + index - len(farm["hands"]), cfg.get("farmHandCostMult", 1)
            )
            if cost > cash or len(market) >= limit:
                break
            market.append(["HIRE"])
            cash -= cost
    return {"farmer": actions[0], "hands": actions[1:], "market": market}, {
        "step": obs.get("step"),
        "investment": investment,
        "workers": explanation,
        "routing": {
            "mode": "shared",
            "routes": zones,
            "planned_steps": durations,
            "daily_cover_feasible": cover_feasible,
            "target_hands": target_hands,
            "protected_production_sites": [assignments[i] for i in dedicated],
            "objective": "Minimum workers covering required service; then minimum route steps.",
        },
        "feed_target": food_goal,
        "cash_reserved_after_orders": cash,
        "policy": "Marginal projected cash with feed liquidity; forecasts are not LP dual prices.",
    }


# Crop investment is bounded independently of the livestock installation slots.
CROP_LIMIT = 8
CROPS = {
    "WHEAT": {"seed": 10, "first": 2, "harvest": 4, "interval": 0, "events": 1, "units": 4},
    "MELON": {"seed": 80, "first": 10, "harvest": 10, "interval": 0, "events": 1, "units": 6},
    "STRAWBERRY": {"seed": 100, "first": 10, "harvest": 10, "interval": 2, "events": 4, "units": 1},
}


def crop_flows(tile, day, final_day):
    """Conservative dated units with survival watering, without future fertilizer."""
    crop = tile.get("crop")
    if crop not in CROPS:
        return {}
    spec = CROPS[crop]
    planted = tile["planted_day"]
    flows = {}
    if spec["interval"]:
        if tile.get("yield_units", 0):
            flows[day] = tile["yield_units"]
        for event in range(spec["events"]):
            date = planted + spec["harvest"] + event * spec["interval"]
            if day < date <= final_day or (date == day and planted > day):
                flows[date] = flows.get(date, 0) + 1
    else:
        date = max(day, planted + spec["harvest"])
        if date <= final_day:
            age = day - planted
            if crop == "WHEAT":
                future_water = max(0, 4 - max(2, age) + 1) - int(
                    tile.get("watered_today", False) and age >= 2
                )
                amount = min(6, tile.get("yield_units", 1) + future_water)
            else:
                future_water = max(0, 10 - max(6, age) + 1) - int(
                    tile.get("watered_today", False) and age >= 6
                )
                amount = min(6, tile.get("yield_units", 1) + future_water)
            flows[date] = max(0, amount)
    return flows


def crop_value(obs, cfg, params, crop, planting_day):
    """Incremental receipts of the visible crop portfolio, less seed and work allowance.

    Prices include visible competing crops and a small unknown-supply buffer.
    New wheat units have a single sale/replacement value, never both revenues.
    """
    day = obs["day"]
    final_day = (cfg.get("episodeSteps", 720) - 2) // cfg.get("turnsPerDay", 24)
    spec = CROPS[crop]
    proposed = crop_flows({"crop": crop, "planted_day": planting_day}, day, final_day)
    if not proposed:
        return {
            "crop": crop,
            "value": -spec["seed"],
            "seed_cost": spec["seed"],
            "receipts": 0,
            "dated_output": {},
        }
    flows = [{}, {}]
    for side, farm in enumerate(obs["farms"]):
        for row in farm["tiles"]:
            for tile in row:
                if isinstance(tile, dict) and tile.get("crop") == crop:
                    for date, units in crop_flows(tile, day, final_day).items():
                        flows[side][date] = flows[side].get(date, 0) + units
    own = obs["player"]
    demand = observed_demand(obs, cfg)[crop]
    totals = []
    for extra in (False, True):
        inventory = obs["market"]["inventory"][crop] + 12  # unobserved future supply scenario
        revenue = 0
        for date in range(day, final_day + 1):
            inventory -= demand
            ours = flows[own].get(date, 0) + (proposed.get(date, 0) if extra else 0)
            rival = flows[1 - own].get(date, 0)
            revenue += batch_revenue(crop, inventory + rival / 2, ours, params)
            for _ in range(ours + rival):
                inventory += int(price_at(crop, inventory, params) > 1)
        totals.append(revenue)
    receipts = totals[1] - totals[0]
    lifetime = max(proposed) - planting_day + 1
    # Heuristic charge for scarce actions; the caller also charges added daily wages.
    work = 8 + lifetime + len(proposed) * 2
    value = 0.85 * receipts - spec["seed"] - 2 * work
    return {
        "crop": crop,
        "value": value,
        "seed_cost": spec["seed"],
        "receipts": receipts,
        "work_allowance": 2 * work,
        "dated_output": proposed,
        "lifetime_days": lifetime,
    }


def crop_job(tile, day, final_day):
    """Required crop action, urgency and remaining actions before safe completion."""
    if not isinstance(tile, dict) or tile.get("crop") not in CROPS:
        return None
    crop = tile["crop"]
    age = day - tile["planted_day"]
    spec = CROPS[crop]
    units = tile.get("yield_units", 0)
    harvestable = age >= spec["first"] and units > 0
    # Harvest one-time crops after their planned bonuses; salvage near termination.
    harvest = harvestable and (spec["interval"] or age >= spec["harvest"] or day == final_day)
    if (
        harvestable
        and spec["interval"]
        and age >= spec["harvest"] + (spec["events"] - 1) * spec["interval"]
    ):
        return ("HARVEST", 280, 1)
    bonus_water = (crop == "WHEAT" and 2 <= age <= 4) or (
        crop == "MELON" and 6 <= age <= 10 and units < 6
    )
    needs_water = not tile.get("watered_today") and (
        tile.get("consecutive_unwatered", 0) >= 1
        or bonus_water
        or (crop == "STRAWBERRY" and age in (9, 11, 13, 15))
    )
    if harvest and not spec["interval"] and (not bonus_water or tile.get("watered_today")):
        return ("HARVEST", 250 + 10 * max(0, age - spec["harvest"]), 1)
    if needs_water and (day < final_day or (harvest and bonus_water)):
        return (
            "WATER",
            260
            if harvest and not spec["interval"]
            else 150
            if tile.get("consecutive_unwatered", 0) >= 1
            else 100,
            1,
        )
    if harvest:
        return ("HARVEST", 120, 1)
    # Remove exhausted ongoing crops; new plantings are admitted separately.
    if (
        spec["interval"]
        and age >= spec["harvest"] + (spec["events"] - 1) * spec["interval"]
        and not units
    ):
        return ("DIG", 10, 1)
    return None


def crop_staff_cost(obs, cfg, extra=None):
    """Dated wage estimate for committed crops; actual Fibonacci prices, approximate routes."""
    day = obs["day"]
    tpd = cfg.get("turnsPerDay", 24)
    final = (cfg.get("episodeSteps", 720) - 2) // tpd
    farm = obs["farms"][obs["player"]]
    half = len(farm["tiles"]) // 2
    animals = [t for row in farm["tiles"] for t in row if isinstance(t, dict) and "animal" in t]
    crops = [
        (t, distance((x, y), (half - 1, half - 1)))
        for y, row in enumerate(farm["tiles"])
        for x, t in enumerate(row)
        if isinstance(t, dict) and t.get("crop") in CROPS
    ]
    if extra:
        crops.append((extra, 6))  # furthest admitted plot in the default bounded area
    wages = [
        sum(hire_cost(i, cfg.get("farmHandCostMult", 1)) for i in range(n))
        for n in range(HERD_LIMIT + 2)
    ]
    total = 0
    for date in range(day, final + 1):
        active = [
            (t, d)
            for t, d in crops
            if t["planted_day"]
            <= date
            <= t["planted_day"]
            + CROPS[t["crop"]]["harvest"]
            + (CROPS[t["crop"]]["events"] - 1) * CROPS[t["crop"]]["interval"]
        ]
        producing = sum(
            date - t["placed_day"] >= ANIMALS[t["animal"]]["first_yield_day"]
            and (date - t["placed_day"] - ANIMALS[t["animal"]]["first_yield_day"])
            % ANIMALS[t["animal"]]["interval"]
            == 0
            for t in animals
        )
        # Production routes are dedicated; remaining animals can share short tours.
        livestock_workers = max(1, producing + math.ceil((len(animals) - producing) / 3))
        workers = min(
            HERD_LIMIT + 2,
            max(
                livestock_workers + math.ceil(len(active) / 4),
                math.ceil((6 * len(animals) + sum(2 * d + 3 for _, d in active)) / max(1, tpd - 4)),
            ),
        )
        total += wages[workers - 1]
    return total


def fertilizer_value(tile, obs, cfg, params):
    """Value a timely owned fertilizer unit against selling it; no free inputs."""
    day = obs["day"]
    crop = tile.get("crop")
    if (
        crop not in CROPS
        or tile.get("fertilized_until_day", -1) >= day
        or tile.get("watered_today")
    ):
        return 0
    final = (cfg.get("episodeSteps", 720) - 2) // cfg.get("turnsPerDay", 24)
    age = day - tile["planted_day"]
    gain = 0
    if crop == "WHEAT" and 2 <= age <= 4:
        days = max(0, min(4 - age + 1, final - day + 1))
        gain = max(0, min(days, 6 - tile.get("yield_units", 1) - days))
    elif crop == "STRAWBERRY" and age in (9, 11, 13, 15):
        gain = sum(day < tile["planted_day"] + a <= min(day + 3, final) for a in (10, 12, 14, 16))
    if not gain:
        return 0
    inventory = (
        obs["market"]["inventory"][crop]
        - observed_demand(obs, cfg)[crop] * min(3, final - day)
        + 12
    )
    benefit = 0.85 * batch_revenue(crop, inventory, gain, params)
    forgone = price_at("FERTILIZER", obs["market"]["inventory"]["FERTILIZER"], params)
    return benefit - forgone - 8  # pickup/application and short detour allowance


def timing_fertilizer_value(tile, obs, cfg, params):
    """Strawberries use fertilizer at night, even after today's watering.

    Require room for the next incremental berry; do not rely on a future harvest
    to make an already full plant profitable. Wheat still requires fertilizer first.
    Investment input orders retain fertilizer_value's unchanged admission rule.
    """
    if tile.get("crop") == "STRAWBERRY":
        if tile.get("yield_units", 0) >= 3:
            return 0
        return fertilizer_value({**tile, "watered_today": False}, obs, cfg, params)
    return fertilizer_value(tile, obs, cfg, params)


def early_harvest_value(tile, obs, cfg, params):
    """Compare harvestable wheat now with its remaining planned growth.

    Visible competing wheat and current town demand estimate the waiting price.
    Two coins per avoided water action is a heuristic opportunity cost, not cash
    income or an exact dual price. No future investment or wage rule is changed.
    """
    day = obs["day"]
    age = day - tile["planted_day"]
    final = (cfg.get("episodeSteps", 720) - 2) // cfg.get("turnsPerDay", 24)
    report = {"harvest_now": False}
    if tile.get("crop") != "WHEAT" or not 2 <= age < 4 or day == final:
        return report
    date = min(tile["planted_day"] + 4, final)
    now = tile.get("yield_units", 0)
    if not tile.get("watered_today"):
        now = min(6, now + (2 if tile.get("fertilized_until_day", -1) >= day else 1))
    later = now
    for water_day in range(day + 1, date + 1):
        later = min(6, later + (2 if tile.get("fertilized_until_day", -1) >= water_day else 1))
    inventory = obs["market"]["inventory"]["WHEAT"]
    future = inventory - observed_demand(obs, cfg)["WHEAT"] * (date - day)
    for farm in obs["farms"]:
        for row in farm["tiles"]:
            for other in row:
                if isinstance(other, dict) and other is not tile and other.get("crop") == "WHEAT":
                    future += sum(
                        n for d, n in crop_flows(other, day, final).items() if day <= d <= date
                    )
    immediate = batch_revenue("WHEAT", inventory, now, params)
    delayed = batch_revenue("WHEAT", future, later, params)
    action_value = 2 * (date - day)
    return {
        "harvest_now": immediate + action_value > delayed,
        "units_now_after_water": now,
        "units_at_planned_harvest": later,
        "receipts_now": immediate,
        "estimated_receipts_waiting": delayed,
        "avoided_action_allowance": action_value,
        "waiting_until_day": date,
    }


def mixed_turn(
    obs,
    configuration=None,
    crop_limit=CROP_LIMIT,
    use_fertilizer=True,
    allowed_crops=("WHEAT", "MELON", "STRAWBERRY"),
    production=False,
    opening=True,
    expansion=0,
    timing=0,
    investments=True,
):
    """Use released livestock workers for bounded crops; share all resource ledgers."""
    cfg = configuration or {}
    action, detail = plan_turn(
        obs,
        cfg,
        allowed_animals=() if production else ("COW", "SHEEP"),
        force_shared=bool(expansion),
    )
    if crop_limit == 0:
        return action, detail
    farm, private = obs["farms"][obs["player"]], obs["private"]
    day, hour = obs["day"], obs["hour"]
    tpd = cfg.get("turnsPerDay", 24)
    final = (cfg.get("episodeSteps", 720) - 2) // tpd
    remaining = min(
        tpd - hour, cfg.get("episodeSteps", 720) - 1 - obs.get("step", day * tpd + hour)
    )
    params = {c: dict(p) for c, p in MARKET.items()}
    for c in params:
        params[c].update(cfg.get("marketParams", {}).get(c, {}))
        params[c].update(obs["market"].get("params", {}).get(c, {}))
    half = len(farm["tiles"]) // 2
    access = [(x, y) for x in (half - 1, half) for y in (half - 1, half)]
    all_sites = sorted(
        [(x, y) for y in range(half) for x in range(half)],
        key=lambda p: (distance(p, access[0]), p),
    )
    # Bound travel as well as crop count; distant empty corners are not free capacity.
    fields = farm_sites(obs)[1] if expansion else all_sites[HERD_LIMIT : HERD_LIMIT + crop_limit]
    plants = [
        (p, farm["tiles"][p[1]][p[0]])
        for p in fields
        if isinstance(farm["tiles"][p[1]][p[0]], dict)
        and farm["tiles"][p[1]][p[0]].get("crop") in CROPS
    ]
    live = sum(isinstance(t, dict) and "animal" in t for row in farm["tiles"] for t in row)
    positions = [tuple(farm["farmer"]), *map(tuple, farm["hands"])]
    commands = [action["farmer"], *action["hands"]]
    # Installation is a complete place/feed/care bundle. A worker released from
    # a distant crop may reach the pasture late; preload feed at the shed so a
    # newly placed animal never requires another round trip before its first meal.
    if production and day < final:
        feed_stock = private["shed"].get("WHEAT", 0)
        for i, (p, inv) in enumerate(zip(positions, private["inventories"])):
            if any(inv.get(a, 0) for a in ANIMALS):
                shed = min(access, key=lambda a: (distance(p, a), a))
                if not inv.get("WHEAT", 0):
                    commands[i] = (
                        move_toward(p, shed)
                        if p != shed
                        else ["PICKUP", "WHEAT", 1]
                        if feed_stock
                        else ["PASS"]
                    )
                elif commands[i][0] == "PLACE" and remaining < 3:
                    commands[i] = ["PASS"]
            if commands[i][0] == "PICKUP" and commands[i][1] == "WHEAT":
                feed_stock -= commands[i][2]
    seeds = dict(private["seeds"])
    pending = sum(seeds.get(c, 0) for c in CROPS)
    limit = len(fields) if production else min(crop_limit, live)
    fertile = (
        {p: fertilizer_value(t, obs, cfg, params) for p, t in plants} if use_fertilizer else {}
    )
    fertile = {p: v for p, v in fertile.items() if v > 0}
    if timing & 1 and use_fertilizer:
        fertile = {p: timing_fertilizer_value(t, obs, cfg, params) for p, t in plants}
        fertile = {p: value for p, value in fertile.items() if value > 0}
    harvest_values = {
        p: early_harvest_value(t, obs, cfg, params)
        for p, t in plants
        if timing & 2 and t["crop"] == "WHEAT"
    }

    def dispatch_job(tile, site):
        job = crop_job(tile, day, final)
        if harvest_values.get(site, {}).get("harvest_now"):
            if not tile["watered_today"] and tile["yield_units"] < 6:
                return ("WATER", 260, 2)
            return ("HARVEST", 250, 1)
        if timing & 1 and not job and site in fertile and tile["crop"] == "STRAWBERRY":
            return ("FERTILIZE", 101, 1)
        return job

    # Release only workers whose assigned livestock jobs have all finished.
    available = []
    for work in detail["workers"]:
        i = work["worker"]
        zone = work.get("route", [work["station"]] if work.get("station") else [])
        done = True
        for p in zone:
            t = farm["tiles"][p[1]][p[0]]
            if not isinstance(t, dict) or "animal" not in t:
                done = False
                break
            if (
                (day < final and not t["fed_today"])
                or (day < final - 1 and not t["cared_today"])
                or t["fertilizer_available"]
                or t["yield_units"]
            ):
                done = False
                break
        inv = private["inventories"][i]
        if done and not any(inv.get(a, 0) for a in ANIMALS):
            available.append(i)
    # A completed placement may change the route cover immediately. Finish its
    # first feed/care with the worker already on that tile before releasing them.
    local_installations = set()
    for i, p in enumerate(positions):
        tile = farm["tiles"][p[1]][p[0]]
        if not expansion or not isinstance(tile, dict) or tile.get("placed_day") != day:
            continue
        inv = private["inventories"][i]
        op = (
            "FEED"
            if not tile["fed_today"] and inv.get("WHEAT", 0)
            else ("CARE" if tile["fed_today"] and not tile["cared_today"] else None)
        )
        if op and p not in local_installations:
            local_installations.add(p)
            for j, q in enumerate(positions):
                if j != i and q == p and commands[j][0] in ("FEED", "CARE"):
                    commands[j] = ["PASS"]
            commands[i] = [op]
            if i in available:
                available.remove(i)
    # Planting and its first watering are one committed two-action bundle.
    newborn_workers = []
    for i, p in enumerate(positions):
        tile = farm["tiles"][p[1]][p[0]]
        if (
            isinstance(tile, dict)
            and tile.get("crop") in CROPS
            and tile["planted_day"] == day
            and not tile["watered_today"]
        ):
            newborn_workers.append(i)
            if i not in available:
                available.append(i)
    # A ripe one-time crop has a hard decay deadline. A worker may handle it
    # before livestock only when a complete return-and-service allowance fits.
    urgent_assignments = {}
    urgent_pairs = []
    for site, tile in plants:
        spec = CROPS[tile["crop"]]
        job = dispatch_job(tile, site)
        deadline_age = spec["harvest"] + (spec["events"] - 1) * spec["interval"]
        dry = bool(
            expansion and tile.get("consecutive_unwatered", 0) >= 1 and job and job[0] == "WATER"
        )
        if (day - tile["planted_day"] < deadline_age and not dry) or not job:
            continue
        candidates = []
        for work in detail["workers"]:
            i = work["worker"]
            inv = private["inventories"][i]
            if (
                i in urgent_assignments
                or i in newborn_workers
                or any(inv.get(c, 0) for c in (*ANIMALS, "MILK", "WOOL", "EGG"))
            ):
                continue
            zone = work.get("route", [work["station"]] if work.get("station") else [])
            if any(
                not isinstance(farm["tiles"][p[1]][p[0]], dict)
                or "animal" not in farm["tiles"][p[1]][p[0]]
                for p in zone
            ):
                continue
            shed = min(access, key=lambda a: (distance(site, a), a))
            service = 0
            for x, y in zone:
                t = farm["tiles"][y][x]
                service += (
                    int(day < final and not t["fed_today"])
                    + int(day < final - 1 and not t["cared_today"])
                    + int(t["fertilizer_available"])
                    + int(bool(t["yield_units"]))
                )
            travel_back = distance(site, shed) + sum(
                distance(a, b) for a, b in zip((shed, *zone), zone)
            )
            if zone:
                travel_back += min(distance(zone[-1], a) for a in access)
            if expansion and service:
                continue  # complete livestock commitments before borrowing more time
            allowance = travel_back + service + 3  # deposit, possible feed pickup, final deposit
            if expansion:
                # Completed animal routes impose no return trip on crop work.
                # Retain only the real terminal delivery obligation.
                allowance = (
                    min(distance(site, a) for a in access) + 1
                    if job[0] == "HARVEST" and day == final
                    else 0
                )
            steps = 2 if job[0] == "WATER" else 1
            if distance(positions[i], site) + steps + allowance <= remaining:
                candidates.append((distance(positions[i], site), i))
        if expansion:
            urgent_pairs.extend((travel, site, i, job[0]) for travel, i in candidates)
        elif candidates:
            _, i = min(candidates)
            urgent_assignments[i] = (site, job[0])
            if i not in available:
                available.append(i)
    urgent_sites = set()
    for _, site, i, op in sorted(urgent_pairs):
        if i not in urgent_assignments and site not in urgent_sites:
            urgent_assignments[i] = (site, op)
            urgent_sites.add(site)
            if i not in available:
                available.append(i)
    reserved = set()
    crop_actions = []
    # Reserve newborn watering before another worker can claim that same tile.
    job_sites = [p for p, tile in plants if dispatch_job(tile, p)]
    available.sort(
        key=lambda i: (
            i not in newborn_workers,
            i not in urgent_assignments,
            min((distance(positions[i], p) for p in job_sites), default=0),
            i,
        )
    )
    stock = dict(private["shed"])
    harvest_room = (
        cfg.get("shedCapacity", 100)
        - sum(stock.values())
        - sum(sum(inv.values()) for inv in private["inventories"])
    )
    # Pickups already issued by livestock workers precede discretionary crop pickups.
    for i, op in enumerate(commands):
        if i not in available and op[0] == "PICKUP":
            stock[op[1]] = stock.get(op[1], 0) - op[2]
        if op[0] in ("HARVEST", "COLLECT_FERTILIZER"):
            x, y = positions[i]
            harvest_room -= farm["tiles"][y][x].get("yield_units", 0) if op[0] == "HARVEST" else 1
    for i in available:
        p = positions[i]
        inv = private["inventories"][i]
        shed = min(access, key=lambda a: (distance(p, a), a))
        if i in newborn_workers and p not in reserved:
            commands[i] = ["WATER"]
            reserved.add(p)
            crop_actions.append({"worker": i, "target": p, "job": "WATER", "action": commands[i]})
            continue
        if i in urgent_assignments:
            target, op = urgent_assignments[i]
            if (
                timing & 1
                and op == "WATER"
                and p == target
                and target in fertile
                and farm["tiles"][target[1]][target[0]]["crop"] == "STRAWBERRY"
                and inv.get("FERTILIZER", 0)
                and remaining >= 2
            ):
                op = "FERTILIZE"
            units = farm["tiles"][target[1]][target[0]]["yield_units"]
            if target not in reserved and (op != "HARVEST" or units <= harvest_room):
                reserved.add(target)
                commands[i] = move_toward(p, target) if p != target else [op]
                if p == target and op == "HARVEST":
                    harvest_room -= units
                crop_actions.append(
                    {
                        "worker": i,
                        "target": target,
                        "job": op,
                        "action": commands[i],
                        "deadline_priority": True,
                    }
                )
                continue
            # Failed crop reservation leaves the original livestock command intact.
            continue
        goods = sum(n for c, n in inv.items() if c != "FERTILIZER")
        if (goods and (not expansion or sum(inv.values()) >= 16 or harvest_room < 12)) or (
            day == final and sum(inv.values()) and remaining <= distance(p, shed) + 2
        ):
            commands[i] = move_toward(p, shed) if p != shed else ["DROP"]
            continue
        choices = []
        for site, tile in plants:
            if site in reserved:
                continue
            job = dispatch_job(tile, site)
            if not job:
                continue
            op, urgency, steps = job
            if op == "HARVEST" and tile.get("yield_units", 0) > harvest_room:
                continue
            travel = distance(p, site)
            return_steps = (
                min(distance(site, a) for a in access) + 1
                if op == "HARVEST" and day == final
                else 0
            )
            if travel + steps + return_steps > remaining:
                continue
            if site in fertile and op in ("WATER", "FERTILIZE"):
                if inv.get("FERTILIZER", 0):
                    if travel + steps + return_steps + 1 <= remaining:
                        op = "FERTILIZE"
                        urgency += 1
                elif (
                    stock.get("FERTILIZER", 0)
                    and not (tile["crop"] == "WHEAT" and day - tile["planted_day"] >= 4)
                    and distance(p, shed) + 1 + min(distance(a, site) for a in access) + steps + 2
                    <= remaining
                ):
                    op = "LOAD_FERTILIZER"
                    travel = distance(p, shed) + 1 + distance(shed, site)
                    urgency += 1
                elif op == "FERTILIZE":
                    continue
            choices.append((urgency - 4 * travel, -travel, site, op))
        # A purchased seed reserves one planting; first-day watering must fit too.
        seed = next((c for c in CROPS if seeds.get(c, 0)), None)
        if seed and len(plants) < limit and day + CROPS[seed]["first"] <= final:
            planting_fields = fields
            if expansion:
                # Match investment geometry: seeds occupy the nearest free plots.
                planting_fields = [
                    q
                    for q in fields
                    if farm["tiles"][q[1]][q[0]] is None
                    or isinstance(farm["tiles"][q[1]][q[0]], dict)
                    and farm["tiles"][q[1]][q[0]].get("kind") == "WEED"
                ][:pending]
            for site in planting_fields:
                tile = farm["tiles"][site[1]][site[0]]
                if site in reserved or (
                    tile is not None and not (isinstance(tile, dict) and tile.get("kind") == "WEED")
                ):
                    continue
                steps = 2 + int(tile is not None)
                travel = distance(p, site)
                if travel + steps + 2 <= remaining:
                    choices.append(
                        (35 - 4 * travel, -travel, site, "DIG" if tile is not None else "PLANT")
                    )
        if choices:
            _, _, target, op = max(choices)
            reserved.add(target)
            if op == "LOAD_FERTILIZER":
                commands[i] = (
                    move_toward(p, shed)
                    if p != shed
                    else ["PICKUP", "FERTILIZER", min(3 if expansion else 1, stock["FERTILIZER"])]
                )
                if p == shed:
                    stock["FERTILIZER"] -= commands[i][2]
            elif p != target:
                commands[i] = move_toward(p, target)
            elif op == "PLANT":
                commands[i] = ["PLANT", seed]
                seeds[seed] -= 1
            else:
                commands[i] = [op]
                if op == "HARVEST":
                    harvest_room -= farm["tiles"][target[1]][target[0]]["yield_units"]
            crop_actions.append({"worker": i, "target": target, "job": op, "action": commands[i]})
        elif sum(inv.values()):
            commands[i] = move_toward(p, shed) if p != shed else ["DROP"]
        else:
            commands[i] = ["PASS"]
    # Replay final unit commands into a shared shed ledger, in actual worker order.
    stock = dict(private["shed"])
    room = max(0, cfg.get("shedCapacity", 100) - sum(stock.values()))
    for i, op in enumerate(commands):
        inv = private["inventories"][i]
        if op[0] == "PICKUP":
            amount = min(op[2], stock.get(op[1], 0))
            commands[i] = ["PICKUP", op[1], amount] if amount else ["PASS"]
            stock[op[1]] = stock.get(op[1], 0) - amount
            room += amount
        elif op[0] == "DROP":
            if sum(inv.values()) <= room:
                for c, n in inv.items():
                    stock[c] = stock.get(c, 0) + n
                room -= sum(inv.values())
            else:
                item = max(inv, key=lambda c: params.get(c, {}).get("base", 0))
                n = min(room, inv[item])
                commands[i] = ["PLACE", item, n] if n else ["PASS"]
                stock[item] = stock.get(item, 0) + n
                room -= n
        elif op[0] == "PLACE" and len(op) > 2 and op[1] in MARKET:
            n = min(op[2], inv.get(op[1], 0), room)
            commands[i] = ["PLACE", op[1], n] if n else ["PASS"]
            stock[op[1]] = stock.get(op[1], 0) + n
            room -= n
    max_orders = cfg.get("maxMarketOrdersPerTurn", 10)
    carried_feed = sum(inv.get("WHEAT", 0) for inv in private["inventories"])
    # Count feed after same-turn deposits/pickups, avoiding double-counting wheat.
    for i, op in enumerate(commands):
        if op[0] == "DROP":
            carried_feed -= private["inventories"][i].get("WHEAT", 0)
        elif op[0] == "PLACE" and len(op) > 2 and op[1] == "WHEAT":
            carried_feed -= op[2]
        elif op[0] == "PICKUP" and op[1] == "WHEAT":
            carried_feed += op[2]
    wheat_keep = max(0, detail["feed_target"] - carried_feed) if day < final else 0
    fert_keep = (
        max(0, len(fertile) - sum(inv.get("FERTILIZER", 0) for inv in private["inventories"]))
        if day < final
        else 0
    )
    market = []
    for c in MARKET:
        keep = wheat_keep if c == "WHEAT" else fert_keep if c == "FERTILIZER" else 0
        n = max(0, stock.get(c, 0) - keep)
        if n and len(market) < max_orders:
            market.append(["SELL", c, n])
    cash = farm["money"]
    # Protect prior livestock spending before admitting new crop commitments.
    for order in action["market"]:
        if order[0] == "SELL":
            continue
        if len(market) >= max_orders:
            break
        if order[0] == "BUY_PRODUCT":
            needed = max(0, detail["feed_target"] - stock.get("WHEAT", 0) - carried_feed)
            n = min(order[2], needed, room)
            quote = 2 * price_at("WHEAT", obs["market"]["inventory"]["WHEAT"] - needed - 20, params)
            n = min(n, int(cash // max(1, quote)))
            if n:
                market.append(["BUY_PRODUCT", "WHEAT", n])
                cash -= n * quote
                room -= n
        elif order[0] == "BUY_ANIMAL":
            cost = ANIMALS[order[1]]["cost"] * order[2]
            if cash >= cost and room >= order[2]:
                market.append(order)
                cash -= cost
                room -= order[2]
        elif order[0] == "HIRE":
            count = sum(o[0] == "HIRE" for o in market)
            cost = hire_cost(farm["hires_today"] + count, cfg.get("farmHandCostMult", 1))
            if cash >= cost:
                market.append(order)
                cash -= cost
    # Bound whole-day work, including individual crop trips, before sizing hires.
    crop_work = sum(2 * min(distance(p, a) for a in access) + 3 for p, _ in plants)
    worker_target = max(1, math.ceil((6 * live + crop_work + 14 * pending) / max(1, tpd - 4)))
    # Some crop work must start before a busy livestock crew returns. Aggregate
    # spare hours alone cannot certify completion of watering/harvest deadlines.
    crop_jobs = sum(bool(crop_job(tile, day, final)) for _, tile in plants)
    livestock_workers = detail.get("routing", {}).get("target_hands", max(0, live - 1)) + 1
    worker_target = max(worker_target, livestock_workers + math.ceil(crop_jobs / 4))
    worker_target = min(HERD_LIMIT + (3 if expansion else 2), worker_target)
    extra_hires = 0
    if (plants or (production and pending)) and hour <= 6:
        while (
            len(positions) + sum(o[0] == "HIRE" for o in market) < worker_target
            and len(market) < max_orders
        ):
            count = sum(o[0] == "HIRE" for o in market)
            cost = hire_cost(farm["hires_today"] + count, cfg.get("farmHandCostMult", 1))
            if cash < cost:
                break
            market.append(["HIRE"])
            cash -= cost
            extra_hires += 1
    alternatives = []
    chosen = None
    reserve = 3 * live * price_at("WHEAT", obs["market"]["inventory"]["WHEAT"] - 3 * live, params)
    reserve += 3 * sum(
        hire_cost(i, cfg.get("farmHandCostMult", 1)) for i in range(worker_target - 1)
    )
    if (
        not production
        and day >= 2
        and hour <= 12
        and available
        and not pending
        and len(plants) < limit
        and len(market) < max_orders
    ):
        alternatives = [crop_value(obs, cfg, params, c, day + 1) for c in allowed_crops]
        baseline_wages = crop_staff_cost(obs, cfg)
        for option in alternatives:
            option["added_wages"] = max(
                0,
                crop_staff_cost(obs, cfg, {"crop": option["crop"], "planted_day": day + 1})
                - baseline_wages,
            )
            option["value"] -= option["added_wages"]
        feasible = [a for a in alternatives if a["value"] > 0 and cash >= a["seed_cost"] + reserve]
        if feasible:
            chosen = max(feasible, key=lambda a: (a["value"] / a["lifetime_days"], a["crop"]))
            market.append(["BUY_SEED", chosen["crop"], 1])
            cash -= chosen["seed_cost"]
    detail["mixed"] = {
        "active_crops": len(plants),
        "crop_limit": limit,
        "released_workers": available,
        "crop_actions": crop_actions,
        "fertilizer_values": {str(p): v for p, v in fertile.items()},
        "retained_wheat": wheat_keep,
        "retained_fertilizer": fert_keep,
        "seed_alternatives": alternatives,
        "chosen_crop": chosen,
        "cash_reserve": reserve,
        "worker_target": worker_target,
        "crop_work_bound": crop_work,
        "incremental_hires": extra_hires,
        "early_harvest_values": {str(p): v for p, v in harvest_values.items()},
    }
    if not investments:
        return {"farmer": commands[0], "hands": commands[1:], "market": market}, detail
    if expansion and day >= 2:
        market, report = expansion_investment(obs, cfg, params, commands, market, expansion)
        detail["expansion"] = report
    elif production:
        market, report = production_orders(
            obs,
            cfg,
            params,
            market,
            cash,
            room,
            stock,
            len(plants),
            min(limit, 12) if expansion else limit,
            bool(available),
            use_fertilizer,
            opening,
            commands,
        )
        detail["production"] = report
    return {"farmer": commands[0], "hands": commands[1:], "market": market}, detail


def crop_column(crop, planted, final, fertilized=False, tile=None, today=0):
    """Dated base/fertilized growth template; inputs precede watered production."""
    spec = CROPS[crop]
    tile = tile or {
        "crop": crop,
        "planted_day": planted,
        "yield_units": 1 if crop != "STRAWBERRY" else 0,
    }
    outputs, applications, work = {}, [], {}
    age = today - planted
    expiry = tile.get("fertilized_until_day", -1)
    if crop == "STRAWBERRY":
        if tile.get("yield_units", 0):
            outputs[today] = tile["yield_units"]
        for a in (10, 12, 14, 16):
            date = planted + a
            if not today < date <= final:
                continue
            water_day = date - 1
            if fertilized and expiry < water_day:
                applications.append(water_day)
                expiry = water_day + 2
            outputs[date] = 2 if expiry >= water_day else 1
    else:
        end = max(today, planted + spec["harvest"])
        if end > final:
            return None
        quantity = tile.get("yield_units", 1)
        for a in range(max(2 if crop == "WHEAT" else 6, age), spec["harvest"] + 1):
            date = planted + a
            if date == today and tile.get("watered_today"):
                continue
            if fertilized and crop == "WHEAT" and expiry < date and not applications:
                applications.append(date)
                expiry = date + 2
            quantity = min(6, quantity + (2 if expiry >= date else 1))
        outputs[end] = quantity
    if not outputs:
        return None
    end = max(outputs)
    for date in range(max(today, planted), end + 1):
        # Individual trips are a conservative capacity estimate, not optimal routes.
        work[date] = 15  # furthest admitted plot: six moves each way plus three operations
    return {
        "crop": crop,
        "planted_day": planted,
        "end": end,
        "outputs": outputs,
        "fertilizer": applications,
        "work": work,
        "fertilized": fertilized,
    }


def production_projection(
    obs, cfg, params, additions=(), cash=None, fertilized=True, stress=0, routed=False, land_cost=0
):
    """Cash/inventory conservation for a visible portfolio plus dated integer columns.

    Future prices and schedules are estimates. Crops have no guaranteed future
    purchases; only the first action of a proposed sequence is executed.
    """
    day, own = obs["day"], obs["player"]
    tpd = cfg.get("turnsPerDay", 24)
    final = (cfg.get("episodeSteps", 720) - 2) // tpd
    animals, crops = [[], []], [[], []]
    for side, farm in enumerate(obs["farms"]):
        for row in farm["tiles"]:
            for tile in row:
                if not isinstance(tile, dict):
                    continue
                if "animal" in tile:
                    animals[side].append(tile)
                elif tile.get("crop") in CROPS:
                    column = crop_column(
                        tile["crop"],
                        tile["planted_day"],
                        final,
                        fertilized and side == own,
                        tile,
                        day,
                    )
                    if column:
                        crops[side].append(column)
    costs = {day: land_cost} if land_cost else {}
    for item in additions:
        date = item.get("buy_day", day)
        if "animal" in item:
            animals[own].append({"animal": item["animal"], "placed_day": item["placed_day"]})
            cost = ANIMALS[item["animal"]]["cost"]
        else:
            column = crop_column(
                item["crop"], item["planted_day"], final, item.get("fertilized", False), today=day
            )
            if column is None:
                return {"value": -1e9, "min_cash": -1e9, "daily": []}
            crops[own].append(column)
            cost = CROPS[item["crop"]]["seed"]
        costs[date] = costs.get(date, 0) + cost
    # Include already purchased animals in transit; no acquisition cost is repeated.
    private = obs["private"]
    for animal in ANIMALS:
        count = private["shed"].get(animal, 0) + sum(
            i.get(animal, 0) for i in private["inventories"]
        )
        animals[own].extend({"animal": animal, "placed_day": day + 1} for _ in range(count))
    flows = [{d: {} for d in range(day, final + 1)} for _ in range(2)]
    for side in (0, 1):
        for tile in animals[side]:
            product = ANIMALS[tile["animal"]]["product"]
            for i, (units, fertilizer) in enumerate(animal_output(tile, day, final)):
                f = flows[side][day + i]
                f[product] = f.get(product, 0) + units
                f["FERTILIZER"] = f.get("FERTILIZER", 0) + fertilizer
        for col in crops[side]:
            for date, units in col["outputs"].items():
                f = flows[side][date]
                f[col["crop"]] = f.get(col["crop"], 0) + units
    if stress and day + stress <= final:
        # Unknown additional early/delayed rival production, not a replay oracle.
        flows[1 - own][day + stress]["MELON"] = flows[1 - own][day + stress].get("MELON", 0) + 48
    inventory = dict(obs["market"]["inventory"])
    stock = {
        c: private["shed"].get(c, 0) + sum(i.get(c, 0) for i in private["inventories"])
        for c in MARKET
    }
    demand = observed_demand(obs, cfg)
    balance = obs["farms"][own]["money"] if cash is None else cash
    start = balance
    minimum = balance
    total_receipts = total_feed = total_fertilizer = total_wages = 0
    daily = []
    for date in range(day, final + 1):
        for c in inventory:
            inventory[c] -= demand[c] * (1 - obs["hour"] / tpd if date == day else 1)
        counts = [sum(t["placed_day"] <= date for t in group) for group in animals]
        active = [c for c in crops[own] if c["planted_day"] <= date <= c["end"]]
        producing = sum(
            date - t["placed_day"] >= ANIMALS[t["animal"]]["first_yield_day"]
            and (date - t["placed_day"] - ANIMALS[t["animal"]]["first_yield_day"])
            % ANIMALS[t["animal"]]["interval"]
            == 0
            for t in animals[own]
        )
        livestock_workers = max(1, producing + math.ceil((counts[own] - producing) / 3))
        workers = min(
            12,
            max(
                livestock_workers + math.ceil(len(active) / 4),
                math.ceil(
                    (6 * counts[own] + sum(c["work"][date] for c in active)) / max(1, tpd - 4)
                ),
            ),
        )
        if routed:
            nodes = []
            for y, row in enumerate(obs["farms"][own]["tiles"]):
                for x, tile in enumerate(row):
                    if not isinstance(tile, dict):
                        continue
                    if "animal" in tile:
                        nodes.append(((x, y), farm_service(tile, date, final)))
                    elif tile.get("crop") in CROPS:
                        spec = CROPS[tile["crop"]]
                        end = tile["planted_day"] + spec["harvest"]
                        end += (spec["events"] - 1) * spec["interval"]
                        if date <= end:
                            nodes.append(((x, y), farm_service(tile, date, final)))
            for item in additions:
                if "animal" in item and date >= item["placed_day"]:
                    nodes.append((tuple(item["site"]), 6 if date == item["placed_day"] else 4))
                elif "crop" in item:
                    spec = CROPS[item["crop"]]
                    end = item["planted_day"] + spec["harvest"]
                    end += (spec["events"] - 1) * spec["interval"]
                    if item["planted_day"] <= date <= end:
                        nodes.append((tuple(item["site"]), farm_service(item, date, final)))
            tours, durations, feasible = farm_tours(
                tuple(sorted(nodes)), tuple(shed_access(obs)), tpd - 3
            )
            if not feasible or len(tours) > 12:
                return {"value": -1e9, "min_cash": -1e9, "daily": [], "route_feasible": False}
            workers = max(1, len(tours))
        wage = sum(hire_cost(i, cfg.get("farmHandCostMult", 1)) for i in range(workers - 1))
        if date == day:
            paid = sum(
                hire_cost(i, cfg.get("farmHandCostMult", 1))
                for i in range(obs["farms"][own]["hires_today"])
            )
            wage = max(0, wage - paid)
        spending = costs.get(date, 0) + wage
        total_wages += wage
        # Protect input cash before today's forecast delivery. Internal wheat and
        # fertilizer are consumed once; only the remainder becomes sales receipts.
        need_food = counts[own] if date < final else 0
        if date == day:
            need_food = (
                sum(t["placed_day"] <= date and not t.get("fed_today", False) for t in animals[own])
                if date < final
                else 0
            )
        need_fert = sum(date in c["fertilizer"] for c in crops[own])
        # Rival private feed stocks are hidden. Approximate net daily purchases
        # from its visible herd and wheat output; never read the other private state.
        if date < final:
            inventory["WHEAT"] -= max(0, counts[1 - own] - flows[1 - own][date].get("WHEAT", 0))
        for product, needed in (("WHEAT", need_food), ("FERTILIZER", need_fert)):
            used = min(stock[product], needed)
            stock[product] -= used
            missing = needed - used
            cost = 0
            for _ in range(missing):
                inventory[product] -= 1
                cost += price_at(product, inventory[product], params)
            spending += cost
            if product == "WHEAT":
                total_feed += cost
            else:
                total_fertilizer += cost
        balance -= spending
        minimum = min(minimum, balance)
        receipts = 0
        for c in MARKET:
            stock[c] += flows[own][date].get(c, 0)
            rival = flows[1 - own][date].get(c, 0)
            # Next-day input stock avoids pretending that tomorrow's fertilizer
            # collection can finance an earlier application that same morning.
            keep = (
                counts[own]
                if c == "WHEAT" and date < final
                else sum(date + 1 in x["fertilizer"] for x in crops[own])
                if c == "FERTILIZER" and date < final
                else 0
            )
            units = max(0, stock[c] - keep)
            receipts += batch_revenue(c, inventory[c] + rival / 2, units, params)
            stock[c] -= units
            for _ in range(units + rival):
                inventory[c] += int(price_at(c, inventory[c], params) > 1)
        # Haircut reflects uncertain deliveries/prices, and applies to cash too.
        credited = 0.8 * receipts
        balance += credited
        total_receipts += credited
        daily.append(
            {
                "day": date,
                "spending_before_receipts": spending,
                "credited_receipts": credited,
                "closing_cash": balance,
                "workers": workers,
                "fertilizer_inputs": need_fert,
            }
        )
    return {
        "value": balance - start,
        "min_cash": minimum,
        "daily": daily,
        "receipts": total_receipts,
        "feed_cost": total_feed,
        "fertilizer_purchase_cost": total_fertilizer,
        "wages": total_wages,
        "investment_cost": sum(costs.values()),
    }


def opening_portfolios(obs, cfg, params, crop_limit=12, fertilized=True):
    """Enumerate joint integer opening choices with dated working-capital checks."""
    alternatives = []
    for cows, sheep in ((0, 0), (0, 2), (1, 1), (0, 4), (2, 2)):
        for melons in (0, 4, 8, 12):
            if melons > crop_limit:
                continue
            additions = [
                dict(animal=a, placed_day=1)
                for a, n in (("COW", cows), ("SHEEP", sheep))
                for _ in range(n)
            ]
            additions += [dict(crop="MELON", planted_day=0) for _ in range(melons)]
            forecasts = [
                production_projection(obs, cfg, params, additions, fertilized=fertilized, stress=s)
                for s in (10, 16)
            ]
            value = sum(f["value"] for f in forecasts) / len(forecasts)
            minimum = min(f["min_cash"] for f in forecasts)
            alternatives.append(
                {
                    "cows": cows,
                    "sheep": sheep,
                    "melons": melons,
                    "value": value,
                    "min_cash": minimum,
                    "affordable": minimum >= 150,
                    "investment_cost": forecasts[0].get("investment_cost", 0),
                    "cash_schedule": forecasts[0]["daily"],
                }
            )
    best = max((x for x in alternatives if x["affordable"]), key=lambda x: x["value"], default=None)
    return best, alternatives


def production_orders(
    obs,
    cfg,
    params,
    market,
    cash,
    room,
    stock,
    active,
    limit,
    available,
    fertilized,
    opening,
    commands,
):
    """Choose one current investment, or the joint opening; reserve complete inputs."""
    day, hour = obs["day"], obs["hour"]
    final = (cfg.get("episodeSteps", 720) - 2) // cfg.get("turnsPerDay", 24)
    private, farm = obs["private"], obs["farms"][obs["player"]]
    max_orders = cfg.get("maxMarketOrdersPerTurn", 10)
    report = {"opening": None, "alternatives": [], "chosen": None}
    if day == 0 and hour == 0 and opening:
        chosen, options = opening_portfolios(obs, cfg, params, limit, fertilized)
        report.update(opening=chosen, alternatives=options)
        if chosen:
            if chosen["melons"]:
                market.append(["BUY_SEED", "MELON", chosen["melons"]])
            for animal, count in (("COW", chosen["cows"]), ("SHEEP", chosen["sheep"])):
                if count:
                    market.append(["BUY_ANIMAL", animal, count])
        return market[:max_orders], report
    if hour > 6 or day == 0:
        return market, report
    pending_crops = sum(private["seeds"].values())
    pending_animals = sum(
        private["shed"].get(a, 0) + sum(i.get(a, 0) for i in private["inventories"])
        for a in ANIMALS
    )
    # Existing input shortages outrank speculative new lots.
    needed_fert = (
        sum(
            fertilizer_value(t, obs, cfg, params) > 0
            for row in farm["tiles"]
            for t in row
            if isinstance(t, dict) and t.get("crop") in CROPS
        )
        if fertilized
        else 0
    )
    held_fert = stock.get("FERTILIZER", 0) + sum(
        i.get("FERTILIZER", 0) for i in private["inventories"]
    )
    if needed_fert > held_fert and room and len(market) < max_orders:
        n = min(needed_fert - held_fert, room)
        cost = (
            2
            * price_at("FERTILIZER", obs["market"]["inventory"]["FERTILIZER"] - n - 20, params)
            * n
        )
        if cash >= cost + 150:
            market.append(["BUY_PRODUCT", "FERTILIZER", n])
            cash -= cost
            room -= n
    if pending_animals or pending_crops or len(market) >= max_orders:
        return market, report
    planned = planning_snapshot(obs, cfg, commands, market, params)
    baseline = production_projection(planned, cfg, params, fertilized=fertilized)
    report["baseline"] = baseline
    options = []
    live = sum(isinstance(t, dict) and "animal" in t for row in farm["tiles"] for t in row)
    if live < HERD_LIMIT and room:
        for animal in ("COW", "SHEEP"):
            options.append(([["BUY_ANIMAL", animal, 1]], [dict(animal=animal, placed_day=day + 1)]))
    if available and active < limit:
        for crop in CROPS:
            for use_fert in (False, True) if fertilized and crop != "MELON" else (False,):
                col = crop_column(crop, day + 1, final, use_fert, today=day)
                if not col:
                    continue
                first = dict(crop=crop, planted_day=day + 1, fertilized=use_fert)
                options.append(([["BUY_SEED", crop, 1]], [first]))
                # Two-stage alternatives share one plot. Only stage one is bought
                # now; stage two is re-evaluated after the observed harvest.
                for follow in ("WHEAT", "MELON", "STRAWBERRY"):
                    planted = col["end"] + 1
                    following = crop_column(follow, planted, final, fertilized, today=day)
                    if following:
                        options.append(
                            (
                                [["BUY_SEED", crop, 1]],
                                [
                                    first,
                                    dict(
                                        crop=follow,
                                        planted_day=planted,
                                        buy_day=planted,
                                        fertilized=fertilized,
                                    ),
                                ],
                            )
                        )
    feasible = []
    for orders, columns in options:
        projection = production_projection(planned, cfg, params, columns, fertilized=fertilized)
        current_cost = sum(
            ANIMALS[c["animal"]]["cost"] if "animal" in c else CROPS[c["crop"]]["seed"]
            for c in columns
            if c.get("buy_day", day) == day
        )
        margin = projection["value"] - baseline["value"]
        option = {
            "orders": orders,
            "columns": columns,
            "marginal_value": margin,
            "min_cash": projection["min_cash"],
            "cost_now": current_cost,
            "affordable": cash >= current_cost and projection["min_cash"] >= 150,
            "projection": projection,
        }
        report["alternatives"].append(option)
        if margin > 0 and option["affordable"]:
            feasible.append(option)
    if feasible:
        chosen = max(feasible, key=lambda x: x["marginal_value"])
        market.extend(chosen["orders"])
        report["chosen"] = chosen
    return market[:max_orders], report


def planning_snapshot(obs, cfg, commands, orders, params):
    """Book this policy's unit operations before its market orders, once each.

    Used only after pending seeds/animals have cleared. This is a local accounting
    projection, not a substitute simulator: movement does not alter the ledger,
    and unknown simultaneous rival transactions are excluded from current quotes.
    """
    result = deepcopy(obs)
    farm, private = result["farms"][obs["player"]], result["private"]
    day = obs["day"]
    positions = [farm["farmer"], *farm["hands"]]
    shed = private["shed"]
    for (x, y), inv, op in zip(positions, private["inventories"], commands):
        tile = farm["tiles"][y][x]
        if op[0] == "FEED":
            inv["WHEAT"] -= 1
            tile["fed_today"] = True
        elif op[0] == "FERTILIZE":
            inv["FERTILIZER"] -= 1
            tile["fertilized_until_day"] = day + 2
        elif op[0] == "COLLECT_FERTILIZER":
            tile["fertilizer_available"] = False
            inv["FERTILIZER"] = inv.get("FERTILIZER", 0) + 1
        elif op[0] == "WATER":
            if not tile["watered_today"] and tile["crop"] != "STRAWBERRY":
                age = day - tile["planted_day"]
                end = CROPS[tile["crop"]]["harvest"]
                if (end + 1) // 2 <= age <= end:
                    tile["yield_units"] = min(
                        6, tile["yield_units"] + (2 if tile["fertilized_until_day"] >= day else 1)
                    )
            tile["watered_today"] = True
        elif op[0] == "HARVEST":
            product = tile.get("crop") or ANIMALS[tile["animal"]]["product"]
            inv[product] = inv.get(product, 0) + tile["yield_units"]
            tile["yield_units"] = 0
            if tile.get("crop") in ("WHEAT", "MELON"):
                farm["tiles"][y][x] = None
        elif op[0] == "DIG":
            farm["tiles"][y][x] = None
        elif op[0] == "PICKUP":
            shed[op[1]] -= op[2]
            inv[op[1]] = inv.get(op[1], 0) + op[2]
        elif op[0] == "DROP":
            for c, n in inv.items():
                shed[c] = shed.get(c, 0) + n
            inv.clear()
        elif op[0] == "PLACE" and op[1] in MARKET:
            inv[op[1]] -= op[2]
            shed[op[1]] = shed.get(op[1], 0) + op[2]
    inventory = result["market"]["inventory"]
    for op in orders:
        if op[0] == "HIRE":
            farm["money"] -= hire_cost(farm["hires_today"], cfg.get("farmHandCostMult", 1))
            farm["hires_today"] += 1
        elif op[0] == "SELL":
            for _ in range(op[2]):
                price = price_at(op[1], inventory[op[1]], params)
                farm["money"] += price
                inventory[op[1]] += int(price > 1)
                shed[op[1]] -= 1
        elif op[0] == "BUY_PRODUCT":
            for _ in range(op[2]):
                inventory[op[1]] -= 1
                farm["money"] -= price_at(op[1], inventory[op[1]], params)
                shed[op[1]] = shed.get(op[1], 0) + 1
    return result


def bundle_turn(obs, configuration=None, crop_limit=12, use_fertilizer=True, opening=True):
    return mixed_turn(
        obs,
        configuration,
        crop_limit=crop_limit,
        use_fertilizer=use_fertilizer,
        production=True,
        opening=opening,
    )


def shed_access(obs):
    half = len(obs["farms"][obs["player"]]["tiles"]) // 2
    return tuple((x, y) for x in (half - 1, half) for y in (half - 1, half))


@lru_cache(maxsize=2048)
def farm_tours(nodes, access, capacity):
    """Deterministic cheapest insertion, with a complete worst-start daily bound.

    Three extra actions reserve feed pickup, fertilizer/animal pickup, and deposit.
    Service allowances depend on crop age and scheduled animal production.
    Tours have no worker collisions: multiple units can occupy the same cell.
    """
    services = dict(nodes)

    def duration(route):
        return (
            max(distance(a, route[0]) for a in access)
            + sum(distance(a, b) for a, b in zip(route, route[1:]))
            + min(distance(route[-1], a) for a in access)
            + sum(services[p] for p in route)
            + 3
        )

    routes = []
    for site in sorted(services, key=lambda p: (-min(distance(p, a) for a in access), p)):
        choices = []
        for i, route in enumerate(routes):
            before = duration(route)
            for at in range(len(route) + 1):
                proposed = (*route[:at], site, *route[at:])
                length = duration(proposed)
                if length <= capacity:
                    choices.append((length - before, length, i, proposed))
        if choices:
            _, _, i, proposed = min(choices)
            routes[i] = proposed
        else:
            routes.append((site,))
    routes = tuple(sorted(routes))
    durations = tuple(duration(route) for route in routes)
    return routes, durations, all(n <= capacity for n in durations)


def farm_sites(obs, extra_land=False):
    """Keep the ten tested animal sites; all other owned cells can grow crops."""
    farm = obs["farms"][obs["player"]]
    size, access = len(farm["tiles"]), shed_access(obs)
    half = size // 2
    animal = sorted(
        [(x, y) for y in range(half) for x in range(half)],
        key=lambda p: (distance(p, access[0]), p),
    )[:HERD_LIMIT]
    owned = len(farm["unlocked_quadrants"])
    next_quadrant = ("NW", "NE", "SW", "SE")[owned] if owned < 4 else None
    fields = []
    for y, row in enumerate(farm["tiles"]):
        for x, tile in enumerate(row):
            quadrant = ("N" if y < half else "S") + ("W" if x < half else "E")
            if (x, y) not in animal and (
                tile != "LOCKED" or extra_land and quadrant == next_quadrant
            ):
                fields.append((x, y))
    fields.sort(key=lambda p: (min(distance(p, a) for a in access), p))
    return animal, fields


def farm_service(tile, day, final):
    """Conservative operations for one date; geometry and inputs are charged separately."""
    if "install" in tile:
        return 6
    if "plant" in tile:
        return 3
    if "animal" in tile:
        spec = ANIMALS[tile["animal"]]
        age = day - tile["placed_day"] - spec["first_yield_day"]
        return 3 + int(age >= 0 and age % spec["interval"] == 0)
    age = day - tile["planted_day"]
    if age <= 0:
        return 3
    if tile["crop"] == "STRAWBERRY":
        return 2 if age in (9, 11, 13, 15) or age >= 16 else 1
    return (
        2
        if tile["crop"] == "WHEAT" and age in (2, 4) or tile["crop"] == "MELON" and age >= 10
        else 1
    )


def expansion_investment(obs, cfg, params, commands, market, max_land=3):
    """Compare finite batches on owned land with batches funding the next quadrant."""
    report = {"alternatives": [], "chosen": None}
    day, hour = obs["day"], obs["hour"]
    private, farm = obs["private"], obs["farms"][obs["player"]]
    if (
        hour > 6
        or sum(private["seeds"].values())
        or any(
            private["shed"].get(a, 0) or any(i.get(a, 0) for i in private["inventories"])
            for a in ANIMALS
        )
    ):
        return market, report
    final = (cfg.get("episodeSteps", 720) - 2) // cfg.get("turnsPerDay", 24)
    planned = planning_snapshot(obs, cfg, commands, market, params)
    needed = sum(
        fertilizer_value(t, obs, cfg, params) > 0
        for row in farm["tiles"]
        for t in row
        if isinstance(t, dict) and t.get("crop") in CROPS
    )
    held = planned["private"]["shed"].get("FERTILIZER", 0) + sum(
        i.get("FERTILIZER", 0) for i in planned["private"]["inventories"]
    )
    if needed > held and len(market) < cfg.get("maxMarketOrdersPerTurn", 10):
        missing = min(
            needed - held,
            max(0, cfg.get("shedCapacity", 100) - sum(planned["private"]["shed"].values())),
        )
        if missing and planned["farms"][obs["player"]]["money"] >= 150 + missing * 2 * price_at(
            "FERTILIZER", obs["market"]["inventory"]["FERTILIZER"] - missing - 20, params
        ):
            market.append(["BUY_PRODUCT", "FERTILIZER", missing])
            planned = planning_snapshot(obs, cfg, commands, market, params)
    baseline = production_projection(planned, cfg, params, routed=True)
    report["baseline"] = baseline
    animal_sites, fields = farm_sites(obs)

    def empty(sites):
        return [
            p
            for p in sites
            if farm["tiles"][p[1]][p[0]] is None
            or farm["tiles"][p[1]][p[0]] == "LOCKED"
            or isinstance(farm["tiles"][p[1]][p[0]], dict)
            and farm["tiles"][p[1]][p[0]].get("kind") == "WEED"
        ]

    options = []
    free_animals = empty(animal_sites)
    if free_animals and sum(planned["private"]["shed"].values()) < cfg.get("shedCapacity", 100):
        for animal in ("COW", "SHEEP"):
            options.append(
                (
                    0,
                    [["BUY_ANIMAL", animal, 1]],
                    [dict(animal=animal, placed_day=day + 1, site=free_animals[0])],
                )
            )
    owned = len(farm["unlocked_quadrants"])
    for extra in (False, True):
        if extra and (owned >= max_land or len(empty(fields)) > 6):
            continue
        possible = empty(farm_sites(obs, extra)[1])
        land = (1000, 2000, 4000)[owned - 1] if extra else 0
        for count in (1, 4, 8, 12):
            if count > len(possible) or extra and count <= len(empty(fields)):
                continue
            for crop in CROPS:
                if day + 1 + CROPS[crop]["harvest"] > final:
                    continue
                additions = [
                    dict(crop=crop, planted_day=day + 1, site=p, fertilized=True)
                    for p in possible[:count]
                ]
                orders = ([["BUY_LAND"]] if extra else []) + [["BUY_SEED", crop, count]]
                options.append((land, orders, additions))
    for land, orders, additions in options:
        if len(market) + len(orders) > cfg.get("maxMarketOrdersPerTurn", 10):
            continue
        projection = production_projection(
            planned, cfg, params, additions, routed=True, land_cost=land
        )
        cost = land + sum(
            ANIMALS[c["animal"]]["cost"] if "animal" in c else CROPS[c["crop"]]["seed"]
            for c in additions
        )
        option = {
            "orders": orders,
            "land_cost": land,
            "columns": additions,
            "marginal_value": projection["value"] - baseline["value"],
            "min_cash": projection["min_cash"],
            "cost_now": cost,
            "route_feasible": projection.get("route_feasible", True),
            "affordable": planned["farms"][obs["player"]]["money"] >= cost + 150
            and projection["min_cash"] >= 150,
            "projection": projection,
        }
        report["alternatives"].append(option)
    feasible = [
        o
        for o in report["alternatives"]
        if o["affordable"] and o["route_feasible"] and o["marginal_value"] > 0
    ]
    if feasible:
        best = max(feasible, key=lambda o: o["marginal_value"] / len(o["columns"]))
        family = best["orders"][-1][:2]
        report["chosen"] = max(
            (o for o in feasible if o["orders"][-1][:2] == family),
            key=lambda o: o["marginal_value"],
        )
        market.extend(report["chosen"]["orders"])
    return market, report


def expansion_turn(obs, configuration=None, max_land=3, timing=0, investments=True):
    return mixed_turn(
        obs,
        configuration,
        crop_limit=65,
        production=True,
        expansion=max_land,
        timing=timing,
        investments=investments,
    )


def agent(obs, configuration=None):
    return expansion_turn(obs, configuration)[0]
