"""Isolated decisions and resource arithmetic; never import or advance the game."""

import json
import runpy
from copy import deepcopy
from pathlib import Path

import pytest

from scripts.make_growth_agent import build

ROOT = Path(__file__).resolve().parents[1]
RECORDS = json.loads((ROOT / "docs/examples/cycle-15-repair-observations.json").read_text())
CFG = RECORDS["configuration"]


@pytest.fixture(scope="module")
def policy(tmp_path_factory):
    path = tmp_path_factory.mktemp("growth") / "main.py"
    build(path)
    return runpy.run_path(str(path))["agent"].__globals__


def observation(day=10, hour=4):
    tiles = [[None if x < 5 and y < 5 else "LOCKED" for x in range(10)] for y in range(10)]
    farm = dict(
        tiles=tiles, farmer=[4, 4], hands=[], hires_today=0, money=3000, unlocked_quadrants=["NW"]
    )
    return dict(
        player=0,
        day=day,
        hour=hour,
        step=day * 24 + hour,
        farms=[farm, deepcopy(farm)],
        private=dict(shed={}, seeds={}, inventories=[{}]),
        market=dict(
            inventory={
                c: 10000
                for c in (
                    "WHEAT",
                    "CARROT",
                    "MELON",
                    "TOMATO",
                    "STRAWBERRY",
                    "MILK",
                    "WOOL",
                    "EGG",
                    "FERTILIZER",
                )
            }
        ),
        town=dict(unlocked_shops=[]),
    )


def crop(name="WHEAT", planted=8, **extra):
    return dict(
        kind="PLANT",
        crop=name,
        planted_day=planted,
        yield_units=1,
        watered_today=False,
        consecutive_unwatered=1,
        fertilized_until_day=-1,
        max_lifespan_step=-1,
        **extra,
    )


def animal(name="COW", placed=1):
    return dict(
        kind="COOP" if name == "GOOSE" else "PASTURE",
        animal=name,
        placed_day=placed,
        yield_units=0,
        fed_today=False,
        cared_today=False,
        fertilizer_available=True,
        pending_care_bonus=0,
        consecutive_unfed=1,
    )


def test_reproducible_independent_package(tmp_path):
    a, b = tmp_path / "a.py", tmp_path / "b.py"
    assert build(a) == build(b)
    assert a.read_bytes() == b.read_bytes()
    with pytest.raises(FileExistsError):
        build(a)
    scope = runpy.run_path(str(a))
    assert [k for k, v in scope.items() if callable(v)][-1] == "agent"


def test_known_demand_floor_and_expected_shop_growth(policy):
    obs = observation(day=9)
    obs["town"]["unlocked_shops"] = ["SMOOTHIE_SHOP", "PIZZA_SHOP", "PET_CAFE"]
    actual = policy["observed_demand"](obs, CFG)
    for d in range(9, 30):
        assert policy["growth_demand"](obs, CFG, d, False) == actual
        expected = policy["growth_demand"](obs, CFG, d, True)
        assert all(expected[c] >= actual[c] for c in actual)
    obs["town"]["unlocked_shops"] = ["PET_CAFE"] * 8
    assert policy["growth_demand"](obs, CFG, 29, True) == policy["observed_demand"](obs, CFG)


def test_animals_can_expand_beyond_old_twelve_locations(policy):
    obs = observation()
    farm = obs["farms"][0]
    farm["unlocked_quadrants"] = ["NW", "NE", "SW"]
    for y in range(10):
        for x in range(10):
            if x < 5 or y < 5:
                farm["tiles"][y][x] = None
    animals, fields = policy["growth_sites"](obs)
    assert len(animals) == 75
    assert len(fields) == 56
    # Every admitted coordinate is actually owned, including secondary locations.
    assert all(farm["tiles"][y][x] != "LOCKED" for x, y in animals)


def test_pending_animals_and_seeds_never_share_a_location(policy):
    obs = observation()
    obs["private"]["shed"] = {"COW": 8}
    obs["private"]["seeds"] = {"WHEAT": 8}
    assets = policy["growth_assets"](obs)
    assert len(assets) == 16
    assert len({t["site"] for t in assets}) == 16


def test_one_installation_does_not_require_one_worker_per_old_animal(policy):
    obs = observation()
    points = [(4, 4), (3, 4), (4, 3), (3, 3), (2, 4), (4, 2)]
    assets = [dict(animal="COW", placed_day=1, site=p, observed=10) for p in points]
    assets[-1].update(placed_day=11, install=True)
    model = policy["growth_workforce"](assets, 11, 29, 24, policy["shed_access"](obs))
    assert model["fits"]
    assert model["workers"] < len(assets)
    assert all(d <= 22 for d in model["durations"])
    assert sorted(p for route in model["routes"] for p in route) == sorted(points)


@pytest.mark.parametrize("name", ["WHEAT", "TOMATO", "STRAWBERRY"])
def test_last_daily_action_waters_endangered_plant_without_forcing_return(policy, name):
    obs = observation(day=10, hour=23)
    obs["farms"][0]["farmer"] = [0, 0]
    obs["farms"][0]["tiles"][0][0] = crop(name, 5)
    if name == "WHEAT":
        obs["farms"][0]["tiles"][0][0]["planted_day"] = 9
    assert policy["agent"](obs, CFG)["farmer"] == ["WATER"]


