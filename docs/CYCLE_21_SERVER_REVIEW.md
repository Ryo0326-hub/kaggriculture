# Cycle 21 — confirmed routing and production regression

Reviewed September 12, 2026 (Toronto; September 13 UTC). **Cycle 21 is not
recommended as an improvement over Cycle 19. Preserve Cycle 19 as the recovery
baseline.** This review changes documentation and evidence only, not any agent
source or upload artifact.

## What was actually submitted and played

The supplied `108351109 (1).json` is the validation episode: Unicorns versus
Unicorns, ending **85,126–85,508**. Kaggle's episode listing identifies it as
validation, so this is not a rated loss to another competitor.

The authenticated CLI also provided the latest two completed public episodes:

| Episode | Opponent | Cycle 21 cash | Opponent cash | Our margin |
|---|---|---:|---:|---:|
| 108360391 | mogura2.0 | 57,930 | 104,432 | -46,502 |
| 108359367 | Nawaf Almutairi | 88,858 | 123,317 | -34,459 |

These are two recent losses, not a randomized sample or the complete ladder.
The CLI rating snapshot during review was Cycle 19 **1,154.0**, Cycle 20
**987.4**, and Cycle 21 **629.8**. Ratings can change; these are not final scores.

All **2,876 own decisions** across the validation's two seats and the two public
games match the frozen Cycle 21 artifact, SHA-256
`f56a3f597528265c8a7ecaeaaf1f08ad03035a5b1ce56809b2baa9c7c5fd2156`, when the
policy's memory is retained across original recorded observations. No returned
action was applied to a game engine. Both validation log files have empty
stdout/stderr throughout, with maximum recorded call duration **0.094193 s**.
All three games finish DONE/DONE. This is a strategy/execution regression, not
evidence of a wrong artifact or a validation crash.

[Machine-readable evidence](benchmarks/cycle-21-server-review.json) records
input hashes, fingerprints, accounting, purchases, output and limitations.

## 1. Deadline preemption breaks route continuity

`service_assignments` can abandon a worker's existing target whenever another
eligible job has higher priority or an earlier deadline and insufficient slack
for that particular worker to finish both. It does this **before the final
allocation determines which worker will actually handle the urgent job**.
Consequently, several workers can abandon their routes for the same urgency,
even though the urgent tasks are subsequently assigned to other workers.

The later greedy assignment can send an interrupted worker to a completely
different ordinary harvest. The builder gives this forced assignment precedence
over both the previous target and work at the worker's current position.

The exact witness is worker index 3 in the mogura game, UI Day 21:

| Decision step / UI turn | Position | Target | Actual command |
|---|---|---|---|
| 492 / Turn 13 | (7,1) | (9,3) | EAST |
| 493 / Turn 14 | (8,1) | (3,1) | WEST |
| 494 / Turn 15 | (7,1) | (9,3) | EAST |

At step 493 the previous harvest still fits in **4 actions with 7 spare**.
The preemption candidates are animal-service jobs ultimately assigned to
workers 2, 4, 5, 6, 8, 9, 10 and 11, not worker 3. The same pattern repeats at
step 494. These are completed server actions, not hypothetical routes.

The problematic logic is in `experiments/majkel_calendar.py`, the commitment
preemption loop, together with forced-target precedence in
`scripts/make_calendar_agent.py`. [Three original observations and exact prior
memory](examples/cycle-21-route-regression.json) preserve this failure for a
bounded future regression check.

The validation has 94/97 immediate direction reversals across its two seats.
The public games have 89 and 86 for Cycle 21, versus 12 and 25 for their
opponents. Some reversals can be legitimate; the traced sequence above proves
that repeated unfinished target changes are occurring here.

## 2. Saved watering actions did not become productive work

Against mogura, the same game and market show:

| Measure | Cycle 21 | mogura2.0 |
|---|---:|---:|
| Peak productive tiles | 50 | 75 |
| Movement actions | 4,098 | 2,802 |
| Movement share of unit actions | 57.1% | 42.1% |
| PASS commands | 1,067 | 408 |
| Water commands | 561 | 1,110 |
| Wages | 5,010 | 3,719 |
| Strawberry events with water/fertilizer bonus | 52/104 (50.0%) | 119/130 (91.5%) |
| Animal production events without a care bonus | 22/92 | 8/162 |
| Wheat harvested | 51 | 521 |
| Milk harvested | 179 | 284 |
| Strawberries harvested | 156 | 249 |

