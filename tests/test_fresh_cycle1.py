"""Independent unit/snapshot tests only. No engine import, steps, or matches."""

import copy
import hashlib
import json
import runpy
from pathlib import Path

import pytest

from scripts.check_fresh_cycle1 import check_action, check_histories
from scripts.make_fresh_cycle1 import SOURCE, build

ROOT = Path(__file__).resolve().parents[1]
CONFIG = {"episodeSteps": 720, "turnsPerDay": 24, "shedCapacity": 100}


@pytest.fixture
def policy():
    return runpy.run_path(str(SOURCE))


def observation(day=0, hour=0, workers=((4, 4),), money=3000):
    tiles = [[None if x < 5 and y < 5 else "LOCKED" for x in range(10)] for y in range(10)]
    farm = {
        "farmer": list(workers[0]),
        "hands": [list(p) for p in workers[1:]],
        "tiles": tiles,
        "money": money,
        "hires_today": len(workers) - 1,
        "unlocked_quadrants": ["NW"],
    }
    return {
        "day": day,
        "hour": hour,
        "player": 0,
        "farms": [farm, copy.deepcopy(farm)],
        "private": {"shed": {}, "seeds": {}, "inventories": [{} for _ in workers]},
        "market": {"inventory": {}},
        "town": {"unlocked_shops": []},
    }


def crop(name="WHEAT", planted=0, quantity=1, **patch):
    result = {
        "kind": "PLANT",
        "crop": name,
        "planted_day": planted,
        "yield_units": quantity,
        "watered_today": False,
        "consecutive_unwatered": 1,
        "fertilized_until_day": -1,
        "max_lifespan_step": -1,
    }
    result.update(patch)
    return result


def animal(name="COW", placed=0, **patch):
    result = {
        "kind": "COOP" if name == "GOOSE" else "PASTURE",
        "animal": name,
        "placed_day": placed,
        "yield_units": 0,
        "fed_today": False,
        "cared_today": False,
        "fertilizer_available": True,
        "consecutive_unfed": 0,
        "pending_care_bonus": 0,
    }
    result.update(patch)
    return result


def invoke(policy, obs, config=None):
    before = copy.deepcopy(obs)
    action = policy["agent"](obs, config or CONFIG)
    assert obs == before
    check_action(obs, config or CONFIG, action)
    return action


def planner(policy, obs, config=None):
    result = policy["Planner"](obs, config or CONFIG)
    result.make_jobs()
    return result


def test_packaging_standalone_deterministic_and_no_overwrite(tmp_path):
    one, two = tmp_path / "one/main.py", tmp_path / "two/main.py"
    assert build(one) == build(two) == hashlib.sha256(SOURCE.read_bytes()).hexdigest()
    assert one.read_bytes() == SOURCE.read_bytes() == two.read_bytes()
    with pytest.raises(FileExistsError):
        build(one)
    module = runpy.run_path(str(one))
    assert [k for k, v in module.items() if callable(v)][-1] == "agent"
    assert module["agent"]({}, CONFIG) == {"farmer": ["PASS"], "hands": [], "market": []}


@pytest.mark.parametrize("item,base", [("WHEAT", 25), ("MELON", 250), ("MILK", 160), ("WOOL", 200)])
def test_price_curves_and_sparse_overrides(policy, item, base):
    price = policy["quoted_price"]
    assert price(item, 10000) == base
    assert price(item, 9900) > base > price(item, 10100)
    assert price(item, 10000, {item: {"base": 2 * base}}) == 2 * base
    assert price(item, 10**20) == 1


def test_duplicate_shops_add_demand(policy):
    obs = observation()
    obs["town"]["unlocked_shops"] = ["YARN_STORE", "YARN_STORE"]
    p = planner(policy, obs)
    assert p.demand["WOOL"] == 25
    assert p.demand["MILK"] == 1


def test_one_seed_never_oversubscribed(policy):
    obs = observation(workers=((1, 4), (2, 3), (3, 2)))
    obs["private"]["seeds"] = {"WHEAT": 1}
    action = invoke(policy, obs)
    assert sum(a[0] == "PLANT" for a in [action["farmer"], *action["hands"]]) == 1


def test_bought_seed_cannot_supply_current_action(policy):
    action = invoke(policy, observation())
    assert action["farmer"][0] != "PLANT"
    assert any(order[0] in ("BUY_SEED", "BUY_ANIMAL") for order in action["market"])


def test_planting_requires_same_day_water_slot(policy):
    obs = observation(hour=23)
    obs["private"]["seeds"] = {"WHEAT": 4}
    assert invoke(policy, obs)["farmer"] != ["PLANT", "WHEAT"]


def test_newborn_and_production_night_water(policy):
    for day, planted, name in ((3, 3, "MELON"), (9, 0, "STRAWBERRY"), (8, 0, "TOMATO")):
        obs = observation(day=day)
        obs["farms"][0]["tiles"][4][4] = crop(name, planted, 0)
        assert invoke(policy, obs)["farmer"] == ["WATER"]


