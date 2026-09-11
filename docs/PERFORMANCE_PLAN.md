# Performance-first plan

Agreed September 10, 2026 (Toronto): prioritize competitive performance; use local CPU compute with **US$0 new spending**; retain a validated incumbent and test bounded challengers. Ryo leads with roughly three hours per day. Ryo and Codex choose hypotheses together; Codex implements and tests; Ryo reviews evidence and reasoning. CO notes remain part of every implementation, but course coverage does not determine feature priority.

This replaces the fixed ordering of the original Steps 9–11. Steps 1–8 are completed engineering checkpoints, not evidence that the agent is finished or medal competitive.

Current checkpoint: **Cycles 6 and 7 are complete without promotion; retain the submitted Cycle 3 agent.** Waiting with rival supply stress scored 38.9% versus 72.2% and lacked runtime headroom. The isolated wheat-conservation fix tied at 72.2%, with no game-outcome improvement. Neither advanced to fresh evaluation or upload. [Cycle 6 results](CYCLE_6_RESULTS.md), [Cycle 7 results](CYCLE_7_RESULTS.md). The latest checked server snapshot remains September 11, 11:28 UTC, when submission 56158876 was COMPLETE and the latest-two pair was Cycle 3 / Step 8. This work did not refresh that snapshot. [Server analysis](CYCLE_3_SERVER_ANALYSIS.md), [snapshot](benchmarks/cycle-4-submissions-snapshot.json).

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

The subsequent server audit confirmed the fertilizer timing behavior in actual ladder games: 96 successful applications after watering, with no own crop decay, missed feeds, overflow or terminal stock. The two losses still showed much larger rival farms with lower wage spending. The broad staffing/forecast redesign remains parked. Fertilizer valuation is still approximate on crowded farms, where extra supply can reduce prices.

## Cycle 4 — location-aware investment alternatives

**Completed without promotion.** Development improved from 66.7% to 83.3% match score, but the frozen 240-game comparison improved only 0.83 percentage points (95% whole-seed interval −5.83 to +6.67). Against the strongest control the candidate won 25/40 versus Cycle 3's 28/40. Both policies were clean on recorded execution and operational checks. Preserve the challenger and evidence; keep `main.py` byte-identical to submitted Cycle 3. Seeds 9301–9320 are now consumed evidence. No new Kaggle upload.

The supplied losses justify testing a specific search restriction before changing hiring or the full forecast. Current admission refuses new land while more than six owned crop sites are vacant, regardless of their locations. A distant vacant tile is not necessarily a substitute for a nearby tile in a new quadrant.

The isolated challenger removes that vacancy-count exclusion and requires each paid-land batch to use at least one actually locked tile. All existing route feasibility, land cost, cash reserve, payback, profitability ranking and hiring rules remain unchanged. [Implementation and CO notes](CYCLE_4_OPTIMIZATION.md). The development screen contains 12 games per policy; the frozen matched comparison uses new seeds 9301–9320, both seats and Cycle 3 / Step 8 / scaled mixed controls. No policy bytes change during evaluation.

A more permissive menu does not establish that the larger farm can be serviced profitably. In the motivating server state, new feasible one-crop expansion options are still unprofitable and larger batches still fail the old forecast. In development every candidate farm still bought only one extra quadrant. Fresh evaluation did sometimes reach a third quadrant, but mean footprint grew less than one productive tile and mean cash declined. The restricted search was real; removing it did not solve the economic bottleneck.

Cycle 4 identified **marginal investment forecasts** as the priority before another admission relaxation. In fresh seed 9310 against the scaled control, the challenger shifted from milk toward more crops and a third quadrant: milk fell from 192 to 129 units while strawberries rose from 158 to 202; both seats changed from wins to losses. Test the actual dated cash and service consequences of competing crop versus livestock additions, holding dispatch and hiring rules fixed first. Check remaining-season yield, land cost, displaced investment and shared-market prices against executed outcomes. Avoid returning to a blanket wage reduction or assuming that a larger portfolio necessarily wins. The same release gates and protected incumbent remain in force.

The exact regression audit also establishes that weed generation and shop selection share a seed/day RNG: changing occupancy can change future town shops even on a matched seed. Seed 9310's towns diverged on Day 13. Therefore do not attribute its entire cash difference to crop-versus-dairy choices at fixed demand. Prioritize plausible future-shop demand scenarios in the investment forecast, using only current observations; retain fixed dispatch/hiring for the initial comparison. No hidden seed, future shop list, or recorded rival actions may enter the live policy. [Mechanism and trajectory evidence](benchmarks/cycle-4-regression.json).

