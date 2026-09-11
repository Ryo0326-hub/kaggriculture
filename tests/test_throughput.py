"""Bounded accounting/decision tests only: no matches, episodes, or engine stepping."""

import json
import runpy
from copy import deepcopy

import pytest

from scripts.make_throughput_agent import build


@pytest.fixture(scope="module")
def policy(tmp_path_factory):
    path = tmp_path_factory.mktemp("throughput") / "main.py"
    build(path)
    return runpy.run_path(str(path))


def observation(day=0, hour=0):
    farm = {
        "money": 3000,
        "farmer": [4, 4],
        "hands": [],
        "hires_today": 0,
        "unlocked_quadrants": ["NW"],
        "tiles": [[None if x < 5 and y < 5 else "LOCKED" for x in range(10)] for y in range(10)],
    }
    return {
        "player": 0,
        "step": day * 24 + hour,
        "day": day,
        "hour": hour,
        "farms": [farm, deepcopy(farm)],
        "town": {"unlocked_shops": []},
        "market": {
            "inventory": {
                c: 10000
                for c in (
                    "WHEAT",
                    "CARROT",
                    "TOMATO",
                    "STRAWBERRY",
                    "MELON",
                    "EGG",
                    "MILK",
                    "WOOL",
                    "FERTILIZER",
                )
            }
        },
        "private": {"shed": {}, "inventories": [{}], "seeds": {}},
    }


def plant(crop, planted=0, units=1, watered=False, fert=-1):
    return {
        "kind": "PLANT",
        "crop": crop,
        "planted_day": planted,
        "yield_units": units,
        "watered_today": watered,
        "consecutive_unwatered": 1,
        "fertilized_until_day": fert,
        "max_lifespan_step": -1,
    }


def test_opening_preserves_joint_portfolio_and_adds_bounded_wheat(policy):
    obs = observation()
    copy = deepcopy(obs)
    action = policy["agent"](obs)
    assert action["market"] == [
        ["BUY_SEED", "MELON", 8],
        ["BUY_ANIMAL", "COW", 2],
        ["BUY_ANIMAL", "SHEEP", 2],
        ["BUY_SEED", "WHEAT", 4],
    ]
    assert obs == copy  # forecasts must not mutate the actual observation
    assert len(action["market"]) <= 10
    json.dumps(action)


def test_staged_geometry_uses_starting_land_and_preserves_installation_space(policy):
    obs = observation()
    animals, crops = policy["farm_sites"](obs)
    assert len(animals) == 5 and len(crops) == 20
    future_animals, future_crops = policy["farm_sites"](obs, True)
    assert len(future_animals) == 12 and len(future_crops) == 38
    assert not set(future_animals) & set(future_crops)
    assert all(obs["farms"][0]["tiles"][y][x] != "LOCKED" for x, y in animals + crops)


def test_five_unit_wheat_releases_plot_at_age_three_only(policy):
    job = policy["crop_job"]
    assert job(plant("WHEAT", units=5, watered=True), 3, 29)[0] == "HARVEST"
    assert job(plant("WHEAT", units=3, watered=True), 3, 29) is None
    assert job(plant("WHEAT", units=5, watered=True), 2, 29) is None
    assert job(plant("WHEAT", planted=25, units=5, watered=True), 28, 29) is None
    col = policy["crop_column"]("WHEAT", 0, 29, tile=plant("WHEAT", units=5), today=3)
    assert col["outputs"] == {3: 5}
    growing = plant("WHEAT", units=3, watered=True, fert=4)
    col = policy["crop_column"]("WHEAT", 0, 29, tile=growing, today=2)
    assert col["outputs"] == {3: 5}


def test_tomato_dates_water_harvest_and_exhaustion(policy):
    assert policy["crop_column"]("TOMATO", 1, 29)["outputs"] == {9: 1, 10: 1, 11: 1, 12: 1}
    assert policy["crop_column"]("TOMATO", 23, 29) is None
    assert policy["crop_job"](plant("TOMATO", units=0), 7, 29)[0] == "WATER"
    assert policy["crop_job"](plant("TOMATO", units=4), 8, 29)[0] == "HARVEST"
    assert policy["crop_job"](plant("TOMATO", units=0, watered=True), 11, 29)[0] == "DIG"


def test_tomato_fertilizer_after_water_and_saturation(policy):
    obs = observation(7, 8)
    obs["market"]["inventory"]["TOMATO"] = 9300
    tile = plant("TOMATO", units=0, watered=True)
    assert policy["timing_fertilizer_value"](tile, obs, {}, policy["MARKET"]) > 0
    tile["yield_units"] = 3
    assert policy["timing_fertilizer_value"](tile, obs, {}, policy["MARKET"]) == 0
    obs["farms"][0]["tiles"][4][0] = plant("TOMATO", units=0)
    obs["farms"][0]["farmer"] = [0, 4]
    future = policy["planning_snapshot"](obs, {}, [["WATER"]], [], policy["MARKET"])
    assert future["farms"][0]["tiles"][4][0]["yield_units"] == 0


