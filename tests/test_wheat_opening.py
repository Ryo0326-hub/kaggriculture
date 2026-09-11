"""Opening capacity, dated reinvestment, internal feed and unchanged downstream policy."""

import ast
import runpy
from copy import deepcopy
from pathlib import Path

import pytest
from kaggle_environments import make
from kaggle_environments.envs.kaggriculture import kaggriculture as engine

from baselines import cycle_3
from evaluate import ROOT, run_match
from scripts.make_opening_control import build
from scripts.report_opening import opening_gate


@pytest.fixture
def candidate(tmp_path):
    output = tmp_path / "main.py"
    build(cycle_3.__file__, output)
    return output, runpy.run_path(str(output))


def test_original_options_unchanged_and_sequences_respect_land_and_dates(candidate):
    _, policy = candidate
    env = make("kaggriculture", configuration={"seed": 17})
    obs, cfg = env.state[0].observation, env.configuration
    before = deepcopy(obs)
    _, old = cycle_3.opening_portfolios(obs, cfg, cycle_3.MARKET)
    best, options = policy["opening_portfolios"](obs, cfg, cycle_3.MARKET)
    assert len(options) == 50 and obs == before
    originals = [p for p in options if not p["wheat"]]
    for left, right in zip(originals, old):
        assert all(left[k] == v for k, v in right.items())
    assert best == max((p for p in options if p["min_cash"] >= 150), key=lambda p: p["value"])
    for p in options:
        assert p["investment_cost"] == p["cost_now"] + p["wheat"] * 80
        for day in range(30):
            active = 0
            for item in p["columns"]:
                if "crop" not in item:
                    continue
                end = item["planted_day"] + cycle_3.CROPS[item["crop"]]["harvest"]
                active += item["planted_day"] <= day <= end
                if item.get("buy_day"):
                    assert item["buy_day"] == item["planted_day"] == 5
            assert active <= 12
    _, limited = policy["opening_portfolios"](obs, cfg, cycle_3.MARKET, crop_limit=7)
    assert all(p["wheat"] + p["melons"] <= 7 for p in limited)


def test_order_only_pays_first_stage_and_ignores_hidden_seed(candidate):
    _, policy = candidate
    env = make("kaggriculture", configuration={"seed": 17})
    obs, cfg = env.state[0].observation, env.configuration
    action, detail = policy["expansion_turn"](obs, cfg)
    assert (action, detail) == policy["expansion_turn"](obs, dict(cfg, seed=999))
    p = detail["production"]["opening"]
    for crop, n in (("WHEAT", p["wheat"]), ("MELON", p["melons"])):
        assert sum(o[2] for o in action["market"] if o[:2] == ["BUY_SEED", crop]) == n
    assert sum(o[2] for o in action["market"] if o[0] == "BUY_SEED") <= 12


def test_internal_wheat_is_not_sold_and_fed_twice(monkeypatch):
    env = make("kaggriculture", configuration={"seed": 17})
    obs = env.state[0].observation
    obs.update(day=4, hour=0, step=96)
    farm = obs.farms[0]
    farm["tiles"][4][4] = engine._new_animal("COW", 0)
    farm["tiles"][4][3] = engine._new_plant("WHEAT", 0, 24)
    farm["tiles"][4][3]["yield_units"] = 3  # Already watered through day 3.
    obs.private["shed"]["WHEAT"] = 4
    sold = []
    original = cycle_3.batch_revenue

    def record(crop, inventory, units, params):
        if crop == "WHEAT":
            sold.append(units)
        return original(crop, inventory, units, params)

    monkeypatch.setattr(cycle_3, "batch_revenue", record)
    forecast = cycle_3.production_projection(
        obs, dict(env.configuration, episodeSteps=145), cycle_3.MARKET, fertilized=False
    )
    # Final day 5: four held + four harvested - one feed today = seven sold in total.
    assert forecast["feed_cost"] == 0
    assert sum(sold) == 7


