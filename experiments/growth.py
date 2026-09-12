"""Cycle 17: executable shared service routes and dated investment economics.

Bundled into the frozen Cycle 15 namespace. No environment, network or ML imports.
Forecasts price dated production columns; they do not roll out games.
"""

# ruff: noqa: F821


def growth_sites(obs, extra_land=False):
    """Extend the same compact livestock layout into every purchased quadrant."""
    farm = obs["farms"][obs["player"]]
    size, access = len(farm["tiles"]), shed_access(obs)
    half = size // 2
    names = ("NW", "NE", "SW", "SE")
    owned = set(farm["unlocked_quadrants"])
    if extra_land:
        owned.update(next(([name] for name in names if name not in owned), []))
    animals, fields = [], []
    for name, count in zip(names, (5, 7, 7, 5)):
        cells = [
            (x, y)
            for y in range(size)
            for x in range(size)
            if ("N" if y < half else "S") + ("W" if x < half else "E") == name
        ]
        cells.sort(key=lambda p: (min(distance(p, a) for a in access), p))
        if name in owned:
            animals.extend(cells[:count])
            fields.extend(cells[count:])
    # Existing crops/animals always remain serviced, even off the preferred layout.
    for y, row in enumerate(farm["tiles"]):
        for x, tile in enumerate(row):
            if isinstance(tile, dict):
                if tile.get("animal") and (x, y) not in animals:
                    animals.append((x, y))
                if tile.get("crop") in CROPS and (x, y) not in fields:
                    fields.append((x, y))
    fields.sort(key=lambda p: (min(distance(p, a) for a in access), p))
    # Preferred livestock pads guide early layout, not a permanent herd ceiling.
    # Once filled, an animal may use an otherwise vacant crop plot too.
    animals.extend(p for p in fields if p not in animals)
    return animals, fields


def growth_vacant(farm, sites, animal=False):
    result = []
    for p in sites:
        tile = farm["tiles"][p[1]][p[0]]
        if tile in (None, "LOCKED") or (
            isinstance(tile, dict)
            and not tile.get("animal")
            and tile.get("kind") in (("WEED", "COOP", "PASTURE") if animal else ("WEED",))
        ):
            result.append(p)
    return result


def growth_assets(obs, pending=True):
    assets = repaired_assets(obs)[obs["player"]]
    if not pending:
        return assets
    farm, private = obs["farms"][obs["player"]], obs["private"]
    animals, fields = growth_sites(obs)
    free = growth_vacant(farm, animals, True)
    for animal in ANIMALS:
        count = private["shed"].get(animal, 0) + sum(
            inv.get(animal, 0) for inv in private["inventories"]
        )
        for _ in range(min(count, len(free))):
            p = free.pop(0)
            assets.append(dict(animal=animal, placed_day=obs["day"], site=p, install=True))
    claimed = {tuple(t["site"]) for t in assets}
    free = [p for p in growth_vacant(farm, fields) if p not in claimed]
    for crop in CROPS:
        for _ in range(min(private["seeds"].get(crop, 0), len(free))):
            p = free.pop(0)
            assets.append(dict(crop=crop, planted_day=obs["day"], site=p, plant=True))
    return assets


def growth_care_due(tile, day, final):
    # The engine pays production BEFORE banking today's care. Care can only
    # increase a production at least two observation dates in the future.
    spec = ANIMALS[tile["animal"]]
    first = tile["placed_day"] + spec["first_yield_day"]
    date = first + max(0, math.ceil((day + 2 - first) / spec["interval"])) * spec["interval"]
    produces_tonight = day + 1 >= first and (day + 1 - first) % spec["interval"] == 0
    return date <= final and (
        produces_tonight or tile.get("pending_care_bonus", 0) < spec["max_held"] - 1
    )


