"""Cycle 19 bounded decisions and authored continuity fixtures; no game engine."""

import json
import runpy
from copy import deepcopy

import pytest
from test_growth import animal, crop, observation

from scripts.check_growth_agent import validate
from scripts.make_calendar_agent import build as build_calendar
from scripts.make_majkel_agent import build
from scripts.make_resilience_agent import build as build_resilience


@pytest.fixture(
    scope="module",
    params=[build, build_resilience, build_calendar],
    ids=["cycle19", "cycle20", "cycle21"],
)
def policy(tmp_path_factory, request):
    p = tmp_path_factory.mktemp("compact-service") / "main.py"
    request.param(p)
    return runpy.run_path(str(p))["agent"].__globals__


def decide(policy, obs, cfg=None):
    cfg = cfg or {}
    old = deepcopy(obs)
    action = policy["agent"](obs, cfg)
    assert obs == old
    validate(obs, cfg, action, policy)
    return action


def direct(policy, obs):
    ctx = policy["context"](obs, {})
    jobs = policy["make_jobs"](obs, ctx)
    return policy["dispatch"](obs, ctx, jobs)


def test_reproducible_single_file_and_no_overwrite(tmp_path):
    a, b = tmp_path / "a.py", tmp_path / "b.py"
    assert build(a) == build(b)
    assert a.read_bytes() == b.read_bytes()
    with pytest.raises(FileExistsError):
        build(a)
    scope = runpy.run_path(str(a))
    assert [k for k, v in scope.items() if callable(v)][-1] == "agent"
    assert "kaggle_environments" not in a.read_text()
    assert "108300532" not in a.read_text() and "108305451" not in a.read_text()


def test_opening_funds_animals_feed_workers_and_seeds(policy):
    o = observation(0, 0)
    policy["_MEMORY"].clear()
    a = decide(policy, o)
    assert ["BUY_ANIMAL", "COW", 2] in a["market"]
    assert ["BUY_ANIMAL", "SHEEP", 3] in a["market"]
    assert sum(z[0] == "HIRE" for z in a["market"]) == 4
    assert ["BUY_SEED", "WHEAT", 10] in a["market"]
    assert ["BUY_SEED", "MELON", 2] in a["market"]
    assert ["BUY_PRODUCT", "WHEAT", 5] in a["market"]


@pytest.mark.parametrize("name", ["WHEAT", "CARROT", "MELON", "STRAWBERRY", "TOMATO"])
def test_last_action_survival_water(policy, name):
    o = observation(10, 23)
    o["farms"][0]["tiles"][4][4] = crop(name, 9)
    o["private"]["inventories"] = [{"FERTILIZER": 1}]
    policy["_MEMORY"].clear()
    assert decide(policy, o)["farmer"] == ["WATER"]


def test_last_action_feeds_at_risk(policy):
    o = observation(10, 23)
    o["farms"][0]["tiles"][4][4] = animal()
    o["private"]["inventories"] = [{"WHEAT": 1}]
    policy["_MEMORY"].clear()
    assert decide(policy, o)["farmer"] == ["FEED"]


def test_two_workers_do_not_water_same_tile(policy):
    o = observation()
    o["farms"][0].update(hands=[[4, 4]], hires_today=1)
    o["private"]["inventories"] = [{}, {}]
    o["farms"][0]["tiles"][4][4] = crop("STRAWBERRY", 1)
    policy["_MEMORY"].clear()
    a = decide(policy, o)
    assert [a["farmer"], *a["hands"]].count(["WATER"]) == 1


def test_two_workers_cannot_consume_one_seed_twice(policy):
    o = observation()
    o["farms"][0].update(hands=[[4, 4]], hires_today=1)
    o["private"].update(inventories=[{}, {}], seeds={"STRAWBERRY": 1})
    policy["_MEMORY"].clear()
    a = decide(policy, o)
    assert sum(op == ["PLANT", "STRAWBERRY"] for op in [a["farmer"], *a["hands"]]) <= 1


