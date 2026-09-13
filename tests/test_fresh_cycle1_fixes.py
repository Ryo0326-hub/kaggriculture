"""Independent, bounded regressions for the Cycle 1 policy fixes; no engine."""

import copy
import runpy
import signal
from itertools import product

import pytest
from test_optimization import CONFIG, MARKETS, animal, crop, decide, observation
from test_research_scenarios import flat_config

from scripts.check_fresh_cycle1 import check_action, timeout_handler
from scripts.make_fresh_cycle1 import SOURCE
from scripts.optimization_oracles import exact_deposits
from scripts.research_oracles import terminal_deposit_choice


@pytest.fixture
def policy():
    return runpy.run_path(str(SOURCE))


@pytest.mark.parametrize(
    "weights",
    [
        [],
        [[], []],
        [[None, None], [None, None]],
        [[-3, None], [None, -1]],
        [[20, 200]],
        [[200, 150], [200, None]],
        [[9, 8, None], [9, None, None], [None, 8, 7]],
        [[1, 2, 3], [3, 2, 1], [2, None, 1], [None, 4, 0]],
        [[0, 0], [0, 0]],
    ],
    ids=[
        "no-workers",
        "no-jobs",
        "forbidden",
        "negative",
        "valuable-deadline",
        "exclusive-access",
        "three-worker-reassignment",
        "more-workers-than-jobs",
        "ties",
    ],
)
def test_matching_agrees_with_exhaustive_small_assignment(policy, weights):
    n, m = len(weights), len(weights[0]) if weights else 0
    expected = 0
    for choices in product(range(-1, m), repeat=n):
        assigned = [c for c in choices if c >= 0]
        if len(assigned) != len(set(assigned)):
            continue
        if any(c >= 0 and weights[w][c] is None for w, c in enumerate(choices)):
            continue
        expected = max(expected, sum(weights[w][c] for w, c in enumerate(choices) if c >= 0))
    pairs = policy["maximum_weight_matching"](weights)
    assert len({w for w, _ in pairs}) == len(pairs) == len({j for _, j in pairs})
    assert all(weights[w][j] is not None for w, j in pairs)
    assert sum(weights[w][j] for w, j in pairs) == expected


@pytest.mark.parametrize("wheat", [0, 1, 2])
def test_joint_assignment_rechecks_shared_feed_supply(policy, wheat):
    obs = observation(day=10, workers=((4, 4), (5, 4)))
    obs["private"]["shed"] = {"WHEAT": wheat}
    obs["farms"][0]["tiles"][3][4] = animal("COW")
    obs["farms"][0]["tiles"][4][3] = animal("COW")
    p = policy["Planner"](obs, CONFIG)
    p.make_jobs()
    p.allocate()
    assert sum(r["needed"].get("WHEAT", 0) for _, r in p.assignments.values()) == wheat
    assert len(p.assignments) == wheat
    decide(policy, obs)


@pytest.mark.parametrize(
    "goods",
    [
        [("WHEAT", 6), ("MILK", 1)],
        [("MILK", 2), ("WOOL", 3), ("WHEAT", 5)],
        [("WOOL", 1), ("WHEAT", 6), ("MILK", 2)],
    ],
)
@pytest.mark.parametrize("room", [0, 1, 2, 4, 6])
def test_global_terminal_capacity_matches_exact_flat_price_oracle(policy, goods, room):
    obs = observation(day=29, hour=22, workers=((4, 4), (5, 4), (4, 5))[: len(goods)])
    obs["private"]["shed"] = {"FERTILIZER": 100 - room}
    obs["private"]["inventories"] = [{item: n} for item, n in goods]
    prices = {p: details[0] for p, details in MARKETS.items()}
    optimum, _ = exact_deposits(goods, prices, room)
    action = decide(policy, obs, flat_config())
    actual = sum(
        o[2] * prices[o[1]] for o in action["market"] if o[0] == "SELL" and o[1] != "FERTILIZER"
    )
    assert actual == optimum