def growth_service(tile, date, final):
    """Full-day site operations. Pickup, travel and deposit are charged per route."""
    if tile.get("animal"):
        placed = tile["placed_day"]
        if date < placed:
            return 0, ()
        install = date == placed and (tile.get("install") or placed > tile.get("observed", -1))
        # At most one feed, care, fertilizer collection and harvest per day.
        care_tile = dict(tile, pending_care_bonus=0) if date > tile.get("observed", date) else tile
        work = int(date < final) + int(growth_care_due(care_tile, date, final)) + 2
        if install:
            work += 3  # clear/build/place; counts only the NEW animal's setup
        inputs = (["WHEAT"] if date < final else []) + ([tile["animal"]] if install else [])
        return work, tuple(inputs)
    spec = CROPS[tile["crop"]]
    age = date - tile["planted_day"]
    end = spec["harvest"] + (spec["events"] - 1) * spec["interval"]
    if age < 0 or age > end:
        return 0, ()
    if age == 0:
        return 3, ()  # clear if needed, plant, first-day water
    if date == final:
        return (2 if age >= spec["first"] else 0), ()
    if spec["interval"]:
        producing = age >= spec["first"] and (age - spec["first"]) % spec["interval"] == 0
        preproduction = (
            age >= spec["first"] - 1 and (age + 1 - spec["first"]) % spec["interval"] == 0
        )
        return 1 + int(producing) + int(preproduction), (("FERTILIZER",) if preproduction else ())
    fertilize = tile["crop"] in ("WHEAT", "CARROT") and age == 2
    return 1 + int(age >= spec["harvest"]) + int(fertilize), (("FERTILIZER",) if fertilize else ())


@lru_cache(maxsize=2048)
def growth_routes(nodes, access, capacity, terminal=False):
    """Construct shared crop/livestock routes with a checkable action budget.

    This is a deterministic insertion heuristic, not an optimal VRP solver.
    Each node carries its service count and required pickup item types.
    """
    work = {p: n for p, n, _ in nodes}
    inputs = {p: set(items) for p, _, items in nodes}

    def duration(route):
        loads = set().union(*(inputs[p] for p in route))
        return (
            max(distance(a, route[0]) for a in access)
            + sum(distance(a, b) for a, b in zip(route, route[1:]))
            + (min(distance(route[-1], a) for a in access) + 1 if terminal else 0)
            + sum(work[p] for p in route)
            + len(loads)
        )

    routes = []
    for site in sorted(work, key=lambda p: (-min(distance(p, a) for a in access), p)):
        choices = []
        for i, route in enumerate(routes):
            before = duration(route)
            for at in range(len(route) + 1):
                proposed = (*route[:at], site, *route[at:])
                length = duration(proposed)
                if length <= capacity:
                    choices.append((length - before, length, i, proposed))
        if choices:
            _, _, i, route = min(choices)
            routes[i] = route
        else:
            routes.append((site,))
    routes = tuple(sorted(routes))
    durations = tuple(duration(route) for route in routes)
    return routes, durations, all(n <= capacity for n in durations)


def growth_workforce(assets, date, final, tpd, access):
    nodes = []
    for tile in assets:
        work, inputs = growth_service(tile, date, final)
        if work:
            nodes.append((tuple(tile["site"]), work, inputs))
    # The game's automatic night deposit removes routine return travel. The
    # final day is different: the final market must follow an explicit deposit.
    routes, durations, fits = growth_routes(
        tuple(nodes), tuple(access), max(1, tpd - 2), date == final
    )
    return dict(
        routes=routes,
        durations=durations,
        workers=max(1, len(routes)),
        fits=fits and len(routes) <= 17,
    )


