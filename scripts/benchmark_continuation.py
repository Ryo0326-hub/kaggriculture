"""Offline interventions with reactive, reinvesting policies; not a release benchmark.

Recorded joint actions reconstruct only the prefix. The official runner then
supplies each policy its own observation, including the shared clock. Policies
must be deterministic and observation-based: Python memory is restarted at the
branch. A fully reproduced control is required for each diagnostic case.
"""

import argparse
import copy
import hashlib
import json
from collections import Counter
from concurrent.futures import ProcessPoolExecutor
from datetime import UTC, datetime
from pathlib import Path

from kaggle_environments import make
from kaggle_environments.agent import build_agent
from kaggle_environments.envs.kaggriculture import kaggriculture as engine

from evaluate import BAD_STATUSES, environment_metadata, sha256
from scripts import audit_replay as audit

CAPITAL = {"BUY_SEED", "BUY_ANIMAL", "BUY_LAND"}
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


def state_view(states):
    """All recorded game state, except wall-clock overage bookkeeping."""
    return [
        {
            "observation": {
                k: v for k, v in s["observation"].items() if k != "remainingOverageTime"
            },
            "status": s["status"],
            "reward": s["reward"],
        }
        for s in states
    ]


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True).encode()).hexdigest()


def reconstruct(replay, observation):
    if not 1 <= observation < len(replay["steps"]) - 1:
        raise ValueError("Branch must follow initialization and precede the final observation")
    env = make(
        "kaggriculture", configuration={**replay["configuration"], "seed": replay["info"]["seed"]}
    )
    # The engine removes the resolved seed from configuration; it is offline-only info.
    if env.configuration != replay["configuration"]:
        raise ValueError("Reconstructed configuration differs from the recorded configuration")
    for i in range(observation + 1):
        if i:
            env.step([s["action"] for s in replay["steps"][i]])
        if state_view(env.state) != state_view(replay["steps"][i]):
            raise ValueError(f"Prefix state mismatch at observation {i}")
    if env.done or env.state[0].observation.step != observation:
        raise ValueError("Branch clock/status mismatch")
    return env


def capital_orders(action):
    return [o for o in action["market"] if o[0] in CAPITAL]


def intervene(action, orders):
    """Preserve unit commands and all non-capital orders in their original order."""
    if any(not o or o[0] not in CAPITAL for o in orders):
        raise ValueError("Only capital orders may be inserted")
    result = copy.deepcopy(action)
    result["market"] = [o for o in result["market"] if o[0] not in CAPITAL]
    result["market"].extend(copy.deepcopy(orders))
    return result


def continuation_policy(path, env, observation, variant, trace):
    policy, _ = build_agent(str(Path(path).resolve()), env.agents, env.name)
    release = variant.get("release", observation + 1)
    if release <= observation:
        raise ValueError("Release must be after the intervention observation")

    def choose(obs, cfg):
        proposed = policy(obs, cfg)
        step = obs["step"]
        action = proposed
        if variant["name"] != "control" and step < release:
            orders = variant.get("orders", []) if step == observation else []
            action = intervene(proposed, orders)
        if len(action["market"]) > cfg["maxMarketOrdersPerTurn"]:
            raise ValueError("Intervention exceeds the market order limit")
        if capital_orders(proposed) or capital_orders(action) or step < release:
            trace.append(
                {
                    "observation": step,
                    "proposed": capital_orders(proposed),
                    "submitted": capital_orders(action),
                    "overridden": action != proposed,
                }
            )
        return action

    return choose


def first_difference(left, right, field, start):
    for i in range(start, min(len(left), len(right))):
        if field(left[i]) != field(right[i]):
            return i
    return None


