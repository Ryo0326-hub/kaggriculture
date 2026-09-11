"""Location-sensitive land options preserve the existing economic constraints."""

import ast
import json
import runpy
from copy import deepcopy
from hashlib import sha256
from pathlib import Path

import pytest
from kaggle_environments import make
from kaggle_environments.envs.kaggriculture import kaggriculture as engine

from baselines import cycle_3
from scripts.make_spatial_control import build
from scripts.report_server import verify_source
from scripts.report_spatial import release_gate


@pytest.fixture
def spatial(tmp_path):
    output = tmp_path / "main.py"
    build(cycle_3.__file__, output)
    return runpy.run_path(str(output))


def investment_state():
    env = make("kaggriculture", configuration={"seed": 17})
    obs = env.state[0].observation
    obs.update(day=3, hour=0, step=72)
    obs.farms[0]["money"] = 30000
    return env, obs


def alternatives(policy, obs, cfg, max_land=3):
    return policy(obs, cfg, cycle_3.MARKET, [["PASS"]], [], max_land)[1]["alternatives"]


def test_spatial_options_exist_with_many_vacant_owned_sites(spatial):
    env, obs = investment_state()
    before = deepcopy(obs)
    old = alternatives(cycle_3.expansion_investment, obs, env.configuration)
    new = alternatives(spatial["expansion_investment"], obs, env.configuration)
    assert not any(o["land_cost"] for o in old)
    extra = [o for o in new if o["land_cost"]]
    assert extra and any(o["route_feasible"] and o["affordable"] for o in extra)
    assert obs == before
    for option in extra:
        sites = [c["site"] for c in option["columns"]]
        assert any(obs.farms[0]["tiles"][y][x] == "LOCKED" for x, y in sites)
        assert option["cost_now"] == 1000 + sum(
            cycle_3.CROPS[c["crop"]]["seed"] for c in option["columns"]
        )
        bought = deepcopy(obs.farms[0])
        engine._do_buy_land(bought, 10)
        assert all(bought["tiles"][y][x] != "LOCKED" for x, y in sites)
        assert bought["money"] == obs.farms[0]["money"] - option["land_cost"]


def test_land_limit_cash_reserve_and_terminal_payback_remain(spatial):
    env, obs = investment_state()
    policy = spatial["expansion_investment"]
    assert not any(o["land_cost"] for o in alternatives(policy, obs, env.configuration, 1))
    obs.farms[0]["money"] = 1100
    options = alternatives(policy, obs, env.configuration)
    assert any(o["land_cost"] for o in options)
    assert not any(o["land_cost"] and o["affordable"] for o in options)
    obs.farms[0]["money"] = 30000
    obs.update(day=29, hour=0, step=696)
    assert not any(o["land_cost"] for o in alternatives(policy, obs, env.configuration))


def test_only_investment_candidate_enumeration_changes(spatial):
    original = ast.parse(Path(cycle_3.__file__).read_text())
    candidate = ast.parse(Path(spatial["__file__"]).read_text())
    old_functions = {n.name: ast.dump(n) for n in original.body if isinstance(n, ast.FunctionDef)}
    new_functions = {n.name: ast.dump(n) for n in candidate.body if isinstance(n, ast.FunctionDef)}
    changed = {name for name in old_functions if old_functions[name] != new_functions[name]}
    assert changed == {"expansion_investment"}
    assert sha256(Path(cycle_3.__file__).read_bytes()).hexdigest() == (
        "47c281bfb4118a9755f1759930b162de007efdfef3b23144457eccbaac42da0c"
    )


def source_fixture(tmp_path):
    source = tmp_path / "agent.py"
    source.write_text('def agent(obs, configuration):\n    return {"farmer": ["PASS"]}\n')
    replay = tmp_path / "123.json"
    replay.write_text(
        json.dumps(
            {
                "info": {"EpisodeId": 123},
                "configuration": {},
                "steps": [[{"observation": {}}, {}], [{"action": {"farmer": ["PASS"]}}, {}]],
                "statuses": ["DONE", "DONE"],
                "rewards": [10, 20],
            }
        )
    )
    log = tmp_path / "123-0.json"
    log.write_text(json.dumps([[{"duration": 0.1, "stderr": ""}]]))
    return source, replay, log


def test_server_report_rejects_wrong_source_or_incomplete_log(tmp_path):
    source, replay, log = source_fixture(tmp_path)
    result = verify_source(replay, log, source)
    assert result["decisions_matched"] == 1 and result["own_margin"] == -10
    source.write_text('def agent(obs, configuration):\n    return {"farmer": ["NORTH"]}\n')
    with pytest.raises(ValueError, match="Source differs"):
        verify_source(replay, log, source)
    log.write_text("[]")
    with pytest.raises(ValueError, match="one entry"):
        verify_source(replay, log, source)


def test_server_report_rejects_wrong_episode_log(tmp_path):
    source, replay, log = source_fixture(tmp_path)
    other = log.with_name("124-0.json")
    log.rename(other)
    with pytest.raises(ValueError, match="this episode"):
        verify_source(replay, other, source)


@pytest.mark.parametrize("failure", ["uncertain", "opponent", "execution", "inventory", "crop"])
def test_release_gate_rejects_improvement_with_material_limitations(failure):
    comparison = {
        "bootstrap_95_percentile_interval": [0.05, 0.25],
        "by_opponent": {"strong": {"candidate_match_score": 0.75, "reference_match_score": 0.5}},
    }
    candidate = {
        "summary": {"errors": 0},
        "terminal_units": 0,
        "operational_totals": {"unplanned_crop_losses": 0},
    }
    assert release_gate(comparison, candidate)["passes_recorded_gate"]
    if failure == "uncertain":
        comparison["bootstrap_95_percentile_interval"][0] = 0
    elif failure == "opponent":
        comparison["by_opponent"]["strong"]["candidate_match_score"] = 0.25
    elif failure == "execution":
        candidate["summary"]["errors"] = 1
    elif failure == "inventory":
        candidate["terminal_units"] = 1
    else:
        candidate["operational_totals"]["unplanned_crop_losses"] = 1
    assert not release_gate(comparison, candidate)["passes_recorded_gate"]
