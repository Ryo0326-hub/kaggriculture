# Cycle 7 — correct accounting, no competitive gain demonstrated

**Retain Cycle 3; no upload.** The isolated wheat-conservation correction tied the incumbent at **72.2%** development match score. It changed actions in only one of eighteen games, with no outcome change and slightly lower mean own cash. The preregistered improvement gate failed, so no fresh evaluation or release preparation followed. [Plan](CYCLE_7_PLAN.md), [CO/conservation notes](CYCLE_7_OPTIMIZATION.md), [checked evidence](benchmarks/cycle-7-wheat.json).

The generated challenger is `232a0293ed5a52beadbf313ef7669161858cbe12e2759d89a3c9f57897af367b`. Build it with `uv run python -m scripts.make_wheat_conservation_control --output NEW_DIRECTORY/main.py`. The submitted `main.py` remains byte-identical to Cycle 3 at `47c281bfb4118a9755f1759930b162de007efdfef3b23144457eccbaac42da0c`.

## One isolated change

On feeding days, rival wheat used to feed animals cannot also be sold. The correction retains net feed purchases of `max(herd - wheat, 0)` and sells only `max(wheat - herd, 0)`. Final-day output remains entirely saleable. It is enabled only in the existing expansion forecast, for both the baseline and alternatives. Opening forecasts, future-demand assumptions, candidate selection, hiring, dispatch, fertilizer, harvest and live sale rules retain their old behavior. No Cycle 6 scenario or waiting code is included.

Tests verify surplus, shortage, zero output, no herd, final-day handling, unchanged default projections, source isolation and unchanged decisions without rival wheat. This corrects an accounting assumption; it does not establish an optimal investment strategy.

Combined verification: **201 tests passed**, repository lint/format checks passed, and the tested standalone source hash reproduces exactly. The active submission artifact remains unchanged.

## Matched screen

Consumed seeds **17/43/9310**, both seats, frozen Cycle 3 / Step 8 / scaled mixed, two CPU processes. Eighteen new candidate games reuse the identical 18-game Cycle 3 reference completed during Cycle 6. The reference is not counted twice as independent evidence.

| Measure | Correction | Cycle 3 |
| --- | ---: | ---: |
| Win / draw / loss | 11 / 4 / 3 | 11 / 4 / 3 |
| Match score | **72.2%** | **72.2%** |
| Versus Cycle 3 | 1 win, 4 draws, 1 loss | same |
| Versus Step 8 | 6 wins / 6 | 6 wins / 6 |
| Versus scaled mixed | 4 wins / 6 | 4 wins / 6 |
| Mean own cash | 90,180.3 | 90,226.6 |
| Mean margin | +5,406.2 | +5,377.3 |
| Maximum decision | 0.380 s | 0.301 s |

All games finish without agent errors, detected crop loss, missed feed, escapes, seed conflicts, duplicate jobs or terminal goods/seeds. Action-by-action comparison establishes identical joint actions in **17/18 games**. In the remaining seed-17, seat-0 game against scaled mixed, 127 own decisions differ after the first change; the rival's actions remain identical. Own cash falls from 44,472 to 43,639, but rival cash also falls, leaving both versions winners. No win rate improvement is demonstrated.

The forecast does change even when the selected action does not. At observation 48 of that strong-control game, the estimated marginal value of one wheat plot rises from 123.6 to 132.2. The selected action remains a melon purchase. A more accurate equation need not move the optimizer to a different choice; constraints and competing margins can dominate.

The first actual difference follows observation **409**, displayed Day 18, hour 1. The correction buys one wheat seed, valued at **78.4** marginal coins, while Cycle 3 buys one melon seed valued at **78.2**. That 0.2-coin estimated advantage accompanies 833 fewer final coins in the completed trajectory. The corrected farm produces six more wheat and six fewer melons. This exposes decision sensitivity to forecast error: tiny differences between point estimates should not be mistaken for strong evidence of a better investment. The archive verifies both decisions on the identical observation.

The one changed game and its reference were resimulated, and all four cash accounts reconcile. These descriptive audits are distinct from a reactive counterfactual comparison. The complete development trajectories—not replayed rival actions—determine the score above.

## Next priority

Fresh seeds **9401–9420 remain unused**. The account-conservation patch is preserved for future models, but a new upload would spend a submission slot without demonstrated competitive value. Neither this tie nor the small screen proves equivalence against unseen opponents.

Before another demand/waiting redesign, calibrate purchase choices with **full continuations of the existing reactive policies**: allow both the buy-now and waiting alternatives to reinvest later, and measure win/loss and cash margin as well as own cash. Start with a small offline diagnostic on already inspected states. Keep any hidden full-state information confined to evaluation; it must not become an input to the live agent. Use the result to select one bounded policy change, then apply the same fresh-evaluation and exact-artifact gates.

Regenerate the checked report from the retained artifacts with:

```bash
uv run python -m scripts.report_conservation \
  --source artifacts/cycle-7-wheat-dev/main.py --output NEW_REPORT.json
```
