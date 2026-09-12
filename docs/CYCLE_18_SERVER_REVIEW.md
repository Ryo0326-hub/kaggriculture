# Cycle 18 — two server losses and the execution gap

Reviewed September 12, 2026. The user reports a ladder rating of 545.3. The
supplied games end at 83,936–98,836 against Makise Kurisu is da Goat! (108239790)
and 61,005–99,962 against Anatoliy_Fomin (108195100). Unicorns is seat 0 in both.

All 1,438 own decisions match the audited Cycle 18 source, SHA-256
`65e0e1f6f12e797c02fff195e168e37c6969a5167ec5f9a2e9d006854b95e314`.
Both games finish DONE, all supplied stderr entries are empty, and maximum
logged callback durations are 0.240360 and 0.340031 seconds. This is behavioral
source matching, not a downloaded-upload source hash. The losses are not runtime
failures. They expose scheduling and investment dependencies missed in the audit.

## What the results establish

| Metric | Us vs Makise | Makise | Us vs Anatoliy | Anatoliy |
|---|---:|---:|---:|---:|
| Final banked coins | 83,936 | 98,836 | 61,005 | 99,962 |
| Peak productive tiles | 38 | 75 | 22 | 59 |
| Final owned quadrants | 3 | 3 | 2 | 3 |
| Peak cows | 6 | 1 | 6 | 5 |
| Peak sheep | 20 | 9 | 2 | 5 |
| Peak strawberry plants | 12 | 46 | 13 | 29 |
| Movement share of unit commands | 65.5% | 48.2% | 65.3% | 44.2% |
| Adjacent inverse-move pairs | 507 | 2 | 357 | 9 |
| Wages | 3,261 | 5,829 | 333 | 8,733 |
| Strawberries harvested | 92 | 169 | 103 | 169 |
| Milk harvested | 96 | 36 | 110 | 131 |
| Wool harvested | 201 | 154 | 39 | 112 |
| Melons harvested | 46 | 120 | 48 | 119 |

Peaks by type need not coincide. Harvest quantities include the separately
recorded night-boundary adjustments; they are not sale receipts. Requested
market quantities are not automatically fills. In particular, Anatoliy requests
42 strawberry seeds but the seed ledger confirms 32 acquisitions, including
three immediately lost newborn plants.

Two selected losses cannot establish a controlled win-rate regression against
Cycle 15. They do establish severe weaknesses in the actual submitted policy.
The older five reviewed Cycle 15 games show 38.7–41.7% movement and 148–237
adjacent reversal pairs. Those are different games, but the increased movement
and oscillation warrant a specific execution investigation.

## 1. Shared routes are repeatedly abandoned before work happens

In `production_dispatch`, routes and worker assignments are recomputed every
callback. The score selects a fresh route from urgency, current travel cost,
route size and carried inputs. It has no commitment to completing the previous
assignment. The route constructor also changes as jobs finish and the remaining
daily action budget shrinks.

Against Anatoliy, worker 3 spends decisions 196–203 alternating between (3,5)
and (4,5): EAST, WEST, EAST, WEST, EAST, WEST, EAST, WEST. Its inventory remains
empty, and it performs no service in those eight actions. The reconstructed
assignments alternate between animal service and crop/planting routes. Against
Makise, the farmer similarly alternates six times between (3,4) and (4,4) at
decisions 274–279 while carrying the same inputs.

The 507 and 357 reversal-pair counts overlap within longer runs; they must not
be multiplied by two and presented as disjoint wasted trips. Nevertheless, the
examples prove an execution defect. A route that fits the action budget on one
callback does not establish that the dispatcher follows it to completion.

## 2. The planting queue disables unrelated investment

`growth_investment` returns immediately whenever *any seed remains* in private
inventory (`experiments/growth.py`, line 551). This was intended to prevent
overbuying a backlog. In combination with low-priority planting and changing
assignments, it becomes a global barrier to growth.

Against Anatoliy, eight strawberry seeds are purchased at decision 264, UI Day
12 Turn 1. Three remain from state 311 through state 596: almost twelve days.
Cash rises from 12,525 to 44,418 over that interval. The investment evaluator
does not examine an additional cow, another crop batch or land while those seeds
remain. The last acquisition of any new productive asset is on Day 12.

Two of those seeds are finally planted at decisions 596 and 619, on Days 25
and 26. A strawberry needs ten days before first production, so neither can
produce before the season ends. One seed remains unused. The purchase-time
maturity check does not protect a seed whose actual planting is delayed.

Across the game, seed inventory blocks 160 of the 174 otherwise scheduled
investment checkpoints before the final day. This does not mean 160 profitable
investments were missed; it means their profitability was never evaluated.
In the Makise game the same barrier occurs at 96 checkpoints; its twelve-seed
berry batch also takes several days to finish planting.

## 3. Full-care forecasts exceed delivered production

The investment model assumes daily feeding, care and collection. The shared
dispatcher does not consistently deliver that service. Against Anatoliy, take
the eight animals already installed at the start of Day 13 and hold their
identities fixed. The unchanged analytic estimator predicts 135 milk and 44
wool, including yield then held on their tiles. Their actual subsequent
harvests total 94 milk and 30 wool. Both measures exclude the starting shed and
carried inventory; no animals are added afterwards and final animal-held output
is zero. Combined realized harvest is 124/179, about 69% of that forecast.

