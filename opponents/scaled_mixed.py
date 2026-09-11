"""Reactive high-throughput benchmark, developed from public replay mechanisms.

Own implementation, derived from our expanding_mixed control (same policy family).
No candidate imports, replay playback, seed access, or future demand information.
Fixed portfolios deliberately test supply pressure; they are not an optimal policy.
"""

COWS = 6
ANIMALS = 10
CROP_SITES = 60


def distance(a, b):
    return abs(a[0] - b[0]) + abs(a[1] - b[1])


def move(a, b):
    if a[0] != b[0]:
        return ["EAST" if a[0] < b[0] else "WEST"]
    if a[1] != b[1]:
        return ["SOUTH" if a[1] < b[1] else "NORTH"]
    return ["PASS"]


def geometry(farm):
    half = len(farm["tiles"]) // 2
    access = [(x, y) for x in (half - 1, half) for y in (half - 1, half)]
    livestock = sorted(
        [(x, y) for x in range(half) for y in range(half)],
        key=lambda p: (distance(p, access[0]), p),
    )[:ANIMALS]
    fields = []
    for qx, qy in ((0, 0), (1, 0), (0, 1), (1, 1)):
        # Serpentine order gives compact zones and keeps earlier quadrants stable.
        for y in range(qy * half, (qy + 1) * half):
            xs = list(range(qx * half, (qx + 1) * half))
            for x in xs if y % 2 == 0 else reversed(xs):
                if farm["tiles"][y][x] != "LOCKED" and (x, y) not in livestock:
                    fields.append((x, y))
    fields = fields[:CROP_SITES]
    zones = [
        [p for p in livestock if p[0] == half - 1],
        [p for p in livestock if p[0] == half - 2],
        [p for p in livestock if p[0] < half - 2],
    ]
    zones += [fields[i : i + 6] for i in range(0, len(fields), 6)]
    return access, livestock, fields, zones


def crop_choice(day, index, final):
    if day < 4:
        return "MELON" if index < 6 else "WHEAT"
    if 5 <= day <= min(14, final - 12) and index % 6 < 4:
        return "STRAWBERRY"
    return "WHEAT" if day + 4 <= final else None


def crop_job(tile, day, final, fertilizer):
    crop, age = tile["crop"], day - tile["planted_day"]
    last = {"WHEAT": 4, "MELON": 12, "STRAWBERRY": 16}[crop]
    if tile["yield_units"] and (day == final or crop == "STRAWBERRY" and age >= last):
        return 950, "HARVEST"
    if tile["yield_units"] and crop != "STRAWBERRY" and age >= last and tile["watered_today"]:
        return 1000, "HARVEST"
    if day == final:
        return None
    bonus = (
        age
        in (
            {"WHEAT": (2, 3, 4), "MELON": (6, 7, 8, 9, 10, 11, 12), "STRAWBERRY": (9, 11, 13, 15)}[
                crop
            ]
        )
    )
    water = not tile["watered_today"] and (age == 0 or tile["consecutive_unwatered"] or bonus)
    if water:
        if fertilizer and bonus and tile["fertilized_until_day"] < day:
            return 920, "FERTILIZE"
        return (930 if age == 0 or tile["consecutive_unwatered"] else 800), "WATER"
    if tile["yield_units"] and (crop == "STRAWBERRY" or age >= (4 if crop == "WHEAT" else 10)):
        return 750, "HARVEST"
    if crop == "STRAWBERRY" and age >= 16:
        return 100, "DIG"
    return None


