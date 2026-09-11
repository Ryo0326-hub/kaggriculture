"""Carrot economics and action semantics checked against the pinned interpreter."""

import ast
import runpy
from copy import deepcopy
from pathlib import Path

import pytest
from kaggle_environments import make
from kaggle_environments.envs.kaggriculture import kaggriculture as engine

from baselines import cycle_3
from evaluate import ROOT, run_match
from scripts.make_carrot_control import build


@pytest.fixture
def policy(tmp_path):
    path = tmp_path / "main.py"
    build(cycle_3.__file__, path)
    return runpy.run_path(str(path))


@pytest.mark.parametrize("fertilized,units", [(False, 3), (True, 4)])
def test_carrot_column_and_dispatch_match_actual_growth(policy, fertilized, units):
    env = make("kaggriculture", configuration={"seed": 17})
    farm, private = env.state[0].observation.farms[0], env.state[0].observation.private
    farm["tiles"][4][4] = engine._new_plant("CARROT", 0, 24)
    col = policy["crop_column"]("CARROT", 0, 29, fertilized)
    private["inventories"][0]["FERTILIZER"] = len(col["fertilizer"])
    for day in range(4):
        tile = farm["tiles"][4][4]
        if day in col["fertilizer"]:
            engine._apply_unit_action(farm, private, 0, ["FERTILIZE"], 10, day, 24)
        for _ in range(2):
            job = policy["crop_job"](tile, day, 29)
            if job is None:
                break
            engine._apply_unit_action(farm, private, 0, [job[0]], 10, day, 24)
            if job[0] == "HARVEST":
                break
        if day < 3:
            engine._daily_refresh_plants(farm, day, 24)
    assert private["inventories"][0]["CARROT"] == units == col["outputs"][3]
    assert farm["tiles"][4][4] is None
    assert private["inventories"][0].get("FERTILIZER", 0) == 0
    assert col["fertilizer"] == ([2] if fertilized else [])


@pytest.mark.parametrize(
    "age,watered,units,expiry",
    [
        (2, False, 1, -1),
        (2, True, 2, -1),
        (2, True, 3, 4),
        (3, False, 2, -1),
        (3, False, 3, -1),
        (3, True, 3, -1),
        (3, True, 4, 4),
    ],
)
def test_remaining_growth_never_repeats_water_or_exceeds_engine_cap(
    policy, age, watered, units, expiry
):
    env = make("kaggriculture", configuration={"seed": 17})
    farm, private = env.state[0].observation.farms[0], env.state[0].observation.private
    tile = engine._new_plant("CARROT", 0, 24)
    tile.update(watered_today=watered, yield_units=units, fertilized_until_day=expiry)
    farm["tiles"][4][4] = tile
    col = policy["crop_column"]("CARROT", 0, 29, True, tile, age)
    private["inventories"][0]["FERTILIZER"] = len(col["fertilizer"])
    for day in range(age, 4):
        if day in col["fertilizer"]:
            engine._apply_unit_action(farm, private, 0, ["FERTILIZE"], 10, day, 24)
        engine._apply_unit_action(farm, private, 0, ["WATER"], 10, day, 24)
        if day == 3:
            assert tile["yield_units"] == col["outputs"][3] <= 4
        else:
            engine._daily_refresh_plants(farm, day, 24)


def test_first_day_water_decay_and_terminal_salvage(policy):
    env = make("kaggriculture", configuration={"seed": 17})
    farm = env.state[0].observation.farms[0]
    farm["tiles"][4][4] = engine._new_plant("CARROT", 0, 24)
    assert policy["crop_job"](farm["tiles"][4][4], 0, 29)[0] == "WATER"
    engine._daily_refresh_plants(farm, 0, 24)
    assert farm["tiles"][4][4]["kind"] == "WEED"
    tile = engine._new_plant("CARROT", 0, 24)
    tile["yield_units"] = 3
    farm["tiles"][4][4] = tile
    engine._decay_plants(farm, 95)
    assert farm["tiles"][4][4] is tile
    engine._decay_plants(farm, 96)
    assert tile["yield_units"] == 2
    assert policy["crop_column"]("CARROT", 0, 29, tile=tile, today=4)["outputs"] == {4: 2}
    engine._decay_plants(farm, 97)
    assert tile["yield_units"] == 2
    engine._decay_plants(farm, 98)
    assert tile["yield_units"] == 1
    engine._decay_plants(farm, 100)
    assert farm["tiles"][4][4]["kind"] == "WEED"
    assert policy["crop_column"]("CARROT", 27, 29) is None
    col = policy["crop_column"](
        "CARROT", 27, 29, tile=engine._new_plant("CARROT", 27, 24), today=29
    )
    assert col["outputs"] == {29: 2}
    assert policy["crop_column"]("CARROT", 0, 29, today=4) is None
    assert policy["crop_job"](engine._new_plant("CARROT", 27, 24), 29, 29)[0] == "WATER"