def growth_jobs(obs, cfg, params, assets):
    """Complete site bundles, recomputed from observed completion flags only."""
    farm, private = obs["farms"][obs["player"]], obs["private"]
    day, tpd = obs["day"], cfg.get("turnsPerDay", 24)
    final = (cfg.get("episodeSteps", 720) - 2) // tpd
    remaining = min(
        tpd - obs["hour"],
        cfg.get("episodeSteps", 720) - 1 - obs.get("step", day * tpd + obs["hour"]),
    )
    fert_stock = private["shed"].get("FERTILIZER", 0) + sum(
        i.get("FERTILIZER", 0) for i in private["inventories"]
    )
    jobs, fertilizer_wanted = {}, 0
    for asset in assets:
        site = tuple(asset["site"])
        tile = farm["tiles"][site[1]][site[0]]
        ops, priority = [], 1
        if asset.get("install"):
            animal = asset["animal"]
            structure = ANIMALS[animal]["structure"]
            if isinstance(tile, dict) and tile.get("kind") != structure:
                ops.append(["DIG"])
            if not isinstance(tile, dict) or tile.get("kind") != structure:
                ops.append(["BUILD_" + structure])
            ops.extend([["PLACE", animal], ["FEED"]])
            if growth_care_due(asset, day, final):
                ops.append(["CARE"])
            priority = 40
        elif asset.get("plant"):
            if isinstance(tile, dict):
                ops.append(["DIG"])
            ops.extend([["PLANT", asset["crop"]], ["WATER"]])
            priority = 30
        elif asset.get("animal"):
            if day < final and not tile["fed_today"]:
                ops.append(["FEED"])
                priority = 300 if tile.get("consecutive_unfed", 0) else 150
            if tile["yield_units"]:
                ops.append(["HARVEST"])
                priority = max(priority, 100)
            if not tile["cared_today"] and growth_care_due(tile, day, final):
                ops.append(["CARE"])
            if tile["fertilizer_available"]:
                ops.append(["COLLECT_FERTILIZER"])
        else:
            crop, spec = asset["crop"], CROPS[asset["crop"]]
            age, units = day - tile["planted_day"], tile.get("yield_units", 0)
            end = spec["harvest"] + (spec["events"] - 1) * spec["interval"]
            ready = age >= spec["first"] and units > 0
            exhausted = age >= end and bool(spec["interval"])
            harvest = ready and (spec["interval"] or age >= spec["harvest"] or day == final)
            if crop == "WHEAT" and age >= 3 and units >= 5 and day + 5 <= final:
                harvest = True
            bonus_water = (
                not spec["interval"]
                and age >= (6 if crop == "MELON" else 2)
                and age <= (12 if crop == "MELON" else spec["harvest"])
                and units < (4 if crop == "CARROT" else 6)
            )
            water = not tile.get("watered_today") and (
                (day < final and not exhausted and (not harvest or bonus_water))
                or (day == final and harvest and bonus_water)
            )
            needs_fert = (
                day < final
                and not exhausted
                and timing_fertilizer_value(tile, obs, cfg, params) > 0
            )
            if needs_fert:
                fertilizer_wanted += 1
                # Missing optional fertilizer must never block required watering.
                if fert_stock and remaining >= 4:
                    ops.append(["FERTILIZE"])
            if water:
                ops.append(["WATER"])
                priority = 350 if tile.get("consecutive_unwatered", 0) else 120
            if harvest:
                ops.append(["HARVEST"])
                priority = max(priority, 280 if exhausted or not spec["interval"] else 100)
            if exhausted and not units and day < final:
                ops.append(["DIG"])
        if (
            day < final
            and len(ops) > remaining
            and not (asset.get("install") or asset.get("plant"))
        ):
            if ["FEED"] in ops:
                ops = [["FEED"]]
            elif ["HARVEST"] in ops and not (
                asset.get("crop") and CROPS[asset["crop"]]["interval"]
            ):
                ops = [["HARVEST"]]
            elif ["WATER"] in ops:
                ops = [["WATER"]]
        if ops:
            jobs[site] = dict(ops=ops, priority=priority, asset=asset)
    return jobs, fertilizer_wanted


def growth_requirements(ops):
    needs = {}
    for op in ops:
        item = (
            "WHEAT"
            if op[0] == "FEED"
            else "FERTILIZER"
            if op[0] == "FERTILIZE"
            else op[1]
            if op[0] == "PLACE" and op[1] in ANIMALS
            else None
        )
        if item:
            needs[item] = needs.get(item, 0) + 1
    return needs


