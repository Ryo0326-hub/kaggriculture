"""Step 3: price-aware crop lots and marginal hiring, with coordinated execution.

Single-file, standard-library Kaggle artifact. See docs/STEP_3_OPTIMIZATION.md.
"""

import math

MAX_HANDS = 6
MAX_WORKERS = MAX_HANDS + 1
MAX_TASKS = 25 + MAX_WORKERS

# Unfertilized peak yields: initial unit plus one per bonus-window watering.
CROPS = {
    "WHEAT": {"seed": 10, "days": 4, "yield": 4},
    "CARROT": {"seed": 20, "days": 3, "yield": 3},
}
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


def crop_forecast(obs, cfg, crop, params, duration=None):
    """Use observed shops and visible standing crops, never hidden rival stock or RNG seed."""
    duration = CROPS[crop]["days"] if duration is None else duration
    tpd = cfg.get("turnsPerDay", 24)
    demand = tpd / max(1, cfg.get("townCenterSellInterval", 24))
    for shop in obs["town"].get("unlocked_shops", []):
        products = SHOP_PRODUCTS.get(shop, [])
        if crop in products:
            demand += (
                tpd / max(1, cfg.get("townShopSellInterval", 4)) * (2 if len(products) == 1 else 1)
            )
    supply = obs["private"]["shed"].get(crop, 0)
    supply += sum(inv.get(crop, 0) for inv in obs["private"]["inventories"])
    for farm in obs["farms"]:
        for row in farm["tiles"]:
            for tile in row:
                if isinstance(tile, dict) and tile.get("crop") == crop:
                    age_at_sale = obs["day"] + duration - tile["planted_day"]
                    expected_yield = min(CROPS[crop]["yield"], 1 + max(0, age_at_sale - 1))
                    supply += max(tile["yield_units"], expected_yield)
    return {
        "inventory_at_harvest": obs["market"]["inventory"][crop] + supply - duration * demand,
        "visible_committed_units": supply,
        "observed_daily_demand": demand,
    }


