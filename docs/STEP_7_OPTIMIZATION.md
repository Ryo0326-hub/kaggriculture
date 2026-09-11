# Step 7: buying a production schedule, not just a seed

Implemented September 10, 2026. Entry point: `main.bundle_turn`; standalone artifact: `main.py`. See [results and release status](STEP_7_RESULTS.md), the [frozen validation protocol](benchmarks/step-7-protocol.json), and the [original staged plan](STEP_7_PLAN.md).

## What changed, and why

The leading-player audit showed that early melon delivery, a productive mix of assets, and timely fertilizer mattered more than simply maximizing harvest quantity. Step 6 waited until Day 3 to buy crops, limited crops by herd size, and valued new strawberries without their complementary fertilizer. It could discover that fertilizer was worthwhile after planting but could not use that benefit when deciding what to plant.

Step 7 makes animals and crops compete in one forecast of future bank balance. It buys an opening portfolio on Day 1, allows up to twelve crop plots independently of herd size, and compares complete base/fertilized crop schedules. Existing livestock service, shared inventory reservations, crop deadlines, and endgame delivery checks remain in the execution layer.

The first quadrant still contains at most ten animal sites and twelve crop sites. This is a deliberate checkpoint before land expansion, not an economically optimal farm-size claim.

## A concrete opening decision

The planner enumerates twenty portfolios:

- Melons: 0, 4, 8, or 12.
- `(cows, sheep)`: `(0, 0)`, `(0, 2)`, `(1, 1)`, `(0, 4)`, or `(2, 2)`.

For each portfolio, it projects production, operating inputs, wages, and sales. Two additional rival-supply scenarios place 48 unknown rival melons on Day 11 or Day 17. These are stress assumptions, not observations or inferred private plans. The selection maximizes the average projected contribution among portfolios whose minimum projected cash stays at least 150 coins in both scenarios.

In the [source-matched opening example](examples/step-7-opening.json), it chooses **two cows, two sheep, and eight melon seeds**, spending 2,440 of the initial 3,000 coins. The forecast's minimum balance is 262 coins; projected contribution over the remaining season is 27,769.6. That contribution is conditional on this fixed portfolio and forecast, not a prediction of the eventual adaptive agent's final score.

The larger twelve-melon/four-animal opening has more projected contribution but fails the dated cash requirement. This is the CO250 distinction between an attractive objective value and a **feasible** solution. We do not spend down to zero merely because a harvest several days away looks profitable.

All eight purchased opening melons were planted and watered on Day 1 in the checked episode. The executor reserves newborn watering and hires for pending crop work without waiting for a large installed herd. New purchases and hires become usable only after the current unit-action phase.

The fixed menu does not contain every possible opening. In particular, it does not make a globally optimal claim about animal counts, crop species, or exact planting routes. Frozen Step 6 is the external control; it is not secretly run as a second online policy.

## CO250: activity columns and integer choices

A column describes one activity's resource use over time. For a crop, `crop_column` records:

| Quantity | Meaning |
| --- | --- |
| Planting day and end day | When a tile is occupied |
| Dated output | Units that can be harvested before the season ends |
| Fertilizer application days | Complementary input commitments assumed by the forecast |
| Daily work allowance | Fifteen actions per active crop, allowing a six-step outward/return trip and three operations |
| Purchase day | When the seed must be paid for, including a proposed second crop |

The underlying integer-programming idea is:

```text
choose integer activities x_j
maximize projected terminal cash
subject to dated cash, inventory, tile, and labor constraints.
```

For example, a cash balance and an inventory balance have the familiar linear form when quantities and prices are fixed:

```text
cash[d+1] = cash[d] + sale_receipts[d] - purchases[d] - wages[d]
stock[c,d+1] = stock[c,d] + production[c,d] + buys[c,d]
               - sales[c,d] - internal_use[c,d]
```

The implementation enumerates a bounded menu instead of invoking an external MIP solver. It prices each alternative through the nonlinear market curve, so the actual objective is not globally linear. Labor requirements and feasible delivery times are estimates checked by the real dispatcher, not a complete time-expanded scheduling certificate.

This distinction matters: **the agent uses ideas from integer programming; it does not solve the whole farming game exactly.**

## Fertilizer is a complementary input

The implemented templates are:

| Crop | Base output | Fertilized output | Planned applications |
| --- | --- | --- | --- |
| Wheat, harvest at age 4 | 4 units | 6 units | Age 2, active through age 4 |
| Melon, harvest at age 10 | 6 units | No extra template | None; daily yield-window watering already reaches the cap |
| Strawberry, complete cycle | 4 units | 8 units | Ages 9 and 13, covering production at ages 10/12/14/16 |

These quantities were checked by independently executing the actions in the pinned official engine. The forecast truncates production and applications at the recoverable horizon. For example, a strawberry planted on zero-based day 19 can produce two units on day 29 with an application on day 28; it cannot claim later events.

Existing wheat and fertilizer are consumed once. The remaining inventory can be sold; the same unit cannot earn sale revenue and replace a purchased input. When fertilizer is produced by owned animals, its cost is the sale income forgone. When it must be purchased, the forecast charges the market price on the scheduled application date. The executor buys shortfalls only when the current marginal yield benefit and cash checks justify them.

An input is required **before** the output it enables. The daily forecast first pays inputs and wages, records minimum cash, and then credits production receipts. It retains enough wheat/fertilizer for the next day's planned needs. This avoids funding an early application with fertilizer that is expected to be collected later that day.

