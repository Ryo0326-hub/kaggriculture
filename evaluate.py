"""Reproducible local matches using Kaggle's actual agent loader and interpreter."""

import argparse
import csv
import hashlib
import json
import math
import platform
import statistics
import sys
from collections import Counter
from datetime import UTC, datetime
from importlib.metadata import version
from pathlib import Path
from time import perf_counter

from kaggle_environments import make
from kaggle_environments.envs.kaggriculture import kaggriculture as engine

ROOT = Path(__file__).resolve().parent
BUILTINS = {"starter", "pass"}
BAD_STATUSES = {"ERROR", "INVALID", "TIMEOUT"}


def sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def agent_reference(value):
    if value in BUILTINS:
        return value
    path = Path(value).resolve()
    if not path.is_file() or path.suffix != ".py":
        raise ValueError(f"Expected a .py agent file or one of {sorted(BUILTINS)}: {value}")
    return str(path)


def agent_metadata(reference):
    if reference in BUILTINS:
        return {"id": reference, "name": reference, "kind": "builtin"}
    digest = sha256(reference)
    return {
        "id": f"{Path(reference).name}@{digest[:12]}",
        "name": Path(reference).name,
        "kind": "file",
        "sha256": digest,
    }


def environment_metadata():
    directory = Path(engine.__file__).parent
    return {
        "package": "kaggle-environments",
        "version": version("kaggle-environments"),
        "python": platform.python_version(),
        "engine_sha256": sha256(directory / "kaggriculture.py"),
        "specification_sha256": sha256(directory / "kaggriculture.json"),
    }


def economic_audit(env, seat):
    """Order-cost accounting and production diagnostics; cash remains engine-authoritative."""
    operations, harvested = Counter(), Counter()
    hired, wages, seed_cost, lost_plants, seed_conflicts, duplicate_targets = 0, 0, 0, 0, 0, 0
    animal_cost, escapes, missed_feed, feed_orders = 0, 0, 0, 0
    for before, after in zip(env.steps, env.steps[1:]):
        old, new = before[seat].observation, after[seat].observation
        action = after[seat].action
        if not isinstance(action, dict):
            continue
        farm = old.farms[seat]
        commands = [action.get("farmer", ["PASS"]), *action.get("hands", [])]
        plant_requests, targets = Counter(), []
        for p, op in zip([farm["farmer"], *farm["hands"]], commands):
            if not isinstance(op, list) or not op:
                continue
            operations[op[0]] += 1
            tile = farm["tiles"][p[1]][p[0]]
            if op[0] in {"PLANT", "WATER", "HARVEST", "DIG", "FEED", "CARE", "COLLECT_FERTILIZER"}:
                targets.append(tuple(p))
            if op[0] == "PLANT" and len(op) > 1:
                plant_requests[op[1]] += 1
            if op[0] == "HARVEST" and isinstance(tile, dict) and tile.get("crop"):
                harvested[tile["crop"]] += tile.get("yield_units", 0)
            elif op[0] == "HARVEST" and isinstance(tile, dict) and tile.get("animal"):
                harvested[engine.ANIMALS[tile["animal"]]["product"]] += tile.get("yield_units", 0)
        seed_conflicts += sum(n > old.private["seeds"].get(c, 0) for c, n in plant_requests.items())
        duplicate_targets += len(targets) - len(set(targets))
        hire_index = farm["hires_today"]
        for order in action.get("market", []):
            if order[0] == "HIRE":
                hired += 1
                wages += engine._hire_cost(hire_index, env.configuration.farmHandCostMult)
                hire_index += 1
            elif order[0] == "BUY_SEED" and len(order) >= 3 and order[1] in engine.CROPS:
                seed_cost += engine.CROPS[order[1]]["seed"] * order[2]
            elif order[0] == "BUY_ANIMAL" and len(order) >= 3 and order[1] in engine.ANIMALS:
                animal_cost += engine.ANIMALS[order[1]]["cost"] * order[2]
            elif order[0] == "BUY_PRODUCT" and len(order) >= 3 and order[1] == "WHEAT":
                feed_orders += order[2]
        for y, tiles in enumerate(farm["tiles"]):
            for x, tile in enumerate(tiles):
                following = new.farms[seat]["tiles"][y][x]
                if isinstance(tile, dict) and tile.get("kind") == "PLANT":
                    lost_plants += int(
                        isinstance(following, dict) and following.get("kind") == "WEED"
                    )
                if isinstance(tile, dict) and "animal" in tile:
                    escapes += int(not isinstance(following, dict) or "animal" not in following)
                    if old.day != new.day and isinstance(following, dict) and "animal" in following:
                        missed_feed += int(following["consecutive_unfed"] > 0)
    return {
        "unit_actions": dict(operations),
        "harvested_units": dict(harvested),
        "hire_orders": hired,
        "hire_order_cost": wages,
        "seed_order_cost": seed_cost,
        "plants_lost_to_weeds": lost_plants,
        "seed_overrequests": seed_conflicts,
        "duplicate_crop_targets": duplicate_targets,
        "animal_order_cost": animal_cost,
        "feed_order_units": feed_orders,
        "animals_escaped": escapes,
        "animal_days_unfed": missed_feed,
    }


