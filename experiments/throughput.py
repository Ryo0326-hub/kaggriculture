"""Cycle 13: extend our Cycle 12 dispatcher with priced production capacity.

Bundled into its namespace; no replay data, network, model, or hidden seed access.
The forecasts below are deterministic accounting estimates, not game rollouts.
"""

# ruff: noqa: F821


def throughput_sites(obs, extra_land=False):
    """Stage livestock capacity with paid land instead of stranding opening crop tiles."""
    farm = obs["farms"][obs["player"]]
    size, access = len(farm["tiles"]), shed_access(obs)
    half = size // 2
    northwest = sorted(
        [(x, y) for y in range(half) for x in range(half)],
        key=lambda p: (distance(p, access[0]), p),
    )[:5]
    northeast = sorted(
        [(x, y) for y in range(half) for x in range(half, size)],
        key=lambda p: (min(distance(p, a) for a in access), p),
    )[:7]
    owned = len(farm["unlocked_quadrants"])
    next_quadrant = ("NW", "NE", "SW", "SE")[owned] if owned < 4 else None
    reserved = set(northwest + northeast)
    fields = []
    for y, row in enumerate(farm["tiles"]):
        for x, tile in enumerate(row):
            quadrant = ("N" if y < half else "S") + ("W" if x < half else "E")
            if (x, y) not in reserved and (
                tile != "LOCKED" or extra_land and quadrant == next_quadrant
            ):
                fields.append((x, y))
    fields.sort(key=lambda p: (min(distance(p, a) for a in access), p))
    return northwest + (northeast if owned >= 2 or extra_land else []), fields


def throughput_crop_job(tile, day, final):
    if not isinstance(tile, dict):
        return None
    crop, age = tile.get("crop"), day - tile.get("planted_day", day)
    if crop == "TOMATO":
        units = tile.get("yield_units", 0)
        if units and (age >= 11 or day == final or units >= 3):
            return "HARVEST", 280, 1
        if (
            day < final
            and not tile.get("watered_today")
            and (tile.get("consecutive_unwatered", 0) or 7 <= age <= 10)
        ):
            return "WATER", 150 if tile.get("consecutive_unwatered", 0) else 100, 1
        if units:
            return "HARVEST", 120, 1
        if age >= 11:
            return "DIG", 10, 1
        return None
    # A five-unit age-three wheat crop gains at most one more unit by waiting.
    # Only the fertilized branch accelerates: ordinary wheat retains Cycle 3 timing.
    if crop == "WHEAT" and age >= 3 and tile.get("yield_units", 0) >= 5 and day + 5 <= final:
        return "HARVEST", 250, 1
    return inherited_crop_job(tile, day, final)


def throughput_column(crop, planted, final, fertilized=False, tile=None, today=0):
    if (
        crop == "WHEAT"
        and tile
        and tile.get("yield_units", 0) >= 5
        and today - planted >= 3
        and today + 5 <= final
    ):
        return {
            "crop": crop,
            "planted_day": planted,
            "end": today,
            "outputs": {today: tile["yield_units"]},
            "fertilizer": [],
            "work": {},
            "fertilized": False,
        }
    if crop != "TOMATO":
        column = inherited_crop_column(crop, planted, final, fertilized, tile, today)
        if crop == "WHEAT" and column:
            state = tile or {"yield_units": 1}
            quantity = state.get("yield_units", 1)
            expiry = state.get("fertilized_until_day", -1)
            for date in range(max(today, planted + 2), min(final, planted + 4) + 1):
                if date in column["fertilizer"]:
                    expiry = date + 2
                if not (date == today and state.get("watered_today")):
                    quantity = min(6, quantity + (2 if expiry >= date else 1))
                if date - planted >= 3 and quantity >= 5 and date + 5 <= final:
                    column.update(end=date, outputs={date: quantity})
                    break
        return column
    outputs = {}
    if tile and tile.get("yield_units", 0):
        outputs[today] = tile["yield_units"]
    for age in range(8, 12):
        date = planted + age
        if today < date <= final:
            # Admission promises base output only; fertilizer is a later priced option.
            outputs[date] = 1
    if not outputs:
        return None
    return {
        "crop": crop,
        "planted_day": planted,
        "end": max(outputs),
        "outputs": outputs,
        "fertilizer": [],
        "work": {},
        "fertilized": False,
    }


