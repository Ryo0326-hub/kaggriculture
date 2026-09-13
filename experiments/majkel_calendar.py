# Cycle 21 overrides, bundled with the hash-checked Cycle 20 agent.
# ruff: noqa: F821


def crop_water_needed(tile, ctx):
    if tile.get("watered_today"):
        return False
    spec = CROPS[tile["crop"]]
    age = ctx["day"] - tile["planted_day"]
    if spec["interval"]:
        last = spec["first"] + (spec["events"] - 1) * spec["interval"]
        if age >= last or ctx["day"] >= ctx["final"]:
            return False
        due = age + 1 - spec["first"]
        productive = 0 <= due < spec["events"] * spec["interval"] and not due % spec["interval"]
    else:
        lower = 6 if tile["crop"] == "MELON" else 2
        upper = {"WHEAT": 4, "CARROT": 3, "MELON": 12}[tile["crop"]]
        productive = lower <= age <= upper and tile.get("yield_units", 0) < spec["cap"]
        if ctx["day"] >= ctx["final"]:
            return productive
    # A newborn's initial drought counter is already one. Safe skips never
    # override the observed counter, even when an earlier visit was missed.
    return bool(age == 0 or tile.get("consecutive_unwatered", 0) >= 1 or productive)


def make_jobs(obs, ctx):
    jobs = calendar_base_jobs(obs, ctx)
    night = ctx["remaining"]
    for p, job in list(jobs.items()):
        t = job["asset"]
        if t.get("install") or t.get("plant"):
            continue
        ops = job["ops"]
        if t.get("crop") and not crop_water_needed(t, ctx):
            ops = [o for o in ops if o[0] != "WATER"]
        names = {o[0] for o in ops}
        hard = ("WATER" in names and t.get("consecutive_unwatered", 0) >= 1) or (
            "FEED" in names and t.get("consecutive_unfed", 0) >= 1
        )
        if hard:
            ops.sort(key=lambda o: o[0] not in ("WATER", "FEED"))
        job["ops"] = ops
        if not ops:
            del jobs[p]
            continue
        if ctx["day"] == ctx["final"]:
            continue  # Preserve terminal delivery and same-action sales.
        essential, priority = [], 0
        if "FEED" in names:
            # Maintain inherited daily feeding; production-night feeding also
            # protects the banked care bonus, even without a survival deadline.
            essential = [["FEED"]]
            priority = 3 if hard else 2
        elif "WATER" in names or "FERTILIZE" in names:
            essential = [o for o in ops if o[0] in ("WATER", "FERTILIZE")]
            priority = 3 if hard else 2
            if hard:
                essential = [["WATER"]]
        elif "HARVEST" in names:
            essential, priority = [["HARVEST"]], 1
        expiry = t.get("max_lifespan_step", -1)
        deadline = night
        if t.get("crop") and "HARVEST" in names and expiry >= 0:
            decay = expiry + 2 * max(0, math.ceil((ctx["step"] - expiry) / 2))
            if decay < ctx["step"] + night:
                # Unit actions occur before decay. Harvest on the decay step is
                # still valid, but spending that action on WATER is too late.
                deadline = max(1, decay - ctx["step"] + 1)
                essential, priority = [["HARVEST"]], 4
                job["decay_deadline"] = True
        if essential:
            product = t.get("crop") or ANIMALS[t["animal"]]["product"]
            units = t.get("yield_units", 0) + 1
            if hard and t.get("crop"):
                spec = CROPS[t["crop"]]
                units += spec["events"] if spec["interval"] else spec["cap"]
            job.update(
                service_ops=essential,
                deadline_remaining=deadline,
                service_priority=priority,
                service_value=max(1, ctx["prices"][product]) * units,
                hard_survival=hard,
            )
    return jobs


def prepare_job(job, inv, stock, p, target, ctx):
    if ctx["day"] == ctx["final"] or "deadline_remaining" not in job:
        return calendar_base_prepare(job, inv, stock, p, target, ctx)
    limit = min(ctx["remaining"], job["deadline_remaining"])
    local = dict(ctx, remaining=limit)
    selected = dict(job, urgency=0, ops=[list(o) for o in job["ops"]])
    if job.get("decay_deadline"):
        selected["ops"] = [["HARVEST"]]
    elif job.get("hard_survival") and not inv.get("FERTILIZER", 0):
        if limit - distance(p, target) - 1 <= 4:
            # A last-minute fertilizer detour must not prevent survival water.
            selected["ops"] = [o for o in selected["ops"] if o[0] != "FERTILIZE"]
    return calendar_base_prepare(selected, inv, stock, p, target, local)


