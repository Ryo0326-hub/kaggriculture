"""Cycle 21 calendars and authored deadline decisions. Never advances a game."""

import json
import runpy
from copy import deepcopy
from hashlib import sha256
from pathlib import Path

import pytest
from test_growth import animal, crop, observation
from test_majkel import decide, direct

from scripts.make_calendar_agent import PARENT_HASH, build
from scripts.make_resilience_agent import source as parent_source


@pytest.fixture(scope="module")
def policy(tmp_path_factory):
    path = tmp_path_factory.mktemp("calendar") / "main.py"
    build(path)
    return runpy.run_path(str(path))["agent"].__globals__


def jobs(policy, obs):
    return policy["make_jobs"](obs, policy["context"](obs, {}))


def test_frozen_parent_and_reproducible_package(tmp_path):
    assert sha256(parent_source().encode()).hexdigest() == PARENT_HASH
    a, b = tmp_path / "a.py", tmp_path / "b.py"
    assert build(a) == build(b)
    with pytest.raises(FileExistsError):
        build(a)
    scope = runpy.run_path(str(a))
    assert [k for k, v in scope.items() if callable(v)][-1] == "agent"
    assert "kaggle_environments" not in a.read_text()
    assert "108335136" not in a.read_text()


@pytest.mark.parametrize("age", [1, 3, 5, 7, 10, 12, 14])
def test_skip_safe_strawberry_watering_between_production_dates(policy, age):
    o = observation(age, 4)
    t = crop("STRAWBERRY", 0)
    t.update(consecutive_unwatered=0, yield_units=0)
    o["farms"][0]["tiles"][4][4] = t
    assert ["WATER"] not in jobs(policy, o).get((4, 4), {}).get("ops", [])


@pytest.mark.parametrize("age", [9, 11, 13, 15])
def test_water_before_each_strawberry_production_night(policy, age):
    o = observation(age, 4)
    t = crop("STRAWBERRY", 0)
    t.update(consecutive_unwatered=0, yield_units=0)
    o["farms"][0]["tiles"][4][4] = t
    assert ["WATER"] in jobs(policy, o)[(4, 4)]["ops"]


@pytest.mark.parametrize("name,age", [("STRAWBERRY", 1), ("TOMATO", 5), ("MELON", 3)])
def test_observed_drought_overrides_calendar_skip(policy, name, age):
    o = observation(age)
    o["farms"][0]["tiles"][4][4] = crop(name, 0)
    assert jobs(policy, o)[(4, 4)]["ops"][0] == ["WATER"]


def test_tomato_daily_production_and_wheat_growth_water_are_retained(policy):
    for name, age in [("TOMATO", 7), ("TOMATO", 8), ("TOMATO", 10), ("WHEAT", 2), ("MELON", 6)]:
        o = observation(age)
        t = crop(name, 0)
        t["consecutive_unwatered"] = 0
        o["farms"][0]["tiles"][4][4] = t
        assert ["WATER"] in jobs(policy, o)[(4, 4)]["ops"]


def test_no_water_after_final_repeater_output(policy):
    o = observation(16)
    o["farms"][0]["tiles"][4][4] = crop("STRAWBERRY", 0)
    assert ["WATER"] not in jobs(policy, o)[(4, 4)]["ops"]
    assert ["HARVEST"] in jobs(policy, o)[(4, 4)]["ops"]


def test_water_then_fertilize_remains_available_on_bonus_night(policy):
    o = observation(9, 22)
    t = crop("STRAWBERRY", 0)
    t["yield_units"] = 0
    o["farms"][0]["tiles"][4][4] = t
    o["private"]["inventories"] = [{"FERTILIZER": 1}]
    policy["_MEMORY"].clear()
    assert decide(policy, o)["farmer"] == ["WATER"]
    # Independent observation authored with water already complete, not an engine step.
    later = deepcopy(o)
    later.update(hour=23, step=239)
    later["farms"][0]["tiles"][4][4]["watered_today"] = True
    assert decide(policy, later)["farmer"] == ["FERTILIZE"]


def test_fertilizer_detour_cannot_delay_last_feasible_survival_visit(policy):
    o = observation(9, 21)
    o["farms"][0]["farmer"] = [2, 1]
    o["farms"][0]["tiles"][0][2] = crop("STRAWBERRY", 0)
    o["private"]["shed"] = {"FERTILIZER": 3}
    policy["_MEMORY"].clear()
    assert decide(policy, o)["farmer"] == ["NORTH"]


