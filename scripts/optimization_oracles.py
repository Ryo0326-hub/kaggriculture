"""Small independent economic oracles, not a game engine or policy forecaster.

All enumerations are bounded, static decision problems. They never apply an
agent command to a farm, generate a next observation, or advance game time.
"""

from itertools import product


def linear_sale_receipts(quantity, rival_quantity=0, *, base=100, slope=1, inventory=10000):
    """One simultaneous SELL order each, at an explicitly linear test market.

    Both players receive the pre-commit quote for unit k. Rival sales after
    our last unit cannot change our already-booked receipts. At the floor,
    inventory need not increase: all remaining prices are already one coin.
    """
    if not 0 <= quantity <= 100 or not 0 <= rival_quantity <= 100:
        raise ValueError("Sale oracle is limited to 100 units per player")
    return sum(
        max(1, round(base - slope * (inventory - 10000 + k + min(k, rival_quantity))))
        for k in range(quantity)
    )


def best_reply(payoffs, probabilities):
    """Expected-profit maximizing pure response under a supplied belief."""
    if abs(sum(probabilities) - 1) > 1e-9 or any(p < 0 for p in probabilities):
        raise ValueError("Probabilities must be nonnegative and sum to one")
    if not payoffs or any(len(row) != len(probabilities) for row in payoffs.values()):
        raise ValueError("Payoff rows must match the supplied opponent states")
    values = {
        name: sum(p * value for p, value in zip(probabilities, row, strict=True))
        for name, row in payoffs.items()
    }
    best = max(values.values())
    return {name for name, value in values.items() if abs(value - best) < 1e-9}, best


def robust_reply(payoffs, *, regret=False):
    """Pure maximin/minimax-regret actions; neither implies a Nash equilibrium."""
    if not payoffs or len({len(row) for row in payoffs.values()}) != 1:
        raise ValueError("A nonempty rectangular payoff matrix is required")
    if not next(iter(payoffs.values())):
        raise ValueError("At least one opponent state is required")
    if regret:
        benchmarks = [max(column) for column in zip(*payoffs.values(), strict=True)]
        values = {
            name: max(b - x for b, x in zip(benchmarks, row, strict=True))
            for name, row in payoffs.items()
        }
        best = min(values.values())
    else:
        values = {name: min(row) for name, row in payoffs.items()}
        best = max(values.values())
    return {name for name, value in values.items() if value == best}, best


def exact_portfolio(offers, *, cash, labor, space):
    """Binary capital/action/space allocation, at most eight indivisible offers.

    Offers are (name, capital, actions, tiles, net_profit). The profit already
    includes all recurring costs. Idle is feasible; negative margin is optional.
    """
    if len(offers) > 8:
        raise ValueError("Portfolio oracle permits at most eight offers")
    best, selections = 0, set()
    for bits in product((0, 1), repeat=len(offers)):
        chosen = [offer for offer, take in zip(offers, bits, strict=True) if take]
        if any(
            sum(o[column] for o in chosen) > limit
            for column, limit in ((1, cash), (2, labor), (3, space))
        ):
            continue
        value = sum(o[4] for o in chosen)
        names = tuple(o[0] for o in chosen)
        if value > best:
            best, selections = value, {names}
        elif value == best:
            selections.add(names)
    return best, selections


def exact_assignment(positions, visits, *, now, final_action=None, access=()):
    """Maximum-value matching of immediate visits, not a multi-visit route plan.

    Each visit has pos, value, actions and deadline. Each worker gets at most
    one visit. Optional final_action adds explicit return/deposit feasibility.
    Hard bound: four workers and six visits (at most 7**4 assignments).
    """
    if len(positions) > 4 or len(visits) > 6:
        raise ValueError("Assignment oracle permits four workers and six visits")
    if final_action is not None and not access:
        raise ValueError("Terminal delivery requires shed access coordinates")
    best, winners = 0, []
    for choices in product(range(-1, len(visits)), repeat=len(positions)):
        active = [j for j in choices if j >= 0]
        if len(active) != len(set(active)):
            continue
        value, feasible = 0, True
        for pos, j in zip(positions, choices, strict=True):
            if j < 0:
                continue
            visit = visits[j]
            target = visit["pos"]
            cost = sum(abs(a - b) for a, b in zip(pos, target, strict=True)) + visit["actions"]
            if now + cost - 1 > visit["deadline"]:
                feasible = False
                break
            if final_action is not None:
                home = min(sum(abs(a - b) for a, b in zip(target, s, strict=True)) for s in access)
                if now + cost + home > final_action:
                    feasible = False
                    break
            value += visit["value"]
        if feasible and value > best:
            best, winners = value, [choices]
        elif feasible and value == best:
            winners.append(choices)
    return best, winners


def exact_deposits(goods, prices, space):
    """Constant-price terminal capacity allocation; one item per worker.

    goods contains (item, carried_quantity) per worker already at shed access.
    Choosing zero means PASS; a positive partial amount means PLACE. This is
    cash arithmetic on a fixed state, not execution of those commands.
    """
    if len(goods) > 4 or any(not 0 <= n <= 6 for _, n in goods):
        raise ValueError("Deposit oracle permits four workers with six units each")
    best, winners = 0, []
    for quantities in product(*(range(n + 1) for _, n in goods)):
        if sum(quantities) > space:
            continue
        value = sum(n * prices[item] for n, (item, _) in zip(quantities, goods, strict=True))
        if value > best:
            best, winners = value, [quantities]
        elif value == best:
            winners.append(quantities)
    return best, winners
