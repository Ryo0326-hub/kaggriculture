# Cycle 18 — funded growth with inputs delivered before deadlines

Cycle 18 enhances the server-validated Cycle 15 lineage. It incorporates the
unsubmitted Cycle 17 shared-route growth work, repairs an ongoing-crop watering
defect found during this release, and adds explicit input allocation and staging.
Cycle 15 and Cycle 17 remain reproducible and unchanged.

## Evidence behind the changes

| Review | Main lesson used here |
|---|---|
| Sergey, 108005959 | A larger serviced herd and crop portfolio can overcome a large early cash deficit. |
| Julian, 108009995 | Expand livestock into observed demand; additional sheep can outweigh their feed and wage costs. |
| Chloe, 108013045 | Eleven missed strawberry fertilizer bonuses show that delivery deadlines matter, even when plants survive. |
| Ahmed, 108014069 | Cycle 15's installation staffing discontinuity and discount to known demand reject otherwise feasible growth. Animal inventory and harvested goods can be lost to shed overflow. |
| Soumic, 108017116 | Scale wins despite waste, but repeating melon cohorts can flood the market. Fourteen missed own fertilizer bonuses repeat the input-location problem. |

The replay observations, source-matched actions and cash accounting are evidence.
The opponent's exact algorithm and hypothetical outcomes under our changes remain
unknown. The policy does not read replay seeds, future shops or rival private
inventories. No games were run to select or validate this release.

## Growth and shared-market economics retained from Cycle 17

One route constructor prices and schedules crop maintenance, animal care and
new installations. Adding one animal no longer switches the entire herd to
one-worker-per-animal staffing. All four quadrants and all three livestock types
are eligible; preferred animal locations can extend into vacant crop fields.
Additional land must be bundled with a funded production plan that uses it.

The investment score remains:

`0.75 × marginal receipts with known demand and stressed rival supply`
`+ 0.25 × marginal receipts with expected new shops`
`− land/seeds/animals − additional Fibonacci wages − installation reserve`.

Both demand branches preserve shops already observed. Both charge our planned
sales' effect on prices received for our existing output. Feed costs and wages
enter dated cash feasibility before projected receipts, and every branch must
retain at least 150 coins. A 17-total-worker search bound controls route and
investment complexity; it is not a target crew size or an optimality claim.

On the fixed Soumic-game observation at decision 340, the candidate rejects all
five additional melon options. One melon has estimated value **−93**, and eight
melons on current land have value **−739**, because visible maturing supply drives
down the forecast selling price. It instead admits **two cows**, with an
800-coin purchase cost, 51 additional modeled wages, 164 setup reserve and
estimated net value 5,068.5. Those are decision diagnostics, not realized profit.

On the fixed Sergey-game observation at decision 244, it also admits two cows;
at decision 340 it admits eight strawberries. A separate bounded fixture with
a full starting quadrant confirms that a paid-land production bundle can be
selected while satisfying cash and workforce constraints. There is no rule to
buy land just to make the end screen look larger.

## Inputs now have a location and a deadline

The old aggregate condition, `shed fertilizer + all carried fertilizer`, does
not establish that a crop worker can access an input before tonight's refresh.
The same limitation applies to feed assigned to another worker.

Cycle 18 implements the following in `experiments/production.py`:

1. **Dated fertilizer requests.** Reuse the existing marginal-value calculation
   to identify profitable applications due today or tomorrow. Active fertilizer
   coverage removes the request. One application reserves one unit per site;
   the next observation recomputes coverage through the game's day+2 expiry.
2. **Funded worker assignments.** Workers already carrying fertilizer receive
   assignment priority after animal-installation carriers. Each proposed route
   explicitly funds its applications from that worker's inventory and the
   unreserved shed balance. If supply is scarce, the higher-value applications
   receive the units. Unfunded optional fertilizer is removed from the route
   while mandatory watering and feeding remain eligible.
3. **Pickup before the funded application.** A worker assigned fertilizer from
   the shed must fetch it. The dispatcher no longer silently skips the input,
   waters, and then needs an avoidable return trip for the same application.
4. **Route-specific inventory credit.** Carried fertilizer offsets today's depot
   requirement only for requests actually allocated to its worker's feasible
   route. Applied units and sites are removed exactly once. Feed uses the same
   rule for unfed animals, including pending installations.
