# Step 6: mixed production, committed work, and input opportunity costs

Implemented September 10, 2026. [Results and release status](STEP_6_RESULTS.md) · [The awarse replay audit](STEP_5_SERVER_ANALYSIS.md).

## Economic motivation

Against awarse, our Step 5 labor cost was only 303 coins, but eight animals were our entire productive portfolio. awarse's larger pipeline eventually paid for its expansion and 12,994-coin labor bill. The lesson is to compare additional revenue with **all additional costs**, rather than minimizing expenditure or maximizing the current bank balance in isolation.

Step 6 adds wheat, melons, and strawberries within the initial quadrant. It admits at most eight crop plots, chosen from the eight nearest plots outside the ten reserved livestock locations. The current crop-count limit is also capped by the installed herd count. These are explicit engineering bounds, not game rules or proven optimal acreage. Land expansion is not implemented here.

The frozen Step 5 file is `baselines/step_5.py`. `main.py` retains its livestock investment and execution functions; `mixed_turn` composes that core with crop investment, dispatch, staffing, and a rebuilt shared-resource ledger. `agent` calls `mixed_turn`. The replay explanation uses that same entry path. Disabling the crop layer reproduces the Step 5 action and explanation exactly.

## Dated production before valuation

| Crop | Base production schedule | Fertilizer opportunity |
| --- | --- | --- |
| Wheat | Four units at age four with the required watering; harvest becomes legal at age two | A timely application can raise the planned lot to six units |
| Melon | Six units at age ten with survival watering and watering during ages six through ten | None required to reach the planned six-unit yield |
| Strawberry | One unit at each of ages 10, 12, 14, and 16 | Applications before production, such as ages nine and thirteen, can cover pairs of events |

The implementation reads actual age, water state, held yield, and fertilizer expiry. It waters on planting day, prevents a second consecutive missed refresh, and respects the finite number of strawberry production events. One-time crop bonus watering precedes harvest. Imminent termination can justify salvaging a legally harvestable lot before its normal peak.

`crop_flows` predicts dated output without assuming future fertilizer applications. Existing visible crops on **both** farms enter the price forecast. Current held output is accounted for separately from future production events. Engine-backed tests independently execute the schedules and recover four wheat, six melons, and four strawberry units without fertilizer.

## CO250: one new integer commitment at a time

For each admissible crop `c`, let `x_c` be one if we buy its seed now. The small admission problem has:

```text
x_c ∈ {0, 1}
Σ_c x_c ≤ 1
seed cost + protected operating cash ≤ available cash after prior orders
active lots + pending seed + Σ_c x_c ≤ admitted plot capacity
at least one useful output date ≤ final recoverable day.
```

Only one unplanted crop seed is allowed in the pipeline. Purchases are limited to the early part of the day, from day two onward, with a worker available to begin crop work. The forecast assumes planting tomorrow to allow setup time. Newborn watering is a committed follow-up operation, not a task that can be freely dropped after buying a seed.

For each crop, the model computes:

```text
estimated marginal value
    = 0.85 × change in our projected crop-portfolio receipts
      − seed cost
      − estimated additional dated wages
      − action/travel allowance.
```

The action allowance is two coins per estimated action, using `8 + lifetime days + 2 × production events` actions. It is a heuristic opportunity-cost charge, **not an LP dual value or a measured market price for labor**. Positive feasible alternatives are ranked by estimated marginal value per occupied tile-day. Enumeration selects the best alternative in that three-crop menu; it does not solve the full-season integer production problem.

The 15% receipts haircut and twelve-unit unobserved-supply buffer are declared forecast assumptions. Observed shops supply average future demand; future shop unlocks and unobserved rival expansion are omitted. Unit sale prices follow the actual nonlinear curve and one-coin inventory rule. Comparing the whole visible crop portfolio with and without a new lot accounts for modeled cannibalization of our other crop sales. It does not recover the opponent's hidden inventory or solve a game-theoretic equilibrium.

[The saved source-matched decision](examples/step-6-decision.json), validation seed 5003 at state 52, chooses wheat. Its four-unit dated lot has 120 projected receipts, a 10-coin seed, 30-coin work allowance, and five additional projected wage coins: `0.85 × 120 − 10 − 30 − 5 = 57` estimated marginal coins. This is the model's forecast, not a realized profit claim for that individual lot.

The melon alternative has a much larger 1,161.80-coin forecast but is infeasible under the current cash rule: its 80-coin seed plus the 405-coin reserve exceeds the 455 coins available. Wheat fits. This explains the actual decision, while exposing a limitation: buying affordable wheat now has not been compared with waiting to afford a melon. That option value and the resulting crop sequence belong in the next finite-horizon allocation model.

## Labor is both quantity and timing

Most crop work starts after a worker finishes its assigned livestock service. Milk, wool, and eggs already being carried retain delivery priority. Additional hands can be hired to support committed crop work; the implementation does **not** assume all crop labor is free spare time.