def agent(obs, configuration=None):
    cfg = configuration or {}
    farm, private = obs["farms"][obs["player"]], obs["private"]
    day, hour = obs["day"], obs["hour"]
    tpd, steps = cfg.get("turnsPerDay", 24), cfg.get("episodeSteps", 720)
    final = (steps - 2) // tpd
    remaining = min(tpd - hour, steps - 1 - obs.get("step", day * tpd + hour))
    access, livestock, fields, zones = geometry(farm)
    types = ["COW", "SHEEP", "COW", "SHEEP"]
    types += ["COW"] * (COWS - 2) + ["SHEEP"] * (ANIMALS - COWS - 2)
    stock, seeds = dict(private["shed"]), dict(private["seeds"])
    positions = [farm["farmer"], *farm["hands"]]
    commands, reserved = [], []
    initial_stock_and_carries = sum(stock.values()) + sum(
        sum(v.values()) for v in private["inventories"]
    )
    for i, (position, inventory) in enumerate(zip(positions, private["inventories"])):
        pos, inv = tuple(position), dict(inventory)
        shed = min(access, key=lambda a: (distance(pos, a), a))
        zone = zones[i] if i < len(zones) else []
        choices = []
        for p in zone:
            tile, travel = farm["tiles"][p[1]][p[0]], distance(pos, p)
            if i < 3:
                item = types[livestock.index(p)]
                if not isinstance(tile, dict) or "animal" not in tile:
                    if day < final - 8 and (inv.get(item, 0) or stock.get(item, 0)):
                        if travel + 5 < remaining:
                            choices.append((500 - travel * 55, p, "INSTALL", item))
                elif day < final and not tile["fed_today"]:
                    choices.append((1000 - travel * 55, p, "FEED", item))
                elif tile["yield_units"]:
                    choices.append((950 - travel * 55, p, "HARVEST", item))
                elif day < final - 1 and not tile["cared_today"]:
                    choices.append((700 - travel * 55, p, "CARE", item))
                elif tile["fertilizer_available"]:
                    choices.append((650 - travel * 55, p, "COLLECT_FERTILIZER", item))
            elif isinstance(tile, dict) and tile.get("crop"):
                job = crop_job(tile, day, final, inv.get("FERTILIZER", 0))
                if job:
                    choices.append((job[0] - travel * 55, p, job[1], tile["crop"]))
            else:
                crop = crop_choice(day, fields.index(p), final)
                if crop and seeds.get(crop, 0) and travel + 3 < remaining:
                    choices.append((150 - travel * 55, p, "DIG" if tile else "PLANT", crop))
        # Normal nights deposit automatically, with a shared 100-unit shed cap.
        # Deposit large loads during the day; final-day deliveries are mandatory.
        sale_goods = sum(
            n for item, n in inv.items() if item not in ("WHEAT", "FERTILIZER", "COW", "SHEEP")
        )
        return_now = (day == final and remaining <= distance(pos, shed) + 2) or sale_goods >= 12
        op = ["PASS"]
        if return_now or not choices:
            if sum(inv.values()):
                op = move(pos, shed) if pos != shed else ["DROP"]
        else:
            _, target, job, item = max(choices)
            travel = distance(pos, target)
            if job in ("HARVEST", "COLLECT_FERTILIZER"):
                tile = farm["tiles"][target[1]][target[0]]
                addition = 1 if job == "COLLECT_FERTILIZER" else tile["yield_units"]
                total = initial_stock_and_carries
                # Conservative shared capacity reservation across simultaneous harvests.
                capacity_ok = total + sum(reserved) + addition <= cfg.get("shedCapacity", 100)
                delivery_ok = (
                    day != final
                    or travel + min(distance(target, a) for a in access) + 2 <= remaining
                )
                if not capacity_ok or not delivery_ok:
                    if sum(inv.values()):
                        op = move(pos, shed) if pos != shed else ["DROP"]
                    commands.append(op)
                    continue
                reserved.append(addition)
            if job in ("FEED", "INSTALL") and not inv.get("WHEAT", 0):
                n = min(len(zone), stock.get("WHEAT", 0))
                op = move(pos, shed) if pos != shed else ["PICKUP", "WHEAT", n] if n else ["PASS"]
            elif job == "INSTALL" and not inv.get(item, 0):
                op = move(pos, shed) if pos != shed else ["PICKUP", item, 1]
            elif (
                i >= 3
                and pos == shed
                and not inv.get("FERTILIZER", 0)
                and stock.get("FERTILIZER", 0)
                and day >= 2
            ):
                op = ["PICKUP", "FERTILIZER", min(3, stock["FERTILIZER"])]
            elif pos != target:
                op = move(pos, target)
            elif job == "INSTALL":
                tile = farm["tiles"][pos[1]][pos[0]]
                op = (
                    ["BUILD_PASTURE"]
                    if tile is None
                    else ["PLACE", item]
                    if tile.get("kind") == "PASTURE"
                    else ["DIG"]
                )
            elif job == "PLANT":
                op = ["PLANT", item]
                seeds[item] -= 1
            else:
                op = [job]
        if op[0] == "PICKUP":
            stock[op[1]] -= op[2]
        if op[0] == "DROP":
            for item, n in inv.items():
                stock[item] = stock.get(item, 0) + n
        commands.append(op)
    orders = []
    for item, n in stock.items():
        keep = (
            2 * ANIMALS
            if item == "WHEAT" and day < final
            else 20
            if item == "FERTILIZER" and day < final - 3
            else 0
        )
        if item not in ("COW", "SHEEP") and n > keep:
            orders.append(["SELL", item, n - keep])
    # Purchases use current cash only; do not spend estimated same-turn receipts.
    cash = farm["money"]
    if day == 0 and hour == 0:
        orders += [
            ["BUY_ANIMAL", "COW", 2],
            ["BUY_ANIMAL", "SHEEP", 2],
            ["BUY_SEED", "MELON", 6],
            ["BUY_SEED", "WHEAT", 9],
        ]
        cash -= 2370
    feed = (
        max(
            0,
            2 * ANIMALS
            - stock.get("WHEAT", 0)
            - sum(v.get("WHEAT", 0) for v in private["inventories"]),
        )
        if day < final
        else 0
    )
    if feed and len(orders) < 10:
        price = 2 * obs["market"]["prices"]["WHEAT"]
        n = min(feed, max(0, int((cash - 100) // price)))
        if n:
            orders.append(["BUY_PRODUCT", "WHEAT", n])
            cash -= price * n
    if hour <= 4:
        hires = len(farm["hands"])
        while hires < min(12, len(zones) - 1) and len(orders) < 10:
            a, b = 1, 1
            for _ in range(farm["hires_today"] + hires - len(farm["hands"])):
                a, b = b, a + b
            if cash < a + 80:
                break
            orders.append(["HIRE"])
            hires += 1
            cash -= a
    if 5 <= day <= 14 and hour == 1:
        nland = len(farm["unlocked_quadrants"])
        if nland < 3 and cash > (1000 if nland == 1 else 2000) + 1600 and len(orders) < 10:
            orders.append(["BUY_LAND"])
            cash -= 1000 if nland == 1 else 2000
    if day < final - 10 and hour == 2:
        for animal in ("COW", "SHEEP"):
            have = sum(
                isinstance(t, dict) and t.get("animal") == animal
                for row in farm["tiles"]
                for t in row
            )
            have += stock.get(animal, 0) + sum(v.get(animal, 0) for v in private["inventories"])
            cost = 400 if animal == "COW" else 500
            if have < types.count(animal) and cash > cost + 1600 and len(orders) < 10:
                orders.append(["BUY_ANIMAL", animal, 1])
                cash -= cost
    if hour <= 12:
        needs = {}
        for index, p in enumerate(fields):
            tile = farm["tiles"][p[1]][p[0]]
            if isinstance(tile, dict) and tile.get("crop"):
                continue
            crop = crop_choice(day, index, final)
            if crop:
                needs[crop] = needs.get(crop, 0) + 1
        for crop, count in needs.items():
            cost = {"WHEAT": 10, "STRAWBERRY": 100, "MELON": 80}[crop]
            n = min(max(0, count - seeds.get(crop, 0)), 6, max(0, int((cash - 350) // cost)))
            if n and len(orders) < 10 and not (day == 0 and hour == 0):
                orders.append(["BUY_SEED", crop, n])
                cash -= n * cost
    return {"farmer": commands[0], "hands": commands[1:], "market": orders[:10]}