def throughput_fertilizer(tile, obs, cfg, params):
    if tile.get("crop") != "TOMATO":
        return inherited_timing_fertilizer(tile, obs, cfg, params)
    day = obs["day"]
    final = (cfg.get("episodeSteps", 720) - 2) // cfg.get("turnsPerDay", 24)
    if tile.get("fertilized_until_day", -1) >= day or tile.get("yield_units", 0) >= 3:
        return 0
    age = day - tile["planted_day"]
    if not 7 <= age <= 10:
        return 0
    events = min(3, 11 - age, final - day)
    inv = obs["market"]["inventory"]
    gain = 0.8 * batch_revenue("TOMATO", inv["TOMATO"] + 12, events, params)
    return gain - price_at("FERTILIZER", inv["FERTILIZER"], params) - 16


def throughput_route_cover(sites, service_steps, access, capacity, dedicated=()):
    # Reuse our Step 8 insertion tours for herd service too. A producing animal
    # needs a harvest action, not necessarily an entire dedicated worker.
    return farm_tours(tuple(zip(sites, service_steps)), access, capacity)


def throughput_service(tile, date, final):
    if "animal" in tile:
        if date < tile["placed_day"]:
            return 0
        if date == tile["placed_day"]:
            return 7  # pickup, travel allowance, build/place, first feed/care
        return 2 if date == final else 5  # feed/care/fertilizer/harvest plus shared travel
    spec = CROPS[tile["crop"]]
    age = date - tile["planted_day"]
    end = spec["harvest"] + (spec["events"] - 1) * spec["interval"]
    if age < 0 or age > end:
        return 0
    if age == 0:
        return 5  # plant, water, clearance/input/travel allowance
    if spec["interval"]:
        producing = age >= spec["first"] and (age - spec["first"]) % spec["interval"] == 0
        return 4 if producing else 3
    return 4 if age >= spec["first"] else 2


def throughput_workers(tiles, date, final, tpd=24):
    work = sum(throughput_service(t, date, final) for t in tiles)
    return max(1, math.ceil(work / max(1, tpd - 5)))


def throughput_staff(obs, cfg, livestock_workers, pending):
    farm = obs["farms"][obs["player"]]
    day, tpd = obs["day"], cfg.get("turnsPerDay", 24)
    final = (cfg.get("episodeSteps", 720) - 2) // tpd
    tiles = [
        t
        for row in farm["tiles"]
        for t in row
        if isinstance(t, dict) and (t.get("animal") or t.get("crop") in CROPS)
    ]
    crops = [
        ((x, y), t)
        for y, row in enumerate(farm["tiles"])
        for x, t in enumerate(row)
        if isinstance(t, dict) and t.get("crop") in CROPS
    ]
    # Independent crop tours prevent assuming all herd-worker time is available
    # before water deadlines. This also provides a workload-driven repair hire.
    nodes = tuple(
        (p, max(2, crop_job(t, day, final)[2])) for p, t in crops if crop_job(t, day, final)
    )
    tours = farm_tours(nodes, tuple(shed_access(obs)), max(1, tpd - 3))[0]
    target = max(
        throughput_workers(tiles, day, final, tpd),
        livestock_workers + len(tours) + math.ceil(pending / 5),
    )
    # 11 paid hands cost 232/day; the 12th costs another 144. Keep the same
    # 12-worker ceiling in admission and execution, while retaining paid workers.
    return min(12, target)


def throughput_assets(obs):
    return [
        [
            dict(t)
            for row in f["tiles"]
            for t in row
            if isinstance(t, dict) and (t.get("animal") or t.get("crop") in CROPS)
        ]
        for f in obs["farms"]
    ]


def throughput_flows(assets, day, final):
    flows = {d: {c: 0 for c in MARKET} for d in range(day, final + 1)}
    for tile in assets:
        if "animal" in tile:
            product = ANIMALS[tile["animal"]]["product"]
            for date, (units, fert) in zip(range(day, final + 1), animal_output(tile, day, final)):
                flows[date][product] += units
                flows[date]["FERTILIZER"] += fert
                if tile["placed_day"] <= date < final:
                    flows[date]["WHEAT"] -= int(date > day or not tile.get("fed_today", False))
        else:
            col = crop_column(tile["crop"], tile["planted_day"], final, False, tile, day)
            if col:
                for date, units in col["outputs"].items():
                    flows[date][tile["crop"]] += units
    return flows


