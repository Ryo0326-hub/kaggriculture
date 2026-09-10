"""Step 4: marginal livestock investment, feed liquidity, and bounded daily routes.

Standard-library, single-file agent. See docs/STEP_4_OPTIMIZATION.md.
"""

import math

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


def plan_turn(obs, configuration=None, allowed_animals=("COW", "SHEEP"), herd_limit=HERD_LIMIT):
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


def agent(obs, configuration=None):
    return plan_turn(obs, configuration)[0]
