"""Small, static terminal cash oracles. No game state transitions or rollouts."""

from itertools import combinations


def _validate(goods, prices):
    if len(goods) > 9 or any(type(n) is not int or not 0 <= n <= 100 for n in goods.values()):
        raise ValueError("At most nine products and 100 units per product")
    if any(item not in prices or prices[item] < 1 for item in goods):
        raise ValueError("Every good needs a positive constant price")


def terminal_order_choice(goods, prices, slots):
    """Exact subset of at most nine SELL orders at declared constant prices.

    Each resource needs one order. All quantities are already in the shed.
    No price impact, other-player interference or orders to buy more goods.
    At most 512 subsets; idle is included.
    """
    _validate(goods, prices)
    if type(slots) is not int or not 0 <= slots <= 10:
        raise ValueError("At most ten market slots")
    best, winners = 0, set()
    for count in range(min(slots, len(goods)) + 1):
        for chosen in combinations(goods, count):
            value = sum(goods[item] * prices[item] for item in chosen)
            if value > best:
                best, winners = value, {chosen}
            elif value == best:
                winners.add(chosen)
    return best, winners


def terminal_deposit_choice(goods, prices, room):
    """One worker already at access: best PASS, DROP or single-product PLACE.

    Enough SELL slots for every deposited product, constant positive prices.
    DROP fills in inventory insertion order; overflow earns zero. Prefix sums
    give accepted quantities directly, without executing an action or mutating
    any observation. PLACE never needs a partial quantity smaller than room.
    """
    _validate(goods, prices)
    if type(room) is not int or not 0 <= room <= 100:
        raise ValueError("At most 100 free shed slots")
    options = {("PASS",): 0}
    prefix, drop_value = 0, 0
    for item, quantity in goods.items():
        accepted = min(quantity, max(0, room - prefix))
        drop_value += accepted * prices[item]
        prefix += quantity
        placed = min(quantity, room)
        if placed:
            options[("PLACE", item, placed)] = placed * prices[item]
    options[("DROP",)] = drop_value
    best = max(options.values())
    return best, {action for action, value in options.items() if value == best}
