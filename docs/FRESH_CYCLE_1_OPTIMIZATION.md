# Fresh Cycle 1 — economics and CO notes

**Subsequent test evidence:** [245 optimization cases](OPTIMIZATION_TESTS.md)
identify four unmet targets in the preserved policy: value-aware deadline
selection, joint worker assignment, terminal shed capacity and rival service
calibration. The notes below describe the current implementation, not a claim
that these optimization targets are satisfied.

**Research-led extension:** [137 additional scenarios](RESEARCH_SCENARIO_TESTS.md)
add uncertainty and terminal-cash analysis, with five strict expected failures
covering three more gaps: market-slot allocation, mixed-product deposits and
rival crop maturity. No policy changes or profit-improvement claim accompany
these tests.

September 12, 2026, Toronto. This is a new policy line, independently written
from the pinned game rules. The user's request supersedes the handoff's advice
to derive from Cycle 19. No prior policy, helper extraction, opening schedule,
or reference performance comparison is used by this agent.

Source: `experiments/fresh_cycle1.py`. The submission is an exact byte copy.
No local games, engine transitions, training, model calls or paid compute were
used. Recorded states are diagnostic inputs only.

## Cash, production and investment

The objective follows the accounting identity:

`final cash = initial cash + sales - seeds - animals - feed - wages - land`.

An asset must mature, receive service, have output harvested and delivered, and
have that output sold. The policy connects those steps through complete visits,
resource reservations and terminal return budgets. Ordinary overnight transfer
is allowed; final-day trips explicitly include returning to an access tile and
depositing. The final morning includes hiring collection/delivery workers,
because yesterday's hands have expired.

Surplus sales release storage and working cash. The policy retains approximately
two days of useful feed and a small fertilizer buffer for identified jobs. It
does not speculate by holding saleable stock for unrevealed shops. Sale requests
include observed shed stock and deposits reserved earlier in the current turn,
never goods held by workers elsewhere. Spending budgets credit only one coin
per planned sale unit, the guaranteed price floor, then observe actual receipts
on the next call. This can delay reinvestment by a turn.

The market curve uses the pinned rule constants and sparse configuration
overrides. Each revealed shop instance contributes demand separately. The value
estimate projects inventory using visible capacity less revealed consumption:
own capacity receives weight 1.0, rival capacity 0.7, and pending seeds add
committed exposure. It does not know rival private stock or future sale timing.
Value prices blend 40% of today's quote with 60% of the projected quote. These
are hand-authored heuristics, not trained or validated coefficients.

The marginal admission score is:

`margin = output value + fertilizer receipts - purchase - feed/input costs
          - 7 × estimated actions`,

`score = margin / estimated actions`.

Crops pay for seed, service and an approximate fertilizer allowance. Animals
pay for purchase, remaining feed and repeated service, and can earn product and
fertilizer receipts. Remaining-season checks exclude investments with no useful
production window. Quantities and labor remain coarse estimates: full bonuses
depend on successful service, and single crops may yield less than estimated
in short late-season windows. Positive model margin is not realized profit.

The seven-coin action charge makes labor scarcity explicit. In CO250 terms it
resembles a penalty on a constrained resource; it is **not** an LP dual price.
No primal LP is solved, no dual certificate exists, and optimality is not claimed.

Admission also checks cash, pending seeds/animals, land and estimated daily
service work. Bounds are four seeds or one animal per turn, eight pending seeds,
two pending animals, sixteen useful/pending animals and a per-crop concentration
limit. There is no fixed opening purchase sequence. Central installation space
is reserved while an animal can repay: six nearest owned cells per quadrant,
up to sixteen. Matching empty structures and carried animals at their matching
structures receive placement preference.

## Matching, paths and deadlines

Think of a bipartite graph with workers on one side and tile visits on the
other. An edge exists only if the worker can obtain inputs, travel, complete
the useful operations and meet the deadline. Manhattan distance models travel
because crossing locked tiles and sharing positions are legal.

Executable remembered edges are reserved first. Unassigned pairs are selected
greedily using slack, on-site service, installation priority and value per
action. Each worker has at most one visit; each tile has one owner. This is
greedy matching, **not** an optimal min-cost flow or vehicle-routing solver.

Slack combines the service deadline and remaining trip time. Final-day trips
include output delivery. Harvest before decay and deposit before termination
are separate clocks: harvesting on the decay action can still allow a later
deposit. A rescue interrupts a worker only for a specific unclaimed essential
job with at most one spare action, sufficient displaced-job slack, and greater
estimated value. That exact replacement is assigned immediately. Urgency already
covered by another worker cannot interrupt an existing route. On-site animal
visits and installations are protected.

The supplied reversal history is tested using only the new agent's memory.
It retains one worker-3 target at all three witness observations. The recorded
positions still come from the old game's actual actions: this demonstrates
requested target continuity, not the candidate's completed routes or earnings.

## Visits, inventories and timing

Animal visits normally bundle feed, available harvest, care and fertilizer
collection. Crop visits can bundle fertilizer, required water and harvest.
Operations are regenerated from observed state each call; issuing a command
does not prove it succeeded. At hard deadlines, optional operations can be
omitted to salvage feeding/watering. Missing feed does not block independent
harvest/collection.

The resource constraints are concrete integer bounds:

- Plant commands cannot exceed observed shared seed counts.
- Reservations cannot exceed observed shed inputs; workers pick up before use.
- Productive visits have one tile owner.
- Deposits reserve capacity in actual farmer/hand execution order.
- Unit work precedes market orders, so purchases cannot supply earlier work.

Small wheat batches reduce repeated trips while preserving other jobs' input
reservations. Selective deposits retain overflow; DROP requires enough room
for all goods. Storage pressure can trigger an early deposit. This establishes
current-turn feasibility, not an optimal future storage schedule.

Water is scheduled for drought, growth bonuses or repeater production nights.
Only a zero-drought crop with no current bonus need may skip water. Planting
reserves time for its first water. Optional fertilizer is valued against its
sale opportunity and cannot block survival. Single-crop bonus water follows
fertilizer; repeaters may receive fertilizer after water before the boundary.

## Wages, land and what remains unverified

Staffing follows estimated remaining work and configured Fibonacci marginal
wages, capped at eleven hands. Feed is funded before hires and investments.
Feed buys use per-unit prices plus a 15% allowance for rival purchases; that
allowance does not guarantee a fill under every possible rival order. Land
requires service capacity and enough cash afterward to invest; at most three
quadrants are bought. Unused acreage earns no score.

The policy does not solve joint land/staffing/portfolio optimization or infer
the opponent's terminal wealth. Bounded checks establish selected feasibility,
continuity and packaging properties. Original-observation histories never
advance an engine and cannot establish season returns, service success rates,
wins, ratings or competitive improvement. Those require the user's Kaggle
validation and rated games. See [release evidence](FRESH_CYCLE_1_RESULTS.md).
