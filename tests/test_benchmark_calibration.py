"""Evidence accounting and economically consequential benchmark contracts."""

import json
from copy import deepcopy
from hashlib import sha256

import pytest
from kaggle_environments import make
from kaggle_environments.envs.kaggriculture import kaggriculture as engine

from evaluate import ROOT, run_match
from opponents.scaled_mixed import agent, crop_job
from scripts.benchmark_profiles import product_flows, profile


def test_uploaded_step_8_is_frozen():
    expected = "63dbf4381d8607cbd681f5296749f4f8af4cc37d0181f97d6b8931f6078d3f72"
    assert sha256((ROOT / "baselines/step_8.py").read_bytes()).hexdigest() == expected


def test_product_accounting_does_not_call_resales_production():
    player = {
        "executed_quantities": {"BUY_PRODUCT WHEAT": 927, "SELL WHEAT": 824},
        "cash_by_operation": {"BUY_PRODUCT WHEAT": 40995, "SELL WHEAT": 37764},
        "harvested_or_collected": {"WHEAT": 218},
        "sales_by_product": {"WHEAT": {}},
    }
    flow = product_flows(player)["WHEAT"]
    assert flow["harvested_or_collected"] == 218
    assert flow["sold"] == 824
    assert flow["sales_less_product_purchases"] == -3231


def test_last_crop_yield_is_collected_before_expiration():
    tile = engine._new_plant("STRAWBERRY", 0, 24)
    tile.update(yield_units=2, consecutive_unwatered=1)
    assert crop_job(tile, 16, 29, True)[1] == "HARVEST"
    tile = engine._new_plant("WHEAT", 0, 24)
    tile.update(yield_units=4, watered_today=True)
    assert crop_job(tile, 4, 29, True)[1] == "HARVEST"


def test_normal_overnight_harvest_and_final_delivery_have_different_deadlines():
    env = make("kaggriculture", configuration={"seed": 17})
    obs = env.state[0].observation
    farm = obs.farms[0]
    farm["farmer"] = [4, 1]
    cow = engine._new_animal("COW", 0)
    cow.update(yield_units=2, fed_today=True, cared_today=True, fertilizer_available=False)
    farm["tiles"][1][4] = cow
    obs.update(day=12, hour=23, step=311)
    before = deepcopy(obs)
    action = agent(obs, env.configuration)
    assert obs == before
    assert action["farmer"] == ["HARVEST"]
    engine._apply_unit_action(farm, obs.private, 0, action["farmer"], 10, 12, 24)
    engine._drop_inventories_to_shed(obs.private, 100)
    assert obs.private.shed["MILK"] == 2
    obs = before
    obs.update(day=29, hour=21, step=717)
    action = agent(obs, env.configuration)
    assert action["farmer"] != ["HARVEST"]


def test_full_season_control_exercises_scale_and_supply_without_execution_errors():
    record, _ = run_match(str(ROOT / "opponents/scaled_mixed.py"), "pass", 43, 0)
    assert record["candidate_status"] == record["opponent_status"] == "DONE"
    assert not record["failures"]
    economics = record["economics"]["candidate"]
    assert economics["peak_productive_tiles"] >= 60
    assert economics["harvested_units"]["STRAWBERRY"] >= 200
    assert economics["duplicate_crop_targets"] == 0
    assert economics["seed_overrequests"] == 0
    assert economics["animals_escaped"] == 0


def test_simultaneous_harvests_reserve_shared_overnight_capacity():
    env = make("kaggriculture", configuration={"seed": 17})
    obs = env.state[0].observation
    obs.update(day=12, hour=23, step=311)
    farm = obs.farms[0]
    farm["farmer"], farm["hands"] = [4, 4], [[3, 4]]
    obs.private["inventories"] = [{}, {}]
    obs.private.shed["MILK"] = 97
    for x in (3, 4):
        animal = engine._new_animal("COW", 0)
        animal.update(yield_units=2, fed_today=True, cared_today=True)
        farm["tiles"][4][x] = animal
    action = agent(obs, env.configuration)
    assert [action["farmer"], *action["hands"]].count(["HARVEST"]) == 1
    for worker, command in enumerate([action["farmer"], *action["hands"]]):
        engine._apply_unit_action(farm, obs.private, worker, command, 10, 12, 24)
    assert (
        sum(obs.private.shed.values()) + sum(sum(v.values()) for v in obs.private["inventories"])
        == 99
    )


def test_profiles_reject_a_stale_replay_or_unreconciled_audit(tmp_path):
    replay = tmp_path / "replay.json"
    replay.write_text(json.dumps({"info": {"EpisodeId": 123}}))
    audit = tmp_path / "analysis-123.json"
    audit.write_text(json.dumps({"source_sha256": "stale", "state_mismatches": {}}))
    with pytest.raises(ValueError, match="matching, reconciled"):
        profile(replay, tmp_path)
    audit.write_text(
        json.dumps(
            {
                "source_sha256": sha256(replay.read_bytes()).hexdigest(),
                "state_mismatches": {"market": 1},
            }
        )
    )
    with pytest.raises(ValueError, match="matching, reconciled"):
        profile(replay, tmp_path)
