"""Expansion admission only: fund remaining-day policy obligations before receipts.

Bundled into the frozen Cycle 3 source by make_cash_control. Uses its constants
and routing helpers; no engine, replay, hidden state or new runtime dependency.
"""

# The generator supplies these names from the frozen standalone agent.
# ruff: noqa: F821


def current_day_cash_bound(obs, cfg, params, additions, projection):
    if not projection["daily"]:
        return {"min_cash": projection["min_cash"], "reason": "Infeasible original projection"}
    own, day = obs["player"], obs["day"]
    farm, private = obs["farms"][own], obs["private"]
    tpd = cfg.get("turnsPerDay", 24)
    final = (cfg.get("episodeSteps", 720) - 2) // tpd
    access = shed_access(obs)
    animal_sites, fields = farm_sites(obs)
    animals = [
        (p, farm["tiles"][p[1]][p[0]])
        for p in animal_sites
        if isinstance(farm["tiles"][p[1]][p[0]], dict) and "animal" in farm["tiles"][p[1]][p[0]]
    ]
    plants = [
        (p, farm["tiles"][p[1]][p[0]])
        for p in fields
        if isinstance(farm["tiles"][p[1]][p[0]], dict)
        and farm["tiles"][p[1]][p[0]].get("crop") in CROPS
    ]
    new_animals = [a for a in additions if "animal" in a]
    new_seeds = sum("crop" in a for a in additions)
    remaining = min(tpd - obs["hour"] - 1, cfg.get("episodeSteps", 720) - 2 - obs["step"])
    # Fastest shed-to-site setup: animal/feed pickups, build, place and first feed.
    # It tests possibility, not a guarantee of timely dispatch; admission is early-day.
    installed = sum(
        min(distance(tuple(a["site"]), p) for p in access) + 5 <= remaining for a in new_animals
    )
    unfed = sum(not t["fed_today"] for _, t in animals) if day < final else 0
    held_feed = private["shed"].get("WHEAT", 0) + sum(
        i.get("WHEAT", 0) for i in private["inventories"]
    )
    # Actual market policy keeps one day's herd feed, including pending installations.
    feed_target = unfed + len(animals) + len(new_animals) + installed if day < final else 0
    missing = max(0, feed_target - held_feed)
    modeled_missing = max(0, unfed - held_feed)
    extra_feed = max(0, missing - modeled_missing)
    inventory = obs["market"]["inventory"]["WHEAT"]
    feed_cost = sum(
        price_at("WHEAT", inventory - i - 1, params) for i in range(modeled_missing, missing)
    )
    if new_animals:
        # Buying an animal switches plan_turn to dedicated installation stations.
        livestock_workers = len(animals) + len(new_animals)
    else:
        dedicated = []
        for i, (_, tile) in enumerate(animals):
            spec = ANIMALS[tile["animal"]]
            age = day - tile["placed_day"] - spec["first_yield_day"]
            if age >= 0 and age % spec["interval"] == 0:
                dedicated.append(i)
        work = 2 if day == final else 3 if day == final - 1 else 4
        routes, _, feasible = route_cover(
            tuple(p for p, _ in animals),
            (work,) * len(animals),
            access,
            min(tpd, cfg.get("episodeSteps", 720) - 1 - day * tpd) - 3,
            tuple(dedicated),
        )
        livestock_workers = max(1, len(routes) if feasible else len(animals))
    crop_work = sum(2 * min(distance(p, a) for a in access) + 3 for p, _ in plants)
    crop_jobs = sum(bool(crop_job(t, day, final)) for _, t in plants)
    worker_target = min(
        HERD_LIMIT + 3,
        max(
            1,
            math.ceil((6 * len(animals) + crop_work + 14 * new_seeds) / max(1, tpd - 4)),
            livestock_workers + math.ceil(crop_jobs / 4),
        ),
    )
    paid = farm["hires_today"]  # Includes this turn's planned hires, already debited.
    multiplier = cfg.get("farmHandCostMult", 1)
    modeled_hires = max(paid, projection["daily"][0]["workers"] - 1)
    target_hires = max(paid, worker_target - 1) if obs["hour"] < 6 else paid
    # Existing forecast already includes the hires through modeled_hires.
    extra_wages = sum(hire_cost(i, multiplier) for i in range(modeled_hires, target_hires))
    floor = (
        farm["money"] - projection["daily"][0]["spending_before_receipts"] - feed_cost - extra_wages
    )
    return {
        "min_cash": min(projection["min_cash"], floor),
        "before_receipts_cash": floor,
        "original_min_cash": projection["min_cash"],
        "feed_target": feed_target,
        "held_feed": held_feed,
        "already_modeled_feed_shortfall": modeled_missing,
        "extra_feed_units": extra_feed,
        "extra_feed_cash": feed_cost,
        "worker_target": worker_target,
        "paid_or_planned_hires": paid,
        "already_modeled_total_hires": modeled_hires,
        "extra_hires": max(0, target_hires - modeled_hires),
        "extra_wage_cash": extra_wages,
        "possible_same_day_installations": installed,
    }
