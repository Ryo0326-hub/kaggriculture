"""Step 1 baseline: four wheat plots, one farmer, exact routing within each task batch.

This file is the complete submission artifact and uses only the Python standard library.
The task priorities are a heuristic; only the small movement subproblem is solved exactly.
"""

from itertools import permutations


def distance(a, b):
    """Shortest grid path length: all tiles, including locked tiles, are traversable."""
    return abs(a[0] - b[0]) + abs(a[1] - b[1])


def shortest_route(start, targets):
    """Minimum-length open route through at most four distinct targets.

    Exhaustive enumeration is exact and costs O(k! * k); the baseline fixes k <= 4.
    Tuple ordering breaks ties deterministically. There is no return-to-shed constraint.
    """
    targets = tuple(sorted(set(targets)))
    if len(targets) > 4:
        raise ValueError("Step 1 routing supports at most four targets")
    if not targets:
        return ()

    def cost(route):
        return distance(start, route[0]) + sum(distance(a, b) for a, b in zip(route, route[1:]))

    return min(permutations(targets), key=lambda route: (cost(route), route))


def move_toward(start, target):
    if start[0] != target[0]:
        return ["EAST" if target[0] > start[0] else "WEST"]
    if start[1] != target[1]:
        return ["SOUTH" if target[1] > start[1] else "NORTH"]
    return ["PASS"]


def next_task(position, targets, operation):
    target = shortest_route(position, targets)[0]
    return operation if position == target else move_toward(position, target)


def agent(obs, configuration=None):
    """Choose a feasible action from the current observation; no persistent state needed."""
    cfg = configuration or {}
    turns_per_day = cfg.get("turnsPerDay", 24)
    last_step = cfg.get("episodeSteps", 720) - 2
    day, hour = obs["day"], obs["hour"]
    step = obs.get("step", day * turns_per_day + hour)
    farm = obs["farms"][obs["player"]]
    private = obs["private"]
    tiles = farm["tiles"]
    half = len(tiles) // 2
    shed = (half - 1, half - 1)
    plots = [(x, y) for y in (half - 2, half - 1) for x in (half - 2, half - 1)]
    position = tuple(farm["farmer"])
    carried = private["inventories"][0].get("WHEAT", 0)
    seeds = private["seeds"].get("WHEAT", 0)
    final_day = day == last_step // turns_per_day
    # Conservative cutoff: allow a complete four-day wheat cycle plus harvesting/transport.
    can_grow = day + 4 <= last_step // turns_per_day
    hours_left = turns_per_day - hour
    empty, weeds, water, harvest = [], [], [], []
    for x, y in plots:
        tile = tiles[y][x]
        if tile is None:
            empty.append((x, y))
        elif isinstance(tile, dict) and tile.get("kind") == "WEED":
            weeds.append((x, y))
        elif isinstance(tile, dict) and tile.get("crop") == "WHEAT":
            age = day - tile["planted_day"]
            if not tile["watered_today"]:
                water.append((x, y))
            if tile["yield_units"] > 0 and (age >= 4 or (final_day and age >= 2)):
                harvest.append((x, y))

    # Return early enough that DROP can run on/before the final actionable turn.
    must_deposit = carried > 0 and last_step - step <= distance(position, shed) + 1
    if must_deposit:
        farmer = ["DROP"] if position == shed else move_toward(position, shed)
    elif water:
        farmer = next_task(position, water, ["WATER"])
    elif harvest:
        farmer = next_task(position, harvest, ["HARVEST"])
    else:
        plantable = [p for p in empty if distance(position, p) + 2 <= hours_left]
        clearable = [p for p in weeds if distance(position, p) + 4 <= hours_left]
        if can_grow and plantable and seeds > 0:
            farmer = next_task(position, plantable, ["PLANT", "WHEAT"])
        elif can_grow and clearable:
            farmer = next_task(position, clearable, ["DIG"])
        elif carried:
            farmer = ["DROP"] if position == shed else move_toward(position, shed)
        else:
            farmer = ["PASS"]

    # Unit actions precede the market. Sell the stock that actually reaches the shed.
    stock = private["shed"].get("WHEAT", 0)
    if farmer == ["DROP"]:
        room = max(0, cfg.get("shedCapacity", 100) - sum(private["shed"].values()))
        stock += min(carried, room)
    market = [["SELL", "WHEAT", stock]] if stock else []
    used_seed = int(farmer == ["PLANT", "WHEAT"])
    # Buy only for empty plots that can be reached, planted, and watered after this turn.
    demand = sum(distance(position, p) + 3 <= hours_left for p in empty) - used_seed
    if can_grow and demand > seeds - used_seed:
        quantity = min(demand - (seeds - used_seed), int(farm["money"] // 10))
        if quantity > 0:
            market.append(["BUY_SEED", "WHEAT", quantity])
    return {
        "farmer": farmer,
        "hands": [["PASS"] for _ in farm["hands"]],
        "market": market[: cfg.get("maxMarketOrdersPerTurn", 10)],
    }
