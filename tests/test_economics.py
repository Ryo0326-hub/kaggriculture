from copy import deepcopy

import pytest
from kaggle_environments import make
from kaggle_environments.envs.kaggriculture import kaggriculture as engine

from baselines.step_3 import (
    CROPS,
    MARKET,
    batch_revenue,
    crop_forecast,
    optimize_lots,
    plan_turn,
    price_at,
)

PASS = {"farmer": ["PASS"], "hands": [], "market": []}


@pytest.mark.parametrize("crop", list(CROPS))
def test_price_curve_matches_pinned_engine(crop):
    for inventory in [0, 9000, 9550, 9800, 9999, 10000, 10001, 10050, 10500, 100000]:
        assert price_at(crop, inventory, MARKET) == engine.market_price(crop, inventory)
    params = deepcopy(MARKET)
    params[crop].update({"base": 40, "above_func": "sq", "above_target": 2})
    for inventory in [9990, 10000, 10100, 10500]:
        assert price_at(crop, inventory, params) == engine.market_price(crop, inventory, params)


@pytest.mark.parametrize(
    "crop,inventory,quantity",
    [
        ("WHEAT", 9900, 50),
        ("WHEAT", 10000, 100),
        ("CARROT", 10000, 90),
        ("CARROT", 11000, 15),
    ],
)
def test_integrated_sale_revenue_matches_real_transaction(crop, inventory, quantity):
    env = make("kaggriculture", configuration={"seed": 7})
    obs = env.state[0].observation
    obs.market["inventory"][crop] = inventory
    obs.private["shed"][crop] = quantity
    before = obs.farms[0]["money"]
    env.step([{**PASS, "market": [["SELL", crop, quantity]]}, PASS])
    assert env.state[0].observation.farms[0]["money"] - before == batch_revenue(
        crop, inventory, quantity, MARKET
    )


def test_two_crop_integer_plan_respects_joint_cash_and_work_constraints():
    # A wheat lot returns 8/15 at quantity 1/2; carrot returns 10/17.
    # Thirty cash buys one of each: 18 beats either pure allocation.
    values = [[0, 8, 15], [0, 10, 17]]
    assert optimize_lots(values, [10, 20], [0, 0], 2, 8, 30) == (18, (1, 1), 30)
    # Four actions admit only one lot; carrot is preferred.
    assert optimize_lots(values, [10, 20], [0, 0], 2, 4, 30) == (10, (0, 1), 20)
    # Owned seeds consume no new cash; the objective table must already reflect sunk cost.
    assert optimize_lots(values, [10, 20], [1, 0], 2, 8, 20) == (18, (1, 1), 20)


def test_forecast_counts_observed_duplicate_shop_instances():
    env = make("kaggriculture", configuration={"seed": 7})
    obs = env.state[0].observation
    obs.town["unlocked_shops"] = ["PET_CAFE", "PET_CAFE", "FARMERS_MARKET"]
    forecast = crop_forecast(obs, env.configuration, "CARROT", MARKET)
    assert forecast["observed_daily_demand"] == 31  # 12 + 12 + 6 + one town center.
    assert forecast["inventory_at_harvest"] == 10000 - 3 * 31


def test_hiring_responds_to_workload_and_price():
    env = make("kaggriculture", configuration={"seed": 7})
    obs = env.state[0].observation
    full, detail = plan_turn(obs, env.configuration)
    assert full["market"].count(["HIRE"]) == 4
    assert detail["economics"]["lots"]["CARROT"] == 0
    assert detail["economics"]["lots"]["WHEAT"] > 0
    scarce = deepcopy(obs)
    scarce.market["inventory"]["CARROT"] = 9500
    _, opportunity = plan_turn(scarce, env.configuration)
    assert opportunity["economics"]["lots"]["CARROT"] > 0
    expensive = dict(env.configuration, farmHandCostMult=10000)
    action, _ = plan_turn(obs, expensive)
    assert ["HIRE"] not in action["market"]
    small = deepcopy(obs)
    for y in range(5):
        for x in range(5):
            if (x, y) not in {(4, 4), (3, 4)}:
                small.farms[0]["tiles"][y][x] = "LOCKED"
    action, _ = plan_turn(small, env.configuration)
    assert ["HIRE"] not in action["market"]


def test_loss_making_production_and_terminal_planting_are_rejected():
    env = make("kaggriculture", configuration={"seed": 7})
    obs = env.state[0].observation
    cfg = dict(env.configuration, marketParams={c: {"base": 1} for c in CROPS})
    action, _ = plan_turn(obs, cfg)
    assert action["market"] == []
    obs["day"], obs["hour"], obs["step"] = 28, 0, 672
    action, detail = plan_turn(obs, env.configuration)
    assert detail["plant_crop"] is None
    assert action["market"] == []


def test_short_endgame_cycle_is_valued_at_its_reduced_yield():
    env = make("kaggriculture", configuration={"seed": 7})
    obs = env.state[0].observation
    obs["day"], obs["hour"], obs["step"] = 27, 0, 648
    action, detail = plan_turn(obs, env.configuration)
    assert detail["economics"]["crop_days_and_yield"] == {"WHEAT": 2, "CARROT": 2}
    assert any(a[0] == "BUY_SEED" for a in action["market"])


def test_observed_cash_funds_both_seed_orders_and_hires():
    env = make("kaggriculture", configuration={"seed": 7, "startingMoney": 25})
    action, detail = plan_turn(env.state[0].observation, env.configuration)
    cost = detail["economics"]["hire_cost"] + sum(
        CROPS[a[1]]["seed"] * a[2] for a in action["market"] if a[0] == "BUY_SEED"
    )
    assert cost <= 25


def test_planner_is_pure_and_does_not_use_evaluation_seed():
    env = make("kaggriculture", configuration={"seed": 7})
    obs = env.state[0].observation
    original = deepcopy(obs)
    result = plan_turn(obs, env.configuration)
    assert obs == original
    assert plan_turn(obs, dict(env.configuration, seed=999999)) == result