def test_no_newborn_without_time_to_water(policy):
    o = observation(10, 23)
    o["private"]["seeds"] = {"WHEAT": 1}
    policy["_MEMORY"].clear()
    a = decide(policy, o)
    assert a["farmer"][0] != "PLANT"


def test_no_planting_stale_seed(policy):
    o = observation(25, 4)
    o["private"]["seeds"] = {"STRAWBERRY": 3, "WHEAT": 1}
    pending = policy["pending_assets"](o, policy["context"](o, {}))
    assert [t["crop"] for t in pending if t.get("plant")] == ["WHEAT"]


def test_pending_seeds_do_not_veto_land_or_livestock(policy):
    o = observation(12, 4)
    o["farms"][0]["money"] = 30000
    o["town"]["unlocked_shops"] = ["ICE_CREAM_SHOP", "ICE_CREAM_SHOP"]
    o["private"]["seeds"] = {"STRAWBERRY": 3}
    for y in range(3):
        for x in range(5):
            o["farms"][0]["tiles"][y][x] = crop("STRAWBERRY", 3)
    policy["_MEMORY"].clear()
    a = decide(policy, o)
    assert ["BUY_LAND"] in a["market"]
    assert any(z[0] == "BUY_ANIMAL" for z in a["market"])


def test_committed_target_survives_new_nearer_work(policy):
    # Authored observations; no returned action is applied to a simulator.
    o = observation(10, 4)
    o["farms"][0]["tiles"][1][4] = crop("STRAWBERRY", 1)
    policy["_MEMORY"].clear()
    assert direct(policy, o)[0][0] == ["NORTH"]
    next_obs = deepcopy(o)
    next_obs.update(hour=5, step=245)
    next_obs["farms"][0]["farmer"] = [4, 3]
    next_obs["farms"][0]["tiles"][4][4] = crop("STRAWBERRY", 1)
    assert direct(policy, next_obs)[0][0] == ["NORTH"]
    assert policy["_MEMORY"]["targets"][0] == (4, 1)


def test_target_waits_through_input_pickup(policy):
    o = observation(10, 4)
    o["farms"][0]["farmer"] = [4, 2]
    o["farms"][0]["tiles"][1][4] = animal()
    o["private"]["shed"] = {"WHEAT": 2}
    policy["_MEMORY"].clear()
    first = direct(policy, o)
    assert first[0][0] == ["SOUTH"]
    n = deepcopy(o)
    n.update(hour=5, step=245)
    n["farms"][0]["farmer"] = [4, 3]
    assert direct(policy, n)[0][0] == ["SOUTH"]
    n = deepcopy(o)
    n.update(hour=6, step=246)
    n["farms"][0]["farmer"] = [4, 4]
    assert direct(policy, n)[0][0][0] == "PICKUP"
    assert policy["_MEMORY"]["targets"][0] == (4, 1)


def test_cold_start_fallback_targets_are_legal(policy):
    o = observation()
    o["farms"][0]["tiles"][1][4] = animal()
    o["private"]["shed"] = {"WHEAT": 2}
    policy["_MEMORY"].clear()
    a = decide(policy, o)
    policy["_MEMORY"].clear()
    assert decide(policy, o) == a
    del o["step"]
    policy["_MEMORY"].clear()
    assert decide(policy, o) == a


def test_service_flags_do_not_move_geographic_ownership(policy):
    o = observation()
    o["farms"][0]["tiles"][3][3] = crop()
    before = policy["ownership"](o, 5)
    o["farms"][0]["tiles"][3][3]["watered_today"] = True
    o["farms"][0]["tiles"][3][3]["yield_units"] = 6
    assert policy["ownership"](o, 5) == before


