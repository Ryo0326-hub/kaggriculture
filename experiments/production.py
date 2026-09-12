"""Cycle 18: deadline-aware inputs on Cycle 17's shared growth policy.

Bundled into the immutable parent namespace. Uses only the current observation
and dated task/price estimates; no environment, network or learned model.
"""

# ruff: noqa: F821


@lru_cache(maxsize=2048)
def production_routes(nodes, access, capacity, terminal=False):
    """Same insertion choices as Cycle 17, using exact incremental route costs."""
    work = {p: n for p, n, _ in nodes}
    types = sorted({c for _, _, inputs in nodes for c in inputs})
    bits = {c: 1 << i for i, c in enumerate(types)}
    masks = {p: sum(bits[c] for c in set(inputs)) for p, _, inputs in nodes}
    start = {p: max(distance(a, p) for a in access) for p in work}
    finish = {p: min(distance(p, a) for a in access) + 1 if terminal else 0 for p in work}
    edges = {(a, b): distance(a, b) for a in work for b in work}
    routes, lengths, loads = [], [], []
    for site in sorted(work, key=lambda p: (-min(distance(p, a) for a in access), p)):
        best = None
        for i, route in enumerate(routes):
            extra = work[site] + (loads[i] | masks[site]).bit_count() - loads[i].bit_count()
            for at in range(len(route) + 1):
                if at == 0:
                    detour = start[site] - start[route[0]] + edges[site, route[0]]
                elif at == len(route):
                    detour = edges[route[-1], site] + finish[site] - finish[route[-1]]
                else:
                    a, b = route[at - 1], route[at]
                    detour = edges[a, site] + edges[site, b] - edges[a, b]
                length = lengths[i] + extra + detour
                if length <= capacity:
                    proposed = (*route[:at], site, *route[at:])
                    option = (length - lengths[i], length, i, proposed)
                    if best is None or option < best:
                        best = option
        if best is None:
            routes.append((site,))
            lengths.append(start[site] + finish[site] + work[site] + masks[site].bit_count())
            loads.append(masks[site])
        else:
            _, length, i, proposed = best
            routes[i], lengths[i], loads[i] = proposed, length, loads[i] | masks[site]
    ordered = sorted(zip(routes, lengths))
    return (
        tuple(r for r, _ in ordered),
        tuple(n for _, n in ordered),
        all(n <= capacity for _, n in ordered),
    )


def production_fertilizer_plan(obs, cfg, params):
    """Reserve one profitable application per site, today or tomorrow.

    An application lasts through day+2; the next callback recomputes coverage.
    Tomorrow's requirements are staged before overnight deposits, rather than
    selling every surplus unit on the day before a large production cohort.
    """
    day, tpd = obs["day"], cfg.get("turnsPerDay", 24)
    final = (cfg.get("episodeSteps", 720) - 2) // tpd
    requests = []
    for row in obs["farms"][obs["player"]]["tiles"]:
        for tile in row:
            if not isinstance(tile, dict) or tile.get("crop") not in CROPS:
                continue
            for date in range(day, min(day + 1, final - 1) + 1):
                future = dict(obs, day=date, hour=obs["hour"] if date == day else 0)
                state = dict(tile)
                if date > day:
                    state["watered_today"] = False
                value = timing_fertilizer_value(state, future, cfg, params)
                if value > 0:
                    requests.append(dict(tile=tile, deadline=date, value=value))
                    break
    # Store coordinates rather than object identity in reports or dispatch.
    by_tile = {id(r["tile"]): r for r in requests}
    result = {}
    for y, row in enumerate(obs["farms"][obs["player"]]["tiles"]):
        for x, tile in enumerate(row):
            if id(tile) in by_tile:
                r = by_tile[id(tile)]
                result[x, y] = dict(deadline=r["deadline"], value=r["value"])
    return result


