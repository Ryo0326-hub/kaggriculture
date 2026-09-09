from collections import deque

import pytest

from baselines.step_1 import distance, shortest_route


def grid_optimum(start, targets, size=4):
    """Independent oracle: breadth-first search over grid position and visited-target mask."""
    bits = {target: 1 << i for i, target in enumerate(targets)}
    initial = (start, bits.get(start, 0))
    queue = deque([(initial, 0)])
    seen = {initial}
    while queue:
        (position, mask), steps = queue.popleft()
        if mask == (1 << len(targets)) - 1:
            return steps
        x, y = position
        for next_position in ((x - 1, y), (x + 1, y), (x, y - 1), (x, y + 1)):
            if not all(0 <= value < size for value in next_position):
                continue
            state = (next_position, mask | bits.get(next_position, 0))
            if state not in seen:
                seen.add(state)
                queue.append((state, steps + 1))
    raise AssertionError("Targets unreachable")


@pytest.mark.parametrize(
    "start,targets",
    [
        ((0, 0), [(0, 1), (1, 0), (0, 3), (3, 0)]),
        ((1, 1), [(1, 1), (2, 1), (1, 2), (2, 2)]),
        ((3, 3), [(0, 0), (1, 2), (2, 1)]),
        ((0, 0), []),
    ],
)
def test_route_matches_independent_grid_search(start, targets):
    route = shortest_route(start, targets)
    assert set(route) == set(targets)
    assert len(route) == len(targets)
    path = (start, *route)
    assert sum(distance(a, b) for a, b in zip(path, path[1:])) == grid_optimum(start, targets)


def test_solver_bounds_factorial_work():
    with pytest.raises(ValueError, match="at most four"):
        shortest_route((0, 0), [(x, 0) for x in range(5)])