def test_safe_skip_requires_zero_drought(policy):
    obs = observation(day=2)
    obs["farms"][0]["tiles"][4][4] = crop("STRAWBERRY", 0, 0, consecutive_unwatered=0)
    assert (4, 4) not in planner(policy, obs).jobs
    obs["farms"][0]["tiles"][4][4]["consecutive_unwatered"] = 1
    assert invoke(policy, obs)["farmer"] == ["WATER"]


def test_fertilizer_before_single_crop_water_but_after_repeater_water(policy):
    obs = observation(day=6)
    obs["farms"][0]["tiles"][4][4] = crop("MELON", 0)
    obs["private"]["inventories"][0] = {"FERTILIZER": 1}
    assert invoke(policy, obs)["farmer"] == ["FERTILIZE"]
    obs = observation(day=9)
    obs["farms"][0]["tiles"][4][4] = crop("STRAWBERRY", 0, 0, watered_today=True)
    obs["private"]["inventories"][0] = {"FERTILIZER": 1}
    assert invoke(policy, obs)["farmer"] == ["FERTILIZE"]


def test_optional_fertilizer_cannot_block_last_water(policy):
    obs = observation(day=9, hour=23)
    obs["farms"][0]["tiles"][4][4] = crop("STRAWBERRY", 0, 0)
    obs["private"]["shed"] = {"FERTILIZER": 3}
    assert invoke(policy, obs)["farmer"] == ["WATER"]


def test_decay_action_is_harvest_not_water(policy):
    obs = observation(day=13)
    obs["farms"][0]["tiles"][4][4] = crop("MELON", 0, 3, max_lifespan_step=312)
    assert invoke(policy, obs)["farmer"] == ["HARVEST"]


def test_final_day_harvest_on_decay_can_still_deliver_later(policy):
    obs = observation(day=29)
    obs["farms"][0]["tiles"][4][4] = crop("MELON", 16, 3, max_lifespan_step=696)
    assert invoke(policy, obs)["farmer"] == ["HARVEST"]


def test_feed_in_shed_gets_picked_up_not_used_remotely(policy):
    obs = observation(day=10, workers=((4, 4), (5, 4)))
    obs["farms"][0]["tiles"][4][3] = animal()
    obs["farms"][0]["tiles"][3][4] = animal()
    obs["private"]["shed"] = {"WHEAT": 2}
    action = invoke(policy, obs)
    commands = [action["farmer"], *action["hands"]]
    assert all(a[:2] == ["PICKUP", "WHEAT"] for a in commands)
    assert sum(a[2] for a in commands) == 2


def test_complete_animal_visit_stays_until_care_and_collection(policy):
    obs = observation(day=10, hour=6)
    tile = animal(fed_today=True, yield_units=2)
    obs["farms"][0]["tiles"][4][4] = tile
    assert invoke(policy, obs)["farmer"] == ["HARVEST"]
    # Independently specified successive service states; no returned action is executed.
    second = observation(day=10, hour=7)
    second["farms"][0]["tiles"][4][4] = animal(fed_today=True, yield_units=0)
    second["farms"][0]["tiles"][0][0] = crop("MELON", 0, 6)
    assert invoke(policy, second)["farmer"] == ["CARE"]
    third = observation(day=10, hour=8)
    third["farms"][0]["tiles"][4][4] = animal(fed_today=True, cared_today=True)
    assert invoke(policy, third)["farmer"] == ["COLLECT_FERTILIZER"]


def test_last_turn_can_feed_even_without_time_for_full_bundle(policy):
    obs = observation(day=10, hour=23)
    obs["farms"][0]["tiles"][4][4] = animal(consecutive_unfed=1, yield_units=3)
    obs["private"]["inventories"][0] = {"WHEAT": 1}
    assert invoke(policy, obs)["farmer"] == ["FEED"]


def test_no_feed_cannot_block_available_animal_harvest(policy):
    obs = observation(day=10, hour=22)
    obs["farms"][0]["tiles"][4][4] = animal(yield_units=3)
    assert invoke(policy, obs)["farmer"] == ["HARVEST"]


def test_carried_installation_precedes_unrelated_work(policy):
    obs = observation(day=4, workers=((2, 4),))
    obs["private"]["inventories"][0] = {"COW": 1}
    obs["farms"][0]["tiles"][4][2] = {"kind": "PASTURE"}
    obs["farms"][0]["tiles"][0][0] = crop("WHEAT", 0, 4)
    assert invoke(policy, obs)["farmer"] == ["PLACE", "COW"]


def test_terminal_delivery_and_same_turn_sale(policy):
    obs = observation(day=29, hour=22)
    obs["private"]["inventories"][0] = {"MILK": 6, "WHEAT": 2}
    action = invoke(policy, obs)
    assert action["farmer"] == ["DROP"]
    assert ["SELL", "MILK", 6] in action["market"]
    assert ["SELL", "WHEAT", 2] in action["market"]
    assert all(order[0] == "SELL" for order in action["market"])