def test_two_endangered_crops_receive_distinct_worker_assignments(policy):
    o = observation(13, 20)
    o["farms"][0].update(farmer=[2, 2], hands=[[3, 2]], hires_today=1)
    o["private"]["inventories"] = [{}, {}]
    for x in [2, 3]:
        t = crop("MELON", 2)
        t.update(yield_units=5, max_lifespan_step=360)
        o["farms"][0]["tiles"][0][x] = t
    # Low-value nearby growth jobs must not preempt the endangered distant fruit.
    for x in [2, 3]:
        t = crop("WHEAT", 11)
        t["consecutive_unwatered"] = 0
        o["farms"][0]["tiles"][2][x] = t
    policy["_MEMORY"].clear()
    commands, _, _, assignment = direct(policy, o)
    assert set(assignment.values()) == {(2, 0), (3, 0)}
    assert commands == [["NORTH"], ["NORTH"]]
    decide(policy, o)


def test_existing_routine_commitment_does_not_hide_expiring_harvest(policy):
    o = observation(10, 20)
    o["farms"][0]["tiles"][3][4] = crop("WHEAT", 6)
    o["farms"][0]["tiles"][3][4].update(yield_units=5, max_lifespan_step=261)
    o["farms"][0]["tiles"][4][2] = crop("STRAWBERRY", 8)
    policy["_MEMORY"].clear()
    policy["_MEMORY"].update(token=(0, 10), step=259, targets={0: (2, 4)})
    assert decide(policy, o)["farmer"] == ["NORTH"]


def test_harvest_on_decay_step_precedes_optional_water(policy):
    o = observation(5, 0)
    t = crop("WHEAT", 0)
    t.update(yield_units=3, max_lifespan_step=120)
    o["farms"][0]["tiles"][4][4] = t
    policy["_MEMORY"].clear()
    assert decide(policy, o)["farmer"] == ["HARVEST"]


def test_deadline_feed_requires_real_inputs_and_keeps_animal_carrier(policy):
    o = observation(12, 20)
    o["farms"][0]["tiles"][4][3] = animal()
    o["farms"][0]["tiles"][4][4] = {"kind": "PASTURE"}
    o["private"]["inventories"] = [{"COW": 1}]
    policy["_MEMORY"].clear()
    a = decide(policy, o)
    assert a["farmer"][0] not in ("FEED", "WATER")


def test_calendar_labor_model_counts_saved_visits(policy):
    # Nine watering visits, four harvests, two setup terms, two fertilizer terms.
    assert policy["crop_work"]("STRAWBERRY", 4) == 17
    assert policy["crop_work"]("TOMATO", 4) == 16
    assert policy["crop_work"]("WHEAT", 1) == 7


def test_deposit_must_not_consume_the_last_required_bonus_service_action(policy):
    o = observation(9, 21)
    o["farms"][0]["money"] = 100
    t = crop("STRAWBERRY", 0)
    t.update(consecutive_unwatered=0, yield_units=0)
    o["farms"][0]["tiles"][4][4] = t
    o["private"].update(shed={"FERTILIZER": 1}, inventories=[{"MILK": 4}])
    policy["_MEMORY"].clear()
    assert decide(policy, o)["farmer"] == ["PICKUP", "FERTILIZER", 1]


def test_deadline_journey_does_not_reverse_for_new_nearby_work(policy):
    o = observation(10, 18)
    o["farms"][0]["tiles"][1][4] = crop("STRAWBERRY", 7)
    policy["_MEMORY"].clear()
    assert decide(policy, o)["farmer"] == ["NORTH"]
    later = deepcopy(o)
    later.update(hour=19, step=259)
    later["farms"][0]["farmer"] = [4, 3]
    later["farms"][0]["tiles"][4][4] = crop("STRAWBERRY", 7)
    assert decide(policy, later)["farmer"] == ["NORTH"]


def test_recorded_endangered_edge_crops_receive_feasible_distinct_assignments(policy):
    path = Path(__file__).resolve().parents[1] / "docs/examples/cycle-21-deadline-observations.json"
    data = json.loads(path.read_text())
    for case in data["cases"]:
        o = case["observation"]
        policy["_MEMORY"].clear()
        _, detail = policy["turn"](o, data["configuration"])
        targets = set(detail["assignments"].values())
        assert all(tuple(p) in targets for p in case["endangered_sites"])
        policy["_MEMORY"].clear()
        decide(policy, o, data["configuration"])
