"""Cycle 6: one-shop lookahead with unobserved rival-growth stress.

Bundled into the frozen standalone agent by make_information_control.py.
"""

# Constants and original accounting functions are supplied by the builder.
# ruff: noqa: F821


def forecast_quote(product, inventory, params, quotes):
    if quotes is None:
        return price_at(product, inventory, params)
    key = product, inventory
    if key not in quotes:
        quotes[key] = price_at(product, inventory, params)
    return quotes[key]


def forecast_sale(product, inventory, amount, params, quotes):
    revenue = 0
    for _ in range(amount):
        price = forecast_quote(product, inventory, params, quotes)
        revenue += price
        inventory += int(price > 1)
    return revenue


def rival_growth_stress(obs, cfg):
    farm = obs["farms"][1 - obs["player"]]
    tiles = [t for row in farm["tiles"] for t in row]
    slots = sum(t is None or isinstance(t, dict) and t.get("kind") == "WEED" for t in tiles)
    budget = max(0, farm["money"] - 150)
    installed = obs["day"] + 1
    final = (cfg.get("episodeSteps", 720) - 2) // cfg.get("turnsPerDay", 24)
    additions = []
    for kind, specs in (("crop", CROPS), ("animal", ANIMALS)):
        counts = {
            name: sum(isinstance(t, dict) and t.get(kind) == name for t in tiles) for name in specs
        }
        name = max(counts, key=lambda n: (counts[n], n))
        if not slots or not counts[name]:
            continue
        item = {kind: name, "planted_day" if kind == "crop" else "placed_day": installed}
        if kind == "crop":
            viable = crop_column(name, installed, final, False, today=obs["day"]) is not None
            cost, cap = specs[name]["seed"], 4
        else:
            viable = any(units for units, _ in animal_output(item, obs["day"], final))
            cost, cap = specs[name]["cost"], 1
        count = min(slots, cap, int(budget // cost)) if viable else 0
        additions.extend(dict(item) for _ in range(count))
        budget -= count * cost
        slots -= count
    return additions


def next_shop_context(obs, cfg):
    day = obs["day"]
    tpd = cfg.get("turnsPerDay", 24)
    final = (cfg.get("episodeSteps", 720) - 2) // tpd
    interval = max(1, int(cfg.get("townShopUnlockInterval", 3)))
    next_day = (day // interval + 1) * interval
    if len(obs["town"].get("unlocked_shops", [])) >= 8 or next_day > final:
        next_day = None
    growth = rival_growth_stress(obs, cfg)
    branches = []
    for shop in sorted(SHOP_PRODUCTS) if next_day is not None else (None,):
        current = observed_demand(obs, cfg)
        future = dict(current)
        if shop:
            products = SHOP_PRODUCTS[shop]
            units = tpd / max(1, int(cfg.get("townShopSellInterval", 4)))
            for product in products:
                future[product] += units * (2 if len(products) == 1 else 1)
        branches.append(
            {
                "shop": shop,
                "demand": {
                    d: future if next_day is not None and d >= next_day else current
                    for d in range(day, final + 1)
                },
            }
        )
    return {
        "next_day": next_day,
        "branches": branches,
        "supply_cases": [[], growth] if growth else [[]],
    }


def continuation_forecasts(obs, cfg, params, context, quotes, additions=(), land=0, buy_day=None):
    date = obs["day"] if buy_day is None else buy_day
    delay = date - obs["day"]
    shifted = []
    for item in additions:
        item = dict(item, buy_day=date)
        key = "placed_day" if "animal" in item else "planted_day"
        item[key] += delay
        shifted.append(item)
    work_cache = {}
    return [
        [
            production_projection(
                obs,
                cfg,
                params,
                shifted,
                routed=True,
                land_cost=land,
                land_day=date,
                demand_path=branch["demand"],
                rival_additions=growth,
                quotes=quotes,
                net_rival_wheat=True,
                work_cache=work_cache,
            )
            for growth in context["supply_cases"]
        ]
        for branch in context["branches"]
    ]


def paired_continuation(projections, baseline):
    values, feasible, minima = [], [], []
    for forecasts, reference in zip(projections, baseline):
        values.append(min(p["value"] - b["value"] for p, b in zip(forecasts, reference)))
        minimum = min(p["min_cash"] for p in forecasts)
        minima.append(minimum)
        feasible.append(
            minimum >= 150 and all(p.get("route_feasible", True) and p["daily"] for p in forecasts)
        )
    return {
        "branch_values": values,
        "branch_feasible": feasible,
        "branch_min_cash": minima,
        "marginal_value": sum(values) / len(values),
        "min_cash": min(minima),
    }


def best_information_option(options, branch=None):
    def value(option):
        return option["marginal_value"] if branch is None else option["branch_values"][branch]

    feasible = [
        o
        for o in options
        if (o["affordable"] if branch is None else o["branch_feasible"][branch]) and value(o) > 0
    ]
    if not feasible:
        return None
    best = max(feasible, key=lambda o: value(o) / len(o["columns"]))
    family = best["orders"][-1][:2]
    return max((o for o in feasible if o["orders"][-1][:2] == family), key=value)


def information_investment(obs, cfg, params, options, market, report):
    context = next_shop_context(obs, cfg)
    # This cache lives for one decision and one parameter dictionary only.
    quotes = {}
    baseline = continuation_forecasts(obs, cfg, params, context, quotes)
    report["information"] = context
    report["baseline_values"] = [[p["value"] for p in branch] for branch in baseline]
    delayed = []
    for land, orders, additions in options:
        if len(market) + len(orders) > cfg.get("maxMarketOrdersPerTurn", 10):
            continue
        cost = land + sum(
            ANIMALS[c["animal"]]["cost"] if "animal" in c else CROPS[c["crop"]]["seed"]
            for c in additions
        )
        for when, target in ((None, report["alternatives"]), (context["next_day"], delayed)):
            if target is delayed and when is None:
                continue
            forecasts = continuation_forecasts(
                obs, cfg, params, context, quotes, additions, land, when
            )
            option = paired_continuation(forecasts, baseline)
            option.update(
                orders=orders,
                land_cost=land,
                columns=additions,
                cost_now=cost,
                buy_day=obs["day"] if when is None else when,
            )
            option["affordable"] = all(option["branch_feasible"]) and (
                when is not None or obs["farms"][obs["player"]]["money"] >= cost + 150
            )
            target.append(option)
    immediate = best_information_option(report["alternatives"])
    wait_choices = [best_information_option(delayed, i) for i in range(len(context["branches"]))]
    wait_value = sum(o["branch_values"][i] if o else 0 for i, o in enumerate(wait_choices)) / len(
        wait_choices
    )
    immediate_value = immediate["marginal_value"] if immediate else 0
    report.update(
        delayed_alternatives=delayed,
        wait_choices=wait_choices,
        wait_value=wait_value,
        immediate_value=immediate_value,
    )
    if wait_value > immediate_value + 1e-6:
        report["decision"] = "wait_for_shop"
    elif immediate:
        report["decision"] = "buy_now"
        report["chosen"] = immediate
        market.extend(immediate["orders"])
    else:
        report["decision"] = "no_profitable_purchase"
    return market, report
