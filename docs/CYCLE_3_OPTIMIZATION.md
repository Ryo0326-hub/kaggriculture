# Cycle 3 — when fertilizer changes the feasible schedule

The useful change is a crop-specific timing correction. Strawberry fertilizer is checked during the overnight production update. Both watering and fertilizing must occur before that update, but either can happen first. Wheat receives its fertilizer bonus immediately when watered, so fertilizing it afterward cannot change today's yield.

Step 8 excluded all watered crops from fertilizer consideration. Its urgent watering branch also bypassed the optional fertilizer branch. The experiment restores two strawberry schedules: fertilize after watering, and fertilize immediately before urgent watering when the worker is already at the crop, carries fertilizer, and has at least two actions left. With only one action remaining, survival watering wins.

The implementation is in [the timing experiment](../experiments/timing.py). The [results](CYCLE_3_RESULTS.md) record the selected artifact and its release status; experimental code alone is not evidence of a stronger submitted bot.

A [source-matched decision example](examples/cycle-3-post-water-fertilizer.json) shows worker 0 applying fertilizer at `(1, 1)` in seed 9201, state 327. The strawberry was already watered. Its estimated net value was 290.1 coins, so the new rule admitted the action that Step 8's eligibility rule excluded. That number is a forecast, not a claim that this single action ultimately earned exactly 290.1 coins.

## CO connection: precedence constraints

For wheat, the useful precedence is `fertilize → water → harvest`. For strawberry production, the constraints are `fertilize → night` and `water → night`. There is no required precedence edge between those two actions. The old rule imposed an unnecessary edge and removed feasible, profitable schedules.

This is a scheduling constraint correction, not a new global integer-programming solver. Worker-to-job reservations remain integral: a worker receives one action, one worker reserves each crop target, and shared fertilizer pickups cannot exceed the stock left after earlier reservations. Existing livestock commitments, newborn watering, survival and terminal delivery rules still apply.

## Economics: fertilizer has an opportunity cost

The experiment retains the existing valuation model rather than changing the investment model simultaneously:

`estimated net value = 0.85 × estimated extra crop receipts − fertilizer sale quote − 8`

The 0.85 factor is a forecast haircut. The eight-coin allowance approximates pickup/application work and a short detour. Neither is a measured LP dual price. Fertilizer collected from an animal still has value because it could be sold; it is not a free input. Already-spent acquisition costs and already-paid wages should not be charged a second time.

A strawberry application can cover two production events: fertilizing on age 9 remains active on ages 9, 10 and 11, and can boost the overnight outputs at ages 10 and 12 if their preceding days are watered. The forecast excludes events beyond the last playable day. It also rejects a new application when at least three berries are already held: the next base berry would fill the four-unit plant capacity, leaving no room for an immediate incremental berry. It does not assume an unplanned future harvest will rescue that application.

The timing correction changes which existing units can be used profitably. The investment functions, opening enumeration, livestock routes, original fertilizer purchase-admission function and hiring calculation remain unchanged. Tests compare their source with frozen Step 8. The dispatcher's fertilizer retention can change because a watered strawberry is now an eligible job. Subsequent cash, market supply and crop state can change later orders under the same investment/hiring rules; identical realized orders are not claimed.

## Harvest timing: an option tested, not automatically adopted

The separate wheat experiment compares harvesting at ages 2–3 with waiting for the planned age-4 harvest. It includes today's possible water bonus, remaining growth under already-active fertilizer, visible competing wheat and current town demand. It charges a two-coin opportunity allowance for each future water action avoided. It does not assume a larger future farm or change hiring rules.

That allowance is only a heuristic value for scarce time. Saving an action on a farm with idle paid workers need not save any cash or enable a useful extra job. In the controlled fixtures, early harvest reduced cash on the larger farms while wages stayed identical. In all eight normal-start development games, the harvest-only policy emitted exactly the same actions as Step 8. Combining it with fertilizer also emitted exactly the same actions as fertilizer-only. It therefore adds no demonstrated competitive value and is excluded from the selected behavior.

This connects directly to complementary slackness from CO250: when an LP resource-capacity constraint is slack, its associated optimal shadow price is zero. A fixed positive price for an otherwise idle worker action can make an early harvest appear worthwhile while destroying saleable yield. A future refinement should estimate action value from displaced profitable work, rather than assume every saved action earns money.

## What the tests prove and what they do not

Engine tests verify an actual extra strawberry after post-water fertilizer, the fertilizer-then-water sequence, one-action survival priority, the final productive night, no duplicate application by two workers on one crop, no retroactive wheat growth, and rejection for active fertilizer, a full plant, the wrong date, low value or production after termination. Disabled timing is compared with Step 8; the frozen investment and hiring rules are checked separately.

Installed-portfolio games count executed inventory gains and reconcile bank cash. Normal games and fresh matched opponents test whether those gains survive changes in market prices and rival behavior. A larger berry harvest alone is not sufficient: added supply can reduce selling prices for both farms. The valuation still approximates future prices and joint delivery capacity. This cycle does not claim optimal fertilizer allocation, exact shadow prices, or a Nash equilibrium.
