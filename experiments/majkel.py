# Cycle 19 policy, bundled with the hash-checked existing mechanics helpers.
# ruff: noqa: F821

CROPS = {
    "WHEAT": dict(seed=10, first=2, harvest=3, interval=0, events=1, cap=6),
    "CARROT": dict(seed=20, first=2, harvest=3, interval=0, events=1, cap=4),
    "MELON": dict(seed=80, first=10, harvest=10, interval=0, events=1, cap=6),
    "STRAWBERRY": dict(seed=100, first=10, harvest=10, interval=2, events=4, cap=4),
    "TOMATO": dict(seed=50, first=8, harvest=8, interval=1, events=4, cap=4),
}
_MEMORY = {}  # An optimization only. Cold starts use deterministic geographic ownership.


def shed_access(obs):
    h = len(obs["farms"][obs["player"]]["tiles"]) // 2
    return ((h - 1, h - 1), (h, h - 1), (h - 1, h), (h, h))


def context(obs, cfg):
    tpd = cfg.get("turnsPerDay", 24)
    day, hour = int(obs["day"]), int(obs["hour"])
    step = day * tpd + hour  # Both seats need not have an observation.step field.
    last = cfg.get("episodeSteps", 720) - 2
    params = {c: dict(p) for c, p in MARKET.items()}
    for c in params:
        params[c].update(cfg.get("marketParams", {}).get(c, {}))
        params[c].update(obs["market"].get("params", {}).get(c, {}))
    return dict(
        prices={c: price_at(c, obs["market"]["inventory"][c], params) for c in MARKET},
        day=day,
        hour=hour,
        step=step,
        final=last // tpd,
        tpd=tpd,
        remaining=max(0, min(tpd - hour, last - step + 1)),
        params=params,
        capacity=cfg.get("shedCapacity", 100),
        access=shed_access(obs),
        demand=observed_demand(obs, cfg),
    )


def assets(obs, seat=None):
    seat = obs["player"] if seat is None else seat
    return [
        dict(t, site=(x, y))
        for y, row in enumerate(obs["farms"][seat]["tiles"])
        for x, t in enumerate(row)
        if isinstance(t, dict) and (t.get("crop") or t.get("animal"))
    ]


def geometry(obs):
    """Reserve five central animal sites, then compact pads in NE/SW."""
    farm = obs["farms"][obs["player"]]
    n, access = len(farm["tiles"]), shed_access(obs)
    h = n // 2
    pads, fields = [], []
    for name, count in [("NW", 5), ("NE", 6), ("SW", 6), ("SE", 5)]:
        cells = [
            (x, y)
            for y in range(n)
            for x in range(n)
            if ("N" if y < h else "S") + ("W" if x < h else "E") == name
        ]
        cells.sort(key=lambda p: (min(distance(p, a) for a in access), p[1], p[0]))
        if name in farm["unlocked_quadrants"]:
            pads.extend(cells[:count])
            fields.extend(cells[count:])
    return pads, fields


def vacant(tile, animal=False):
    return tile is None or (
        isinstance(tile, dict)
        and not tile.get("animal")
        and tile.get("kind") in (("WEED", "COOP", "PASTURE") if animal else ("WEED",))
    )


def pending_assets(obs, ctx):
    """Bounded, disjoint installation slots. Actual inventory, never order requests."""
    farm, private = obs["farms"][obs["player"]], obs["private"]
    result = assets(obs)
    pads, fields = geometry(obs)
    slots = [p for p in pads + fields if vacant(farm["tiles"][p[1]][p[0]], True)]
    # Carried animals precede depot animals so the installation follows its carrier.
    animal_order = []
    for inv in private["inventories"]:
        for a in ANIMALS:
            animal_order.extend([a] * inv.get(a, 0))
    for a in ANIMALS:
        animal_order.extend([a] * private["shed"].get(a, 0))
    animal_order = [
        a for a in animal_order if ctx["day"] + ANIMALS[a]["first_yield_day"] <= ctx["final"]
    ]
    for a, p in zip(animal_order, slots):
        result.append(dict(animal=a, placed_day=ctx["day"], site=p, install=True))
    used = {t["site"] for t in result}
    # Unoccupied preferred pads remain reserved while an early herd can expand.
    if ctx["day"] >= 14:
        fields += pads
    slots = [p for p in fields if p not in used and vacant(farm["tiles"][p[1]][p[0]])]
    slots.sort(key=lambda p: (min(distance(p, a) for a in ctx["access"]), p))
    for c in ("MELON", "STRAWBERRY", "TOMATO", "CARROT", "WHEAT"):
        spec = CROPS[c]
        if ctx["day"] + spec["first"] > ctx["final"]:
            continue  # Stale seeds cannot earn back even their installation time.
        for _ in range(min(private["seeds"].get(c, 0), len(slots))):
            result.append(dict(crop=c, planted_day=ctx["day"], site=slots.pop(0), plant=True))
    return result