The future template remains conditional: subsequent turns can reprice fertilizer, change the crop mix, or reject a follow-on purchase. There is no hidden persistent promise to spend on an unprofitable application.

The same complementarity applies to animal installation. The first validation attempt exposed a case where placement fitted before the daily refresh but a separate trip for feed did not. The corrected executor loads feed before taking the animal to its site, then requires room for placement, feeding, and care. A profitable asset still needs an executable service schedule. The failed attempt and all thirty of its seeds were retired; see [the rejection record](benchmarks/step-7-rejected.json).

## A concrete marginal-value comparison

In the [Day 13 decision example](examples/step-7-production.json), the planner chooses a fertilized strawberry schedule, with planting conservatively forecast for Day 14. Zero-based days 13–29 allow all four production events.

| Forecast difference from keeping the existing portfolio | Coins |
| --- | ---: |
| Additional credited receipts, after internal use and price impact | +1,632.8 |
| Seed | −100.0 |
| Additional wages | −155.0 |
| Additional feed purchases | 0.0 |
| Additional fertilizer purchases | 0.0 |
| **Marginal projected contribution** | **+1,377.8** |

No additional fertilizer purchase does not mean free fertilizer. Owned production is diverted from sale inside the inventory ledger; that foregone revenue is already included in the receipts difference.

The whole portfolio is repriced for each alternative. Adding supply can lower revenue from our other units, so the comparison is not simply `new units × current price`. This is an economics concept of marginal contribution with a price externality.

## Cash, labor, and opportunity cost

`planning_snapshot` books the selected unit operations before the already selected market orders. Feed used, fertilizer collected or applied, harvested output, deposits, sales, purchases, and paid hires are accounted for once. It is a narrow accounting snapshot for the policy's reachable operations after pending installations/seeds clear. It is not another game engine and does not simulate unknown simultaneous rival orders.

`production_projection` then checks future spending from that state. Already paid hires are deducted from today's remaining wage requirement. Each animal's actual placement date determines its production-day staffing; one producing sheep does not make every sheep a production-day task.

Wages are nonlinear. Additional workers follow the engine's Fibonacci hire prices, so an activity can have a much larger marginal labor cost when it crosses a staffing threshold. The crop allowance and installed-animal routes determine a bounded crew estimate, capped at twelve total workers. Admission is followed by per-turn travel, input, seed, deposit-capacity, and deadline checks in the executor.

From the perspective of LP duality, scarce cash, labor, land, and fertilizer all have opportunity costs. Here those costs come from comparing feasible alternatives, foregone sales, and estimated extra wages. **They are not dual values computed from an LP relaxation.** An offline LP/MIP benchmark would be useful later for measuring the heuristic's gap.

## Recurring decisions and game theory

During early hours after the opening, the planner compares no purchase, one cow/sheep, and one crop with optional fertilizer. It also evaluates two-stage crop sequences sharing a plot; the follow-on seed is charged on its future purchase day. Only the first purchase is executed, and the second is reconsidered after observing the game.

Current market inventory, visible rival animals/crops, and currently revealed shops drive prices. Rival wheat purchases are approximated from visible feed needs and wheat output; private stocks and future investments remain unknown. New shop unlocks are not forecast from the episode seed. Sale batches use a midpoint approximation for competing deliveries and the exact pinned marginal price formula, including the one-coin floor.

Eighty percent of projected receipts is credited to both contribution and the cash path. This is a heuristic buffer for timing and price error, not a calibrated probability or lower confidence bound. The 150-coin minimum cash buffer is likewise a tested design choice, not a guarantee against all possible opponents.

The approach is a repeated best-response heuristic to visible supply. It is not a Nash-equilibrium solver. The final release decision uses wins and losses against reactive opponents because expected bank and probability of winning are different objectives.

Equal episode seeds do **not** hold future shops fixed when policies occupy different tiles: weed generation consumes RNG draws before the shop draw. Whole-policy paired games remain useful, but they do not isolate a feature's effect while holding every future market event constant.

## What this checkpoint deliberately leaves for later

- Wheat currently follows the reliable age-four harvest policy. Age-two/three templates need matching execution choices before they can be credited in valuation.
- No purchase is an explicit alternative. There is no separate multi-day waiting optimizer; future crop sequences are conditional proposals, not binding schedules.
- There is no land purchase or distant-farm routing. Expansion to 50/75 tiles needs a jointly feasible work and delivery plan.
- Maintenance still protects all owned animals. Deliberate retirement or survival-only service is not implemented.
- Two crop controls have independent code, but none of the local opponents reproduces an expanding elite mixed farm. Their source is not available.

These limits narrow the first implementation relative to the broader Step 7 proposal. The next checkpoint should test **conditional land expansion and integrated routes**, with an expanding mixed opponent, while preserving this release as the benchmark.

## Verification and explanation

`tests/test_bundles.py` checks base/fertilized yields against the engine, horizon truncation, input accounting, paid hires, opportunity cost, opening liquidity, source purity, seed independence, opening execution, and the independent early seller. Existing full-season resource and isolated-loader tests run the new default agent.

`explain_turn.py` now invokes `bundle_turn`. It requires the replay's candidate hash to match current `main.py` and verifies that the recomputed action equals the recorded action before returning economic alternatives. A plausible explanation from the wrong policy version is rejected.

The final source, seeds, opponents, promotion gates, and process count were frozen before validation. Development trials are not treated as fresh evidence. The [results document](STEP_7_RESULTS.md) records the comparison and any remaining limitations.