def throughput_value(obs, cfg, params, base, extra, additions, cost, assets):
    """Marginal own cash INCLUDING price impact on existing own production.

    Two demand scenarios value dated physical flows. Future shop draws, actions,
    weed RNG and counterfactual games are never generated.
    """
    day, own = obs["day"], obs["player"]
    tpd = cfg.get("turnsPerDay", 24)
    final = (cfg.get("episodeSteps", 720) - 2) // tpd
    demand = observed_demand(obs, cfg)
    affected = [c for c in MARKET if any(extra[d][c] for d in extra)]
    outcomes = []
    for fraction, rival_growth in ((1.0, 1.0), (0.5, 1.5)):
        difference = 0
        for product in affected:
            # Opponent inventory is hidden: buffer future supply, never read its private state.
            inventory = [obs["market"]["inventory"][product] + 12] * 2
            for date in range(day, final + 1):
                rival = base[1 - own][date][product]
                if date > day + 2 and rival > 0:
                    rival = math.ceil(rival * rival_growth)
                for branch in (0, 1):
                    inventory[branch] -= (
                        fraction * demand[product] * (1 - obs["hour"] / tpd if date == day else 1)
                    )
                    quantity = base[own][date][product] + branch * extra[date][product]
                    inventory[branch] += min(0, rival)
                    if quantity < 0:
                        # Post-decrement buy quote, charged once; wheat has no double credit.
                        receipt = -sum(
                            price_at(product, inventory[branch] - k, params)
                            for k in range(1, -quantity + 1)
                        )
                        inventory[branch] += quantity
                    else:
                        receipt = batch_revenue(
                            product, inventory[branch] + max(0, rival) / 2, quantity, params
                        )
                        for _ in range(quantity):
                            inventory[branch] += int(
                                price_at(product, inventory[branch], params) > 1
                            )
                    for _ in range(max(0, rival)):
                        inventory[branch] += int(price_at(product, inventory[branch], params) > 1)
                    difference += (1 if branch else -1) * receipt
        outcomes.append(difference)
    wages = work = 0
    feasible = True
    for date in range(day + 1, final + 1):
        before = throughput_workers(assets, date, final, tpd)
        after = throughput_workers(assets + additions, date, final, tpd)
        feasible &= after <= 12
        wages += sum(
            hire_cost(i, cfg.get("farmHandCostMult", 1)) for i in range(before - 1, after - 1)
        )
        work += sum(throughput_service(t, date, final) for t in additions)
    # Retain 75% of the worse estimated revenue change. No optimized/game-theoretic guarantee.
    value = min(outcomes) * 0.75 - cost - wages
    return {
        "value": value,
        "scenario_receipts": outcomes,
        "added_wages": wages,
        "work": work,
        "capacity_estimate_fits": bool(feasible),
        "score": value / max(1, work),
    }


