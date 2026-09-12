"""Cycle 18 resource/deadline regressions; no environment import or state advance."""

import json
import random
import runpy
from copy import deepcopy

import pytest
from test_growth import animal, crop, observation

from scripts.check_growth_agent import validate
from scripts.make_growth_agent import build as build_parent
from scripts.make_production_agent import build


@pytest.fixture(scope="module")
def policy(tmp_path_factory):
    path = tmp_path_factory.mktemp("production") / "main.py"
    build(path)
    return runpy.run_path(str(path))["agent"].__globals__


def economy(policy, day=10, hour=4):
    obs = observation(day, hour)
    obs["market"]["inventory"] = {c: p["I0"] for c, p in policy["MARKET"].items()}
    obs["town"]["unlocked_shops"] = ["ICE_CREAM_SHOP", "SMOOTHIE_SHOP"]
    return obs


def berry(planted=1, watered=True):
    tile = crop("STRAWBERRY", planted)
    tile.update(yield_units=0, watered_today=watered, consecutive_unwatered=0)
    return tile


def dispatch(policy, obs):
    cfg, params = {}, policy["MARKET"]
    plan = policy["production_fertilizer_plan"](obs, cfg, params)
    jobs = policy["production_jobs"](obs, cfg, params, policy["growth_assets"](obs), plan)
    return policy["production_dispatch"](obs, cfg, params, jobs)


def test_deterministic_standalone_build_and_no_overwrite(tmp_path):
    a, b = tmp_path / "a.py", tmp_path / "b.py"
    assert build(a) == build(b)
    assert a.read_bytes() == b.read_bytes()
    with pytest.raises(FileExistsError):
        build(a)
    scope = runpy.run_path(str(a))
    assert [k for k, v in scope.items() if callable(v)][-1] == "agent"


def test_incremental_routing_matches_frozen_insertion_exactly(policy, tmp_path):
    parent = tmp_path / "parent.py"
    build_parent(parent)
    reference = runpy.run_path(str(parent))["growth_routes"]
    access = ((4, 4), (4, 5), (5, 4), (5, 5))
    rng = random.Random(18)
    for size in (0, 1, 5, 20, 55, 96):
        sites = rng.sample([(x, y) for x in range(10) for y in range(10)], size)
        nodes = tuple(
            (
                p,
                rng.randint(1, 6),
                rng.choice(
                    ((), ("WHEAT",), ("FERTILIZER",), ("WHEAT", "COW"), ("FERTILIZER", "WHEAT"))
                ),
            )
            for p in sites
        )
        for terminal in (False, True):
            for capacity in (1, 12, 22):
                assert policy["growth_routes"](nodes, access, capacity, terminal) == reference(
                    nodes, access, capacity, terminal
                )


def test_last_action_can_apply_fertilizer_to_watered_berry(policy):
    obs = economy(policy, hour=23)
    obs["farms"][0]["tiles"][4][4] = berry()
    obs["private"]["inventories"] = [{"FERTILIZER": 1}]
    assert policy["agent"](obs)["farmer"] == ["FERTILIZE"]


@pytest.mark.parametrize("name", ["WHEAT", "TOMATO", "STRAWBERRY"])
def test_survival_water_wins_over_optional_input_on_last_action(policy, name):
    obs = economy(policy, hour=23)
    obs["farms"][0]["tiles"][4][4] = crop(name, 9 if name == "WHEAT" else 1)
    obs["private"]["inventories"] = [{"FERTILIZER": 1}]
    assert policy["agent"](obs)["farmer"] == ["WATER"]


def test_last_action_feeds_animal_at_risk(policy):
    obs = economy(policy, hour=23)
    obs["farms"][0]["tiles"][4][4] = animal()
    obs["private"]["inventories"] = [{"WHEAT": 1, "FERTILIZER": 1}]
    assert policy["agent"](obs)["farmer"] == ["FEED"]


