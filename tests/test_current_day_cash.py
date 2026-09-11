"""Only cash admission changes; held inputs and paid labor are never charged twice."""

import ast
import json
import runpy
from copy import deepcopy
from pathlib import Path

import pytest
from kaggle_environments import make

from baselines import cycle_3
from scripts.benchmark_continuation import audit_continuation
from scripts.make_cash_control import build


@pytest.fixture
def policy(tmp_path):
    output = tmp_path / "main.py"
    build(cycle_3.__file__, output)
    return runpy.run_path(str(output))


@pytest.fixture
def state():
    return json.loads((Path(__file__).parent / "fixtures/cash-144.json").read_text())


def quote(policy, state):
    obs, cfg = state["observation"], state["configuration"]
    action, detail = policy["expansion_turn"](obs, cfg)
    option = next(
        o
        for o in detail["expansion"]["alternatives"]
        if o["orders"] == [["BUY_ANIMAL", "SHEEP", 1]]
    )
    return action, option


def test_missing_feed_and_installation_hire_explain_cash_gap(policy, state):
    before = deepcopy(state)
    old_action, old = cycle_3.expansion_turn(state["observation"], state["configuration"])
    action, option = quote(policy, state)
    assert state == before
    assert old["expansion"]["chosen"]["min_cash"] == 155
    bound = option["current_day_cash"]
    assert bound["extra_feed_units"] == 2
    assert bound["held_feed"] == 10 and bound["feed_target"] == 12
    assert bound["extra_feed_cash"] == 68
    assert bound["worker_target"] == 9 and bound["paid_or_planned_hires"] == 7
    assert bound["extra_hires"] == 1 and bound["extra_wage_cash"] == 21
    assert bound["min_cash"] == 66  # Recorded continuation reaches 64 after rival trades.
    assert not option["affordable"]
    assert action["farmer"] == old_action["farmer"] and action["hands"] == old_action["hands"]
    assert action["market"][:-1] == old_action["market"][:-1]


def test_projection_values_and_abundant_cash_choices_stay_identical(policy, state):
    state["observation"]["farms"][0]["money"] = 100000
    a, new = policy["expansion_turn"](state["observation"], state["configuration"])
    b, old = cycle_3.expansion_turn(state["observation"], state["configuration"])
    assert a == b
    for left, right in zip(new["expansion"]["alternatives"], old["expansion"]["alternatives"]):
        for key in ("orders", "columns", "projection", "marginal_value", "route_feasible"):
            assert left[key] == right[key]


def prepared(state):
    obs, cfg = state["observation"], state["configuration"]
    a, d = cycle_3.expansion_turn(obs, cfg)
    orders = [o for o in a["market"] if o[0] not in ("BUY_ANIMAL", "BUY_LAND", "BUY_SEED")]
    planned = cycle_3.planning_snapshot(
        obs, cfg, [a["farmer"], *a["hands"]], orders, cycle_3.MARKET
    )
    option = d["expansion"]["chosen"]
    return planned, cfg, option["columns"], option["projection"]


def test_paid_and_previously_forecast_hires_are_not_charged_twice(policy, state):
    obs, cfg, columns, projection = prepared(state)
    projection["daily"][0]["workers"] = 9
    b = policy["current_day_cash_bound"](obs, cfg, cycle_3.MARKET, columns, projection)
    assert b["extra_wage_cash"] == 0
    obs["farms"][0]["hires_today"] = 10
    b = policy["current_day_cash_bound"](obs, cfg, cycle_3.MARKET, columns, projection)
    assert b["extra_hires"] == 0 and b["extra_wage_cash"] == 0


def test_held_feed_and_physical_shortfalls_are_not_double_charged(policy, state):
    obs, cfg, columns, projection = prepared(state)
    obs["private"]["shed"]["WHEAT"] = 20
    b = policy["current_day_cash_bound"](obs, cfg, cycle_3.MARKET, columns, projection)
    assert b["extra_feed_units"] == 0
    obs["private"]["shed"]["WHEAT"] = 0
    obs["private"]["inventories"][0]["WHEAT"] = 0
    b = policy["current_day_cash_bound"](obs, cfg, cycle_3.MARKET, columns, projection)
    assert b["already_modeled_feed_shortfall"] == 5
    assert b["extra_feed_units"] == 7  # 12 needed minus the five already priced by the model.


def test_terminal_feed_and_hire_deadline_and_setup_time(policy, state):
    obs, cfg, columns, projection = prepared(state)
    obs.update(day=29, hour=22, step=718)
    b = policy["current_day_cash_bound"](obs, cfg, cycle_3.MARKET, columns, projection)
    assert b["extra_feed_units"] == b["extra_hires"] == 0
    assert b["possible_same_day_installations"] == 0
    obs.update(day=6, hour=6, step=150)
    b = policy["current_day_cash_bound"](obs, cfg, cycle_3.MARKET, columns, projection)
    assert b["extra_hires"] == 0  # The policy's hiring window ends before the next observation.
    bad = {"daily": [], "min_cash": -1e9}
    assert (
        policy["current_day_cash_bound"](obs, cfg, cycle_3.MARKET, columns, bad)["min_cash"] == -1e9
    )


def test_only_expansion_admission_is_changed(policy):
    def functions(code):
        return {n.name: ast.dump(n) for n in ast.parse(code).body if isinstance(n, ast.FunctionDef)}

    old = functions(Path(cycle_3.__file__).read_text())
    new = functions(Path(policy["__file__"]).read_text())
    assert set(new) - set(old) == {"current_day_cash_bound"}
    assert {k for k in old if old[k] != new[k]} == {"expansion_investment"}
    env = make("kaggriculture", configuration={"seed": 17})
    assert policy["agent"](env.state[0].observation, env.configuration) == cycle_3.agent(
        env.state[0].observation, env.configuration
    )


def test_auditor_accepts_empty_market_orders(tmp_path):
    env = make("kaggriculture", configuration={"seed": 17, "episodeSteps": 4})

    def empty_orders(obs):
        return {"farmer": ["PASS"], "hands": [], "market": [[], ["BUY_SEED", "WHEAT", 1]]}

    env.run([empty_orders, empty_orders])
    path = tmp_path / "empty.json"
    path.write_text(json.dumps(env.toJSON()))
    report = audit_continuation(path, tmp_path, 1, 0)
    assert all(p["cash_reconciled"] for p in report["players"])
    assert report["players"][0]["executed_quantities"] == {"BUY_SEED WHEAT": 2}
