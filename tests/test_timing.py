"""Fertilizer timing uses the actual engine; capital and hiring rules remain fixed."""

import inspect
import runpy
from copy import deepcopy
from hashlib import sha256
from pathlib import Path

import pytest
from kaggle_environments import make
from kaggle_environments.envs.kaggriculture import kaggriculture as engine

from baselines import step_8
from experiments import timing
from scripts.benchmark_staffing import installed_environment
from scripts.make_timing_control import build


def strawberry_state(day=9, hour=8, watered=True):
    env = make("kaggriculture", configuration={"seed": 17})
    obs = env.state[0].observation
    obs.update(day=day, hour=hour, step=24 * day + hour)
    farm = obs.farms[0]
    farm["farmer"] = [3, 4]
    plant = engine._new_plant("STRAWBERRY", 0, 24)
    plant.update(watered_today=watered, consecutive_unwatered=1)
    farm["tiles"][4][3] = plant
    # This cell is a livestock station in the default layout; move it to a crop cell.
    site = timing.farm_sites(obs)[1][0]
    farm["tiles"][4][3] = None
    farm["tiles"][site[1]][site[0]] = plant
    farm["farmer"] = list(site)
    obs.private["inventories"][0]["FERTILIZER"] = 1
    return env, obs, plant


def test_fertilize_after_water_creates_actual_extra_strawberry_at_night():
    env, obs, tile = strawberry_state()
    before = deepcopy(obs)
    assert step_8.fertilizer_value(tile, obs, env.configuration, timing.MARKET) == 0
    assert timing.timing_fertilizer_value(tile, obs, env.configuration, timing.MARKET) > 0
    action, _ = timing.expansion_turn(obs, env.configuration, timing=1, investments=False)
    assert obs == before
    assert action["farmer"] == ["FERTILIZE"]
    engine._apply_unit_action(obs.farms[0], obs.private, 0, action["farmer"], 10, 9, 24)
    engine._daily_refresh_plants(obs.farms[0], 9, 24)
    assert tile["yield_units"] == 2
    assert obs.private["inventories"][0].get("FERTILIZER", 0) == 0


def test_urgent_water_preserves_time_for_fertilizer_then_water():
    env, obs, tile = strawberry_state(watered=False)
    action, _ = timing.expansion_turn(obs, env.configuration, timing=1, investments=False)
    assert action["farmer"] == ["FERTILIZE"]
    engine._apply_unit_action(obs.farms[0], obs.private, 0, action["farmer"], 10, 9, 24)
    obs.update(hour=9, step=225)
    action, _ = timing.expansion_turn(obs, env.configuration, timing=1, investments=False)
    assert action["farmer"] == ["WATER"]
    engine._apply_unit_action(obs.farms[0], obs.private, 0, action["farmer"], 10, 9, 24)
    engine._daily_refresh_plants(obs.farms[0], 9, 24)
    assert tile["yield_units"] == 2


def test_last_hour_preserves_survival_water_before_optional_fertilizer():
    env, obs, _ = strawberry_state(hour=23, watered=False)
    action, _ = timing.expansion_turn(obs, env.configuration, timing=1, investments=False)
    assert action["farmer"] == ["WATER"]


@pytest.mark.parametrize("case", ["full", "active", "last_day", "wrong_date", "low_price"])
def test_fertilizer_requires_extra_sellable_yield_and_positive_value(case):
    env, obs, tile = strawberry_state()
    if case == "full":
        tile["yield_units"] = 3
    elif case == "active":
        tile["fertilized_until_day"] = 9
    elif case == "last_day":
        obs.update(day=29, hour=20, step=716)
        tile["planted_day"] = 20
    elif case == "wrong_date":
        obs.update(day=8, step=200)
    else:
        obs.market["inventory"]["STRAWBERRY"] = 100000
    assert timing.timing_fertilizer_value(tile, obs, env.configuration, timing.MARKET) <= 0


