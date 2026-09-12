"""Cycle 15 correctness repairs, bundled after the unchanged Cycle 13 helpers.

These are dated cash/work estimates and one-observation decisions, not rollouts.
"""

# ruff: noqa: F821


def repaired_crop_job(tile, day, final):
    if isinstance(tile, dict) and tile.get("crop") == "TOMATO":
        age = day - tile["planted_day"]
        # A harvest does not prevent overnight death. Preserve the remaining
        # production events before collecting a nearly full tomato plant.
        if (
            day < final
            and age < 11
            and not tile.get("watered_today")
            and tile.get("consecutive_unwatered", 0) >= 1
        ):
            return "WATER", 290, 1
    return throughput_crop_job(tile, day, final)


def repaired_column(crop, planted, final, fertilized=False, tile=None, today=0):
    column = throughput_column(crop, planted, final, fertilized, tile, today)
    if crop == "TOMATO" and column:
        expiry = (tile or {}).get("fertilized_until_day", -1)
        for date in column["outputs"]:
            if date > today:
                # The production night uses the PREVIOUS day's water and expiry.
                # Maintenance is budgeted, but no future fertilizer purchase is assumed.
                column["outputs"][date] = 2 if expiry >= date - 1 else 1
        column["fertilized"] = expiry >= today
    return column


def repaired_assets(obs):
    return [
        [
            dict(t, site=(x, y))
            for y, row in enumerate(farm["tiles"])
            for x, t in enumerate(row)
            if isinstance(t, dict) and (t.get("animal") or t.get("crop") in CROPS)
        ]
        for farm in obs["farms"]
    ]


def repaired_workforce(assets, date, final, tpd=24, access=((4, 4), (4, 5), (5, 4), (5, 5))):
    """One site-aware daily crew contract for admission, reserves and hiring.

    Service bounds stay stable as today's tasks finish. Installation temporarily
    uses station crews, matching the installation dispatcher. Crop tours include
    travel, two daily service actions and the inherited pickup/deposit allowance.
    Return the UNCLIPPED requirement so infeasible investments cannot hide at 12.
    """
    animals = [t for t in assets if t.get("animal") and t["placed_day"] <= date]
    animal_nodes = tuple(
        (tuple(t["site"]), 2 if date == final else 3 if date == final - 1 else 4) for t in animals
    )
    capacity = max(1, tpd - 3 - int(date == final))
    herd, _, herd_fits = farm_tours(animal_nodes, tuple(access), capacity)
    installing = any(t["placed_day"] == date for t in animals)
    herd_workers = len(animals) if installing else len(herd)
    crops = []
    for tile in assets:
        if tile.get("crop") not in CROPS:
            continue
        spec = CROPS[tile["crop"]]
        age = date - tile["planted_day"]
        end = spec["harvest"] + (spec["events"] - 1) * spec["interval"]
        if 0 <= age <= end:
            crops.append((tuple(tile["site"]), 3 if age == 0 else 2))
    routes, _, crop_fits = farm_tours(tuple(crops), tuple(access), capacity)
    workers = max(1, herd_workers + len(routes))
    return {"workers": workers, "fits": herd_fits and crop_fits and workers <= 12}


def repaired_staff(obs, cfg, livestock_workers, pending):
    private = obs["private"]
    day, tpd = obs["day"], cfg.get("turnsPerDay", 24)
    final = (cfg.get("episodeSteps", 720) - 2) // tpd
    assets = repaired_assets(obs)[obs["player"]]
    # Reserve actual pending installations in the same geometry as new purchases.
    animals, fields = farm_sites(obs)
    occupied = {tuple(t["site"]) for t in assets}
    free_animals = [p for p in animals if p not in occupied]
    for animal in ANIMALS:
        count = private["shed"].get(animal, 0) + sum(
            inv.get(animal, 0) for inv in private["inventories"]
        )
        for _ in range(count):
            if free_animals:
                assets.append(dict(animal=animal, placed_day=day, site=free_animals.pop(0)))
    free_fields = [p for p in fields if p not in occupied]
    for crop, count in private["seeds"].items():
        if crop in CROPS:
            for _ in range(count):
                if free_fields:
                    assets.append(dict(crop=crop, planted_day=day, site=free_fields.pop(0)))
    model = repaired_workforce(assets, day, final, tpd, shed_access(obs))
    return min(12, model["workers"])


