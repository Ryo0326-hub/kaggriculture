"""Controlled installed-portfolio experiment with actual engine cash/work accounting.

Assets and initial inputs are supplied equally; no seed/animal/land investment is
allowed. These are modified-start fixtures, not standard competition outcomes.
"""

import argparse
import copy
import json
from collections import Counter
from concurrent.futures import ProcessPoolExecutor
from datetime import UTC, datetime
from pathlib import Path
from time import perf_counter

from kaggle_environments import make
from kaggle_environments.envs.kaggriculture import kaggriculture as engine

from evaluate import economic_audit, environment_metadata, sha256
from experiments import staffing_dispatch as main
from scripts import audit_replay as audit

MODES = {
    "legacy": {},
    "open_routes": {"overnight": True},
    "dated_closed": {"dated_staffing": True},
    "dated_open": {"overnight": True, "dated_staffing": True},
}
HOOKS = {
    "_process_market": audit.on_market,
    "_commit_unit": audit.on_commit,
    "_do_hire": audit.on_hire,
    "_do_buy_land": audit.on_land,
    "_apply_unit_action": audit.on_unit,
    "_drop_inventories_to_shed": audit.on_drop,
    "_decay_plants": audit.on_decay,
    "_daily_refresh_animals": audit.on_animals,
}


def installed_environment(seed, quadrants):
    env = make("kaggriculture", configuration={"seed": seed, "startingMoney": 30000})
    farms = env.state[0].observation.farms
    for player, farm in enumerate(farms):
        for _ in range(quadrants - 1):
            engine._do_buy_land(farm, 10)
        farm["money"] = 30000
        view = {"farms": farms, "player": player}
        animals, fields = main.farm_sites(view)
        for i, (x, y) in enumerate(animals):
            farm["tiles"][y][x] = engine._new_animal("COW" if i % 2 == 0 else "SHEEP", 0)
        count = (15, 35, 55)[quadrants - 1]
        for i, (x, y) in enumerate(fields[:count]):
            crop = ("WHEAT", "MELON", "STRAWBERRY")[i % 3]
            tile = engine._new_plant(crop, 0, 24)
            tile["watered_today"] = True
            farm["tiles"][y][x] = tile
    for state in env.state:
        state.observation["farms"] = copy.deepcopy(farms)
        state.observation.private["shed"]["WHEAT"] = 20
        state.observation.private["shed"]["FERTILIZER"] = 20
    return env


