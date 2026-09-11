"""Independent engine checks for dated inputs, working capital, and the opening."""

from copy import deepcopy
from hashlib import sha256

import pytest
from kaggle_environments import make
from kaggle_environments.envs.kaggriculture import kaggriculture as engine

import main
from evaluate import ROOT, run_match
from scripts.make_bundle_control import build


@pytest.mark.parametrize(
    "crop,fertilized,total",
    [
        ("WHEAT", False, 4),
        ("WHEAT", True, 6),
        ("MELON", False, 6),
        ("STRAWBERRY", False, 4),
        ("STRAWBERRY", True, 8),
    ],
)
def test_complete_column_matches_engine_with_each_input_paid(crop, fertilized, total):
    env = make("kaggriculture", configuration={"seed": 17})
    farm, private = env.state[0].observation.farms[0], env.state[0].observation.private
    farm["tiles"][4][4] = engine._new_plant(crop, 0, 24)
    column = main.crop_column(crop, 0, 29, fertilized)
    observed, applications = {}, []
    private["inventories"][0]["FERTILIZER"] = len(column["fertilizer"])
    for day in range(column["end"] + 1):
        if day in column["fertilizer"]:
            applications.append(day)
            engine._apply_unit_action(farm, private, 0, ["FERTILIZE"], 10, day, 24)
        engine._apply_unit_action(farm, private, 0, ["WATER"], 10, day, 24)
        tile = farm["tiles"][4][4]
        if day in column["outputs"]:
            observed[day] = tile["yield_units"]
            engine._apply_unit_action(farm, private, 0, ["HARVEST"], 10, day, 24)
        engine._daily_refresh_plants(farm, day, 24)
    assert observed == column["outputs"]
    assert sum(observed.values()) == total
    assert private["inventories"][0].get("FERTILIZER", 0) == 0
    if crop == "STRAWBERRY" and fertilized:
        assert applications == [9, 13]


def test_final_day_excludes_unrecoverable_production_and_inputs():
    assert main.crop_column("MELON", 20, 29) is None
    col = main.crop_column("STRAWBERRY", 19, 29, True)
    assert col["outputs"] == {29: 2}
    assert col["fertilizer"] == [28]
    assert main.crop_column("WHEAT", 26, 29) is None


def test_paid_hires_feed_and_sales_are_booked_once_before_projection():
    env = make("kaggriculture", configuration={"seed": 17})
    obs = env.state[0].observation
    obs.update(day=3, hour=0, step=72)
    farm = obs.farms[0]
    farm["tiles"][4][4] = engine._new_animal("COW", 0)
    obs.private["inventories"][0]["WHEAT"] = 1
    obs.private["shed"]["MILK"] = 3
    commands = [["FEED"]]
    orders = [["SELL", "MILK", 3], ["BUY_PRODUCT", "WHEAT", 2], ["HIRE"]]
    before = deepcopy(obs)
    planned = main.planning_snapshot(obs, env.configuration, commands, orders, main.MARKET)
    engine._apply_unit_action(farm, obs.private, 0, commands[0], 10, 3, 24)
    for op in orders:
        if op[0] == "HIRE":
            engine._do_hire(farm, obs.private, 10)
        else:
            for _ in range(op[2]):
                inventory = obs.market["inventory"][op[1]]
                price = engine.market_price(op[1], inventory - (op[0] == "BUY_PRODUCT"))
                engine._commit_unit(op[0], op[1], price, farm, obs.private, obs.market)
    assert planned.farms[0]["money"] == farm["money"]
    assert planned.private["shed"] == obs.private["shed"]
    assert planned.market["inventory"] == obs.market["inventory"]
    forecast = main.production_projection(planned, env.configuration, main.MARKET)
    assert forecast["daily"][0]["spending_before_receipts"] == 0
    assert before.private["inventories"][0]["WHEAT"] == 1


def test_owned_fertilizer_is_not_sold_and_consumed_in_same_forecast():
    env = make("kaggriculture", configuration={"seed": 17})
    obs = env.state[0].observation
    obs.update(day=9, hour=0, step=216)
    obs.farms[0]["tiles"][4][4] = engine._new_plant("STRAWBERRY", 0, 24)
    obs.private["shed"]["FERTILIZER"] = 1
    f = main.production_projection(obs, env.configuration, main.MARKET)
    assert f["daily"][0]["fertilizer_inputs"] == 1
    assert f["daily"][0]["credited_receipts"] == 0