def growth_dispatch(obs, cfg, params, jobs):
    """Assign physical routes to present workers; reserve inputs in worker order."""
    farm, private = obs["farms"][obs["player"]], obs["private"]
    access = shed_access(obs)
    positions = [tuple(farm["farmer"]), *map(tuple, farm["hands"])]
    day, hour, tpd = obs["day"], obs["hour"], cfg.get("turnsPerDay", 24)
    final = (cfg.get("episodeSteps", 720) - 2) // tpd
    remaining = min(
        tpd - hour, cfg.get("episodeSteps", 720) - 1 - obs.get("step", day * tpd + hour)
    )
    jobs = deepcopy(jobs)
    # On the final day, salvage a one-time crop when watering would make
    # harvest+delivery impossible, and exclude production that cannot be sold.
    if day == final:
        for site in list(jobs):
            ops = jobs[site]["ops"]
            if ["HARVEST"] in ops:
                best = min(distance(p, site) for p in positions)
                delivery = min(distance(site, a) for a in access) + 1
                if best + len(ops) + delivery > remaining:
                    jobs[site]["ops"] = [["HARVEST"]]
                if best + 1 + delivery > remaining:
                    del jobs[site]
            elif jobs[site]["ops"] != [["COLLECT_FERTILIZER"]]:
                del jobs[site]
    nodes = tuple((p, len(j["ops"]), tuple(growth_requirements(j["ops"]))) for p, j in jobs.items())
    routes, durations, _ = growth_routes(
        nodes, tuple(access), max(1, remaining - int(hour == 0)), day == final
    )
    actions = [["PASS"] for _ in positions]
    stock = dict(private["shed"])
    room = max(0, cfg.get("shedCapacity", 100) - sum(stock.values()))
    assignments, reserved, terminal = {}, set(), set()
    unallocated_stock = dict(stock)
    stored_and_carried = sum(stock.values()) + sum(sum(v.values()) for v in private["inventories"])
    for i, p in enumerate(positions):
        tile = farm["tiles"][p[1]][p[0]]
        fatal_local = isinstance(tile, dict) and (
            (
                tile.get("crop")
                and not tile.get("watered_today")
                and tile.get("consecutive_unwatered", 0)
            )
            or (
                tile.get("animal")
                and not tile.get("fed_today")
                and tile.get("consecutive_unfed", 0)
            )
        )
        goods = sum(n for c, n in private["inventories"][i].items() if c in MARKET and c != "WHEAT")
        if (
            day == final
            and sum(private["inventories"][i].values())
            and remaining <= min(distance(p, a) for a in access) + 2
        ):
            terminal.add(i)
        elif day < final and not fatal_local and goods and stored_and_carried >= 80:
            # Deliver sizeable batches before all workers' automatic night drops
            # compete for the same finite shed. Feed stocks stay on service tours.
            terminal.add(i)
    # Workers carrying a purchased animal keep priority for its installation.
    order = sorted(
        range(len(positions)),
        key=lambda i: (not any(private["inventories"][i].get(a, 0) for a in ANIMALS), i),
    )
    for i in order:
        if i in terminal:
            continue
        p, inv = positions[i], private["inventories"][i]
        choices = []
        # Single-site alternatives salvage urgent work when a worker cannot
        # complete a full route from its present location or carried inputs.
        candidates = [*routes, *((p,) for p in jobs)]
        for route_index, route in enumerate(candidates):
            if any(q in reserved for q in route):
                continue
            needs = growth_requirements([op for q in route for op in jobs[q]["ops"]])
            missing = {c: n - inv.get(c, 0) for c, n in needs.items() if n > inv.get(c, 0)}
            # Optional fertilizer can be dropped from a bundle; animals/feed
            # must really be available to the worker (or in the shed).
            if any(
                n > unallocated_stock.get(c, 0) for c, n in missing.items() if c != "FERTILIZER"
            ):
                continue
            missing = {c: n for c, n in missing.items() if unallocated_stock.get(c, 0)}
            held_animals = [a for a in ANIMALS if inv.get(a, 0)]
            if held_animals and not any(needs.get(a, 0) for a in held_animals):
                continue
            start = (
                min(access, key=lambda a: (distance(p, a) + distance(a, route[0]), a))
                if missing
                else p
            )
            travel = distance(p, start) + distance(start, route[0])
            length = (
                travel
                + len(missing)
                + sum(distance(a, b) for a, b in zip(route, route[1:]))
                + sum(len(jobs[q]["ops"]) for q in route)
                + (min(distance(route[-1], a) for a in access) + 1 if day == final else 0)
            )
            if length > remaining:
                continue
            urgency = max(jobs[q]["priority"] for q in route)
            local = p == route[0]
            choices.append(
                (
                    urgency + 30 * local + 5 * len(route) - 4 * travel,
                    -length,
                    -route_index,
                    route_index,
                    start,
                    needs,
                )
            )
        if choices:
            _, _, _, ri, start, needs = max(choices)
            route = candidates[ri]
            reserved.update(route)
            assignments[i] = (route, start, needs)
            for c, n in needs.items():
                unallocated_stock[c] = max(
                    0, unallocated_stock.get(c, 0) - max(0, n - inv.get(c, 0))
                )
    # Generate operations and a single sequential shed ledger, including the
    # capacity made available by earlier pickups. Sales happen AFTER this ledger.
    for i, p in enumerate(positions):
        inv = private["inventories"][i]
        shed = min(access, key=lambda a: (distance(p, a), a))
        if i not in assignments or i in terminal:
            if sum(inv.values()):
                actions[i] = move_toward(p, shed) if p != shed else ["DROP"]
        else:
            route, start, needs = assignments[i]
            target = route[0]
            ops = jobs[target]["ops"]
            first_op = next(
                (v for v in ops if v[0] != "FERTILIZE" or inv.get("FERTILIZER", 0)), ["PASS"]
            )
            immediate_inputs = growth_requirements([first_op])
            can_serve_here = p == target and all(
                inv.get(c, 0) >= n for c, n in immediate_inputs.items()
            )
            missing = {
                c: n - inv.get(c, 0)
                for c, n in needs.items()
                if n > inv.get(c, 0) and stock.get(c, 0)
            }
            if can_serve_here:
                actions[i] = first_op
            elif missing:
                if p not in access:
                    actions[i] = move_toward(p, start if start in access else shed)
                else:
                    item = next(iter(missing))
                    actions[i] = ["PICKUP", item, min(missing[item], stock[item])]
            else:
                op = first_op
                actions[i] = move_toward(p, target) if p != target else op
                if p == target and op[0] == "FEED" and not inv.get("WHEAT", 0):
                    actions[i] = ["PASS"]
                if p == target and op[0] == "PLACE" and not inv.get(op[1], 0):
                    actions[i] = ["PASS"]
        op = actions[i]
        if op[0] == "PICKUP":
            amount = min(op[2], stock.get(op[1], 0))
            actions[i] = ["PICKUP", op[1], amount] if amount else ["PASS"]
            stock[op[1]] = stock.get(op[1], 0) - amount
            room += amount
        elif op[0] == "DROP":
            if sum(inv.values()) <= room:
                for item, amount in inv.items():
                    stock[item] = stock.get(item, 0) + amount
                room -= sum(inv.values())
            else:
                item = max(inv, key=lambda c: params.get(c, {}).get("base", 0))
                amount = min(room, inv[item])
                actions[i] = ["PLACE", item, amount] if amount else ["PASS"]
                stock[item] = stock.get(item, 0) + amount
                room -= amount
    return (
        actions,
        stock,
        room,
        dict(
            routes=routes,
            durations=durations,
            assigned={i: r[0] for i, r in assignments.items()},
            terminal_returns=sorted(terminal),
        ),
    )


