# Cycle 5 — forecasting investments across possible future markets

**Implemented as an isolated challenger, not promoted.** [Results](CYCLE_5_RESULTS.md) · [Plan recorded before development](CYCLE_5_PLAN.md) · [Checked experiment and decision archive](benchmarks/cycle-5-demand.json).

## What changes in a decision

Cycle 3 projects the entire remaining season using the shops visible today. The challenger considers eight possible sequences of future shop openings. It recomputes the price and cash trajectory separately for each sequence. A cow, sheep or crop batch must pay for its inputs and labor before its expected production becomes cash; a land batch also pays for its quadrant.

The patch applies only inside expansion investment, starting at internal day 2 (displayed Day 3). Opening purchases, the spatial admission restrictions, crop harvest/fertilizer timing, actual hiring and dispatch, sale rules and dated yield assumptions remain unchanged. Different investments can still cause different later routes, wages, production and opponent behavior under those same rules.

`scripts/make_demand_control.py` checks the exact frozen Cycle 3 hash, adds an optional dated demand path to `production_projection`, and replaces only expansion's forecast calls. It bundles `experiments/future_demand.py` into a standalone standard-library agent. With no demand path supplied, accounting is unchanged. The tests compare full forecast dictionaries with paid wages, existing inputs, land cost, crops, livestock, partial days and rival-production stress.

## Scenario construction and its limits

The pinned engine chooses uniformly from eight shop types with replacement. A new instance opens on a configured day boundary, defaults to every three days, and persists. At most eight instances open. Duplicate shops consume independently. A single-product shop consumes two units per event; other shops consume one of each listed product. No shop buys melons or fertilizer. Town-center consumption remains part of every scenario, except fertilizer.

Each future unlock column is a fixed shuffled permutation of the eight types. Therefore every type appears once per unlock across the eight equally weighted paths. Columns are shuffled successively using a fixed sampler seed, **unrelated to the game seed**. Repetition within a path is allowed. Already observed shop instances are never resampled. Once there are no remaining openings, the forecast collapses to the original single path.

These paths are deterministic quadrature: a small representative set for integrating uncertain outcomes. They are neither eight independent draws nor exhaustive coverage of the `8^k` sequences with `k` openings left. Marginal frequencies are balanced; joint tails are not guaranteed to appear. In the audited Day 3 decision, every sampled path gave the strawberry a higher marginal value than the melon. That did not protect a game whose actual town eventually had no strawberry-buying shops.

The daily demand rate is the existing approximation to the engine's intraday consumption ticks. The current day's rate is prorated by remaining hours. The new code preserves that approximation instead of mixing a demand change with a sale-timing redesign. Tests compare full-day scenario rates to actual engine consumption, including duplicate shops and nondefault intervals.

## The CO250 connection: integer choices and resource constraints

Think of each enumerated investment as a column: buy one cow, buy one sheep, or buy a dated batch of crop plots, possibly with land. Each column has discrete acquisition cost, dated production, input needs and route workload. We choose one column now, or no purchase. The existing heuristic first selects the best per-plot family, then the best total-value batch in that family; it is not a global integer-programming solver.

For scenario `s` and candidate `j`, calculate the marginal terminal cash:

```text
Delta[j,s] = forecast_terminal_cash(existing portfolio + j, scenario s)
             - forecast_terminal_cash(existing portfolio, scenario s)

score[j] = mean_s Delta[j,s]

admit j only if:
  immediate cash >= acquisition cost[j] + 150
  forecast cash before every day's receipts >= 150, for every sampled s
  forecast routes are feasible and require at most 12 total workers
  score[j] > 0
```

The same demand path is used on both sides of the subtraction. This charges the incremental wages and inputs and includes lower prices on the existing portfolio caused by additional own supply. It does not confuse gross revenue with profit. The original 20% haircut still applies to receipts and hence to cash availability.

This extends familiar resource constraints to several possible futures: each scenario adds a set of working-capital inequalities. It resembles a small scenario-based stochastic integer model with conservative cash constraints. It is not an exact stochastic-programming solution: future own purchases are not optimized jointly, future rival expansion is not modeled, and route and production estimates retain their old limitations. The 150-coin scenario reserve is not a guarantee about actual cash; it covers only the simulated paths and accounting assumptions.

There are no computed LP dual multipliers here. The economic connection to duality is opportunity cost: extra capital, service capacity and feed have value because allocating them to one project restricts another. Current code captures some incremental service and cash costs, but does not price the option to wait for a shop opening or all future displaced investments.

## Why average cash rather than average demand

Market prices change with inventory, batch sales move inventory again, and price rounding and floors make the cash response nonlinear. In general:

```text
mean(cash under each demand path) != cash under mean demand
```

The tests demonstrate this distinction on an actual cow forecast. The implementation propagates every path's inventories and input purchases separately, then averages marginal values. Wages and physical output assumptions remain the same across paths.

Expected coins remain a surrogate for winning the match. A mean-value improvement could still lose more often against a particular opponent. That is why reactive match outcomes and per-opponent results determine promotion; a higher forecast value is not a release criterion.

## Concrete source-matched decision

In seed 43, seat 1 against Cycle 3, the first difference is the action following observation 48: internal day 2, hour 0. Both policies receive identical observations and issue the same feed purchase and five hiring orders. Cycle 3 then buys one melon seed; the challenger buys one strawberry seed.

| One-plot investment | Static-demand marginal coins | Scenario mean marginal coins | Worst forecast cash |
| --- | ---: | ---: | ---: |
| Melon | 768.8 | 768.8 | 313 |
| Strawberry | 747.2 | 1,151.9 | 293 |

The strawberry's eight marginal forecasts range from 956.0 to 1,404.0. A cow has a much larger mean forecast but is rejected: the projected cash trough is −7. The current cash constraint therefore still matters even when future demand increases expected revenue. The archive contains every enumerated option, sampled shop sequence and exact action verification.

## Shared-market game theory

Both farms change common inventory and prices. More rival production can destroy a crop's margin even if the town later demands that crop. This challenger carries forward visible rival production only; it does not model a rival's future purchases or solve for a Nash equilibrium.

The engine also uses one day-specific RNG for weed placement and the subsequent shop draw. Farm occupancy affects how many draws are consumed first. Consequently, changed investment can change the future town on a matched seed. Pairing scenarios within a forecast is a valuation approximation; pairing seeds in full games does not hold the town fixed. The diagnostic replay audit establishes executed accounting, not a causal estimate with an unchanged opponent or market.

The useful next experiment is downside-aware **joint demand and rival-supply stress**, with an explicit alternative of waiting for information. First measure which forecast errors reverse the preferred investment. Do not fix the failed screen by repeatedly tuning the eight paths on these same two seeds. Retain Cycle 3 until a bounded successor passes the full gates.
