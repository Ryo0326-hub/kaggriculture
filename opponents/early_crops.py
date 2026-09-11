"""Independent reactive crop control: twelve early melons, then dated rotations.

No imports from the candidate, hidden-state access, replay actions, or RNG seed.
Fixed two-plot worker zones isolate early market supply from investment modeling.
This is a stress opponent, not an imitation of a leaderboard player's source.
"""

DELAY_SALES_UNTIL = 0  # A generated control can hold output until a specified day.


def distance(a, b):
    return abs(a[0] - b[0]) + abs(a[1] - b[1])


def move(a, b):
    if a[0] != b[0]:
        return ["EAST" if a[0] < b[0] else "WEST"]
    if a[1] != b[1]:
        return ["SOUTH" if a[1] < b[1] else "NORTH"]
    return ["PASS"]


def agent(obs, configuration=None):
    cfg = configuration or {}
    farm, private = obs["farms"][obs["player"]], obs["private"]
    day, hour = obs["day"], obs["hour"]
    final = (cfg.get("episodeSteps", 720) - 2) // cfg.get("turnsPerDay", 24)
    remaining = min(24 - hour, cfg.get("episodeSteps", 720) - 1 - obs.get("step", 24 * day + hour))
    half = len(farm["tiles"]) // 2
    shed_pos = (half - 1, half - 1)
    sites = sorted(
        [(x, y) for y in range(half) for x in range(half)],
        key=lambda p: (distance(p, shed_pos), p),
    )[:12]
    stock, seeds = dict(private["shed"]), dict(private["seeds"])
    commands, desired = [], {}
    for i, (pos, inv) in enumerate(zip([farm["farmer"], *farm["hands"]], private["inventories"])):
        zone = sites[2 * i : 2 * i + 2]
        if sum(inv.values()):
            op = move(pos, shed_pos) if tuple(pos) != shed_pos else ["DROP"]
            if op[0] == "DROP":
                for c, n in inv.items():
                    stock[c] = stock.get(c, 0) + n
            commands.append(op)
            continue
        choices = []
        for p in zone:
            tile = farm["tiles"][p[1]][p[0]]
            travel = distance(pos, p)
            if isinstance(tile, dict) and tile.get("crop"):
                crop, age = tile["crop"], day - tile["planted_day"]
                end = 4 if crop == "WHEAT" else 10
                growth_water = not tile["watered_today"] and (
                    crop == "WHEAT" and 2 <= age <= 4 or crop == "MELON" and 6 <= age <= 10
                )
                if growth_water and travel + 1 <= remaining:
                    choices.append((110 - travel, p, ["WATER"]))
                if not tile["watered_today"] and (age == 0 or tile["consecutive_unwatered"]):
                    choices.append((140 - travel, p, ["WATER"]))
                if tile["yield_units"] and (
                    age >= end or (day == final and age >= 2 and crop == "WHEAT")
                ):
                    if day != final or travel + distance(p, shed_pos) + 2 <= remaining:
                        choices.append((100 - travel, p, ["HARVEST"]))
                elif not tile["watered_today"] and (
                    age == 0
                    or tile["consecutive_unwatered"]
                    or crop == "WHEAT"
                    and age >= 2
                    or crop == "MELON"
                    and age >= 6
                ):
                    choices.append((80 - travel, p, ["WATER"]))
                elif crop == "STRAWBERRY" and age >= 16 and not tile["yield_units"]:
                    choices.append((10 - travel, p, ["DIG"]))
            else:
                crop = "MELON" if day == 0 else "STRAWBERRY" if day <= 12 else "WHEAT"
                maturity = 4 if crop == "WHEAT" else 10
                if day + maturity <= final and travel + 3 <= remaining:
                    if tile is not None:
                        choices.append((20 - travel, p, ["DIG"]))
                    elif seeds.get(crop, 0):
                        choices.append((30 - travel, p, ["PLANT", crop]))
                    else:
                        desired[crop] = desired.get(crop, 0) + 1
        if choices:
            _, target, job = max(choices)
            op = move(pos, target) if tuple(pos) != target else job
            if op[0] == "PLANT":
                seeds[op[1]] -= 1
            commands.append(op)
        else:
            commands.append(["PASS"])
    orders = []
    if day >= DELAY_SALES_UNTIL or sum(stock.values()) > 75 or day == final:
        orders += [["SELL", c, n] for c, n in stock.items() if n]
    cash = farm["money"]
    hired = farm["hires_today"]
    if hour < 5:
        while len(farm["hands"]) + sum(o[0] == "HIRE" for o in orders) < 5 and len(orders) < 10:
            a, b = 1, 1
            for _ in range(hired):
                a, b = b, a + b
            cost = a * cfg.get("farmHandCostMult", 1)
            if cash < cost:
                break
            orders.append(["HIRE"])
            cash -= cost
            hired += 1
    if day == 0 and hour == 0:
        orders.append(["BUY_SEED", "MELON", 12])
    elif hour <= 16 and len(orders) < 10:
        for crop, count in desired.items():
            n = min(count, max(0, int((cash - 60) // (10 if crop == "WHEAT" else 100))))
            if n and not private["seeds"].get(crop, 0):
                orders.append(["BUY_SEED", crop, n])
                break
    return {"farmer": commands[0], "hands": commands[1:], "market": orders[:10]}