def test_final_delivery_precedes_unreachable_harvest(policy):
    o = observation(29, 21)
    o["farms"][0]["farmer"] = [3, 4]
    o["private"]["inventories"] = [{"MILK": 4}]
    o["farms"][0]["tiles"][0][0] = animal()
    o["farms"][0]["tiles"][0][0]["yield_units"] = 6
    policy["_MEMORY"].clear()
    assert decide(policy, o)["farmer"] == ["EAST"]
    n = observation(29, 22)
    n["private"]["inventories"] = [{"MILK": 4}]
    a = decide(policy, n)
    assert a["farmer"] == ["PLACE", "MILK", 4]
    assert ["SELL", "MILK", 4] in a["market"]


def test_full_shed_does_not_destroy_carried_goods(policy):
    o = observation(20, 10)
    o["private"].update(shed={"WHEAT": 100}, inventories=[{"MILK": 6}])
    policy["_MEMORY"].clear()
    a = decide(policy, o)
    assert a["farmer"][0] not in ("DROP", "PLACE")
    assert any(z[0] == "SELL" and z[1] == "WHEAT" for z in a["market"])


def test_projection_reserves_night_harvest(policy):
    o = observation(20, 23)
    o["private"]["shed"] = {"FERTILIZER": 95}
    o["farms"][0]["tiles"][4][4] = animal()
    o["farms"][0]["tiles"][4][4].update(
        fed_today=True, cared_today=True, yield_units=6, fertilizer_available=False
    )
    policy["_MEMORY"].clear()
    a = decide(policy, o)
    assert a["farmer"] == ["HARVEST"]
    assert sum(z[2] for z in a["market"] if z[0] == "SELL") >= 1
    stock_after = 95 - sum(z[2] for z in a["market"] if z[0] == "SELL")
    stock_after += sum(z[2] for z in a["market"] if z[0] in ("BUY_PRODUCT", "BUY_ANIMAL"))
    assert stock_after + 6 <= 100


def test_own_route_carried_feed_is_not_bought_again(policy):
    o = observation(10, 4)
    o["farms"][0]["tiles"][1][4] = animal()
    o["private"].update(shed={"WHEAT": 1}, inventories=[{"WHEAT": 1}])
    policy["_MEMORY"].clear()
    a = decide(policy, o)
    assert not any(z[0] == "BUY_PRODUCT" and z[1] == "WHEAT" for z in a["market"])


def test_retire_animals_only_after_last_possible_production(policy):
    t = animal("SHEEP", 0)
    assert policy["future_animal"](t, 26, 29) == 27
    assert policy["future_animal"](t, 27, 29) is None
    assert policy["future_animal"](t, 26, 29, 2) is None


def test_negative_fertilizer_margin_does_not_hold_up_watering(policy):
    o = observation(2, 4)
    o["farms"][0]["tiles"][4][4] = crop("WHEAT", 0)
    o["private"]["inventories"] = [{"FERTILIZER": 1}]
    policy["_MEMORY"].clear()
    assert decide(policy, o)["farmer"] == ["WATER"]


def test_watered_strawberry_can_receive_night_bonus(policy):
    o = observation(10, 23)
    t = crop("STRAWBERRY", 1)
    t.update(watered_today=True, yield_units=0)
    o["farms"][0]["tiles"][4][4] = t
    o["private"]["inventories"] = [{"FERTILIZER": 1}]
    policy["_MEMORY"].clear()
    assert decide(policy, o)["farmer"] == ["FERTILIZE"]


def test_bakery_demand_admits_geese_but_caps_overproduction(policy):
    o = observation(7, 4)
    o["farms"][0]["money"] = 20000
    o["town"]["unlocked_shops"] = ["BAKERY"]
    policy["_MEMORY"].clear()
    a = decide(policy, o)
    assert ["BUY_ANIMAL", "GOOSE", 1] in a["market"]
    for x in range(4):
        o["farms"][0]["tiles"][4][x] = animal("GOOSE", 6)
    policy["_MEMORY"].clear()
    a = decide(policy, o)
    assert not any(z[:2] == ["BUY_ANIMAL", "GOOSE"] for z in a["market"])


