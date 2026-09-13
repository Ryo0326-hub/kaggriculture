"""Research-led fixed scenarios. See docs/RESEARCH_SCENARIO_TESTS.md.

Never imports an engine, produces a next observation, or tunes the policy.
All payoff tables are assumptions and all cash witnesses are one-decision
arithmetic, not measured full-game profits.
"""

import copy
import runpy
from fractions import Fraction

import pytest
from test_optimization import CONFIG, MARKETS, SHOPS, animal, crop, decide, observation

from scripts.make_fresh_cycle1 import SOURCE
from scripts.optimization_oracles import (
    best_reply,
    exact_portfolio,
    linear_sale_receipts,
    robust_reply,
)
from scripts.research_oracles import terminal_deposit_choice, terminal_order_choice


class OptimizationTargetGap(AssertionError):
    """Only the final unmet economic target, not a failed precondition or oracle."""


def require_target(condition, evidence):
    if not condition:
        raise OptimizationTargetGap(evidence)


@pytest.fixture(scope="module")
def module():
    return runpy.run_path(str(SOURCE))


@pytest.fixture
def policy(module):
    module["agent"].__globals__["_MEMORY"].clear()
    return module


def flat_config(**patch):
    return {
        **CONFIG,
        "marketParams": {p: {"above_target": 0, "below_target": 0} for p in MARKETS},
        **patch,
    }


def banked(action, prices):
    return sum(o[2] * prices[o[1]] for o in action["market"] if o[0] == "SELL")


@pytest.mark.parametrize(
    "product,base,scale,target",
    [
        ("CARROT", 35, 450, Fraction(1)),
        ("TOMATO", 60, 200, Fraction(2, 5)),
        ("EGG", 50, 332, Fraction(2, 5)),
    ],
)
@pytest.mark.parametrize(
    "deficit",
    [Fraction(1, 2), Fraction(1), Fraction(3, 2), Fraction(2)],
    ids=["before-knee", "at-knee", "past-knee", "severe-scarcity"],
)
def test_demand_shock_uses_nonlinear_scarcity_knee(policy, product, base, scale, target, deficit):
    # Independent rational formula, not a call to the policy's shape helper.
    expected = round(base * (1 + target * (deficit + 8 * max(0, deficit - 1) ** 2)))
    actual = policy["quoted_price"](product, 10000 - int(scale * deficit))
    assert actual == expected


@pytest.mark.parametrize("product", MARKETS)
def test_observed_market_parameters_override_configuration(policy, product):
    obs = observation()
    obs["market"]["inventory"][product] = 1234
    obs["market"]["params"] = {product: {"base": 77, "I0": 1234}}
    cfg = {**CONFIG, "marketParams": {product: {"base": 999, "I0": 10000}}}
    assert policy["Planner"](obs, cfg).prices[product] == 77


@pytest.mark.parametrize("shop,item,default_daily", SHOPS, ids=[row[0] for row in SHOPS])
@pytest.mark.parametrize(
    "tpd,shop_period,center_period",
    [(24, 6, 12), (12, 4, 24)],
    ids=["slower-shops-faster-center", "short-day"],
)
def test_duplicate_shop_demand_respects_configured_clock(
    policy, shop, item, default_daily, tpd, shop_period, center_period
):
    obs = observation(day=8)
    obs["town"]["unlocked_shops"] = [shop] * 8
    cfg = {
        **CONFIG,
        "turnsPerDay": tpd,
        "townShopSellInterval": shop_period,
        "townCenterSellInterval": center_period,
    }
    p = policy["Planner"](obs, cfg)
    multiplier = default_daily // 6
    expected = Fraction(tpd, center_period) + 8 * multiplier * Fraction(tpd, shop_period)
    assert p.demand[item] == expected
    assert p.demand["FERTILIZER"] == 0


