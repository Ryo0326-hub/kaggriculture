# Cycle 8 results — reactive purchase continuation

**Evaluator completed; no live-policy change or upload.** Six continuations from two selected seed-17 observations passed. Both unchanged controls reproduce every remaining action and economic state of their source games; wall-clock overage bookkeeping is excluded. All twelve player cash accounts reconcile from the branch through termination. [Frozen plan](CYCLE_8_PLAN.md), [machine-readable evidence](benchmarks/cycle-8-continuation.json), [CO notes](CYCLE_8_OPTIMIZATION.md).

Every alternative uses the same Cycle 3 continuation policy for our decisions. The opponent also replans from its own current observation. Future recorded actions are comparison evidence only. Investments can continue after the intervention. These are **conditional diagnostics from two states on one consumed seed**, not six independent games or a promotion benchmark.

## Outcomes

| State | Intervention | Own final cash | Rival final cash | Margin | Outcome |
| --- | --- | ---: | ---: | ---: | --- |
| Early, observation 48 | Original melon purchase | 86,066 | 86,066 | 0 | Draw |
| Early | Omit purchase this turn | 86,066 | 86,066 | 0 | Draw |
| Early | Wait until next shop, observation 72 | 86,753 | 81,386 | +5,367 | Win |
| Late, observation 409 | Original melon purchase | 44,472 | 31,043 | +13,429 | Win |
| Late | Buy one wheat instead | 43,639 | 29,690 | +13,949 | Win |
| Late | Omit purchase this turn | 44,472 | 31,043 | +13,429 | Win |

The one-turn omissions simply buy the melon on the following observation, leaving terminal cash, physical output and shops unchanged. Omitting one action is therefore different from deliberately waiting for information.

Early waiting releases capital decisions at observation 72, when Cycle 3 buys a sheep. Our continuation produces 220 wool versus 190, but 72 milk versus 87 and 166 strawberries versus 175. Additional sales of 1,262 exceed additional expenses of 575, leaving 687 more own coins. The rival loses 4,680 coins, accounting for most of the margin improvement. Our control makes fourteen further capital-order turns after its initial melon; the waiting branch makes seventeen from observation 72 onward. The comparison gives both paths future investment opportunities.

However, the first shop changes from PET_CAFE to YARN_STORE at observation 72. Occupancy affects the random draws consumed before shop selection. The actual reactive opponent first changes an action at recorded state 97. This result combines timing, reinvestment, market response and a different demand realization; it is not an estimate of pure information value. It also does not rehabilitate Cycle 6, whose whole-policy development comparison failed.

At the late state, original forecasts value wheat at 74.6 and melon at 78.2. Correcting rival wheat accounting raises wheat to 78.4, a predicted 0.2 advantage over melon. The actual wheat continuation reproduces Cycle 7's changed outcome even though all later decisions use the original Cycle 3. It produces six more wheat and six fewer melons. Our sales fall 937 and expenses fall 104, leaving 833 fewer own coins. Rival cash falls 1,353, so the winning margin improves by 520.

The rival's actions remain identical on this branch, but they were generated reactively, not copied. At observation 576 its final town opening changes from PIZZA_SHOP to FARMERS_MARKET. Own-profit and margin rankings differ, and a tiny forecast preference does not describe the size or cause of the realized difference. Neither outcome improves the existing win.

## An actionable cash constraint error

In the early waiting branch, observation 144 starts with 853 coins. The incumbent buys a sheep for 500 after ordering feed and hiring. Its source-matched investment projection reports **minimum cash 155**; actual cash reaches **64 at observation 153**, before any intervening sale.

Executed costs from observations 144–152 are:

| Cost | Coins |
| --- | ---: |
| Sheep | 500 |
| Five initial wheat units | 167 |
| Initial seven hires | 33 |
| Two additional wheat units | 68 |
| One additional hire | 21 |
| Total | 789 |

853 − 789 = 64. The projection's current-day spending after its planning snapshot includes the animal purchase but does not cover the subsequent 89 coins of feed and repair labor. A further two-coin difference comes from the initial quote versus execution. The model's 150-coin reserve is an estimated admission constraint, not a guaranteed account floor. The farm nevertheless completes with no missed feeding or lost stock; this is a calibration defect, not evidence that a larger blanket reserve would improve competition performance.

**Next priority:** calibrate remaining-day cash obligations before capital admission. Use consumed states to compare forecast feed and repair-hiring costs with executed costs before receipts arrive. Then isolate a correction to current-day input/labor charging, leaving actual dispatch, hiring rules, future-demand model and candidate ranking fixed. Require a bounded development improvement before fresh seeds. Do not encode these particular shop outcomes, adopt unconditional waiting, or restore the rejected scenario policy.

## Validation and preservation

All six continuations finish with both players DONE and 720 recorded states. Both controls exactly reproduce the source future. Our audited continuations have no ineffective non-pass operations, missed animal feeding, escapes, crop decay, overflow or terminal stock/seeds. Maximum observed own decision time is 0.334 seconds; these local timings are not server guarantees. The 207-test suite passes, including focused tests for both seats/shared clocks, prefix corruption, reactive rivals, poisoned recorded future actions, intervention release, failed agents and cash accounting. Lint and formatting checks pass.

`main.py`, frozen Cycle 3 and its uploaded artifact retain SHA-256 `47c281bfb4118a9755f1759930b162de007efdfef3b23144457eccbaac42da0c`. No new agent is ready to upload. Seeds 9401–9420 remain unused; no compute was purchased. Kaggle status was not refreshed during this diagnostic.

Reproduce from the repository root, with the two pinned Cycle 6 source replays present:

```bash
uv run python -m scripts.benchmark_continuation --cases experiments/continuation_cases.json --workers 2 --output artifacts/cycle-8-continuation-repeat
uv run python -m scripts.report_continuation --root artifacts/cycle-8-continuation-repeat --output artifacts/cycle-8-continuation-repeat/evidence.json
```

Full replays/audits remain local under the run directory. Committed evidence includes source hashes, branch-state hashes, interventions, forecasts, executed costs/output, capital traces and divergence indices. A clean clone needs the exact archived source replays. Regenerating matches can change replay metadata and file hashes even when gameplay is identical; those would be new inputs requiring a separately pinned case specification, not a silent replacement of the archived evidence.