def test_snapshot_matches_water_then_harvest_and_deposit_sale(policy):
    env = make("kaggriculture", configuration={"seed": 17})
    obs, cfg = env.state[0].observation, env.configuration
    obs.update(day=3, hour=0, step=72)
    tile = engine._new_plant("CARROT", 0, 24)
    tile.update(yield_units=3, fertilized_until_day=4)
    obs.farms[0]["tiles"][4][4] = tile
    for op in (["WATER"], ["HARVEST"]):
        forecast = policy["planning_snapshot"](obs, cfg, [op], [], cycle_3.MARKET)
        engine._apply_unit_action(obs.farms[0], obs.private, 0, op, 10, 3, 24)
        assert forecast.farms[0]["tiles"] == obs.farms[0]["tiles"]
        assert forecast.private["inventories"] == obs.private["inventories"]
    assert obs.private["inventories"][0]["CARROT"] == 4
    forecast = policy["planning_snapshot"](
        obs, cfg, [["DROP"]], [["SELL", "CARROT", 4]], cycle_3.MARKET
    )
    engine._apply_unit_action(obs.farms[0], obs.private, 0, ["DROP"], 10, 3, 24)
    for _ in range(4):
        price = engine.market_price("CARROT", obs.market["inventory"]["CARROT"])
        engine._commit_unit("SELL", "CARROT", price, obs.farms[0], obs.private, obs.market)
    assert forecast.farms[0]["money"] == obs.farms[0]["money"]
    assert forecast.private == obs.private


def test_fertilizer_prices_its_extra_unit_and_skips_capped_or_already_watered_crop(policy):
    env = make("kaggriculture", configuration={"seed": 17})
    obs, cfg = env.state[0].observation, env.configuration
    obs.update(day=2, hour=0, step=48)
    tile = engine._new_plant("CARROT", 0, 24)
    assert policy["fertilizer_value"](tile, obs, cfg, cycle_3.MARKET) < 0
    obs.market["inventory"]["CARROT"] = 9000
    assert policy["fertilizer_value"](tile, obs, cfg, cycle_3.MARKET) > 0
    tile["watered_today"] = True
    assert policy["fertilizer_value"](tile, obs, cfg, cycle_3.MARKET) == 0
    obs["day"] = 3
    tile.update(watered_today=False, yield_units=3)
    assert policy["fertilizer_value"](tile, obs, cfg, cycle_3.MARKET) == 0


@pytest.mark.parametrize("day", [0, 2, 12, 25])
def test_no_demand_preserves_incumbent_actions_and_opening(policy, day):
    env = make("kaggriculture", configuration={"seed": 17})
    obs, cfg = env.state[0].observation, env.configuration
    obs.update(day=day, hour=0, step=24 * day)
    obs.town["unlocked_shops"] = ["YARN_STORE"] if day else []
    before = deepcopy(obs)
    action, detail = policy["expansion_turn"](obs, cfg, timing=1)
    old_action, _ = cycle_3.expansion_turn(obs, cfg, timing=1)
    assert action == old_action and obs == before
    assert action == policy["expansion_turn"](obs, dict(cfg, seed=999), timing=1)[0]
    if day >= 2:
        assert not any(
            o["columns"][0].get("crop") == "CARROT" for o in detail["expansion"]["alternatives"]
        )


def test_visible_demand_admits_both_carrot_templates_at_real_seed_cost(policy):
    env = make("kaggriculture", configuration={"seed": 17})
    obs, cfg = env.state[0].observation, env.configuration
    obs.update(day=12, hour=0, step=288)
    obs.town["unlocked_shops"] = ["PET_CAFE"]
    obs.farms[0]["money"] = 50000
    obs.market["inventory"]["CARROT"] = 9000
    for x, y in policy["farm_sites"](obs)[0]:
        animal = engine._new_animal("COW", 0)
        animal["fed_today"] = True
        obs.farms[0]["tiles"][y][x] = animal
    obs.private["shed"]["WHEAT"] = 20
    _, report = policy["expansion_investment"](obs, cfg, cycle_3.MARKET, [["PASS"]], [], 3)
    options = [o for o in report["alternatives"] if o["columns"][0].get("crop") == "CARROT"]
    assert options
    assert {o["columns"][0]["fertilized"] for o in options} == {False, True}
    for option in options:
        assert option["cost_now"] == option["land_cost"] + 20 * len(option["columns"])
    assert report["chosen"]["orders"][-1][1] == "CARROT"


def test_source_isolation_original_crop_results_and_reproduction(policy, tmp_path):
    source = Path(cycle_3.__file__)
    target = tmp_path / "reproduced.py"
    build(source, target)
    assert target.read_bytes() == Path(policy["__file__"]).read_bytes()
    before, after = [
        {
            n.name: ast.dump(n)
            for n in ast.parse(p.read_text()).body
            if isinstance(n, ast.FunctionDef)
        }
        for p in (source, target)
    ]
    changed = {name for name in before if before[name] != after[name]}
    assert changed == {
        "crop_flows",
        "crop_column",
        "crop_job",
        "fertilizer_value",
        "farm_service",
        "planning_snapshot",
        "production_orders",
        "expansion_investment",
    }
    for crop in cycle_3.CROPS:
        for day in (0, 2, 9, 16, 25):
            for fertilized in (False, True):
                assert policy["crop_column"](crop, day, 29, fertilized) == cycle_3.crop_column(
                    crop, day, 29, fertilized
                )
    with pytest.raises(FileExistsError):
        build(source, target)
    with pytest.raises(ValueError):
        build(target, tmp_path / "wrong.py")


def test_carrot_pressure_control_loads_and_completes_a_season(tmp_path):
    target = tmp_path / "carrot_pressure.py"
    build(ROOT / "opponents/scaled_mixed.py", target, pressure=True)
    row, env = run_match(str(target), "pass", 17, 0)
    assert row["outcome"] != "error"
    opening = env.steps[1][0].action["market"]
    assert [o for o in opening if o[0] == "BUY_SEED"] == [
        ["BUY_SEED", "MELON", 4],
        ["BUY_SEED", "WHEAT", 6],
        ["BUY_SEED", "CARROT", 5],
    ]
    assert row["economics"]["candidate"]["harvested_units"]["CARROT"] > 0