def run_match(candidate, opponent, seed, seat, episode_steps=720):
    if seat not in (0, 1):
        raise ValueError("seat must be 0 or 1")
    env = make("kaggriculture", configuration={"seed": seed, "episodeSteps": episode_steps})
    agents = [opponent, opponent]
    agents[seat] = candidate
    started = perf_counter()
    env.run(agents)
    elapsed = perf_counter() - started
    final = env.steps[-1]
    statuses = [s.status for s in final]
    failures = [
        {"state_index": i, "player": p, "status": s.status}
        for i, states in enumerate(env.steps)
        for p, s in enumerate(states)
        if s.status in BAD_STATUSES
    ]
    # Never classify a crash (including an opponent crash) as an economic win.
    valid = not failures and statuses == ["DONE", "DONE"] and len(env.steps) == episode_steps
    cash = [float(s.observation.farms[p]["money"]) for p, s in enumerate(final)]
    if not all(math.isfinite(v) for v in cash):
        valid = False
    margin = cash[seat] - cash[1 - seat]
    outcome = ("win" if margin > 0 else "loss" if margin < 0 else "draw") if valid else "error"
    actions = Counter()
    durations = []
    for states in env.steps[1:]:
        action = states[seat].action
        if isinstance(action, dict):
            actions[action.get("farmer", ["PASS"])[0]] += 1
    for logs in env.logs:
        if len(logs) > seat and isinstance(logs[seat], dict) and "duration" in logs[seat]:
            durations.append(logs[seat]["duration"])
    private = final[seat].observation.private
    record = {
        "seed": seed,
        "seat": seat,
        "opponent": agent_metadata(opponent)["id"],
        "outcome": outcome,
        "candidate_cash": cash[seat],
        "opponent_cash": cash[1 - seat],
        "margin": margin,
        "candidate_status": statuses[seat],
        "opponent_status": statuses[1 - seat],
        "recorded_states": len(env.steps),
        # Replay storage keeps the shared step field on player zero only.
        "last_action_step": env.steps[-2][0].observation.step,
        "resolved_seed": env.info["seed"],
        "elapsed_seconds": elapsed,
        "decision_max_seconds": max(durations, default=0),
        "decision_p99_seconds": sorted(durations)[int(0.99 * (len(durations) - 1))]
        if durations
        else 0,
        "unsold_shed_units": sum(private["shed"].values()),
        "unsold_carried_units": sum(sum(inv.values()) for inv in private["inventories"]),
        "unused_seeds": sum(private["seeds"].values()),
        "farmer_actions": dict(actions),
        "failures": failures,
        "economics": {
            "candidate": economic_audit(env, seat),
            "opponent": economic_audit(env, 1 - seat),
        },
    }
    return record, env