REPEATER_NIGHTS = [
    ("TOMATO", 6, False),
    ("TOMATO", 7, True),
    ("TOMATO", 8, True),
    ("TOMATO", 9, True),
    ("TOMATO", 10, True),
    ("TOMATO", 11, False),
    ("TOMATO", 12, False),
    ("STRAWBERRY", 8, False),
    ("STRAWBERRY", 9, True),
    ("STRAWBERRY", 10, False),
    ("STRAWBERRY", 11, True),
    ("STRAWBERRY", 13, True),
    ("STRAWBERRY", 15, True),
    ("STRAWBERRY", 16, False),
]


@pytest.mark.parametrize(
    "name,day,expected",
    REPEATER_NIGHTS,
    ids=[f"{n}-age{d}-{'produces' if e else 'no-production'}" for n, d, e in REPEATER_NIGHTS],
)
def test_repeater_water_value_uses_finite_production_calendar(policy, name, day, expected):
    obs = observation(day=day)
    assert policy["Planner"](obs, CONFIG).production_night(crop(name)) is expected


@pytest.mark.parametrize("name,retired_age", [("TOMATO", 12), ("STRAWBERRY", 17)])
@pytest.mark.parametrize("count", [1, 12], ids=["one-retired-plant", "retired-specialist"])
def test_retired_rival_repeaters_have_no_new_production_capacity(policy, name, retired_age, count):
    obs = observation(day=retired_age)
    for i in range(count):
        obs["farms"][1]["tiles"][i // 10][i % 10] = crop(name, quantity=0)
    assert policy["Planner"](obs, CONFIG).supply[name] == 0


@pytest.mark.parametrize("name,held", [("COW", 6), ("SHEEP", 6), ("GOOSE", 4)])
@pytest.mark.parametrize("quantity", [0, 1], ids=["no-held-output", "valuable-held-output"])
def test_survival_feed_precedes_cash_when_escape_is_imminent(policy, name, held, quantity):
    obs = observation(day=12, hour=23, money=0)
    obs["farms"][0]["tiles"][4][4] = animal(name, consecutive_unfed=1, yield_units=held * quantity)
    obs["private"]["inventories"][0] = {"WHEAT": 1}
    assert decide(policy, obs)["farmer"] == ["FEED"]


@pytest.mark.parametrize("name,cap,day", [("COW", 6, 9), ("SHEEP", 6, 8), ("GOOSE", 4, 5)])
@pytest.mark.parametrize("free", [0, 1], ids=["held-cap-full", "one-slot-left"])
def test_held_output_is_collected_before_optional_care(policy, name, cap, day, free):
    obs = observation(day=day, hour=22, money=0)
    obs["farms"][0]["tiles"][4][4] = animal(
        name, fed_today=True, yield_units=cap - free, pending_care_bonus=2
    )
    # Today's CARE cannot increase tonight's payout; collection also frees capacity.
    assert decide(policy, obs)["farmer"] == ["HARVEST"]


@pytest.mark.parametrize("tpd,steps", [(24, 720), (12, 360), (24, 710), (8, 160)])
@pytest.mark.parametrize("name", ["COW", "SHEEP", "GOOSE"])
def test_final_action_has_no_feed_or_capital_reserve_on_alternative_clocks(
    policy, tpd, steps, name
):
    day, hour = divmod(steps - 2, tpd)
    obs = observation(day=day, hour=hour, money=0)
    obs["farms"][0]["tiles"][4][4] = animal(name, consecutive_unfed=1)
    obs["private"]["shed"] = {"WHEAT": 2}
    cfg = flat_config(turnsPerDay=tpd, episodeSteps=steps)
    action = decide(policy, obs, cfg)
    assert action["market"] == [["SELL", "WHEAT", 2]]
    assert action["farmer"] == ["PASS"]


@pytest.mark.parametrize(
    "goods",
    [
        {"MELON": 1, "WOOL": 1, "MILK": 1},
        {"STRAWBERRY": 3, "FERTILIZER": 3, "TOMATO": 3},
        {"EGG": 2, "CARROT": 2, "WHEAT": 2},
    ],
    ids=["premium-lots", "midprice-lots", "staple-lots"],
)
@pytest.mark.parametrize("slots", [1, 2, 3])
def test_order_capacity_control_maximizes_terminal_receipts_for_equal_lots(policy, goods, slots):
    obs = observation(day=29, hour=22)
    obs["private"]["shed"] = goods.copy()
    prices = {p: values[0] for p, values in MARKETS.items()}
    action = decide(policy, obs, flat_config(maxMarketOrdersPerTurn=slots))
    expected, _ = terminal_order_choice(goods, prices, slots)
    assert banked(action, prices) == expected


@pytest.mark.parametrize(
    "room,expected",
    [
        (0, 0),
        (1, 160),
        (2, 320),
        pytest.param(
            3,
            345,
            marks=pytest.mark.optimization_gap,
        ),
        (4, 370),
    ],
)
def test_terminal_mixed_deposit_control_respects_cash_and_capacity(policy, room, expected):
    goods, prices = {"MILK": 2, "WHEAT": 2}, {"MILK": 160, "WHEAT": 25}
    obs = observation(day=29, hour=22)
    obs["private"]["shed"] = {"FERTILIZER": 100 - room}
    obs["private"]["inventories"][0] = goods.copy()
    action = decide(policy, obs, flat_config())
    optimum, _ = terminal_deposit_choice(goods, prices, room)
    assert optimum == expected
    sales = {o[1]: o[2] for o in action["market"] if o[0] == "SELL"}
    actual = sum(sales.get(p, 0) * prices[p] for p in prices)
    require_target(actual == optimum, f"Mixed deposit banks {actual}; feasible optimum {optimum}")


@pytest.mark.parametrize("rival", [2, 8, 20], ids=["small-lot", "matched-lot", "dump"])
@pytest.mark.parametrize("base,slope", [(100, 1), (100, 3)], ids=["deep-market", "thin-market"])
def test_rival_sale_order_position_changes_receipts(rival, base, slope):
    # Three alternative assumptions, not three steps of a simulated market.
    ours = 8
    first = linear_sale_receipts(ours, base=base, slope=slope)
    simultaneous = linear_sale_receipts(ours, rival, base=base, slope=slope)
    after = linear_sale_receipts(ours, base=base, slope=slope, inventory=10000 + rival)
    assert first > simultaneous > after
    assert first == sum(base - slope * k for k in range(ours))
    assert after == first - ours * slope * rival  # These cases never hit the floor.


@pytest.mark.parametrize(
    "item,scale", [("MILK", 122), ("WOOL", 105), ("MELON", 300), ("STRAWBERRY", 100)]
)
def test_floor_still_rewards_liquidation_despite_unobservable_rival_sales(policy, item, scale):
    obs = observation(day=29, hour=22)
    obs["market"]["inventory"][item] = 10000 + 3 * scale
    obs["private"]["shed"] = {item: 12}
    p = policy["Planner"](obs, CONFIG)
    assert p.prices[item] == 1
    action = decide(policy, obs)
    assert action["market"] == [["SELL", item, 12]]
    for rival_sale in (0, 1, 12, 100):
        # Alternative hidden quantities at an already reached floor. Floor sales
        # cannot increase public inventory; no future observation is fabricated.
        assert linear_sale_receipts(12, rival_sale, base=1, slope=0) == 12


FUTURE_SHOPS = {"berries": (140, 0), "dairy": (0, 140), "flexible": (60, 60)}


@pytest.mark.parametrize(
    "berry_probability,winner,profit",
    [
        (Fraction(0), "dairy", 140),
        (Fraction(1, 4), "dairy", 105),
        (Fraction(1, 2), "either", 70),
        (Fraction(3, 4), "berries", 105),
        (Fraction(1), "berries", 140),
    ],
)
def test_unrevealed_shop_choice_does_not_receive_perfect_information_profit(
    berry_probability, winner, profit
):
    belief = (berry_probability, 1 - berry_probability)
    choices, value = best_reply(FUTURE_SHOPS, belief)
    assert choices == ({"berries", "dairy"} if winner == "either" else {winner})
    assert value == profit
    perfect_information = sum(
        p * max(column)
        for p, column in zip(belief, zip(*FUTURE_SHOPS.values(), strict=True), strict=True)
    )
    assert perfect_information == 140
    assert perfect_information - value == 140 - profit


@pytest.mark.parametrize(
    "risk_set,belief,worst",
    [
        ([(0, 0), (1, 1)], [Fraction(1, 2)] * 2, -40),
        ([(0, 1), (1, 0)], [Fraction(1, 2)] * 2, 30),
        ([(0, 0), (0, 1), (1, 0), (1, 1)], [Fraction(1, 4)] * 4, -40),
    ],
    ids=["correlated-feed-and-price-shocks", "mutually-exclusive-shocks", "independent-shocks"],
)
def test_equal_marginal_shocks_have_different_portfolio_downside(risk_set, belief, worst):
    risky = tuple(100 - 70 * feed - 70 * output for feed, output in risk_set)
    payoffs = {"livestock": risky, "cash-reserve": (20,) * len(risky)}
    for column in (0, 1):
        assert sum(
            p * state[column] for p, state in zip(belief, risk_set, strict=True)
        ) == Fraction(1, 2)
    assert best_reply(payoffs, belief) == ({"livestock"}, 30)
    assert min(risky) == worst
    robust = ({"cash-reserve"}, 20) if worst < 20 else ({"livestock"}, 30)
    assert robust_reply(payoffs) == robust


OFFERS = [("wheat", 100, 2, 1, 40), ("dairy", 200, 3, 1, 90), ("berries", 200, 2, 2, 110)]


@pytest.mark.parametrize(
    "resource,increment,expected_gain",
    [
        ("cash", 100, 0),
        ("cash", 200, 0),
        ("labor", 1, 20),
        ("labor", 2, 20),
        ("space", 1, 40),
        ("space", 2, 40),
    ],
)
def test_integer_resource_value_is_a_threshold_not_a_fixed_penalty(
    resource, increment, expected_gain
):
    budget = {"cash": 300, "labor": 4, "space": 2}
    baseline, _ = exact_portfolio(OFFERS, **budget)
    assert baseline == 110
    budget[resource] += increment
    expanded, _ = exact_portfolio(OFFERS, **budget)
    assert expanded - baseline == expected_gain


def test_joint_resource_relaxation_can_be_more_valuable_than_each_alone():
    baseline, _ = exact_portfolio(OFFERS, cash=300, labor=4, space=3)
    cash_only, _ = exact_portfolio(OFFERS, cash=400, labor=4, space=3)
    labor_only, _ = exact_portfolio(OFFERS, cash=300, labor=5, space=3)
    joint, winners = exact_portfolio(OFFERS, cash=400, labor=5, space=3)
    # Cash alone and labor alone have zero marginal value; together they add 50.
    assert baseline == cash_only == labor_only == 150
    assert joint - baseline == 50
    assert winners == {("dairy", "berries")}


@pytest.mark.optimization_gap
def test_terminal_order_cap_selects_total_receipts_not_unit_price(policy):
    obs = observation(day=29, hour=22)
    obs["private"]["shed"] = {"MILK": 1, "WHEAT": 20}
    cfg = flat_config(maxMarketOrdersPerTurn=1)
    action = decide(policy, obs, cfg)
    prices = {"MILK": 160, "WHEAT": 25}
    expected, winners = terminal_order_choice(obs["private"]["shed"], prices, 1)
    assert expected == 500 and winners == {("WHEAT",)}
    actual = banked(action, prices)
    require_target(actual == expected, f"One order banks {actual}; feasible optimum {expected}")


@pytest.mark.optimization_gap
def test_single_worker_terminal_deposit_selects_total_receipts_not_unit_price(policy):
    obs = observation(day=29, hour=22)
    obs["private"]["shed"] = {"FERTILIZER": 92}
    obs["private"]["inventories"][0] = {"MILK": 1, "WHEAT": 8}
    prices = {"MILK": 160, "WHEAT": 25}
    expected, _ = terminal_deposit_choice(obs["private"]["inventories"][0], prices, 8)
    # DROP also uses the otherwise-idle space: 160 + 7*25 = 335.
    assert expected == 335
    action = decide(policy, obs, flat_config())
    sales = {o[1]: o[2] for o in action["market"] if o[0] == "SELL"}
    actual = sum(sales.get(p, 0) * prices[p] for p in prices)
    require_target(actual == expected, f"Mixed cargo banks {actual}; feasible optimum {expected}")


@pytest.mark.optimization_gap
@pytest.mark.parametrize("name,first", [("TOMATO", 8), ("STRAWBERRY", 10)])
def test_immature_rival_repeaters_do_not_depress_one_day_output_price(policy, name, first):
    newly_planted = observation(day=12)
    productive = copy.deepcopy(newly_planted)
    for i in range(12):
        newly_planted["farms"][1]["tiles"][i // 10][i % 10] = crop(name, planted=12, quantity=0)
        productive["farms"][1]["tiles"][i // 10][i % 10] = crop(
            name, planted=13 - first, quantity=0
        )
    new_value = policy["Planner"](newly_planted, CONFIG).value_price(name, horizon=1)
    mature_value = policy["Planner"](productive, CONFIG).value_price(name, horizon=1)
    require_target(
        new_value > mature_value, f"Immature value {new_value}; productive {mature_value}"
    )


@pytest.mark.parametrize(
    "goods,room,expected,witness",
    [
        ({"MILK": 1, "WHEAT": 8}, 8, 335, ("DROP",)),
        ({"WHEAT": 8, "MILK": 1}, 8, 200, ("PLACE", "WHEAT", 8)),
        ({"MILK": 2, "WHEAT": 2}, 3, 345, ("DROP",)),
        ({"MILK": 2, "WHEAT": 2}, 4, 370, ("DROP",)),
        ({"MILK": 2, "WHEAT": 2}, 0, 0, ("PASS",)),
    ],
    ids=[
        "milk-first-overflow",
        "wheat-first-selective-place",
        "partly-filled-drop",
        "all-cargo-fits",
        "full-shed",
    ],
)
def test_deposit_oracle_has_hand_calculated_cash_witnesses(goods, room, expected, witness):
    before = copy.deepcopy(goods)
    value, actions = terminal_deposit_choice(goods, {"MILK": 160, "WHEAT": 25}, room)
    assert goods == before
    assert value == expected and witness in actions


@pytest.mark.parametrize("slots,expected", [(0, 0), (1, 500), (2, 700), (3, 860)])
def test_order_oracle_has_hand_calculated_cash_witnesses(slots, expected):
    goods = {"MILK": 1, "WHEAT": 20, "FERTILIZER": 2}
    before = goods.copy()
    value, _ = terminal_order_choice(goods, {"MILK": 160, "WHEAT": 25, "FERTILIZER": 100}, slots)
    assert goods == before
    assert value == expected


@pytest.mark.parametrize(
    "call",
    [
        lambda: terminal_order_choice({str(i): 1 for i in range(10)}, {}, 1),
        lambda: terminal_order_choice({"MILK": 101}, {"MILK": 160}, 1),
        lambda: terminal_order_choice({"MILK": 1}, {"MILK": 160}, 11),
        lambda: terminal_deposit_choice({"MILK": 1}, {"MILK": 160}, 101),
        lambda: terminal_deposit_choice({"MILK": -1}, {"MILK": 160}, 1),
        lambda: terminal_deposit_choice({"MILK": 1}, {"MILK": 0}, 1),
    ],
    ids=["products-cap", "units-cap", "order-cap", "space-cap", "negative-quantity", "bad-price"],
)
def test_research_oracles_reject_unbounded_or_invalid_inputs(call):
    with pytest.raises(ValueError):
        call()