The staffing estimate combines two constraints:

```text
workers × (turns per day − 4) ≥ estimated animal and crop workload
workers ≥ planned livestock crew + ceil(current crop jobs / 4).
```

The workload estimate uses six actions per animal plus an individual return trip and three service actions per crop. The second constraint reserves some workers who can start crops before the livestock crew returns. Both are planning allowances, not certified upper bounds for every dynamic schedule. Current staffing is capped at twelve total workers. Hires must fit current cash, the market queue, and the early hiring window.

`crop_staff_cost` also projects daily workforce costs through the crop's useful lifetime. It estimates producing animals as dedicated routes and other animals in small shared groups, then adds crop capacity. The wage arithmetic uses the **actual Fibonacci hire schedule**. Marginal crop admission subtracts the difference between the two portfolio wage estimates. The three-day cash reserve includes feed and the current staffing target. These estimates omit future unobserved purchases and can differ from realized wages.

Workers already hired today are sunk cost. Replanning can reduce the workforce target, but the executor continues to use workers already present. The next day's hires are decided again from its obligations.

## Dispatch, deadlines, and the limits of greedy assignment

Workers and crop tasks are matched using urgency, distance, and a shared reservation set. First watering is reserved before another worker can claim the newborn plot. Nearby workers get priority over distant workers so a new idle worker is less likely to take over a route already in progress. Mandatory watering and mature one-time crops outrank discretionary sowing.

A ripe one-time crop may be serviced **before** livestock when the plan budgets the crop operation, travel back through the shed, current livestock service, feed pickup, and deposits within the remaining day. Workers carrying an animal or main livestock products are excluded from this reassignment. If the crop reservation fails, the original livestock command is retained. This addresses a precedence/deadline constraint that an aggregate count of spare worker-hours cannot express.

This is a bounded greedy dispatcher with feasibility checks. It is not an optimal assignment or vehicle-routing solver. The small exact set-partitioning algorithm remains inside the livestock core; its optimality guarantee does not extend to the mixed dispatcher. A future network-flow or integer-routing model can benchmark this dispatcher on frozen states before replacing it.

## Fertilizer and wheat have alternative uses

An owned fertilizer unit is applied only when discounted additional crop receipts exceed its **forgone sale price**, plus an eight-coin pickup/application/detour allowance. The policy checks active fertilizer duration, whether watering has already occurred, remaining bonus capacity, future production dates, and the terminal cutoff. It does not fertilize melons that can reach six units without it. It retains stock for currently valuable applications and sells the remainder; it does not buy fertilizer in this checkpoint.

Survival watering is not delayed indefinitely while waiting for fertilizer. The implementation also avoids a new fertilizer pickup trip on wheat's planned harvest day. A regression test covers the late-day case in which a worker already carrying fertilizer must apply it and water rather than return it to the shed unnecessarily.

Homegrown wheat enters the same inventory balance as purchased feed. Retained feed reduces purchases; surplus can be sold. Each harvested unit receives **one** forecast sale/replacement value, not both feed savings and sale revenue. The model does not claim harvested wheat is free, and it does not count wheat buying and resale as crop production profit.

## Shared resources and termination

After crop actions replace some livestock commands, the policy rebuilds the shed ledger in actual worker order. It caps pickups to available stock, reserves shared deposit space, and uses partial `PLACE` instead of an overflowing `DROP`. Harvest admission checks total current shed/carried stock plus reserved harvests. Market sales are built from the resulting stock; original livestock spending is protected before new crop admission. New hires and purchases are never used in the same turn's unit phase.

Ordinary daily inventory transfer can finish delivery when there is reserved capacity. The final day has no assumed extra transfer: harvest must leave time to reach the shed, deposit, and sell before the pinned last actionable step, 718. Final stock and unused seeds are explicit release checks.

An exhausted strawberry plant with zero held yield is distinct from losing an unharvested crop. Evaluation retains the raw weed-transition count and separately reports exhausted expirations and unplanned losses. A test ensures the exemption cannot hide held produce lost to decay.

## Evidence and next questions

Development initially exposed first-water reassignment, long trips, inadequate early capacity, and delayed crop harvests. Those are recorded as rejected development outcomes rather than omitted from the history. The frozen candidate is evaluated on fresh seeds against both livestock and reactive crop-specialist controls. [Results](STEP_6_RESULTS.md) record the protocol, hashes, limitations, and exact standalone-file check.

The first next question is crop sequencing: compare planting now with waiting for a better crop, accounting for liquidity and occupied tile-days through termination. The candidate lost 49 of 60 games against the melon-only crop control despite beating Step 5 in all 60 direct games. Further questions include expanding land profitably, coordinating larger crop bundles, valuing deliberate reduced animal maintenance after price collapse, and forecasting the rival's production and delivery uncertainty. The current cash lead still is not a sufficient estimate of winning probability.
