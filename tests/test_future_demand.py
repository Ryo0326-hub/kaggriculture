"""Scenario mechanics, accounting parity, information boundaries and investment risk."""

import ast
import runpy
from collections import Counter
from copy import deepcopy
from hashlib import sha256
from pathlib import Path

import pytest
from kaggle_environments import make
from kaggle_environments.envs.kaggriculture import kaggriculture as engine

from baselines import cycle_3
from scripts.make_demand_control import build
from scripts.report_demand import development_gate


@pytest.fixture
def demand(tmp_path):
    output = tmp_path / "main.py"
    build(cycle_3.__file__, output)
    return runpy.run_path(str(output))


def investment_state(day=3, hour=0):
    env = make("kaggriculture", configuration={"seed": 17})
    obs = env.state[0].observation
    obs.update(day=day, hour=hour, step=day * 24 + hour)
    obs.farms[0]["money"] = 30000
    obs.town["unlocked_shops"] = ["PET_CAFE"]
    return env, obs


def test_future_shop_paths_obey_schedule_cap_and_replacement(demand):
    env, obs = investment_state()
    paths = demand["future_demand_paths"](obs, env.configuration)
    assert len(paths) == 8
    assert all([d for d, _ in p["unlocks"]] == [6, 9, 12, 15, 18, 21, 24] for p in paths)
    for column in zip(*(p["unlocks"] for p in paths)):
        assert Counter(shop for _, shop in column) == Counter(engine.SHOPS.keys())
    assert any(len(set(s for _, s in p["unlocks"])) < 7 for p in paths)
    for p in paths:
        assert p["daily"][5] == cycle_3.observed_demand(obs, env.configuration)
        assert p["daily"][24] == p["daily"][29]
        assert all(v["FERTILIZER"] == 0 for v in p["daily"].values())


def test_demand_rates_match_actual_engine_consumption_with_duplicate_shops(demand):
    env, obs = investment_state()
    obs.town["unlocked_shops"] = ["YARN_STORE", "YARN_STORE", "PET_CAFE"]
    env.configuration.townShopSellInterval = 6
    env.configuration.townShopUnlockInterval = 2
    env.configuration.townCenterSellInterval = 12
    paths = demand["future_demand_paths"](obs, env.configuration)
    assert [d for d, _ in paths[0]["unlocks"]] == [4, 6, 8, 10, 12]
    existing = list(obs.town["unlocked_shops"])
    for path in paths:
        for day in (3, 4, 12, 29):
            obs.town["unlocked_shops"] = existing + [
                shop for date, shop in path["unlocks"] if date <= day
            ]
            obs.market["inventory"] = {c: 0 for c in cycle_3.MARKET}
            for step in range(day * 24 + 1, (day + 1) * 24 + 1):
                engine._town_consume(env, env.state, step)
            assert path["daily"][day] == {c: -v for c, v in obs.market["inventory"].items()}


@pytest.mark.parametrize("day,shops", [(24, ["YARN_STORE"] * 8), (29, [])])
def test_no_future_shops_collapses_to_incumbent_forecast(demand, day, shops):
    env, obs = investment_state(day)
    obs.town["unlocked_shops"] = shops
    paths = demand["future_demand_paths"](obs, env.configuration)
    assert len(paths) == 1 and paths[0]["unlocks"] == []
    new = demand["investment_projection"](obs, env.configuration, cycle_3.MARKET, paths)
    old = cycle_3.production_projection(obs, env.configuration, cycle_3.MARKET, routed=True)
    assert new["scenarios"] == [old]


@pytest.mark.parametrize("routed", [False, True])
def test_accounting_unchanged_for_constant_demand_with_real_inputs(demand, routed):
    env, obs = investment_state(9, 3)
    obs.farms[0]["tiles"][4][4] = engine._new_animal("COW", 1)
    obs.farms[0]["tiles"][3][4] = engine._new_plant("STRAWBERRY", 0, 24)
    obs.farms[0]["hires_today"] = 1
    obs.private["shed"].update(WHEAT=3, FERTILIZER=2, MILK=5)
    before = deepcopy(obs)
    additions = [dict(crop="MELON", planted_day=10, site=(3, 3), fertilized=True)]
    kwargs = dict(additions=additions, routed=routed, stress=10, land_cost=1000, cash=25000)
    old = cycle_3.production_projection(obs, env.configuration, cycle_3.MARKET, **kwargs)
    new = demand["production_projection"](obs, env.configuration, cycle_3.MARKET, **kwargs)
    assert new == old and obs == before
    path = {date: cycle_3.observed_demand(obs, env.configuration) for date in range(9, 30)}
    assert (
        demand["production_projection"](
            obs, env.configuration, cycle_3.MARKET, **kwargs, demand_path=path
        )
        == old
    )