@pytest.mark.parametrize(
    "goods",
    [
        {"MILK": 1, "WHEAT": 8},
        {"WHEAT": 8, "MILK": 1},
        {"MILK": 2, "WHEAT": 2},
    ],
)
@pytest.mark.parametrize("room", [1, 3, 8])
def test_mixed_cargo_uses_legal_one_action_cash_optimum(policy, goods, room):
    obs = observation(day=29, hour=22)
    obs["private"]["shed"] = {"FERTILIZER": 100 - room}
    obs["private"]["inventories"][0] = goods.copy()
    expected, winners = terminal_deposit_choice(goods, {"MILK": 160, "WHEAT": 25}, room)
    action = decide(policy, obs, flat_config())
    assert tuple(action["farmer"]) in winners
    actual = sum(o[2] * {"MILK": 160, "WHEAT": 25}.get(o[1], 0) for o in action["market"])
    assert actual == expected


@pytest.mark.parametrize("tpd,steps", [(24, 720), (24, 710), (12, 360)])
def test_overflow_validator_is_terminal_only_and_never_sells_discarded_units(tpd, steps):
    day, hour = divmod(steps - 2, tpd)
    obs = observation(day=day, hour=hour)
    obs["private"]["shed"] = {"WHEAT": 98}
    obs["private"]["inventories"][0] = {"MILK": 3}
    cfg = {**CONFIG, "turnsPerDay": tpd, "episodeSteps": steps}
    action = {"farmer": ["DROP"], "hands": [], "market": [["SELL", "MILK", 2]]}
    check_action(obs, cfg, action)
    earlier = copy.deepcopy(obs)
    earlier["day"], earlier["hour"] = divmod(steps - 3, tpd)
    with pytest.raises(AssertionError):
        check_action(earlier, cfg, action)
    action["market"][0][2] = 3
    with pytest.raises(AssertionError):
        check_action(obs, cfg, action)


def test_terminal_order_value_includes_own_sale_slippage(policy):
    obs = observation(day=29, hour=22)
    obs["private"]["shed"] = {"MILK": 3, "WHEAT": 3}
    cfg = flat_config(maxMarketOrdersPerTurn=1)
    cfg["marketParams"]["MILK"].update(base=100, T=1, above_func="linear", above_target=0.5)
    cfg["marketParams"]["WHEAT"].update(base=60)
    # Milk receipts 100+50+1=151, wheat receipts 60+60+60=180.
    assert decide(policy, obs, cfg)["market"] == [["SELL", "WHEAT", 3]]


@pytest.mark.parametrize("name,first", [("TOMATO", 8), ("STRAWBERRY", 10)])
@pytest.mark.parametrize("horizon", [1, 2, 5])
def test_forecast_counts_only_crop_events_inside_requested_horizon(policy, name, first, horizon):
    obs = observation(day=12)
    obs["farms"][1]["tiles"][0][0] = crop(name, planted=12, quantity=0)
    assert policy["Planner"](obs, CONFIG).visible_supply(horizon)[name] == 0
    obs["farms"][1]["tiles"][0][0] = crop(name, planted=13 - first, quantity=0)
    assert policy["Planner"](obs, CONFIG).visible_supply(horizon)[name] > 0


@pytest.mark.parametrize("factor", ["crew", "feeding", "care"])
def test_service_signals_separately_discount_rival_output(policy, factor):
    healthy = observation(profile="dairy-specialist")
    neglected = copy.deepcopy(healthy)
    if factor == "crew":
        neglected["farms"][1]["hands"] = []
    for row in neglected["farms"][1]["tiles"]:
        for tile in row:
            if isinstance(tile, dict) and tile.get("animal"):
                if factor == "feeding":
                    tile.update(fed_today=False, consecutive_unfed=1)
                if factor == "care":
                    tile.update(cared_today=False, pending_care_bonus=0)
    assert policy["Planner"](neglected, CONFIG).value_price("MILK") > policy["Planner"](
        healthy, CONFIG
    ).value_price("MILK")


@pytest.mark.parametrize("capacity", [100, 200])
def test_large_crew_terminal_capacity_and_callback_budget(policy, capacity):
    obs = observation(day=29, hour=22, workers=((4, 4),) * 15)
    obs["private"]["inventories"] = [{"MILK": 18} for _ in range(15)]
    cfg = flat_config(shedCapacity=capacity)
    previous = signal.signal(signal.SIGALRM, timeout_handler)
    try:
        signal.setitimer(signal.ITIMER_REAL, 1.0)
        action = decide(policy, obs, cfg)
    finally:
        signal.setitimer(signal.ITIMER_REAL, 0)
        signal.signal(signal.SIGALRM, previous)
    assert action["market"] == [["SELL", "MILK", capacity]]
