"""Cycle 10: an opening-only dated wheat-to-melon portfolio extension.

Bundled into the frozen Cycle 3 source; later purchases remain adaptive.
"""

# ruff: noqa: F821


def opening_portfolios(obs, cfg, params, crop_limit=12, fertilized=True):
    alternatives = []
    mixes = [(n, 0) for n in (0, 4, 8, 12)]
    mixes += [(0, 4), (4, 4), (8, 4), (0, 8), (4, 8), (0, 12)]
    for cows, sheep in ((0, 0), (0, 2), (1, 1), (0, 4), (2, 2)):
        for melons, wheat in mixes:
            if melons + wheat > crop_limit:
                continue
            additions = [
                dict(animal=a, placed_day=1)
                for a, n in (("COW", cows), ("SHEEP", sheep))
                for _ in range(n)
            ]
            additions += [dict(crop="MELON", planted_day=0) for _ in range(melons)]
            additions += [dict(crop="WHEAT", planted_day=0) for _ in range(wheat)]
            reuse_day = CROPS["WHEAT"]["harvest"] + 1
            additions += [
                dict(crop="MELON", planted_day=reuse_day, buy_day=reuse_day) for _ in range(wheat)
            ]
            forecasts = [
                production_projection(obs, cfg, params, additions, fertilized=fertilized, stress=s)
                for s in (10, 16)
            ]
            value = sum(f["value"] for f in forecasts) / len(forecasts)
            minimum = min(f["min_cash"] for f in forecasts)
            alternatives.append(
                {
                    "cows": cows,
                    "sheep": sheep,
                    "melons": melons,
                    "wheat": wheat,
                    "value": value,
                    "min_cash": minimum,
                    "affordable": minimum >= 150,
                    "investment_cost": forecasts[0].get("investment_cost", 0),
                    "cost_now": cows * ANIMALS["COW"]["cost"]
                    + sheep * ANIMALS["SHEEP"]["cost"]
                    + melons * CROPS["MELON"]["seed"]
                    + wheat * CROPS["WHEAT"]["seed"],
                    "cash_schedule": forecasts[0]["daily"],
                    "columns": additions,
                }
            )
    best = max((p for p in alternatives if p["affordable"]), key=lambda p: p["value"], default=None)
    return best, alternatives