At ordinary night boundaries, 86 care opportunities that the policy itself
considers due remain unfinished in the Anatoliy game; the Makise game has 169.
Not every such miss costs one saleable unit because bonus timing, pending caps
and later care matter. They demonstrate the gap between the assumed service
schedule and execution. Feeding largely preserves survival: our animals miss
only one and ten observed existing-animal feeding nights, with no escapes.

The cheap 333-coin wage bill against Anatoliy is therefore not evidence of an
efficient profit-maximizing crew. We save on staff while leaving planting and
care incomplete. More hiring alone is not the remedy: workers first need stable,
productive assignments. The model's labor and income estimates must describe
what the dispatcher can actually execute.

## Opponent strategy and the cash gap

Makise buys the second quadrant on Day 8 and the third on Day 14; ours arrive
on Days 11 and 19. Makise develops a broad crop portfolio, with 46 peak berries,
18 tomatoes and twenty melons. We concentrate more capital in livestock:
12,400 coins in animal purchases versus 5,500, but fewer crop cohorts mature.
The two yarn shops support our sheep; the portfolio is not inherently irrational.
It simply fails to generate enough total net income. Our final day is actually
stronger: +18,790 versus +14,563, but that does not erase the earlier deficit.

Anatoliy funds larger berry and melon cohorts, replenishes wheat and accepts
a larger wage bill. By Day 13, 29 berries are already planted, versus our twelve
at that day's start and three seeds later left waiting. Its feed/crop losses
should not be copied: three animals escape, some plants die early, and final
wheat remains unliquidated. Its larger operating portfolio still wins.

| Cash account | Us vs Makise | Makise | Us vs Anatoliy | Anatoliy |
|---|---:|---:|---:|---:|
| Starting cash | 3,000 | 3,000 | 3,000 | 3,000 |
| Net product receipts, after product purchases | 101,567 | 118,055 | 65,098 | 120,705 |
| Seeds | −1,970 | −7,890 | −2,360 | −6,210 |
| Animals | −12,400 | −5,500 | −3,400 | −5,800 |
| Land | −3,000 | −3,000 | −1,000 | −3,000 |
| Wages | −3,261 | −5,829 | −333 | −8,733 |
| Final cash | **83,936** | **98,836** | **61,005** | **99,962** |

The net-product row is the reconciled cash residual after confirmed fixed-price
purchases and hires, not independently reconstructed gross revenue by product.
There are no unresolved night-boundary hiring requests. Makise generates 16,488
more net product receipts for 1,588 more other costs: exactly the 14,900 margin.
Anatoliy generates 55,607 more for 16,650 more costs: exactly 38,957.

## Improvements that did work

- Own animals do not escape, and visible own crop-to-weed transitions are normal
  zero-yield, age-17 strawberry retirements, not premature crop deaths.
- Own terminal shed, carried products and harvestable held yield are cleared.
  Unused seeds and the two immature late berries are separate failures.
- Strawberry fertilizer bonuses occur on 45/47 observed production events
  against Makise and 51/52 against Anatoliy. Input timing is substantially more
  reliable than our planting and care execution.
- Land and livestock expansion are enabled and occur. More unlocked acreage
  alone does not repair a stalled planting queue.

Wheat buying/selling also churns, but isolated equal-quantity adjacent round trips
mostly reconcile to zero cash. It is not evidence for a large hidden trading
loss. The main demonstrated failures are route continuity, planting completion,
the investment gate and overestimated service-dependent output.

## Revised priorities and responsibility for the audit gap

The earlier 40 tests and 140 isolated state checks established selected action
preconditions, inventory arithmetic, runtime and deadline boundaries. They did
not establish sustained task completion or competitive improvement. The release
was described too confidently relative to that evidence. The shared-route change
needed explicit continuity and backlog analysis, which this audit supplies.

1. Stabilize worker/job ownership and complete feasible routes. Measure reversals,
   useful service per worker-day and missed care/planting deadlines in server logs.
2. Replace the global seed barrier with bounded commitments. Give planting a
   completion deadline, stop planting seeds that can no longer mature, and allow
   independent profitable investments when resources are genuinely available.
3. Couple investment dates and output assumptions to achieved installation and
   service capacity. Calibrate the existing-cohort forecast against actual output
   before expanding the economic feature set.
4. Retain the fertilizer, survival and terminal-delivery improvements. Package a
   focused execution repair for server evidence before any further expansion.

In CO terms, current route feasibility is a one-decision certificate, not a
feasible schedule over time. Planting jobs can starve under greedy priorities,
and an unrelated inventory condition excludes valid investment alternatives.
The solution needs completion guarantees and resource-linked commitments, not
more optimistic profit coefficients or simply a larger worker cap.

This review changes no agent logic and performs no local game, training or
counterfactual episode. [Machine-readable evidence](benchmarks/cycle-18-server-review.json)
contains source matches, physical/accounting metrics, route traces and the
forecast comparison. The two losses identify repair priorities; they cannot
promise a rating or assign an exact recoverable coin value to each defect.
