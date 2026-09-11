"""Counterfactuals must preserve state, information boundaries and reactive futures."""

import copy
import json

import pytest
from kaggle_environments import make

from scripts.benchmark_continuation import (
    audit_continuation,
    intervene,
    reconstruct,
    run_continuation,
    state_view,
)


@pytest.fixture
def fixture(tmp_path):
    policy = tmp_path / "policy.py"
    policy.write_text("""
def agent(obs, cfg):
    assert cfg["seed"] is None
    step = obs["step"]  # Must also be available to seat 1.
    orders = []
    if obs["player"] == 0 and step in (2, 4):
        orders = [["BUY_SEED", "MELON" if step == 2 else "WHEAT", 1]]
    move = "NORTH" if obs["player"] == 1 and obs["farms"][0]["money"] < 3000 else "PASS"
    return {"farmer": [move], "hands": [], "market": orders}
""")
    agents = [str(policy), str(policy)]
    env = make("kaggriculture", configuration={"seed": 17, "episodeSteps": 8})
    env.run(agents)
    return env.toJSON(), agents


@pytest.mark.parametrize("seat", [0, 1])
def test_control_reproduces_entire_future_and_shared_clock(fixture, seat):
    replay, agents = fixture
    actual, row = run_continuation(replay, 2, seat, agents, {"name": "control"})
    assert row["prefix_observations_verified"] == 3
    assert [state_view(s) for s in actual["steps"]] == [state_view(s) for s in replay["steps"]]
    assert row["comparison_with_recorded_control"]["first_action_difference_by_seat"] == [
        None,
        None,
    ]


def test_wait_preserves_maintenance_and_resumes_investment(fixture):
    replay, agents = fixture
    actual, row = run_continuation(
        replay, 2, 0, agents, {"name": "wait", "release": 4, "orders": []}
    )
    assert actual["steps"][3][0]["action"]["market"] == []
    assert actual["steps"][5][0]["action"]["market"] == [["BUY_SEED", "WHEAT", 1]]
    # The opponent reacts to our changed public cash; its future isn't replayed.
    assert row["comparison_with_recorded_control"]["first_action_difference_by_seat"] == [3, 4]
    assert row["capital_trace"][-1]["observation"] == 4
    assert not row["capital_trace"][-1]["overridden"]
    action = {
        "farmer": ["FEED"],
        "hands": [["NORTH"]],
        "market": [
            ["HIRE"],
            ["BUY_PRODUCT", "FERTILIZER", 3],
            ["SELL", "MILK", 2],
            ["BUY_LAND"],
            ["BUY_SEED", "MELON", 4],
        ],
    }
    before = copy.deepcopy(action)
    changed = intervene(action, [["BUY_SEED", "WHEAT", 1]])
    assert action == before
    assert changed["farmer"] == before["farmer"] and changed["hands"] == before["hands"]
    assert changed["market"] == before["market"][:3] + [["BUY_SEED", "WHEAT", 1]]
    with pytest.raises(ValueError, match="Only capital"):
        intervene(action, [["HIRE"]])


def test_recorded_future_is_only_an_audit_reference(fixture):
    replay, agents = fixture
    variant = {"name": "skip"}
    actual, _ = run_continuation(replay, 2, 0, agents, variant)
    poisoned = copy.deepcopy(replay)
    for states in poisoned["steps"][3:]:
        for s in states:
            s["action"] = {"farmer": ["SOUTH"], "hands": [], "market": []}
    other, _ = run_continuation(poisoned, 2, 0, agents, variant)
    assert [s[0]["action"] for s in actual["steps"]] == [s[0]["action"] for s in other["steps"]]
    assert [state_view(s) for s in actual["steps"]] == [state_view(s) for s in other["steps"]]
    with pytest.raises(ValueError, match="control does not reproduce"):
        run_continuation(poisoned, 2, 0, agents, {"name": "control"})


def test_reject_corrupt_prefix_clock_and_failed_agents(fixture, tmp_path):
    replay, agents = fixture
    corrupt = copy.deepcopy(replay)
    corrupt["steps"][1][1]["observation"]["private"]["seeds"]["WHEAT"] += 1
    with pytest.raises(ValueError, match="Prefix state mismatch"):
        reconstruct(corrupt, 2)
    for index in (0, 7, -1):
        with pytest.raises(ValueError, match="Branch must"):
            reconstruct(replay, index)
    with pytest.raises(ValueError, match="Release must"):
        run_continuation(replay, 2, 0, agents, {"name": "wait", "release": 2})
    broken = tmp_path / "broken.py"
    broken.write_text('def agent(obs, cfg):\n    raise RuntimeError("test failure")\n')
    with pytest.raises(ValueError, match="failed or did not finish"):
        run_continuation(replay, 2, 0, [str(broken), agents[1]], {"name": "skip"})


def test_continuation_cash_reconciles_and_excludes_prefix(fixture, tmp_path):
    replay, agents = fixture
    actual, _ = run_continuation(replay, 3, 0, agents, {"name": "control"})
    path = tmp_path / "control.json"
    path.write_text(json.dumps(actual))
    result = audit_continuation(path, tmp_path, 3, 0)
    own = result["players"][0]
    assert own["starting_cash"] == 2920
    assert own["expenses"] == 10
    assert own["final_cash"] == 2910
    assert own["cash_reconciled"]
    assert own["executed_quantities"] == {"BUY_SEED WHEAT": 1}