def production_jobs(obs, cfg, params, assets, fertilizer_plan):
    jobs, _ = growth_jobs(obs, cfg, params, assets)
    for job in jobs.values():
        job["maintenance_priority"] = job["priority"]
    day, tpd = obs["day"], cfg.get("turnsPerDay", 24)
    remaining = min(
        tpd - obs["hour"],
        cfg.get("episodeSteps", 720) - 1 - obs.get("step", day * tpd + obs["hour"]),
    )
    for site, request in fertilizer_plan.items():
        if request["deadline"] != day:
            continue
        tile = obs["farms"][obs["player"]]["tiles"][site[1]][site[0]]
        # Optional input cannot use the sole action needed for survival water.
        needs_water = not tile["watered_today"]
        if remaining < 1 + int(needs_water):
            continue
        job = jobs.setdefault(site, dict(ops=[], priority=1, asset=dict(tile, site=site)))
        if ["FERTILIZE"] not in job["ops"]:
            job["ops"].insert(0, ["FERTILIZE"])
        job["fertilizer_value"] = request["value"]
        job["priority"] = max(job["priority"], 180 + min(40, request["value"] / 10))
    return jobs


def production_carried_after(obs, commands):
    """Account only for carried inputs, in the engine's unit-before-market order."""
    result = [dict(inv) for inv in obs["private"]["inventories"]]
    for i, op in enumerate(commands):
        inv = result[i]
        if op[0] == "PICKUP":
            inv[op[1]] = inv.get(op[1], 0) + op[2]
        elif op[0] == "DROP":
            inv.clear()
        elif op[0] == "PLACE":
            inv[op[1]] = inv.get(op[1], 0) - (op[2] if len(op) == 3 else 1)
        elif op[0] in ("FEED", "FERTILIZE"):
            item = "WHEAT" if op[0] == "FEED" else "FERTILIZER"
            inv[item] = inv.get(item, 0) - 1
        elif op[0] == "COLLECT_FERTILIZER":
            inv["FERTILIZER"] = inv.get("FERTILIZER", 0) + 1
        elif op[0] == "HARVEST":
            farm = obs["farms"][obs["player"]]
            x, y = [farm["farmer"], *farm["hands"]][i]
            tile = farm["tiles"][y][x]
            item = tile.get("crop") or ANIMALS[tile["animal"]]["product"]
            inv[item] = inv.get(item, 0) + tile["yield_units"]
    return result


def production_fertilizer_reserve(obs, commands, dispatch, plan):
    """Carried fertilizer offsets today's depot stock only on a funded route.

    Other carried fertilizer can cover tomorrow through the normal night deposit,
    but cannot cancel today's missing pickup. Each unit and site is credited once.
    """
    positions = [obs["farms"][obs["player"]]["farmer"], *obs["farms"][obs["player"]]["hands"]]
    applied = {tuple(p) for p, op in zip(positions, commands) if op[0] == "FERTILIZE"}
    today = {p for p, r in plan.items() if r["deadline"] == obs["day"] and p not in applied}
    tomorrow = sum(r["deadline"] > obs["day"] for r in plan.values())
    carried = production_carried_after(obs, commands)
    credit, assigned = 0, set()
    for i, inv in enumerate(carried):
        sites = [
            p
            for p in dispatch.get("fertilizer_sites", {}).get(i, ())
            if p in today and p not in assigned
        ]
        count = min(max(0, inv.get("FERTILIZER", 0)), len(sites))
        credit += count
        assigned.update(sites[:count])
    total = sum(inv.get("FERTILIZER", 0) for inv in carried)
    depot = len(today) - credit + max(0, tomorrow - max(0, total - credit))
    return dict(
        depot_target=depot,
        today=len(today),
        tomorrow=tomorrow,
        credited_on_routes=credit,
        carried=total,
    )


def production_feed_reserve(obs, cfg, commands, dispatch, assets):
    """Feed on an unrelated worker cannot cancel a hungry route's pickup."""
    final = (cfg.get("episodeSteps", 720) - 2) // cfg.get("turnsPerDay", 24)
    if obs["day"] == final:
        return dict(depot_target=0, today=0, tomorrow=0, credited_on_routes=0)
    farm = obs["farms"][obs["player"]]
    positions = [farm["farmer"], *farm["hands"]]
    fed = {tuple(p) for p, op in zip(positions, commands) if op[0] == "FEED"}
    live = [t for t in assets if t.get("animal")]
    hungry = {
        tuple(t["site"]) for t in live if not t.get("fed_today") and tuple(t["site"]) not in fed
    }
    carried = production_carried_after(obs, commands)
    credit, assigned = 0, set()
    for i, inv in enumerate(carried):
        sites = [
            p
            for p in dispatch.get("feed_sites", {}).get(i, ())
            if p in hungry and p not in assigned
        ]
        count = min(max(0, inv.get("WHEAT", 0)), len(sites))
        assigned.update(sites[:count])
        credit += count
    tomorrow = min(len(live), max(2, math.ceil(len(live) / 4))) if obs["day"] < final - 1 else 0
    spare = max(0, sum(inv.get("WHEAT", 0) for inv in carried) - credit)
    return dict(
        depot_target=len(hungry) - credit + max(0, tomorrow - spare),
        today=len(hungry),
        tomorrow=tomorrow,
        credited_on_routes=credit,
    )