@pytest.mark.parametrize("name", ["TOMATO", "STRAWBERRY"])
def test_reachable_water_survives_bundle_deadline(policy, name):
    obs = economy(policy, hour=22)
    obs["farms"][0]["farmer"] = [3, 4]
    obs["farms"][0]["tiles"][4][2] = crop(name, 1)
    # One move + WATER fits, but one move + WATER + HARVEST does not.
    assert policy["agent"](obs)["farmer"] == ["WEST"]


def test_reachable_feed_survives_bundle_deadline(policy):
    obs = economy(policy, hour=21)
    obs["farms"][0]["tiles"][4][2] = animal()
    obs["private"]["inventories"] = [{"WHEAT": 1}]
    # Two moves + FEED fits; adding CARE and collection would miss night.
    commands, _, _, detail = dispatch(policy, obs)
    assert commands == [["WEST"]]
    assert detail["feed_sites"] == {0: ((2, 4),)}


def test_essential_feed_counts_depot_pickup(policy):
    obs = economy(policy, hour=21)
    obs["farms"][0]["tiles"][4][3] = animal()
    obs["private"]["shed"] = {"WHEAT": 1}
    assert dispatch(policy, obs)[0] == [["PICKUP", "WHEAT", 1]]
    # A separate fixed observation: pickup + move + feed no longer fits.
    obs.update(hour=22, step=10 * 24 + 22)
    assert dispatch(policy, obs)[3]["feed_sites"].get(0, ()) == ()


def test_essential_water_is_not_blocked_by_funded_optional_bonus(policy):
    obs = economy(policy, hour=22)
    obs["farms"][0]["farmer"] = [3, 4]
    obs["farms"][0]["tiles"][4][2] = berry(watered=False)
    obs["private"]["inventories"] = [{"FERTILIZER": 1}]
    commands, _, _, detail = dispatch(policy, obs)
    assert commands == [["WEST"]]
    assert detail["fertilizer_sites"] == {0: ()}


def test_missing_step_uses_day_hour_without_mutating_input(policy):
    obs = economy(policy)
    obs["farms"][0]["tiles"][4][3] = berry()
    expected = policy["agent"](obs)
    del obs["step"]
    before = deepcopy(obs)
    assert policy["agent"](obs) == expected
    assert obs == before


def test_carrier_gets_bonus_job_before_empty_lower_index_worker(policy):
    obs = economy(policy)
    obs["farms"][0].update(hands=[[4, 4]], hires_today=1)
    obs["farms"][0]["tiles"][4][3] = berry()
    obs["private"]["inventories"] = [{}, {"FERTILIZER": 1}]
    commands, _, _, detail = dispatch(policy, obs)
    assert commands[1] == ["WEST"]
    assert detail["fertilizer_sites"] == {1: ((3, 4),)}
    assert 0 not in detail["assigned"]


def test_pick_up_funded_input_before_visiting_crop(policy):
    obs = economy(policy)
    obs["farms"][0]["tiles"][4][3] = berry(watered=False)
    obs["private"]["shed"] = {"FERTILIZER": 1}
    commands, stock, _, detail = dispatch(policy, obs)
    assert commands == [["PICKUP", "FERTILIZER", 1]]
    assert stock["FERTILIZER"] == 0
    assert detail["fertilizer_sites"] == {0: ((3, 4),)}


def test_absent_optional_fertilizer_does_not_block_watering(policy):
    obs = economy(policy)
    obs["farms"][0]["tiles"][4][4] = berry(watered=False)
    commands, _, _, _ = dispatch(policy, obs)
    assert commands == [["WATER"]]


def test_scarce_fertilizer_allocates_highest_marginal_bonus(policy):
    jobs = {
        (3, 4): dict(ops=[["FERTILIZE"], ["WATER"]], fertilizer_value=10),
        (4, 3): dict(ops=[["FERTILIZE"], ["WATER"]], fertilizer_value=200),
    }
    ops = policy["production_route_ops"](((3, 4), (4, 3)), jobs, {"FERTILIZER": 1}, {})
    assert ops[3, 4] == [["WATER"]]
    assert ops[4, 3] == [["FERTILIZE"], ["WATER"]]