def future_animal(tile, day, final, offset=1):
    spec = ANIMALS[tile["animal"]]
    first = tile["placed_day"] + spec["first_yield_day"]
    next_date = (
        first + max(0, math.ceil((day + offset - first) / spec["interval"])) * spec["interval"]
    )
    return next_date if next_date <= final else None


def fertilizer_due(tile, ctx):
    c, day = tile["crop"], ctx["day"]
    if tile.get("fertilized_until_day", -1) >= day:
        return False
    age, spec = day - tile["planted_day"], CROPS[c]
    if spec["interval"]:
        due = age + 1 - spec["first"]
        return (
            day < ctx["final"]
            and 0 <= due < spec["interval"] * spec["events"]
            and due % spec["interval"] == 0
        )
    return (
        c in ("WHEAT", "CARROT")
        and age in (2, 3)
        and not tile.get("watered_today")
        and tile.get("yield_units", 1) < spec["cap"] - 1
    )


def fertilizer_margin(tile, ctx):
    c = tile.get("crop")
    if c is None:
        return 0
    spec = CROPS[c]
    age = ctx["day"] - tile["planted_day"]
    if spec["interval"]:
        bonus = sum(
            age + k - spec["first"] in range(0, spec["interval"] * spec["events"], spec["interval"])
            for k in (1, 2, 3)
            if ctx["day"] + k <= ctx["final"]
        )
    else:
        waterings = max(0, min(2, 4 - age))
        bonus = max(0, min(waterings, spec["cap"] - tile.get("yield_units", 1) - waterings))
    return bonus * ctx["prices"][c] - ctx["prices"]["FERTILIZER"] - 4


def make_jobs(obs, ctx):
    farm = obs["farms"][obs["player"]]
    jobs = {}
    for a in pending_assets(obs, ctx):
        p = a["site"]
        t = farm["tiles"][p[1]][p[0]]
        ops = []
        urgency = 1
        day, final = ctx["day"], ctx["final"]
        if a.get("install"):
            structure = ANIMALS[a["animal"]]["structure"]
            if t is not None and t.get("kind") != structure:
                ops.append(["DIG"])
            if t is None or t.get("kind") != structure:
                ops.append(["BUILD_" + structure])
            ops += [["PLACE", a["animal"]], ["FEED"], ["CARE"]]
            urgency = 3
        elif a.get("plant"):
            if t is not None:
                ops.append(["DIG"])
            ops += [["PLANT", a["crop"]], ["WATER"]]
            urgency = 3
        elif a.get("animal"):
            production = future_animal(t, day, final)
            if production is not None and not t["fed_today"]:
                ops.append(["FEED"])
                urgency = 5 if t.get("consecutive_unfed") else 3
            if t["yield_units"]:
                ops.append(["HARVEST"])
            spec = ANIMALS[t["animal"]]
            if (
                future_animal(t, day, final, 2) is not None
                and not t["cared_today"]
                and (t["pending_care_bonus"] < spec["max_held"] - 1 or production == day + 1)
            ):
                ops.append(["CARE"])
            if t["fertilizer_available"]:
                ops.append(["COLLECT_FERTILIZER"])
        else:
            c = t["crop"]
            spec = CROPS[c]
            age = day - t["planted_day"]
            units = t.get("yield_units", 0)
            end = spec["first"] + (spec["events"] - 1) * spec["interval"]
            exhausted = bool(spec["interval"]) and age >= end
            ready = age >= spec["first"] and units > 0
            harvest = ready and (
                bool(spec["interval"])
                or age >= spec["harvest"]
                or units >= spec["cap"]
                or day == final
            )
            if c == "WHEAT" and age == 3 and units < 3 and day < final:
                harvest = False
            bonus_water = (
                not spec["interval"]
                and (6 if c == "MELON" else 2)
                <= age
                <= (12 if c == "MELON" else (3 if c == "CARROT" else 4))
                and units < spec["cap"]
            )
            water = not t.get("watered_today") and (
                (day < final and not exhausted) or (harvest and bonus_water)
            )
            if fertilizer_due(t, ctx) and fertilizer_margin(t, ctx) > 0:
                ops.append(["FERTILIZE"])
            if water:
                ops.append(["WATER"])
                urgency = 5 if t.get("consecutive_unwatered") else 2
            if harvest:
                ops.append(["HARVEST"])
            if exhausted and units == 0 and day < final:
                ops.append(["DIG"])
        if ops:
            jobs[p] = dict(ops=ops, asset=a, urgency=urgency)
    return jobs