def test_terminal_skips_water_if_only_harvest_can_be_delivered(policy):
    o = observation(29, 21)
    o["farms"][0]["tiles"][4][4] = crop("WHEAT", 27)
    policy["_MEMORY"].clear()
    a = decide(policy, o)
    assert a["farmer"] == ["HARVEST"]


def test_animal_installs_never_use_ambiguous_product_deposit(policy):
    o = observation(10, 4)
    o["private"]["inventories"] = [{"COW": 1, "MILK": 6, "WHEAT": 1}]
    o["farms"][0]["tiles"][4][4] = {"kind": "PASTURE"}
    policy["_MEMORY"].clear()
    a = decide(policy, o)
    if a["farmer"][0] == "PLACE" and a["farmer"][1] == "COW":
        assert a["farmer"] == ["PLACE", "COW"]
    json.dumps(a)


def test_plain_wheat_remains_viable_when_fertilizer_is_expensive(policy):
    o = observation(5, 4)
    ctx = policy["context"](o, {})
    assert policy["crop_value"](o, ctx, "WHEAT", policy["production_rates"](o, ctx)) > 0


def test_harvest_does_not_exceed_total_possible_night_storage(policy):
    o = observation(15, 23)
    o["farms"][0]["farmer"] = [0, 0]
    o["farms"][0]["tiles"][0][0] = animal()
    o["farms"][0]["tiles"][0][0].update(
        yield_units=6, fed_today=True, cared_today=True, fertilizer_available=False
    )
    o["private"]["inventories"] = [{"MILK": 99}]
    policy["_MEMORY"].clear()
    assert decide(policy, o)["farmer"] == ["PASS"]


def test_deposit_and_pickup_ledger_uses_engine_worker_order(policy):
    o = observation(10, 4)
    o["farms"][0].update(hands=[[4, 4]], hires_today=1, money=100)
    o["private"].update(shed={"WHEAT": 1}, inventories=[{"MILK": 4}, {}])
    o["farms"][0]["tiles"][3][4] = animal()
    policy["_MEMORY"].clear()
    decide(policy, o)  # The independent validator processes farmer before hands.


def test_stale_uninstalled_animal_does_not_block_useful_worker(policy):
    o = observation(25, 4)
    o["private"]["inventories"] = [{"COW": 1}]
    o["farms"][0]["tiles"][4][4] = crop("WHEAT", 23)
    policy["_MEMORY"].clear()
    assert not any(t.get("install") for t in policy["pending_assets"](o, policy["context"](o, {})))
    assert decide(policy, o)["farmer"][0] in ("WATER", "HARVEST")


def test_unused_late_animal_pads_can_receive_crops(policy):
    o = observation(15, 4)
    pads, fields = policy["geometry"](o)
    for x, y in fields:
        o["farms"][0]["tiles"][y][x] = crop("STRAWBERRY", 2)
    o["private"]["seeds"] = {"WHEAT": 1}
    pending = policy["pending_assets"](o, policy["context"](o, {}))
    assert all(t["site"] in pads for t in pending if t.get("plant"))
    assert any(t.get("plant") for t in pending)


def test_feed_is_funded_before_expensive_hires(policy):
    o = observation(10, 0)
    o["farms"][0]["money"] = 50
    o["farms"][0]["tiles"][3][4] = animal()
    policy["_MEMORY"].clear()
    a = decide(policy, o)
    feed_index = next(i for i, z in enumerate(a["market"]) if z[:2] == ["BUY_PRODUCT", "WHEAT"])
    hire_index = next(i for i, z in enumerate(a["market"]) if z[0] == "HIRE")
    assert feed_index < hire_index
    assert sum(z[0] == "HIRE" for z in a["market"]) >= 4
