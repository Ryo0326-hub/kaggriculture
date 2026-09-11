# Cycle 9 results — better cash estimates, worse match outcomes

**Completed without promotion or upload.** The isolated cash-admission challenger failed its development performance gate. Preserve Cycle 3 as the submitted bot. [Plan](CYCLE_9_PLAN.md), [CO notes](CYCLE_9_OPTIMIZATION.md), [new server-game analysis](CYCLE_9_SERVER_ANALYSIS.md).

The standalone candidate is generated from frozen Cycle 3 by `scripts/make_cash_control.py`, with SHA-256 `f789bc00a15fd25056e337ad8cd18a1b279899514685c57a861d5f05a0d5417f`. Only expansion affordability changes, through a bundled current-day cash helper. Existing profit projections, candidate generation/ranking, opening, actual dispatch/hiring, fertilizer and sales functions retain their behavior. The generator reproduces the evaluated bytes exactly.

## Calibration

The helper funds feed replenishment and extra installation/crop hires before forecast receipts, without charging held inputs or paid/planned labor twice. On 64 eligible intervals from four already observed trajectories:

| Diagnostic | Original | Challenger |
| --- | ---: | ---: |
| Mean absolute cash-estimate error | 82.3 | 37.5 |
| Optimistic intervals | 32 | 10 |
| Motivating sheep-purchase estimate | 155 | 66 |

The motivating observed balance is 64. Five recorded purchases become ineligible, including two in the supplied server game. These are correlated calibration observations, not independent performance tests. Some full-day charges precede sales in the model even when actual receipts arrive earlier. [Calibration evidence](benchmarks/cycle-9-cash-calibration.json).

## Frozen development screen

Eighteen new games use consumed seeds 17/43/9310, both seats and three reactive controls, with two local processes. The matched incumbent reference is the existing complete Cycle 6 run; it is reused evidence, not eighteen new reference games. [Results, first changed decisions and exact audits](benchmarks/cycle-9-cash.json).

| Measure | Challenger | Cycle 3 |
| --- | ---: | ---: |
| Wins / draws / losses | 10 / 2 / 6 | 11 / 4 / 3 |
| Match score | **61.1%** | **72.2%** |
| Score against Cycle 3 | 33.3% | 50.0% |
| Score against Step 8 | 100% | 100% |
| Score against scaled mixed | 50.0% | 66.7% |
| Mean own cash | 90,243.4 | 90,226.6 |
| Mean cash margin | +3,173.5 | +5,377.3 |
| Mean wages | 7,043.8 | 7,055.2 |
| Mean peak productive tiles | 35.44 | 35.83 |
| Mean strawberries harvested | 145.9 | 163.8 |
| Maximum local decision time | 0.453 s | 0.301 s |

All games complete without execution errors. Both policies have zero recorded crop losses, seed overrequests, duplicate crop targets, escaped/unfed animals or remaining terminal stock. Exact audits of two changed matches per policy also reconcile all eight accounts, with no own ineffective operations or missed feeding. Runtime remains below one second. The rejection is for competitive results, not a software failure.

## Why the more accurate gate hurt

At observation 193 of seed 9310 against Cycle 3, the original buys twelve strawberries. The new forecast correctly includes another 233 coins of hiring, reducing its cash estimate from 276 to 43. The candidate instead buys eight strawberries. **Both branches still execute the same two extra hires for 233 coins on the next turn.** The smaller batch does not save that labor cost.

The original actually reaches 43 coins and completes its work. The challenger has a higher overall minimum of 183 but ends with 93,042 versus the rival's 94,561, replacing a 94,405–94,405 draw. Own strawberries fall from 214 to 144, while milk rises from 165 to 201. Gross sales fall only 88, but expenses rise 1,275. The changed portfolio and later shops mean this is not a fixed-demand causal estimate of the four omitted seedlings. It does establish that a low positive balance is not the same as infeasibility.

Against scaled mixed on seed 17, the same twelve-versus-eight decision predicts 148 coins after wages. The retained 150 threshold rejects the larger batch by just two coins. It changes a 44,472–31,043 win to a 53,673–53,770 loss. Our cash increases 9,201, but the rival gains 22,727. Both branches again pay the same immediate extra hires. Later shops differ, so the larger own cash does not establish better production economics at fixed demand, and it certainly does not establish a better match outcome.

The cash accounting defect was real. Using the corrected estimate with an unchanged blanket reserve is not a proven improvement. Do not lower that reserve repeatedly until these inspected seeds pass, or merge the correction on accounting accuracy alone. The failed challenger stays an archived experiment.

## Next priority

Shift the next bounded experiment toward **early wheat production for feed and short-cycle receipts**. The new server opponent physically harvested 517 wheat versus our 48, supported a larger farm and spent substantially less on wages. Add a wheat-inclusive opening alternative to the existing finite portfolio search, with explicit seed, service, harvest and avoided feed-purchase accounting. Keep actual hiring/dispatch fixed initially and compare on the reactive development pool, including wheat-heavy supply stress. Preregister the exact menu before running it; this is a hypothesis, not a conclusion from one opponent's trajectory.

The batch audit adds a constraint for that work: fewer planted tiles need not save wages when both batches need the same integer crew. Compare production and net cash per paid crew, not only asset count or minimum bank balance. Do not extend the failed reserve tuning or copy Ace Team's future actions.

No fresh seeds were consumed; 9401–9420 remain unused. No paid compute, new submission file, isolated release validation or Kaggle upload was performed. The submitted source stays `47c281bfb411…`. The new server replay adds evidence about that policy; no live leaderboard/latest-two query was made.

Reproduction, from the repository root with the archived inputs present:

```bash
uv run python -m scripts.make_cash_control --output artifacts/cycle-9-cash-repeat/main.py
uv run python -m scripts.calibrate_cash --source artifacts/cycle-9-cash-repeat/main.py --output artifacts/cycle-9-cash-repeat/calibration.json
uv run python evaluate.py --agent artifacts/cycle-9-cash-repeat/main.py --opponents baselines/cycle_3.py baselines/step_8.py opponents/scaled_mixed.py --seeds 17 43 9310 --workers 2 --replays all --output artifacts/cycle-9-cash-repeat/development
```

The committed reports preserve evaluated hashes, costs, outcomes and first changed decisions. Raw server inputs stay in Downloads; local complete replays/audits stay under `artifacts`. The auditor now handles empty market orders accepted by the engine, with a regression test. All 214 tests pass, including source-isolation, stock/labor conservation, final-day behavior, hire-window and setup feasibility checks. Lint and formatting checks pass.