def production_route_ops(route, jobs, inv, stock):
    """Fund optional applications by marginal value, retaining mandatory jobs."""
    fertilizer = inv.get("FERTILIZER", 0) + stock.get("FERTILIZER", 0)
    fertile = sorted(
        (p for p in route if ["FERTILIZE"] in jobs[p]["ops"]),
        key=lambda p: (-jobs[p].get("fertilizer_value", 0), p),
    )
    funded = set(fertile[:fertilizer])
    return {p: [op for op in jobs[p]["ops"] if op[0] != "FERTILIZE" or p in funded] for p in route}


def production_service_variants(route, route_ops, jobs, terminal):
    """Keep feasible bundles; salvage essential service when travel makes them late."""
    yield route_ops
    if len(route) != 1:
        return
    site = route[0]
    ops = route_ops[site]
    if any(op[0] in ("PLANT", "PLACE", "BUILD_COOP", "BUILD_PASTURE") for op in ops):
        return  # Never split installation from its first water/feed.
    if terminal:
        if ["HARVEST"] in ops and ops != [["HARVEST"]]:
            yield {site: [["HARVEST"]]}
        return  # Every variant still needs this worker's harvest + delivery time.
    asset = jobs[site]["asset"]
    one_time = asset.get("crop") and not CROPS[asset["crop"]]["interval"]
    # Harvest removes a mature one-time crop; ongoing crops still need water.
    priorities = ("FEED", "HARVEST", "WATER") if one_time else ("FEED", "WATER", "HARVEST")
    for name in (*priorities, "FERTILIZE", "COLLECT_FERTILIZER", "CARE"):
        if [name] in ops and ops != [[name]]:
            if name == "FERTILIZE" and ["WATER"] in ops:
                continue  # A bonus alone cannot replace this day's water.
            yield {site: [[name]]}


def production_route_fit(p, inv, stock, route, route_ops, access, remaining, terminal):
    """Check one worker's travel, pickups, service and final delivery budget."""
    needs = growth_requirements([op for q in route for op in route_ops[q]])
    missing = {c: n - inv.get(c, 0) for c, n in needs.items() if n > inv.get(c, 0)}
    if any(n > stock.get(c, 0) for c, n in missing.items()):
        return None
    held_animals = [a for a in ANIMALS if inv.get(a, 0)]
    if held_animals and not any(needs.get(a, 0) for a in held_animals):
        return None
    start = min(access, key=lambda a: (distance(p, a) + distance(a, route[0]), a)) if missing else p
    travel = distance(p, start) + distance(start, route[0])
    length = (
        travel
        + len(missing)
        + sum(distance(a, b) for a, b in zip(route, route[1:]))
        + sum(len(route_ops[q]) for q in route)
        + (min(distance(route[-1], a) for a in access) + 1 if terminal else 0)
    )
    return (start, needs, travel, length) if length <= remaining else None


