# Cycle 12 — input feasibility before optional yield

Workflow update: the user stopped local match simulations during this cycle and will use Kaggle runs for competitive evaluation. The candidate is packaged for that server test; Cycle 3 remains protected. The earlier local protocol is historical, and no final paired qualification is claimed. Future full-game simulations require a new explicit request.

The Cycle 11 audit found a gap between an investment forecast and its execution: four-unit carrot forecasts could win a purchase comparison, yet the urgent work dispatcher watered those carrots without fertilizer. An input purchase could also raise its own price enough to cancel the next turn's retention target. This experiment connects current fertilizer value to a feasible worker sequence and removes uncommitted future fertilizer yield from carrot investment forecasts.

## What is already in the submitted agent

| Game component | Implemented behavior | Remaining performance work |
| --- | --- | --- |
| Animals | Buy and place cows/sheep; feed, care, harvest milk/wool; share worker routes | Egg-producing geese are modeled but excluded from the current purchase menu. Test their full acquisition, feed, care, labor and demand economics separately. |
| Fertilizer | Collect animal fertilizer; reserve, buy, apply or sell it; Cycle 3 has validated strawberry timing | Carrot input execution is experimental here. Value competes with selling the fertilizer and with the worker's other jobs. |
| Land | Compare crop batches on owned land with batches paying for another quadrant | Current policy allows at most three total quadrants. Relaxing admission alone did not qualify in Cycle 4; bigger farms require profitable service capacity. |
| Market | Observe shared inventory/prices and shops; model dated sales, feed costs and visible rival production; sell delivered output while retaining inputs | Future demand and rival behavior remain approximate. Earlier uncertainty challengers did not earn promotion. More own receipts alone need not improve wins. |

These features are implemented to different depths. A game action's existence is not a reason to force its use. Selective maintenance, goose admission, larger herds, land/crew planning and opponent-sensitive trading remain evidence-driven candidates. The immediate priority comes from a measured execution gap, not from crop-only scope.

## CO250 connection: integer assignment and resource constraints

Let `x[i,j]` be one if available worker `i` takes a complete fertilizer bundle for carrot plot `j`. The conceptual objective is `max sum(v[i,j] * x[i,j])`, subject to at most one chosen bundle per worker and per plot, available fertilizer stock, buying capacity, cash and each worker's remaining turns. The binary decisions are an integer assignment problem. The implementation uses a small greedy feasible assignment by estimated net value per occupied turn; it does not solve an LP or certify an optimum.

`v[i,j]` equals the existing discounted value of the incremental carrot output, minus the fertilizer's opportunity cost, minus eight coins for each extra action relative to ordinary watering. A carried input needs an application action; a shed input also needs pickup and any detour. A purchased input requires a wait because market orders happen after unit actions. The eight-coin allowance is inherited heuristic pricing of scarce worker time, analogous to a shadow price, not a measured optimal dual variable.

An age-three bundle must leave time for harvest. On the final day it must also leave a path to shed access and a deposit action so the product can be sold. No worker is borrowed from unfinished animal obligations, newborn watering or a non-carrot urgent assignment. Shared shed units are reserved before other crop pickups, then final commands are reconciled in actual worker order.

## Economics: owned fertilizer is not free

Animal fertilizer has a sale opportunity cost. Buying removes market inventory and changes the next quote. Every selected bundle must remain profitable at the quote after the complete proposed input purchase, not just at the pre-purchase quote. Cash is rechecked after the existing feed, hire and sale orders, with the existing 150-coin floor and order/shed limits. Input buying is restricted to assigned workers currently at shed access with enough turns to pick up and use it later.

The current bundle is re-evaluated from observations each turn; it is not a binding multi-turn contract or a guarantee against later rival price changes. No hidden seed, future shop sequence, rival private inventory or recorded future action is read. Model uncertainty and opportunity cost are still approximations.

## Conservative forecast and option value

New carrot columns promise ordinary three-unit growth. An already applied fertilizer is visible in the planning snapshot and can justify four-unit output. Optional future fertilizing is treated as an opportunity, not as guaranteed receipts from unassigned labor. That can make investment forecasts conservative and change crop choices; it is part of this preregistered experiment. Original crop columns, opening portfolios, actual hiring, land rules and investment ranking remain fixed.

The useful distinction is between a feasible current input action and a hoped-for future action. More fertilizer applications, higher physical yield or a cleaner forecast alone cannot establish competitive superiority. Under the updated workflow, the user uploads a valid candidate and supplies server results for the next decision. See the historical frozen [plan](CYCLE_12_PLAN.md), [results](CYCLE_12_RESULTS.md) and [current workflow](PERFORMANCE_PLAN.md).