def test_candidate_is_pure_and_independent_of_hidden_game_seed(demand):
    env, obs = investment_state()
    before = deepcopy(obs)
    policy = demand["expansion_investment"]
    args = (cycle_3.MARKET, [["PASS"]], [])
    first = policy(obs, env.configuration, *deepcopy(args))
    second = policy(obs, dict(env.configuration, seed=99999), *deepcopy(args))
    assert first == second and obs == before
    detail = first[1]
    assert detail["chosen"] is not None
    for option in detail["alternatives"]:
        scenarios = option["projection"]["scenarios"]
        margins = [
            p["value"] - b["value"] for p, b in zip(scenarios, detail["baseline"]["scenarios"])
        ]
        assert option["scenario_marginal_values"] == margins
        assert option["marginal_value"] == sum(margins) / len(margins)
        assert option["min_cash"] == min(p["min_cash"] for p in scenarios)
        if option["route_feasible"]:
            assert len({p["wages"] for p in scenarios}) == 1
            assert {p["investment_cost"] for p in scenarios} == {option["cost_now"]}


def test_low_cash_in_one_scenario_blocks_investment(demand, monkeypatch):
    env, obs = investment_state()

    def projection(obs, cfg, params, additions=(), **kwargs):
        low = kwargs["demand_path"][6]["WOOL"] > 1
        return {"value": 1000 if additions else 0, "min_cash": 149 if low else 10000}

    monkeypatch.setitem(
        demand["investment_projection"].__globals__, "production_projection", projection
    )
    orders, detail = demand["expansion_investment"](
        obs, env.configuration, cycle_3.MARKET, [["PASS"]], []
    )
    assert detail["alternatives"] and all(o["marginal_value"] > 0 for o in detail["alternatives"])
    assert orders == [] and detail["chosen"] is None
    assert all(not o["affordable"] for o in detail["alternatives"])


def test_scenarios_price_cash_paths_instead_of_mean_demand(demand):
    env, obs = investment_state()
    paths = demand["future_demand_paths"](obs, env.configuration)
    additions = [dict(animal="COW", placed_day=4, site=(4, 4))]
    forecast = demand["investment_projection"](
        obs, env.configuration, cycle_3.MARKET, paths, additions
    )
    mean_demand = {
        day: {c: sum(p["daily"][day][c] for p in paths) / len(paths) for c in cycle_3.MARKET}
        for day in range(3, 30)
    }
    certainty_equivalent = demand["production_projection"](
        obs, env.configuration, cycle_3.MARKET, additions, routed=True, demand_path=mean_demand
    )
    values = [p["value"] for p in forecast["scenarios"]]
    assert max(values) > min(values)
    assert forecast["value"] == sum(values) / len(values)
    # Rounded/capped price curves make averaging cash differ from pricing at the mean inventory.
    assert abs(forecast["value"] - certainty_equivalent["value"]) > 1


def test_only_forecast_and_investment_functions_change(tmp_path):
    output = tmp_path / "main.py"
    build(cycle_3.__file__, output)
    assert sha256(output.read_bytes()).hexdigest() == (
        "3f2691bf276175c6ba43d1ecf657fcb49a5a7f21f4f9e53b8ed5971babee3456"
    )

    def functions(code):
        return {n.name: ast.dump(n) for n in ast.parse(code).body if isinstance(n, ast.FunctionDef)}

    old = functions(Path(cycle_3.__file__).read_text())
    new = functions(output.read_text())
    changed = {name for name in old if old[name] != new[name]}
    assert changed == {"production_projection", "expansion_investment"}
    assert new.keys() - old.keys() == {"future_demand_paths", "investment_projection"}
    with pytest.raises(FileExistsError):
        build(cycle_3.__file__, output)
    with pytest.raises(ValueError, match="frozen"):
        build(output, tmp_path / "other.py")


@pytest.mark.parametrize("failure", ["tie", "execution", "stock", "crop", "runtime"])
def test_development_gate_does_not_advance_failed_candidates(failure):
    reference = {"summary": {"match_score": 2 / 3}}
    candidate = {
        "summary": {"match_score": 0.75, "errors": 0, "decision_max_seconds": 0.4},
        "terminal_units": 0,
        "operational_totals": {"unplanned_crop_losses": 0},
    }
    assert development_gate(candidate, reference)["advance_to_fresh_evaluation"]
    if failure == "tie":
        candidate["summary"]["match_score"] = 2 / 3
    elif failure == "execution":
        candidate["summary"]["errors"] = 1
    elif failure == "stock":
        candidate["terminal_units"] = 1
    elif failure == "crop":
        candidate["operational_totals"]["unplanned_crop_losses"] = 1
    else:
        candidate["summary"]["decision_max_seconds"] = 1
    assert not development_gate(candidate, reference)["advance_to_fresh_evaluation"]
