"""Full dispatch/input sequences, including the urgent carrot path."""

import ast
import runpy
from copy import deepcopy
from pathlib import Path

import pytest
from kaggle_environments import make
from kaggle_environments.envs.kaggriculture import kaggriculture as engine

from baselines import cycle_3
from scripts.make_carrot_control import build as build_carrots
from scripts.make_carrot_input_control import build


@pytest.fixture
def policy(tmp_path):
    path = tmp_path / "inputs.py"
    build(path)
    return runpy.run_path(str(path))


def fixture(day=3, hour=7, position=(0, 4), carried=0, shed=0):
    env = make("kaggriculture", configuration={"seed": 17})
    obs = env.state[0].observation
    obs.update(day=day, hour=hour, step=day * 24 + hour)
    farm, private = obs.farms[0], obs.private
    farm["farmer"] = list(position)
    tile = engine._new_plant("CARROT", day - 3, 24)
    tile.update(yield_units=2, consecutive_unwatered=1)
    farm["tiles"][4][0] = tile
    private["inventories"][0]["FERTILIZER"] = carried
    private["shed"]["FERTILIZER"] = shed
    obs.market["inventory"]["CARROT"] = 7000
    obs.town["unlocked_shops"] = ["PET_CAFE"]
    return env


def step(env, action):
    obs = env.state[0].observation
    previous = obs["step"]
    env.state[0].action = action
    env.state[1].action = {"farmer": ["PASS"], "hands": [], "market": []}
    engine.interpreter(env.state, env)
    obs["step"] = previous + 1


@pytest.mark.parametrize("carried,shed,first", [(1, 0, "FERTILIZE"), (0, 1, "EAST")])
def test_urgent_bundle_really_loads_fertilizes_waters_and_harvests(policy, carried, shed, first):
    env = fixture(carried=carried, shed=shed)
    actions = []
    for _ in range(15):
        action, _ = policy["expansion_turn"](
            env.state[0].observation, env.configuration, investments=False
        )
        actions.append(action["farmer"][0])
        step(env, action)
        if "HARVEST" in actions:
            break
    assert actions[0] == first
    assert actions.index("FERTILIZE") < actions.index("WATER") < actions.index("HARVEST")
    assert env.state[0].observation.private["inventories"][0]["CARROT"] == 4
    assert env.state[0].observation.farms[0]["tiles"][4][0] is None
    if shed:
        assert actions.index("PICKUP") < actions.index("FERTILIZE")


def test_purchased_input_is_retained_and_executed_next_turn(policy):
    env = fixture(hour=0, position=(4, 4))
    obs, cfg = env.state[0].observation, env.configuration
    plan = policy["carrot_input_plan"](obs, cfg, cycle_3.MARKET, [0], [], {}, obs.private.shed)
    assert plan["buy"] == 1
    assert plan["bundles"][0]["action"] == ["PASS"]
    market = policy["fund_carrot_inputs"](obs, cfg, cycle_3.MARKET, [["PASS"]], [], plan)
    assert market == [["BUY_PRODUCT", "FERTILIZER", 1]]
    step(env, {"farmer": ["PASS"], "hands": [], "market": market})
    # Keep ordinary investment off to identify the exact input sequence. The
    # interpreter still processes real unit actions, markets and town demand.
    actions = []
    for _ in range(12):
        action, _ = policy["expansion_turn"](obs, cfg, investments=False)
        actions.append(action["farmer"][0])
        assert not any(o[:2] == ["SELL", "FERTILIZER"] for o in action["market"])
        step(env, action)
        if "HARVEST" in actions:
            break
    assert actions[0] == "PICKUP"
    assert actions.index("FERTILIZE") < actions.index("WATER") < actions.index("HARVEST")


@pytest.mark.parametrize("hour,expected", [(15, "FERTILIZE"), (16, "WATER")])
def test_terminal_bundle_needs_time_to_bank_the_harvest(policy, hour, expected):
    env = fixture(day=29, hour=hour, carried=1)
    obs, cfg = env.state[0].observation, env.configuration
    action, _ = policy["expansion_turn"](obs, cfg, investments=False)
    assert action["farmer"] == [expected]
    start = obs.farms[0]["money"]
    for _ in range(23 - hour):
        action, _ = policy["expansion_turn"](obs, cfg, investments=False)
        step(env, action)
    assert obs.farms[0]["money"] > start
    assert not sum(obs.private["shed"].values())
    assert not any(sum(inv.values()) for inv in obs.private["inventories"])


def test_post_buy_price_and_full_action_cost_reject_marginal_input(policy):
    env = fixture(hour=0, position=(4, 4))
    obs, cfg = env.state[0].observation, env.configuration
    obs.market["inventory"]["CARROT"] = 9450
    params = deepcopy(cycle_3.MARKET)
    params["FERTILIZER"].update(base=60, T=1)
    tile = obs.farms[0]["tiles"][4][0]
    assert policy["carrot_fertilizer_value"](tile, obs, cfg, params) > 0
    plan = policy["carrot_input_plan"](obs, cfg, params, [0], [], {}, obs.private.shed)
    assert plan["buy"] == 0 and not plan["bundles"]


