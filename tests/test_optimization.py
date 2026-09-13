"""Economic contracts against stylized opponents and independent static oracles.

No engine, season rollouts, parameter tuning or paid compute. Every parameter
row is a named economic condition, not an arbitrary repetition to raise count.
Known optimization gaps retain strict expected-failure assertions.
"""

import copy
import runpy
from fractions import Fraction

import pytest

from scripts.check_fresh_cycle1 import check_action
from scripts.make_fresh_cycle1 import SOURCE
from scripts.optimization_oracles import (
    best_reply,
    exact_assignment,
    exact_deposits,
    exact_portfolio,
    linear_sale_receipts,
    robust_reply,
)

# Published rule anchors, independent of the candidate's constant dictionaries.
# Product: base, inventory scale, scarcity rise, glut fall (as exact decimals).
MARKETS = {
    "WHEAT": (25, 400, "0.8", "0.2"),
    "CARROT": (35, 450, "1", "0.7"),
    "MELON": (250, 300, "0.2", "3.6"),
    "TOMATO": (60, 200, "0.4", "0.6"),
    "STRAWBERRY": (120, 100, "0.7", "1.6"),
    "MILK": (160, 122, "0.6", "1.6"),
    "WOOL": (200, 105, "0.2", "3.2"),
    "EGG": (50, 332, "0.4", "0.2"),
    "FERTILIZER": (100, 200, "0.4", "0.4"),
}
ASSET_OUTPUT = {
    "WHEAT": "WHEAT",
    "CARROT": "CARROT",
    "MELON": "MELON",
    "TOMATO": "TOMATO",
    "STRAWBERRY": "STRAWBERRY",
    "COW": "MILK",
    "SHEEP": "WOOL",
    "GOOSE": "EGG",
}
FIRST = {
    "WHEAT": 2,
    "CARROT": 2,
    "MELON": 10,
    "TOMATO": 8,
    "STRAWBERRY": 10,
    "COW": 8,
    "SHEEP": 6,
    "GOOSE": 4,
}
SHOPS = [
    ("BAKERY", "EGG", 6),
    ("PIZZA_SHOP", "TOMATO", 6),
    ("BRUNCH_SPOT", "STRAWBERRY", 6),
    ("YARN_STORE", "WOOL", 12),
    ("ICE_CREAM_SHOP", "MILK", 6),
    ("PET_CAFE", "CARROT", 12),
    ("SMOOTHIE_SHOP", "MILK", 6),
    ("FARMERS_MARKET", "WHEAT", 6),
]
PROFILES = {
    "passive": (),
    "dairy-specialist": (("COW", 12),),
    "wool-specialist": (("SHEEP", 12),),
    "egg-specialist": (("GOOSE", 12),),
    "berry-specialist": (("STRAWBERRY", 20),),
    "melon-dumper": (("MELON", 16),),
    "feed-supplier": (("WHEAT", 20),),
    "mixed-farm": (("COW", 4), ("SHEEP", 3), ("GOOSE", 3), ("STRAWBERRY", 8)),
}
CONFIG = {"episodeSteps": 720, "turnsPerDay": 24, "shedCapacity": 100}


def crop(name, *, planted=0, quantity=1, **patch):
    tile = {
        "kind": "PLANT",
        "crop": name,
        "planted_day": planted,
        "yield_units": quantity,
        "watered_today": False,
        "consecutive_unwatered": 1,
        "fertilized_until_day": -1,
        "max_lifespan_step": -1,
    }
    tile.update(patch)
    return tile


def animal(name, **patch):
    tile = {
        "kind": "COOP" if name == "GOOSE" else "PASTURE",
        "animal": name,
        "placed_day": 0,
        "yield_units": 0,
        "fed_today": False,
        "cared_today": False,
        "fertilizer_available": False,
        "consecutive_unfed": 0,
        "pending_care_bonus": 0,
    }
    tile.update(patch)
    return tile