def test_wheat_cannot_receive_retroactive_fertilizer_bonus():
    env, obs, tile = strawberry_state()
    tile.update(crop="WHEAT", planted_day=7, yield_units=2)
    assert timing.timing_fertilizer_value(tile, obs, env.configuration, timing.MARKET) == 0
    engine._apply_unit_action(obs.farms[0], obs.private, 0, ["FERTILIZE"], 10, 9, 24)
    engine._apply_unit_action(obs.farms[0], obs.private, 0, ["WATER"], 10, 9, 24)
    assert tile["yield_units"] == 2


def test_final_productive_night_and_shared_tile_reservation():
    env, obs, tile = strawberry_state(day=28, hour=22)
    tile["planted_day"] = 19
    obs.market["inventory"]["STRAWBERRY"] = 8000
    farm = obs.farms[0]
    farm["hands"] = [list(farm["farmer"])]
    obs.private["inventories"].append({"FERTILIZER": 1})
    action, _ = timing.expansion_turn(obs, env.configuration, timing=1, investments=False)
    commands = [action["farmer"], *action["hands"]]
    assert commands.count(["FERTILIZE"]) == 1
    for worker, command in enumerate(commands):
        engine._apply_unit_action(farm, obs.private, worker, command, 10, 28, 24)
    engine._daily_refresh_plants(farm, 28, 24)
    assert tile["yield_units"] == 2
    obs.update(day=29, hour=0, step=696)
    assert timing.timing_fertilizer_value(tile, obs, env.configuration, timing.MARKET) == 0


def test_early_wheat_harvest_accounts_for_lost_growth():
    env = make("kaggriculture", configuration={"seed": 17})
    obs = env.state[0].observation
    obs.update(day=3, hour=4, step=76)
    tile = engine._new_plant("WHEAT", 0, 24)
    tile.update(yield_units=3, watered_today=True)
    value = timing.early_harvest_value(tile, obs, env.configuration, timing.MARKET)
    assert value["units_now_after_water"] == 3
    assert value["units_at_planned_harvest"] == 4
    assert not value["harvest_now"]


def test_disabled_timing_matches_original_on_installed_observations():
    for q in (1, 2, 3):
        env = installed_environment(17, q)
        for seat in (0, 1):
            obs = env.state[seat].observation
            assert timing.expansion_turn(obs, env.configuration)[0] == step_8.agent(
                obs, env.configuration
            )


def test_investment_and_hiring_rules_are_unchanged():
    for name in (
        "investment_plan",
        "opening_portfolios",
        "production_projection",
        "production_orders",
        "expansion_investment",
        "fertilizer_value",
        "crop_job",
        "plan_turn",
    ):
        assert inspect.getsource(getattr(timing, name)) == inspect.getsource(getattr(step_8, name))
    start, end = "    # Bound whole-day work", "    alternatives = []"
    current = inspect.getsource(timing.mixed_turn).split(start)[1].split(end)[0]
    original = inspect.getsource(step_8.mixed_turn).split(start)[1].split(end)[0]
    assert current == original


def test_frozen_entry_point_and_explanation_use_the_same_timing_mode(tmp_path):
    path = tmp_path / "main.py"
    build(timing.__file__, path, "fertilizer", bake_default=True)
    loaded = runpy.run_path(str(path))
    env, obs, _ = strawberry_state()
    action = loaded["agent"](obs, env.configuration)
    explained, detail = loaded["expansion_turn"](obs, env.configuration)
    assert action == explained
    assert action["farmer"] == ["FERTILIZE"]
    assert detail["mixed"]["fertilizer_values"]


def test_current_submission_is_the_exact_frozen_timing_candidate(tmp_path):
    path = tmp_path / "main.py"
    build(timing.__file__, path, "fertilizer", bake_default=True)
    assert path.read_bytes() == Path("main.py").read_bytes()
    assert sha256(path.read_bytes()).hexdigest() == (
        "47c281bfb4118a9755f1759930b162de007efdfef3b23144457eccbaac42da0c"
    )