def test_stranded_fertilizer_does_not_cancel_today_depot_reserve(policy):
    obs = economy(policy)
    obs["private"]["inventories"] = [{"FERTILIZER": 4}]
    plan = {(0, 0): dict(deadline=10), (0, 1): dict(deadline=10)}
    reserve = policy["production_fertilizer_reserve"](obs, [["PASS"]], {}, plan)
    assert reserve["depot_target"] == 2
    assert reserve["credited_on_routes"] == 0


def test_assigned_carrier_is_credited_once(policy):
    obs = economy(policy)
    obs["private"]["inventories"] = [{"FERTILIZER": 1}]
    plan = {(3, 4): dict(deadline=10), (4, 3): dict(deadline=10)}
    reserve = policy["production_fertilizer_reserve"](
        obs, [["WEST"]], {"fertilizer_sites": {0: ((3, 4), (4, 3))}}, plan
    )
    assert reserve["credited_on_routes"] == 1
    assert reserve["depot_target"] == 1


def test_applied_input_not_reserved_again(policy):
    obs = economy(policy)
    obs["private"]["inventories"] = [{"FERTILIZER": 1}]
    reserve = policy["production_fertilizer_reserve"](
        obs, [["FERTILIZE"]], {"fertilizer_sites": {0: ((4, 4),)}}, {(4, 4): dict(deadline=10)}
    )
    assert reserve["today"] == reserve["depot_target"] == reserve["credited_on_routes"] == 0


def test_reserve_tomorrow_berry_wave_instead_of_selling_fertilizer(policy):
    obs = economy(policy, day=9, hour=14)
    obs["farms"][0]["tiles"][4][3] = berry()
    obs["private"]["shed"] = {"FERTILIZER": 2}
    action, detail = policy["production_turn"](obs)
    assert detail["fertilizer_reserve"]["tomorrow"] == 1
    assert ["SELL", "FERTILIZER", 1] in action["market"]
    assert ["SELL", "FERTILIZER", 2] not in action["market"]


def test_active_coverage_needs_no_new_application(policy):
    obs = economy(policy)
    obs["farms"][0]["tiles"][4][3] = dict(berry(), fertilized_until_day=12)
    assert policy["production_fertilizer_plan"](obs, {}, policy["MARKET"]) == {}


def test_floor_price_berries_do_not_trigger_fertilizer_purchase(policy):
    obs = observation(day=10)
    obs["market"]["inventory"]["STRAWBERRY"] = 1000000
    obs["farms"][0]["tiles"][4][3] = berry()
    assert policy["production_fertilizer_plan"](obs, {}, policy["MARKET"]) == {}


def test_unassigned_wheat_cannot_cancel_hungry_route_reserve(policy):
    obs = economy(policy, day=28)
    obs["private"]["inventories"] = [{"WHEAT": 10}]
    assets = [dict(animal(), site=(0, 0))]
    r = policy["production_feed_reserve"](obs, {}, [["PASS"]], {}, assets)
    assert r["today"] == r["depot_target"] == 1
    r = policy["production_feed_reserve"](
        obs, {}, [["WEST"]], {"feed_sites": {0: ((0, 0),)}}, assets
    )
    assert r["depot_target"] == 0


def test_same_action_harvest_is_included_in_carried_capacity(policy):
    obs = economy(policy)
    obs["farms"][0]["tiles"][4][4] = dict(berry(), yield_units=4)
    assert policy["production_carried_after"](obs, [["HARVEST"]]) == [{"STRAWBERRY": 4}]


def test_full_carried_load_blocks_additional_animal_inventory(policy):
    obs = economy(policy)
    obs["farms"][0]["money"] = 30000
    obs["farms"][0]["farmer"] = [0, 0]
    obs["private"]["inventories"] = [{"MILK": 100}]
    _, detail = policy["growth_investment"](obs, {}, policy["MARKET"], [["PASS"]], [], 30000)
    assert all(
        not any(o[0] == "BUY_ANIMAL" for o in option["orders"]) for option in detail["alternatives"]
    )


