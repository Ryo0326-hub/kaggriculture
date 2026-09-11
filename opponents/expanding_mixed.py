"""Independent expanding dairy/crop control with fixed geographic work zones.

This is our own reactive stress policy, not reconstructed private leaderboard code.
It has no imports from the candidate and cannot see seeds, future shops, or replays.
"""

MILK_COWS = 2
DELAY_SALES_UNTIL = 0


def dist(a, b):
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
    tpd = cfg.get("turnsPerDay", 24)
    final = (cfg.get("episodeSteps", 720) - 2) // tpd
    remaining = min(
        tpd - hour, cfg.get("episodeSteps", 720) - 1 - obs.get("step", day * tpd + hour)
    )
    half = len(farm["tiles"]) // 2
    accesses = [(x, y) for x in (half - 1, half) for y in (half - 1, half)]
    animal_sites = [
        (half - 1, half - 1),
        (half - 2, half - 1),
        (half - 1, half - 2),
        (half - 2, half - 2),
    ]
    animal_types = ["COW"] * MILK_COWS + ["SHEEP"] * (4 - MILK_COWS)
    fields = [
        (x, y)
        for y, row in enumerate(farm["tiles"])
        for x, t in enumerate(row)
        if t != "LOCKED" and (x, y) not in animal_sites
    ]
    # Compact four-cell strips give each crop worker a predictable local area.
    fields.sort(key=lambda p: (p[1] // 2, p[0] // 2, p[1], p[0]))
    target_fields = sorted(fields, key=lambda p: (min(dist(p, a) for a in accesses), p))[:36]
    target_fields.sort(key=lambda p: (p[1] // 2, p[0] // 2, p[1], p[0]))
    zones = [animal_sites[:2], animal_sites[2:]] + [
        target_fields[i : i + 4] for i in range(0, len(target_fields), 4)
    ]
    stock, seeds = dict(private["shed"]), dict(private["seeds"])
    commands, desired = [], 0
    for i, (pos, inv) in enumerate(zip([farm["farmer"], *farm["hands"]], private["inventories"])):
        pos = tuple(pos)
        shed = min(accesses, key=lambda a: (dist(pos, a), a))
        zone = zones[i] if i < len(zones) else []
        op = ["PASS"]
        choices = []
        for p in zone:
            t = farm["tiles"][p[1]][p[0]]
            travel = dist(pos, p)
            if i < 2:
                animal = animal_types[animal_sites.index(p)]
                if not isinstance(t, dict) or "animal" not in t:
                    if stock.get(animal, 0) or inv.get(animal, 0):
                        choices.append((400 - travel, p, "INSTALL", animal))
                elif day < final and not t["fed_today"]:
                    choices.append((600 - travel, p, "FEED", animal))
                elif day < final - 1 and not t["cared_today"]:
                    choices.append((300 - travel, p, "CARE", animal))
                elif t["yield_units"]:
                    choices.append((250 - travel, p, "HARVEST", animal))
                elif t["fertilizer_available"]:
                    choices.append((200 - travel, p, "COLLECT_FERTILIZER", animal))
            elif isinstance(t, dict) and t.get("crop"):
                crop, age = t["crop"], day - t["planted_day"]
                ripe = t["yield_units"] and (age >= (4 if crop == "WHEAT" else 10) or day == final)
                water = (
                    not t["watered_today"]
                    and day < final
                    and (
                        age == 0
                        or t["consecutive_unwatered"]
                        or crop == "MELON"
                        and 6 <= age <= 10
                        or crop == "WHEAT"
                        and 2 <= age <= 4
                        or crop == "STRAWBERRY"
                        and age in (9, 11, 13, 15)
                    )
                )
                if water:
                    job = (
                        "FERTILIZE"
                        if crop == "STRAWBERRY"
                        and age in (9, 11, 13, 15)
                        and t["fertilized_until_day"] < day
                        and inv.get("FERTILIZER", 0)
                        else "WATER"
                    )
                    choices.append((500 - travel, p, job, crop))
                elif ripe and travel + min(dist(p, a) for a in accesses) + 2 <= remaining:
                    choices.append((450 - travel, p, "HARVEST", crop))
                elif crop == "STRAWBERRY" and age >= 16 and not t["yield_units"]:
                    choices.append((50 - travel, p, "DIG", crop))
            else:
                crop = "MELON" if day < 4 else "STRAWBERRY" if day <= 17 else "WHEAT"
                maturity = 4 if crop == "WHEAT" else 10
                if day + maturity <= final and travel + 3 <= remaining:
                    if seeds.get(crop, 0):
                        choices.append((80 - travel, p, "DIG" if t else "PLANT", crop))
                    else:
                        desired += 1
        goods = sum(n for c, n in inv.items() if c not in ("FERTILIZER", "WHEAT", "COW", "SHEEP"))
        if remaining <= dist(pos, shed) + 2 or not choices or goods >= 16:
            if sum(inv.values()):
                op = move(pos, shed) if pos != shed else ["DROP"]
        elif choices:
            _, target, job, item = max(choices)
            if i < 2 and job in ("FEED", "INSTALL") and inv.get("WHEAT", 0) == 0:
                op = (
                    move(pos, shed)
                    if pos != shed
                    else ["PICKUP", "WHEAT", min(2, stock.get("WHEAT", 0))]
                )
            elif job == "INSTALL" and not inv.get(item, 0):
                op = move(pos, shed) if pos != shed else ["PICKUP", item, 1]
            elif (
                i >= 2
                and pos == shed
                and not inv.get("FERTILIZER", 0)
                and stock.get("FERTILIZER", 0)
                and day >= 8
                and any(
                    isinstance(farm["tiles"][q[1]][q[0]], dict)
                    and farm["tiles"][q[1]][q[0]].get("crop") == "STRAWBERRY"
                    and day - farm["tiles"][q[1]][q[0]]["planted_day"] in (9, 11, 13, 15)
                    for q in zone
                )
            ):
                op = ["PICKUP", "FERTILIZER", min(4, stock["FERTILIZER"])]
            elif pos != target:
                op = move(pos, target)
            elif job == "INSTALL":
                t = farm["tiles"][pos[1]][pos[0]]
                op = (
                    ["BUILD_PASTURE"]
                    if t is None
                    else ["PLACE", item]
                    if t.get("kind") == "PASTURE"
                    else ["DIG"]
                )
            elif job == "PLANT":
                op = ["PLANT", item]
                seeds[item] -= 1
            else:
                op = [job]
        if op[0] == "PICKUP":
            n = min(op[2], stock.get(op[1], 0))
            op = ["PICKUP", op[1], n] if n else ["PASS"]
            if n:
                stock[op[1]] -= n
        if op[0] == "DROP":
            for c, n in inv.items():
                stock[c] = stock.get(c, 0) + n
        commands.append(op)
    orders = []
    for c, n in stock.items():
        keep = (
            8
            if c == "WHEAT" and day < final
            else 8
            if c == "FERTILIZER" and 16 <= day < final
            else 0
        )
        if (
            c not in ("COW", "SHEEP")
            and n > keep
            and (day >= DELAY_SALES_UNTIL or sum(stock.values()) > 65 or day == final)
        ):
            orders.append(["SELL", c, n - keep])
    cash = farm["money"]
    if day == 0 and hour == 0:
        orders += [
            ["BUY_ANIMAL", "COW", MILK_COWS],
            ["BUY_ANIMAL", "SHEEP", 4 - MILK_COWS],
            ["BUY_SEED", "MELON", 8],
        ]
        cash -= 400 * MILK_COWS + 500 * (4 - MILK_COWS) + 640
    feed = (
        max(
            0,
            8 - stock.get("WHEAT", 0) - sum(inv.get("WHEAT", 0) for inv in private["inventories"]),
        )
        if day < final
        else 0
    )
    if feed and len(orders) < 10:
        price = 2 * obs["market"]["prices"]["WHEAT"]
        n = min(feed, int(cash // price))
        if n:
            orders.append(["BUY_PRODUCT", "WHEAT", n])
            cash -= n * price
    if hour <= 6:
        while (
            len(farm["hands"]) + sum(o[0] == "HIRE" for o in orders) < len(zones) - 1
            and len(orders) < 10
        ):
            a, b = 1, 1
            for _ in range(farm["hires_today"] + sum(o[0] == "HIRE" for o in orders)):
                a, b = b, a + b
            if cash < a + (
                0 if len(farm["hands"]) + sum(o[0] == "HIRE" for o in orders) < 2 else 100
            ):
                break
            orders.append(["HIRE"])
            cash -= a
    if day >= 8 and day <= 15 and hour == 0 and len(farm["unlocked_quadrants"]) < 3:
        cost = (1000, 2000)[len(farm["unlocked_quadrants"]) - 1]
        if cash > cost + 1500 and len(orders) < 10:
            orders.append(["BUY_LAND"])
            cash -= cost
    if (
        day >= 8
        and hour <= 10
        and desired
        and not sum(private["seeds"].values())
        and len(orders) < 10
    ):
        crop = "MELON" if day < 4 else "STRAWBERRY" if day <= 17 else "WHEAT"
        cost = {"MELON": 80, "STRAWBERRY": 100, "WHEAT": 10}[crop]
        n = min(desired, 4, max(0, int((cash - 400) // cost)))
        if n:
            orders.append(["BUY_SEED", crop, n])
    return {"farmer": commands[0], "hands": commands[1:], "market": orders[:10]}
