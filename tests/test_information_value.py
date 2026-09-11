"""Information is revealed by the next shop, not by a sampled hidden supply case."""

import ast
import runpy
from copy import deepcopy
from hashlib import sha256
from pathlib import Path

import pytest
from kaggle_environments import make
from kaggle_environments.envs.kaggriculture import kaggriculture as engine

from baselines import cycle_3
from scripts.make_information_control import build


@pytest.fixture
def information(tmp_path):
    output = tmp_path / "main.py"
    build(cycle_3.__file__, output)
    return runpy.run_path(str(output))


def state(day=3, hour=0):
    env = make("kaggriculture", configuration={"seed": 17})
    obs = env.state[0].observation
    obs.update(day=day, hour=hour, step=day * 24 + hour)
    obs.farms[0]["money"] = 30000
    return env, obs


def test_next_shop_branches_obey_information_time_and_instance_cap(information):
    env, obs = state(2)
    context = information["next_shop_context"](obs, env.configuration)
    assert context["next_day"] == 3
    assert {b["shop"] for b in context["branches"]} == set(engine.SHOPS)
    for b in context["branches"]:
        assert b["demand"][2] == cycle_3.observed_demand(obs, env.configuration)
        following = deepcopy(obs)
        following.town["unlocked_shops"].append(b["shop"])
        assert b["demand"][3] == cycle_3.observed_demand(following, env.configuration)
        assert b["demand"][29] == b["demand"][3]  # later openings intentionally unmodeled
    obs.update(day=3, step=72)
    assert information["next_shop_context"](obs, env.configuration)["next_day"] == 6
    obs.town["unlocked_shops"] = ["YARN_STORE"] * 8
    context = information["next_shop_context"](obs, env.configuration)
    assert context["next_day"] is None and len(context["branches"]) == 1
    assert context["branches"][0]["demand"][3]["WOOL"] == 97


def test_growth_stress_respects_observed_species_cash_land_and_horizon(information):
    env, obs = state(4)
    farm = obs.farms[1]
    farm["tiles"][0][0] = engine._new_plant("MELON", 0, 24)
    farm["tiles"][0][1] = engine._new_animal("SHEEP", 0)
    farm["money"] = 1200
    before = deepcopy(obs)
    growth = information["rival_growth_stress"](obs, env.configuration)
    assert [c.get("crop") for c in growth[:4]] == ["MELON"] * 4
    assert growth[-1] == {"animal": "SHEEP", "placed_day": 5}
    assert all(c.get("planted_day", 5) == 5 for c in growth)
    assert obs == before
    farm["money"] = 500
    assert len(information["rival_growth_stress"](obs, env.configuration)) == 4
    farm["money"] = 150
    assert information["rival_growth_stress"](obs, env.configuration) == []
    farm["money"] = 30000
    obs.update(day=28, step=672)
    assert information["rival_growth_stress"](obs, env.configuration) == []
    obs.update(day=4, step=96)
    for y, row in enumerate(farm["tiles"]):
        for x, tile in enumerate(row):
            if tile is None:
                row[x] = engine._new_plant("MELON", 0, 24)
    assert information["rival_growth_stress"](obs, env.configuration) == []


@pytest.mark.parametrize("routed", [False, True])
def test_default_and_cached_forecasts_preserve_incumbent_accounting(information, routed):
    env, obs = state(9, 3)
    obs.farms[0]["tiles"][4][4] = engine._new_animal("COW", 0)
    obs.farms[0]["tiles"][3][4] = engine._new_plant("STRAWBERRY", 0, 24)
    obs.farms[0]["hires_today"] = 1
    obs.private["shed"].update(WHEAT=3, FERTILIZER=2, MILK=5)
    kwargs = dict(
        additions=[dict(crop="MELON", planted_day=10, site=(3, 3), fertilized=True)],
        routed=routed,
        stress=10,
        land_cost=1000,
        cash=25000,
    )
    old = cycle_3.production_projection(obs, env.configuration, cycle_3.MARKET, **kwargs)
    fn = information["production_projection"]
    assert fn(obs, env.configuration, cycle_3.MARKET, **kwargs) == old
    assert fn(obs, env.configuration, cycle_3.MARKET, **kwargs, quotes={}) == old
    assert fn(obs, env.configuration, cycle_3.MARKET, **kwargs, quotes={}, work_cache={}) == old