def repaired_labor_delta(obs, cfg, assets, additions):
    day, tpd = obs["day"], cfg.get("turnsPerDay", 24)
    final = (cfg.get("episodeSteps", 720) - 2) // tpd
    access = shed_access(obs)
    wages = work = 0
    fits = True
    next_wages = 0
    for date in range(day + 1, final + 1):
        before = repaired_workforce(assets, date, final, tpd, access)
        after = repaired_workforce(assets + additions, date, final, tpd, access)
        fits &= after["fits"]
        # A greedy route regrouping is not evidence of achievable wage savings.
        wages += sum(
            hire_cost(i, cfg.get("farmHandCostMult", 1))
            for i in range(before["workers"] - 1, after["workers"] - 1)
        )
        if date == day + 1:
            next_wages = sum(
                hire_cost(i, cfg.get("farmHandCostMult", 1)) for i in range(after["workers"] - 1)
            )
        work += sum(throughput_service(t, date, final) for t in additions)
    # Seeds/animals can start installation before the modeled next-day date.
    # Protect any extra hires this can trigger while morning hiring is open.
    immediate_wages = 0
    if obs["hour"] < 6:
        immediate = [
            dict(t, **{"placed_day" if "animal" in t else "planted_day": day}) for t in additions
        ]
        after = repaired_workforce(assets + immediate, day, final, tpd, access)
        fits &= after["fits"]
        farm = obs["farms"][obs["player"]]
        before = max(
            farm["hires_today"] + 1,
            repaired_workforce(assets, day, final, tpd, access)["workers"],
        )
        immediate_wages = sum(
            hire_cost(i, cfg.get("farmHandCostMult", 1))
            for i in range(before - 1, after["workers"] - 1)
        )
    return wages + immediate_wages, work, bool(fits), next_wages, immediate_wages


def repaired_terminal_job(tile, job, day, final, remaining, travel, delivery):
    """Reserve the complete water -> harvest -> shed -> deposit chain."""
    if not job or day != final:
        return job
    crop = tile.get("crop")
    if crop not in CROPS:
        return job
    ready = day - tile["planted_day"] >= CROPS[crop]["first"] and tile.get("yield_units", 0)
    if not ready:
        return None
    op, urgency, _ = job
    steps = 2 if op == "WATER" and not CROPS[crop]["interval"] else 1
    if op not in ("WATER", "HARVEST") or travel + steps + delivery > remaining:
        if travel + 1 + delivery <= remaining:
            return "HARVEST", 280, 1
        return None
    return op, urgency, steps