def ownership(obs, count):
    """Static geographic sectors. Completion flags cannot move sector boundaries."""
    farm = obs["farms"][obs["player"]]
    pads, _ = geometry(obs)
    h = len(farm["tiles"]) / 2 - 0.5
    cells = [
        (x, y) for y, row in enumerate(farm["tiles"]) for x, t in enumerate(row) if t != "LOCKED"
    ]
    cells.sort(key=lambda p: (math.atan2(p[1] - h, p[0] - h), distance(p, (h, h)), p))
    total = sum(4.5 if p in pads else 1.7 for p in cells)
    result, weight = {}, 0
    for p in cells:
        w = 4.5 if p in pads else 1.7
        result[p] = min(count - 1, int((weight + w / 2) * count / max(1, total)))
        weight += w
    return result


def route_order(jobs, owner, worker, access):
    left = {p for p in jobs if owner.get(p) == worker}
    ordered, pos = [], min(access)
    while left:
        p = min(left, key=lambda p: (distance(pos, p), p))
        ordered.append(p)
        left.remove(p)
        pos = p
    return ordered


def needs(ops):
    items = Counter()
    for op in ops:
        if op[0] == "FEED":
            items["WHEAT"] += 1
        if op[0] == "FERTILIZE":
            items["FERTILIZER"] += 1
        if op[0] == "PLACE":
            items[op[1]] += 1
    return items


def prepare_job(job, inv, stock, p, target, ctx):
    """Drop optional unavailable inputs; never postpone survival for fertilizer."""
    ops = [list(o) for o in job["ops"]]
    fert_value = fertilizer_margin(job["asset"], ctx)
    if (
        ctx["day"] == ctx["final"]
        or inv.get("FERTILIZER", 0) + stock.get("FERTILIZER", 0) <= 0
        or fert_value <= 0
    ):
        ops = [o for o in ops if o[0] != "FERTILIZE"]
    # A one-time crop may become full by the immediately preceding WATER.
    requirements = needs(ops)
    if any(inv.get(c, 0) + stock.get(c, 0) < q for c, q in requirements.items()):
        if job["asset"].get("install"):
            return None
        ops = [o for o in ops if o[0] != "FEED" or inv.get("WHEAT", 0) + stock.get("WHEAT", 0) > 0]
    if not ops:
        return None
    requirements = needs(ops)
    missing = [c for c, q in requirements.items() if inv.get(c, 0) < q]
    home = min(ctx["access"], key=lambda a: (distance(p, a) + distance(a, target), a))
    travel = distance(p, home) + distance(home, target) if missing else distance(p, target)
    terminal = ctx["day"] == ctx["final"]
    tail = (
        min(distance(target, a) for a in ctx["access"]) + 1
        if terminal and any(o[0] in ("HARVEST", "COLLECT_FERTILIZER") for o in ops)
        else 0
    )
    cost = travel + len(missing) + len(ops) + tail
    if cost > ctx["remaining"]:
        if job["asset"].get("install") or job["asset"].get("plant"):
            return None  # Never start newborns without time to finish their basic needs.
        # Salvage one necessary operation with its real pickup/delivery cost.
        for name in (
            ("HARVEST", "COLLECT_FERTILIZER")
            if terminal
            else ("FEED", "WATER", "HARVEST", "CARE", "COLLECT_FERTILIZER")
        ):
            simple = [o for o in ops if o[0] == name]
            if not simple:
                continue
            need = needs(simple)
            miss = [c for c, q in need.items() if inv.get(c, 0) < q]
            dist = distance(p, home) + distance(home, target) if miss else distance(p, target)
            end = (
                min(distance(target, a) for a in ctx["access"]) + 1
                if terminal and name in ("HARVEST", "COLLECT_FERTILIZER")
                else 0
            )
            if dist + len(miss) + 1 + end <= ctx["remaining"]:
                return simple, miss, home
        return None
    return ops, missing, home


