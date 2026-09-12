"""Independent observation/accounting checks. Never import or advance the engine."""

import json
import runpy
from copy import deepcopy
from hashlib import sha256
from pathlib import Path

import pytest

from scripts.make_repaired_agent import CYCLE13_SHA256, build

ROOT = Path(__file__).resolve().parents[1]
AUDIT = json.loads((ROOT / "docs/benchmarks/cycle-13-logic-audit.json").read_text())
RECORDS = json.loads((ROOT / "docs/examples/cycle-15-repair-observations.json").read_text())
CFG = RECORDS["configuration"]


@pytest.fixture(scope="module")
def policy(tmp_path_factory):
    path = tmp_path_factory.mktemp("repairs") / "main.py"
    build(path)
    # Use the same namespace as the actual entrypoint, not runpy's copied globals.
    return runpy.run_path(str(path))["agent"].__globals__


def terminal():
    return deepcopy(AUDIT["constructed_terminal_case"]["observation"])


def recorded(step):
    return deepcopy(RECORDS["observations"][str(step)])


def test_package_is_reproducible_and_refuses_overwrite(tmp_path):
    first, second = tmp_path / "a.py", tmp_path / "b.py"
    assert build(first) == build(second)
    assert first.read_bytes() == second.read_bytes()
    with pytest.raises(FileExistsError):
        build(first)
    # Last callable remains the Kaggle entrypoint; no package imports are needed.
    scope = runpy.run_path(str(first))
    assert [name for name, value in scope.items() if callable(value)][-1] == "agent"


@pytest.mark.parametrize("crop,planted,units", [("WHEAT", 25, 3), ("CARROT", 26, 2)])
def test_terminal_cargo_preempts_water_and_fertilizer(policy, crop, planted, units):
    obs = terminal()
    obs["farms"][0]["tiles"][4][1].update(crop=crop, planted_day=planted, yield_units=units)
    obs["private"]["inventories"][0]["FERTILIZER"] = 1
    action, detail = policy["expansion_turn"](obs, CFG, timing=1)
    assert action["farmer"] == ["EAST"]
    assert detail["mixed"]["terminal_returns"] == [0]
    assert not detail["mixed"]["carrot_inputs"]["bundles"]


@pytest.mark.parametrize("remaining,expected", [(4, "PASS"), (5, "HARVEST"), (6, "WATER")])
def test_terminal_watering_reserves_harvest_and_delivery(policy, remaining, expected):
    obs = terminal()
    obs.update(step=719 - remaining, hour=23 - remaining)
    obs["private"]["inventories"] = [{}]
    assert policy["agent"](obs, CFG)["farmer"] == [expected]


def test_terminal_deposit_is_in_same_turn_sale_ledger(policy):
    obs = terminal()
    obs.update(step=718, hour=22)
    obs["farms"][0]["farmer"] = [4, 4]
    action = policy["agent"](obs, CFG)
    assert action["farmer"] == ["DROP"]
    assert ["SELL", "CARROT", 10] in action["market"]
    assert not any(o[0].startswith("BUY") for o in action["market"])


def test_shared_deposit_capacity_still_precedes_sales(policy):
    obs = terminal()
    obs.update(step=718, hour=22)
    obs["farms"][0].update(farmer=[4, 4], hands=[[4, 4]])
    obs["private"].update(shed={"WHEAT": 95}, inventories=[{"CARROT": 4}, {"CARROT": 4}])
    action = policy["agent"](obs, CFG)
    assert action["farmer"] == ["DROP"]
    assert action["hands"] == [["PLACE", "CARROT", 1]]
    assert ["SELL", "CARROT", 5] in action["market"]


def test_fatal_tomato_watering_wins_at_last_daily_action(policy):
    obs = deepcopy(AUDIT["constructed_tomato_case"]["observation"])
    assert policy["agent"](obs, CFG)["farmer"] == ["WATER"]


@pytest.mark.parametrize("final,age,watered", [(29, 11, False), (10, 10, False), (29, 10, True)])
def test_tomato_still_harvests_after_last_event_or_final_day(policy, final, age, watered):
    tile = deepcopy(AUDIT["constructed_tomato_case"]["observation"]["farms"][0]["tiles"][4][1])
    tile.update(planted_day=10 - age, watered_today=watered)
    assert policy["crop_job"](tile, 10, final)[0] == "HARVEST"


def test_tomato_existing_fertilizer_uses_prior_night_and_expires(policy):
    tile = dict(
        crop="TOMATO", planted_day=0, yield_units=0, watered_today=True, fertilized_until_day=8
    )
    col = policy["crop_column"]("TOMATO", 0, 29, tile=tile, today=7)
    assert col["outputs"] == {8: 2, 9: 2, 10: 1, 11: 1}
    assert col["fertilizer"] == []
    tile.update(yield_units=3)
    assert policy["crop_column"]("TOMATO", 0, 29, tile=tile, today=8)["outputs"] == {
        8: 3,
        9: 2,
        10: 1,
        11: 1,
    }
    assert policy["crop_column"]("TOMATO", 0, 29)["outputs"] == {8: 1, 9: 1, 10: 1, 11: 1}