def compare_trajectories(actual, reference, observation):
    a, b = actual["steps"], reference["steps"]
    if len(a) != len(b):
        raise ValueError("Incomplete continuation")
    return {
        "first_state_difference": first_difference(a, b, state_view, observation),
        "first_shop_difference": first_difference(
            a, b, lambda s: s[0]["observation"]["town"], observation
        ),
        "first_action_difference_by_seat": [
            first_difference(a, b, lambda s, p=p: s[p]["action"], observation + 1) for p in (0, 1)
        ],
    }


def run_continuation(replay, observation, seat, agents, variant):
    if seat not in (0, 1) or len(agents) != 2:
        raise ValueError("Two agents and a seat of 0 or 1 are required")
    env = reconstruct(replay, observation)
    start_digest = digest(state_view(env.state))
    trace = []
    policies = list(agents)
    policies[seat] = continuation_policy(agents[seat], env, observation, variant, trace)
    # len(steps) > 1 prevents run() from resetting the reconstructed prefix.
    env.run(policies)
    if (
        len(env.steps) != env.configuration.episodeSteps
        or any(s.status in BAD_STATUSES for states in env.steps for s in states)
        or [s.status for s in env.state] != ["DONE", "DONE"]
    ):
        raise ValueError("Continuation failed or did not finish; no economic result is valid")
    result = env.toJSON()
    comparison = compare_trajectories(result, replay, observation)
    if variant["name"] == "control" and (
        comparison["first_state_difference"] is not None
        or any(i is not None for i in comparison["first_action_difference_by_seat"])
    ):
        raise ValueError("Reactive control does not reproduce the recorded future")
    durations = [
        log[seat]["duration"]
        for log in env.logs
        if len(log) > seat and isinstance(log[seat], dict) and "duration" in log[seat]
    ]
    return result, {
        "variant": variant,
        "start_state_sha256": start_digest,
        "prefix_observations_verified": observation + 1,
        "comparison_with_recorded_control": comparison,
        "capital_trace": trace,
        "decision_max_seconds": max(durations, default=0),
        "statuses": [s.status for s in env.state],
        "recorded_states": len(env.steps),
    }


def audit_continuation(path, directory, observation, seat):
    originals = {name: getattr(engine, name) for name in HOOKS}
    try:
        for name, hook in HOOKS.items():
            setattr(engine, name, hook)
        full = audit.analyze(path, directory)
    finally:
        for name, fn in originals.items():
            setattr(engine, name, fn)
    replay = json.loads(path.read_text())
    players = []
    for p in (0, 1):
        events = [
            e for e in audit.context["transactions"] if e["seat"] == p and e["step"] >= observation
        ]
        work = [
            e for e in audit.context["unit_events"] if e["seat"] == p and e["step"] >= observation
        ]
        quantities, outputs, cash = Counter(), Counter(), Counter()
        for e in events:
            quantities[e["op"] + " " + e["item"]] += e["quantity"]
            cash[e["op"]] += e["cash"]
        for e in work:
            if e["op"] in ("HARVEST", "COLLECT_FERTILIZER"):
                outputs.update(e.get("inventory_gains", {}))
        start = replay["steps"][observation][p]["observation"]["farms"][p]["money"]
        end = full["players"][p]["cash"]
        sales, expenses = cash["SELL"], sum(v for k, v in cash.items() if k != "SELL")
        if start + sales - expenses != end:
            raise ValueError("Continuation cash does not reconcile")
        players.append(
            {
                "seat": p,
                "starting_cash": start,
                "final_cash": end,
                "sales": sales,
                "expenses": expenses,
                "cash_reconciled": True,
                "cash_by_operation": dict(cash),
                "executed_quantities": dict(quantities),
                "physical_output": dict(outputs),
                "ineffective_non_pass_ops": dict(
                    Counter(e["op"] for e in work if not e["changed"] and e["op"] != "PASS")
                ),
                # Full-game checks are labelled as such; they include the common prefix.
                "whole_game_checks": {
                    k: full["players"][p][k]
                    for k in (
                        "unfed_animal_days",
                        "escapes",
                        "decayed_units",
                        "end_day_overflow",
                        "explicit_overflow",
                        "final_shed",
                        "final_carried",
                        "final_seeds",
                    )
                },
            }
        )
    margin = players[seat]["final_cash"] - players[1 - seat]["final_cash"]
    return {
        "players": players,
        "margin": margin,
        "outcome": "win" if margin > 0 else "loss" if margin < 0 else "draw",
        "audit_sha256": sha256(directory / f"analysis-{path.stem}.json"),
    }


