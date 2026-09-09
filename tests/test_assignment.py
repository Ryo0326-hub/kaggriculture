from itertools import product
from random import Random

import pytest

from main import MAX_WORKERS, maximum_assignment


def value(assignment, weights):
    return sum(weights[w][j] for w, j in enumerate(assignment) if j >= 0)


def feasible(assignment, weights, needs_seed, budget):
    chosen = [j for j in assignment if j >= 0]
    return (
        len(chosen) == len(set(chosen))
        and sum(needs_seed[j] for j in chosen) <= budget
        and all(j < 0 or weights[w][j] is not None for w, j in enumerate(assignment))
    )


def test_assignment_repairs_the_worker_order_greedy_trap():
    # Greedy gives worker 0 task 0 (10), leaving 0 for worker 1. Joint assignment earns 18.
    weights = [[10, 9], [9, 0]]
    assert maximum_assignment(weights, [False, False], 0) == (1, 0)


def test_seed_quota_and_infeasible_edges():
    weights = [[100, 80, None], [90, None, 50]]
    answer = maximum_assignment(weights, [True, True, False], 1)
    assert answer == (0, 2)
    assert value(answer, weights) == 150


def test_exact_assignment_against_independent_brute_force():
    rng = Random(7250)
    for _ in range(50):
        n, m = rng.randint(1, 4), rng.randint(0, 5)
        weights = [[rng.choice([None, -3, 0, 2, 7, 11]) for _ in range(m)] for _ in range(n)]
        seeds = [rng.choice([True, False]) for _ in range(m)]
        budget = rng.randint(0, n)
        answer = maximum_assignment(weights, seeds, budget)
        assert feasible(answer, weights, seeds, budget)
        optimum = max(
            value(a, weights)
            for a in product(range(-1, m), repeat=n)
            if feasible(a, weights, seeds, budget)
        )
        assert value(answer, weights) == optimum
        assert maximum_assignment(weights, seeds, budget) == answer


def test_bounded_assignment_rejects_oversized_inputs():
    with pytest.raises(ValueError, match="bounded"):
        maximum_assignment([[] for _ in range(MAX_WORKERS + 1)], [], 0)