def dispatch(obs, ctx, jobs):
    farm, private = obs["farms"][obs["player"]], obs["private"]
    positions = [tuple(farm["farmer"]), *map(tuple, farm["hands"])]
    stock = dict(private["shed"])
    carried = [dict(v) for v in private["inventories"]]
    owner = ownership(obs, len(positions))
    routes = {i: route_order(jobs, owner, i, ctx["access"]) for i in range(len(positions))}
    token = (obs["player"], ctx["day"])
    if _MEMORY.get("token") != token or _MEMORY.get("step", -2) not in (
        ctx["step"] - 1,
        ctx["step"],
    ):
        _MEMORY.clear()
        _MEMORY.update(token=token, targets={})
    _MEMORY["step"] = ctx["step"]
    committed = _MEMORY["targets"]
    committed = {
        i: tuple(p) for i, p in committed.items() if i < len(positions) and tuple(p) in jobs
    }
    commands = [["PASS"] for _ in positions]
    taken = set()
    assignments = {}
    # Carriers choose matching installations; shared stock follows engine unit order.
    indices = range(len(positions))  # Engine unit order; earlier deposits may fund later pickups.
    for i in indices:
        p, inv = positions[i], carried[i]
        valuable = sum(inv.get(c, 0) for c in MARKET)
        home = min(ctx["access"], key=lambda a: (distance(p, a), a))
        terminal = ctx["day"] == ctx["final"]
        if terminal and valuable and ctx["remaining"] <= distance(p, home) + 2:
            commands[i] = move_toward(p, home) if p != home else ["PASS"]
            chosen = None
        else:
            protected = {q for k, q in committed.items() if k != i and q not in taken}
            candidates = []
            if i in committed:
                candidates.append(committed[i])
            if p in jobs:
                candidates.append(p)
            candidates += routes[i]
            # Idle workers help outside their zone only after their own feasible work.
            candidates += sorted(jobs, key=lambda q: (distance(p, q), -jobs[q]["urgency"], q))
            chosen = None
            for q in dict.fromkeys(candidates):
                if q in taken or (q in protected and q != p):
                    continue
                fit = prepare_job(jobs[q], inv, stock, p, q, ctx)
                if fit is None:
                    continue
                # A worker carrying an animal must finish that installation first.
                animal = jobs[q]["asset"].get("animal")
                if any(
                    inv.get(a, 0) and ctx["day"] + ANIMALS[a]["first_yield_day"] <= ctx["final"]
                    for a in ANIMALS
                ) and not (jobs[q]["asset"].get("install") and inv.get(animal, 0)):
                    continue
                chosen = q, fit
                break
            if chosen:
                q, (ops, missing, depot) = chosen
                taken.add(q)
                assignments[i] = q
                committed[i] = q
                if missing:
                    if p not in ctx["access"]:
                        commands[i] = move_toward(p, depot)
                    else:
                        item = min(missing, key=lambda c: (c not in ANIMALS, c == "FERTILIZER", c))
                        demand = sum(
                            needs(jobs[z]["ops"]).get(item, 0)
                            for z in routes[i]
                            if z not in taken or z == q
                        )
                        n = min(stock.get(item, 0), max(1, min(4, demand) - inv.get(item, 0)))
                        if item in ANIMALS:
                            n = 1
                        commands[i] = ["PICKUP", item, n]
                elif p != q:
                    commands[i] = move_toward(p, q)
                else:
                    commands[i] = ops[0]
            else:
                committed.pop(i, None)
                if valuable and (terminal or farm["money"] < 1200):
                    commands[i] = move_toward(p, home) if p != home else ["PASS"]
        # Deposit at access when useful, while retaining assigned feed/fertilizer.
        room = ctx["capacity"] - sum(stock.values())
        if p in ctx["access"] and room > 0 and valuable:
            jobneed = needs(jobs[assignments[i]]["ops"]) if i in assignments else {}
            saleable = {
                c: n
                for c, n in inv.items()
                if c in MARKET
                and n > jobneed.get(c, 0)
                and (terminal or c not in ("WHEAT", "FERTILIZER") or not chosen)
            }
            if saleable and (terminal or commands[i][0] == "PASS" or farm["money"] < 1200):
                item = max(saleable, key=lambda c: (ctx["params"][c]["base"] * saleable[c], c))
                n = min(room, saleable[item] - jobneed.get(item, 0))
                if n > 0:
                    commands[i] = ["PLACE", item, int(n)]
        op = commands[i]
        if not terminal and op[0] in ("HARVEST", "COLLECT_FERTILIZER"):
            t = farm["tiles"][p[1]][p[0]]
            addition = t["yield_units"] if op[0] == "HARVEST" else 1
            unsellable = sum(n for c, n in stock.items() if c not in MARKET)
            incoming = sum(sum(v.values()) for v in carried)
            if unsellable + incoming + addition > ctx["capacity"]:
                # Stored field output can wait; excess carried output cannot survive night.
                commands[i] = op = ["PASS"]
        if op[0] == "PICKUP":
            stock[op[1]] -= op[2]
            inv[op[1]] = inv.get(op[1], 0) + op[2]
        elif op[0] == "PLACE":
            q = op[2] if len(op) > 2 else 1
            inv[op[1]] -= q
            if op[1] in MARKET:
                stock[op[1]] = stock.get(op[1], 0) + q
        elif op[0] in ("FEED", "FERTILIZE"):
            c = "WHEAT" if op[0] == "FEED" else "FERTILIZER"
            inv[c] -= 1
        elif op[0] == "COLLECT_FERTILIZER":
            inv["FERTILIZER"] = inv.get("FERTILIZER", 0) + 1
        elif op[0] == "HARVEST":
            tile = farm["tiles"][p[1]][p[0]]
            c = tile.get("crop") or ANIMALS[tile["animal"]]["product"]
            inv[c] = inv.get(c, 0) + tile["yield_units"]
    _MEMORY["targets"] = assignments
    return commands, stock, carried, assignments