5. **Stage tomorrow's requirements.** Retain required shed fertilizer through
   the day before a production wave, and buy missing units subject to cash and
   capacity. Spare carried fertilizer can cover tomorrow through the normal
   night deposit; it cannot erase today's missing pickup. Future animal
   collections are not credited before the units exist.

The sale ledger keeps this required depot stock. Inputs are budgeted before
speculative expansion. Because markets execute after unit actions, an input
bought this turn is only usable on a later turn. Late purchases are limited;
the planner does not pretend a last-action BUY can rescue a same-night crop.

This is a small resource-constrained scheduling heuristic, not an LP/IP solver.
In CO250 terms, each application has a marginal objective coefficient and uses
scarce labor, stock and time. A unit in the wrong location has a different
opportunity cost from a unit already on the worker's route. Future graph and
network-flow courses connect naturally to this time-and-location formulation.

## Production survival and terminal delivery

The pre-release checks exposed a Cycle 17 defect: a ready ongoing crop could
lose its watering job because the dispatcher treated harvest like the removal
of a one-time crop. A tomato harvested today can still have production ahead.
Cycle 18 preserves watering for ongoing crops while production remains, and
prioritizes survival water over optional work when only one action remains.

Conversely, a watered strawberry may receive a profitable fertilizer application
on the last ordinary action. The previous unconditional four-action minimum
unnecessarily excluded that legal opportunity. A new crop is not planted when
the complete planting-and-first-water bundle cannot fit.

Normal nights still deposit worker inventories automatically. The final day
requires explicit harvest, travel, deposit and market sale before termination;
there is no assumed final-night transfer. Partial deposits protect the shed
capacity instead of discarding the remainder of a worker's inventory.

The second pre-submission audit found that global bundle length was insufficient:
the *assigned worker's* travel and pickups can make a bundle late even when an
essential action still fits. Complete feasible bundles retain priority. When a
single existing asset's bundle cannot fit, the dispatcher tries essential feed,
water or harvest with the same physical input and travel accounting. It never
splits a new planting or animal installation from its first maintenance action.
On the final day, harvest alone is an alternative only when that worker can also
deliver it before termination. See the [audit counterexamples](CYCLE_18_AUDIT.md).

For CO250, this repairs the feasible set rather than changing a profit coefficient:
an indivisible full-service job had incorrectly excluded feasible survival work.
The model still treats asset installation as a complementary bundle, since a
plant without its first water can die before producing anything. No optimal
schedule or exact dual prices are claimed.

Deposit accounting now follows the engine's overloaded `PLACE` semantics:
an animal on an empty matching pen is an installation, regardless of the
quantity argument. Overflow handling skips that ambiguous deposit and ignores
zero-quantity inventory keys when choosing a product. Observations without the
optional `step` field use `day × turnsPerDay + hour` for their action budget.

Purchases now reserve space beside goods already carried, including goods
harvested by the current command. The investment ledger applies the same rule
to new animals. This strengthens the overflow protection motivated by Chloe
and Ahmed; it cannot guarantee that every later harvest wave will fit, so
current inventory-pressure delivery remains active.

## Runtime without weakening the route model

An early bounded check on Sergey's larger farm exceeded the one-second callback
limit. Profiling identified repeated full route-duration calculations during
investment assessment. `production_routes` instead computes the exact change
in travel, service work and distinct input pickups for each insertion.

The cost formula and tie-breaking are unchanged. Thirty-six bounded comparisons
against the frozen constructor cover empty through 96-node routes, three action
budgets, and ordinary versus terminal delivery. They produce identical routes,
durations and feasibility flags. This improves computation without loosening the
modeled work constraints or using a hardware-dependent time cutoff.

## Submission status and next evidence

The complete standalone candidate and its exact command are in
[Cycle 18 results](CYCLE_18_RESULTS.md). It passes bounded engineering checks;
Kaggle validation and competitive performance are still pending. No claim of
150K coins, a rating increase, or optimal play follows from these checks.

The next returned server games should answer whether purchases become operating
assets promptly, whether production and delivered units grow, whether fertilizer
bonuses improve without excessive purchases, and whether the added wages and
inputs pay back. Compare animal/crop losses, storage overflow, terminal stock,
banked coins and opponent demand/supply. Preserve Cycle 15 as the reference while
collecting that evidence.