## Cycle 5 — investment under uncertain future shop demand

**Completed without promotion.** The isolated challenger values each expansion option over eight equally weighted, dated shop sequences, pairing the option with the existing portfolio under the same future demand. It enforces the existing cash reserve in every sampled path. Opening, land admission, actual dispatch/hiring, fertilizer, harvest and sale rules remain fixed. [Implementation/CO notes](CYCLE_5_OPTIMIZATION.md), [pre-experiment plan](CYCLE_5_PLAN.md).

The 24-game development comparison on seeds 17/43 tied at 66.7% match score. The challenger won 4/4 against scaled mixed versus 2/4 for Cycle 3, but declined to 1/4 against Cycle 3 and 3/4 against Step 8. Mean own cash fell from 87,434.2 to 79,748.3. Both policies were clean on recorded operational checks; four exact audits also reconcile cash and show no own overflow or decay. The preregistered improvement gate failed, so seeds 9401–9420 were not run. The eight-path approximation is implemented and reproducible; it is not part of `main.py`.

The portfolio shifted toward more milk and fewer sheep/melons. In the largest regression, the challenger sold 64 strawberries at the one-coin floor in a town with no strawberry-buying shops. In a strong-control win, three ice-cream shops and a smoothie shop supported dairy/strawberry production. These are two inspected seed blocks, not proof of general superiority or inferiority. The towns differed between policies because occupancy affects shop randomness.

Cycle 5 identified **downside investment error from joint demand and rival-supply uncertainty**, including the option to wait for a shop opening, as the next hypothesis. Keep actual hiring and dispatch fixed. Determine when future rival production or a poorly covered low-demand path changes the preferred purchase. The current forecast assumes only visible rival assets and does not price all future displaced investments. Do not repeatedly tune scenario paths against these development games or blend rejected code into the submitted bot. Freeze any bounded successor before assigning a new evaluation set.

## Cycles 6 and 7 — waiting, supply stress and an isolated accounting correction

**Both completed without promotion.** Cycle 6 compared immediate purchases with branch-dependent purchases after the next shop opening, using a conservative marginal value across visible and expanded rival supply. It preserved the opening, actual hiring/dispatch and fertilizer rules. Two partial engineering runs were superseded for a wheat-conservation correction and equivalent labor caching; only the final complete run counts for selection. [Plan](CYCLE_6_PLAN.md), [CO notes](CYCLE_6_OPTIMIZATION.md).

On consumed seeds 17/43/9310, both seats and the three controls, its 18 games scored 38.9% versus 72.2% for 18 incumbent games. Mean own cash rose by 1,639.4, but mean margin fell from +5,377.3 to −2,976.4; it lost all six direct games. Maximum decision time was 1.636 seconds. Own operational checks were clean, and four exact audits reconcile cash. The larger waiting estimate is not pure information value: it combines timing and future liquidity while omitting later reinvestment after buying now.

Cycle 7 then tested only rival wheat conservation in the original expansion forecast. Wheat used as feed cannot also be sold. This is a separately recorded correctness hypothesis, with no Cycle 6 scenario/waiting policy. Eighteen new games reuse the same incumbent reference. Match score tied at 72.2%, with seventeen identical joint-action trajectories. A 0.2-coin forecast advantage switched one late melon purchase to wheat, accompanying 833 fewer own terminal coins in the one changed game; it remained a win. [Plan](CYCLE_7_PLAN.md), [results](CYCLE_7_RESULTS.md), [CO notes](CYCLE_7_OPTIMIZATION.md).

Both gates failed; the submitted artifact remains untouched and **9401–9420 remain unused**. Across the two screens there are 54 complete games (two challengers and one shared reference), plus eight completed games from excluded partial engineering runs. These are not 62 independent selection observations.

Next priority: an offline **purchase-continuation calibration** on a small set of already inspected states, including Cycle 7's observation 409. Compare the competing purchases with both sides continuing their reactive policies and with both buy-now and wait alternatives allowed to reinvest later. Measure win/loss and cash margin, not only own cash, and compare realized differences with the forecast's tiny decision margins. Do not give hidden replay state or future RNG information to the live bot. Use this diagnostic to choose one bounded improvement before allocating fresh seeds; do not keep enlarging the failed one-purchase scenario model.

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
