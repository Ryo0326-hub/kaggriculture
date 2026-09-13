"""Fresh Cycle 1: observation-driven farming with reserved, persistent visits.

Written independently of all previous agents. Constants describe the pinned
game rules; exact assignment/deposit subproblems use heuristic economic values.
No engine, local modules, network, randomness, or filesystem access at runtime.
"""

import math

# seed, first harvest age, preferred harvest age, repeat interval, yield cap
CROPS = {
    "WHEAT": (10, 2, 4, 0, 6),
    "CARROT": (20, 2, 3, 0, 4),
    "MELON": (80, 10, 10, 0, 6),
    "TOMATO": (50, 8, 8, 1, 4),
    "STRAWBERRY": (100, 10, 10, 2, 4),
}
# cost, first production age, interval, product, structure
ANIMALS = {
    "COW": (400, 8, 2, "MILK", "PASTURE"),
    "SHEEP": (500, 6, 3, "WOOL", "PASTURE"),
    "GOOSE": (300, 4, 1, "EGG", "COOP"),
}
# base, scale T, below function/target, above function/target
CURVES = {
    "WHEAT": (25, 400, "sqrt", 0.8, "log", 0.2),
    "CARROT": (35, 450, "hinge", 1.0, "sqrt", 0.7),
    "MELON": (250, 300, "log", 0.2, "sq", 3.6),
    "TOMATO": (60, 200, "hinge", 0.4, "sqrt", 0.6),
    "STRAWBERRY": (120, 100, "sqrt", 0.7, "linear", 1.6),
    "MILK": (160, 122, "sqrt", 0.6, "linear", 1.6),
    "WOOL": (200, 105, "log", 0.2, "sq", 3.2),
    "EGG": (50, 332, "hinge", 0.4, "log", 0.2),
    "FERTILIZER": (100, 200, "linear", 0.4, "linear", 0.4),
}
SHOPS = {
    "BAKERY": ("EGG", "WHEAT"),
    "PIZZA_SHOP": ("MILK", "TOMATO", "WHEAT"),
    "BRUNCH_SPOT": ("EGG", "WHEAT", "STRAWBERRY"),
    "YARN_STORE": ("WOOL",),
    "ICE_CREAM_SHOP": ("STRAWBERRY", "MILK", "WHEAT"),
    "PET_CAFE": ("CARROT",),
    "SMOOTHIE_SHOP": ("STRAWBERRY", "MILK"),
    "FARMERS_MARKET": ("WHEAT", "CARROT", "TOMATO", "STRAWBERRY"),
}
MOVES = {"NORTH": (0, -1), "SOUTH": (0, 1), "EAST": (1, 0), "WEST": (-1, 0)}
_MEMORY = {}


def distance(a, b):
    return abs(a[0] - b[0]) + abs(a[1] - b[1])


def move(a, b):
    # Fixed tie breaking prevents a changing route preference on equal paths.
    if a[0] != b[0]:
        return ["EAST" if a[0] < b[0] else "WEST"]
    if a[1] != b[1]:
        return ["SOUTH" if a[1] < b[1] else "NORTH"]
    return ["PASS"]


def shape(name, x, scale):
    x = max(0, x)
    if name == "sq":
        return x * x
    if name == "sqrt":
        return math.sqrt(x)
    if name == "log":
        return math.log1p(x)
    if name == "log10":
        return math.log10(1 + x)
    if name == "hinge" and scale > 0:
        u = x / scale
        return u + 8 * max(0, u - 1) ** 2
    return x


def quoted_price(item, inventory, overrides=None):
    base, scale, below, bt, above, at = CURVES[item]
    p = {
        "base": base,
        "T": scale,
        "I0": 10000,
        "below_func": below,
        "below_target": bt,
        "above_func": above,
        "above_target": at,
    }
    p.update((overrides or {}).get(item, {}))
    delta = inventory - p["I0"]
    side = "below" if delta < 0 else "above"
    f = p[side + "_func"]
    change = p["base"] * p[side + "_target"] * shape(f, abs(delta), p["T"])
    change /= max(1e-9, shape(f, p["T"], p["T"]))
    return max(1, round(p["base"] + (-change if delta >= 0 else change)))


def fib(index):
    a = b = 1
    for _ in range(index):
        a, b = b, a + b
    return a


def maximum_weight_matching(weights):
    """Rectangular assignment with one private idle column per worker.

    Hungarian potentials: O(workers**2 * (jobs + workers)); None forbids an
    edge. This solves the supplied additive weights, not an entire farm plan.
    """
    n = len(weights)
    if not n:
        return []
    jobs = len(weights[0])
    m = jobs + n
    u, v, owner, previous = [0.0] * (n + 1), [0.0] * (m + 1), [0] * (m + 1), [0] * (m + 1)
    for worker in range(1, n + 1):
        owner[0] = worker
        column = 0
        distance_to, seen = [math.inf] * (m + 1), [False] * (m + 1)
        while True:
            seen[column] = True
            row, delta, next_column = owner[column], math.inf, 0
            for j in range(1, m + 1):
                if seen[j]:
                    continue
                weight = weights[row - 1][j - 1] if j <= jobs else 0
                cost = math.inf if weight is None else -weight
                reduced = cost - u[row] - v[j]
                if reduced < distance_to[j]:
                    distance_to[j], previous[j] = reduced, column
                if distance_to[j] < delta:
                    delta, next_column = distance_to[j], j
            for j in range(m + 1):
                if seen[j]:
                    u[owner[j]] += delta
                    v[j] -= delta
                else:
                    distance_to[j] -= delta
            column = next_column
            if owner[column] == 0:
                break
        while column:
            parent = previous[column]
            owner[column] = owner[parent]
            column = parent
    return [(owner[j] - 1, j - 1) for j in range(1, jobs + 1) if owner[j]]


