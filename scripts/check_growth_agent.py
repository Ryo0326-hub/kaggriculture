"""Read recorded observations and check individual commands, without a simulator."""

import argparse
import json
import runpy
from collections import Counter
from copy import deepcopy
from hashlib import sha256
from pathlib import Path
from time import perf_counter


def validate(obs, cfg, action, scope):
    """Action preconditions and shared inventory arithmetic, not state transitions."""
    farm, private = obs["farms"][obs["player"]], obs["private"]
    positions = [farm["farmer"], *farm["hands"]]
    commands = [action["farmer"], *action["hands"]]
    assert len(commands) == len(positions)
    assert len(action["market"]) <= cfg.get("maxMarketOrdersPerTurn", 10)
    stock = dict(private["shed"])
    seeds, touched = Counter(), set()
    access = scope["shed_access"](obs)
    inventory_limit = cfg.get("shedCapacity", 100)
    for i, (pos, op) in enumerate(zip(positions, commands)):
        assert isinstance(op, list) and op
        p = tuple(pos)
        inv = private["inventories"][i]
        tile = farm["tiles"][p[1]][p[0]]
        name = op[0]
        if name in ("PASS", "NORTH", "SOUTH", "EAST", "WEST"):
            continue
        if name == "PICKUP":
            assert p in access and op[2] > 0 and stock.get(op[1], 0) >= op[2], (i, op)
            stock[op[1]] -= op[2]
            continue
        if name == "DROP" or name == "PLACE" and op[1] in scope["MARKET"]:
            assert p in access
            deposits = inv if name == "DROP" else {op[1]: op[2]}
            assert all(0 < n <= inv.get(c, 0) for c, n in deposits.items() if n)
            assert sum(stock.values()) + sum(deposits.values()) <= inventory_limit
            for c, n in deposits.items():
                stock[c] = stock.get(c, 0) + n
            continue
        assert p not in touched, ("duplicate tile operation", p, op)
        touched.add(p)
        assert tile != "LOCKED", ("locked", p, op)
        if name == "PLANT":
            assert tile is None
            seeds[op[1]] += 1
        elif name.startswith("BUILD_"):
            assert tile is None
        elif name == "PLACE":
            assert inv.get(op[1], 0) > 0
            assert isinstance(tile, dict) and not tile.get("animal")
            assert tile["kind"] == scope["ANIMALS"][op[1]]["structure"]
        elif name == "DIG":
            assert isinstance(tile, dict) and not tile.get("animal")
        else:
            assert isinstance(tile, dict)
            if name == "WATER":
                assert tile.get("crop") and not tile.get("watered_today")
            elif name == "FERTILIZE":
                assert tile.get("crop") and inv.get("FERTILIZER", 0) > 0
            elif name == "FEED":
                assert tile.get("animal") and not tile.get("fed_today") and inv.get("WHEAT", 0) > 0
            elif name == "CARE":
                assert tile.get("animal") and not tile.get("cared_today")
            elif name == "COLLECT_FERTILIZER":
                assert tile.get("animal") and tile.get("fertilizer_available")
            elif name == "HARVEST":
                assert tile.get("yield_units", 0) > 0
                if tile.get("crop"):
                    assert obs["day"] - tile["planted_day"] >= scope["CROPS"][tile["crop"]]["first"]
            else:
                raise AssertionError(("unknown", op))
    assert all(n <= private["seeds"].get(c, 0) for c, n in seeds.items())
    for order in action["market"]:
        assert isinstance(order, list) and order
        if len(order) == 3:
            assert isinstance(order[2], int) and order[2] > 0
        if order[0] == "SELL":
            assert stock.get(order[1], 0) >= order[2], ("oversell", order, stock)
            stock[order[1]] -= order[2]
        elif order[0] in ("BUY_PRODUCT", "BUY_ANIMAL"):
            stock[order[1]] = stock.get(order[1], 0) + order[2]
            assert sum(stock.values()) <= inventory_limit
    json.dumps(action)


def check(source, paths):
    start = perf_counter()
    loaded = runpy.run_path(str(source))
    name, agent = [(k, v) for k, v in loaded.items() if callable(v)][-1]
    assert name == "agent"
    startup = perf_counter() - start
    scope = agent.__globals__
    rows, inputs = [], []
    for path in paths:
        replay = json.loads(path.read_text())
        cfg = replay["configuration"]
        inputs.append(dict(file=path.name, sha256=sha256(path.read_bytes()).hexdigest()))
        for seat in (0, 1):
            for step in (0, 4, 72, 144, 179, 244, 340, 388, 483, 600, 696, 714, 718):
                obs = deepcopy(replay["steps"][step][seat]["observation"])
                obs["step"] = step
                before = deepcopy(obs)
                # Empty route caches exercise isolated callbacks without warm-up.
                scope["growth_routes"].cache_clear()
                start = perf_counter()
                action, detail = scope["growth_turn"](obs, cfg)
                seconds = perf_counter() - start
                assert seconds < cfg.get("actTimeout", 1), (path.name, seat, step, seconds)
                assert obs == before
                try:
                    validate(obs, cfg, action, scope)
                except AssertionError as exc:
                    raise AssertionError((path.name, seat, step, exc.args)) from exc
                rows.append(
                    dict(
                        replay=path.name,
                        seat=seat,
                        step=step,
                        seconds=seconds,
                        daily_workers=detail["daily"]["workers"],
                        assignments=len(detail["dispatch"]["assigned"]),
                        market=action["market"],
                        chosen=detail["investment"].get("chosen"),
                    )
                )
    return dict(
        method=(
            "Independent recorded observations, resource preconditions and cold route caches; "
            "no engine import, game advance or performance simulation."
        ),
        source_sha256=sha256(source.read_bytes()).hexdigest(),
        inputs=inputs,
        startup_seconds=startup,
        decisions=len(rows),
        max_seconds=max(r["seconds"] for r in rows),
        checks=rows,
        server_validation="pending",
        competitive_performance="unmeasured",
    )


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("replays", nargs="+", type=Path)
    args = parser.parse_args()
    result = check(args.source, args.replays)
    with args.output.open("x") as file:
        file.write(json.dumps(result, indent=2) + "\n")
    print(json.dumps({k: v for k, v in result.items() if k not in ("inputs", "checks")}, indent=2))


if __name__ == "__main__":
    main()
