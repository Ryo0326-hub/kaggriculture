"""Economic intentions must survive the official engine's joint action ordering."""

from collections import Counter

import pytest
from kaggle_environments import make
from kaggle_environments.envs.kaggriculture import kaggriculture as engine

from baselines.step_3 import CROPS, MAX_HANDS, plan_turn
from evaluate import ROOT, run_match

PASS = {"farmer": ["PASS"], "hands": [], "market": []}


@pytest.fixture(scope="module")
def games():
    artifact = str(ROOT / "baselines/step_3.py")
    return [
        run_match(artifact, str(ROOT / "baselines/step_2.py"), 11, 0),
        run_match(artifact, str(ROOT / "baselines/step_2.py"), 29, 1),
        run_match(artifact, artifact, 71, 0),
    ]


def test_full_season_resource_contract_and_banking(games):
    for row, env in games:
        assert row["outcome"] != "error"
        assert row["recorded_states"] == 720
        assert row["unsold_shed_units"] == row["unsold_carried_units"] == 0
        p = row["seat"]
        assert max(len(s[p].observation.farms[p]["hands"]) for s in env.steps) <= MAX_HANDS
        assert any(len(s[p].observation.farms[p]["hands"]) > 4 for s in env.steps)
        for before, after in zip(env.steps, env.steps[1:]):
            old, new = before[p].observation, after[p].observation
            farm = old.farms[p]
            action = after[p].action
            assert len(action["hands"]) == len(farm["hands"])
            units = [action["farmer"], *action["hands"]]
            plants = Counter(a[1] for a in units if a[0] == "PLANT")
            for crop, count in plants.items():
                assert count <= old.private["seeds"][crop]
            room = env.configuration.shedCapacity - sum(old.private["shed"].values())
            available = Counter(old.private["shed"])
            targets = []
            for i, (position, op) in enumerate(zip([farm["farmer"], *farm["hands"]], units)):
                x, y = position
                tile = farm["tiles"][y][x]
                inventory = old.private["inventories"][i]
                if op[0] in {"PLANT", "WATER", "HARVEST", "DIG"}:
                    targets.append(tuple(position))
                if op[0] == "PLANT":
                    assert tile is None
                    assert new.farms[p]["tiles"][y][x]["crop"] == op[1]
                elif op[0] == "WATER":
                    assert tile["kind"] == "PLANT" and not tile["watered_today"]
                    if old.day == new.day:
                        assert new.farms[p]["tiles"][y][x]["watered_today"]
                elif op[0] == "HARVEST":
                    assert old.day - tile["planted_day"] >= 2 and tile["yield_units"] > 0
                elif op[0] == "DIG":
                    assert tile["kind"] == "WEED"
                elif op[0] == "DROP":
                    amount = sum(inventory.values())
                    assert amount <= room
                    room -= amount
                    available.update(inventory)
                elif op[0] == "PLACE":
                    assert op[2] <= room and op[2] <= inventory[op[1]]
                    room -= op[2]
                    available[op[1]] += op[2]
            assert len(targets) == len(set(targets))
            cost, hires = 0, farm["hires_today"]
            assert len(action["market"]) <= env.configuration.maxMarketOrdersPerTurn
            for order in action["market"]:
                if order[0] == "SELL":
                    assert order[2] <= available[order[1]]
                    available[order[1]] -= order[2]
                elif order[0] == "BUY_SEED":
                    cost += engine.CROPS[order[1]]["seed"] * order[2]
                elif order[0] == "HIRE":
                    cost += engine._hire_cost(hires, env.configuration.farmHandCostMult)
                    hires += 1
            assert cost <= farm["money"]  # No financing from uncertain same-turn sales.
            for y, tiles in enumerate(farm["tiles"]):
                for x, tile in enumerate(tiles):
                    following = new.farms[p]["tiles"][y][x]
                    if isinstance(tile, dict) and tile.get("kind") == "PLANT":
                        assert not (isinstance(following, dict) and following.get("kind") == "WEED")


def test_mixed_inventory_is_banked_in_one_final_action():
    env = make("kaggriculture", configuration={"seed": 7, "episodeSteps": 4})
    env.step([PASS, PASS])
    env.step([PASS, PASS])
    obs = env.state[0].observation
    obs.private["inventories"] = [{"WHEAT": 3, "CARROT": 2}]
    action, _ = plan_turn(obs, env.configuration)
    assert action["farmer"] == ["DROP"]
    assert action["market"] == [["SELL", "WHEAT", 3], ["SELL", "CARROT", 2]]
    env.step([action, PASS])
    assert env.done
    assert sum(env.state[0].observation.private["shed"].values()) == 0


def test_overlapping_deposits_keep_unfittable_inventory():
    env = make("kaggriculture", configuration={"seed": 7})
    obs = env.state[0].observation
    obs.farms[0]["hands"] = [[5, 4]]
    obs.private["inventories"] = [{"WHEAT": 3, "CARROT": 2}, {"WHEAT": 4}]
    obs.private["shed"] = {"WHEAT": 98}
    action, _ = plan_turn(obs, env.configuration)
    assert action["farmer"][0] == "PLACE"
    assert action["hands"][0] == ["PASS"]
    env.step([action, PASS])
    assert sum(sum(inv.values()) for inv in env.state[0].observation.private["inventories"]) == 7


def test_seed_reservations_cover_both_crops_and_current_lot_limit():
    env = make("kaggriculture", configuration={"seed": 7})
    obs = env.state[0].observation
    obs.farms[0]["hands"] = [[3, 4]]
    obs.private["inventories"] = [{}, {}]
    obs.private["seeds"] = {c: 1 for c in CROPS}
    action, detail = plan_turn(obs, env.configuration)
    count = sum(a[0] == "PLANT" for a in [action["farmer"], *action["hands"]])
    assert count <= 1
    assert count <= detail["economics"]["lots"][detail["plant_crop"]]
    env.step([action, PASS])
    assert env.state[0].status == "ACTIVE"