def test_one_shed_input_is_never_promised_to_two_workers(policy):
    env = fixture(hour=7, position=(4, 4), shed=1)
    obs, cfg = env.state[0].observation, env.configuration
    obs.farms[0]["hands"] = [[4, 4]]
    obs.private["inventories"].append({})
    obs.farms[0]["tiles"][3][1] = deepcopy(obs.farms[0]["tiles"][4][0])
    action, detail = policy["expansion_turn"](obs, cfg, investments=False)
    bundles = detail["mixed"]["carrot_inputs"]["bundles"]
    assert len(bundles) == 1
    assert sum(a[:2] == ["PICKUP", "FERTILIZER"] for a in [action["farmer"], *action["hands"]]) == 1
    step(env, action)
    assert obs.private["shed"]["FERTILIZER"] == 0
    assert sum(i.get("FERTILIZER", 0) for i in obs.private["inventories"]) == 1


def test_animal_obligations_and_newborn_water_are_not_borrowed(policy):
    env = fixture(hour=7, position=(4, 4), carried=1)
    obs, cfg = env.state[0].observation, env.configuration
    obs.farms[0]["tiles"][4][4] = engine._new_animal("COW", 0)
    obs.private["inventories"][0]["WHEAT"] = 1
    action, detail = policy["expansion_turn"](obs, cfg, investments=False)
    assert action["farmer"] == ["FEED"]
    assert not detail["mixed"]["carrot_inputs"]["bundles"]
    plan = policy["carrot_input_plan"](obs, cfg, cycle_3.MARKET, [0], [0], {}, obs.private.shed)
    assert not plan["bundles"]


def test_funding_checks_existing_cash_orders_capacity_and_market_slots(policy):
    env = fixture(hour=0, position=(4, 4))
    obs, cfg = env.state[0].observation, env.configuration
    plan = policy["carrot_input_plan"](obs, cfg, cycle_3.MARKET, [0], [], {}, obs.private.shed)
    obs.farms[0]["money"] = 151 + plan["purchase_cost"]
    market = [["HIRE"], ["HIRE"]]
    assert (
        policy["fund_carrot_inputs"](obs, cfg, cycle_3.MARKET, [["PASS"]], market[:], plan)
        == market
    )
    assert plan["funded"] == 0
    obs.farms[0]["money"] = 10000
    obs.private["shed"]["WHEAT"] = 100
    assert policy["fund_carrot_inputs"](obs, cfg, cycle_3.MARKET, [["PASS"]], [], plan) == []
    obs.private["shed"]["WHEAT"] = 0
    assert policy["fund_carrot_inputs"](
        obs, dict(cfg, maxMarketOrdersPerTurn=1), cycle_3.MARKET, [["PASS"]], [["HIRE"]], plan
    ) == [["HIRE"]]


def test_forecast_only_credits_fertilizer_already_applied(policy):
    env = fixture(carried=1)
    obs, cfg = env.state[0].observation, env.configuration
    assert policy["crop_column"]("CARROT", 4, 29, True)["outputs"] == {7: 3}
    assert policy["crop_column"]("CARROT", 4, 29, True)["fertilizer"] == []
    action, _ = policy["expansion_turn"](obs, cfg, investments=False)
    snapshot = policy["planning_snapshot"](obs, cfg, [action["farmer"]], [], cycle_3.MARKET)
    col = policy["crop_column"]("CARROT", 0, 29, True, snapshot.farms[0]["tiles"][4][0], 3)
    assert col["outputs"] == {3: 4} and not col["fertilizer"]


def test_original_rules_and_opening_are_preserved_and_build_is_reproducible(policy, tmp_path):
    old = tmp_path / "carrots.py"
    build_carrots(cycle_3.__file__, old)
    new = tmp_path / "again.py"
    build(new)
    assert new.read_bytes() == Path(policy["__file__"]).read_bytes()
    trees = [
        {
            n.name: ast.dump(n)
            for n in ast.parse(p.read_text()).body
            if isinstance(n, ast.FunctionDef)
        }
        for p in (old, new)
    ]
    assert {name for name in trees[0] if trees[0][name] != trees[1][name]} == {
        "crop_column",
        "farm_service",
        "mixed_turn",
        "production_orders",
        "expansion_investment",
    }
    env = make("kaggriculture", configuration={"seed": 17})
    obs, cfg = env.state[0].observation, env.configuration
    assert policy["agent"](obs, cfg) == cycle_3.agent(obs, cfg)
    for crop in cycle_3.CROPS:
        assert policy["crop_column"](crop, 2, 29, True) == cycle_3.crop_column(crop, 2, 29, True)
