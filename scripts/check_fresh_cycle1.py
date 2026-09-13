"""Bounded checks on recorded observations. Never creates or advances a game.

The ledger below checks one action's inventory preconditions only. Candidate
actions are never used to produce the next observation; all states come from
the supplied recording. This is not a return, outcome, or win-rate benchmark.
"""

import argparse
import base64
import copy
import gzip
import hashlib
import json
import runpy
import signal
import time
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PRODUCTS = {"WHEAT", "CARROT", "TOMATO", "STRAWBERRY", "MELON", "MILK", "WOOL", "EGG", "FERTILIZER"}
FIRST = {"WHEAT": 2, "CARROT": 2, "MELON": 10, "TOMATO": 8, "STRAWBERRY": 10}
STRUCTURE = {"COW": "PASTURE", "SHEEP": "PASTURE", "GOOSE": "COOP"}
MOVES = {"NORTH": (0, -1), "SOUTH": (0, 1), "EAST": (1, 0), "WEST": (-1, 0)}


def check_action(obs, config, action):
    """Independent, bounded preconditions, including execution-order reservations."""
    assert set(action) == {"farmer", "hands", "market"}
    farm = obs["farms"][obs["player"]]
    positions = [farm["farmer"], *farm["hands"]]
    assert len(action["hands"]) == len(farm["hands"])
    assert len(action["market"]) <= config.get("maxMarketOrdersPerTurn", 10)
    seeds = Counter(obs["private"].get("seeds", {}))
    shed = Counter(obs["private"].get("shed", {}))
    capacity = config.get("shedCapacity", 100)
    board_size = len(farm["tiles"])
    half = board_size // 2
    access = {(x, y) for x in (half - 1, half) for y in (half - 1, half)}
    used = set()
    for i, command in enumerate([action["farmer"], *action["hands"]]):
        assert isinstance(command, list) and command
        op, *args = command
        x, y = positions[i]
        inv = Counter(obs["private"]["inventories"][i])
        tile = farm["tiles"][y][x]
        if op in MOVES:
            dx, dy = MOVES[op]
            assert not args and 0 <= x + dx < board_size and 0 <= y + dy < board_size
            continue
        if op == "PASS":
            assert not args
            continue
        if op in ("PICKUP", "DROP") or (op == "PLACE" and args[0] in PRODUCTS):
            assert (x, y) in access
            if op == "PICKUP":
                item, n = args
                assert type(n) is int and 0 < n <= shed[item]
                shed[item] -= n
            elif op == "DROP":
                assert not args
                final_action = obs["day"] * config.get("turnsPerDay", 24) + obs["hour"]
                if sum(inv.values()) > capacity - sum(shed.values()):
                    assert final_action == config.get("episodeSteps", 720) - 2
                # Engine order: accepted prefix only; discarded overflow must
                # never become a SELL quantity. Earlier DROP still cannot waste stock.
                for item, quantity in inv.items():
                    shed[item] += min(quantity, max(0, capacity - sum(shed.values())))
            else:
                item, n = args
                assert type(n) is int and 0 < n <= inv[item]
                assert n <= capacity - sum(shed.values())
                shed[item] += n
            continue
        assert tile != "LOCKED", (i, command, "locked tile")
        assert (x, y) not in used, (i, command, "duplicate productive target")
        used.add((x, y))
        if op == "PLANT":
            assert tile is None and len(args) == 1 and seeds[args[0]] > 0
            seeds[args[0]] -= 1
            assert obs["hour"] + 1 < config.get("turnsPerDay", 24)
        elif op.startswith("BUILD_"):
            assert not args and tile is None and op in ("BUILD_COOP", "BUILD_PASTURE")
        elif op == "PLACE":
            assert len(args) == 1 and args[0] in STRUCTURE and inv[args[0]] > 0
            assert isinstance(tile, dict) and tile["kind"] == STRUCTURE[args[0]]
            assert "animal" not in tile
        elif op == "DIG":
            assert not args and isinstance(tile, dict) and "animal" not in tile
        elif op in ("WATER", "FERTILIZE"):
            assert not args and isinstance(tile, dict) and tile.get("kind") == "PLANT"
            if op == "WATER":
                assert not tile["watered_today"]
            else:
                assert inv["FERTILIZER"] > 0
                assert tile.get("fertilized_until_day", -1) < obs["day"]
        elif op == "HARVEST":
            assert not args and isinstance(tile, dict) and tile.get("yield_units", 0) > 0
            if "crop" in tile:
                assert obs["day"] - tile["planted_day"] >= FIRST[tile["crop"]]
            else:
                assert "animal" in tile
        elif op in ("FEED", "CARE", "COLLECT_FERTILIZER"):
            assert not args and isinstance(tile, dict) and "animal" in tile
            if op == "FEED":
                assert inv["WHEAT"] > 0 and not tile["fed_today"]
            elif op == "CARE":
                assert not tile["cared_today"]
            else:
                assert tile["fertilizer_available"]
        else:
            raise AssertionError((i, command, "unknown operation"))
    for order in action["market"]:
        op, *args = order
        if op in ("HIRE", "BUY_LAND"):
            assert not args
            continue
        assert len(args) == 2 and type(args[1]) is int and args[1] > 0
        item, n = args
        if op == "SELL":
            assert item in PRODUCTS and n <= shed[item], (order, dict(shed))
            shed[item] -= n
        elif op == "BUY_PRODUCT":
            assert item in ("WHEAT", "FERTILIZER")
            assert sum(shed.values()) + n <= capacity
            shed[item] += n
        elif op == "BUY_ANIMAL":
            assert item in STRUCTURE and sum(shed.values()) + n <= capacity
            shed[item] += n
        else:
            assert op == "BUY_SEED" and item in FIRST