def test_last_daily_action_feeds_endangered_animal(policy):
    obs = observation(day=10, hour=23)
    obs["farms"][0]["farmer"] = [0, 0]
    obs["farms"][0]["tiles"][0][0] = animal()
    obs["private"]["inventories"] = [{"WHEAT": 1}]
    assert policy["agent"](obs, CFG)["farmer"] == ["FEED"]


def test_terminal_cargo_has_priority_and_sells_deposit(policy):
    obs = observation(day=29, hour=22)
    obs["private"]["inventories"] = [{"MILK": 12}]
    result = policy["agent"](obs, CFG)
    assert result["farmer"] == ["DROP"]
    assert ["SELL", "MILK", 12] in result["market"]
    assert not any(o[0].startswith("BUY") for o in result["market"])


@pytest.mark.parametrize("remaining,expected", [(1, "PASS"), (2, "HARVEST"), (3, "WATER")])
def test_terminal_water_harvest_deposit_chain(policy, remaining, expected):
    obs = observation(day=29, hour=23 - remaining)
    obs["farms"][0]["tiles"][4][4] = crop("WHEAT", 25)
    assert policy["agent"](obs, CFG)["farmer"] == [expected]


def test_overfull_shed_uses_partial_deposit_before_sale(policy):
    obs = observation(day=29, hour=22)
    obs["private"].update(shed={"WHEAT": 95}, inventories=[{"MILK": 4}, {"MILK": 4}])
    obs["farms"][0].update(hands=[[4, 4]], hires_today=1)
    result = policy["agent"](obs, CFG)
    assert result["farmer"] == ["DROP"]
    assert result["hands"] == [["PLACE", "MILK", 1]]
    assert ["SELL", "MILK", 5] in result["market"]


def test_care_stops_when_bonus_cannot_reach_a_remaining_production(policy):
    cow = animal(placed=1)
    assert policy["growth_care_due"](cow, 27, 29)
    assert not policy["growth_care_due"](cow, 28, 29)
    assert not policy["growth_care_due"](cow, 29, 29)


def test_care_before_production_banks_after_reset_even_with_full_bonus(policy):
    cow = animal(placed=1)
    cow["pending_care_bonus"] = 5
    assert policy["growth_care_due"](cow, 8, 29)
    assert not policy["growth_care_due"](cow, 7, 29)


def test_night_transfer_releases_return_travel_except_on_terminal_day(policy):
    node = (((0, 0), 1, ()),)
    access = ((4, 4), (4, 5), (5, 4), (5, 5))
    normal = policy["growth_routes"](node, access, 22)
    final = policy["growth_routes"](node, access, 22, True)
    assert final[1][0] - normal[1][0] == 9


def test_shed_pressure_deposits_collected_fertilizer(policy):
    obs = observation()
    obs["private"].update(shed={"WHEAT": 75}, inventories=[{"FERTILIZER": 10}])
    obs["farms"][0]["tiles"][4][4] = animal()
    obs["farms"][0]["tiles"][4][4]["consecutive_unfed"] = 0
    assert policy["agent"](obs, CFG)["farmer"] == ["DROP"]


def test_empty_structure_is_rebuilt_for_correct_species(policy):
    obs = observation()
    obs["farms"][0]["tiles"][4][4] = dict(kind="COOP", animal=None)
    obs["private"].update(shed={"WHEAT": 4}, inventories=[{"COW": 1, "WHEAT": 1}])
    result = policy["agent"](obs, CFG)
    assert result["farmer"] == ["DIG"]


def test_real_land_case_has_priced_expansion_alternatives(policy):
    obs = deepcopy(RECORDS["observations"]["336"])
    obs.update(hour=4, step=340)
    obs["farms"][0]["money"] = 30000
    market, report = policy["growth_investment"](
        obs, CFG, policy["MARKET"], [["PASS"] for _ in obs["private"]["inventories"]], [], 30000
    )
    land = [v for v in report["alternatives"] if v["orders"][0] == ["BUY_LAND"]]
    assert land
    assert all(v["cost"] >= 1000 for v in land)
    assert report["chosen"] and market
    assert report["chosen"]["value"] == max(
        v["value"] for v in report["alternatives"] if v["min_cash"] >= 150
    )


def test_no_cash_no_speculative_purchases(policy):
    obs = observation()
    obs["farms"][0]["money"] = 100
    _, detail = policy["growth_investment"](obs, CFG, policy["MARKET"], [["PASS"]], [], 100)
    assert detail["chosen"] is None


def test_isolated_decision_preserves_observation(policy):
    obs = deepcopy(RECORDS["observations"]["384"])
    before = deepcopy(obs)
    action = policy["agent"](obs, CFG)
    assert obs == before
    assert len(action["hands"]) == len(obs["farms"][obs["player"]]["hands"])
    assert len(action["market"]) <= CFG["maxMarketOrdersPerTurn"]
    json.dumps(action)
