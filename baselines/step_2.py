"""Step 2: exact small worker-task assignment inside a heuristic wheat policy.

Single-file, standard-library Kaggle artifact. See docs/STEP_2_OPTIMIZATION.md.
"""

MAX_HANDS = 4
MAX_WORKERS = MAX_HANDS + 1
MAX_TASKS = 30  # 25 crop tiles plus up to five private deposit tasks.


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


def plan_turn(obs, configuration=None, allocator=maximum_assignment):
    """Return (action, explanation). This pure function never mutates the observation."""
    cfg = configuration or {}
    tpd = cfg.get("turnsPerDay", 24)
    last_step = cfg.get("episodeSteps", 720) - 2
    day, hour = obs["day"], obs["hour"]
    step = obs.get("step", day * tpd + hour)
    remaining, today = last_step - step + 1, tpd - hour
    final_day = day == last_step // tpd
    can_grow = day + 4 <= last_step // tpd
    farm = obs["farms"][obs["player"]]
    private = obs["private"]
    tiles = farm["tiles"]
    half = len(tiles) // 2
    access = [(x, y) for x in (half - 1, half) for y in (half - 1, half)]
    positions = [tuple(p) for p in [farm["farmer"], *farm["hands"]]]
    inventories = private["inventories"]
    seeds = private["seeds"].get("WHEAT", 0)
    stock = private["shed"].get("WHEAT", 0)
    # Limit scope to the initial quadrant and at most 25 nearby tiles.
    plots = sorted(
        [(x, y) for y in range(max(0, half - 5), half) for x in range(max(0, half - 5), half)],
        key=lambda p: (distance(p, access[0]), p),
    )
    growing = [
        p
        for p in plots
        if isinstance(tiles[p[1]][p[0]], dict) and tiles[p[1]][p[0]].get("crop") == "WHEAT"
    ]
    # Workforce size is a conservative policy cap, not an optimal investment decision.
    target_hands = (
        min(MAX_HANDS, (len(plots) - 1) // 5)
        if can_grow
        else min(MAX_HANDS, max(0, len(growing) - 1))
    )
    cash = int(farm["money"])
    order_limit = max(1, cfg.get("maxMarketOrdersPerTurn", 10))
    reserve = 10 if can_grow and seeds == 0 else 0
    hires = []
    if hour == 0 and remaining > 2:
        for index in range(farm["hires_today"], target_hands):
            # Keep one order available for a sale or a seed purchase.
            if len(hires) >= order_limit - 1:
                break
            cost = hire_cost(index, cfg.get("farmHandCostMult", 1))
            if cash - cost < reserve:
                break
            hires.append(["HIRE"])
            cash -= cost
    # Newly hired hands start acting next turn. Only existing units enter this solve.
    n = min(len(positions), MAX_WORKERS)
    production_plots = set(plots[: min(len(plots), 5 * (n + len(hires)))])
    tasks = []
    for p in plots:
        tile = tiles[p[1]][p[0]]
        operation, priority = None, 0
        if isinstance(tile, dict) and tile.get("crop") == "WHEAT":
            age = day - tile["planted_day"]
            mature = age >= 4 or (final_day and age >= 2)
            # Near termination, harvesting a smaller yield can beat another watering.
            can_water_then_bank = remaining >= 3 + min(distance(p, a) for a in access)
            if not tile["watered_today"] and (not final_day or can_water_then_bank):
                operation = "WATER"
                priority = 40_000 if tile["consecutive_unwatered"] else 20_000
            elif mature and tile["yield_units"] > 0:
                operation, priority = "HARVEST", 30_000
        elif can_grow and p in production_plots:
            if tile is None:
                operation, priority = "PLANT", 4_000
            elif isinstance(tile, dict) and tile.get("kind") == "WEED":
                operation, priority = "DIG", 3_000
        if operation:
            tasks.append({"position": p, "op": operation, "priority": priority, "owner": None})
    for worker, p in enumerate(positions[:n]):
        carried = inventories[worker].get("WHEAT", 0)
        if carried:
            target = min(access, key=lambda a: (distance(p, a), a))
            urgent = remaining <= distance(p, target) + 2
            tasks.append(
                {
                    "position": target,
                    "op": "PLACE",
                    "owner": worker,
                    "priority": 100_000 if urgent else 8_000,
                }
            )

    weights = []
    for worker, p in enumerate(positions[:n]):
        carried = inventories[worker].get("WHEAT", 0)
        return_distance = min(distance(p, a) for a in access)
        must_return = carried > 0 and remaining <= return_distance + 2
        row = []
        for task in tasks:
            target, op = task["position"], task["op"]
            travel = distance(p, target)
            feasible = task["owner"] in (None, worker)
            if must_return and op != "PLACE":
                feasible = False
            required = travel + (2 if op == "PLANT" else 1)
            if required > min(today, remaining):
                feasible = False
            if op == "HARVEST" and final_day:
                bank_time = travel + 2 + min(distance(target, a) for a in access)
                feasible = feasible and bank_time <= remaining
            if op == "WATER" and final_day:
                bank_time = travel + 3 + min(distance(target, a) for a in access)
                feasible = feasible and bank_time <= remaining
            if op == "PLACE" and sum(private["shed"].values()) >= cfg.get("shedCapacity", 100):
                feasible = False
            row.append(task["priority"] - 100 * travel if feasible else None)
        weights.append(row)
    chosen = allocator(weights, [t["op"] == "PLANT" for t in tasks], seeds)
    actions = [["PASS"] for _ in positions]
    explanation = []
    room = max(0, cfg.get("shedCapacity", 100) - sum(private["shed"].values()))
    # Engine executes units in farmer/hand order. Reserve shared space in that order.
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
            actions[worker] = ["PLANT", "WHEAT"]
        elif op == "PLACE":
            amount = min(inventories[worker].get("WHEAT", 0), room)
            if amount:
                actions[worker] = ["PLACE", "WHEAT", amount]
                room -= amount
                stock += amount
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

    market = [["SELL", "WHEAT", stock]] if stock else []
    # Never finance purchases from uncertain future sale proceeds.
    market.extend(hires[: max(0, order_limit - len(market))])
    # Buy at most one small workforce-sized batch; exact lot sizing is Step 3.
    used = sum(action == ["PLANT", "WHEAT"] for action in actions)
    empty = sum(tiles[y][x] is None for x, y in production_plots)
    wanted = max(0, min(empty, n) - seeds)
    if can_grow and today >= 4 and wanted and len(market) < order_limit:
        amount = min(wanted, cash // 10)
        if amount:
            market.append(["BUY_SEED", "WHEAT", amount])
    return {"farmer": actions[0], "hands": actions[1:], "market": market}, {
        "step": step,
        "seeds_available": seeds,
        "seeds_used_now": used,
        "workers": explanation,
        "planned_hires": len(hires),
        "assignment_score": sum(item["score"] for item in explanation),
        "policy": "Four-hand cap; wheat only; priority scores are not cash or dual prices.",
    }


def agent(obs, configuration=None):
    return plan_turn(obs, configuration)[0]
