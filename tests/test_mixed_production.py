"""Crop growth, opportunity cost, committed work, and full mixed-game contracts."""

from copy import deepcopy

import pytest
from kaggle_environments import make
from kaggle_environments.envs.kaggriculture import kaggriculture as engine

import main
from baselines import step_5
from evaluate import ROOT, economic_audit, run_match


@pytest.mark.parametrize("crop", ["WHEAT", "MELON", "STRAWBERRY"])
def test_dated_crop_output_matches_engine_schedule(crop):
    env = make("kaggriculture", configuration={"seed": 17})
    farm = env.state[0].observation.farms[0]
    private = env.state[0].observation.private
    farm["tiles"][4][4] = engine._new_plant(crop, 0, 24)
    forecast = main.crop_flows(farm["tiles"][4][4], 0, 29)
    observed = {}
    for day in range(30):
        for _ in range(3):
            tile = farm["tiles"][4][4]
            job = main.crop_job(tile, day, 29)
            if not job:
                break
            op = job[0]
            if op == "HARVEST":
                observed[day] = observed.get(day, 0) + tile["yield_units"]
            engine._apply_unit_action(farm, private, 0, [op], 10, day, 24)
        engine._daily_refresh_plants(farm, day, 24)
    assert observed == forecast
    assert sum(observed.values()) == {"WHEAT": 4, "MELON": 6, "STRAWBERRY": 4}[crop]


def test_fertilizer_compares_extra_output_with_sale_opportunity():
    env = make("kaggriculture", configuration={"seed": 17})
    obs = env.state[0].observation
    obs.update(day=2, hour=0, step=48)
    tile = engine._new_plant("WHEAT", 0, 24)
    assert (
        main.fertilizer_value(tile, obs, env.configuration, main.MARKET) == 0
        or main.fertilizer_value(tile, obs, env.configuration, main.MARKET) < 0
    )
    obs.market["inventory"]["WHEAT"] = 8000
    assert main.fertilizer_value(tile, obs, env.configuration, main.MARKET) > 0
    tile["watered_today"] = True
    assert main.fertilizer_value(tile, obs, env.configuration, main.MARKET) == 0


def test_crop_admission_rejects_unrecoverable_horizon_and_oversupply():
    env = make("kaggriculture", configuration={"seed": 17})
    obs = env.state[0].observation
    obs.update(day=22, hour=0, step=528)
    assert main.crop_value(obs, env.configuration, main.MARKET, "MELON", 23)["value"] < 0
    obs.update(day=2, hour=0, step=48)
    obs.market["inventory"]["MELON"] = 12000
    assert main.crop_value(obs, env.configuration, main.MARKET, "MELON", 3)["value"] < 0
    assert main.crop_value(obs, env.configuration, main.MARKET, "WHEAT", 3)["value"] > 0


def test_dated_staffing_charges_added_capacity_and_respects_horizon():
    env = make("kaggriculture", configuration={"seed": 17})
    obs = env.state[0].observation
    obs.update(day=3, hour=0, step=72)
    for x, y in [(4, 4), (3, 4), (4, 3), (2, 4)]:
        obs.farms[0]["tiles"][y][x] = engine._new_animal("COW", 0)
    baseline = main.crop_staff_cost(obs, env.configuration)
    extra = main.crop_staff_cost(obs, env.configuration, {"crop": "MELON", "planted_day": 4})
    assert extra > baseline
    assert (
        main.crop_staff_cost(obs, env.configuration, {"crop": "MELON", "planted_day": 30})
        == baseline
    )


def test_planting_commits_to_first_watering_even_during_new_installation():
    env = make("kaggriculture", configuration={"seed": 17})
    obs = env.state[0].observation
    obs.update(day=4, hour=22, step=118)
    obs.farms[0]["farmer"] = [0, 4]
    obs.farms[0]["tiles"][4][0] = engine._new_plant("MELON", 4, 24)
    obs.private["shed"]["COW"] = 1
    action, _ = main.mixed_turn(obs, env.configuration)
    assert action["farmer"] == ["WATER"]
    env.step([action, {}])
    assert env.state[0].observation.farms[0]["tiles"][4][0]["watered_today"]


def test_late_water_is_feasible_without_same_turn_harvest_bundle():
    tile = engine._new_plant("WHEAT", 0, 24)
    assert main.crop_job(tile, 4, 29) == ("WATER", 260, 1)
    tile["watered_today"] = True
    assert main.crop_job(tile, 4, 29)[0] == "HARVEST"


def test_newborn_watering_cannot_be_stolen_by_an_earlier_worker():
    env = make("kaggriculture", configuration={"seed": 17})
    obs = env.state[0].observation
    obs.update(day=5, hour=22, step=142)
    farm = obs.farms[0]
    farm["farmer"], farm["hands"] = [1, 4], [[0, 4]]
    obs.private["inventories"].append({})
    animal = engine._new_animal("COW", 0)
    animal.update(fed_today=True, cared_today=True)
    farm["tiles"][4][4] = animal
    farm["tiles"][4][0] = engine._new_plant("WHEAT", 5, 24)
    action, _ = main.mixed_turn(obs, env.configuration)
    assert action["hands"][0] == ["WATER"]
    assert action["farmer"] != ["WEST"]


