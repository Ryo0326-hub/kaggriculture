"""Engine-backed checks for capital, feed logistics, animal care, and liquidation."""

from copy import deepcopy

import pytest
from kaggle_environments import make
from kaggle_environments.envs.kaggriculture import kaggriculture as engine

from evaluate import ROOT, run_match
from main import ANIMALS, HERD_LIMIT, MARKET, animal_output, observed_demand, plan_turn, price_at
from scripts.make_livestock_control import build


@pytest.mark.parametrize("animal", ["COW", "SHEEP", "GOOSE"])
def test_output_projection_matches_daily_engine_care_and_production(animal):
    farm = {"tiles": [[engine._new_animal(animal, 0)]]}
    for start in [0, 8, 13]:
        # Build the observed history using the authoritative transition function.
        farm = {"tiles": [[engine._new_animal(animal, 0)]]}
        for day in range(start):
            tile = farm["tiles"][0][0]
            tile.update(fed_today=True, cared_today=True, yield_units=0, fertilizer_available=False)
            engine._daily_refresh_animals(farm, day)
        forecast = animal_output(farm["tiles"][0][0], start, 29)
        observed = []
        for day in range(start, 30):
            tile = farm["tiles"][0][0]
            observed.append((tile["yield_units"], int(tile["fertilizer_available"])))
            tile.update(
                fed_today=True, cared_today=day < 28, yield_units=0, fertilizer_available=False
            )
            engine._daily_refresh_animals(farm, day)
        assert forecast == observed


def test_no_production_before_installation():
    future = {"animal": "COW", "placed_day": 4}
    output = animal_output(future, 2, 15)
    assert output[:3] == [(0, 0)] * 3
    assert output[3] == (0, 1)
    assert all(units == 0 for units, _ in output[:10])
    assert output[10][0] == 6


def test_livestock_prices_and_fertilizer_demand_match_engine():
    for product in ["WHEAT", "MILK", "WOOL", "FERTILIZER"]:
        for inventory in [9800, 10000, 10100, 10500]:
            assert price_at(product, inventory, MARKET) == engine.market_price(product, inventory)
    env = make("kaggriculture", configuration={"seed": 17})
    obs = env.state[0].observation
    obs.town["unlocked_shops"] = ["YARN_STORE", "YARN_STORE", "PIZZA_SHOP"]
    demand = observed_demand(obs, env.configuration)
    assert demand["WOOL"] == 25
    assert demand["MILK"] == 7
    assert demand["FERTILIZER"] == 0


def test_investment_reserves_cash_and_responds_to_product_scarcity():
    env = make("kaggriculture", configuration={"seed": 17})
    obs = env.state[0].observation
    _, detail = plan_turn(obs, env.configuration)
    alternatives = detail["investment"]["alternatives"]
    assert alternatives and all(a["reserve"] > 0 for a in alternatives)
    poor = deepcopy(obs)
    poor.farms[0]["money"] = 400
    action, detail = plan_turn(poor, env.configuration)
    assert detail["investment"]["animal"] is None
    assert not any(o[0] == "BUY_ANIMAL" for o in action["market"])
    scarce = deepcopy(obs)
    scarce.market["inventory"]["MILK"] = 9000
    _, detail = plan_turn(scarce, env.configuration)
    assert detail["investment"]["animal"] == "COW"


def test_pending_animal_and_short_horizon_block_additional_capital():
    env = make("kaggriculture", configuration={"seed": 17})
    obs = env.state[0].observation
    obs.private["shed"]["SHEEP"] = 1
    action, detail = plan_turn(obs, env.configuration)
    assert detail["investment"]["pending"] == 1
    assert not any(o[0] == "BUY_ANIMAL" for o in action["market"])
    obs.private["shed"]["SHEEP"] = 0
    obs["day"], obs["hour"], obs["step"] = 27, 0, 648
    action, _ = plan_turn(obs, env.configuration)
    assert action["market"] == []


def test_policy_is_pure_and_ignores_evaluation_seed():
    env = make("kaggriculture", configuration={"seed": 17})
    obs = env.state[0].observation
    original = deepcopy(obs)
    action = plan_turn(obs, env.configuration)
    assert obs == original
    assert plan_turn(obs, dict(env.configuration, seed=987654321)) == action


@pytest.fixture(scope="module")
def games(tmp_path_factory):
    control = tmp_path_factory.mktemp("controls") / "cows.py"
    build(ROOT / "baselines/step_5.py", control, animal="COW")
    candidate = str(ROOT / "baselines/step_5.py")
    return [
        run_match(candidate, str(ROOT / "baselines/step_3.py"), 17, 0),
        run_match(candidate, str(control), 43, 1),
        run_match(candidate, candidate, 83, 0),
    ]


def test_full_seasons_feed_and_care_without_lost_animals(games):
    for record, env in games:
        assert record["outcome"] != "error"
        assert record["recorded_states"] == 720
        assert record["unsold_shed_units"] == record["unsold_carried_units"] == 0
        audit = record["economics"]["candidate"]
        assert audit["animals_escaped"] == audit["animal_days_unfed"] == 0
        assert audit["duplicate_crop_targets"] == 0
        assert audit["animal_order_cost"] > 0
        assert sum(audit["harvested_units"].values()) > 0
        seat = record["seat"]
        for before, after in zip(env.steps, env.steps[1:]):
            old = before[seat].observation
            farm, private = old.farms[seat], old.private
            action = after[seat].action
            assert len(action["hands"]) == len(farm["hands"]) < HERD_LIMIT
            assert len(action["market"]) <= env.configuration.maxMarketOrdersPerTurn
            stock = dict(private["shed"])
            room = env.configuration.shedCapacity - sum(stock.values())
            for p, inv, op in zip(
                [farm["farmer"], *farm["hands"]],
                private["inventories"],
                [action["farmer"], *action["hands"]],
            ):
                tile = farm["tiles"][p[1]][p[0]]
                if op[0] == "PICKUP":
                    assert engine._is_shed_adjacent(p, len(farm["tiles"]))
                    assert 0 < op[2] <= stock[op[1]]
                    stock[op[1]] -= op[2]
                    room += op[2]
                elif op[0] == "DROP":
                    assert engine._is_shed_adjacent(p, len(farm["tiles"]))
                    assert sum(inv.values()) <= room
                    room -= sum(inv.values())
                    for c, n in inv.items():
                        stock[c] = stock.get(c, 0) + n
                elif op[0] == "FEED":
                    assert "animal" in tile and not tile["fed_today"]
                    assert inv.get("WHEAT", 0) >= 1
                elif op[0] == "CARE":
                    assert "animal" in tile and tile["fed_today"] and not tile["cared_today"]
                elif op[0] == "COLLECT_FERTILIZER":
                    assert "animal" in tile and tile["fertilizer_available"]
                elif op[0] == "HARVEST":
                    assert "animal" in tile and tile["yield_units"] > 0
                elif op[0] == "PLACE" and op[1] in ANIMALS:
                    assert inv.get(op[1], 0) > 0 and "animal" not in tile
                    assert tile["kind"] == ANIMALS[op[1]]["structure"]
            for order in action["market"]:
                if order[0] == "SELL":
                    assert 0 < order[2] <= stock[order[1]]
                    stock[order[1]] -= order[2]


def test_control_refuses_overwrite_and_unsupported_bound(tmp_path):
    path = tmp_path / "control.py"
    build(ROOT / "main.py", path, herd_limit=6)
    with pytest.raises(FileExistsError):
        build(ROOT / "main.py", path)
    with pytest.raises(ValueError):
        build(ROOT / "main.py", tmp_path / "bad.py", herd_limit=25)