def throughput_investment(obs, cfg, params, commands, market, max_land=3):
    report = {"chosen": None, "alternatives": []}
    day, hour, own = obs["day"], obs["hour"], obs["player"]
    farm, private = obs["farms"][own], obs["private"]
    final = (cfg.get("episodeSteps", 720) - 2) // cfg.get("turnsPerDay", 24)
    if (
        hour > 6
        or len(market) >= cfg.get("maxMarketOrdersPerTurn", 10)
        or day >= final
        or sum(private["seeds"].values())
        or any(
            private["shed"].get(a, 0) or any(v.get(a, 0) for v in private["inventories"])
            for a in ANIMALS
        )
    ):
        return market, report
    planned = planning_snapshot(obs, cfg, commands, market, params)
    assets = throughput_assets(planned)
    base = [throughput_flows(group, day, final) for group in assets]
    for product in MARKET:
        base[own][day][product] += planned["private"]["shed"].get(product, 0) + sum(
            v.get(product, 0) for v in planned["private"]["inventories"]
        )
    animal_sites, fields = farm_sites(obs)
    live = sum("animal" in t for t in assets[own])
    # Ring-fence next-day inputs and wages after already issued orders. Do not
    # spend every coin just because a long-horizon value estimate is positive.
    wheat = planned["private"]["shed"].get("WHEAT", 0) + sum(
        v.get("WHEAT", 0) for v in planned["private"]["inventories"]
    )
    target = throughput_workers(assets[own], day + 1, final, cfg.get("turnsPerDay", 24))
    reserve = (
        150
        + max(0, live - wheat)
        * 2
        * price_at("WHEAT", obs["market"]["inventory"]["WHEAT"] - live - 20, params)
        + sum(hire_cost(i, cfg.get("farmHandCostMult", 1)) for i in range(target - 1))
    )
    cash = planned["farms"][own]["money"]
    room = cfg.get("shedCapacity", 100) - sum(planned["private"]["shed"].values())

    def vacant(sites):
        return [
            p
            for p in sites
            if farm["tiles"][p[1]][p[0]] in (None, "LOCKED")
            or isinstance(farm["tiles"][p[1]][p[0]], dict)
            and farm["tiles"][p[1]][p[0]].get("kind") in ("WEED", "COOP", "PASTURE")
            and not farm["tiles"][p[1]][p[0]].get("animal")
        ]

    options = []
    free = vacant(animal_sites)
    if free and room > 0:
        for animal, spec in ANIMALS.items():
            if day + 2 + spec["first_yield_day"] > final:
                continue
            options.append(
                (
                    [["BUY_ANIMAL", animal, 1]],
                    [
                        dict(
                            animal=animal,
                            placed_day=day + 1,
                            site=free[0],
                            yield_units=0,
                            pending_care_bonus=0,
                        )
                    ],
                    spec["cost"],
                )
            )
    owned = len(farm["unlocked_quadrants"])
    for extra_land in (False, True):
        if extra_land and (owned >= max_land or len(vacant(fields)) > 4):
            continue
        sites = vacant(farm_sites(obs, extra_land)[1])
        land = (1000, 2000, 4000)[owned - 1] if extra_land else 0
        # Owned plots use small batches. A land purchase can fund eight real
        # plantings so the entire fixed land charge is not assigned to one crop.
        for count in (4, 8) if extra_land else (1, 4):
            if (
                len(sites) < count
                or extra_land
                and not any(farm["tiles"][y][x] == "LOCKED" for x, y in sites[:count])
            ):
                continue
            for crop, spec in CROPS.items():
                if day + 1 + spec["harvest"] > final:
                    continue
                if crop in ("CARROT", "TOMATO") and observed_demand(obs, cfg)[crop] <= 1:
                    continue
                columns = [
                    dict(
                        crop=crop,
                        planted_day=day + 1,
                        site=p,
                        yield_units=0 if spec["interval"] else 1,
                    )
                    for p in sites[:count]
                ]
                orders = ([["BUY_LAND"]] if extra_land else []) + [["BUY_SEED", crop, count]]
                options.append((orders, columns, land + count * spec["seed"]))
    for orders, additions, cost in options:
        # A fresh animal's first feed is additional to incumbent operating reserves.
        first_feed = 2 * price_at("WHEAT", obs["market"]["inventory"]["WHEAT"] - 20, params)
        if cash < reserve + cost + (first_feed if "animal" in additions[0] else 0):
            continue
        if len(market) + len(orders) > cfg.get("maxMarketOrdersPerTurn", 10):
            continue
        extra = throughput_flows(additions, day, final)
        value = throughput_value(planned, cfg, params, base, extra, additions, cost, assets[own])
        option = dict(value, orders=orders, cost=cost, reserve=reserve)
        report["alternatives"].append(option)
    feasible = [a for a in report["alternatives"] if a["value"] > 0 and a["capacity_estimate_fits"]]
    if feasible:
        chosen = max(feasible, key=lambda a: (a["score"], a["value"]))
        market.extend(chosen["orders"])
        report["chosen"] = chosen
    return market, report


def throughput_production(
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
    if obs["day"] == 0 and obs["hour"] == 0:
        # Keep our existing joint livestock/melon opening. Add only cheap wheat
        # to free reserved crop slots, never displace its admitted animal bundle.
        result, report = inherited_production_orders(
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
        )
        spent = sum(
            CROPS[o[1]]["seed"] * o[2]
            if o[0] == "BUY_SEED"
            else ANIMALS[o[1]]["cost"] * o[2]
            if o[0] == "BUY_ANIMAL"
            else 0
            for o in result
        )
        planted = sum(o[2] for o in result if o[0] == "BUY_SEED")
        n = min(4, len(farm_sites(obs)[1]) - planted, max(0, int((cash - spent - 200) // 10)))
        if n > 0 and len(result) < cfg.get("maxMarketOrdersPerTurn", 10):
            result.append(["BUY_SEED", "WHEAT", n])
        report["wheat_opening_addition"] = n
        return result, report
    return throughput_investment(obs, cfg, params, commands, market)
