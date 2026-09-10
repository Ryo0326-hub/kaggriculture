# Step 4: livestock investment and a broader evaluation pool

Implemented September 9, 2026 (Toronto time). Promote this as the next locally validated candidate. It uses cows, sheep, fertilizer sales, feed liquidity, and marginal whole-herd economics. The source and controls were frozen before fresh validation; no strategy changes followed the validation results. [CO implementation notes](STEP_4_OPTIMIZATION.md).

## Why the strategy changed

Step 3 passed server self-play validation in episode `107286447`, with 15,355 coins per farm, both `DONE`, no stderr, and exact local reproduction of actions and economic state. Its displayed initial rating of 600 was a skill rating. A subsequent CLI snapshot showed Step 3 at 436.8 and Step 2 at 366.7; these are historical snapshots, not current ratings.

Two actual Step 3 ladder losses were then downloaded and inspected. In episode `107287517`, our 21,902 coins lost to 91,625; in `107288503`, our 20,940 lost to 123,336. The rivals used livestock, fertilizer, premium crops, and land. Every recorded action from our bot matches the frozen Step 3 source. This showed that improving a crop-only forecast was too narrow as the main next step. [Ladder audit](benchmarks/step-4-ladder-audit.json).

Those replay files contain recorded trajectories, not rival source code. We do not use their fixed actions as reactive opponents or claim the new candidate has beaten those rivals. The local controls below are our own implementations.

## Candidate results

| Set | Opponent | Games | W / D / L / errors | Mean candidate cash | Mean margin |
| --- | --- | ---: | --- | ---: | ---: |
| Development | Frozen Step 3 | 6 | 6 / 0 / 0 / 0 | 76,575.17 | +54,826.83 |
| Development | Step 3 without supply buffer | 6 | 6 / 0 / 0 / 0 | 76,099.67 | +54,208.67 |
| Development | Cow-only control | 6 | 6 / 0 / 0 / 0 | 55,949.83 | +20,629.83 |
| Development | Sheep-only control | 6 | 6 / 0 / 0 / 0 | 59,010.67 | +19,627.33 |
| Development | Six-animal portfolio control | 6 | 6 / 0 / 0 / 0 | 57,006.50 | +18,099.50 |
| Fresh validation | Frozen Step 3 | 20 | 20 / 0 / 0 / 0 | 75,429.55 | +53,967.85 |
| Fresh validation | Step 3 without supply buffer | 20 | 20 / 0 / 0 / 0 | 76,140.45 | +54,559.95 |
| Fresh validation | Cow-only control | 20 | 17 / 0 / 3 / 0 | 45,560.35 | +13,014.05 |
| Fresh validation | Sheep-only control | 20 | 20 / 0 / 0 / 0 | 61,258.15 | +29,015.95 |
| Fresh validation | Six-animal portfolio control | 20 | 18 / 2 / 0 / 0 | 46,699.80 | +13,867.65 |

Development used `17, 43, 83`. Fresh validation used `2003, 2017, 2027, 2053, 2081, 2099, 2111, 2131, 2153, 2179`. Every seed ran in both player positions against each opponent. The fresh result is **95 wins, 2 draws, 3 losses, no errors**, a match score of 0.96 for this equally weighted internal pool. These are ten seed blocks, not 100 independent observations. The used seeds are no longer an untouched selection set.

The cow-only control won both positions at seed 2003 by 3,589 coins and one position at seed 2099 by 1,008. The six-animal control tied both positions at seed 2111. The mixed portfolio is therefore not universally stronger than a specialized or smaller herd. The lowest candidate cash in the fresh pool was 14,095, illustrating substantial demand sensitivity despite the favorable average.

The livestock controls share station operations and the investment model. They isolate allowed species or the herd cap within this implementation, not the superiority of all possible portfolio or staffing algorithms. Changing from Step 3 to Step 4 bundles a different production system, feed purchases, capital decisions, and worker routes; the entire gain cannot be attributed to the marginal-value formula alone.

## Matched comparison with the previous candidate

Step 3 also played the same 100 fresh seed/seat/opponent combinations, with identical environment, configuration, runner, and dependency hashes. It finished **18 wins, 10 draws, 72 losses**, for a match score of **0.23**, compared with Step 4's **0.96**.

| Opponent | Step 3 match score | Step 4 match score |
| --- | ---: | ---: |
| Frozen Step 3 | 0.50 | 1.00 |
| Crop policy without buffer | 0.40 | 1.00 |
| Cow-only | 0.10 | 0.85 |
| Sheep-only | 0.15 | 1.00 |
| Six-animal portfolio | 0.00 | 0.95 |