def test_opening_is_pure_seed_independent_and_rejects_unfunded_larger_option():
    env = make("kaggriculture", configuration={"seed": 17})
    obs = env.state[0].observation
    before = deepcopy(obs)
    action, detail = main.bundle_turn(obs, env.configuration)
    assert (action, detail) == main.bundle_turn(obs, dict(env.configuration, seed=999))
    assert before == obs
    options = detail["production"]["alternatives"]
    selected = detail["production"]["opening"]
    assert selected["min_cash"] >= 150
    assert selected["melons"] > 0
    assert any(not p["affordable"] and p["value"] > selected["value"] for p in options)
    assert sum(o[2] for o in action["market"] if o[0] == "BUY_SEED") == selected["melons"]


def test_frozen_step_6_preserves_server_validated_source():
    assert sha256((ROOT / "baselines/step_6.py").read_bytes()).hexdigest() == (
        "d545236b1045fa522676931380ba68517eb2d359252783ea997156bb0f6f13ac"
    )


def test_bundle_control_keeps_actual_loader_entrypoint(tmp_path):
    path = tmp_path / "no-opening.py"
    build(ROOT / "main.py", path, opening=False)
    row, _ = run_match(str(path), "pass", 17, 0, episode_steps=4)
    assert row["outcome"] != "error"
    with pytest.raises(FileExistsError):
        build(ROOT / "main.py", path)


def test_independent_early_seller_delivers_all_twelve_melons_without_losses():
    row, env = run_match(str(ROOT / "opponents/early_crops.py"), "pass", 17, 0)
    assert row["outcome"] != "error"
    audit = row["economics"]["candidate"]
    assert audit["harvested_units"]["MELON"] == 72
    assert audit["harvested_units"]["STRAWBERRY"] == 48
    assert audit["unplanned_crop_losses"] == audit["seed_overrequests"] == 0
    assert row["unused_seeds"] == row["unsold_shed_units"] == row["unsold_carried_units"] == 0
    sold = sum(
        op[2]
        for state in env.steps[1 : 12 * 24]
        for op in state[0].action["market"]
        if op[:2] == ["SELL", "MELON"]
    )
    assert sold == 72


def test_joint_opening_is_installed_and_watered_on_day_one():
    row, env = run_match(str(ROOT / "main.py"), "pass", 17, 0)
    opening = env.steps[1][0].action["market"]
    promised = sum(op[2] for op in opening if op[:2] == ["BUY_SEED", "MELON"])
    farm = env.steps[24][0].observation.farms[0]
    crops = [t for r in farm["tiles"] for t in r if isinstance(t, dict) and t.get("crop")]
    assert len(crops) == promised > 0
    assert all(t["planted_day"] == 0 and t["consecutive_unwatered"] == 0 for t in crops)
    assert row["economics"]["candidate"]["animal_days_unfed"] == 0


def test_installation_preloads_feed_and_defers_an_incomplete_late_bundle():
    env = make("kaggriculture", configuration={"seed": 17})
    obs = env.state[0].observation
    obs.update(day=12, hour=12, step=300)
    obs.private["inventories"][0]["COW"] = 1
    obs.private["shed"]["WHEAT"] = 1
    action, _ = main.bundle_turn(obs, env.configuration)
    assert action["farmer"] == ["PICKUP", "WHEAT", 1]
    obs.private["inventories"][0]["WHEAT"] = 1
    obs.private["shed"]["WHEAT"] = 0
    obs.farms[0]["tiles"][4][4] = {"kind": "PASTURE"}
    obs.update(hour=22, step=310)
    action, _ = main.bundle_turn(obs, env.configuration)
    assert action["farmer"] == ["PASS"]
    obs.update(day=13, hour=0, step=312)
    action, _ = main.bundle_turn(obs, env.configuration)
    assert action["farmer"] == ["PLACE", "COW"]


def test_late_installation_regression_finishes_first_feed_before_refresh():
    row, _ = run_match(str(ROOT / "main.py"), str(ROOT / "baselines/step_6.py"), 7004, 0)
    assert row["economics"]["candidate"]["animal_days_unfed"] == 0
    assert row["economics"]["candidate"]["animals_escaped"] == 0
