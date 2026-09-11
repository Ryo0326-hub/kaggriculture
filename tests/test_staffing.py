"""Dated workforce bounds and ordinary-night/final delivery constraints."""

from copy import deepcopy
from hashlib import sha256
from itertools import permutations
from pathlib import Path

import pytest
from kaggle_environments import make

import main as submitted
from baselines import step_8
from experiments import staffing as main
from scripts.benchmark_staffing import installed_environment


@pytest.mark.parametrize("closed", [False, True])
def test_route_menu_matches_exhaustive_travel_with_and_without_terminal_edge(closed):
    sites = ((4, 1), (3, 2), (1, 3))
    access = ((4, 4), (4, 5), (5, 4), (5, 5))
    options = main.route_geometry(sites, access, closed)
    for mask, order, distance in options:
        members = [i for i in range(len(sites)) if mask & (1 << i)]
        expected = min(
            max(main.distance(a, sites[route[0]]) for a in access)
            + sum(main.distance(sites[a], sites[b]) for a, b in zip(route, route[1:]))
            + (min(main.distance(sites[route[-1]], a) for a in access) if closed else 0)
            for route in permutations(members)
        )
        assert distance == expected
        assert sorted(order) == members


def test_dated_staffing_does_not_charge_empty_days_for_mature_crop_round_trips():
    env = installed_environment(17, 2)
    obs = env.state[0].observation
    fields = main.farm_sites(obs)[1]
    plants = [
        (p, obs.farms[0]["tiles"][p[1]][p[0]])
        for p in fields
        if isinstance(obs.farms[0]["tiles"][p[1]][p[0]], dict)
    ]
    before = deepcopy(obs)
    bound = main.crop_route_staffing(obs, env.configuration, fields, plants, {}, {}, True)
    assert not bound["nodes"] and not bound["routes"]
    assert obs == before


def test_final_day_bound_keeps_explicit_return_even_when_overnight_is_enabled():
    env = installed_environment(17, 2)
    obs = env.state[0].observation
    obs.update(day=29, hour=0, step=696)
    tile = {
        "kind": "PLANT",
        "crop": "STRAWBERRY",
        "planted_day": 19,
        "yield_units": 2,
        "watered_today": False,
        "consecutive_unwatered": 0,
        "fertilized_until_day": -1,
    }
    nodes = [((0, 0), tile)]
    bound = main.crop_route_staffing(obs, env.configuration, [], nodes, {}, {}, True)
    assert bound["return_to_shed"]
    assert bound["steps"] == main.farm_tours((((0, 0), 1),), main.shed_access(obs), 21)[1]


def test_disabled_flags_preserve_step_8_actions_with_capital_investment_removed(monkeypatch):
    # The immutable reference only has its purchase-admission functions disabled;
    # dispatch, input purchases, prices and labor behavior remain unchanged.
    monkeypatch.setattr(
        step_8,
        "expansion_investment",
        lambda obs, cfg, params, commands, market, max_land=3: (market, {}),
    )
    monkeypatch.setattr(
        step_8, "production_orders", lambda obs, cfg, params, market, *args: (market, {})
    )
    for quadrants in (1, 2, 3):
        env = installed_environment(17, quadrants)
        for _ in range(30):
            actions = []
            for seat in (0, 1):
                obs = env.state[seat].observation
                actual = main.expansion_turn(obs, env.configuration, investments=False)[0]
                expected = step_8.expansion_turn(obs, env.configuration)[0]
                assert actual == expected
                actions.append(actual)
            env.step(actions)


def test_legacy_standard_start_still_matches_frozen_artifact():
    env = make("kaggriculture", configuration={"seed": 17})
    for _ in range(48):
        actions = []
        for seat in (0, 1):
            obs = env.state[seat].observation
            assert main.agent(obs, env.configuration) == step_8.agent(obs, env.configuration)
            assert submitted.agent(obs, env.configuration) == step_8.agent(obs, env.configuration)
            actions.append(main.agent(obs, env.configuration))
        env.step(actions)


def test_server_validated_step_8_is_preserved_byte_for_byte():
    assert sha256(Path(step_8.__file__).read_bytes()).hexdigest() == (
        "63dbf4381d8607cbd681f5296749f4f8af4cc37d0181f97d6b8931f6078d3f72"
    )


@pytest.mark.parametrize("day", [0, 8, 12, 28, 29])
@pytest.mark.parametrize("overnight", [False, True])
def test_forecast_animal_crew_matches_dispatch_on_production_and_terminal_dates(day, overnight):
    env = installed_environment(17, 1)
    obs = env.state[0].observation
    obs.update(day=day, hour=0, step=24 * day)
    animals = []
    for y, row in enumerate(obs.farms[0]["tiles"]):
        for x, tile in enumerate(row):
            if isinstance(tile, dict) and "crop" in tile:
                row[x] = None
            elif isinstance(tile, dict) and "animal" in tile:
                animals.append({**tile, "site": (x, y)})
    _, detail = main.plan_turn(obs, env.configuration, force_shared=True, overnight=overnight)
    forecast = main.projected_staffing(obs, env.configuration, day, animals, [], overnight, True)
    assert forecast["feasible"]
    assert forecast["animal_workers"] == detail["routing"]["target_hands"] + 1


def test_forecast_charges_thirteenth_worker_and_excludes_already_paid_labor(monkeypatch):
    env = make("kaggriculture", configuration={"seed": 17})
    obs = env.state[0].observation
    obs.update(day=29, hour=0, step=696)
    obs.farms[0]["hires_today"] = 11
    # Isolate cash conservation from the route heuristic: the next, twelfth hand
    # costs 144, while the eleven already paid hands cost 232 in total.
    monkeypatch.setattr(main, "projected_staffing", lambda *args: {"workers": 13, "feasible": True})
    projection = main.production_projection(
        obs, env.configuration, main.MARKET, routed=True, staffing=(True, True)
    )
    assert projection["wages"] == 144
    assert projection["daily"][0]["spending_before_receipts"] == 144


def test_forecast_rejects_unknown_asset_location_without_mutating_observation():
    env = make("kaggriculture", configuration={"seed": 17})
    obs = env.state[0].observation
    before = deepcopy(obs)
    forecast = main.projected_staffing(
        obs, env.configuration, 1, [{"animal": "COW", "placed_day": 1}], [], True, True
    )
    assert not forecast["feasible"]
    assert obs == before


def test_forecast_flag_has_no_effect_when_capital_purchases_are_disabled():
    env = installed_environment(43, 3)
    obs = env.state[0].observation
    args = dict(overnight=True, dated_staffing=True, investments=False)
    expected = main.expansion_turn(obs, env.configuration, **args)[0]
    assert (
        main.expansion_turn(obs, env.configuration, staffing_forecast=True, **args)[0] == expected
    )
