"""Independent cover oracle, inventory edge cases, and controlled engine scenarios."""

import inspect
from itertools import permutations

import pytest
from kaggle_environments import make
from kaggle_environments.envs.kaggriculture import kaggriculture as engine

import main
from baselines import step_4
from scripts.benchmark_routes import fixed_herd_game


def partitions(items):
    if not items:
        yield []
        return
    first, *rest = items
    for groups in partitions(rest):
        yield [(first,), *groups]
        for i, group in enumerate(groups):
            if len(group) < 4:
                yield [*groups[:i], (first, *group), *groups[i + 1 :]]


@pytest.mark.parametrize("capacity", [15, 18, 21])
def test_cover_matches_exhaustive_partition_and_permutation_oracle(capacity):
    sites = ((4, 4), (3, 4), (4, 3), (2, 4), (3, 3), (4, 2))
    access = ((4, 4), (4, 5), (5, 4), (5, 5))
    work = (4, 4, 4, 4, 4, 6)

    def dist(a, b):
        return abs(a[0] - b[0]) + abs(a[1] - b[1])

    def duration(group):
        return min(
            max(dist(a, sites[order[0]]) for a in access)
            + sum(dist(sites[a], sites[b]) for a, b in zip(order, order[1:]))
            + min(dist(sites[order[-1]], a) for a in access)
            + 2
            + sum(work[i] for i in order)
            for order in permutations(group)
        )

    choices = []
    for groups in partitions(list(range(len(sites)))):
        durations = [duration(group) for group in groups]
        if max(durations) <= capacity:
            choices.append((len(groups), sum(durations)))
    routes, lengths, feasible = main.route_cover(sites, work, access, capacity)
    assert feasible
    assert (len(routes), sum(lengths)) == min(choices)
    assert sorted(p for route in routes for p in route) == sorted(sites)
    assert max(lengths) <= capacity


def test_cached_cover_and_infeasible_fallback_are_deterministic():
    args = (((4, 4), (0, 0)), (4, 4), ((4, 4), (5, 5)), 2)
    result = main.route_cover(*args)
    assert result[0] == (((4, 4),), ((0, 0),))
    assert result[2] is False
    main.route_cover.cache_clear()
    main.route_geometry.cache_clear()
    assert main.route_cover(*args) == result
    assert main.route_cover((), (), ((4, 4),), 21) == ((), (), True)


def test_investment_equations_remain_identical_to_step_4():
    for name in ("investment_plan", "livestock_value", "animal_output"):
        assert inspect.getsource(getattr(main, name)) == inspect.getsource(getattr(step_4, name))
    assert inspect.getsource(main.station_turn).replace("def station_turn(", "def plan_turn(") == (
        inspect.getsource(step_4.plan_turn)
    )


def animal_observation():
    env = make("kaggriculture", configuration={"seed": 17})
    obs = env.state[0].observation
    for x, y in [(4, 4), (3, 4), (4, 3)]:
        obs.farms[0]["tiles"][y][x] = engine._new_animal("COW", 0)
    return env, obs


def test_worker_loads_feed_for_multiple_assigned_animals():
    env, obs = animal_observation()
    obs.private["shed"]["WHEAT"] = 6
    action, detail = main.plan_turn(obs, env.configuration, herd_limit=3)
    assert action["farmer"] == ["PICKUP", "WHEAT", 3]
    assert detail["routing"]["target_hands"] == 0


def test_production_routes_stay_protected_after_harvest():
    env, obs = animal_observation()
    obs.update(day=8, hour=0, step=192)
    obs.private["shed"]["WHEAT"] = 6
    for x, y in [(4, 4), (3, 4), (4, 3)]:
        obs.farms[0]["tiles"][y][x]["yield_units"] = 6
    _, detail = main.plan_turn(obs, env.configuration, herd_limit=3)
    assert detail["routing"]["target_hands"] == 2
    assert all(len(route) == 1 for route in detail["routing"]["routes"])
    obs.farms[0]["tiles"][4][4]["yield_units"] = 0
    _, after = main.plan_turn(obs, env.configuration, herd_limit=3)
    assert after["routing"]["routes"] == detail["routing"]["routes"]


def test_pending_installation_keeps_station_execution():
    env = make("kaggriculture", configuration={"seed": 17})
    obs = env.state[0].observation
    obs.private["shed"]["SHEEP"] = 1
    action, detail = main.plan_turn(obs, env.configuration)
    assert action == step_4.plan_turn(obs, env.configuration)[0]
    assert detail["routing"]["mode"] == "stations"


def test_carried_produce_can_restore_cash_instead_of_waiting_for_feed():
    env, obs = animal_observation()
    obs.farms[0]["money"] = 0
    obs.private["inventories"][0]["MILK"] = 2
    action, _ = main.plan_turn(obs, env.configuration, herd_limit=3)
    assert action["farmer"] == ["DROP"]
    assert ["SELL", "MILK", 2] in action["market"]
    env.step([action, {}])
    assert env.state[0].observation.farms[0]["money"] > 0


@pytest.mark.parametrize("seat", [0, 1])
def test_installed_mixed_herd_preserves_output_and_reduces_wages(seat):
    row = fixed_herd_game(17, seat, ["COW", "SHEEP"] * 5)
    assert row["statuses"] == ["DONE", "DONE"]
    assert row["recorded_states"] == 720
    assert row["equal_output"]
    assert row["shared"]["wages"] < row["station"]["wages"]
    assert row["shared"]["multi_animal_worker_days"] > 0
    for policy in ("shared", "station"):
        assert row[policy]["unfed_animal_days"] == 0
        assert row[policy]["uncared_required_animal_days"] == 0
        assert row[policy]["escapes"] == 0
        assert row[policy]["unsold_units"] == 0
