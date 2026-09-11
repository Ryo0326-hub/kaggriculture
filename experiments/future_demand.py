"""Helpers bundled into the isolated Cycle 5 investment challenger.

The builder supplies Cycle 3's constants and accounting functions. No game seed
or future observations are used by this deterministic scenario approximation.
"""

# These names are supplied by the standalone builder's frozen Cycle 3 module.
# ruff: noqa: F821


def future_demand_paths(obs, cfg):
    from random import Random

    day = obs["day"]
    tpd = cfg.get("turnsPerDay", 24)
    final = (cfg.get("episodeSteps", 720) - 2) // tpd
    interval = max(1, int(cfg.get("townShopUnlockInterval", 3)))
    remaining = max(0, 8 - len(obs.get("town", {}).get("unlocked_shops", [])))
    dates = [d for d in range(day + 1, final + 1) if d % interval == 0][:remaining]
    # Stratify each column, not whole paths. Independent column permutations
    # permit repeated shops within a path, as in draws with replacement.
    rng = Random(20260911)
    columns = []
    for _ in dates:
        column = sorted(SHOP_PRODUCTS)
        rng.shuffle(column)
        columns.append(column)
    paths = []
    for scenario in range(8 if dates else 1):
        unlocks = [(date, column[scenario]) for date, column in zip(dates, columns)]
        demand = observed_demand(obs, cfg)
        daily = {}
        future = dict(unlocks)
        for date in range(day, final + 1):
            if date in future:
                products = SHOP_PRODUCTS[future[date]]
                units = tpd / max(1, int(cfg.get("townShopSellInterval", 4)))
                units *= 2 if len(products) == 1 else 1
                for product in products:
                    demand[product] += units
            daily[date] = dict(demand)
        paths.append({"unlocks": unlocks, "daily": daily})
    return paths


def investment_projection(obs, cfg, params, paths, additions=(), land_cost=0):
    scenarios = [
        production_projection(
            obs, cfg, params, additions, routed=True, land_cost=land_cost, demand_path=p["daily"]
        )
        for p in paths
    ]
    return {
        "value": sum(p["value"] for p in scenarios) / len(scenarios),
        "min_cash": min(p["min_cash"] for p in scenarios),
        "route_feasible": all(p.get("route_feasible", True) for p in scenarios),
        "scenarios": scenarios,
    }