Fewer WATER commands are not themselves an efficiency result: there are fewer
crops, and the freed actions can be lost to movement, waiting and missed input
visits. The rival grows more wheat, which can supply feed or generate receipts;
the harvest comparison is physical output, not a claim that every unit was sold.

The Nawaf game independently shows only **45/104** strawberry events receiving
the bonus, including **13 unwatered production events**, versus the opponent's
50/50 bonus events. Safe skipping is only safe when the required later visit is
actually completed. The combination of the new calendar and disrupted routing
does not satisfy that condition reliably.

## 3. Input delivery and complete animal service are being displaced

In the validation, five animals miss feeding on UI Day 11 while **nine wheat
remain in the shed** immediately before the final action. The final commands
feed other sites; those five remain unfed across the daily boundary. Available
cash is 1,810. This is a delivery/scheduling failure, not a lack of feed or cash.

The new job metadata treats FEED as essential, but CARE and fertilizer
collection alone do not receive deadline metadata. A worker can therefore be
pulled away immediately after feeding or harvesting an animal. In the mogura
trace, worker 1 feeds and harvests a cow at (3,4), then leaves its still-pending
care/collection work for a distant crop assignment. Another worker might finish
it later; the trace establishes the interruption, not the entire missed-day
effect by itself.

Animal installation also slows. In validation seat 0, cows purchased at steps
289 and 290 are installed only at 357 and 441; a later cow bought at 442 remains
in the shed at termination. Seat 1 ends with an uninstalled goose. Protecting
animals already carried did not guarantee timely pickup and installation from
the shed.

Do not label every unfed late-season animal or escape a defect. Some have no
remaining production and are deliberately no longer maintained. The midseason
feed failures and zero-bonus production events above are the relevant evidence.

## 4. Economic changes are a separate confounder

Cycle 21 descends from Cycle 20, not directly from Cycle 19. It therefore also
includes the changed committed-supply forecast and stronger price-downside
response. Its own crop-work formula changes investment rankings again.

On the exact mogura observation at step 266, the Cycle 19 cow score is +2.32;
Cycles 20/21 score it -13.67. At step 314, the strawberry score changes from
+8.08 in Cycle 19 to -8.00 in Cycle 21. These are heuristic scores, not realized
coins. Other admission rules can still block a purchase, and independent
callbacks do not prove a counterfactual profit advantage. They demonstrate that
this was not an isolated watering revision.

The supply forecast assumes future service and sales more confidently than
the actual execution warrants. Its conservatism may reject useful investments,
but the present evidence does not isolate the forecast's effect from scheduling,
different portfolios and opponent responses. Do not fix the routing problem by
adding more economic features at the same time.

## What did work, and why previous checks missed this

Both rated losses reach **three quadrants**; lack of land expansion is not the
failure here. Their sellable terminal shed, carried inventory and field output
are empty. Terminal delivery is not the principal missing-revenue explanation.
There are no duplicate productive commands in the supplied validation.

The release's 176 tests and 5,752 independent observation calls checked legal
actions, resources and selected decision cases. The large observation check
cleared policy memory for every callback. It therefore did not exercise the
actual server's persistent target history. Simple continuity fixtures also did
not cover many workers preempting for jobs later assigned to someone else.
The new fingerprints retain that history and exactly reproduce the failures.

The engineering mistake was combining several behavioral changes while lacking
adequate checks for their stateful scheduling interactions. More features and
legal commands do not establish a better policy. The user's server-first testing
constraint remains in force; this review ran no local matches or paid compute.

## Recovery direction

Use unchanged Cycle 19 as the recovery baseline. The next challenger should
isolate one scheduling change and preserve its opening, investment forecasts,
staffing and sales. Route changes must reserve a specific replacement task for
the specific worker and consider existing team coverage; an unrelated urgency
must not destroy an otherwise feasible commitment. Preserve useful feed/care/
collection bundles and require an executable input path before expecting a
fertilizer bonus. Account for actual travel before admitting more service work.

Check these exact recorded histories without advancing a simulator, then use
Kaggle games for competitive validation. Do not call the repaired policy stronger
until server evidence supports it. Cycle 21 and all older artifacts remain
unchanged and no new submission is uploaded by this review.