def test_terminal_return_deadline_and_unreachable_harvest(policy):
    obs = observation(day=29, hour=20, workers=((2, 4),))
    obs["private"]["inventories"][0] = {"MILK": 6}
    assert invoke(policy, obs)["farmer"] == ["EAST"]
    obs = observation(day=29, hour=22, workers=((3, 4),))
    obs["farms"][0]["tiles"][4][3] = crop("WHEAT", 25, 4)
    assert invoke(policy, obs)["farmer"] != ["HARVEST"]


def test_final_morning_hires_delivery_workers(policy):
    obs = observation(day=29)
    for y in range(5):
        for x in range(5):
            obs["farms"][0]["tiles"][y][x] = crop("MELON", 18, 6)
    action = invoke(policy, obs)
    assert ["HIRE"] in action["market"]
    assert not any(o[0].startswith("BUY") for o in action["market"])


def test_partial_deposit_reserves_space_without_discarding(policy):
    obs = observation(day=29, hour=22, workers=((4, 4), (5, 4)))
    obs["private"]["shed"] = {"WHEAT": 98}
    obs["private"]["inventories"] = [{"MILK": 6}, {"WOOL": 4}]
    action = invoke(policy, obs)
    assert action["farmer"] == ["PLACE", "MILK", 2]
    assert action["hands"] == [["PASS"]]
    assert ["SELL", "MILK", 2] in action["market"]


def test_unrelated_covered_urgency_does_not_interrupt_commitment(policy):
    obs = observation(day=20, hour=12, workers=((7, 1), (4, 3)))
    # Geometry and times are independently specified, not another policy's memory.
    obs["farms"][0]["tiles"][3][9] = crop("MELON", 10, 6)
    obs["farms"][0]["tiles"][3][4] = animal()
    obs["private"]["inventories"][1] = {"WHEAT": 2}
    memory = policy["agent"].__globals__["_MEMORY"]
    memory.update(token=(0, 20, 10, 718), step=491, targets={0: ((9, 3), "service")})
    action = invoke(policy, obs)
    assert action["farmer"] == ["EAST"]
    assert action["hands"] == [["FEED"]]
    assert memory["targets"][0][0] == (9, 3)


def test_short_recorded_histories_are_bounded_deterministic_and_legal():
    report = check_histories(SOURCE, ROOT / "docs/examples/fresh-cycle1-histories.json")
    assert report["calls"] > 100
    assert report["max_seconds"] < 1


def test_original_reversal_observations_without_old_policy_memory(policy):
    recorded = json.loads((ROOT / "docs/examples/cycle-21-route-regression.json").read_text())
    for case in recorded["cases"]:
        invoke(policy, case["observation"], recorded["configuration"])


def test_memory_resets_between_seats_days_and_repeated_calls(policy):
    obs = observation()
    first = invoke(policy, obs)
    assert invoke(policy, obs) == first
    obs["player"] = 1
    invoke(policy, obs)
    memory = policy["agent"].__globals__["_MEMORY"]
    assert memory["token"][:2] == (1, 0)
    obs["day"] = 1
    invoke(policy, obs)
    assert memory["token"][:2] == (1, 1)


def test_actual_rescue_assigns_specific_uncovered_job(policy):
    obs = observation(day=12, hour=10, workers=((4, 4),))
    p = policy["Planner"](obs, CONFIG)
    p.add_job((4, 2), [["WATER"]], 20, deadline=p.step + 12)
    p.add_job((3, 4), [["HARVEST"]], 1000, deadline=p.step + 2, essential=True)
    policy["agent"].__globals__["_MEMORY"]["targets"] = {0: ((4, 2), "service")}
    p.allocate()
    assert p.assignments[0][0]["pos"] == (3, 4)
    assert p.switches == [(0, (4, 2), (3, 4))]
    assert p.claimed == {(3, 4)}


def test_no_new_purchase_when_feed_is_unfunded(policy):
    obs = observation(day=10, money=0)
    obs["farms"][0]["tiles"][4][4] = animal()
    action = invoke(policy, obs)
    assert not any(o[0] in ("HIRE", "BUY_SEED", "BUY_ANIMAL", "BUY_LAND") for o in action["market"])


def test_one_market_slot_remains_bounded(policy):
    obs = observation(day=10)
    obs["private"]["shed"] = {"MILK": 6, "WOOL": 4, "WHEAT": 10}
    config = {**CONFIG, "maxMarketOrdersPerTurn": 1}
    assert len(invoke(policy, obs, config)["market"]) == 1


@pytest.mark.parametrize("size", [4, 8, 12])
def test_configured_geometry_does_not_use_fixed_shed_coordinates(policy, size):
    obs = observation()
    half = size // 2
    for farm in obs["farms"]:
        farm["farmer"] = [half - 1, half - 1]
        farm["tiles"] = [
            [None if x < half and y < half else "LOCKED" for x in range(size)] for y in range(size)
        ]
    invoke(policy, obs, {**CONFIG, "boardSize": size})