def production_dispatch(obs, cfg, params, jobs):
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
        key=lambda i: (
            not any(private["inventories"][i].get(a, 0) for a in ANIMALS),
            not private["inventories"][i].get("FERTILIZER", 0),
            not private["inventories"][i].get("WHEAT", 0),
            i,
        ),
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
            route_ops = production_route_ops(route, jobs, inv, unallocated_stock)
            route = tuple(q for q in route if route_ops[q])
            if not route:
                continue
            fit = None
            for variant in production_service_variants(route, route_ops, jobs, day == final):
                fit = production_route_fit(
                    p, inv, unallocated_stock, route, variant, access, remaining, day == final
                )
                if fit is not None:
                    route_ops = variant
                    break
            if fit is None:
                continue
            start, needs, travel, length = fit
            urgency = max(
                jobs[q]["priority"]
                if ["FERTILIZE"] in route_ops[q]
                else jobs[q].get("maintenance_priority", jobs[q]["priority"])
                for q in route
            )
            local = p == route[0]
            choices.append(
                (
                    urgency
                    + 30 * local
                    + 5 * len(route)
                    - 4 * travel
                    + 20 * min(inv.get("FERTILIZER", 0), needs.get("FERTILIZER", 0)),
                    -length,
                    -route_index,
                    route_index,
                    start,
                    needs,
                    route,
                    route_ops,
                )
            )
        if choices:
            _, _, _, _, start, needs, route, route_ops = max(choices, key=lambda v: v[:3])
            reserved.update(route)
            assignments[i] = (route, start, needs, route_ops)
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
            route, start, needs, route_ops = assignments[i]
            target = route[0]
            # Funded fertilizer remains an input requirement until picked up.
            # Skipping it here would water first and trigger an avoidable return.
            first_op = route_ops[target][0]
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
                tile = farm["tiles"][p[1]][p[0]]
                depositable = [
                    c
                    for c, n in inv.items()
                    if n > 0
                    and not (
                        c in ANIMALS
                        and isinstance(tile, dict)
                        and tile.get("kind") == ANIMALS[c]["structure"]
                        and "animal" not in tile
                    )
                ]
                # PLACE on a matching empty pen installs ONE animal, regardless
                # of its quantity argument. Never mistake that for a deposit.
                if not depositable:
                    actions[i] = ["PASS"]
                    continue
                item = max(depositable, key=lambda c: params.get(c, {}).get("base", 0))
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
            fertilizer_sites={
                i: tuple(p for p in r[0] if ["FERTILIZE"] in r[3][p])
                for i, r in assignments.items()
            },
            feed_sites={
                i: tuple(p for p in r[0] if ["FEED"] in r[3][p]) for i, r in assignments.items()
            },
            terminal_returns=sorted(terminal),
        ),
    )


def production_turn(obs, configuration=None):
    cfg = configuration or {}
    farm = obs["farms"][obs["player"]]
    day, hour, tpd = obs["day"], obs["hour"], cfg.get("turnsPerDay", 24)
    final = (cfg.get("episodeSteps", 720) - 2) // tpd
    params = {c: dict(p) for c, p in MARKET.items()}
    for c in params:
        params[c].update(cfg.get("marketParams", {}).get(c, {}))
        params[c].update(obs["market"].get("params", {}).get(c, {}))
    assets = growth_assets(obs)
    for tile in assets:
        tile["observed"] = day
    fertilizer_plan = production_fertilizer_plan(obs, cfg, params)
    jobs = production_jobs(obs, cfg, params, assets, fertilizer_plan)
    commands, stock, room, dispatch = production_dispatch(obs, cfg, params, jobs)
    daily = growth_workforce(assets, day, final, tpd, shed_access(obs))
    carried = production_carried_after(obs, commands)
    fertilizer = production_fertilizer_reserve(obs, commands, dispatch, fertilizer_plan)
    feed = production_feed_reserve(obs, cfg, commands, dispatch, assets)
    feed_target = feed["depot_target"]
    fert_target = fertilizer["depot_target"] if day < final else 0
    keep = dict(WHEAT=feed_target, FERTILIZER=fert_target)
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
    # Bought stock must also fit beside goods already carried toward the night
    # deposit; seeds bypass the shed and are unaffected by this bound.
    room = max(0, room - sum(sum(inv.values()) for inv in carried))
    for product, goal in (("WHEAT", feed_target),):
        needed = max(0, goal - stock.get(product, 0))
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
    needed = max(0, fert_target - stock.get("FERTILIZER", 0))
    # After midday only restock tomorrow's wave; a last-minute purchase cannot
    # service a field in the same action in which the market accepts it.
    can_restock = hour <= 12 or (hour <= tpd - 4 and fertilizer["tomorrow"] > 0)
    if needed and day < final and can_restock and len(market) < limit:
        quote = 2 * price_at(
            "FERTILIZER", obs["market"]["inventory"]["FERTILIZER"] - needed - 20, params
        )
        count = min(needed, room, max(0, int((cash - 150) // max(1, quote))))
        if count:
            market.append(["BUY_PRODUCT", "FERTILIZER", count])
            cash -= count * quote
            room -= count
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
        fertilizer_reserve=fertilizer,
        feed_target=feed_target,
        feed_reserve=feed,
    )