def production_rates(obs, ctx):
    """Visible portfolios only. Conservative full-care capacity, not hidden stocks."""
    rates = Counter()
    for seat in (0, 1):
        for t in assets(obs, seat):
            if t.get("animal"):
                s = ANIMALS[t["animal"]]
                rates[s["product"]] += (s["interval"] + 1) / s["interval"]
            else:
                c = t["crop"]
                s = CROPS[c]
                rates[c] += (
                    1.7 * s["events"] / (s["first"] + (s["events"] - 1) * s["interval"] + 1)
                    if s["interval"]
                    else (4 if c == "WHEAT" else s["cap"]) / (s["harvest"] + 1)
                )
    return rates


def expected_price(obs, ctx, item, horizon, rates, extra=0):
    inventory = obs["market"]["inventory"][item]
    # No unrevealed shops are assumed. Current crop/animal capacity supplies both sides.
    future = inventory + (rates[item] - ctx["demand"][item]) * horizon + extra
    now = price_at(item, inventory, ctx["params"])
    later = price_at(item, future, ctx["params"])
    return max(1, 0.35 * now + 0.65 * later)


def crop_value(obs, ctx, c, rates):
    s = CROPS[c]
    available = ctx["final"] - ctx["day"] - 1
    if available < s["first"]:
        return -1e9
    events = min(s["events"], 1 + (available - s["first"]) // s["interval"]) if s["interval"] else 1
    life = s["first"] + (events - 1) * s["interval"] + 1 if s["interval"] else s["harvest"] + 1
    yield_units = events * 1.7 if s["interval"] else (4.2 if c == "WHEAT" else s["cap"])
    quote = expected_price(obs, ctx, c, life, rates, yield_units * 2)
    fert = events / 2 if s["interval"] else (1 if c in ("WHEAT", "CARROT") else 0)
    fert_cost = price_at("FERTILIZER", obs["market"]["inventory"]["FERTILIZER"], ctx["params"])
    # CO shadow price is an explicit heuristic; it is not an LP dual certificate.
    work = life + events + 2 + fert
    net = quote * yield_units - s["seed"] - fert * fert_cost - work * 4
    plain_units = events if s["interval"] else (3 if c in ("WHEAT", "CARROT") else s["cap"])
    plain_net = quote * plain_units - s["seed"] - (work - fert) * 4
    net = max(net, plain_net)  # Optional fertilizer must not make a viable plain crop inadmissible.
    if s["interval"] and events < 2:
        net *= 0.6
    return net / (life + work * 0.25)


def animal_value(obs, ctx, a, rates):
    s = ANIMALS[a]
    life = ctx["final"] - ctx["day"] - 1
    if life < s["first_yield_day"] + s["interval"]:
        return -1e9
    events = 1 + (life - s["first_yield_day"]) // s["interval"]
    output = min(s["max_held"], s["first_yield_day"]) + (events - 1) * (s["interval"] + 1)
    product = s["product"]
    price = expected_price(obs, ctx, product, life / 2, rates, output * 0.5)
    feed = expected_price(obs, ctx, "WHEAT", life / 2, rates)
    fertilizer = (
        min(40, price_at("FERTILIZER", obs["market"]["inventory"]["FERTILIZER"], ctx["params"]))
        * 0.6
    )
    net = 0.8 * output * price - s["cost"] - life * feed + life * fertilizer - (life * 4 + 8) * 4
    return net / (life * 4 + 8)


def market_orders(obs, cfg, ctx, commands, stock, carried, jobs, assignments=None):
    farm = obs["farms"][obs["player"]]
    limit = cfg.get("maxMarketOrdersPerTurn", 10)
    orders = []
    cash = float(farm["money"])
    rates = production_rates(obs, ctx)
    all_assets = pending_assets(obs, ctx)
    live = [
        t
        for t in all_assets
        if t.get("animal") and future_animal(t, ctx["day"], ctx["final"]) is not None
    ]
    positions = [tuple(farm["farmer"]), *map(tuple, farm["hands"])]
    fed = {p for p, o in zip(positions, commands) if o[0] == "FEED"}
    hungry_sites = {
        t["site"] for t in live if not t.get("fed_today", False) and t["site"] not in fed
    }
    owner = ownership(obs, len(positions))
    credit = set()
    for i, inv in enumerate(carried):
        route_sites = sorted(
            p for p in hungry_sites - credit if owner.get(p) == i or (assignments or {}).get(i) == p
        )
        credit.update(route_sites[: inv.get("WHEAT", 0)])
    tomorrow = min(4, len(live)) if ctx["day"] < ctx["final"] - 1 else 0
    spare = max(0, sum(v.get("WHEAT", 0) for v in carried) - len(credit))
    feed_keep = len(hungry_sites - credit) + max(0, tomorrow - spare)
    applied = {p for p, o in zip(positions, commands) if o[0] == "FERTILIZE"}
    fert_keep = sum(
        any(op[0] == "FERTILIZE" for op in j["ops"]) and p not in applied for p, j in jobs.items()
    )
    fert_keep = min(fert_keep + 2, 12) if ctx["day"] < ctx["final"] else 0
    keep = {"WHEAT": feed_keep, "FERTILIZER": fert_keep}
    cargo = sum(sum(v.values()) for v in carried)
    stock = dict(stock)
    schedule = (
        4
        if ctx["day"] < 2
        else 6
        if ctx["day"] < 6
        else 8
        if ctx["day"] == 6
        else 9
        if ctx["day"] < 9
        else 11
        if ctx["day"] < 28
        else 10
    )
    if ctx["remaining"] < 5:
        schedule = len(farm["hands"])
    wage = sum(hire_cost(i, cfg.get("farmHandCostMult", 1)) for i in range(schedule))
    reserve = (
        wage
        + len(live)
        * max(1, price_at("WHEAT", obs["market"]["inventory"]["WHEAT"] - 20, ctx["params"]))
        + 40
    )
    candidates = []
    for c in MARKET:
        qty = max(0, stock.get(c, 0) - keep.get(c, 0))
        if not qty:
            continue
        if (
            c not in ("WHEAT", "FERTILIZER")
            and ctx["day"] < ctx["final"] - 1
            and cash > reserve + 1000
            and sum(stock.values()) + cargo < ctx["capacity"] * 0.7
        ):
            now = price_at(c, obs["market"]["inventory"][c], ctx["params"])
            if expected_price(obs, ctx, c, 1, rates) > now * 1.05:
                qty = max(0, qty - min(10, int(ctx["demand"][c])))
        if qty:
            loss = (
                price_at(c, obs["market"]["inventory"][c], ctx["params"])
                - price_at(c, obs["market"]["inventory"][c] + 20, ctx["params"])
            ) * qty
            candidates.append((loss, c, qty))
    # Clear carried-stock headroom before night, even if input reserves are overfull.
    projected = sum(stock.values()) + cargo - sum(q for _, _, q in candidates)
    for c in ("FERTILIZER", "WHEAT"):
        extra = min(
            max(0, projected - ctx["capacity"]),
            max(0, stock.get(c, 0) - sum(q for _, z, q in candidates if z == c)),
        )
        if extra:
            candidates = (
                [(v, z, q + extra if z == c else q) for v, z, q in candidates]
                if any(z == c for _, z, _ in candidates)
                else candidates + [(0, c, extra)]
            )
            projected -= extra
    for _, c, q in sorted(candidates, reverse=True):
        if len(orders) >= limit:
            break
        orders.append(["SELL", c, int(q)])
        stock[c] -= q
        # Stress competing sales; these proceeds are a budget estimate, never a fill claim.
        cash += 0.8 * batch_revenue(c, obs["market"]["inventory"][c] + 32, int(q), ctx["params"])

    def buy(kind, item, n, buffer=0):
        nonlocal cash
        n = int(n)
        if n <= 0 or len(orders) >= limit:
            return 0
        if kind == "BUY_SEED":
            unit = CROPS[item]["seed"]
        elif kind == "BUY_ANIMAL":
            unit = ANIMALS[item]["cost"]
        else:
            unit = price_at(item, obs["market"]["inventory"][item] - n - 20, ctx["params"])
        n = min(n, max(0, int((cash - buffer) // max(1, unit))))
        if kind != "BUY_SEED":
            n = min(n, max(0, ctx["capacity"] - sum(stock.values()) - cargo))
        if n:
            orders.append([kind, item, n])
            cash -= n * unit
            if kind != "BUY_SEED":
                stock[item] = stock.get(item, 0) + n
        return n

    # Feed is an operating obligation, not residual spending after maximum hiring.
    # Retain the seven coins needed for the first four hands when the day starts poor.
    if ctx["day"] < ctx["final"]:
        starter_wages = (
            sum(
                hire_cost(i, cfg.get("farmHandCostMult", 1))
                for i in range(farm["hires_today"], min(4, schedule))
            )
            if ctx["hour"] <= 1
            else 0
        )
        buy(
            "BUY_PRODUCT",
            "WHEAT",
            max(0, feed_keep - stock.get("WHEAT", 0)),
            buffer=min(cash, starter_wages),
        )
    # Hires only near dawn; assets installed today are serviced by a complete crew.
    if ctx["hour"] <= 1:
        for i in range(farm["hires_today"], schedule):
            cost = hire_cost(i, cfg.get("farmHandCostMult", 1))
            if cash < cost or len(orders) >= limit:
                break
            orders.append(["HIRE"])
            cash -= cost
    counts = Counter(t.get("crop") or t.get("animal") for t in all_assets)
    installed = Counter(t.get("crop") or t.get("animal") for t in assets(obs))
    pads, fields = geometry(obs)
    if ctx["day"] >= 14:
        fields += pads
    unplaced = sum(t.get("install", False) for t in all_assets)
    queued = sum(t.get("plant", False) for t in all_assets)
    newborn = sum(
        bool(t.get("crop")) and t["planted_day"] == ctx["day"] and not t.get("watered_today")
        for t in assets(obs)
    )
    room_fields = sum(vacant(farm["tiles"][y][x]) for x, y in fields)
    day = ctx["day"]
    changes = []
    if day < 2:
        for a, target in [("COW", 2), ("SHEEP", 3)]:
            n = buy("BUY_ANIMAL", a, max(0, target - counts[a]), buffer=30)
            if n:
                changes.append((a, n))
                counts[a] += n
        # Purchased animals need feed even before they exist as tile jobs.
        buy("BUY_PRODUCT", "WHEAT", max(0, sum(counts[a] for a in ANIMALS) - stock.get("WHEAT", 0)))
        # The opening has ten wheat and twelve staggered melons, as in both records.
        if day == 0 and counts["WHEAT"] < 10:
            n = buy(
                "BUY_SEED",
                "WHEAT",
                min(10 - counts["WHEAT"], max(0, room_fields - queued)),
                buffer=50,
            )
            queued += n
    if day <= 3 and counts["MELON"] < 12:
        n = buy(
            "BUY_SEED",
            "MELON",
            min(2, 12 - counts["MELON"], max(0, room_fields - queued)),
            buffer=30,
        )
        queued += n
    # An explicit expansion window replaces the seed-backlog veto.
    owned = len(farm["unlocked_quadrants"])
    land_cost = (1000, 2000, 4000)[owned - 1] if owned < 4 else 0
    due = (owned == 1 and day >= 6) or (owned == 2 and day >= 9)
    utilized = sum(installed.values())
    if (
        due
        and day <= 14
        and utilized >= 15
        and len(orders) < limit
        and cash >= land_cost + reserve + 300
    ):
        orders.append(["BUY_LAND"])
        cash -= land_cost
        changes.append(("LAND", 1))
    if 6 <= day <= 18 and unplaced < 2 and len(orders) < limit:
        animal_room = sum(vacant(farm["tiles"][y][x], True) for x, y in pads) - unplaced
        choices = []
        for a in ANIMALS:
            product = ANIMALS[a]["product"]
            if ctx["demand"][product] <= 1:
                continue
            productivity = (ANIMALS[a]["interval"] + 1) / ANIMALS[a]["interval"]
            market_cap = math.ceil(0.8 * ctx["demand"][product] / productivity) + 1
            if counts[a] >= max({"COW": 2, "SHEEP": 3, "GOOSE": 0}[a], market_cap):
                continue
            value = animal_value(obs, ctx, a, rates)
            if value > 0:
                choices.append((value, a))
        if choices and animal_room > 0 and sum(counts[a] for a in ANIMALS) < 17:
            value, a = max(choices)
            if buy("BUY_ANIMAL", a, 1, buffer=reserve + 120):
                changes.append((a, 1))
    # Small queues are permitted, but never disable other investment categories.
    # New plots must fit before night; observed early delays cannot be hidden by seed value.
    if day >= 2 and ctx["hour"] <= ctx["tpd"] - 7 and queued + newborn < 4 and room_fields > queued:
        choices = []
        for c in ("STRAWBERRY", "TOMATO", "CARROT", "WHEAT"):
            if c in ("TOMATO", "CARROT") and ctx["demand"][c] <= 1:
                continue
            if c == "STRAWBERRY" and day > ctx["final"] - 12:
                continue
            value = crop_value(obs, ctx, c, rates)
            if value > 0:
                choices.append((value, c))
        if choices:
            value, c = max(choices)
            n = buy(
                "BUY_SEED",
                c,
                min(2, 4 - queued - newborn, room_fields - queued),
                buffer=max(30, reserve * 0.4),
            )
            if n:
                changes.append((c, n))
    return orders, dict(
        changes=changes,
        reserve=reserve,
        feed_keep=feed_keep,
        projected_shed=sum(stock.values()) + cargo,
        crew_target=schedule,
    )


def turn(obs, configuration=None):
    cfg = configuration or {}
    ctx = context(obs, cfg)
    jobs = make_jobs(obs, ctx)
    commands, stock, carried, assignments = dispatch(obs, ctx, jobs)
    orders, report = market_orders(obs, cfg, ctx, commands, stock, carried, jobs, assignments)
    return dict(farmer=commands[0], hands=commands[1:], market=orders), dict(
        assignments=assignments, market=report
    )


def agent(observation, configuration=None):
    return turn(observation, configuration)[0]
