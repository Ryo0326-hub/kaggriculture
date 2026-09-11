# Server evidence and benchmark calibration

The submitted Step 8 source is unchanged. This cycle establishes server execution evidence, adds a more demanding reactive opponent, and replaces the fixed feature roadmap with an evidence-driven plan. Local compute only; no paid infrastructure was created.

## Server release and validation

Step 8 was uploaded as **56157664** on September 11, 2026 at 03:29:35 UTC (September 10, 23:29 Toronto). Its exact source hash is `63dbf4381d8607cbd681f5296749f4f8af4cc37d0181f97d6b8931f6078d3f72`; `main.py`, `baselines/step_8.py`, and the uploaded artifact agree. The latest-two pair is now **Step 8 / Step 7**; Step 6 remains saved locally.

Validation episode **107689872** completed with 94,876 / 95,069 cash and DONE/DONE status. All **1,438 decisions** match the frozen source. The pinned 1.32.7 engine reproduces every recorded economic state exactly. Maximum server decision time was **0.206756 seconds**, with no stderr, unplanned crop loss, starvation, escaped animals, resource conflicts, decay, storage overflow or terminal goods/seeds. [Source, replay/log hashes and accounting](benchmarks/step-8-server.json).

The starting 600 rating indicates no measured competitive gain. Server self-play demonstrates execution in that episode; public matches test performance against other policies. Final cash is also distinct from rating: 94,876 coins does not mean a 94,876 ladder score.

The user's earlier attachment **107665260** was Step 7 validation self-play, 82,812 per farm, all decisions matching Step 7. It precedes the previously analyzed MugaBros and Jaikrishna games. It must not be counted as another independent win or as Step 8 evidence.

## First public Step 8 game

The September 11, 03:43:17 UTC snapshot contained one completed public game: **0 wins / 0 draws / 1 loss**. Episode **107691005**, against Noobykiller16, ended **80,484–102,430**. All 719 of our decisions match Step 8, economic states reconcile exactly, both players finished DONE, and our maximum server decision time was 0.199830 seconds. Our log contains no stderr; the opponent log was inaccessible. [Public-game evidence](benchmarks/step-8-public-first.json) · [Timestamped listing](benchmarks/step-8-public-snapshot.json).

| Measure | Our Step 8 | Noobykiller16 |
| --- | ---: | ---: |
| Peak productive tiles | 37 | 70 |
| Executed wages | 6,248 | 5,791 |
| Milk / wool / strawberries sold | 93 / 194 / 70 | 155 / 258 / 148 |
| PASS actions | 2,886 | 360 |

Our execution was clean: no accidental crop losses, unfed days, escapes, ineffective actions, overflow or terminal inventory. The rival expanded on Days 7, 12 and 13; we expanded on Day 14. It won despite five animal escapes and other execution waste. This points to productive scale and labor utilization as a worthwhile hypothesis, not a conclusion from PASS counts alone. One match cannot estimate Step 8's overall ladder strength.

The generic match runner's requested-harvest diagnostic overcounts output when a rival repeatedly issues ineffective harvest commands. Public-game production in this report comes from the exact instrumented audit, which records actual inventory gains. For example, the rival's actual melon harvest was 72 units, not the 1,362 implied by summing its attempted harvests.

## Why the benchmark needed repair

The September 11, 03:21 UTC official snapshot recorded **9 wins / 13 losses** across Step 7's 22 completed public games. Step 7's original local promotion pool had yielded 360/360 wins. Different opponents and selection processes make these percentages incomparable as a causal estimate, but the discrepancy is strong evidence that internal coverage was inadequate. [Timestamped public listing](benchmarks/step-7-live-snapshot.json).

We selected three informative losses for mechanism analysis. Each replay reproduces exactly and cash reconciles to starting cash plus executed sales less executed expenses. These selected losses are development evidence, not a random sample.

| Episode / opponent | Opponent bank | Step 7 bank | Opponent peak productive tiles | Opponent strawberries sold |
| --- | ---: | ---: | ---: | ---: |
| 107670771 / Tamizharuvi | 162,638 | 83,771 | 68 | 271 |
| 107680182 / OceanMix | 143,157 | 51,380 | 75 | 245 |
| 107685480 / DevilQ | 89,173 | 74,565 | 70 | 72 |

Step 7 peaked at **19 productive tiles in each of these games**. The old independent expanding control allowed only 36 crop sites plus four animals, excluded carrots/tomatoes/geese, paused new seed buying after its opening until Day 9, and reserved return-to-shed travel every day. Those limits left important pressure untested. [Reconciled profiles](benchmarks/calibration-server-profiles.json) · [Crop-age and transaction timing](benchmarks/calibration-server-timing.json).

## What the stronger opponents actually did

