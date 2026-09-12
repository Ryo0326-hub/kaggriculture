"""Forecast arithmetic and individual authored decisions; no engine or local game."""

import runpy
from copy import deepcopy
from hashlib import sha256

import pytest
from test_growth import animal, crop, observation
from test_majkel import decide

from scripts.make_majkel_agent import source as parent_source
from scripts.make_resilience_agent import PARENT_HASH, build


@pytest.fixture(scope="module")
def policy(tmp_path_factory):
    path = tmp_path_factory.mktemp("resilience") / "main.py"
    build(path)
    return runpy.run_path(str(path))["agent"].__globals__


def supply(policy, obs, item, days):
    return policy["committed_supply"](obs, policy["context"](obs, {}), item, days)


def test_parent_frozen_and_package_reproducible(tmp_path):
    assert sha256(parent_source().encode()).hexdigest() == PARENT_HASH
    a, b = tmp_path / "a.py", tmp_path / "b.py"
    assert build(a) == build(b)
    assert a.read_bytes() == b.read_bytes()
    with pytest.raises(FileExistsError):
        build(a)
    text = a.read_text()
    assert "108295517" not in text and "kaggle_environments" not in text
    scope = runpy.run_path(str(a))
    assert [k for k, v in scope.items() if callable(v)][-1] == "agent"


def test_repeaters_use_remaining_event_dates_and_include_held_crop(policy):
    o = observation(10)
    o["farms"][1]["tiles"][0][0] = crop("STRAWBERRY", 0)
    # First production has happened: one held plus events on days 12,14,16.
    assert supply(policy, o, "STRAWBERRY", 1) == 1
    assert supply(policy, o, "STRAWBERRY", 2) == pytest.approx(2.7)
    assert supply(policy, o, "STRAWBERRY", 19) == pytest.approx(6.1)


def test_exhausted_repeater_contributes_only_existing_output(policy):
    o = observation(20)
    o["farms"][1]["tiles"][0][0] = crop("STRAWBERRY", 0)
    assert supply(policy, o, "STRAWBERRY", 8) == 1


def test_single_crop_not_replanted_in_forecast(policy):
    o = observation(2)
    o["farms"][1]["tiles"][0][0] = crop("MELON", 0)
    assert supply(policy, o, "MELON", 7) == 0
    assert supply(policy, o, "MELON", 8) == 6
    assert supply(policy, o, "MELON", 27) == 6


def test_queued_seeds_have_installation_delay_and_known_stock_counted_once(policy):
    o = observation(4)
    o["private"].update(
        seeds={"STRAWBERRY": 2}, shed={"STRAWBERRY": 3}, inventories=[{"STRAWBERRY": 2}]
    )
    assert supply(policy, o, "STRAWBERRY", 10) == 5
    assert supply(policy, o, "STRAWBERRY", 11) == pytest.approx(8.4)


def test_feed_use_offsets_wheat_supply_but_already_fed_is_not_charged_twice(policy):
    o = observation(10)
    o["farms"][1]["tiles"][0][0] = animal("COW", 0)
    o["private"]["shed"] = {"WHEAT": 3}
    assert supply(policy, o, "WHEAT", 4) == -1
    o["farms"][1]["tiles"][0][0]["fed_today"] = True
    assert supply(policy, o, "WHEAT", 4) == 0


def test_animal_held_output_and_care_bank_respect_next_production_date(policy):
    o = observation(7)
    t = animal("COW", 0)
    t.update(yield_units=2, pending_care_bonus=5, cared_today=True)
    o["farms"][1]["tiles"][0][0] = t
    assert supply(policy, o, "MILK", 1) == 8
    assert supply(policy, o, "MILK", 3) == 11


def test_late_queue_cannot_produce_past_terminal_date(policy):
    o = observation(25)
    o["private"].update(seeds={"STRAWBERRY": 4}, shed={"COW": 2})
    assert supply(policy, o, "STRAWBERRY", 20) == 0
    assert supply(policy, o, "MILK", 20) == 0
    assert supply(policy, o, "WHEAT", 20) == 0


def test_predicted_price_floor_not_subsidized_by_todays_high_quote(policy):
    o = observation(10)
    for y in range(5):
        for x in range(5):
            o["farms"][1]["tiles"][y][x] = crop("STRAWBERRY", 0)
    ctx = policy["context"](o, {})
    rates = policy["production_rates"](o, ctx)
    assert ctx["prices"]["STRAWBERRY"] == 120
    assert policy["expected_price"](o, ctx, "STRAWBERRY", 6, rates) == 1
    assert policy["crop_value"](o, ctx, "STRAWBERRY", rates) < 0


def test_visible_buyer_demand_changes_forecast_without_future_shops(policy):
    o = observation(10)
    for x in range(5):
        o["farms"][1]["tiles"][0][x] = crop("STRAWBERRY", 0)
    ctx = policy["context"](o, {})
    low = policy["expected_price"](o, ctx, "STRAWBERRY", 6, {})
    o["town"]["unlocked_shops"] = ["ICE_CREAM_SHOP"] * 3
    high = policy["expected_price"](o, policy["context"](o, {}), "STRAWBERRY", 6, {})
    assert high > low


def test_late_survival_preempts_routine_committed_target(policy):
    o = observation(10, 18)
    o["farms"][0]["tiles"][4][3] = crop("STRAWBERRY", 5)
    routine = crop("WHEAT", 9)
    routine["consecutive_unwatered"] = 0
    o["farms"][0]["tiles"][3][4] = routine
    policy["_MEMORY"].clear()
    policy["_MEMORY"].update(token=(0, 10), step=257, targets={0: (4, 3)})
    assert decide(policy, o)["farmer"] == ["WEST"]
    # Independently authored later observation: water before fertilizer or routine work.
    n = deepcopy(o)
    n.update(hour=19, step=259)
    n["farms"][0]["farmer"] = [3, 4]
    n["private"]["inventories"] = [{"FERTILIZER": 1}]
    assert decide(policy, n)["farmer"] == ["WATER"]


def test_rescue_retains_exclusive_assignments_and_available_feed(policy):
    o = observation(10, 22)
    o["farms"][0].update(hands=[[4, 4]], hires_today=1)
    o["farms"][0]["tiles"][4][4] = animal()
    o["private"]["inventories"] = [{"WHEAT": 1}, {"WHEAT": 1}]
    policy["_MEMORY"].clear()
    a = decide(policy, o)
    assert [a["farmer"], *a["hands"]].count(["FEED"]) == 1
