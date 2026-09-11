"""Carrot-specific mechanics; bundled into frozen Cycle 3 without changing other crops."""

# ruff: noqa: F821


def carrot_demand_visible(obs):
    return any(s in ("PET_CAFE", "FARMERS_MARKET") for s in obs["town"]["unlocked_shops"])


def carrot_column(planted, final, fertilized=False, tile=None, today=0):
    if today > final or final < planted + 2:
        return None
    # Existing plots can be salvaged at age two on the terminal day. New
    # investments still require the full age-three deadline in admission.
    end = max(today, min(final, planted + 3))
    if tile is None and (end < planted + 3 or today > planted + 3):
        return None
    tile = tile or {"yield_units": 1}
    quantity = tile.get("yield_units", 1)
    expiry = tile.get("fertilized_until_day", -1)
    applications = []
    for date in range(max(today, planted + 2), min(end, planted + 3) + 1):
        if date == today and tile.get("watered_today"):
            continue
        remaining = end - date + 1
        if fertilized and expiry < date and quantity + remaining < 4 and not applications:
            applications.append(date)
            expiry = date + 2
        quantity = min(4, quantity + (2 if expiry >= date else 1))
    return {
        "crop": "CARROT",
        "planted_day": planted,
        "end": end,
        "outputs": {end: quantity},
        "fertilizer": applications,
        "work": {date: 15 for date in range(max(today, planted), end + 1)},
        "fertilized": fertilized,
    }


def carrot_job(tile, day, final):
    age, units = day - tile["planted_day"], tile.get("yield_units", 0)
    harvest = age >= 2 and units > 0 and (age >= 3 or day == final)
    bonus = 2 <= age <= 3 and units < 4
    if harvest and (not bonus or tile.get("watered_today")):
        return ("HARVEST", 250 + 10 * max(0, age - 3), 1)
    water = not tile.get("watered_today") and (tile.get("consecutive_unwatered", 0) >= 1 or bonus)
    if water and (day < final or harvest and bonus):
        return (
            "WATER",
            260 if harvest else 150 if tile.get("consecutive_unwatered", 0) else 100,
            1,
        )
    return None


def carrot_fertilizer_value(tile, obs, cfg, params):
    day = obs["day"]
    final = (cfg.get("episodeSteps", 720) - 2) // cfg.get("turnsPerDay", 24)
    if tile.get("watered_today") or tile.get("fertilized_until_day", -1) >= day:
        return 0
    if not 2 <= day - tile["planted_day"] <= 3:
        return 0
    base = carrot_column(tile["planted_day"], final, False, tile, day)
    extra = carrot_column(tile["planted_day"], final, True, tile, day)
    if not base or not extra:
        return 0
    gain = sum(extra["outputs"].values()) - sum(base["outputs"].values())
    if gain <= 0:
        return 0
    inventory = (
        obs["market"]["inventory"]["CARROT"]
        - observed_demand(obs, cfg)["CARROT"] * min(3, final - day)
        + 12
    )
    benefit = 0.85 * batch_revenue("CARROT", inventory, gain, params)
    forgone = price_at("FERTILIZER", obs["market"]["inventory"]["FERTILIZER"], params)
    return benefit - forgone - 8