def summarize(records):
    counts = Counter(row["outcome"] for row in records)
    valid = [row for row in records if row["outcome"] != "error"]
    return {
        "games": len(records),
        "wins": counts["win"],
        "draws": counts["draw"],
        "losses": counts["loss"],
        "errors": counts["error"],
        "match_score": (counts["win"] + 0.5 * counts["draw"]) / len(valid) if valid else None,
        "mean_cash": statistics.mean(r["candidate_cash"] for r in valid) if valid else None,
        "mean_margin": statistics.mean(r["margin"] for r in valid) if valid else None,
        "decision_max_seconds": max((r["decision_max_seconds"] for r in records), default=0),
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--agent", default=str(ROOT / "main.py"))
    parser.add_argument("--opponents", nargs="+", default=["starter"])
    parser.add_argument("--seeds", nargs="+", type=int, default=[11, 29, 47])
    parser.add_argument("--output", type=Path, default=ROOT / "artifacts" / "baseline")
    parser.add_argument("--replays", choices=["first", "all", "none"], default="first")
    args = parser.parse_args()
    if len(set(args.seeds)) != len(args.seeds):
        parser.error("Seeds must be unique; repeated deterministic games are not new evidence")
    try:
        candidate = agent_reference(args.agent)
        opponents = [agent_reference(value) for value in args.opponents]
    except ValueError as error:
        parser.error(str(error))
    if len(set(opponents)) != len(opponents):
        parser.error("Opponents must be unique")
    # Preserve previous experiments rather than accidentally overwriting their evidence.
    args.output.mkdir(parents=True, exist_ok=False)
    manifest = {
        "created_at": datetime.now(UTC).isoformat(),
        "environment": environment_metadata(),
        "candidate": agent_metadata(candidate),
        "opponents": [agent_metadata(value) for value in opponents],
        "seeds": args.seeds,
        "seats": [0, 1],
        "episode_steps": 720,
        "runner_sha256": sha256(__file__),
        "lock_sha256": sha256(ROOT / "uv.lock"),
    }
    (args.output / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    records = []
    with (args.output / "matches.jsonl").open("w") as output:
        for opponent in opponents:
            for seed in args.seeds:
                for seat in (0, 1):
                    row, env = run_match(candidate, opponent, seed, seat)
                    records.append(row)
                    if len(records) == 1:
                        manifest["configuration"] = dict(env.configuration)
                        (args.output / "manifest.json").write_text(
                            json.dumps(manifest, indent=2) + "\n"
                        )
                    output.write(json.dumps(row) + "\n")
                    output.flush()
                    index = len(records)
                    save = args.replays == "all" or (args.replays == "first" and index == 1)
                    if save or row["outcome"] == "error":
                        (args.output / f"replay-{index:04d}.json").write_text(
                            json.dumps(env.toJSON())
                        )
                        (args.output / f"logs-{index:04d}.json").write_text(json.dumps(env.logs))
                    print(
                        f"seed={seed} seat={seat} opponent={row['opponent']} "
                        f"{row['outcome']} cash={row['candidate_cash']:.0f} "
                        f"margin={row['margin']:+.0f}",
                        flush=True,
                    )
    if (
        agent_metadata(candidate) != manifest["candidate"]
        or [agent_metadata(value) for value in opponents] != manifest["opponents"]
    ):
        raise RuntimeError("Agent files changed during evaluation; discard this run")
    summary = {
        "overall": summarize(records),
        "by_opponent": {
            name: summarize([r for r in records if r["opponent"] == name])
            for name in sorted({r["opponent"] for r in records})
        },
        "interpretation": "Development baseline only; no leaderboard or medal-strength claim.",
    }
    (args.output / "summary.json").write_text(json.dumps(summary, indent=2) + "\n")
    fields = [k for k in records[0] if k not in ("farmer_actions", "failures", "economics")]
    with (args.output / "matches.csv").open("w", newline="") as output:
        writer = csv.DictWriter(output, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(records)
    print(json.dumps(summary, indent=2))
    return 1 if summary["overall"]["errors"] else 0


if __name__ == "__main__":
    sys.exit(main())
