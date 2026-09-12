"""Audit frozen Cycle 13 decisions and bounded cases, without advancing a game."""

import argparse
import json
import runpy
from copy import deepcopy
from hashlib import sha256
from pathlib import Path

SOURCE_HASH = "542547dbe7cd63856b2a6f037e2014790c1410316c3b3872f67ea85c2b628947"
REPLAY_HASH = "a6bb766aa8563f76983944f93cd8a8905a1c366457ef88a9c865736a188dbd27"


def audit(source, replay_path):
    if sha256(source.read_bytes()).hexdigest() != SOURCE_HASH:
        raise ValueError("This audit requires the frozen Cycle 13 source")
    if sha256(replay_path.read_bytes()).hexdigest() != REPLAY_HASH:
        raise ValueError("This audit requires the supplied episode 107984963")
    replay = json.loads(replay_path.read_text())
    cfg = replay["configuration"]
    policy = runpy.run_path(str(source))["agent"]
    scope = policy.__globals__
    mismatches, staffing, tomato_nights, efficiency_choices = [], [], [], []
    for step, (before, after) in enumerate(zip(replay["steps"], replay["steps"][1:])):
        obs = deepcopy(before[0]["observation"])
        obs["step"] = step
        action, detail = scope["expansion_turn"](obs, cfg, timing=1)
        if action != after[0]["action"]:
            mismatches.append(step)
        investment = detail.get("expansion", {})
        chosen = investment.get("chosen")
        feasible = [
            candidate
            for candidate in investment.get("alternatives", [])
            if candidate["value"] > 0 and candidate["capacity_estimate_fits"]
        ]
        if chosen and feasible:
            most_value = max(feasible, key=lambda candidate: candidate["value"])
            if most_value["value"] > chosen["value"]:
                efficiency_choices.append(
                    {
                        "step": step,
                        "chosen": {k: chosen[k] for k in ("orders", "value", "score", "work")},
                        "higher_total_value": {
                            k: most_value[k] for k in ("orders", "value", "score", "work")
                        },
                    }
                )
        if obs["hour"] == 0:
            tiles = scope["throughput_assets"](obs)[0]
            estimated = scope["throughput_workers"](tiles, obs["day"], 29)
            dispatched = detail["mixed"]["worker_target"]
            staffing.append(
                {
                    "step": step,
                    "forecast_total_workers": estimated,
                    "dispatcher_target_total_workers": dispatched,
                    "forecast_full_day_wages": sum(
                        scope["hire_cost"](i, 1) for i in range(estimated - 1)
                    ),
                    "dispatcher_target_full_day_wages": sum(
                        scope["hire_cost"](i, 1) for i in range(dispatched - 1)
                    ),
                }
            )
        if obs["hour"] != 23 or obs["day"] >= 29:
            continue
        for y, row in enumerate(obs["farms"][0]["tiles"]):
            for x, tile in enumerate(row):
                if (
                    not isinstance(tile, dict)
                    or tile.get("crop") != "TOMATO"
                    or not tile["watered_today"]
                    or tile["fertilized_until_day"] < obs["day"]
                    or tile["yield_units"] != 0
                ):
                    continue
                following = after[0]["observation"]["farms"][0]["tiles"][y][x]
                if not isinstance(following, dict) or following.get("yield_units", 0) <= 0:
                    continue
                column = scope["crop_column"](
                    "TOMATO", tile["planted_day"], 29, False, tile, obs["day"]
                )
                tomato_nights.append(
                    {
                        "step": step,
                        "site": [x, y],
                        "fertilized_until_day": tile["fertilized_until_day"],
                        "forecast_next_day": column["outputs"].get(obs["day"] + 1, 0),
                        "recorded_next_day": following["yield_units"],
                    }
                )

    # Construct individual legal-shaped observations. Never apply their actions.
    def case(day, hour, crop, planted, units, cargo):
        obs = deepcopy(replay["steps"][0][0]["observation"])
        obs.update(day=day, hour=hour, step=day * 24 + hour)
        obs["farms"][0].update(money=50000, farmer=[1, 4])
        obs["private"]["inventories"] = [cargo]
        obs["farms"][0]["tiles"][4][1] = {
            "kind": "PLANT",
            "crop": crop,
            "planted_day": planted,
            "yield_units": units,
            "watered_today": False,
            "consecutive_unwatered": 1,
            "fertilized_until_day": -1,
            "max_lifespan_step": 720 if crop == "WHEAT" else -1,
        }
        return obs

    terminal = case(29, 19, "WHEAT", 25, 3, {"CARROT": 10})
    terminal_action = policy(deepcopy(terminal), cfg)
    tomato = case(10, 23, "TOMATO", 0, 3, {})
    tomato_action = policy(deepcopy(tomato), cfg)

    # Compare two workload calculations on a recorded farm and one extra crop.
    workload = deepcopy(replay["steps"][384][0]["observation"])
    _, detail = scope["plan_turn"](workload, cfg, allowed_animals=(), force_shared=True)
    herd_workers = detail["routing"]["target_hands"] + 1

    def crew(obs):
        return {
            "forecast": scope["throughput_workers"](
                scope["throughput_assets"](obs)[0], obs["day"], 29
            ),
            "dispatcher": scope["throughput_staff"](obs, cfg, herd_workers, 0),
        }

    before_crew = crew(workload)
    assert workload["farms"][0]["tiles"][1][4] is None
    workload["farms"][0]["tiles"][1][4] = {
        "kind": "PLANT",
        "crop": "WHEAT",
        "planted_day": 12,
        "yield_units": 4,
        "watered_today": True,
        "consecutive_unwatered": 0,
        "fertilized_until_day": -1,
        "max_lifespan_step": 408,
    }
    after_crew = crew(workload)
    return {
        "method": "Recorded-observation decisions, passive state differences and bounded "
        "constructed cases. No engine import, game advance or counterfactual episode.",
        "source_sha256": SOURCE_HASH,
        "replay_sha256": REPLAY_HASH,
        "matched_decisions": 719 - len(mismatches),
        "mismatch_steps": mismatches,
        "staffing_at_recorded_day_starts": staffing,
        "known_fertilized_tomato_nights": tomato_nights,
        "efficiency_preferred_to_higher_total_forecast": efficiency_choices,
        "constructed_terminal_case": {
            "observation": terminal,
            "action": terminal_action,
            "remaining_actions": 4,
            "shortest_moves_plus_drop": 4,
            "cargo": {"CARROT": 10},
            "one_non_delivery_action_leaves_insufficient_return_time": True,
        },
        "constructed_tomato_case": {
            "observation": tomato,
            "action": tomato_action,
            "remaining_actions_before_night": 1,
            "unwatered_counter_before_night": 1,
            "pinned_engine_weed_threshold": 2,
            "last_tomato_output_age": 11,
        },
        "constructed_marginal_labor_case": {
            "base_recorded_step": 384,
            "added_crop": "mature watered wheat at [4, 1]",
            "before": before_crew,
            "after": after_crew,
            "forecast_extra_daily_wages": sum(
                scope["hire_cost"](i, 1)
                for i in range(before_crew["forecast"] - 1, after_crew["forecast"] - 1)
            ),
            "dispatcher_extra_daily_wages": sum(
                scope["hire_cost"](i, 1)
                for i in range(before_crew["dispatcher"] - 1, after_crew["dispatcher"] - 1)
            ),
        },
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--replay", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    report = audit(args.source, args.replay)
    with args.output.open("x") as stream:
        json.dump(report, stream, indent=2)
        stream.write("\n")
    print(
        json.dumps(
            {
                "matched_decisions": report["matched_decisions"],
                "tomato_nights": len(report["known_fertilized_tomato_nights"]),
                "terminal_action": report["constructed_terminal_case"]["action"]["farmer"],
                "last_hour_tomato": report["constructed_tomato_case"]["action"]["farmer"],
                "marginal_labor": report["constructed_marginal_labor_case"],
            }
        )
    )


if __name__ == "__main__":
    main()