def test_rival_additions_match_visible_asset_output_without_charging_our_cash(information):
    env, obs = state(5)
    obs.farms[0]["tiles"][4][4] = engine._new_animal("COW", 0)
    additions = [dict(animal="COW", placed_day=6), dict(crop="WHEAT", planted_day=6)]
    stressed = information["production_projection"](
        obs, env.configuration, cycle_3.MARKET, rival_additions=additions
    )
    visible = deepcopy(obs)
    visible.farms[1]["tiles"][0][0] = engine._new_animal("COW", 6)
    visible.farms[1]["tiles"][0][1] = engine._new_plant("WHEAT", 6, 24)
    equivalent = cycle_3.production_projection(visible, env.configuration, cycle_3.MARKET)
    assert stressed == equivalent
    assert stressed["investment_cost"] == 0
    ordinary = cycle_3.production_projection(obs, env.configuration, cycle_3.MARKET)
    assert stressed["wages"] == ordinary["wages"]
    assert stressed["feed_cost"] != ordinary["feed_cost"]  # rival net wheat demand is included


@pytest.mark.parametrize("crowded", [False, True])
def test_shared_work_cache_matches_independent_scenario_forecasts(
    information, monkeypatch, crowded
):
    env, obs = state(3)
    obs.farms[0]["tiles"][4][4] = engine._new_animal("COW", 0)
    obs.farms[1]["tiles"][4][4] = engine._new_animal("COW", 0)
    obs.farms[1]["tiles"][3][4] = engine._new_plant("WHEAT", 0, 24)
    if crowded:
        for row in obs.farms[0]["tiles"]:
            for x in range(len(row)):
                row[x] = engine._new_plant("STRAWBERRY", 0, 24)
    context = information["next_shop_context"](obs, env.configuration)
    fn = information["continuation_forecasts"]
    cached = fn(obs, env.configuration, cycle_3.MARKET, context, {})
    original = fn.__globals__["production_projection"]

    def without_cache(*args, **kwargs):
        kwargs["work_cache"] = None
        return original(*args, **kwargs)

    monkeypatch.setitem(fn.__globals__, "production_projection", without_cache)
    assert cached == fn(obs, env.configuration, cycle_3.MARKET, context, {})
    if crowded:
        assert all(not p["route_feasible"] for branch in cached for p in branch)


def test_delayed_land_seeds_and_service_are_paid_at_correct_dates(information):
    env, obs = state(3)
    context = information["next_shop_context"](obs, env.configuration)
    additions = [dict(crop="WHEAT", planted_day=4, site=(3, 3), fertilized=True)]
    forecasts = information["continuation_forecasts"](
        obs, env.configuration, cycle_3.MARKET, context, {}, additions, 1000, 6
    )
    for branch in forecasts:
        for p in branch:
            assert p["investment_cost"] == 1010
            days = {d["day"]: d for d in p["daily"]}
            assert all(days[d]["spending_before_receipts"] == 0 for d in (3, 4, 5))
            assert days[6]["spending_before_receipts"] == 1010
            assert all(days[d]["credited_receipts"] == 0 for d in range(3, 11))
            assert days[11]["credited_receipts"] > 0


def forecast(value, cash=1000):
    return {"value": value, "min_cash": cash, "daily": [{"day": 0}]}


