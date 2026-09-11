# Cycle 5 — future demand implemented, incumbent retained

**The challenger did not pass the development gate. Keep Cycle 3.** Across 12 games per policy, both scored 66.7%, while the challenger banked 7,685.9 fewer coins on average. Its improvement against the strongest control came with regressions against both other opponents. No fresh evaluation, release preparation or Kaggle upload was performed. Seeds 9401–9420 remain unused by this cycle.

`main.py` and `baselines/cycle_3.py` remain SHA-256 `47c281bfb4118a9755f1759930b162de007efdfef3b23144457eccbaac42da0c`. The isolated challenger is `3f2691bf276175c6ba43d1ecf657fcb49a5a7f21f4f9e53b8ed5971babee3456`. Its implementation and tests are preserved, so rejection does not discard the work. [CO/economics notes](CYCLE_5_OPTIMIZATION.md) · [Preregistered development plan](CYCLE_5_PLAN.md) · [Complete checked archive](benchmarks/cycle-5-demand.json).

## Implementation

The challenger values expansion investments under eight plausible future shop sequences, using only current observations and public mechanics. It compares each option with the existing portfolio under the same sequences, averages marginal cash, and requires the existing cash reserve in every path. Repeated shops, opening dates, the shop cap, nonlinear prices and dated input costs are included. Actual dispatch, hiring, opening, land admission, sales and fertilizer/harvest rules remain fixed.

The source generator checks the frozen baseline and creates a single standalone file. Tests verify the modification scope, engine demand rates, timing/cap/repeated shops, constant-demand accounting parity, information boundaries, scenario cash constraints and the difference between averaging cash and averaging demand. The development gate explicitly rejects a tie. Verification: **180 tests passed**, repository lint and formatting checks passed.

## Matched development screen

Seeds **17/43**, both seats, Cycle 3 / Step 8 / scaled mixed, two CPU processes per run; 24 full-season games through the official loader. Both policies were run again with matching runner, environment and control hashes. All replays and runtime logs are retained locally.

| Opponent | Demand challenger | Cycle 3 reference |
| --- | ---: | ---: |
| Cycle 3 | 1 win, 3 losses | 1 win, 2 draws, 1 loss |
| Step 8 | 3 wins, 1 loss | 4 wins |
| Scaled mixed | **4 wins** | 2 wins, 2 losses |
| Total | 8 wins, 4 losses | 7 wins, 2 draws, 3 losses |
| Match score, draws half | **66.7%** | **66.7%** |
| Mean banked cash | 79,748.3 | 87,434.2 |
| Mean wages | 7,086.8 | 7,001.6 |
| Mean peak productive tiles | 35.83 | 35.25 |
| Mean milk output | 138.50 | 91.00 |
| Mean wool output | 136.33 | 178.83 |
| Mean melon output | 73.00 | 94.00 |
| Mean strawberry output | 155.08 | 148.00 |

The scenario model shifts the portfolio toward dairy and away from sheep/melons. It is not simply a larger-farm policy: every game still buys one extra quadrant. More plausible future demand assumptions do not automatically produce a stronger competitive policy.

Both policies completed all games with zero agent errors, detected unplanned crop losses, missed feeds, escaped animals, seed conflicts, duplicate crop jobs or terminal inventory/seeds. Maximum local decision time was **0.429 seconds** for the challenger and **0.205 seconds** for Cycle 3, within the configured one-second budget on this machine. This is not a server runtime guarantee.

The two development seeds are too small a sample to establish that the approach is worse in general, or that it reliably beats the strongest control. The predeclared rule required improved development match score before fresh evaluation; the tie fails that rule. We did not choose a favorable opponent subgroup after seeing results.

## Audited loss: seed 43, seat 1 versus Cycle 3

The challenger lost **57,721–73,108**. The matched Cycle 3 reference finished **86,006–86,030**. At the identical observation before the first changed action, the new forecast selected a strawberry over a melon: estimated marginal value 1,151.9 versus 768.8 coins. All eight sampled strawberry values exceeded the melon value.

The towns diverged at observation 144, displayed Day 7. The challenger eventually saw **no strawberry-buying shops**. It harvested and sold 124 strawberries for only **4,122 coins**, including **64 units sold at the one-coin floor**. The reference sold 166 for 24,081 coins. Total own receipts were 83,119 versus 111,166, while expenses were similar: 28,398 versus 28,160. The loss reflects poor realized revenue, not an execution crash or unbanked final stock.

The challenger also sold more milk but earned less milk revenue: 126 units / 11,413 coins versus 90 / 12,867. Shared inventory and different town paths matter. These are whole-policy outcomes, not proof that the first strawberry purchase alone caused the final loss. The eight-path sample did not represent every economically important low-demand sequence, and the forecast still omits future rival expansion.

## Audited win: seed 43, seat 0 versus scaled mixed

The challenger won **114,133–112,472**, while Cycle 3 lost **105,150–114,081**. It operated five cows/five sheep versus three cows/seven sheep and generated 147 milk and 155 strawberries versus 93 and 86. Own gross receipts increased by **9,775**, expenses by **792**, and final cash by **8,983**.

Town paths diverged at observation 360, displayed Day 16. The challenger ultimately received three ice-cream shops and a smoothie shop, supporting its dairy/strawberry exposure. Those favorable demand conditions accompanied the gain; the outcome does not isolate a fixed-market investment effect. Both own farms executed cleanly. The scaled opponent had its own missed feeds and crop losses in these audited games, further limiting what a win says about top-player strength.

All four selected replays were resimulated exactly. All eight player cash accounts reconcile. For the four own-player accounts there were no ineffective non-pass actions, decayed crop units, missed feeds, escapes, explicit or overnight overflow, or final goods/seeds. These executed audits are distinct from the broader runner diagnostics based on observed actions.

## Reproduction and next decision

```bash
uv run python -m scripts.make_demand_control --output artifacts/cycle-5-reproduction/main.py
uv run python evaluate.py --agent artifacts/cycle-5-reproduction/main.py \
  --opponents baselines/cycle_3.py baselines/step_8.py opponents/scaled_mixed.py \
  --seeds 17 43 --workers 2 --replays all --output artifacts/cycle-5-reproduction-games
```

The original result archive was generated with:

```bash
uv run python -m scripts.report_demand \
  --source artifacts/cycle-5-demand-dev/main.py --output NEW_REPORT.json
```

The reporter checks matching experiment manifests, source identity, audited replay hashes, state/cash reconciliation, and exact actions at the first divergent observation. Its default inputs are the retained `artifacts/cycle-5-*-development` and `artifacts/cycle-5-*-audit` directories. The archive includes the descriptive paired comparison but makes no holdout or ladder claim.

Next priority: measure downside forecast error from **future demand jointly with rival supply**, and the value of waiting for observed demand before committing scarce capacity. Keep the existing hiring and dispatch rules fixed for that diagnostic. Use the rejected implementation as a research tool; do not blend it into the submitted bot or tune path weights repeatedly on this screen. Local CPU only, $0 new spending.