def test_generated_sources_only_change_registered_functions(candidate, tmp_path):
    output, _ = candidate

    def functions(path):
        return {
            n.name: ast.dump(n)
            for n in ast.parse(Path(path).read_text()).body
            if isinstance(n, ast.FunctionDef)
        }

    old, new = functions(cycle_3.__file__), functions(output)
    assert old.keys() == new.keys()
    assert {k for k in old if old[k] != new[k]} == {"opening_portfolios", "production_orders"}
    # Every decision after the first opening branch uses the original production body.
    old_code, new_code = [Path(p).read_text() for p in (cycle_3.__file__, output)]
    anchor = "    if hour > 6 or day == 0:"
    assert old_code[old_code.index(anchor) :] == new_code[new_code.index(anchor) :]
    reproduced = tmp_path / "reproduced.py"
    build(cycle_3.__file__, reproduced)
    assert output.read_bytes() == reproduced.read_bytes()
    with pytest.raises(FileExistsError):
        build(cycle_3.__file__, output)
    with pytest.raises(ValueError):
        build(output, tmp_path / "wrong-source.py")


def test_wheat_pressure_control_is_standalone_and_has_correct_cost(tmp_path):
    path = tmp_path / "pressure.py"
    build(ROOT / "opponents/scaled_mixed.py", path, wheat_opponent=True)
    policy = runpy.run_path(str(path))
    assert policy["crop_choice"](25, 0, 29) == "WHEAT"
    assert policy["crop_choice"](26, 0, 29) is None
    row, env = run_match(str(path), "pass", 17, 0, episode_steps=4)
    assert row["outcome"] != "error"
    opening = env.steps[1][0].action["market"]
    assert [o for o in opening if o[0] == "BUY_SEED"] == [["BUY_SEED", "WHEAT", 15]]
    assert "cash -= 1950" in path.read_text()


def test_opening_installs_and_harvests_without_operational_losses(candidate):
    path, _ = candidate
    row, env = run_match(str(path), "pass", 17, 0)
    assert row["outcome"] != "error"
    orders = env.steps[1][0].action["market"]
    wheat = sum(o[2] for o in orders if o[:2] == ["BUY_SEED", "WHEAT"])
    assert wheat > 0  # This hypothesis must actually change opening production.
    initial = [
        t
        for r in env.steps[24][0].observation.farms[0]["tiles"]
        for t in r
        if isinstance(t, dict) and t.get("crop") == "WHEAT"
    ]
    assert len(initial) == wheat
    assert all(t["planted_day"] == 0 and t["consecutive_unwatered"] == 0 for t in initial)
    harvested = sum(
        state[0].action["farmer"] == ["HARVEST"]
        or any(op == ["HARVEST"] for op in state[0].action["hands"])
        for state in env.steps[1:145]
    )
    assert harvested > 0
    econ = row["economics"]["candidate"]
    for key in (
        "unplanned_crop_losses",
        "seed_overrequests",
        "animal_days_unfed",
        "animals_escaped",
    ):
        assert econ[key] == 0
    assert row["unused_seeds"] == row["unsold_shed_units"] == row["unsold_carried_units"] == 0


def test_opening_gate_requires_improvement_without_a_stratum_regression():
    reference = {"summary": {"match_score": 0.6}}
    candidate = {
        "summary": {"match_score": 0.7, "errors": 0, "decision_max_seconds": 0.4},
        "terminal_units": 0,
        "operational_totals": {"unplanned_crop_losses": 0},
    }
    comparison = {
        "by_opponent": {
            "pressure": {
                "candidate_match_score": 0.5,
                "reference_match_score": 0.5,
            }
        }
    }
    assert opening_gate(candidate, reference, comparison)["advance_to_fresh_evaluation"]
    comparison["by_opponent"]["pressure"]["candidate_match_score"] = 0.4
    assert not opening_gate(candidate, reference, comparison)["advance_to_fresh_evaluation"]
    comparison["by_opponent"]["pressure"]["candidate_match_score"] = 0.6
    candidate["summary"]["match_score"] = 0.6
    assert not opening_gate(candidate, reference, comparison)["advance_to_fresh_evaluation"]
