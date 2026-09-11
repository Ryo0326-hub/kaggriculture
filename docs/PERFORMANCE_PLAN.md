# Performance-first plan

Agreed September 10, 2026 (Toronto): prioritize competitive performance; use local CPU compute with **US$0 new spending**; retain a validated incumbent and test bounded challengers. Ryo leads with roughly three hours per day. Ryo and Codex choose hypotheses together; Codex implements and tests; Ryo reviews evidence and reasoning. CO notes remain part of every implementation, but course coverage does not determine feature priority.

This replaces the fixed ordering of the original Steps 9–11. Steps 1–8 are completed engineering checkpoints, not evidence that the agent is finished or medal competitive.

Current checkpoint: **Cycle 3 fertilizer timing is locally qualified and packaged; upload is pending.** The exact current file is `47c281bfb411…`. Review the intended latest-two pair before uploading, then reconcile server validation and public episodes. [Results](CYCLE_3_RESULTS.md), [CO notes](CYCLE_3_OPTIMIZATION.md).

## Cycle 1 — server evidence and benchmark calibration

**Implemented.** Upload the exact Step 8 artifact, reconcile its server validation, audit three actual Step 7 losses, add a reactive high-throughput control, and compare frozen Steps 7/8 on matched fresh games. Read [the calibration report](SERVER_AND_BENCHMARK_CALIBRATION.md) and [frozen protocol](benchmarks/calibration-protocol.json) for outcomes and remaining coverage gaps.

Step 8 and Step 7 now occupy the latest-two submission window. Step 6 remains preserved locally. Keep Step 7 as the protected incumbent while Step 8 accumulates actual public games; the latest rating alone does not select a champion.

## Cycle 2 — measure recoverable scheduling value

**Completed without promotion.** [Cycle 2 results and CO notes](CYCLE_2_RESULTS.md): 36 controlled installed-portfolio games plus 56 standard-start development games. Staffing changes saved wages in some fixtures, but none of six candidates improved the matched Step 8 match score. Forecast variants also exposed one crop loss and seven unused seeds. The submitted `main.py` was retained at that checkpoint; Step 8 remains preserved in its baseline file. Experimental implementations are isolated under `experiments/`. No fresh validation seeds or new submission slot were used in Cycle 2.

The tested hypothesis: day-aware delivery routes can increase banked output or reduce wages because ordinary nights automatically deposit carried goods and reset worker positions. The final day still needs explicit delivery and sale before termination. Inspection confirmed that Step 8's crop dispatcher already allowed ordinary-night deposit; changes therefore targeted livestock routing and the staffing/forecast assumptions.

First run a controlled installed-portfolio experiment. Compare the unchanged dispatcher with one delivery-rule challenger on identical farms, inventory, markets and staffing alternatives. Include one-, two-, and three-quadrant portfolios. Keep investment and sale policy fixed so the experiment identifies dispatch effects. Measure completed maintenance and production, wages, deposit overflow, missed deliveries, and terminal cash. PASS counts alone are not the target.

Then connect the investment forecast to the same service and delivery assumptions, charging the actual discrete hiring schedule. Test forecast changes separately before combining them with dispatch changes. Reject a change that simply reports lower predicted costs without realizing more banked cash, or that creates accidental crop loss, starvation, overflow, resource conflicts or final stock.

The new benchmark provides difficult development cases, not permission to optimize repeatedly against a supposedly untouched holdout. Seeds 9101–9120 become development data once used to change either policy. Freeze promising challengers before allocating new evaluation seeds.

## Cycle 3 — production timing and marginal inputs

**Implemented; fertilizer-only passed local qualification.** [Cycle 3 results](CYCLE_3_RESULTS.md): 36 installed-portfolio games, 24 normal-start development games and 240 matched fresh games. The selected policy allows profitable strawberry fertilizer after watering and before urgent watering when both actions fit. Step 8's investment functions and hiring calculation remain unchanged. The early-wheat-harvest experiment lost fixture cash and added no new decisions in normal-start games, so the old harvest rule is retained.

On the frozen 20-seed pool, the selected candidate scored 86.7% versus 60.8% for Step 8, with whole-seed 95% improvement interval +20.0 to +32.5 points. It won 24/40 versus Step 8's 13/40 against the stronger control. Both runs were clean on the recorded execution, crop-loss, feeding and terminal-stock diagnostics. The exact file passed isolated full-season validation and is now `main.py`; the submitted Step 8 file remains preserved separately. These are local results, not server or medal evidence. Seeds 9201–9220 are consumed evaluation data and must not be reused as an untouched holdout.

Next, validate the exact artifact on Kaggle and audit real ladder games before changing the policy again. The last recorded latest-two pair is Steps 8/7, so review which proven bot the next upload should retain. The broad staffing/forecast redesign remains parked. Fertilizer valuation is still approximate on crowded farms, where extra supply can reduce prices.

Other candidates remain early wheat/carrot receipts, profitable crop maturity dates, selective maintenance, and response to visible rival supply and shop demand. Test one economic claim at a time. For example, compare an early harvest with waiting after charging lost future yield, tied-up cash, extra service, inventory pressure and expected market prices.

A larger farm is useful only when its extra sales repay seeds, land, feed and incremental Fibonacci wages before termination. Neither copying an opponent's purchase list nor buying every quadrant is the objective. Gross wheat sales can include bought-and-resold inventory; use physical production and executed net cash flows separately.

Add competent carrot/tomato/goose and larger livestock scenarios to the benchmark when their behavior is relevant to a challenger. The new mixed control is related to the old mixed control; they do not count as independent algorithm families.

## Selection and release gates — applied every cycle

1. State one hypothesis and its success/failure measurements before coding. Keep the incumbent artifact hash fixed.
2. Run a bounded development screen and explain the cash and resource differences. Do not spend days tuning a weak result.
3. Freeze the challenger and relevant controls. Evaluate both policies on the same new seeds, seats and reactive pool. Use whole-seed uncertainty intervals and inspect opponent-specific regressions.
4. Resolve execution failures and material accidental operational losses. Verify the exact self-contained artifact in isolated full-season play and check server runtime after upload.
5. Upload a meaningful challenger only after reviewing which incumbent the new upload displaces. Record submission ID, source hash, validation episode, and a timestamped public-game snapshot.
6. Promote on consistent local and server evidence. A validation win, a starting 600 rating, or one favorable ladder match is insufficient. Preserve rejected experiments and the reason for rejection.

Do not buy compute without a new budget decision. Do not switch to end-to-end reinforcement learning or an LLM acting every turn without evidence that it addresses a measured bottleneck better than the current approach.

## Time budget and final window

A practical three-hour review/experiment block: 20 minutes for new server evidence, 30 minutes for the hypothesis and CO/economic model, 90 minutes for a bounded experiment, and 40 minutes for results, regression checks and the next decision. Larger changes can span several blocks; avoid forcing an upload each day.

Internal target: stop speculative redesigns by September 27 and validate the intended final two artifacts on September 28–29, leaving September 30 for verified defects or platform delays. Official entry/team-merger deadline: September 23, 23:59 UTC; final submission deadline: September 30, 23:59 UTC (19:59 Toronto). These dates were checked during this review against the [official timeline](https://www.kaggle.com/competitions/kaggriculture/overview/timeline).

The [evaluation rules](https://www.kaggle.com/competitions/kaggriculture/overview/evaluation) allow five submissions per day and use the latest two for final evaluation. Matchmaking and opponent selection are not randomized experiments under our control. Track actual game outcomes and validation status separately from the changing rating.
