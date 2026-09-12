# Cycle 20 replacements/additions to the frozen Cycle 19 implementation.
# ruff: noqa: F821


def committed_supply(obs, ctx, item, horizon):
    """Closed-form output commitments, not a game rollout or a future-action claim."""
    day = ctx["day"]
    end = min(ctx["final"], day + max(0, math.ceil(horizon)))
    if end <= day:
        return 0.0
    private = obs["private"]
    # Only our inventory is observable. Rival shed/carries are deliberately absent.
    supply = private["shed"].get(item, 0) + sum(inv.get(item, 0) for inv in private["inventories"])
    portfolio = assets(obs, 0) + assets(obs, 1)
    for c, count in private["seeds"].items():
        portfolio += [dict(crop=c, planted_day=day + 1, yield_units=0)] * count
    for a in ANIMALS:
        count = private["shed"].get(a, 0) + sum(inv.get(a, 0) for inv in private["inventories"])
        portfolio += [dict(animal=a, placed_day=day + 1, yield_units=0)] * count
    for tile in portfolio:
        if tile.get("animal"):
            spec = ANIMALS[tile["animal"]]
            first = tile["placed_day"] + spec["first_yield_day"]
            last = first + max(0, (ctx["final"] - first) // spec["interval"]) * spec["interval"]
            if item == "WHEAT" and first <= ctx["final"]:
                # Feed absorbs production or requires market purchases. Gross wheat
                # output is not all market supply. No feeding after last useful yield.
                start = max(day, tile["placed_day"])
                feed = max(0, min(end, last) - start)
                if start == day and tile.get("fed_today"):
                    feed = max(0, feed - 1)
                supply -= feed
            if spec["product"] != item:
                continue
            supply += tile.get("yield_units", 0)
            due = first + max(0, math.ceil((day + 1 - first) / spec["interval"])) * spec["interval"]
            if due <= end:
                events = 1 + (end - due) // spec["interval"]
                care = tile.get("pending_care_bonus", 0) + max(
                    0, due - max(day, tile["placed_day"]) - 1
                )
                supply += min(spec["max_held"], 1 + care)
                supply += (events - 1) * min(spec["max_held"], spec["interval"] + 1)
        elif tile.get("crop") == item:
            spec = CROPS[item]
            first = tile["planted_day"] + spec["first"]
            if spec["interval"]:
                supply += tile.get("yield_units", 0)
                last = first + (spec["events"] - 1) * spec["interval"]
                due = (
                    first
                    + max(0, math.ceil((day + 1 - first) / spec["interval"])) * spec["interval"]
                )
                if due <= min(end, last):
                    supply += 1.7 * (1 + (min(end, last) - due) // spec["interval"])
            else:
                # One planting yields once; never extrapolate imaginary replanting.
                due = max(day, tile["planted_day"] + spec["harvest"])
                if due <= end:
                    target = 4.2 if item == "WHEAT" else spec["cap"]
                    supply += max(tile.get("yield_units", 0), target)
    return supply


def expected_price(obs, ctx, item, horizon, rates, extra=0):
    inventory = obs["market"]["inventory"][item]
    duration = min(max(0, math.ceil(horizon)), ctx["final"] - ctx["day"])
    supply = committed_supply(obs, ctx, item, duration)
    future = inventory + supply - ctx["demand"][item] * duration + extra
    now = price_at(item, inventory, ctx["params"])
    later = price_at(item, future, ctx["params"])
    # Today's quote cannot subsidize a harvest sold after a projected price crash.
    # Retain the inherited discount for uncertain price appreciation only.
    return max(1, min(later, 0.35 * now + 0.65 * later))


def rescue_sites(jobs, position, ctx):
    """Late-day survival precedes routine routes; existing reservations still apply."""
    if ctx["day"] == ctx["final"] or ctx["remaining"] > 6:
        return []
    return sorted(
        (p for p, job in jobs.items() if job["urgency"] >= 5),
        key=lambda p: (distance(position, p), p),
    )