def test_late_owned_fertilizer_does_not_force_return_before_survival_water():
    env = make("kaggriculture", configuration={"seed": 17})
    obs = env.state[0].observation
    obs.update(day=4, hour=21, step=117)
    farm = obs.farms[0]
    farm["farmer"] = [4, 0]
    animal = engine._new_animal("COW", 0)
    animal.update(fed_today=True, cared_today=True)
    farm["tiles"][4][4] = animal
    farm["tiles"][0][4] = engine._new_plant("WHEAT", 2, 24)
    obs.private["inventories"][0]["FERTILIZER"] = 1
    obs.market["inventory"]["WHEAT"] = 8000
    action, _ = main.mixed_turn(obs, env.configuration)
    assert action["farmer"] == ["FERTILIZE"]


def test_mixed_policy_is_pure_and_disabled_control_preserves_step_5():
    env = make("kaggriculture", configuration={"seed": 17})
    obs = env.state[0].observation
    before = deepcopy(obs)
    assert main.mixed_turn(obs, env.configuration, crop_limit=0) == step_5.plan_turn(
        obs, env.configuration
    )
    a = main.mixed_turn(obs, env.configuration)
    assert a == main.mixed_turn(obs, dict(env.configuration, seed=123456))
    assert before == obs


@pytest.mark.parametrize("held,expected_loss", [(0, 0), (1, 1)])
def test_expiration_diagnostic_does_not_hide_unharvested_output(held, expected_loss):
    env = make("kaggriculture", configuration={"seed": 17, "episodeSteps": 4})
    tile = engine._new_plant("STRAWBERRY", -16, 24)
    tile.update(yield_units=held, max_lifespan_step=0)
    env.state[0].observation.farms[0]["tiles"][4][4] = tile
    env.step([{}, {}])
    report = economic_audit(env, 0)
    assert report["plants_lost_to_weeds"] == 1
    assert report["unplanned_crop_losses"] == expected_loss


@pytest.fixture(scope="module")
def mixed_games():
    return [
        run_match(str(ROOT / "main.py"), str(ROOT / "baselines/step_5.py"), seed, seat)
        for seed, seat in [(17, 0), (43, 1)]
    ]


def test_mixed_full_seasons_preserve_resources_and_bank_output(mixed_games):
    for row, env in mixed_games:
        assert row["outcome"] != "error"
        assert row["unsold_shed_units"] == row["unsold_carried_units"] == row["unused_seeds"] == 0
        audit = row["economics"]["candidate"]
        assert audit["animals_escaped"] == audit["animal_days_unfed"] == 0
        assert audit["seed_overrequests"] == audit["duplicate_crop_targets"] == 0
        assert audit["unplanned_crop_losses"] == 0
        assert audit["harvested_units"]["MELON"] > 0
        seat = row["seat"]
        for before, after in zip(env.steps, env.steps[1:]):
            obs = before[seat].observation
            farm, private = obs.farms[seat], obs.private
            action = after[seat].action
            assert len(action["hands"]) == len(farm["hands"])
            assert len(action["market"]) <= env.configuration.maxMarketOrdersPerTurn
            stock = dict(private["shed"])
            seeds = dict(private["seeds"])
            room = env.configuration.shedCapacity - sum(stock.values())
            for pos, inv, op in zip(
                [farm["farmer"], *farm["hands"]],
                private["inventories"],
                [action["farmer"], *action["hands"]],
            ):
                tile = farm["tiles"][pos[1]][pos[0]]
                if op[0] == "PICKUP":
                    assert engine._is_shed_adjacent(pos, 10)
                    assert 0 < op[2] <= stock.get(op[1], 0)
                    stock[op[1]] -= op[2]
                    room += op[2]
                elif op[0] == "DROP":
                    assert engine._is_shed_adjacent(pos, 10)
                    assert sum(inv.values()) <= room
                    room -= sum(inv.values())
                    for c, n in inv.items():
                        stock[c] = stock.get(c, 0) + n
                elif op[0] == "PLACE" and op[1] in main.MARKET:
                    assert engine._is_shed_adjacent(pos, 10)
                    assert 0 < op[2] <= min(room, inv.get(op[1], 0))
                    stock[op[1]] = stock.get(op[1], 0) + op[2]
                    room -= op[2]
                elif op[0] == "PLANT":
                    assert tile is None and seeds[op[1]] > 0
                    seeds[op[1]] -= 1
                elif op[0] == "WATER":
                    assert tile.get("crop") and not tile["watered_today"]
                elif op[0] == "FERTILIZE":
                    assert tile.get("crop") and inv.get("FERTILIZER", 0) > 0
                elif op[0] == "FEED":
                    assert tile.get("animal") and inv.get("WHEAT", 0) > 0 and not tile["fed_today"]
                elif op[0] == "HARVEST":
                    assert tile["yield_units"] > 0
                    if tile.get("crop"):
                        assert (
                            obs.day - tile["planted_day"]
                            >= engine.CROPS[tile["crop"]]["first_yield_day"]
                        )
            for order in action["market"]:
                if order[0] == "SELL":
                    assert 0 < order[2] <= stock[order[1]]
                    stock[order[1]] -= order[2]