**Use scarce worker turns on dated service.** OceanMix's Day 16 farm held 58 crops plus 17 animals. The farmer and 12 hands issued 293 actions: 115 moves, 158 successful service/handling operations, and 20 passes. A tile did not need every possible service every day. This matters more than simply imposing a larger worker cap.

**Exploit ordinary-night deposit/reset.** OceanMix ended 261/297 worker-days away from the shed; DevilQ 244/258 and Tamizharuvi 230/322. The engine transfers carried goods at ordinary day boundaries and resets positions. A route need not return every night. The shared shed cap is still 100 units and overflow destroys value; the final partial day still requires explicit delivery and sale.

**Coordinate fertilizer with yield dates.** OceanMix fertilized wheat at age 2 in 70/72 applications and harvested 67 mature wheat lots at six units each. Strawberry applications concentrated around ages 9 and 13; seven tomato plants delivered 56 units with applications around ages 7 and 10. This is evidence of timed input use, not evidence that their private code solves an integer program. Surviving a crop is different from maximizing its harvest.

**Finance scale and apply market pressure.** Tamizharuvi sold 271 strawberries for 69,493 coins. OceanMix sold 245 for 60,075, alongside carrots, tomatoes and animal goods. These larger portfolios create a different shared market for our production. Current prices and visible shops matter; neither future shop unlocks nor rival intentions are known to the agent.

**Separate trading from physical output.** Gross wheat sales are misleading when wheat is bought and resold:

| Opponent | Wheat harvested | Bought | Sold | Wheat sales less purchase cash |
| --- | ---: | ---: | ---: | ---: |
| Tamizharuvi | 218 | 927 | 824 | −3,231 |
| OceanMix | 522 | 356 | 527 | +8,294 |
| DevilQ | 242 | 505 | 498 | +1,251 |

The last column excludes seeds, wages and the opportunity cost of wheat fed to animals. It is not wheat profit. All observed equal-quantity buy/sell turns (12 Tamizharuvi, eight OceanMix) netted exactly zero cash. Their intent is unknown; the evidence does not support copying those pairs as profitable arbitrage.

## Implemented benchmark changes

`opponents/scaled_mixed.py` is our own reactive stress policy derived from our existing expanding control. It imports no candidate code and reads no evaluation seed, future demand or replay. Its fixed portfolio is a deliberate stress case, not an optimal farm strategy.

It targets ten animals and up to 60 crop sites, purchases up to two additional quadrants subject to current cash, reinvests in early wheat and strawberries, schedules fertilizer around yield dates, and uses compact worker zones. Ordinary-night harvests do not reserve a return journey; the final day does. Shared seed, feed and fertilizer reservations prevent simultaneous overrequests; harvests reserve remaining shed capacity. It uses current cash to fund purchases and does not spend hypothetical same-turn receipts.

Development seeds 17 and 43 exposed unnecessary travel and crop-expiration priorities; those were corrected before freezing. The control beat the old expanding control in all four development games. Its later frozen comparison is the evidence that matters for benchmarking. Larger scale is implemented, but installation, wheat expiration, seed buying and maintenance remain imperfect. It is a **test opponent, not a new release candidate**.

`scripts/benchmark_profiles.py` extracts the same descriptive measurements from server and local replays after verifying the replay hash and exact-state audit: productive scale, physical output, product purchases/sales, wages, first-sale steps, land dates, overnight positions and operational losses. It prevents bought-and-resold goods from being described as production.

## Matched frozen comparison

The [protocol](benchmarks/calibration-protocol.json) was saved before running seeds 9101–9120: both seats, three opponents, 120 games per policy, four local CPU processes. Both Steps 7 and 8 remained fixed. The old and new expanding controls share a policy family; delayed crop supply supplies another family. This is a coverage diagnostic, not a complete ladder model.

| Opponent | Step 7 wins / 40 | Step 8 wins / 40 |
| --- | ---: | ---: |
| Stronger scaled mixed control | 5 | 13 |
| Old expanding mixed control | 23 | 39 |
| Delayed crop supply | 40 | 40 |
| **Total wins / 120** | **68** | **92** |

There were no draws or execution errors. Step 8 improved matched pool score from **56.67% to 76.67%**, a **20.00 percentage-point** gain. The 95% whole-seed bootstrap interval for the difference was **+10.00 to +30.83 points** (20 seed blocks, 10,000 resamples). The result supports retaining Step 8's expansion improvement, while its **32.5% score against the new control** exposes substantial remaining weakness. The aggregate score weights these three controls equally and should not be extrapolated to the leaderboard. [All manifests, game records, operational totals and comparison](benchmarks/calibration.json).

Across both 120-game runs, the frozen policies had zero recorded unplanned crop losses, missed feeds, escapes, seed overrequests, duplicate targets or terminal goods/seeds. There were no errors counted as economic wins.

Against Step 8, the stronger control consistently reached **67–68 productive tiles** and produced **245–249 strawberries**, versus **39 productive tiles and 172–178 strawberries** for the old control. It also produced 387–415 wheat, 129–138 milk and 88–106 wool. This closes a material scale/strawberry coverage gap but still falls short of some rivals' animal output and product breadth.

