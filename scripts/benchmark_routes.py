"""Controlled scheduling experiment: identical installed herds, no new investment.

Run as python -m scripts.benchmark_routes. These modified initial states isolate
operations; their cash totals are not standard-start competition scores.
"""

import argparse
import json
from collections import Counter, defaultdict
from datetime import UTC, datetime
from pathlib import Path

from kaggle_environments import make
from kaggle_environments.envs.kaggriculture import kaggriculture as engine

from baselines.step_4 import plan_turn as station_plan
from evaluate import ROOT, environment_metadata, sha256
from main import plan_turn as shared_plan


def fixed_herd_game(seed, seat, animals):
    env = make("kaggriculture", configuration={"seed": seed, "startingMoney": 15000})
    count = len(animals)
    sites = sorted(
        [(x, y) for y in range(5) for x in range(5)],
        key=lambda p: (abs(p[0] - 4) + abs(p[1] - 4), p),
    )[:count]
    for farm in env.state[0].observation.farms:
        for (x, y), animal in zip(sites, animals):
            farm["tiles"][y][x] = engine._new_animal(animal, 0)
    for state in env.state:
        state.observation.private["shed"]["WHEAT"] = 2 * count

    def shared(obs, cfg):
        return shared_plan(obs, cfg, allowed_animals=(), herd_limit=count)[0]

    def station(obs, cfg):
        return station_plan(obs, cfg, allowed_animals=(), herd_limit=count)[0]

    agents = [station, station]
    agents[seat] = shared
    # Environment.run resets a one-state environment. Execute the opening step
    # first so the deliberately installed fixtures survive that reset guard.
    env.step([fn(env.state[i].observation, env.configuration) for i, fn in enumerate(agents)])
    env.run(agents)
    diagnostics = []
    for player in (seat, 1 - seat):
        outputs, ops = Counter(), Counter()
        roles = defaultdict(set)
        wages = hires = missed_feed = missed_care = escapes = 0
        for before, after in zip(env.steps, env.steps[1:]):
            old, new = before[player].observation, after[player].observation
            farm = old.farms[player]
            commands = [after[player].action["farmer"], *after[player].action["hands"]]
            for worker, (pos, op) in enumerate(zip([farm["farmer"], *farm["hands"]], commands)):
                ops[op[0]] += 1
                tile = farm["tiles"][pos[1]][pos[0]]
                if op[0] in ("HARVEST", "CARE", "FEED", "COLLECT_FERTILIZER"):
                    assert isinstance(tile, dict) and "animal" in tile
                    roles[(old.day, worker)].add(tuple(pos))
                    if op[0] == "HARVEST":
                        assert tile["yield_units"] > 0
                        outputs[engine.ANIMALS[tile["animal"]]["product"]] += tile["yield_units"]
                    elif op[0] == "COLLECT_FERTILIZER":
                        assert tile["fertilizer_available"]
                        outputs["FERTILIZER"] += 1
            if old.day == new.day:
                actual = new.farms[player]["hires_today"] - farm["hires_today"]
                hires += actual
                wages += sum(
                    engine._hire_cost(i, env.configuration.farmHandCostMult)
                    for i in range(farm["hires_today"], farm["hires_today"] + actual)
                )
            else:
                assert not any(o[0] == "HIRE" for o in after[player].action["market"])
                care_now = {
                    tuple(p)
                    for p, op in zip([farm["farmer"], *farm["hands"]], commands)
                    if op[0] == "CARE"
                }
                for x, y in sites:
                    tile, following = farm["tiles"][y][x], new.farms[player]["tiles"][y][x]
                    tile = tile if isinstance(tile, dict) else {}
                    following = following if isinstance(following, dict) else {}
                    escapes += int("animal" in tile and "animal" not in following)
                    missed_feed += int(following.get("consecutive_unfed", 0) > 0)
                    if old.day < 28:
                        missed_care += int(not tile.get("cared_today") and (x, y) not in care_now)
        final = env.steps[-1][player].observation
        diagnostics.append(
            {
                "cash": final.farms[player]["money"],
                "wages": wages,
                "successful_hires": hires,
                "outputs": dict(outputs),
                "unit_actions": dict(ops),
                "multi_animal_worker_days": sum(len(v) > 1 for v in roles.values()),
                "unfed_animal_days": missed_feed,
                "uncared_required_animal_days": missed_care,
                "escapes": escapes,
                "unsold_units": sum(final.private["shed"].values())
                + sum(sum(inv.values()) for inv in final.private["inventories"]),
            }
        )
    return {
        "seed": seed,
        "candidate_seat": seat,
        "animals": animals,
        "starting_cash": 15000,
        "starting_wheat": 2 * count,
        "statuses": [s.status for s in env.steps[-1]],
        "recorded_states": len(env.steps),
        "shared": diagnostics[0],
        "station": diagnostics[1],
        "equal_output": diagnostics[0]["outputs"] == diagnostics[1]["outputs"],
        "margin": diagnostics[0]["cash"] - diagnostics[1]["cash"],
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seeds", nargs="+", type=int, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if len(set(args.seeds)) != len(args.seeds):
        parser.error("Seeds must be unique")
    report = {
        "kind": "Controlled installed-herd experiment; not standard-start competition games",
        "created_at": datetime.now(UTC).isoformat(),
        "environment": environment_metadata(),
        "candidate_sha256": sha256(ROOT / "main.py"),
        "reference_sha256": sha256(ROOT / "baselines/step_4.py"),
        "runner_sha256": sha256(__file__),
        "games": [],
    }
    with args.output.open("x") as output:
        for animals in [["COW"] * 10, ["SHEEP"] * 10, ["COW", "SHEEP"] * 5]:
            for seed in args.seeds:
                for seat in (0, 1):
                    row = fixed_herd_game(seed, seat, animals)
                    report["games"].append(row)
                    print(
                        f"{seed=} {seat=} {animals[:2]} margin={row['margin']:+.0f} "
                        f"equal_output={row['equal_output']}",
                        flush=True,
                    )
        assert report["candidate_sha256"] == sha256(ROOT / "main.py")
        json.dump(report, output, indent=2)
        output.write("\n")


if __name__ == "__main__":
    main()
