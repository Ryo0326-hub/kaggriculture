"""Spatial investment, deadline, and resource contracts for expanded farms."""

from copy import deepcopy
from hashlib import sha256

from kaggle_environments import make
from kaggle_environments.envs.kaggriculture import kaggriculture as engine

import main
from evaluate import ROOT, run_match


def test_step_7_control_is_the_exact_server_validated_source():
    assert sha256((ROOT / "baselines/step_7.py").read_bytes()).hexdigest() == (
        "5ec112bd59eae75b2da53b4a35754a1d9c4261a6eb35677fef0b1d231e5b7a41"
    )


def test_next_quadrant_matches_engine_and_does_not_mutate_observation():
    env = make("kaggriculture", configuration={"seed": 17})
    obs = env.state[0].observation
    before = deepcopy(obs)
    _, owned = main.farm_sites(obs)
    _, expanded = main.farm_sites(obs, True)
    assert obs == before
    assert len(owned) == 15 and len(expanded) == 40
    assert set(expanded) - set(owned) == {(x, y) for x in range(5, 10) for y in range(5)}
    engine._do_buy_land(obs.farms[0], 10)
    assert main.farm_sites(obs)[1] == expanded
    assert obs.farms[0]["money"] == 2000


def test_tours_cover_every_site_once_with_actual_travel_and_service_bounds():
    access = ((4, 4), (4, 5), (5, 4), (5, 5))
    nodes = tuple(((x, y), 2) for x in range(3, 8) for y in range(2, 5))
    routes, durations, feasible = main.farm_tours(nodes, access, 21)
    assert feasible
    assert sorted(p for route in routes for p in route) == sorted(dict(nodes))
    for route, reported in zip(routes, durations):
        for start in access:
            moves = main.distance(start, route[0])
            moves += sum(main.distance(a, b) for a, b in zip(route, route[1:]))
            moves += min(main.distance(route[-1], a) for a in access)
            assert moves + sum(dict(nodes)[p] for p in route) + 3 <= reported <= 21
    assert not main.farm_tours((((0, 0), 20),), access, 21)[2]


def test_last_strawberry_output_is_harvested_before_expiry_instead_of_watered():
    tile = engine._new_plant("STRAWBERRY", 0, 24)
    tile.update(yield_units=2, consecutive_unwatered=1)
    assert main.crop_job(tile, 16, 29)[0] == "HARVEST"
    assert main.crop_job(tile, 17, 29)[0] == "HARVEST"


def test_land_cost_is_paid_before_receipts_and_has_no_terminal_salvage():
    env = make("kaggriculture", configuration={"seed": 17})
    obs = env.state[0].observation
    obs.update(day=29, hour=0, step=696)
    base = main.production_projection(obs, env.configuration, main.MARKET, routed=True)
    land = main.production_projection(
        obs, env.configuration, main.MARKET, routed=True, land_cost=1000
    )
    assert land["value"] == base["value"] - 1000
    assert land["min_cash"] == base["min_cash"] - 1000
    orders, report = main.expansion_investment(obs, env.configuration, main.MARKET, [["PASS"]], [])
    assert not orders and report["chosen"] is None


def test_new_installation_keeps_its_first_feed_when_route_partition_changes():
    env = make("kaggriculture", configuration={"seed": 17})
    obs = env.state[0].observation
    obs.update(day=18, hour=14, step=446)
    farm = obs.farms[0]
    sites, _ = main.farm_sites(obs)
    for site in sites:
        tile = engine._new_animal("SHEEP", 0)
        tile.update(fed_today=True, cared_today=True, fertilizer_available=False)
        farm["tiles"][site[1]][site[0]] = tile
    target = sites[-1]
    farm["tiles"][target[1]][target[0]] = engine._new_animal("SHEEP", 18)
    farm["hands"] = [[4, 4] for _ in range(9)]
    farm["hands"][-1] = list(target)
    obs.private["inventories"] = [{} for _ in range(10)]
    obs.private["inventories"][-1]["WHEAT"] = 1
    action, detail = main.expansion_turn(obs, env.configuration)
    assert detail["routing"]["mode"] == "shared"
    assert action["hands"][-1] == ["FEED"]
    engine._apply_unit_action(farm, obs.private, 9, action["hands"][-1], 10, 18, 24)
    action, _ = main.expansion_turn(obs, env.configuration)
    assert action["hands"][-1] == ["CARE"]


def test_expansion_actions_are_pure_and_do_not_depend_on_seed():
    env = make("kaggriculture", configuration={"seed": 17})
    obs = env.state[0].observation
    obs.update(day=9, hour=1, step=217)
    obs.farms[0]["money"] = 20000
    before = deepcopy(obs)
    action, report = main.expansion_turn(obs, env.configuration)
    assert obs == before
    assert (action, report) == main.expansion_turn(obs, dict(env.configuration, seed=999))
    assert len(action["market"]) <= 10


def test_expanding_control_is_independent_and_creates_meaningful_supply():
    code = (ROOT / "opponents/expanding_mixed.py").read_text()
    assert "import main" not in code and "baselines" not in code
    row, env = run_match(str(ROOT / "opponents/expanding_mixed.py"), "pass", 17, 0)
    assert row["outcome"] != "error"
    assert len(env.steps[-1][0].observation.farms[0]["unlocked_quadrants"]) >= 2
    assert row["economics"]["candidate"]["harvested_units"]["STRAWBERRY"] >= 100
    assert row["economics"]["candidate"]["animals_escaped"] == 0