def run_case(job):
    case, output = job
    directory = Path(output) / case["name"]
    directory.mkdir()
    path = Path(case["replay"])
    replay = json.loads(path.read_text())
    observation, seat = case["observation"], case["seat"]
    if case["variants"][0] != {"name": "control"}:
        raise ValueError("First continuation must be an unchanged control")
    if len({v["name"] for v in case["variants"]}) != len(case["variants"]):
        raise ValueError("Duplicate variant names")
    records = []
    for variant in case["variants"]:
        actual, record = run_continuation(replay, observation, seat, case["agents"], variant)
        target = directory / f"{variant['name']}.json"
        target.write_text(json.dumps(actual) + "\n")
        record.update(audit_continuation(target, directory, observation, seat))
        record["replay_sha256"] = sha256(target)
        if records:
            control = records[0]
            record["difference_from_control"] = {
                "own_cash": record["players"][seat]["final_cash"]
                - control["players"][seat]["final_cash"],
                "opponent_cash": record["players"][1 - seat]["final_cash"]
                - control["players"][1 - seat]["final_cash"],
                "margin": record["margin"] - control["margin"],
            }
            if record["start_state_sha256"] != control["start_state_sha256"]:
                raise ValueError("Alternatives did not start from identical states")
        records.append(record)
        (directory / "results.json").write_text(json.dumps(records, indent=2) + "\n")
        print(
            f"{case['name']} {variant['name']}: {record['outcome']} "
            f"cash={record['players'][seat]['final_cash']} margin={record['margin']:+}",
            flush=True,
        )
    return {"case": case, "continuations": records}


def verify_sources(spec):
    for path, expected in spec["source_sha256"].items():
        if sha256(path) != expected:
            raise ValueError(f"Source mismatch: {path}")
    if engine_digest := spec.get("engine_sha256"):
        if sha256(engine.__file__) != engine_digest:
            raise ValueError("Pinned interpreter changed")
    for case in spec["cases"]:
        for path in [case["replay"], *case["agents"]]:
            if path not in spec["source_sha256"]:
                raise ValueError(f"Unpinned input: {path}")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cases", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--workers", type=int, choices=(1, 2), default=2)
    args = parser.parse_args()
    spec = json.loads(args.cases.read_text())
    verify_sources(spec)
    args.output.mkdir(parents=True, exist_ok=False)
    manifest = {
        "kind": "conditional continuation diagnostic, not independent games or a release gate",
        "created_at": datetime.now(UTC).isoformat(),
        "environment": environment_metadata(),
        "runner_sha256": sha256(__file__),
        "auditor_sha256": sha256(audit.__file__),
        "lock_sha256": sha256("uv.lock"),
        "spec_sha256": sha256(args.cases),
        "workers": args.workers,
        "specification": spec,
    }
    (args.output / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    with ProcessPoolExecutor(max_workers=args.workers) as pool:
        results = list(pool.map(run_case, [(c, str(args.output)) for c in spec["cases"]]))
    verify_sources(spec)
    if (
        sha256(__file__) != manifest["runner_sha256"]
        or sha256(audit.__file__) != manifest["auditor_sha256"]
    ):
        raise ValueError("Evaluator sources changed during the run")
    report = {"manifest": manifest, "results": results}
    (args.output / "report.json").write_text(json.dumps(report, indent=2) + "\n")


if __name__ == "__main__":
    main()
