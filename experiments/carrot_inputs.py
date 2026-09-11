"""Executable current-day carrot inputs; future optional yield is not promised."""

# Bundled into the frozen agent's global namespace.
# ruff: noqa: F821


def carrot_input_plan(obs, cfg, params, available, newborn, urgent, stock, enabled=True):
    result = {"bundles": {}, "buy": 0, "keep": 0, "purchase_cost": 0}
    if not enabled:
        return result
    farm, private = obs["farms"][obs["player"]], obs["private"]
    day, hour = obs["day"], obs["hour"]
    tpd = cfg.get("turnsPerDay", 24)
    final = (cfg.get("episodeSteps", 720) - 2) // tpd
    remaining = min(tpd - hour, cfg.get("episodeSteps", 720) - 1 - obs["step"])
    positions = [tuple(farm["farmer"]), *map(tuple, farm["hands"])]
    access = shed_access(obs)
    eligible = []
    for i in available:
        inv = private["inventories"][i]
        if i in newborn or any(inv.get(c, 0) for c in (*ANIMALS, "MILK", "WOOL", "EGG")):
            continue
        if i in urgent:
            x, y = urgent[i][0]
            if farm["tiles"][y][x].get("crop") != "CARROT":
                continue
        if sum(inv.values()) >= 16:
            continue
        eligible.append(i)
    targets = []
    for y, row in enumerate(farm["tiles"]):
        for x, tile in enumerate(row):
            if not isinstance(tile, dict) or tile.get("crop") != "CARROT":
                continue
            value = carrot_fertilizer_value(tile, obs, cfg, params)
            if value <= 0:
                continue
            # Undo the old one-action allowance/opportunity quote; charge the
            # actual extra actions and the complete purchase's final quote below.
            benefit = (
                value + 8 + price_at("FERTILIZER", obs["market"]["inventory"]["FERTILIZER"], params)
            )
            targets.append(((x, y), tile, benefit))
    inventory = obs["market"]["inventory"]["FERTILIZER"]
    shed_units = max(0, stock.get("FERTILIZER", 0))
    used_workers, used_sites = set(), set()
    while True:
        choices = []
        for site, tile, benefit in targets:
            if site in used_sites:
                continue
            mature = day - tile["planted_day"] >= 3 or day == final
            delivery = min(distance(site, a) for a in access) + 1 if day == final else 0
            for i in eligible:
                if i in used_workers:
                    continue
                p, inv = positions[i], private["inventories"][i]
                direct = distance(p, site)
                shed = min(access, key=lambda a: (distance(p, a) + distance(a, site), a))
                if inv.get("FERTILIZER", 0):
                    source, steps, extra = "carried", direct + 2, 1
                    command = move_toward(p, site) if p != site else ["FERTILIZE"]
                elif shed_units:
                    source = "shed"
                    steps = distance(p, shed) + 1 + distance(shed, site) + 2
                    extra = steps - (direct + 1)
                    command = move_toward(p, shed) if p != shed else ["PICKUP", "FERTILIZER", 1]
                elif p in access and hour <= 6 and day < final:
                    # Unit actions precede market purchases. A newly bought input
                    # cannot be picked up until the next decision.
                    source, steps = "buy", 1 + 1 + distance(p, site) + 2
                    extra = steps - (direct + 1)
                    command = ["PASS"]
                else:
                    continue
                if steps + int(mature) + delivery > remaining:
                    continue
                if (
                    mature
                    and cfg.get("shedCapacity", 100)
                    - sum(private["shed"].values())
                    - sum(sum(v.values()) for v in private["inventories"])
                    < 4
                ):
                    continue
                buys = result["buy"] + int(source == "buy")
                quote = price_at("FERTILIZER", inventory - buys, params)
                net = benefit - quote - 8 * extra
                if net <= 0:
                    continue
                # One purchase can increase the opportunity cost of every
                # reserved unit; never invalidate a previously selected bundle.
                if any(
                    b["benefit"] - quote - 8 * b["extra_actions"] <= 0
                    for b in result["bundles"].values()
                ):
                    continue
                cost = sum(
                    price_at("FERTILIZER", inventory - k, params) for k in range(1, buys + 1)
                )
                if source == "buy" and (
                    farm["money"] < 150 + cost
                    or sum(private["shed"].values()) + buys > cfg.get("shedCapacity", 100)
                ):
                    continue
                choices.append(
                    (
                        net / steps,
                        -steps,
                        -i,
                        site,
                        {
                            "worker": i,
                            "target": site,
                            "source": source,
                            "action": command,
                            "steps": steps + int(mature) + delivery,
                            "extra_actions": extra,
                            "benefit": benefit,
                            "post_buy_value": net,
                        },
                    )
                )
        if not choices:
            break
        bundle = max(choices, key=lambda c: c[:4])[-1]
        i, site = bundle["worker"], bundle["target"]
        result["bundles"][i] = bundle
        used_workers.add(i)
        used_sites.add(site)
        if bundle["source"] == "shed":
            shed_units -= 1
            result["keep"] += int(bundle["action"][0] != "PICKUP")
        elif bundle["source"] == "buy":
            result["buy"] += 1
    result["purchase_cost"] = sum(
        price_at("FERTILIZER", inventory - k, params) for k in range(1, result["buy"] + 1)
    )
    return result


def fund_carrot_inputs(obs, cfg, params, commands, market, plan):
    """Recheck the real ledger after existing feed/hiring/sale commitments."""
    if not plan["buy"]:
        return market
    snapshot = planning_snapshot(obs, cfg, commands, market, params)
    inv = snapshot["market"]["inventory"]["FERTILIZER"]
    n = plan["buy"]
    quote = price_at("FERTILIZER", inv - n, params)
    cost = sum(price_at("FERTILIZER", inv - k, params) for k in range(1, n + 1))
    if (
        len(market) < cfg.get("maxMarketOrdersPerTurn", 10)
        and snapshot["farms"][obs["player"]]["money"] >= 150 + cost
        and sum(snapshot["private"]["shed"].values()) + n <= cfg.get("shedCapacity", 100)
        and all(b["benefit"] - quote - 8 * b["extra_actions"] > 0 for b in plan["bundles"].values())
    ):
        market.append(["BUY_PRODUCT", "FERTILIZER", n])
        plan["funded"] = n
        plan["purchase_cost"] = cost
    else:
        plan["funded"] = 0
    return market
