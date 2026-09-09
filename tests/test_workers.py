"""Joint-action feasibility and full-season checks for the current artifact."""

import json
from copy import deepcopy

import pytest
from kaggle_environments import make

from evaluate import ROOT, run_match
from main import agent, plan_turn

PASS = {"farmer": ["PASS"], "hands": [], "market": []}


@pytest.fixture(scope="module")
def games():
    artifact = str(ROOT / "main.py")
    return [
        run_match(artifact, str(ROOT / "baselines/step_1.py"), 11, 0),
        run_match(artifact, str(ROOT / "baselines/step_1.py"), 11, 1),
        run_match(artifact, artifact, 29, 0),
        run_match(artifact, artifact, 29, 0),
    ]


def test_coordinated_full_seasons(games):
    for row, env in games:
        assert row["outcome"] != "error"
        assert row["recorded_states"] == 720
        assert row["last_action_step"] == 718
        assert row["unsold_shed_units"] == row["unsold_carried_units"] == 0
        seat = row["seat"]
        assert max(len(states[seat].observation.farms[seat]["hands"]) for states in env.steps) == 4
        assert all(not log.get("stderr") for turn in env.logs for log in turn)
        for before, after in zip(env.steps, env.steps[1:]):
            old, new = before[seat].observation, after[seat].observation
            farm = old.farms[seat]
            action = after[seat].action
            assert len(action["hands"]) == len(farm["hands"])
            operations = [action["farmer"], *action["hands"]]
            assert sum(a[0] == "PLANT" for a in operations) <= old.private.seeds.get("WHEAT", 0)
            targets = []
            for position, operation in zip([farm["farmer"], *farm["hands"]], operations):
                x, y = position
                if operation[0] in ("PLANT", "WATER", "HARVEST", "DIG"):
                    targets.append(tuple(position))
                    # Detect operations the engine silently ignored, including on hands.
                    assert farm["tiles"][y][x] != new.farms[seat]["tiles"][y][x]
            assert len(targets) == len(set(targets))
            for y, tiles in enumerate(farm["tiles"]):
                for x, tile in enumerate(tiles):
                    following = new.farms[seat]["tiles"][y][x]
                    if isinstance(tile, dict) and tile.get("kind") == "PLANT":
                        assert not (isinstance(following, dict) and following.get("kind") == "WEED")


def test_repeat_is_reproducible_in_the_same_seat(games):
    # Random weed draws differ across player positions; do not demand identical seat cash.
    for a, b in zip(games[2][1].steps, games[3][1].steps):
        assert a[0].action == b[0].action
        assert a[0].observation.farms == b[0].observation.farms
        assert a[0].observation.market == b[0].observation.market


def test_explanation_is_pure_and_matches_commands():
    env = make("kaggriculture", configuration={"seed": 5})
    obs = env.state[0].observation
    before = deepcopy(obs)
    action, explanation = plan_turn(obs, env.configuration)
    assert obs == before
    assert action == agent(obs, env.configuration)
    assert [worker["action"] for worker in explanation["workers"]] == [
        action["farmer"],
        *action["hands"],
    ]
    json.dumps(explanation, allow_nan=False)


def test_hires_start_acting_on_the_next_turn():
    env = make("kaggriculture", configuration={"seed": 5})
    action = agent(env.state[0].observation, env.configuration)
    assert action["hands"] == []
    assert action["market"].count(["HIRE"]) == 4
    env.step([action, PASS])
    following = agent(env.state[0].observation, env.configuration)
    assert len(following["hands"]) == 4


def test_shared_seed_reservation_avoids_atomic_cancellation():
    env = make("kaggriculture", configuration={"seed": 5, "weedSpawnChance": 0})
    obs = env.state[0].observation
    obs.farms[0]["hands"] = [[3, 4]]
    obs.private["inventories"] = [{}, {}]
    obs.private["seeds"] = {"WHEAT": 1}
    action = agent(obs, env.configuration)
    assert sum(a[0] == "PLANT" for a in [action["farmer"], *action["hands"]]) == 1
    env.step([action, PASS])
    tiles = env.state[0].observation.farms[0]["tiles"]
    assert sum(isinstance(t, dict) and t.get("crop") == "WHEAT" for row in tiles for t in row) == 1


def test_deposit_capacity_is_reserved_without_discarding_excess():
    env = make("kaggriculture", configuration={"seed": 5})
    obs = env.state[0].observation
    obs.farms[0]["hands"] = [[5, 4]]
    obs.private["inventories"] = [{"WHEAT": 5}, {"WHEAT": 5}]
    obs.private["shed"] = {"WHEAT": 98}
    action = agent(obs, env.configuration)
    assert sum(a[2] for a in [action["farmer"], *action["hands"]] if a[0] == "PLACE") == 2
    assert action["market"][0] == ["SELL", "WHEAT", 100]
    env.step([action, PASS])
    private = env.state[0].observation.private
    assert sum(inv.get("WHEAT", 0) for inv in private["inventories"]) == 8
    assert sum(private["shed"].values()) == 0


def test_terminal_action_deposits_and_sells():
    env = make("kaggriculture", configuration={"seed": 5, "episodeSteps": 4})
    env.step([PASS, PASS])
    env.step([PASS, PASS])
    env.state[0].observation.private["inventories"] = [{"WHEAT": 3}]
    action = agent(env.state[0].observation, env.configuration)
    assert action["farmer"] == ["PLACE", "WHEAT", 3]
    assert action["market"] == [["SELL", "WHEAT", 3]]
    env.step([action, PASS])
    assert env.done
    assert env.state[0].reward > 3_000
    assert env.state[0].observation.private["inventories"] == [{}]


def test_small_market_queue_does_not_plan_unissued_hires():
    env = make("kaggriculture", configuration={"seed": 5, "maxMarketOrdersPerTurn": 1})
    action, explanation = plan_turn(env.state[0].observation, env.configuration)
    assert len(action["market"]) <= 1
    assert explanation["planned_hires"] == action["market"].count(["HIRE"])