def run_fixture(seed, seat, quadrants, mode, keep_replay=False):
    env = installed_environment(seed, quadrants)
    initial = copy.deepcopy(env.state)
    traces = [[], []]
    durations = [[], []]
    candidates = ["legacy", "legacy"]
    candidates[seat] = mode

    def choose(obs, cfg):
        side = obs["player"]
        started = perf_counter()
        action, detail = main.expansion_turn(obs, cfg, investments=False, **MODES[candidates[side]])
        durations[side].append(perf_counter() - started)
        assert not any(o[0] in ("BUY_SEED", "BUY_ANIMAL", "BUY_LAND") for o in action["market"])
        if obs["hour"] <= 6:
            mixed = detail["mixed"]
            traces[side].append(
                {
                    "step": obs.get("step", 24 * obs["day"] + obs["hour"]),
                    "day": obs["day"],
                    "hour": obs["hour"],
                    "workers_present": len(obs["farms"][side]["hands"]) + 1,
                    "worker_target": mixed["worker_target"],
                    "crop_work_bound": mixed["crop_work_bound"],
                    "crop_routes": mixed["crop_route_staffing"],
                    "hire_orders": sum(o[0] == "HIRE" for o in action["market"]),
                }
            )
        return action

    audit.context.clear()
    audit.context.update(
        transactions=[], unit_events=[], overflow=[], decay=[], escapes=[], missed_feed=[]
    )
    original = {name: getattr(engine, name) for name in HOOKS}
    base_interpreter = env.interpreter

    def interpret(state, environment):
        audit.context.update(
            step=state[0].observation.step,
            drop_seat=0,
            decay_seat=0,
            animal_seat=0,
            unit_farms=state[0].observation.farms,
        )
        return base_interpreter(state, environment)

    env.interpreter = interpret
    try:
        for name, fn in HOOKS.items():
            setattr(engine, name, fn)
        # An explicit first step preserves installed assets; run() alone resets them.
        env.step([choose(env.state[i].observation, env.configuration) for i in range(2)])
        env.run([choose, choose])
    finally:
        for name, fn in original.items():
            setattr(engine, name, fn)
    players = []
    for side in range(2):
        events = [e for e in audit.context["transactions"] if e["seat"] == side]
        units = [e for e in audit.context["unit_events"] if e["seat"] == side]
        outputs = Counter()
        for e in units:
            if e["op"] in ("HARVEST", "COLLECT_FERTILIZER"):
                outputs.update(e.get("inventory_gains", {}))
        sales = sum(e["cash"] for e in events if e["op"] == "SELL")
        expenses = sum(e["cash"] for e in events if e["op"] != "SELL")
        obs = env.state[side].observation
        cash = obs.farms[side]["money"]
        assert cash == 30000 + sales - expenses
        daily = []
        for day in range(30):
            day_events = [e for e in events if e["step"] // 24 == day]
            daily.append(
                {
                    "day": day,
                    "hires": sum(e["quantity"] for e in day_events if e["op"] == "HIRE"),
                    "wages": sum(e["cash"] for e in day_events if e["op"] == "HIRE"),
                    "sales": sum(e["cash"] for e in day_events if e["op"] == "SELL"),
                }
            )
        players.append(
            {
                "seat": side,
                "mode": candidates[side],
                "cash": cash,
                "sales": sales,
                "expenses": expenses,
                "cash_reconciled": True,
                "wages": sum(e["cash"] for e in events if e["op"] == "HIRE"),
                "outputs": dict(outputs),
                "daily": daily,
                "actions": dict(Counter(e["op"] for e in units)),
                "ineffective_actions": dict(
                    Counter(e["op"] for e in units if not e["changed"] and e["op"] != "PASS")
                ),
                "unfed_days": sum(e["seat"] == side for e in audit.context["missed_feed"]),
                "escapes": sum(e["seat"] == side for e in audit.context["escapes"]),
                "decayed_units": sum(
                    e["units"] for e in audit.context["decay"] if e["seat"] == side
                ),
                "overnight_overflow": sum(
                    sum(e["items"].values()) for e in audit.context["overflow"] if e["seat"] == side
                ),
                "explicit_overflow": sum(sum(e.get("overflow", {}).values()) for e in units),
                "final_stock": sum(obs.private.shed.values())
                + sum(sum(v.values()) for v in obs.private.inventories),
                "economic_audit": economic_audit(env, side),
                "max_decision_seconds": max(durations[side]),
                "staffing_trace": traces[side],
            }
        )
    report = {
        "seed": seed,
        "candidate_seat": seat,
        "mode": mode,
        "quadrants": quadrants,
        "starting_assets": (25, 45, 65)[quadrants - 1],
        "statuses": [s.status for s in env.state],
        "states": len(env.steps),
        "candidate": players[seat],
        "reference": players[1 - seat],
        "cash_difference": players[seat]["cash"] - players[1 - seat]["cash"],
        "wage_saving": players[1 - seat]["wages"] - players[seat]["wages"],
    }
    if keep_replay:
        report["replay"] = json.loads(env.toJSON())
        report["initial_state"] = initial
    return report


def job(args):
    return run_fixture(*args)


def main_cli():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seeds", nargs="+", type=int, default=[17, 43])
    parser.add_argument("--quadrants", nargs="+", type=int, choices=[1, 2, 3], default=[1, 2, 3])
    parser.add_argument(
        "--modes",
        nargs="+",
        choices=list(MODES),
        default=["open_routes", "dated_closed", "dated_open"],
    )
    parser.add_argument("--workers", type=int, default=2)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=False)
    manifest = {
        "kind": "Controlled installed portfolios; no capital investment; not competition games",
        "created_at": datetime.now(UTC).isoformat(),
        "environment": environment_metadata(),
        "source_sha256": sha256(main.__file__),
        "runner_sha256": sha256(__file__),
        "seeds": args.seeds,
        "quadrants": args.quadrants,
        "modes": args.modes,
        "workers": args.workers,
        "starting_money": 30000,
        "initial_inputs": {"WHEAT": 20, "FERTILIZER": 20},
        "initial_crops_watered": True,
    }
    (args.output / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    jobs = [
        (seed, seat, q, mode)
        for mode in args.modes
        for q in args.quadrants
        for seed in args.seeds
        for seat in (0, 1)
    ]
    with (
        ProcessPoolExecutor(max_workers=args.workers) as pool,
        (args.output / "matches.jsonl").open("x") as file,
    ):
        for result in pool.map(job, jobs):
            file.write(json.dumps(result) + "\n")
            file.flush()
            c = result["candidate"]
            print(
                f"{result['mode']} land={result['quadrants']} seed={result['seed']} "
                f"seat={result['candidate_seat']} cash_delta={result['cash_difference']:+.0f} "
                f"wage_saving={result['wage_saving']:+.0f} unfed={c['unfed_days']} "
                f"decay={c['decayed_units']} stock={c['final_stock']}",
                flush=True,
            )
    assert sha256(main.__file__) == manifest["source_sha256"]


if __name__ == "__main__":
    main_cli()
