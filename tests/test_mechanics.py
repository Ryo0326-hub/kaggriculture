"""Regression probes against the pinned official interpreter, via public env.step()."""

import pytest
from kaggle_environments import make

PASS = {"farmer": ["PASS"], "hands": [], "market": []}


@pytest.fixture
def env():
    return make("kaggriculture", configuration={"seed": 17, "weedSpawnChance": 0})


def play(env, farmer=None, market=None, hands=None):
    return env.step(
        [
            {"farmer": farmer or ["PASS"], "market": market or [], "hands": hands or []},
            PASS,
        ]
    )


def test_purchase_cannot_supply_same_turn_planting(env):
    play(env, ["PLANT", "WHEAT"], [["BUY_SEED", "WHEAT", 1]])
    assert env.state[0].observation.farms[0]["tiles"][4][4] is None
    play(env, ["PLANT", "WHEAT"])
    assert env.state[0].observation.farms[0]["tiles"][4][4]["crop"] == "WHEAT"


@pytest.mark.parametrize("water,expected", [(False, "WEED"), (True, "PLANT")])
def test_new_seed_needs_water_on_planting_day(env, water, expected):
    play(env, market=[["BUY_SEED", "WHEAT", 1]])
    while env.state[0].observation.step < 22:
        play(env)
    play(env, ["PLANT", "WHEAT"])
    play(env, ["WATER"] if water else ["PASS"])
    assert env.state[0].observation.farms[0]["tiles"][4][4]["kind"] == expected


def test_excess_simultaneous_planting_cancels_both_requests(env):
    play(env, market=[["BUY_SEED", "WHEAT", 1], ["HIRE"]])
    play(env, hands=[["WEST"]])
    play(env, hands=[["WEST"]])
    play(env, ["PLANT", "WHEAT"], hands=[["PLANT", "WHEAT"]])
    obs = env.state[0].observation
    assert obs.farms[0]["tiles"][4][4] is None
    assert obs.farms[0]["tiles"][4][3] is None
    assert obs.private["seeds"]["WHEAT"] == 1


def test_feed_requires_worker_inventory(env):
    play(env, ["BUILD_PASTURE"], [["BUY_ANIMAL", "COW", 1], ["BUY_PRODUCT", "WHEAT", 1]])
    play(env, ["PICKUP", "COW", 1])
    play(env, ["PLACE", "COW"])
    play(env, ["FEED"])
    assert not env.state[0].observation.farms[0]["tiles"][4][4]["fed_today"]
    play(env, ["PICKUP", "WHEAT", 1])
    play(env, ["FEED"])
    assert env.state[0].observation.farms[0]["tiles"][4][4]["fed_today"]


def test_end_of_day_shed_overflow_is_lost(env):
    # Arrange a nearly full store and field inventory to isolate the deposit rule.
    env.state[0].observation.private["shed"] = {"WHEAT": 99}
    env.state[0].observation.private["inventories"] = [{"WHEAT": 5}]
    for _ in range(24):
        play(env)
    private = env.state[0].observation.private
    assert private["shed"]["WHEAT"] == 100
    assert private["inventories"] == [{}]


def test_buy_product_price_changes_with_inventory(env):
    # The supplied getting-started guide says fixed BUY_PRODUCT prices; engine disagrees.
    obs = env.state[0].observation
    obs.market["inventory"]["WHEAT"] = 9_600
    before = obs.farms[0]["money"]
    play(env, market=[["BUY_PRODUCT", "WHEAT", 1]])
    assert before - env.state[0].observation.farms[0]["money"] > 25


def test_last_action_can_drop_and_sell_without_an_extra_turn():
    env = make("kaggriculture", configuration={"seed": 17, "episodeSteps": 4})
    play(env)
    play(env)
    assert env.state[0].observation.step == 2
    env.state[0].observation.private["inventories"] = [{"WHEAT": 3}]
    play(env, ["DROP"], [["SELL", "WHEAT", 3]])
    assert env.done
    assert len(env.steps) == 4
    assert env.state[0].reward > 3_000
    assert sum(env.state[0].observation.private["shed"].values()) == 0
    assert env.state[0].observation.private["inventories"] == [{}]