class Planner:
    def __init__(self, obs, config):
        self.obs = obs
        self.cfg = config or {}
        self.seat = int(obs.get("player", 0))
        self.farm = obs["farms"][self.seat]
        self.tiles = self.farm["tiles"]
        self.size = len(self.tiles)
        half = self.size // 2
        self.access = [(x, y) for y in (half - 1, half) for x in (half - 1, half)]
        self.day, self.hour = int(obs.get("day", 0)), int(obs.get("hour", 0))
        self.tpd = max(1, int(self.cfg.get("turnsPerDay", 24)))
        self.step = self.day * self.tpd + self.hour
        self.last = int(self.cfg.get("episodeSteps", 720)) - 2
        self.final_day = self.last // self.tpd
        self.left = min(self.tpd - self.hour, self.last - self.step + 1)
        self.terminal = self.day == self.final_day
        self.positions = [tuple(self.farm["farmer"])] + [tuple(p) for p in self.farm["hands"]]
        private = obs.get("private", {})
        inventories = private.get("inventories", [])
        self.carry = [
            dict(inventories[i]) if i < len(inventories) else {} for i in range(len(self.positions))
        ]
        self.shed = dict(private.get("shed", {}))
        self.seeds = dict(private.get("seeds", {}))
        self.capacity = int(self.cfg.get("shedCapacity", 100))
        self.market = dict(obs.get("market", {}).get("inventory", {}))
        self.params = obs.get("market", {}).get("params") or self.cfg.get("marketParams", {})
        self.prices = {p: quoted_price(p, self.market.get(p, 10000), self.params) for p in CURVES}
        self.sites = {
            (x, y): t
            for y, row in enumerate(self.tiles)
            for x, t in enumerate(row)
            if t != "LOCKED"
        }
        self.animals = {
            p: t for p, t in self.sites.items() if isinstance(t, dict) and "animal" in t
        }
        self.plants = {
            p: t for p, t in self.sites.items() if isinstance(t, dict) and t.get("kind") == "PLANT"
        }
        self.feed_count = sum(
            self.useful_animal(t) and not t.get("fed_today", False) for t in self.animals.values()
        )
        self.future_animals = sum(self.useful_animal(t) for t in self.animals.values())
        self.jobs = {}
        self.assignments = {}
        self.reserved = {}
        self.claimed = set()
        self.switches = []
        self.cash = float(self.farm["money"])
        self.orders = []
        self.max_orders = int(self.cfg.get("maxMarketOrdersPerTurn", 10))
        self.demand = {
            p: (
                0
                if p == "FERTILIZER"
                else self.tpd / max(1, self.cfg.get("townCenterSellInterval", 24))
            )
            for p in CURVES
        }
        for shop in obs.get("town", {}).get("unlocked_shops", []):
            items = SHOPS.get(shop, ())
            rate = self.tpd / max(1, self.cfg.get("townShopSellInterval", 4))
            for item in items:
                self.demand[item] += rate * (2 if len(items) == 1 else 1)
        self._supply_cache = {}
        self._receipt_cache = {}
        self.supply = self.visible_supply()

    def nearest_shed(self, pos, target=None):
        return min(
            self.access,
            key=lambda s: (
                distance(pos, s) + (distance(s, target) if target is not None else 0),
                s,
            ),
        )

    def home_distance(self, pos):
        return distance(pos, self.nearest_shed(pos))

    def useful_animal(self, tile):
        _, first, interval, _, _ = ANIMALS[tile["animal"]]
        first_day = tile["placed_day"] + first
        next_day = max(self.day + 1, first_day)
        next_day += (first_day - next_day) % interval
        return next_day <= self.final_day

    def production_night(self, tile):
        _, first, _, interval, cap = CROPS[tile["crop"]]
        age = self.day + 1 - tile["planted_day"]
        return bool(
            interval
            and first <= age <= first + (cap - 1) * interval
            and (age - first) % interval == 0
        )

    def visible_supply(self, horizon=5):
        """Horizon-specific output estimate, not a hidden-stock or fill prediction."""
        horizon = min(horizon, max(0, self.final_day - self.day))
        if horizon in self._supply_cache:
            return self._supply_cache[horizon]
        supply = dict.fromkeys(CURVES, 0.0)
        if horizon <= 0:
            return supply

        def events(first, interval, last):
            next_day = max(self.day + 1, first)
            next_day += (first - next_day) % interval
            return max(0, int((min(self.day + horizon, last) - next_day) // interval) + 1)

        for seat, farm in enumerate(self.obs["farms"]):
            reliability = 1.0 if seat == self.seat else 0.7
            cells = [t for row in farm["tiles"] for t in row if isinstance(t, dict)]
            animals = sum(bool(t.get("animal")) for t in cells)
            crops = sum(t.get("kind") == "PLANT" for t in cells)
            crew = 1 + len(farm["hands"])
            # A conservative observable service-capacity discount, not a fitted
            # probability. Cash alone does not reveal future staffing decisions.
            service = min(1, crew * max(1, self.tpd - 4) / max(1, 3 * animals + crops))
            if seat != self.seat:
                reliability *= service
            for row in farm["tiles"]:
                for tile in row:
                    if not isinstance(tile, dict):
                        continue
                    if tile.get("animal"):
                        _, first, interval, product, _ = ANIMALS[tile["animal"]]
                        if self.useful_animal(tile):
                            animal_reliability = reliability
                            if seat != self.seat and not tile.get("fed_today", False):
                                animal_reliability /= 1 + tile.get("consecutive_unfed", 0)
                            care = min(
                                1,
                                (
                                    tile.get("pending_care_bonus", 0)
                                    + int(tile.get("cared_today", False))
                                )
                                / (interval + 1),
                            )
                            # Future service can recover: neglect discounts rather
                            # than certifies zero future output. Today's CARE is
                            # not credited to today's scheduled production.
                            per_event = 1 + interval * (0.25 + 0.75 * care)
                            count = events(tile["placed_day"] + first, interval, self.final_day)
                            output = tile.get("yield_units", 0) + count * per_event
                            supply[product] += animal_reliability * output / horizon
                            supply["FERTILIZER"] += animal_reliability * 0.8
                            supply["WHEAT"] -= animal_reliability
                    elif tile.get("kind") == "PLANT":
                        crop = tile["crop"]
                        _, first, preferred, interval, cap = CROPS[crop]
                        age = self.day - tile["planted_day"]
                        if interval:
                            first_day = tile["planted_day"] + first
                            count = events(first_day, interval, first_day + (cap - 1) * interval)
                            output = tile.get("yield_units", 0) + 2 * count
                            supply[crop] += reliability * output / horizon
                        else:
                            quantity = {"WHEAT": 4, "CARROT": 3, "MELON": 6}[crop]
                            if age + horizon >= first:
                                supply[crop] += (
                                    reliability
                                    * max(quantity, tile.get("yield_units", 0))
                                    / horizon
                                )
        # Purchased but undeployed seeds still represent committed exposure.
        for crop, quantity in self.seeds.items():
            if crop in CROPS:
                if horizon >= CROPS[crop][1] + 1:
                    supply[crop] += quantity * (2 if CROPS[crop][3] else 4) / horizon
        self._supply_cache[horizon] = supply
        return supply

    def value_price(self, item, horizon=5, extra=0):
        horizon = min(horizon, max(0, self.final_day - self.day))
        inventory = self.market.get(item, 10000)
        forecast = (
            inventory + (self.visible_supply(horizon)[item] - self.demand[item]) * horizon + extra
        )
        future = quoted_price(item, forecast, self.params)
        # Explicit uncertainty blend; neither capacity nor a price is a promised fill.
        return 0.4 * self.prices[item] + 0.6 * future

    def investment(self, item):
        remaining = self.final_day - self.day
        if item in CROPS:
            cost, first, preferred, interval, cap = CROPS[item]
            if remaining < first + 1:
                return -1, 0
            events = min(cap, 1 + (remaining - first - 1) // interval) if interval else 1
            quantity = events * 2 if interval else {"WHEAT": 4, "CARROT": 3, "MELON": 6}[item]
            duration = min(remaining, first + (events - 1) * interval if interval else preferred)
            work = 3 + duration * 1.15 + events
            fertilizer = math.ceil(events / 2) if interval else (1 if item == "MELON" else 0)
            income = quantity * self.value_price(item, min(10, first), quantity)
            margin = income - cost - fertilizer * self.value_price("FERTILIZER") - 7 * work
            return margin / work, margin
        cost, first, interval, product, _ = ANIMALS[item]
        if remaining < first + 2:
            return -1, 0
        events = 1 + (remaining - first - 1) // interval
        quantity = (interval + 1) * events
        work = 4 + remaining * 3.8
        income = quantity * self.value_price(product, min(10, first), quantity / 2)
        income += max(0, remaining - 2) * 0.8 * self.value_price("FERTILIZER", 8)
        margin = income - cost - remaining * self.value_price("WHEAT") - 7 * work
        return margin / work, margin

    def add_job(self, pos, operations, value, deadline=None, essential=False, kind="service"):
        if not operations:
            return
        self.jobs[pos] = {
            "pos": pos,
            "ops": operations,
            "value": max(1, value),
            "deadline": self.step + self.left - 1 if deadline is None else deadline,
            "essential": essential,
            "kind": kind,
        }

    def crop_job(self, pos, tile):
        crop = tile["crop"]
        _, first, preferred, interval, cap = CROPS[crop]
        age = self.day - tile["planted_day"]
        yield_units = tile.get("yield_units", 0)
        ripe = age >= first and yield_units > 0
        expiry = tile.get("max_lifespan_step", -1)
        deadline = self.step + self.left - 1
        if expiry >= 0 and ripe:
            decay = expiry if self.step <= expiry else self.step + (self.step - expiry) % 2
            deadline = min(deadline, decay)
        exhausted = bool(interval and age >= first + (cap - 1) * interval)
        terminal_harvest = self.terminal and ripe
        harvest = ripe and (
            interval
            or age >= preferred
            or terminal_harvest
            or (expiry >= 0 and expiry <= self.step + self.left)
        )
        if harvest and (terminal_harvest or deadline <= self.step + 1 or exhausted):
            self.add_job(pos, [["HARVEST"]], yield_units * self.prices[crop], deadline, True)
            return
        if exhausted and not yield_units:
            self.add_job(pos, [["DIG"]], 5, kind="clear")
            return
        if self.terminal and not ripe:
            return
        window_end = 12 if crop == "MELON" else preferred
        growth = not interval and (window_end + 1) // 2 <= age <= window_end and yield_units < cap
        watered = tile.get("watered_today", False)
        # Safe skip only with zero drought and no growth/production benefit.
        water = not watered and (
            tile.get("consecutive_unwatered", 1) >= 1 or growth or self.production_night(tile)
        )
        operations = []
        fertilizer = tile.get("fertilized_until_day", -1) < self.day
        fertilizer_gain = self.prices[crop] * (2 if interval == 2 else 1)
        fertilizer_worth = fertilizer_gain > self.prices["FERTILIZER"] + 18
        # Optional input never blocks survival. Only use carried fertilizer or
        # a shed supply when a worker is already on a shed tile (see route()).
        if (
            fertilizer
            and fertilizer_worth
            and (self.production_night(tile) or (growth and not watered))
        ):
            operations.append(["FERTILIZE"])
        if water:
            operations.append(["WATER"])
        if harvest:
            operations.append(["HARVEST"])
        essential = bool(water or harvest)
        value = yield_units * self.prices[crop] if harvest else 0
        value += self.prices[crop] * (2 if water else 0.3)
        self.add_job(pos, operations, value, deadline, essential)

    def make_jobs(self):
        for pos, tile in self.animals.items():
            operations = []
            useful = self.useful_animal(tile)
            if useful and not tile.get("fed_today", False):
                operations.append(["FEED"])
            if tile.get("yield_units", 0):
                operations.append(["HARVEST"])
            if useful and not tile.get("cared_today", False):
                operations.append(["CARE"])
            if tile.get("fertilizer_available", False):
                operations.append(["COLLECT_FERTILIZER"])
            product = ANIMALS[tile["animal"]][3]
            value = tile.get("yield_units", 0) * self.prices[product]
            value += (self.prices[product] + self.prices["FERTILIZER"]) if useful else 0
            if tile.get("fertilizer_available", False):
                value += self.prices["FERTILIZER"]
            self.add_job(
                pos,
                operations,
                value,
                essential=useful or bool(tile.get("yield_units")),
                kind="animal",
            )
        for pos, tile in self.plants.items():
            self.crop_job(pos, tile)

        # Install already purchased animals first; ownership binds one item to
        # one pad. Retain pads on subsequent calls so two empty sites cannot swap.
        pending = {
            a: self.shed.get(a, 0) + sum(inv.get(a, 0) for inv in self.carry) for a in ANIMALS
        }
        pads = [
            p
            for p, t in self.sites.items()
            if p not in self.jobs
            and (
                t is None
                or (
                    isinstance(t, dict)
                    and t.get("kind") in ("WEED", "COOP", "PASTURE")
                    and "animal" not in t
                )
            )
        ]
        old = _MEMORY.get("targets", {})
        pads.sort(
            key=lambda p: (
                0 if any(tuple(v[0]) == p and v[1] == "install" for v in old.values()) else 1,
                self.home_distance(p),
                p,
            )
        )
        for animal, count in pending.items():
            for _ in range(count):
                matches = [
                    p
                    for p in pads
                    if not isinstance(self.sites[p], dict)
                    or self.sites[p].get("kind") in ("WEED", ANIMALS[animal][4])
                ]
                if not matches:
                    break
                matches.sort(
                    key=lambda p: (
                        not any(
                            self.positions[i] == p and inv.get(animal, 0)
                            for i, inv in enumerate(self.carry)
                        ),
                        not (
                            isinstance(self.sites[p], dict)
                            and self.sites[p].get("kind") == ANIMALS[animal][4]
                        ),
                        pads.index(p),
                    )
                )
                p = matches[0]
                pads.remove(p)
                tile = self.sites[p]
                ops = []
                if isinstance(tile, dict) and tile.get("kind") == "WEED":
                    ops.append(["DIG"])
                if tile is None or (isinstance(tile, dict) and tile.get("kind") == "WEED"):
                    ops.append(["BUILD_" + ANIMALS[animal][4]])
                ops.append(["PLACE", animal])
                # A placement must leave time for a feeding visit as well.
                self.add_job(
                    p, ops, 500 + ANIMALS[animal][0], self.step + self.left - 3, True, "install"
                )

        seeds = dict(self.seeds)
        # Preserve a small central installation area while animals can repay.
        # It is a layout choice, not a prescribed opening purchase sequence.
        animal_viable = any(self.investment(a)[0] > 0 for a in ANIMALS)
        central = (
            sorted(self.sites, key=lambda p: (self.home_distance(p), p))[
                : min(16, 6 * len(self.farm.get("unlocked_quadrants", ["NW"])))
            ]
            if animal_viable
            else []
        )
        empty = [
            p
            for p, t in self.sites.items()
            if t is None and p not in self.jobs and p not in central
        ]
        # Preserve planting targets, then prefer short trips from actual workers.
        empty.sort(
            key=lambda p: (
                0 if any(tuple(v[0]) == p for v in old.values()) else 1,
                min(distance(p, q) for q in self.positions),
                p,
            )
        )
        ranked = sorted(CROPS, key=lambda c: (-self.investment(c)[0], c))
        for p in empty:
            crop = next(
                (
                    c
                    for c in ranked
                    if seeds.get(c, 0) > 0 and self.final_day - self.day >= CROPS[c][1]
                ),
                None,
            )
            if crop is None:
                break
            seeds[crop] -= 1
            self.add_job(
                p,
                [["PLANT", crop], ["WATER"]],
                max(20, self.investment(crop)[1]),
                self.step + self.left - 1,
                False,
                "plant",
            )
        if not self.terminal:
            for p, tile in self.sites.items():
                if p not in self.jobs and isinstance(tile, dict) and "animal" not in tile:
                    if tile.get("kind") in ("WEED", "COOP", "PASTURE"):
                        self.add_job(p, [["DIG"]], 8, kind="clear")

    def route(self, worker, job, available):
        inv, pos, target = self.carry[worker], self.positions[worker], job["pos"]
        operations = [list(op) for op in job["ops"]]
        needed = {}
        for op in operations:
            if op[0] == "FEED" and inv.get("WHEAT", 0) <= 0:
                needed["WHEAT"] = 1
            elif op[0] == "PLACE" and op[1] in ANIMALS and not inv.get(op[1], 0):
                needed[op[1]] = 1
        if ["FERTILIZE"] in operations and inv.get("FERTILIZER", 0) <= 0:
            if pos in self.access and available.get("FERTILIZER", 0) > 0:
                needed["FERTILIZER"] = 1
            else:
                operations.remove(["FERTILIZE"])
        via = self.nearest_shed(pos, target)

        def costs():
            travel = distance(pos, target)
            if needed:
                travel = distance(pos, via) + distance(via, target) + len(needed)
            service = travel + len(operations)
            total = service + (self.home_distance(target) + 1 if self.terminal else 0)
            return total, min(job["deadline"] - self.step - service + 1, self.left - total)

        if needed.get("WHEAT") and available.get("WHEAT", 0) < 1:
            # No executable feed route: salvage independent output/collection.
            operations = [op for op in operations if op not in (["FEED"], ["CARE"])]
            del needed["WHEAT"]
        if any(available.get(item, 0) < n for item, n in needed.items()):
            return None
        cost, slack = costs()
        # Full visits are preferred. At a hard deadline, salvage the essential
        # prefix rather than declining a feasible feed or water entirely.
        optional_ops = [["COLLECT_FERTILIZER"], ["FERTILIZE"]]
        if job["kind"] == "animal":
            optional_ops += [["CARE"], ["HARVEST"]]
        for optional in optional_ops:
            if slack >= 0:
                break
            if optional in operations and len(operations) > 1:
                operations.remove(optional)
                if optional == ["FERTILIZE"]:
                    needed.pop("FERTILIZER", None)
                cost, slack = costs()
        if not operations or slack < 0:
            return None
        return {"cost": cost, "slack": slack, "needed": needed, "ops": operations, "via": via}

    def reserve(self, worker, job, route):
        self.assignments[worker] = (job, route)
        self.claimed.add(job["pos"])
        for item, n in route["needed"].items():
            self.reserved[item] = self.reserved.get(item, 0) + n

    def available(self):
        return {p: n - self.reserved.get(p, 0) for p, n in self.shed.items()}

    def allocate(self):
        # First retain executable commitments; urgency elsewhere cannot clear them.
        for worker in range(len(self.positions)):
            prior = _MEMORY.get("targets", {}).get(worker)
            if not prior:
                continue
            job = self.jobs.get(tuple(prior[0]))
            if job is None or job["pos"] in self.claimed:
                continue
            route = self.route(worker, job, self.available())
            if route:
                self.reserve(worker, job, route)

        # Joint assignment among free workers; retained visits remain protected.
        # Shared shed inputs are rechecked when reserving each matched edge.
        while len(self.assignments) < len(self.positions):
            workers = [w for w in range(len(self.positions)) if w not in self.assignments]
            jobs = [j for p, j in self.jobs.items() if p not in self.claimed]
            if not jobs:
                break
            scale = max(1, sum(j["value"] for j in jobs))
            weights, routes = [], {}
            for i, worker in enumerate(workers):
                row = []
                carried_animal = next((a for a in ANIMALS if self.carry[worker].get(a, 0)), None)
                for j, job in enumerate(jobs):
                    if carried_animal and ["PLACE", carried_animal] not in job["ops"]:
                        row.append(None)
                        continue
                    route = self.route(worker, job, self.available())
                    if route is None:
                        row.append(None)
                        continue
                    urgent = job["essential"] and route["slack"] <= 3
                    on_site = job["pos"] == self.positions[worker] and job["kind"] == "animal"
                    value = job["value"] if urgent else job["value"] / (route["cost"] + 2)
                    priority = 4 * urgent + 2 * on_site + (job["kind"] == "install")
                    priority += 0.25 * job["essential"]
                    row.append(scale * priority + value - 1e-6 * route["cost"])
                    routes[i, j] = route
                weights.append(row)
            pairs = maximum_weight_matching(weights)
            reserved = 0
            for i, j in sorted(pairs, key=lambda pair: (-weights[pair[0]][pair[1]], pair)):
                worker, job = workers[i], jobs[j]
                route = routes[i, j]
                available = self.available()
                if any(available.get(p, 0) < n for p, n in route["needed"].items()):
                    continue
                self.reserve(worker, job, route)
                reserved += 1
            if not reserved:
                break

        # Rescue only an actually unclaimed threatened job, and give it to the
        # worker we interrupt. Never interrupt an on-site animal service bundle.
        for pos, job in sorted(self.jobs.items(), key=lambda pair: (pair[1]["deadline"], pair[0])):
            if pos in self.claimed or not job["essential"]:
                continue
            options = []
            for worker, (previous, prior_route) in self.assignments.items():
                if previous["kind"] == "install" or (
                    previous["kind"] == "animal" and previous["pos"] == self.positions[worker]
                ):
                    continue
                available = self.available()
                for item, n in prior_route["needed"].items():
                    available[item] = available.get(item, 0) + n
                route = self.route(worker, job, available)
                if route is None:
                    continue
                slack = route["slack"]
                old_slack = prior_route["slack"]
                if (
                    slack <= 1
                    and old_slack >= route["cost"] + 3
                    and job["value"] > previous["value"]
                ):
                    options.append((route["cost"], worker, route))
            if options:
                _, worker, route = min(options, key=lambda e: (e[0], e[1]))
                previous, prior_route = self.assignments.pop(worker)
                self.claimed.remove(previous["pos"])
                for item, n in prior_route["needed"].items():
                    self.reserved[item] -= n
                self.reserve(worker, job, route)
                self.switches.append((worker, previous["pos"], pos))

    def deposit(self, worker):
        pos, inv = self.positions[worker], self.carry[worker]
        if not any(n > 0 for p, n in inv.items() if p in CURVES):
            return None
        if pos not in self.access:
            return move(pos, self.nearest_shed(pos))
        room = self.capacity - sum(self.shed.values())
        if room <= 0:
            return ["PASS"]
        # Selective deposits preserve feed and never discard overflow. Avoid the
        # PLACE-animal ambiguity by depositing only saleable products.
        goods = [p for p, n in inv.items() if n > 0 and p in CURVES]
        item = max(goods, key=lambda p: (self.prices[p], p))
        if sum(inv.values()) <= room and not any(inv.get(a, 0) for a in ANIMALS):
            if self.terminal or not inv.get("WHEAT", 0) or not self.feed_count:
                for p, n in inv.items():
                    self.shed[p] = self.shed.get(p, 0) + n
                inv.clear()
                return ["DROP"]
        n = min(inv[item], room)
        self.shed[item] = self.shed.get(item, 0) + n
        inv[item] -= n
        return ["PLACE", item, n]

    def sale_receipts(self, item, quantity):
        """Per-unit proceeds assuming no unseen rival order, with own price impact."""
        n = max(0, min(int(quantity), self.capacity))
        prefix = self._receipt_cache.setdefault(item, [0])
        while len(prefix) <= n:
            k = len(prefix) - 1
            price = quoted_price(item, self.market.get(item, 10000) + k, self.params)
            prefix.append(prefix[-1] + price)
        return prefix[n]

    def final_deposits(self):
        """Capacity DP across all workers, restricted to the final action.

        Exact for constant product values with sufficient SELL slots. For
        moving prices, average incremental receipts are a valuation heuristic.
        No future farm states are generated; only current deposit reservations.
        """
        cargo_units = sum(
            sum(inv.values()) for pos, inv in zip(self.positions, self.carry) if pos in self.access
        )
        room = max(0, min(cargo_units, self.capacity - sum(self.shed.values())))
        values = {}
        for item in CURVES:
            cargo = min(
                room,
                sum(
                    inv.get(item, 0)
                    for pos, inv in zip(self.positions, self.carry)
                    if pos in self.access
                ),
            )
            stock = self.shed.get(item, 0)
            values[item] = (
                self.sale_receipts(item, stock + cargo) - self.sale_receipts(item, stock)
            ) / max(1, cargo)
        # used capacity -> (value, negative discarded quantity, command tuple)
        states = {0: (0, 0, ())}
        for pos, inv in zip(self.positions, self.carry):
            following = {}
            for used, (value, kept, commands) in states.items():
                free = room - used
                options = [(0, 0, 0, ("PASS",))]
                if pos in self.access and free:
                    taken, gain = 0, 0
                    for item, quantity in inv.items():
                        n = min(max(0, quantity), free - taken)
                        taken += n
                        gain += n * values.get(item, 0)
                    options.append((taken, gain, -max(0, sum(inv.values()) - taken), ("DROP",)))
                    for item, quantity in inv.items():
                        if item in CURVES:
                            for n in range(1, min(quantity, free) + 1):
                                options.append((n, n * values[item], 0, ("PLACE", item, n)))
                for take, gain, loss, command in options:
                    candidate = (value + gain, kept + loss, commands + (command,))
                    old = following.get(used + take)
                    if old is None or candidate[:2] > old[:2]:
                        following[used + take] = candidate
            states = following
        _, best = max(states.items(), key=lambda pair: (pair[1][:2], -pair[0]))
        actions = [list(command) for command in best[2]]
        for inv, command in zip(self.carry, actions):
            if command[0] == "DROP":
                for item, quantity in inv.items():
                    n = min(max(0, quantity), max(0, self.capacity - sum(self.shed.values())))
                    self.shed[item] = self.shed.get(item, 0) + n
                inv.clear()
            elif command[0] == "PLACE":
                item, n = command[1:]
                self.shed[item] = self.shed.get(item, 0) + n
                inv[item] -= n
        _MEMORY["targets"] = {}
        return actions

    def unit_actions(self):
        if self.step == self.last:
            return self.final_deposits()
        actions, targets = [], {}
        for worker, pos in enumerate(self.positions):
            inv = self.carry[worker]
            deliver = self.terminal and any(inv.get(p, 0) for p in CURVES)
            if deliver and (
                self.left <= self.home_distance(pos) + 3 or worker not in self.assignments
            ):
                actions.append(self.deposit(worker) or ["PASS"])
                continue
            assigned = self.assignments.get(worker)
            storage_pressure = sum(self.shed.values()) + sum(sum(v.values()) for v in self.carry)
            if (
                not self.terminal
                and pos in self.access
                and storage_pressure >= self.capacity * 0.8
                and any(inv.get(p, 0) for p in CURVES if p != "WHEAT")
            ):
                actions.append(self.deposit(worker) or ["PASS"])
                continue
            if assigned:
                job, route = assigned
                targets[worker] = (job["pos"], job["kind"])
                needed = route["needed"]
                if needed:
                    if pos not in self.access:
                        action = move(pos, route["via"])
                    else:
                        item = next(iter(needed))
                        n = needed[item]
                        if item == "WHEAT":
                            spare = max(0, self.shed.get(item, 0) - self.reserved.get(item, 0))
                            n += min(2, spare, max(0, self.feed_count - self.reserved.get(item, 0)))
                        n = min(n, self.shed.get(item, 0))
                        action = ["PICKUP", item, n] if n > 0 else ["PASS"]
                        self.shed[item] = self.shed.get(item, 0) - n
                        inv[item] = inv.get(item, 0) + n
                        self.reserved[item] -= needed[item]
                elif pos != job["pos"]:
                    action = move(pos, job["pos"])
                else:
                    action = route["ops"][0]
                    if action[0] == "PLANT":
                        crop = action[1]
                        if self.seeds.get(crop, 0) <= 0:
                            action = ["PASS"]
                        else:
                            self.seeds[crop] -= 1
                    elif action[0] in ("FEED", "FERTILIZE"):
                        item = "WHEAT" if action[0] == "FEED" else "FERTILIZER"
                        inv[item] = inv.get(item, 0) - 1
                    elif action[0] == "PLACE":
                        inv[action[1]] -= 1
                    elif action[0] == "HARVEST":
                        tile = self.sites[pos]
                        item = tile["crop"] if "crop" in tile else ANIMALS[tile["animal"]][3]
                        inv[item] = inv.get(item, 0) + tile.get("yield_units", 0)
                    elif action[0] == "COLLECT_FERTILIZER":
                        inv["FERTILIZER"] = inv.get("FERTILIZER", 0) + 1
                actions.append(action)
            else:
                # Early delivery frees storage and brings harvest cash into use.
                sellable = sum(n for p, n in inv.items() if p in CURVES)
                if sellable and (self.terminal or pos in self.access or sellable >= 12):
                    actions.append(self.deposit(worker) or ["PASS"])
                else:
                    actions.append(["PASS"])
        _MEMORY["targets"] = targets
        return actions

    def order(self, op):
        if len(self.orders) >= self.max_orders:
            return False
        self.orders.append(op)
        return True

    def trade(self):
        # Sales include only observed stock plus deposits reserved in unit order.
        # Feed is reserved before cash is allocated to hires or new investments.
        feed_stock = 0 if self.terminal else self.future_animals + self.feed_count
        carry_wheat = sum(inv.get("WHEAT", 0) for inv in self.carry)
        keep_wheat = max(0, feed_stock - carry_wheat)
        sale_order = sorted(
            CURVES,
            key=lambda p: (
                -self.sale_receipts(p, self.shed.get(p, 0)) if self.terminal else -self.prices[p],
                p,
            ),
        )
        for item in sale_order:
            n = max(0, self.shed.get(item, 0) - (keep_wheat if item == "WHEAT" else 0))
            # Keep a small, executable fertilizer buffer only for near-term crop demand.
            if item == "FERTILIZER" and not self.terminal:
                need = sum(["FERTILIZE"] in j["ops"] for j in self.jobs.values())
                n = max(0, n - min(6, need))
            if n and self.order(["SELL", item, n]):
                self.shed[item] -= n
                # Bank only the guaranteed floor in the purchase budget; rival
                # simultaneous sales can invalidate a current-quote proceeds estimate.
                self.cash += n
        if self.terminal:
            # Hands expire overnight. Hire delivery/harvest workers on the final
            # morning too, while leaving enough time for them to act and return.
            work = sum(len(j["ops"]) + 2 * self.home_distance(p) + 1 for p, j in self.jobs.items())
            wanted = min(11, max(0, math.ceil(work / max(1, self.left - 3)) - 1))
            hires = int(self.farm.get("hires_today", len(self.positions) - 1))
            value = sum(j["value"] for j in self.jobs.values())
            while hires < wanted and self.left >= 6:
                cost = fib(hires) * int(self.cfg.get("farmHandCostMult", 1))
                if cost > self.cash or cost > value / max(1, wanted + 1):
                    break
                if not self.order(["HIRE"]):
                    break
                self.cash -= cost
                hires += 1
            return
        feed_short = max(0, feed_stock - self.shed.get("WHEAT", 0) - carry_wheat)
        room = self.capacity - sum(self.shed.values())
        n = 0
        feed_cost = 0
        for k in range(min(feed_short, max(0, room))):
            price = quoted_price("WHEAT", self.market.get("WHEAT", 10000) - k - 1, self.params)
            # A modest buffer for unknown rival purchases; fills remain server-dependent.
            price = math.ceil(price * 1.15)
            if feed_cost + price > self.cash:
                break
            n += 1
            feed_cost += price
        if n and self.order(["BUY_PRODUCT", "WHEAT", n]):
            self.cash -= feed_cost
            self.shed["WHEAT"] = self.shed.get("WHEAT", 0) + n
        if feed_short > n:
            return
        reserve_cash = max(80, self.future_animals * self.prices["WHEAT"])
        work = sum(len(j["ops"]) + 1.8 + self.home_distance(p) * 0.35 for p, j in self.jobs.items())
        work += sum(self.seeds.values()) * 2.5
        potential = max(self.investment(item)[0] for item in (*CROPS, *ANIMALS))
        if potential > 0 and self.hour < 8:
            work += min(35, sum(t is None for t in self.sites.values()) * 2)
        useful_actions = max(1, self.left - 3)
        wanted = min(11, max(0, math.ceil(work / useful_actions) - 1))
        hires = int(self.farm.get("hires_today", len(self.positions) - 1))
        mult = int(self.cfg.get("farmHandCostMult", 1))
        while hires < wanted and self.left >= 8:
            cost = fib(hires) * mult
            if self.cash - cost < reserve_cash or cost > useful_actions * max(2, potential):
                break
            if not self.order(["HIRE"]):
                break
            self.cash -= cost
            hires += 1
        if self.left < 9 or self.hour > self.tpd // 2:
            return
        empty = sum(
            t is None or (isinstance(t, dict) and t.get("kind") == "WEED")
            for t in self.sites.values()
        )
        pending_animals = sum(
            self.shed.get(a, 0) + sum(inv.get(a, 0) for inv in self.carry) for a in ANIMALS
        )
        pending_seeds = sum(self.seeds.values())
        spare_work = (hires + 1) * (self.tpd - 4) - (
            self.future_animals * 4.7 + len(self.plants) * 1.8
        )
        choices = []
        for item in (*CROPS, *ANIMALS):
            score, margin = self.investment(item)
            if score <= 0 or margin <= 0:
                continue
            if item in ANIMALS:
                if pending_animals >= 2 or self.future_animals + pending_animals >= 16:
                    continue
                if not any(
                    self.home_distance(p) <= 2
                    and (
                        t is None
                        or (
                            isinstance(t, dict)
                            and t.get("kind") in ("WEED", ANIMALS[item][4])
                            and "animal" not in t
                        )
                    )
                    for p, t in self.sites.items()
                ):
                    continue
                cost, work = ANIMALS[item][0], 5
            else:
                count = sum(t["crop"] == item for t in self.plants.values()) + self.seeds.get(
                    item, 0
                )
                if pending_seeds >= 8 or count >= max(6, math.ceil(len(self.sites) * 0.35)):
                    continue
                cost, work = CROPS[item][0], 2
            if empty <= pending_seeds + pending_animals or spare_work < work:
                continue
            if self.cash >= cost + reserve_cash:
                choices.append((score, item, cost))
        if choices:
            _, item, cost = max(choices)
            if item in CROPS:
                concentration_room = max(6, math.ceil(len(self.sites) * 0.35)) - (
                    sum(t["crop"] == item for t in self.plants.values()) + self.seeds.get(item, 0)
                )
                n = min(
                    4,
                    concentration_room,
                    empty - pending_seeds - pending_animals,
                    8 - pending_seeds,
                    int((self.cash - reserve_cash) // cost),
                    max(1, int(spare_work // 2)),
                )
                if n > 0:
                    self.order(["BUY_SEED", item, n])
            elif self.capacity - sum(self.shed.values()) > 0:
                self.order(["BUY_ANIMAL", item, 1])
        # Land has a cash and service gate, and must leave capital to fill it.
        quadrants = len(self.farm.get("unlocked_quadrants", ["NW"]))
        if not choices and quadrants < 3 and empty <= 4 and self.final_day - self.day >= 8:
            cost = (1000, 2000, 4000)[quadrants - 1]
            if potential > 5 and spare_work >= 8 and self.cash >= cost + reserve_cash + 800:
                self.order(["BUY_LAND"])

    def run(self):
        token = (self.seat, self.day, self.size, self.last)
        if _MEMORY.get("token") != token or self.step <= _MEMORY.get("step", -1):
            _MEMORY.clear()
        _MEMORY.update(token=token, step=self.step)
        self.make_jobs()
        self.allocate()
        actions = self.unit_actions()
        self.trade()
        return {"farmer": actions[0], "hands": actions[1:], "market": self.orders}


# Kaggle selects the last callable inserted into the module namespace.
def agent(observation, configuration=None):
    if not observation.get("farms"):
        return {"farmer": ["PASS"], "hands": [], "market": []}
    return Planner(observation, configuration).run()