@pytest.mark.parametrize("rival_wheat,herd", [(6, 3), (2, 3), (0, 3)])
def test_rival_wheat_is_fed_or_sold_once(information, rival_wheat, herd):
    env, obs = state(4)
    for side, quantity in ((0, 6), (1, rival_wheat)):
        tile = engine._new_plant("WHEAT", 0, 24)
        tile.update(yield_units=quantity, watered_today=True)
        obs.farms[side]["tiles"][0][0] = tile
    for x in range(herd):
        obs.farms[1]["tiles"][1][x] = engine._new_animal("COW", 0)
    projection = information["production_projection"](
        obs, env.configuration, cycle_3.MARKET, net_rival_wheat=True
    )
    inventory = obs.market["inventory"]["WHEAT"] - 1  # one center unit per full day
    inventory -= max(0, herd - rival_wheat)
    rival_sales = max(0, rival_wheat - herd)
    expected = 0.8 * cycle_3.batch_revenue("WHEAT", inventory + rival_sales / 2, 6, cycle_3.MARKET)
    assert projection["daily"][0]["credited_receipts"] == expected


def test_supply_risk_is_applied_to_paired_marginal_values(information):
    result = information["paired_continuation"](
        [[forecast(150), forecast(340)]], [[forecast(100), forecast(300)]]
    )
    assert result["marginal_value"] == 40  # not min(150,340) - min(100,300)
    assert result["branch_feasible"] == [True]
    result = information["paired_continuation"](
        [[forecast(150, 149), forecast(340)]], [[forecast(100), forecast(300)]]
    )
    assert result["branch_feasible"] == [False]


def test_waiting_cannot_choose_using_unobserved_supply_case(information, monkeypatch):
    env, obs = state(2)
    namespace = information["information_investment"].__globals__
    monkeypatch.setitem(
        namespace,
        "next_shop_context",
        lambda obs, cfg: {
            "next_day": 3,
            "branches": [{"shop": "BAKERY"}, {"shop": "YARN_STORE"}],
            "supply_cases": [[], [{}]],
        },
    )

    def projections(obs, cfg, params, context, quotes, additions=(), land=0, buy_day=None):
        if not additions:
            values = [[0, 0], [0, 0]]
        elif buy_day is None:
            values = [[20, 20], [20, 20]]
        elif additions[0]["crop"] == "WHEAT":
            values = [[100, -100], [80, 80]]
        else:
            values = [[-100, 100], [40, 40]]
        return [[forecast(v) for v in branch] for branch in values]

    monkeypatch.setitem(namespace, "continuation_forecasts", projections)
    options = [
        (0, [["BUY_SEED", c, 1]], [dict(crop=c, planted_day=3, site=(3, 3))])
        for c in ("WHEAT", "MELON")
    ]
    orders, report = information["information_investment"](
        obs, env.configuration, cycle_3.MARKET, options, [], {"alternatives": [], "chosen": None}
    )
    assert report["wait_value"] == 40  # not (100 + 80) / 2 from supply clairvoyance
    assert report["wait_choices"][0] is None
    assert report["wait_choices"][1]["orders"] == [["BUY_SEED", "WHEAT", 1]]
    assert report["immediate_value"] == 20 and report["decision"] == "wait_for_shop"
    assert not orders and report["chosen"] is None


def test_terminal_horizon_and_seed_independence(information):
    env, obs = state(29)
    before = deepcopy(obs)
    fn = information["expansion_turn"]
    a = fn(obs, env.configuration)
    assert a == fn(obs, dict(env.configuration, seed=99999)) and obs == before
    report = a[1]["expansion"]
    assert report["information"]["next_day"] is None
    assert report["decision"] == "no_profitable_purchase"
    assert not report["delayed_alternatives"]


def test_only_investment_and_projection_functions_change(tmp_path):
    output = tmp_path / "main.py"
    build(cycle_3.__file__, output)
    assert sha256(output.read_bytes()).hexdigest() == (
        "6365a19af351075e5942654a52a4b2fd6f75678547adc4d429eaafc9dee56724"
    )

    def functions(code):
        return {n.name: ast.dump(n) for n in ast.parse(code).body if isinstance(n, ast.FunctionDef)}

    old, new = functions(Path(cycle_3.__file__).read_text()), functions(output.read_text())
    assert {n for n in old if old[n] != new[n]} == {"production_projection", "expansion_investment"}
    with pytest.raises(FileExistsError):
        build(cycle_3.__file__, output)
    with pytest.raises(ValueError, match="frozen"):
        build(output, tmp_path / "other.py")