@pytest.mark.parametrize("remaining,expected", [(1, "PASS"), (2, "HARVEST"), (3, "WATER")])
def test_terminal_harvest_reserves_delivery(policy, remaining, expected):
    obs = economy(policy, day=29, hour=23 - remaining)
    obs["farms"][0]["tiles"][4][4] = crop("WHEAT", 25)
    assert policy["agent"](obs)["farmer"] == [expected]


def test_terminal_partial_deposit_then_sale_without_overflow(policy):
    obs = economy(policy, day=29, hour=22)
    obs["private"].update(shed={"WHEAT": 95}, inventories=[{"MILK": 4}, {"MILK": 4}])
    obs["farms"][0].update(hands=[[4, 4]], hires_today=1)
    action = policy["agent"](obs)
    assert action["farmer"] == ["DROP"]
    assert action["hands"] == [["PLACE", "MILK", 1]]
    assert ["SELL", "MILK", 5] in action["market"]
    assert not any(o[0].startswith("BUY") for o in action["market"])
    validate(obs, {}, action, policy)


def test_terminal_harvest_uses_available_worker_not_only_nearest(policy):
    obs = economy(policy, day=29, hour=20)
    obs["farms"][0].update(hands=[[3, 4]], hires_today=1)
    obs["farms"][0]["tiles"][4][4] = crop("WHEAT", 25)
    obs["private"]["inventories"] = [{"COW": 1}, {}]
    # The closest worker carries an animal and returns it to the shed.
    # The hand has time for move + HARVEST + DROP, but not extra WATER.
    action = policy["agent"](obs)
    assert action["farmer"] == ["DROP"]
    assert action["hands"] == [["EAST"]]
    validate(obs, {}, action, policy)


@pytest.mark.parametrize("tile", [None, "LOCKED", {"kind": "PASTURE"}])
@pytest.mark.parametrize("with_empty_product_key", [False, True])
def test_partial_animal_deposit_never_miscounts_an_installation(
    policy, tile, with_empty_product_key
):
    obs = economy(policy, day=29, hour=22)
    obs["farms"][0]["tiles"][4][4] = tile
    inv = {"MILK": 0, "COW": 2} if with_empty_product_key else {"COW": 2}
    obs["private"].update(shed={"WHEAT": 99}, inventories=[inv])
    action = policy["agent"](obs)
    if isinstance(tile, dict):
        assert action["farmer"] == ["PASS"]
    else:
        assert action["farmer"] == ["PLACE", "COW", 1]
    validate(obs, {}, action, policy)


def test_last_action_does_not_plant_without_time_to_water(policy):
    obs = economy(policy, hour=23)
    obs["private"]["seeds"] = {"STRAWBERRY": 1}
    assert policy["agent"](obs)["farmer"][0] != "PLANT"


def test_full_quadrant_can_admit_paid_land_with_a_feasible_batch(policy):
    obs = economy(policy, day=12)
    obs["farms"][0]["money"] = 40000
    obs["town"]["unlocked_shops"] = [
        "ICE_CREAM_SHOP",
        "SMOOTHIE_SHOP",
        "YARN_STORE",
        "FARMERS_MARKET",
    ]
    for y in range(5):
        for x in range(5):
            obs["farms"][0]["tiles"][y][x] = berry(planted=3)
    _, detail = policy["growth_investment"](obs, {}, policy["MARKET"], [["PASS"]], [], 40000)
    chosen = detail["chosen"]
    assert chosen and chosen["orders"][0] == ["BUY_LAND"]
    assert chosen["cost"] >= 1000 and chosen["value"] > 0
    assert chosen["min_cash"] >= 150 and chosen["peak_workers"] <= 17


def test_callback_preserves_observation_and_serializes(policy):
    obs = economy(policy)
    obs["farms"][0]["tiles"][4][3] = berry()
    original = deepcopy(obs)
    action = policy["agent"](obs)
    assert obs == original
    validate(obs, {}, action, policy)
    json.dumps(action)