def observation(*, day=12, hour=0, money=3000, workers=((4, 4),), profile="passive"):
    tiles = [[None if x < 5 and y < 5 else "LOCKED" for x in range(10)] for y in range(10)]
    farm = {
        "tiles": tiles,
        "farmer": list(workers[0]),
        "hands": [list(p) for p in workers[1:]],
        "money": money,
        "hires_today": len(workers) - 1,
        "unlocked_quadrants": ["NW"],
    }
    rival = copy.deepcopy(farm)
    rival["hands"] = [[4, 4]] * 8
    rival["hires_today"] = 8
    rival["unlocked_quadrants"] = ["NW", "NE", "SW", "SE"]
    rival["tiles"] = [[None for _ in range(10)] for _ in range(10)]
    obs = {
        "day": day,
        "hour": hour,
        "player": 0,
        "farms": [farm, rival],
        "private": {"shed": {}, "seeds": {}, "inventories": [{} for _ in workers]},
        "market": {"inventory": dict.fromkeys(MARKETS, 10000)},
        "town": {"unlocked_shops": []},
    }
    fill_rival(obs, PROFILES[profile])
    return obs


def fill_rival(obs, assets):
    index = 0
    for name, count in assets:
        for _ in range(count):
            tile = (
                animal(name, fed_today=True, cared_today=True, pending_care_bonus=2)
                if name in ("COW", "SHEEP", "GOOSE")
                else crop(name, planted=max(0, obs["day"] - FIRST[name]), quantity=3)
            )
            obs["farms"][1]["tiles"][index // 10][index % 10] = tile
            index += 1


def linear_config(*, base=100, slope=1):
    return {
        **CONFIG,
        "marketParams": {
            p: {
                "base": base,
                "I0": 10000,
                "T": 100,
                "above_func": "linear",
                "below_func": "linear",
                "above_target": 100 * slope / base,
                "below_target": 100 * slope / base,
            }
            for p in MARKETS
        },
    }


@pytest.fixture(scope="module")
def module():
    return runpy.run_path(str(SOURCE))


@pytest.fixture
def policy(module):
    module["agent"].__globals__["_MEMORY"].clear()
    return module


def decide(policy, obs, config=None):
    before = copy.deepcopy(obs)
    result = policy["agent"](obs, config or CONFIG)
    assert obs == before
    check_action(obs, config or CONFIG, result)
    return result


@pytest.mark.parametrize("product_name", MARKETS)
@pytest.mark.parametrize("regime", ["scarcity", "anchor", "glut"])
def test_price_anchors_preserve_expected_unit_economics(policy, product_name, regime):
    base, scale, rise, fall = MARKETS[product_name]
    offset = {"scarcity": -scale, "anchor": 0, "glut": scale}[regime]
    expected = {
        "scarcity": base * (1 + Fraction(rise)),
        "anchor": Fraction(base),
        "glut": max(1, base * (1 - Fraction(fall))),
    }[regime]
    actual = policy["quoted_price"](product_name, 10000 + offset)
    # Half-unit ties may land on either neighbor due to floating point curves.
    assert abs(actual - expected) <= Fraction(500001, 1000000)


@pytest.mark.parametrize("asset", ASSET_OUTPUT)
@pytest.mark.parametrize("rival_size", [6, 16], ids=["focused-competitor", "large-specialist"])
def test_competing_supply_reduces_same_asset_marginal_value(policy, asset, rival_size):
    idle = observation(day=8)
    rival = copy.deepcopy(idle)
    fill_rival(rival, [(asset, rival_size)])
    before = policy["Planner"](idle, CONFIG).investment(asset)[1]
    after = policy["Planner"](rival, CONFIG).investment(asset)[1]
    assert after < before, (asset, before, after)


@pytest.mark.parametrize("herd", ["COW", "SHEEP", "GOOSE"])
@pytest.mark.parametrize("headcount", [4, 12], ids=["small-herd", "large-herd"])
def test_rival_herd_creates_complementary_wheat_demand(policy, herd, headcount):
    idle = observation(day=8)
    rival = copy.deepcopy(idle)
    fill_rival(rival, [(herd, headcount)])
    assert policy["Planner"](rival, CONFIG).value_price("WHEAT") > (
        policy["Planner"](idle, CONFIG).value_price("WHEAT")
    )


@pytest.mark.parametrize("animal_name", ["COW", "SHEEP", "GOOSE"])
@pytest.mark.parametrize("rival_wheat", [8, 20], ids=["modest-feed-supply", "large-feed-supply"])
def test_rival_feed_supplier_improves_our_livestock_margins(policy, animal_name, rival_wheat):
    idle = observation(day=8)
    rival = copy.deepcopy(idle)
    fill_rival(rival, [("WHEAT", rival_wheat)])
    assert (
        policy["Planner"](rival, CONFIG).investment(animal_name)[1]
        > (policy["Planner"](idle, CONFIG).investment(animal_name)[1])
    )


@pytest.mark.parametrize("shop,item,daily", SHOPS, ids=[x[0] for x in SHOPS])
@pytest.mark.parametrize("copies", [1, 2, 3], ids=["one-shop", "duplicate-shops", "three-shops"])
def test_revealed_demand_raises_target_product_value(policy, shop, item, daily, copies):
    before = observation()
    after = copy.deepcopy(before)
    after["town"]["unlocked_shops"] = [shop] * copies
    a, b = policy["Planner"](before, CONFIG), policy["Planner"](after, CONFIG)
    assert b.demand[item] - a.demand[item] == daily * copies
    assert b.value_price(item) > a.value_price(item)


@pytest.mark.parametrize("profile", PROFILES)
@pytest.mark.parametrize("season", ["early-reinvestment", "maturing-farm", "final-liquidation"])
def test_actions_remain_feasible_against_each_opponent_style(policy, profile, season):
    day = {"early-reinvestment": 3, "maturing-farm": 12, "final-liquidation": 29}[season]
    obs = observation(day=day, profile=profile, workers=((4, 4), (3, 4), (4, 3)))
    obs["private"]["shed"] = {"WHEAT": 8, "FERTILIZER": 2, "MELON": 3}
    obs["farms"][0]["tiles"][4][4] = animal("COW", yield_units=3)
    obs["farms"][0]["tiles"][4][3] = crop("WHEAT", planted=max(0, day - 4), quantity=3)
    action = decide(policy, obs)
    if day == 29:
        assert all(o[0] in ("SELL", "HIRE") for o in action["market"])
    else:
        for order in action["market"]:
            if order[0] in ("BUY_ANIMAL", "BUY_SEED"):
                assert policy["Planner"](obs, CONFIG).investment(order[1])[1] > 0


@pytest.mark.parametrize("item", MARKETS)
@pytest.mark.parametrize(
    "rival_units", [0, 4, 40], ids=["rival-holds", "matched-sale", "rival-dumps"]
)
def test_final_shed_sale_is_best_response_to_rival_sales(policy, item, rival_units):
    obs = observation(day=29, hour=22)
    obs["private"]["shed"] = {item: 4}
    cfg = linear_config(base=30, slope=1)
    action = decide(policy, obs, cfg)
    sold = sum(o[2] for o in action["market"] if o[:2] == ["SELL", item])
    payoffs = {n: linear_sale_receipts(n, rival_units, base=30) for n in range(5)}
    assert payoffs[sold] == max(payoffs.values())
    assert sold == 4  # Positive remaining units have no terminal continuation value.


@pytest.mark.parametrize("item", MARKETS)
def test_unit_price_times_quantity_overstates_cash_against_dumping_rival(policy, item):
    cfg = linear_config(base=100, slope=1)
    prices = [policy["quoted_price"](item, 10000 + 2 * k, cfg["marketParams"]) for k in range(6)]
    exact = linear_sale_receipts(6, 6, base=100)
    assert sum(prices) == exact == 570
    assert exact < 6 * prices[0]


@pytest.mark.parametrize("quoted_units", [2, 4], ids=["two-unit-budget", "four-unit-budget"])
@pytest.mark.parametrize(
    "inventory", [9800, 10000, 10100], ids=["scarce", "neutral", "oversupplied"]
)
def test_feed_budget_accounts_for_post_buy_price_impact(policy, quoted_units, inventory):
    # Cash would buy quoted_units at today's displayed quote. Each actual buy
    # removes inventory first, increasing its own unit price in this market.
    cfg = linear_config(base=300, slope=1)
    initial_price = 10300 - inventory
    obs = observation(day=8, money=quoted_units * initial_price)
    obs["market"]["inventory"]["WHEAT"] = inventory
    for x in (2, 3, 4):
        obs["farms"][0]["tiles"][4][x] = animal("COW")
    action = decide(policy, obs, cfg)
    bought = sum(o[2] for o in action["market"] if o[:2] == ["BUY_PRODUCT", "WHEAT"])
    independent_cost = sum(initial_price + k for k in range(1, bought + 1))
    assert 0 < bought < quoted_units
    assert independent_cost <= obs["farms"][0]["money"]


@pytest.mark.parametrize("animal_name", ["COW", "SHEEP", "GOOSE"])
@pytest.mark.parametrize(
    "wheat_inventory", [9900, 9600, 9100], ids=["tight-feed", "scarce-feed", "feed-shock"]
)
def test_feed_price_shock_reduces_net_livestock_margin(policy, animal_name, wheat_inventory):
    normal = observation(day=8)
    shock = copy.deepcopy(normal)
    shock["market"]["inventory"]["WHEAT"] = wheat_inventory
    assert (
        policy["Planner"](shock, CONFIG).investment(animal_name)[1]
        < (policy["Planner"](normal, CONFIG).investment(animal_name)[1])
    )


@pytest.mark.parametrize("asset", ASSET_OUTPUT)
@pytest.mark.parametrize("window", ["cannot-mature", "already-final"])
def test_no_capital_for_production_beyond_terminal_horizon(policy, asset, window):
    day = 30 - FIRST[asset] if window == "cannot-mature" else 29
    score, margin = policy["Planner"](observation(day=day), CONFIG).investment(asset)
    assert score <= 0 and margin <= 0


@pytest.mark.parametrize("animal_name", ["COW", "SHEEP", "GOOSE"])
@pytest.mark.parametrize("cash", [0, 10], ids=["no-liquidity", "insufficient-feed-cash"])
def test_unfunded_feed_blocks_discretionary_expansion(policy, animal_name, cash):
    obs = observation(day=8, money=cash)
    obs["farms"][0]["tiles"][4][4] = animal(animal_name)
    action = decide(policy, obs)
    assert not any(o[0] in ("BUY_LAND", "BUY_ANIMAL", "BUY_SEED", "HIRE") for o in action["market"])


@pytest.mark.parametrize("profile", PROFILES)
def test_rival_displayed_cash_alone_does_not_change_profit_plan(policy, profile):
    low = observation(profile=profile)
    rich = copy.deepcopy(low)
    low["farms"][1]["money"] = 0
    rich["farms"][1]["money"] = 150000
    assert decide(policy, low) == decide(policy, rich)


@pytest.mark.parametrize("hand,cost", list(enumerate([1, 1, 2, 3, 5, 8, 13, 21, 34, 55, 89, 144])))
def test_labor_marginal_costs_prevent_linear_wage_assumptions(policy, hand, cost):
    assert policy["fib"](hand) == cost


@pytest.mark.parametrize("multiplier", [0, 1, 3, 20])
def test_idle_final_day_has_no_value_for_additional_hands(policy, multiplier):
    obs = observation(day=29)
    action = decide(policy, obs, {**CONFIG, "farmHandCostMult": multiplier})
    assert ["HIRE"] not in action["market"]


@pytest.mark.parametrize(
    "crop_name,age", [("WHEAT", 2), ("CARROT", 2), ("MELON", 6), ("TOMATO", 7), ("STRAWBERRY", 9)]
)
@pytest.mark.parametrize(
    "fertilizer_cost", [1000, 4000], ids=["valuable-fertilizer", "extreme-opportunity-cost"]
)
def test_bonus_does_not_justify_expensive_fertilizer(policy, crop_name, age, fertilizer_cost):
    obs = observation(day=age)
    obs["farms"][0]["tiles"][4][4] = crop(crop_name)
    obs["private"]["inventories"][0] = {"FERTILIZER": 1}
    cfg = {**CONFIG, "marketParams": {"FERTILIZER": {"base": fertilizer_cost}}}
    assert decide(policy, obs, cfg)["farmer"] == ["WATER"]


PAYOFFS = {"milk": (350, -150), "wool": (100, 100), "eggs": (50, 180), "idle": (0, 0)}


@pytest.mark.parametrize(
    "belief,expected,value",
    [
        ((1, 0), {"milk"}, 350),
        ((0, 1), {"eggs"}, 180),
        ((0.9, 0.1), {"milk"}, 300),
        ((0.5, 0.5), {"eggs"}, 115),
        ((0.1, 0.9), {"eggs"}, 167),
    ],
    ids=["benign-rival", "aggressive-rival", "mostly-benign", "unknown-even", "mostly-aggressive"],
)
def test_expected_profit_best_responses_have_independent_answers(belief, expected, value):
    actions, actual = best_reply(PAYOFFS, belief)
    assert actions == expected and actual == pytest.approx(value)


def test_maximin_protects_worst_case_cash():
    assert robust_reply(PAYOFFS) == ({"wool"}, 100)


def test_minimax_regret_uses_each_opponent_states_best_feasible_choice():
    assert robust_reply(PAYOFFS, regret=True) == ({"wool"}, 250)


@pytest.mark.parametrize("dominated", [(90, 90), (0, -10), (49, 179)])
def test_dominated_investment_never_beats_its_dominator(dominated):
    augmented = {**PAYOFFS, "dominated": dominated}
    assert "dominated" not in best_reply(augmented, (0.5, 0.5))[0]
    assert "dominated" not in robust_reply(augmented)[0]


@pytest.mark.parametrize(
    "cash,labor,space,expected",
    [
        (0, 6, 3, 0),
        (3, 6, 3, 5),
        (4, 6, 3, 6),
        (7, 6, 3, 11),
        (7, 2, 3, 6),
        (7, 6, 1, 5),
        (7, 0, 3, 0),
        (7, 6, 0, 0),
    ],
    ids=[
        "no-capital",
        "ratio-greedy-trap",
        "two-small-assets",
        "all-assets",
        "labor-bottleneck",
        "land-bottleneck",
        "no-actions",
        "no-land",
    ],
)
def test_exact_integer_portfolio_respects_scarce_capital_labor_and_land(
    cash, labor, space, expected
):
    offers = [("large", 3, 4, 1, 5), ("small-a", 2, 1, 1, 3), ("small-b", 2, 1, 1, 3)]
    assert exact_portfolio(offers, cash=cash, labor=labor, space=space)[0] == expected


@pytest.mark.parametrize("loss", [-1, -100, -1000])
def test_abstaining_dominates_negative_net_margin_even_with_idle_resources(loss):
    assert exact_portfolio([("loss", 1, 1, 1, loss)], cash=100, labor=100, space=100) == (0, {()})


@pytest.mark.parametrize("return_distance", [0, 1, 3])
@pytest.mark.parametrize("remaining", [1, 2, 5])
def test_terminal_assignment_has_an_explicit_cash_delivery_deadline(
    policy, return_distance, remaining
):
    target = (4 - return_distance, 4)
    obs = observation(day=29, hour=23 - remaining, workers=(target,))
    p = policy["Planner"](obs, CONFIG)
    p.add_job(target, [["HARVEST"]], 300, deadline=p.last, essential=True)
    p.allocate()
    optimum, _ = exact_assignment(
        [target],
        [{"pos": target, "value": 300, "actions": 1, "deadline": p.last}],
        now=p.step,
        final_action=p.last,
        access=((4, 4), (5, 4), (4, 5), (5, 5)),
    )
    actual = sum(job["value"] for job, _ in p.assignments.values())
    assert actual == optimum


@pytest.mark.optimization_gap
@pytest.mark.xfail(
    strict=True, raises=AssertionError, reason="OPT-001: slack priority loses 180 visit-value units"
)
def test_scheduler_prioritizes_best_deliverable_value_under_competing_deadlines(policy):
    obs = observation(hour=21)
    p = policy["Planner"](obs, CONFIG)
    visits = [
        {"pos": (2, 4), "value": 20, "actions": 1, "deadline": p.step + 2},
        {"pos": (3, 4), "value": 200, "actions": 1, "deadline": p.step + 2},
    ]
    for v in visits:
        p.add_job(v["pos"], [["HARVEST"]], v["value"], v["deadline"], True)
    p.allocate()
    optimum, _ = exact_assignment(p.positions, visits, now=p.step)
    actual = sum(j["value"] for j, _ in p.assignments.values())
    assert actual == optimum, f"Deadline-only dispatch retains {actual}, available value {optimum}"


@pytest.mark.optimization_gap
@pytest.mark.xfail(
    strict=True,
    raises=AssertionError,
    reason="OPT-002: greedy matching loses 150 visit-value units",
)
def test_matching_preserves_worker_with_exclusive_access_to_second_job(policy):
    obs = observation(hour=21, workers=((4, 3), (3, 4)))
    p = policy["Planner"](obs, CONFIG)
    visits = [
        {"pos": (4, 4), "value": 200, "actions": 1, "deadline": p.step + 1},
        {"pos": (4, 2), "value": 150, "actions": 1, "deadline": p.step + 1},
    ]
    for v in visits:
        p.add_job(v["pos"], [["HARVEST"]], v["value"], v["deadline"], True)
    p.allocate()
    optimum, _ = exact_assignment(p.positions, visits, now=p.step)
    actual = sum(j["value"] for j, _ in p.assignments.values())
    assert actual == optimum, (
        f"Greedy matching retains {actual}, joint assignment retains {optimum}"
    )


@pytest.mark.optimization_gap
@pytest.mark.xfail(
    strict=True,
    raises=AssertionError,
    reason="OPT-003: terminal capacity ordering leaves 270 feasible coins",
)
def test_final_capacity_is_reserved_for_highest_total_receipts(policy):
    obs = observation(day=29, hour=22, workers=((4, 4), (5, 4)))
    obs["private"]["shed"] = {"FERTILIZER": 98}
    obs["private"]["inventories"] = [{"WHEAT": 2}, {"MILK": 2}]
    cfg = {**CONFIG, "marketParams": {p: {"above_target": 0, "below_target": 0} for p in MARKETS}}
    action = decide(policy, obs, cfg)
    sales = {o[1]: o[2] for o in action["market"] if o[0] == "SELL"}
    actual = sales.get("WHEAT", 0) * 25 + sales.get("MILK", 0) * 160
    optimum, _ = exact_deposits([("WHEAT", 2), ("MILK", 2)], {"WHEAT": 25, "MILK": 160}, 2)
    assert actual == optimum, f"Sequential capacity allocation banks {actual}, feasible {optimum}"


@pytest.mark.optimization_gap
@pytest.mark.xfail(
    strict=True,
    raises=AssertionError,
    reason="OPT-004: forecast ignores observable rival service deterioration",
)
def test_neglected_rival_capacity_is_not_valued_as_fully_serviced_capacity(policy):
    healthy = observation(profile="dairy-specialist")
    neglected = copy.deepcopy(healthy)
    for row in neglected["farms"][1]["tiles"]:
        for tile in row:
            if isinstance(tile, dict) and "animal" in tile:
                tile.update(
                    fed_today=False, cared_today=False, consecutive_unfed=1, pending_care_bonus=0
                )
    neglected["farms"][1]["hands"] = []
    neglected["farms"][1]["hires_today"] = 0
    healthy_value = policy["Planner"](healthy, CONFIG).value_price("MILK")
    neglected_value = policy["Planner"](neglected, CONFIG).value_price("MILK")
    assert neglected_value > healthy_value, (neglected_value, healthy_value)


def test_all_exact_oracles_enforce_small_problem_limits():
    with pytest.raises(ValueError):
        exact_assignment([(0, 0)] * 5, [], now=0)
    with pytest.raises(ValueError):
        exact_portfolio([("asset", 0, 0, 0, 1)] * 9, cash=1, labor=1, space=1)
    with pytest.raises(ValueError):
        exact_deposits([("MILK", 7)], {"MILK": 1}, 100)
    with pytest.raises(ValueError):
        linear_sale_receipts(101)