def growth_demand(obs, cfg, date, expected=False):
    demand = observed_demand(obs, cfg)
    if not expected:
        return demand
    interval = max(1, cfg.get("townShopUnlockInterval", 3))
    count = len(obs["town"]["unlocked_shops"])
    additions = min(8 - count, max(0, date // interval - obs["day"] // interval))
    # Uniform future shop draws, with replacement. Never subtract known shops.
    for products in SHOP_PRODUCTS.values():
        for c in products:
            demand[c] += (
                additions
                * cfg.get("turnsPerDay", 24)
                / cfg.get("townShopSellInterval", 4)
                * (2 if len(products) == 1 else 1)
                / len(SHOP_PRODUCTS)
            )
    return demand


def growth_receipts(obs, cfg, params, own_flows, rival_flows, product, expected):
    day, tpd = obs["day"], cfg.get("turnsPerDay", 24)
    final = (cfg.get("episodeSteps", 720) - 2) // tpd
    inventory = obs["market"]["inventory"][product] + 12
    result = {}
    for date in range(day, final + 1):
        demand = growth_demand(obs, cfg, date, expected)[product]
        inventory -= demand * (1 - obs["hour"] / tpd if date == day else 1)
        rival = rival_flows[date][product]
        if date > day + 2 and rival > 0:
            rival = math.ceil(rival * (1.25 if expected else 1.5))
        inventory += min(0, rival)
        quantity = own_flows[date][product]
        if quantity < 0:
            result[date] = -sum(
                price_at(product, inventory - k, params) for k in range(1, -quantity + 1)
            )
            inventory += quantity
        else:
            result[date] = batch_revenue(product, inventory + max(0, rival) / 2, quantity, params)
            for _ in range(quantity):
                inventory += int(price_at(product, inventory, params) > 1)
        for _ in range(max(0, rival)):
            inventory += int(price_at(product, inventory, params) > 1)
    return result


def growth_investment(obs, cfg, params, commands, market, cash):
    report = dict(chosen=None, alternatives=[], rejected={})
    day, hour, private = obs["day"], obs["hour"], obs["private"]
    tpd = cfg.get("turnsPerDay", 24)
    final = (cfg.get("episodeSteps", 720) - 2) // tpd
    if (
        day >= final
        or hour > tpd - 4
        or hour % 4
        or sum(private["seeds"].values())
        or any(
            private["shed"].get(a, 0) or any(inv.get(a, 0) for inv in private["inventories"])
            for a in ANIMALS
        )
    ):
        return market, report
    if len(market) >= cfg.get("maxMarketOrdersPerTurn", 10):
        return market, report
    planned = planning_snapshot(obs, cfg, commands, market, params)
    own = obs["player"]
    farm = planned["farms"][own]
    assets = repaired_assets(planned)
    for group in assets:
        for tile in group:
            tile["observed"] = day
    base = [throughput_flows(group, day, final) for group in assets]
    for c in MARKET:
        base[own][day][c] += planned["private"]["shed"].get(c, 0) + sum(
            v.get(c, 0) for v in planned["private"]["inventories"]
        )
    access = shed_access(obs)
    baseline_labor = {
        d: growth_workforce(assets[own], d, final, tpd, access) for d in range(day + 1, final + 1)
    }
    baseline = {
        s: {
            c: growth_receipts(planned, cfg, params, base[own], base[1 - own], c, s) for c in MARKET
        }
        for s in (False, True)
    }
    options = []
    owned = len(farm["unlocked_quadrants"])
    room = cfg.get("shedCapacity", 100) - sum(planned["private"]["shed"].values())
    for land in (False, True):
        if land and owned >= 4:
            continue
        animal_sites, fields = growth_sites(planned, land)
        land_cost = (1000, 2000, 4000)[owned - 1] if land else 0
        prefix = [["BUY_LAND"]] if land else []
        for animal, spec in ANIMALS.items():
            free = growth_vacant(farm, animal_sites, True)
            for count in (2, 4) if land else (1, 2):
                if len(free) < count or room < count or day + 1 + spec["first_yield_day"] > final:
                    continue
                if land and not any(farm["tiles"][y][x] == "LOCKED" for x, y in free[:count]):
                    continue
                additions = [
                    dict(
                        animal=animal,
                        site=p,
                        placed_day=day + 1,
                        observed=day,
                        install=True,
                        yield_units=0,
                        pending_care_bonus=0,
                    )
                    for p in free[:count]
                ]
                options.append(
                    (
                        prefix + [["BUY_ANIMAL", animal, count]],
                        additions,
                        land_cost + count * spec["cost"],
                    )
                )
        free = growth_vacant(farm, fields)
        for crop, spec in CROPS.items():
            for count in (8, 12) if land else (1, 4, 8):
                if len(free) < count or day + 1 + spec["harvest"] > final:
                    continue
                additions = [
                    dict(
                        crop=crop,
                        site=p,
                        planted_day=day + 1,
                        observed=day,
                        plant=True,
                        yield_units=0 if spec["interval"] else 1,
                    )
                    for p in free[:count]
                ]
                if land and not any(farm["tiles"][y][x] == "LOCKED" for x, y in free[:count]):
                    continue
                options.append(
                    (
                        prefix + [["BUY_SEED", crop, count]],
                        additions,
                        land_cost + count * spec["seed"],
                    )
                )
    for orders, additions, cost in options:
        if cash < cost + 150 or len(market) + len(orders) > cfg.get("maxMarketOrdersPerTurn", 10):
            continue
        labor = {
            d: growth_workforce(assets[own] + additions, d, final, tpd, access)
            for d in baseline_labor
        }
        if not all(v["fits"] for v in labor.values()):
            report["rejected"]["capacity"] = report["rejected"].get("capacity", 0) + 1
            continue
        wages = {
            d: sum(
                hire_cost(i, cfg.get("farmHandCostMult", 1)) for i in range(labor[d]["workers"] - 1)
            )
            for d in labor
        }
        added_wages = sum(
            max(
                0,
                wages[d]
                - sum(
                    hire_cost(i, cfg.get("farmHandCostMult", 1))
                    for i in range(baseline_labor[d]["workers"] - 1)
                ),
            )
            for d in labor
        )
        immediate_wages = 0
        if hour < 6:
            immediate = [
                dict(t, **{"placed_day" if t.get("animal") else "planted_day": day})
                for t in additions
            ]
            current = growth_workforce(assets[own] + immediate, day, final, tpd, access)
            if not current["fits"]:
                continue
            paid = farm["hires_today"] + 1
            immediate_wages = sum(
                hire_cost(i, cfg.get("farmHandCostMult", 1))
                for i in range(paid - 1, current["workers"] - 1)
            )
        # Installation can finish today, one date before its conservative
        # production column. Reserve that extra feeding and any repair hires.
        early_feed = (
            sum(bool(t.get("animal")) for t in additions)
            * 2
            * price_at(
                "WHEAT", planned["market"]["inventory"]["WHEAT"] - len(additions) - 20, params
            )
        )
        setup_reserve = immediate_wages + early_feed
        extra = throughput_flows(additions, day, final)
        combined = {d: {c: base[own][d][c] + extra[d][c] for c in MARKET} for d in base[own]}
        affected = [c for c in MARKET if any(extra[d][c] for d in extra)]
        outcomes, minimum = [], cash - cost - setup_reserve
        for scenario in (False, True):
            receipts = dict(baseline[scenario])
            for c in affected:
                receipts[c] = growth_receipts(
                    planned, cfg, params, combined, base[1 - own], c, scenario
                )
            delta = sum(receipts[c][d] - baseline[scenario][c][d] for c in affected for d in extra)
            outcomes.append(delta)
            balance = cash - cost - setup_reserve
            for date in range(day, final + 1):
                # Inputs/wages are due before this date's forecast sales.
                balance += sum(min(0, receipts[c][date]) for c in MARKET) - wages.get(date, 0)
                minimum = min(minimum, balance)
                balance += sum(max(0, receipts[c][date]) for c in MARKET)
        value = 0.75 * outcomes[0] + 0.25 * outcomes[1] - cost - added_wages - setup_reserve
        option = dict(
            orders=orders,
            value=value,
            cost=cost,
            scenario_receipts=outcomes,
            min_cash=minimum,
            added_wages=added_wages,
            immediate_setup_reserve=setup_reserve,
            peak_workers=max(v["workers"] for v in labor.values()),
        )
        report["alternatives"].append(option)
    eligible = [v for v in report["alternatives"] if v["value"] > 0 and v["min_cash"] >= 150]
    if eligible:
        report["chosen"] = max(eligible, key=lambda v: (v["value"], -v["cost"]))
        market.extend(report["chosen"]["orders"])
    return market, report


def growth_turn(obs, configuration=None):
    cfg = configuration or {}
    farm, private = obs["farms"][obs["player"]], obs["private"]
    day, hour, tpd = obs["day"], obs["hour"], cfg.get("turnsPerDay", 24)
    final = (cfg.get("episodeSteps", 720) - 2) // tpd
    params = {c: dict(p) for c, p in MARKET.items()}
    for c in params:
        params[c].update(cfg.get("marketParams", {}).get(c, {}))
        params[c].update(obs["market"].get("params", {}).get(c, {}))
    assets = growth_assets(obs)
    for tile in assets:
        tile["observed"] = day
    jobs, fertilizer_wanted = growth_jobs(obs, cfg, params, assets)
    commands, stock, room, dispatch = growth_dispatch(obs, cfg, params, jobs)
    daily = growth_workforce(assets, day, final, tpd, shed_access(obs))
    held = {c: sum(inv.get(c, 0) for inv in private["inventories"]) for c in MARKET}
    for i, op in enumerate(commands):
        if op[0] == "PICKUP" and op[1] in held:
            held[op[1]] += op[2]
        elif op[0] == "DROP":
            for c, n in private["inventories"][i].items():
                if c in held:
                    held[c] -= n
        elif op[0] == "PLACE" and op[1] in held:
            held[op[1]] -= op[2]
        elif op[0] == "FEED":
            held["WHEAT"] -= 1
        elif op[0] == "FERTILIZE":
            held["FERTILIZER"] -= 1
        elif op[0] == "COLLECT_FERTILIZER":
            held["FERTILIZER"] += 1
    live = [t for t in assets if t.get("animal")]
    fed_now = sum(op[0] == "FEED" for op in commands)
    feed_target = (
        (
            sum(not t.get("fed_today", False) for t in live)
            - fed_now
            + (min(len(live), max(2, math.ceil(len(live) / 4))) if day < final - 1 else 0)
        )
        if day < final
        else 0
    )
    fert_target = (
        max(0, fertilizer_wanted - sum(op[0] == "FERTILIZE" for op in commands))
        if day < final
        else 0
    )
    keep = dict(
        WHEAT=max(0, feed_target - held["WHEAT"]),
        FERTILIZER=max(0, fert_target - held["FERTILIZER"]),
    )
    market = [
        ["SELL", c, int(n - keep.get(c, 0))]
        for c, n in stock.items()
        if c in MARKET and n > keep.get(c, 0)
    ]
    limit = cfg.get("maxMarketOrdersPerTurn", 10)
    market.sort(
        key=lambda o: (-o[2] * price_at(o[1], obs["market"]["inventory"][o[1]], params), o[1])
    )
    market = market[:limit]
    cash = farm["money"]
    # The shed has been cleared by preceding sale orders before any purchases.
    room += sum(o[2] for o in market)
    for product, goal in (("WHEAT", feed_target),):
        needed = max(0, goal - stock.get(product, 0) - held[product])
        quote = 2 * price_at(product, obs["market"]["inventory"][product] - needed - 20, params)
        count = min(needed, room, max(0, int(cash // max(1, quote))))
        if count and len(market) < limit:
            market.append(["BUY_PRODUCT", product, count])
            cash -= count * quote
            room -= count
    target = min(17, max(daily["workers"], len(dispatch["routes"])))
    if hour <= 6:
        for index in range(len(farm["hands"]), target - 1):
            cost = hire_cost(
                farm["hires_today"] + index - len(farm["hands"]), cfg.get("farmHandCostMult", 1)
            )
            if cash < cost or len(market) >= limit:
                break
            market.append(["HIRE"])
            cash -= cost
    needed = max(0, fert_target - stock.get("FERTILIZER", 0) - held["FERTILIZER"])
    if needed and day < final and hour <= 12 and len(market) < limit:
        quote = 2 * price_at(
            "FERTILIZER", obs["market"]["inventory"]["FERTILIZER"] - needed - 20, params
        )
        count = min(needed, room, max(0, int((cash - 150) // max(1, quote))))
        if count:
            market.append(["BUY_PRODUCT", "FERTILIZER", count])
            cash -= count * quote
    if day == 0 and hour == 0:
        market, investment = throughput_production(
            obs, cfg, params, market, cash, room, stock, 0, 12, True, True, True, commands
        )
    else:
        market, investment = growth_investment(obs, cfg, params, commands, market, cash)
    return dict(farmer=commands[0], hands=commands[1:], market=market), dict(
        dispatch=dispatch,
        daily=daily,
        investment=investment,
        fertilizer_target=fert_target,
        feed_target=feed_target,
    )