def test_producing_animals_share_bounded_routes(policy):
    sites = ((4, 4), (3, 4), (4, 3))
    routes, durations, feasible = policy["route_cover"](
        sites, (4, 4, 4), ((4, 4), (5, 4), (4, 5), (5, 5)), 21, (0, 1, 2)
    )
    assert feasible and len(routes) < 3
    assert sorted(p for route in routes for p in route) == sorted(sites)
    assert max(durations) <= 21


def test_goose_flows_charge_feed_and_credit_eggs_and_fertilizer_once(policy):
    tile = {"animal": "GOOSE", "placed_day": 1, "yield_units": 0, "pending_care_bonus": 0}
    flows = policy["throughput_flows"]([tile], 0, 8)
    assert flows[0]["WHEAT"] == 0
    assert sum(row["WHEAT"] for row in flows.values()) == -7
    assert sum(row["EGG"] for row in flows.values()) > 0
    assert sum(row["FERTILIZER"] for row in flows.values()) == 7


def test_demand_menu_includes_goose_and_excludes_unsupported_tomato_carrot(policy):
    obs = observation(5, 3)
    obs["farms"][0]["money"] = 100000
    _, detail = policy["throughput_investment"](obs, {}, policy["MARKET"], [["PASS"]], [])
    types = {tuple(r["orders"][-1][:2]) for r in detail["alternatives"]}
    assert ("BUY_ANIMAL", "GOOSE") in types
    assert ("BUY_SEED", "CARROT") not in types and ("BUY_SEED", "TOMATO") not in types
    obs["town"]["unlocked_shops"] = ["PET_CAFE", "PIZZA_SHOP"]
    _, detail = policy["throughput_investment"](obs, {}, policy["MARKET"], [["PASS"]], [])
    types = {tuple(r["orders"][-1][:2]) for r in detail["alternatives"]}
    assert ("BUY_SEED", "CARROT") in types and ("BUY_SEED", "TOMATO") in types


@pytest.mark.parametrize("condition", ["poor", "queued", "late", "full_orders"])
def test_investment_rejects_unfunded_queued_late_or_full_orders(policy, condition):
    obs = observation(5, 3)
    market = []
    if condition == "poor":
        obs["farms"][0]["money"] = 100
    if condition == "queued":
        obs["private"]["seeds"]["WHEAT"] = 1
    if condition == "late":
        obs.update(day=29, step=699)
    if condition == "full_orders":
        market = [["SELL", "WHEAT", 1]] * 10
    orders, report = policy["throughput_investment"](
        obs, {}, policy["MARKET"], [["PASS"]], market[:]
    )
    assert orders == market and report["chosen"] is None


def test_terminal_sale_and_delivery_still_use_inherited_path(policy):
    obs = observation(29, 22)
    obs["private"]["inventories"] = [{"MILK": 3}]
    action = policy["agent"](obs)
    assert action["farmer"] == ["DROP"]
    assert ["SELL", "MILK", 3] in action["market"]
    assert not any(o[0].startswith("BUY") for o in action["market"])


def test_accounting_saturation_reduces_additional_production_value(policy):
    obs = observation(5, 3)
    addition = [plant("STRAWBERRY", planted=6, units=0)]
    extra = policy["throughput_flows"](addition, 5, 29)
    baseline = [policy["throughput_flows"]([], 5, 29) for _ in range(2)]
    kwargs = (obs, {}, policy["MARKET"], baseline, extra, addition, 100, [])
    good = policy["throughput_value"](*kwargs)["value"]
    obs["market"]["inventory"]["STRAWBERRY"] = 10500
    bad = policy["throughput_value"](*kwargs)["value"]
    assert bad < good and bad < 0


def test_expansion_pays_for_land_that_the_ordered_batch_will_use(policy):
    obs = observation(6, 4)
    obs["farms"][0]["money"] = 100000
    _, fields = policy["farm_sites"](obs)
    for x, y in fields:
        obs["farms"][0]["tiles"][y][x] = plant("WHEAT", planted=5)
    _, report = policy["throughput_investment"](obs, {}, policy["MARKET"], [["PASS"]], [])
    land = [r for r in report["alternatives"] if r["orders"][0] == ["BUY_LAND"]]
    assert land
    for r in land:
        _, crop, count = r["orders"][1]
        assert r["cost"] == 1000 + policy["CROPS"][crop]["seed"] * count


def test_dense_portfolio_cannot_hide_extra_fibonacci_wages(policy):
    obs = observation(6, 3)
    assets = [{"animal": "COW", "placed_day": 0, "yield_units": 0}] * 12
    assets += [plant("STRAWBERRY", planted=6, units=0)] * 40
    additions = [plant("STRAWBERRY", planted=7, units=0)] * 12
    base = [policy["throughput_flows"](assets, 6, 29), policy["throughput_flows"]([], 6, 29)]
    extra = policy["throughput_flows"](additions, 6, 29)
    result = policy["throughput_value"](
        obs, {}, policy["MARKET"], base, extra, additions, 1200, assets
    )
    assert result["added_wages"] > 0
    assert not result["capacity_estimate_fits"]