def timeout_handler(signum, frame):
    raise TimeoutError("Recorded-observation callback exceeded one second")


def read_histories(fixture):
    raw = Path(fixture).read_bytes()
    document = json.loads(raw)
    if document.get("encoding") == "gzip+base64":
        expanded = gzip.decompress(base64.b64decode(document["payload"]))
        assert hashlib.sha256(expanded).hexdigest() == document["expanded_sha256"]
        document = json.loads(expanded)
    return raw, document


def check_histories(source, fixture):
    raw, document = read_histories(fixture)
    module = runpy.run_path(str(source))
    callback = module["agent"]
    memory = callback.__globals__["_MEMORY"]
    assert [name for name, value in module.items() if callable(value)][-1] == "agent"
    report = {
        "source_sha256": hashlib.sha256(Path(source).read_bytes()).hexdigest(),
        "fixture_sha256": hashlib.sha256(raw).hexdigest(),
        "method": "Original observations only; actions never generate states.",
        "sources": document["sources"],
        "histories": [],
        "calls": 0,
        "max_seconds": 0.0,
    }
    old_handler = signal.signal(signal.SIGALRM, timeout_handler)
    try:
        for history in document["histories"]:
            assert 1 <= len(history["observations"]) <= 24
            actions_by_mode = {}
            witness = []
            for mode in ("warm", "warm_repeat", "cold"):
                memory.clear()
                actions = []
                for obs in history["observations"]:
                    if mode == "cold":
                        memory.clear()
                    before = copy.deepcopy(obs)
                    signal.setitimer(signal.ITIMER_REAL, 1.0)
                    started = time.perf_counter()
                    action = callback(obs, document["configuration"])
                    elapsed = time.perf_counter() - started
                    signal.setitimer(signal.ITIMER_REAL, 0)
                    assert obs == before, "Agent mutated a recorded observation"
                    check_action(obs, document["configuration"], action)
                    targets = [tuple(v[0]) for v in memory.get("targets", {}).values()]
                    assert len(targets) == len(set(targets)), "Duplicate remembered owners"
                    actions.append(action)
                    step = obs["day"] * document["configuration"]["turnsPerDay"] + obs["hour"]
                    if (
                        mode == "warm"
                        and "routing-history" in history["label"]
                        and 492 <= step <= 494
                    ):
                        witness.append(
                            {
                                "step": step,
                                "worker": 3,
                                "action": action["hands"][2],
                                "target": memory.get("targets", {}).get(3),
                            }
                        )
                    report["calls"] += 1
                    report["max_seconds"] = max(report["max_seconds"], elapsed)
                actions_by_mode[mode] = actions
            assert actions_by_mode["warm"] == actions_by_mode["warm_repeat"]
            if witness:
                assert len(witness) == 3
                assert all(w["target"] == witness[0]["target"] for w in witness)
                report["route_witness"] = witness
            digest = hashlib.sha256(json.dumps(actions_by_mode["warm"], sort_keys=True).encode())
            report["histories"].append(
                {
                    "label": history["label"],
                    "count": len(actions),
                    "warm_action_sha256": digest.hexdigest(),
                }
            )
    finally:
        signal.setitimer(signal.ITIMER_REAL, 0)
        signal.signal(signal.SIGALRM, old_handler)
    return report


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--agent", type=Path, required=True)
    parser.add_argument(
        "--fixture", type=Path, default=ROOT / "docs/examples/fresh-cycle1-histories.json"
    )
    args = parser.parse_args()
    print(json.dumps(check_histories(args.agent, args.fixture), indent=2))