The mean paired improvement is 0.73. Resampling the ten whole seed blocks 10,000 times gives a 95% percentile interval of approximately **[0.62, 0.82]** for this pool's match-score difference. Seats and opponents remain together within each resampled seed. This interval does not cover unseen opponent classes, model-selection bias, or leaderboard uncertainty. The pool is still small and internally constructed.

`compare_results.py` rejects incomplete/duplicate games, error outcomes, and mismatched simulation settings before calculating the comparison. It preserves the full seed-level differences in [the evidence package](benchmarks/step-4.json). No policy was changed in response to these fresh results.

## Costs, reliability, and model limits

Against the six-animal control, the candidate spent 1,549.80 coins on hire orders versus 326.00, and 4,220.00 on animals versus 2,710.00. It still finished 13,867.65 coins ahead on average. This supports the extra capacity under the tested demand regimes; it does not prove that ten animals or one worker per animal is optimal.

About 49–52% of candidate worker commands were `PASS`, depending on opponent. The station policy buys operational reliability with idle capacity. Combining stations into shared-worker routes or using idle time for crops is a clear next experiment, provided feeding, collections, and final liquidation remain reliable.

All 130 final candidate development/validation games completed 720 states, with the last action based on step 718. Across those games, the candidate had zero escapes, zero unfed animal-days, no duplicate target operations, no leftover seeds, and zero unsold shed or carried inventory. Live animals remain on the farm without assigned salvage value. Order-cost and harvest-command metrics are diagnostics; official engine cash and state remain authoritative.

The maximum fresh decision time was **79.723 ms**, and the largest per-game p99 was **7.885 ms**, below the configured one-second action limit. Concurrent local evaluation can affect timings; these are not a server-hardware guarantee.

The full existing suite passed 60 tests, followed by two new common-pool comparison tests. Ruff lint and formatting checks passed. New engine-backed tests cover care-bonus timing, first production, fertilizer demand, purchase liquidity, incomplete installations, scarce-product response, shared stock, feeding, care, escapes, terminal liquidation, and actual control loading. Historical crop/assignment tests now explicitly use their frozen sources. GitHub CI runs the complete 62-test suite on the pushed commit.

The first four-game smoke probe used an earlier output projection. Subsequent engine tests corrected the timing of the observed care bonus before the 30-game development run and all fresh games. That smoke probe is exploratory only and is not added to the final benchmark sample.

## Exact submission artifact

Prepared file: `artifacts/submission-step-4/main.py`, **18,833 bytes**, SHA-256:

```text
0024dc48be607636775eba055eea8bde54d3c0679e5e851439791b5d6cb741f9
```

The copied file passed isolated official-loader self-play at seed 505: both players `DONE`, 720 states, 65,088 coins each, no error statuses or agent stderr, no unsold inventory or leftover seeds. Maximum recorded decision time was 8.812 ms. It uses only the standard library and requires no repository imports.

**Step 4 has not been uploaded to Kaggle.** Source pushes, local matches, and isolated self-play do not certify server execution or a leaderboard rating. An upload would move the latest-two window from Steps 2/3 to Steps 3/4. [Submission registry](SUBMISSIONS.md).

## Reproduce

Generate the controls with [the README commands](../README.md), then use unused output paths:

```bash
uv run python evaluate.py --seeds 2003 2017 2027 2053 2081 2099 2111 2131 2153 2179 \
  --opponents baselines/step_3.py artifacts/controls/crop-no-buffer.py \
    artifacts/controls/cows.py artifacts/controls/sheep.py artifacts/controls/six.py \
  --output artifacts/step-4-rerun
uv run python evaluate.py --agent baselines/step_3.py \
  --seeds 2003 2017 2027 2053 2081 2099 2111 2131 2153 2179 \
  --opponents baselines/step_3.py artifacts/controls/crop-no-buffer.py \
    artifacts/controls/cows.py artifacts/controls/sheep.py artifacts/controls/six.py \
  --output artifacts/step-4-reference-rerun
uv run python compare_results.py --candidate artifacts/step-4-rerun \
  --reference artifacts/step-4-reference-rerun --output artifacts/step-4-paired-rerun.json
uv run python prepare_submission.py --output artifacts/submission-step-4-rerun
```

Control filenames affect display IDs; their contents must match the recorded hashes. Rerunning deterministic matches does not add independent evidence. [The evidence package](benchmarks/step-4.json) contains manifests, match records, summaries, diagnostics, comparison, and release validation. Raw replays remain in ignored local artifacts; downloaded ladder replays are losslessly gzip-compressed. [The saved decision](examples/step-4-decision.json) shows the actual initial investment alternatives.