def test_recorded_farm_and_added_wheat_use_identical_nine_then_ten_crew(policy):
    obs = recorded(384)
    for extra in (False, True):
        if extra:
            obs["farms"][0]["tiles"][1][4] = dict(
                kind="PLANT",
                crop="WHEAT",
                planted_day=12,
                yield_units=4,
                watered_today=True,
                consecutive_unwatered=0,
                fertilized_until_day=-1,
                max_lifespan_step=408,
            )
        assets = policy["throughput_assets"](obs)[0]
        assert all("site" in tile for tile in assets)
        forecast = policy["repaired_workforce"](assets, 16, 29, 24, policy["shed_access"](obs))
        _, detail = policy["expansion_turn"](obs, CFG, timing=1)
        assert forecast["workers"] == detail["mixed"]["worker_target"] == 9 + int(extra)
    assert policy["hire_cost"](8, 1) == 34


def test_marginal_wage_forecast_charges_the_extra_worker(policy):
    obs = recorded(384)
    obs.update(day=15, hour=7, step=367)
    assets = policy["throughput_assets"](recorded(384))[0]
    addition = dict(crop="WHEAT", planted_day=12, site=(4, 1), yield_units=4, watered_today=True)
    wages, _, fits, next_wages, immediate = policy["repaired_labor_delta"](
        obs, CFG, assets, [addition]
    )
    # Age-four wheat has only the next day's marginal labor left, not a lifetime annuity.
    assert (wages, next_wages, immediate) == (34, 88, 0)
    assert fits


def test_labor_infeasibility_is_not_hidden_by_hiring_cap(policy):
    assets = [dict(crop="WHEAT", planted_day=0, site=(x, y)) for y in range(10) for x in range(10)]
    model = policy["repaired_workforce"](assets, 1, 29)
    assert model["workers"] > 12
    assert not model["fits"]
    remote = [dict(crop="WHEAT", planted_day=0, site=(30, 30))]
    assert not policy["repaired_workforce"](remote, 1, 29)["fits"]


def test_recorded_land_opportunity_reaches_actual_output(policy):
    obs = recorded(336)
    original = deepcopy(obs)
    _, fields = policy["farm_sites"](obs)
    assert sum(obs["farms"][0]["tiles"][y][x] is None for x, y in fields) > 4
    action, detail = policy["expansion_turn"](obs, CFG, timing=1)
    assert ["BUY_LAND"] in action["market"]
    assert action["market"][-2:] == [["BUY_LAND"], ["BUY_SEED", "TOMATO", 8]]
    options = detail["expansion"]["alternatives"]
    assert detail["expansion"]["chosen"]["value"] == max(a["value"] for a in options)
    assert obs == original


def test_crowded_land_bundle_defers_without_inferior_seed_commitment(policy):
    obs = recorded(336)
    obs.update(hour=7, step=343)
    commands = [["PASS"] for _ in obs["private"]["inventories"]]
    # Existing orders remain untouched; evaluate a full bundle even with one slot.
    market = [["SELL", "WHEAT", 0] for _ in range(9)]
    result, detail = policy["repaired_investment"](obs, CFG, policy["MARKET"], commands, market[:])
    assert detail["deferred"] == [["BUY_LAND"], ["BUY_SEED", "TOMATO", 8]]
    assert result == market and detail["chosen"] is None
    # Independent observation with cleared order slots. No game/action is advanced.
    result, detail = policy["repaired_investment"](obs, CFG, policy["MARKET"], commands, [])
    assert result == [["BUY_LAND"], ["BUY_SEED", "TOMATO", 8]]
    assert detail["chosen"] is not None


def test_expansion_can_fund_animals_on_new_land(policy):
    obs = recorded(336)
    obs.update(hour=7, step=343)
    commands = [["PASS"] for _ in obs["private"]["inventories"]]
    _, detail = policy["repaired_investment"](obs, CFG, policy["MARKET"], commands, [])
    animals = [
        a
        for a in detail["alternatives"]
        if a["orders"][0] == ["BUY_LAND"] and a["orders"][-1][0] == "BUY_ANIMAL"
    ]
    assert animals
    for a in animals:
        _, animal, count = a["orders"][-1]
        assert a["cost"] == 1000 + count * policy["ANIMALS"][animal]["cost"]


@pytest.mark.parametrize(
    "reason", ["poor", "pending_seeds", "pending_animal", "full_orders", "late"]
)
def test_admission_keeps_funding_and_installation_constraints(policy, reason):
    obs = recorded(336)
    market = []
    if reason == "poor":
        obs["farms"][0]["money"] = 100
    elif reason == "pending_seeds":
        obs["private"]["seeds"]["WHEAT"] = 1
    elif reason == "pending_animal":
        obs["private"]["shed"]["COW"] = 1
    elif reason == "full_orders":
        market = [["SELL", "WHEAT", 0] for _ in range(10)]
    else:
        obs.update(day=29, hour=0, step=696)
    commands = [["PASS"] for _ in obs["private"]["inventories"]]
    result, detail = policy["repaired_investment"](obs, CFG, policy["MARKET"], commands, market[:])
    assert result == market and detail["chosen"] is None


def test_frozen_parent_is_not_modified():
    parent = ROOT / "artifacts/submission-cycle-13-throughput/main.py"
    if parent.exists():
        assert sha256(parent.read_bytes()).hexdigest() == CYCLE13_SHA256


def test_investment_does_not_spend_uncertain_sale_proceeds(policy):
    obs = recorded(336)
    obs["farms"][0]["money"] = 100
    obs["private"]["shed"]["MILK"] = 20
    commands = [["PASS"] for _ in obs["private"]["inventories"]]
    market = [["SELL", "MILK", 20]]
    result, report = policy["repaired_investment"](obs, CFG, policy["MARKET"], commands, market[:])
    assert result == market
    assert report["chosen"] is None