The exact audited first game confirms **245 actual strawberries harvested and sold**, with no ineffective non-pass commands or overflow in the control. Its limitations are measurable: two unfed animal-days, 19 wheat units decayed, two uninstalled purchased animals left in stock, and five unused seeds. These weaken this benchmark opponent; they are not intentional optimal retirement decisions. Our Step 8 side was operationally clean. [Exact local profile](benchmarks/calibration-local-profile.json).

Parallel local execution recorded three Step 8 games with a decision above one second, with a **2.169056-second** maximum while other local verification work was also active. No engine timeout occurred. The two affected seeds (9115/9116 against delayed crops) were rerun serially in both seats: all four final cash pairs matched exactly and maximum decision time fell to **0.246675 seconds**. These reruns are timing diagnostics, not four extra independent games. Actual audited server maxima were 0.206756 seconds in validation and 0.199830 in the public game; neither local nor two server games proves worst-case runtime for all observations.

The new control was frozen before the matched games and was not changed in response to them. The benchmark is now more demanding; calibration remains incomplete for larger livestock herds, additional crop/animal species and genuinely different reactive policy families.

## CO250, economics and the next hypothesis

The binding constraint is often **available service and travel time**, not land alone. In an integer model, let a binary variable select a worker route. Route coefficients consume turns, seed/feed/fertilizer stock and delivery capacity; associated jobs release dated output. The discrete number of hired workers determines Fibonacci wage costs. A job's value is its marginal banked receipts after inputs, extra labor and displaced work.

A route-to-shed constraint on every normal day can exclude useful feasible schedules. Model the ordinary overnight transfer as a time-bound inventory flow into a shared 100-unit capacity. At season termination that edge is unavailable, so goods must reach the shed through actual worker actions. This is an introduction to time-expanded network-flow thinking; the current policy is a heuristic and does not solve a full network-flow or global integer optimization problem.

In LP-duality language, a shadow price represents the value of relaxing a scarce resource constraint. Here, saved worker turns have value only if they complete profitable work or allow a cheaper crew. The actual value is not simply `saved turns × average wage`: hire counts are discrete, wages grow nonlinearly, and task prerequisites/deadlines matter. Current prices times total output also overstate receipts when our sales depress a shared market.

**Recommended next experiment:** hold the installed portfolio fixed and test day-aware delivery routing against unchanged Step 8. Measure realized wages, output, storage losses and final cash, then reconcile investment forecasts with actual staffing. Keep ordinary-night optimization and final-day safety distinct. This isolates a plausible bottleneck before adding more acreage or another product. [Active performance plan and release gates](PERFORMANCE_PLAN.md).

## Verification

All **120 tests passed** locally; Ruff lint and formatting checks passed. New tests cover frozen Step 8 identity, production versus resale accounting, crop expiration, normal-night versus final-day delivery, shared harvest capacity, full-season supply coverage, and rejection of mismatched replay audits. The submitted policy and all frozen benchmark hashes were rechecked after evaluation.

## Limits and reproduction

- Public opponent source is unavailable. Observed behavior does not reveal whether their bots use optimization, heuristics or learning. Recorded actions are used only for audit, never as a reactive counterfactual opponent.
- The new control improves scale and strawberry coverage. It does not reproduce leaders' larger dairy herds, carrots/tomatoes/geese, all timing choices or adaptive game theory. Local confidence intervals omit those coverage gaps and matchmaking selection.
- An away-from-shed fraction describes positions, not useful work. Our control can finish early and return voluntarily; sharing the overnight mechanism does not imply matching the leaders' schedule efficiency.
- Seeds 9101–9120 must become development data if future policies are changed after inspecting these results. The old 9001–9030 validation set is already retired for subsequent tuning.
- Raw replays/logs are kept in ignored `artifacts/`; compact evidence and their hashes are committed. Engine/version and exact source hashes are preserved in the protocol and server reports.

```bash
uv run python scripts/audit_replay.py <downloaded-replay.json> --output artifacts/replay-audit
uv run python scripts/benchmark_profiles.py <downloaded-replay.json> \
  --audit-directory artifacts/replay-audit --output artifacts/replay-profile.json
uv run python evaluate.py --agent baselines/step_8.py \
  --opponents opponents/scaled_mixed.py opponents/expanding_mixed.py \
  --seeds 9101 9102 --workers 4 --output artifacts/calibration-reproduction
```

For the full frozen protocol, regenerate the delayed control with `uv run python scripts/make_early_control.py --delay-sales-until 18 --output artifacts/step-7-pool/delayed-crops.py`, verify its hash against the protocol, and run all three opponents on seeds 9101–9120 for each baseline. Existing output directories are not overwritten. Reproduction is not additional statistical evidence.