def optimize_lots(values, seed_costs, owned_seeds, slots, work_capacity, cash):
    """Exact two-crop integer allocation for tabulated returns and a cash/work budget."""
    best = (0.0, (0, 0), 0)
    limit = min(slots, max(0, int(work_capacity // 4)))
    for wheat in range(limit + 1):
        for carrot in range(limit - wheat + 1):
            quantities = (wheat, carrot)
            spend = sum(max(0, q - s) * c for q, s, c in zip(quantities, owned_seeds, seed_costs))
            if spend > cash:
                continue
            value = values[0][wheat] + values[1][carrot]
            if value > best[0]:
                best = (value, quantities, spend)
    return best


def economic_plan(obs, cfg, plots, fixed_hands=False, wheat_only=False, supply_buffer=True):
    """Enumerate affordable workforce/lot plans in a small, explicitly approximate model."""
    farm, private = obs["farms"][obs["player"]], obs["private"]
    tpd = cfg.get("turnsPerDay", 24)
    last_step = cfg.get("episodeSteps", 720) - 2
    remaining = last_step - obs.get("step", obs["day"] * tpd + obs["hour"]) + 1
    today = min(tpd - obs["hour"], remaining)
    current = len(farm["hands"])
    params = {c: dict(p) for c, p in MARKET.items()}
    for c in params:
        params[c].update(cfg.get("marketParams", {}).get(c, {}))
        params[c].update(obs["market"].get("params", {}).get(c, {}))
    cycles = {
        c: max(0, min(data["days"], last_step // tpd - obs["day"])) for c, data in CROPS.items()
    }
    forecasts = {c: crop_forecast(obs, cfg, c, params, cycles[c]) for c in CROPS}
    for c, f in forecasts.items():
        # Stress scenario: one additional field's unfertilized harvest precedes ours.
        f["supply_buffer_units"] = 25 * CROPS[c]["yield"] if supply_buffer else 0
        f["stress_inventory"] = f["inventory_at_harvest"] + f["supply_buffer_units"]
    slots, required_work, protected_value = 0, 0, 0.0
    for x, y in plots:
        tile = farm["tiles"][y][x]
        if tile is None or (isinstance(tile, dict) and tile.get("kind") == "WEED"):
            slots += 1
        elif isinstance(tile, dict) and tile.get("crop") in CROPS:
            c = tile["crop"]
            need_water = not tile["watered_today"]
            age = obs["day"] - tile["planted_day"]
            ripe = age >= CROPS[c]["days"] or (obs["day"] == last_step // tpd and age >= 2)
            # A harvest releases land for another crop during this same day.
            slots += int(ripe)
            required_work += 3 * need_water + 2 * int(ripe)
            if need_water or ripe:
                protected_value += batch_revenue(
                    c,
                    forecasts[c]["inventory_at_harvest"],
                    max(tile["yield_units"], CROPS[c]["yield"]),
                    params,
                )
    # Returning carried goods also consumes worker actions, especially in the endgame.
    half = len(farm["tiles"]) // 2
    for p, inv in zip([farm["farmer"], *farm["hands"]], private["inventories"]):
        if sum(inv.values()):
            required_work += abs(p[0] - (half - 1)) + abs(p[1] - (half - 1)) + 1
            protected_value += sum(inv.get(c, 0) * obs["market"]["prices"][c] for c in CROPS)
    values = []
    for c, data in CROPS.items():
        duration = cycles[c]
        can_finish = duration >= 2 and today >= 3
        if wheat_only and c != "WHEAT":
            can_finish = False
        table = [0.0]
        for q in range(1, slots + 1):
            spend = max(0, q - private["seeds"].get(c, 0)) * data["seed"]
            revenue = batch_revenue(c, forecasts[c]["stress_inventory"], q * duration, params)
            table.append((revenue - spend) / duration if can_finish else -1e12)
        values.append(table)
    max_extra = max(0, cfg.get("maxMarketOrdersPerTurn", 10) - len(CROPS) - 1)
    maximum = min(MAX_HANDS, current + max_extra) if today >= 4 else current
    if fixed_hands:
        maximum = min(maximum, max(current, 4))
    choices = []
    cost = 0
    for hands in range(current, maximum + 1):
        if hands > current:
            cost += hire_cost(
                farm["hires_today"] + hands - current - 1, cfg.get("farmHandCostMult", 1)
            )
        if cost > farm["money"]:
            break
        capacity = today * (current + 1) + max(0, today - 1) * (hands - current)
        service = min(1, capacity / required_work) if required_work else 1.0
        value, quantities, seed_spend = optimize_lots(
            values,
            [CROPS[c]["seed"] for c in CROPS],
            [private["seeds"].get(c, 0) for c in CROPS],
            slots,
            max(0, capacity - required_work),
            farm["money"] - cost,
        )
        choices.append(
            {
                "hands": hands,
                "hire_cost": cost,
                "seed_cost": seed_spend,
                "lots": dict(zip(CROPS, quantities)),
                "production_value": value,
                "capacity": capacity,
                "service_fraction": service,
                "model_value": service * protected_value + value - cost,
            }
        )
    selected = max(choices, key=lambda x: x["model_value"])
    if fixed_hands and (required_work or selected["production_value"] > 0):
        selected = choices[-1]
    selected = dict(selected)
    selected.update(
        {
            "required_work_estimate": required_work,
            "forecasts": forecasts,
            "crop_days_and_yield": cycles,
            "alternatives": choices,
            "params": params,
        }
    )
    return selected


def distance(a, b):
    return abs(a[0] - b[0]) + abs(a[1] - b[1])


def move_toward(start, target):
    if start[0] != target[0]:
        return ["EAST" if target[0] > start[0] else "WEST"]
    if start[1] != target[1]:
        return ["SOUTH" if target[1] > start[1] else "NORTH"]
    return ["PASS"]


def maximum_assignment(weights, seed_tasks, seed_budget):
    """Maximize total score with worker/task uniqueness and a shared seed quota.

    None removes an infeasible edge. -1 in the result means the worker stays idle.
    DP scans tasks; state = (assigned-worker bitmask, reserved seeds).
    Exact for these supplied scores/constraints, not for full-season profit.
    """
    n, m = len(weights), len(seed_tasks)
    if n > MAX_WORKERS or m > MAX_TASKS:
        raise ValueError("Assignment exceeds the bounded Step 2 problem size")
    if seed_budget < 0 or any(len(row) != m for row in weights):
        raise ValueError("Invalid assignment matrix or seed budget")
    budget = min(seed_budget, n)
    states = {(0, 0): (0, (-1,) * n)}
    for task in range(m):
        following = dict(states)  # Skipping this task is feasible.
        for (mask, used), (score, assignment) in states.items():
            new_used = used + int(seed_tasks[task])
            if new_used > budget:
                continue
            for worker, row in enumerate(weights):
                value = row[task]
                if mask & (1 << worker) or value is None or value <= 0:
                    continue
                key = (mask | (1 << worker), new_used)
                total = score + value
                if key not in following or total > following[key][0]:
                    chosen = assignment[:worker] + (task,) + assignment[worker + 1 :]
                    following[key] = (total, chosen)
        states = following
    # Stable input order and strict improvement give deterministic tie-breaking.
    return max(states.values(), key=lambda entry: entry[0])[1]


def hire_cost(index, multiplier):
    a, b = 1, 1
    for _ in range(index):
        a, b = b, a + b
    return multiplier * a


def plan_turn(
    obs,
    configuration=None,
    allocator=maximum_assignment,
    fixed_hands=False,
    wheat_only=False,
    supply_buffer=True,
):
    """Return an executable action and a source-replayable decision explanation."""
    cfg = configuration or {}
    tpd = cfg.get("turnsPerDay", 24)
    last_step = cfg.get("episodeSteps", 720) - 2
    day, hour = obs["day"], obs["hour"]
    step = obs.get("step", day * tpd + hour)
    remaining, today = last_step - step + 1, tpd - hour
    final_day = day == last_step // tpd
    farm, private = obs["farms"][obs["player"]], obs["private"]
    tiles = farm["tiles"]
    half = len(tiles) // 2
    access = [(x, y) for x in (half - 1, half) for y in (half - 1, half)]
    positions = [tuple(p) for p in [farm["farmer"], *farm["hands"]]]
    inventories = private["inventories"]
    plots = sorted(
        [(x, y) for y in range(max(0, half - 5), half) for x in range(max(0, half - 5), half)],
        key=lambda p: (distance(p, access[0]), p),
    )
    economics = economic_plan(obs, cfg, plots, fixed_hands, wheat_only, supply_buffer)
    hires = [["HIRE"] for _ in range(economics["hands"] - len(farm["hands"]))]
    n = min(len(positions), MAX_WORKERS)
    wanted_crops = [c for c in CROPS if economics["lots"][c] > 0]
    stocked = [c for c in wanted_crops if private["seeds"].get(c, 0)]
    plant_crop = max(stocked or wanted_crops, key=lambda c: economics["lots"][c], default=None)
    seeds = private["seeds"].get(plant_crop, 0)
    tasks = []
    for p in plots:
        tile = tiles[p[1]][p[0]]
        op, priority = None, 0
        if isinstance(tile, dict) and tile.get("crop") in CROPS:
            age = day - tile["planted_day"]
            mature = age >= CROPS[tile["crop"]]["days"] or (final_day and age >= 2)
            can_water_then_bank = remaining >= 3 + min(distance(p, a) for a in access)
            if not tile["watered_today"] and (not final_day or can_water_then_bank):
                op = "WATER"
                priority = 40_000 if tile["consecutive_unwatered"] else 20_000
            elif mature and tile["yield_units"] > 0:
                op, priority = "HARVEST", 30_000
        elif plant_crop:
            if tile is None:
                op, priority = "PLANT", 4_000
            elif isinstance(tile, dict) and tile.get("kind") == "WEED":
                op, priority = "DIG", 3_000
        if op:
            tasks.append({"position": p, "op": op, "priority": priority, "owner": None})
    for worker, p in enumerate(positions[:n]):
        if sum(inventories[worker].values()):
            target = min(access, key=lambda a: (distance(p, a), a))
            urgent = remaining <= distance(p, target) + 2
            tasks.append(
                {
                    "position": target,
                    "op": "DEPOSIT",
                    "owner": worker,
                    "priority": 100_000 if urgent else 8_000,
                }
            )
    weights = []
    for worker, p in enumerate(positions[:n]):
        carried = sum(inventories[worker].values())
        return_distance = min(distance(p, a) for a in access)
        must_return = carried > 0 and remaining <= return_distance + 2
        row = []
        for task in tasks:
            target, op = task["position"], task["op"]
            travel = distance(p, target)
            feasible = task["owner"] in (None, worker)
            if must_return and op != "DEPOSIT":
                feasible = False
            if travel + (2 if op == "PLANT" else 1) > min(today, remaining):
                feasible = False
            if op in ("HARVEST", "WATER") and final_day:
                bank_time = (
                    travel + (3 if op == "WATER" else 2) + min(distance(target, a) for a in access)
                )
                feasible = feasible and bank_time <= remaining
            if op == "DEPOSIT" and sum(private["shed"].values()) >= cfg.get("shedCapacity", 100):
                feasible = False
            row.append(task["priority"] - 100 * travel if feasible else None)
        weights.append(row)
    planting_budget = min(seeds, economics["lots"].get(plant_crop, 0))
    chosen = allocator(weights, [t["op"] == "PLANT" for t in tasks], planting_budget)
    actions = [["PASS"] for _ in positions]
    explanation = []
    room = max(0, cfg.get("shedCapacity", 100) - sum(private["shed"].values()))
    stock = {c: private["shed"].get(c, 0) for c in CROPS}
    for worker, task_index in enumerate(chosen):
        if task_index < 0:
            explanation.append(
                {"worker": worker, "task": None, "score": 0, "action": actions[worker]}
            )
            continue
        task = tasks[task_index]
        op, target = task["op"], task["position"]
        if positions[worker] != target:
            actions[worker] = move_toward(positions[worker], target)
        elif op == "PLANT":
            actions[worker] = ["PLANT", plant_crop]
        elif op == "DEPOSIT":
            inventory = inventories[worker]
            carried = sum(inventory.values())
            if carried <= room:
                # DROP is safe only after reserving room for this entire inventory.
                actions[worker] = ["DROP"]
                for c in CROPS:
                    stock[c] += inventory.get(c, 0)
                room -= carried
            elif room:
                c = max(
                    (c for c in CROPS if inventory.get(c, 0)),
                    key=lambda c: obs["market"]["prices"][c],
                )
                amount = min(room, inventory[c])
                actions[worker] = ["PLACE", c, amount]
                room -= amount
                stock[c] += amount
        else:
            actions[worker] = [op]
        explanation.append(
            {
                "worker": worker,
                "task": task,
                "score": weights[worker][task_index],
                "action": actions[worker],
            }
        )
    order_limit = max(1, cfg.get("maxMarketOrdersPerTurn", 10))
    market = [["SELL", c, stock[c]] for c in CROPS if stock[c]][:order_limit]
    market.extend(hires[: max(0, order_limit - len(market))])
    if plant_crop and len(market) < order_limit and today >= 4:
        wanted = min(economics["lots"][plant_crop], n + len(hires)) - seeds
        cash = farm["money"] - economics["hire_cost"]
        amount = min(wanted, int(cash // CROPS[plant_crop]["seed"]))
        if amount > 0:
            market.append(["BUY_SEED", plant_crop, amount])
    return {"farmer": actions[0], "hands": actions[1:], "market": market}, {
        "step": step,
        "plant_crop": plant_crop,
        "seeds_available": seeds,
        "seeds_used_now": sum(a[0] == "PLANT" for a in actions),
        "workers": explanation,
        "planned_hires": len(hires),
        "assignment_score": sum(x["score"] for x in explanation),
        "economics": economics,
        "policy": "Approximate crop/labor forecasts; assignment scores are not LP dual prices.",
    }


def agent(obs, configuration=None):
    return plan_turn(obs, configuration)[0]