def repaired_investment(obs, cfg, params, commands, market, max_land=3):
    report = {"chosen": None, "alternatives": [], "deferred": []}
    day, own = obs["day"], obs["player"]
    farm, private = obs["farms"][own], obs["private"]
    tpd = cfg.get("turnsPerDay", 24)
    final = (cfg.get("episodeSteps", 720) - 2) // tpd
    # Purchases are for the next day's crew. Retry after morning sales/hires,
    # rather than making their order congestion a permanent growth prohibition.
    if (
        day >= final
        or obs["hour"] > tpd - 4
        or len(market) >= cfg.get("maxMarketOrdersPerTurn", 10)
        or sum(private["seeds"].values())
        or any(
            private["shed"].get(a, 0) or any(v.get(a, 0) for v in private["inventories"])
            for a in ANIMALS
        )
    ):
        return market, report
    planned = planning_snapshot(obs, cfg, commands, market, params)
    assets = repaired_assets(planned)
    base = [throughput_flows(group, day, final) for group in assets]
    for product in MARKET:
        base[own][day][product] += planned["private"]["shed"].get(product, 0) + sum(
            v.get(product, 0) for v in planned["private"]["inventories"]
        )
    live = sum("animal" in t for t in assets[own])
    wheat = planned["private"]["shed"].get("WHEAT", 0) + sum(
        v.get("WHEAT", 0) for v in planned["private"]["inventories"]
    )
    feed_quote = 2 * price_at("WHEAT", obs["market"]["inventory"]["WHEAT"] - live - 24, params)
    # Do not spend uncertain same-turn sale proceeds. Stock accounting still
    # includes deposits/sales so receipts cannot be forecast twice.
    banked = farm["money"] - sum(
        hire_cost(farm["hires_today"] + i, cfg.get("farmHandCostMult", 1))
        for i in range(sum(o[0] == "HIRE" for o in market))
    )
    banked -= sum(
        o[2] * 2 * price_at(o[1], obs["market"]["inventory"][o[1]] - o[2] - 20, params)
        for o in market
        if o[0] == "BUY_PRODUCT"
    )
    cash = min(banked, planned["farms"][own]["money"])
    room = cfg.get("shedCapacity", 100) - sum(planned["private"]["shed"].values())
    owned = len(farm["unlocked_quadrants"])

    def vacant(sites, animal=False):
        return [
            p
            for p in sites
            if farm["tiles"][p[1]][p[0]] in (None, "LOCKED")
            or isinstance(farm["tiles"][p[1]][p[0]], dict)
            and farm["tiles"][p[1]][p[0]].get("kind")
            in (("WEED", "COOP", "PASTURE") if animal else ("WEED",))
            and not farm["tiles"][p[1]][p[0]].get("animal")
        ]

    options = []
    for land in (False, True):
        if land and owned >= max_land:
            continue
        animal_sites, fields = farm_sites(obs, land)
        land_cost = (1000, 2000, 4000)[owned - 1] if land else 0
        prefix = [["BUY_LAND"]] if land else []
        free = vacant(animal_sites, animal=True)
        for count in (1, 2) if land else (1,):
            if len(free) < count or room < count:
                continue
            if land and not any(farm["tiles"][y][x] == "LOCKED" for x, y in free[:count]):
                continue
            for animal, spec in ANIMALS.items():
                if day + 2 + spec["first_yield_day"] > final:
                    continue
                additions = [
                    dict(
                        animal=animal,
                        placed_day=day + 1,
                        site=p,
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
        free = vacant(fields)
        for count in (4, 8) if land else (1, 4):
            if len(free) < count:
                continue
            if land and not any(farm["tiles"][y][x] == "LOCKED" for x, y in free[:count]):
                continue
            for crop, spec in CROPS.items():
                if day + 1 + spec["harvest"] > final:
                    continue
                if crop in ("CARROT", "TOMATO") and observed_demand(obs, cfg)[crop] <= 1:
                    continue
                additions = [
                    dict(
                        crop=crop,
                        planted_day=day + 1,
                        site=p,
                        yield_units=0 if spec["interval"] else 1,
                    )
                    for p in free[:count]
                ]
                options.append(
                    (
                        prefix + [["BUY_SEED", crop, count]],
                        additions,
                        land_cost + count * spec["seed"],
                    )
                )
    for orders, additions, cost in options:
        labor = repaired_labor_delta(planned, cfg, assets[own], additions)
        new_animals = sum("animal" in t for t in additions)
        reserve = 150 + max(0, live + new_animals - wheat) * feed_quote + labor[3] + labor[4]
        if cash < reserve + cost or not labor[2]:
            continue
        extra = throughput_flows(additions, day, final)
        value = throughput_value(planned, cfg, params, base, extra, additions, cost, assets[own])
        option = dict(value, orders=orders, cost=cost, reserve=reserve)
        report["alternatives"].append(option)
    feasible = [a for a in report["alternatives"] if a["value"] > 0 and a["capacity_estimate_fits"]]
    if feasible:
        chosen = max(feasible, key=lambda a: (a["value"], -a["work"]))
        if len(market) + len(chosen["orders"]) <= cfg.get("maxMarketOrdersPerTurn", 10):
            market.extend(chosen["orders"])
            report["chosen"] = chosen
        else:
            # Do not consume the cleared installation queue on an inferior
            # one-order purchase. Reconsider the whole bundle next observation.
            report["deferred"] = chosen["orders"]
    return market, report