def service_fit(job, inv, stock, p, target, ctx):
    limit = min(ctx["remaining"], job["deadline_remaining"])
    local = dict(ctx, remaining=limit)
    minimal = dict(job, urgency=0, ops=job["service_ops"])
    fit = calendar_base_prepare(minimal, inv, stock, p, target, local)
    if fit is None:
        return None
    ops, missing, depot = fit
    # No synthetic credit for a feed that cannot actually be obtained.
    if job["hard_survival"] and not any(o[0] in ("FEED", "WATER", "HARVEST") for o in ops):
        return None
    travel = distance(p, depot) + distance(depot, target) if missing else distance(p, target)
    cost = travel + len(missing) + len(ops)
    return cost, limit - cost


def service_assignments(jobs, owner, routes, positions, carried, stock, ctx, committed):
    """Bounded deadline matching, retaining feasible commitments to avoid churn."""
    if ctx["day"] == ctx["final"]:
        return {}
    loads = {}
    for i, route in routes.items():
        pos, load = positions[i], 0
        for q in route:
            # New planting/optional collection cannot hide an overloaded sector.
            if "deadline_remaining" not in jobs[q]:
                continue
            load += distance(pos, q) + len(jobs[q]["ops"])
            pos = q
        loads[i] = load
    fits = {}
    for q, job in jobs.items():
        if "deadline_remaining" not in job:
            continue
        choices = {}
        for i, p in enumerate(positions):
            if any(
                carried[i].get(a, 0) and ctx["day"] + ANIMALS[a]["first_yield_day"] <= ctx["final"]
                for a in ANIMALS
            ):
                continue
            fit = service_fit(job, carried[i], stock, p, q, ctx)
            if fit is not None:
                choices[i] = fit
        if not choices:
            continue
        best = min(choices.values())
        overloaded = loads.get(owner.get(q), 0) > ctx["remaining"] - 2
        if best[1] <= 4 or overloaded:
            fits[q] = choices
    result, taken = {}, set()
    # Keep feasible deadline journeys already in progress, including input trips.
    for i, q in committed.items():
        if q in fits and i in fits[q] and q not in taken:
            preempt = any(
                z != q
                and z not in taken
                and i in options
                and (
                    jobs[z]["deadline_remaining"] < jobs[q]["deadline_remaining"]
                    or jobs[z]["service_priority"] > jobs[q]["service_priority"]
                )
                and options[i][1] < fits[q][i][0]
                for z, options in fits.items()
            )
            if preempt:
                continue
            result[i] = q
            taken.add(q)
    ordered = sorted(
        fits,
        key=lambda q: (
            jobs[q]["deadline_remaining"],
            -jobs[q]["service_priority"],
            -jobs[q]["service_value"],
            q,
        ),
    )
    for q in ordered:
        if q in taken:
            continue
        choices = [i for i in fits[q] if i not in result]
        if not choices:
            continue
        i = min(choices, key=lambda i: (fits[q][i][0], owner.get(q) != i, i))
        result[i] = q
        taken.add(q)
    return result


def crop_work(c, events):
    """Count calendar water visits, not a rollout or a daily-watering assumption."""
    spec = CROPS[c]
    last = spec["first"] + (events - 1) * spec["interval"] if spec["interval"] else spec["harvest"]
    water, dry = 0, 1
    for age in range(last + (not spec["interval"])):
        due = age + 1 - spec["first"]
        productive = (
            due >= 0 and due % spec["interval"] == 0
            if spec["interval"]
            else (6 if c == "MELON" else 2) <= age
        )
        if age == 0 or dry or productive:
            water += 1
            dry = 0
        else:
            dry = 1
    fert = events / 2 if spec["interval"] else (1 if c in ("WHEAT", "CARROT") else 0)
    return water + events + 2 + fert
