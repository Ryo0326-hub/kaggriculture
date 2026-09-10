# Step 5 results: shared livestock routes

September 10, 2026. **Promoted locally; Kaggle upload and server validation are pending.** The candidate improves the paired internal-pool score while preserving output and reducing wages in the controlled installed-herd experiment. [CO model and implementation notes](STEP_5_OPTIMIZATION.md) · [Machine-readable evidence](benchmarks/step-5.json).

## Candidate and experiment boundary

| Artifact | SHA-256 |
| --- | --- |
| Step 5 `main.py` | `70fa2f8a16316bb51fc2ce9eb01b08259fdb83c256359ffc29e847dd459d5816` |
| Frozen `baselines/step_4.py` | `0024dc48be607636775eba055eea8bde54d3c0679e5e851439791b5d6cb741f9` |

Only staffing and execution change. Investment functions and the station executor are preserved textually, checked by tests. Different available cash and transaction timing can still change subsequent investments in ordinary games. Shared routes are bounded to four animals; the herd remains capped at ten nearby cows/sheep. Installation and already-paid full station crews use the original executor. Scheduled production sites receive individual routes.

The final source was frozen before evaluating the 30 validation seeds. The [recorded protocol](benchmarks/step-5-protocol.json) required no errors or escapes, empty final saleable inventory, preserved controlled-herd output, and a positive paired improvement with its whole-seed 95% bootstrap interval above zero. Opponent-score regressions beyond five percentage points required investigation. No candidate code changed after these results were inspected.

## Normal-start comparison

Each policy played **240 complete games**: 30 fresh seeds × both seats × four frozen opponents. Both used the same pinned engine, runner, configuration, and four CPU processes per run. Score is `(wins + 0.5 × draws) / games`; it is not a Kaggle rating.

| Opponent | Step 5 W/D/L | Step 5 score | Step 4 W/D/L | Step 4 score | Change |
| --- | --- | --- | --- | --- | --- |
| Frozen Step 4 | 49 / 0 / 11 | 81.67% | 1 / 58 / 1 | 50.00% | +31.67 pp |
| Step 4, cows only | 56 / 0 / 4 | 93.33% | 53 / 0 / 7 | 88.33% | +5.00 pp |
| Step 4, sheep only | 50 / 0 / 10 | 83.33% | 50 / 0 / 10 | 83.33% | 0.00 pp |
| Step 4, six animals | 56 / 0 / 4 | 93.33% | 54 / 6 / 0 | 95.00% | −1.67 pp |
| **Overall** | **211 / 0 / 29** | **87.92%** | **158 / 64 / 18** | **79.17%** | **+8.75 pp** |

The paired whole-seed bootstrap interval is **+5.00 to +11.67 percentage points**, using 10,000 resamples of 30 seed blocks. Seats and opponents stay together within each resampled block; the 480 games are not treated as 480 independent random samples.

Every game ended with both agents `DONE`. Neither policy run had reported execution failures, missed feeding, animal escapes, or final unsold candidate stock in the shed or carried inventory. The candidate's maximum observed decision time was **0.211069 seconds** under concurrent local evaluation. These timings depend on the machine and load.

The candidate's mean cash was 51,082.50 versus the reference's 49,767.00 in their separate common-pool runs. Against Step 4 directly, its mean cash margin was only **+648.47**, with a worst result of **−5,056**. Those 11 direct losses remain real limitations. The six-animal control also shows a small score regression, below the protocol's five-point investigation threshold. The policy was not retuned on those seeds.

Most of the overall score gain comes from replacing draws against the old policy with wins. The three controls share that policy's architecture. This pool supports an incremental improvement over Step 4; it does not establish robustness to crop-heavy opponents, Otter Vibe, SpaTaro, or medal-level play. Mean cash and the bootstrap interval do not remove that opponent-selection limitation.

## Installed-herd experiment: isolate labor economics

Twelve additional games use seeds 4001 and 4021, both seats, and three ten-animal herd configurations. Both farms start with the same installed assets, **15,000 cash and 20 wheat**, and new purchases are disabled. This is a controlled operations experiment, not a normal-start competition score.

| Herd | Station wages | Shared-route wages | Saving | Output per farm, identical | Shared-route cash advantage |
| --- | --- | --- | --- | --- | --- |
| Ten cows | 2,640 | 1,096 | 1,544 (58.5%) | 360 milk + 290 fertilizer | +1,279 to +1,301 |
| Ten sheep | 2,640 | 848 | 1,792 (67.9%) | 340 wool + 290 fertilizer | +1,495 to +1,517 |
| Five cows / five sheep | 2,640 | 773 | 1,867 (70.7%) | 180 milk + 170 wool + 290 fertilizer | +1,144 to +1,192 |

Wages count observed successful hires. All twelve cases preserve harvested/collected quantities, complete required feeding and care, avoid escapes, and finish with no unsold units. Shared workers service multiple animals on 75 cow-herd, 86 sheep-herd, and 81 mixed-herd worker-days per game. The station control has zero such worker-days.

Final cash gains are smaller than wage savings because sales and feed purchases occur at different times in a shared market. Preserving quantities does not guarantee identical receipts or optimal delivery times.

## Development evidence and the rejected alternative

The first wage-minimizing version reduced installed-herd wages to 200 from 2,640 and preserved quantities, but lost **2,407 to 25,132 coins** in twelve development cases. Delayed selling outweighed the wage saving. Its ordinary development pool went 33–7 overall but only 2–6 against Step 4. Aggregate wins alone would have hidden that regression.

The corrected version protects scheduled product deliveries and retains the original installation sequence. Before the final freeze, it went 12–2 against Step 4 across seven development seeds and passed twelve installed-herd cases. Those development results guided the design and are not independent validation. The final normal-start seeds and the 4001/4021 controlled-herd seeds were used only after that freeze. The evidence file preserves the rejected and corrected development hashes separately.

## Release and checks

- 76 tests pass across the full-suite run and the subsequent concurrency-comparison addition. Coverage includes the independent partition/permutation oracle, unchanged investment/executor checks, shared inventories, production protection, both-seat full seasons, and serial/parallel evaluation consistency.
- Ruff lint, formatting, and whitespace checks pass.
- `artifacts/submission-step-5/main.py` is an exact **30,864-byte** copy of the frozen candidate. Isolated official-loader self-play, seed 505, reaches 720 states with both agents `DONE`, 66,115 cash each, no stderr/failures, and no final saleable inventory. Maximum observed decision time: **0.018236 seconds**.
- The release needs only this single standard-library Python file. It was validated in a separate process without repository imports. It has **not been uploaded to Kaggle**; local validation cannot certify server execution or rating.

[The explained decision](examples/step-5-decision.json) is reconstructed from candidate validation seed 3001, seat 0, state 72. Source and action both match. On zero-based day 3, hour 0, it covers five animals with two routes, budgeted at 20 and 16 actions, and targets one hired hand. The accompanying notes show the integer model behind that choice.

## Reproduce

From the repository root, use new output paths if the originals already exist:

```bash
uv sync --locked
uv run python scripts/make_livestock_control.py --source baselines/step_4.py \
  --animal COW --output artifacts/step-5-controls/cows.py
uv run python scripts/make_livestock_control.py --source baselines/step_4.py \
  --animal SHEEP --output artifacts/step-5-controls/sheep.py
uv run python scripts/make_livestock_control.py --source baselines/step_4.py \
  --herd-limit 6 --output artifacts/step-5-controls/six.py

uv run python evaluate.py --agent main.py --workers 4 \
  --seeds 3001 3011 3019 3023 3037 3041 3049 3061 3067 3079 \
    3083 3089 3109 3119 3121 3137 3163 3167 3169 3181 \
    3187 3191 3203 3209 3217 3221 3229 3251 3253 3257 \
  --opponents baselines/step_4.py artifacts/step-5-controls/cows.py \
    artifacts/step-5-controls/sheep.py artifacts/step-5-controls/six.py \
  --output artifacts/step-5-validation

uv run python evaluate.py --agent baselines/step_4.py --workers 4 \
  --seeds 3001 3011 3019 3023 3037 3041 3049 3061 3067 3079 \
    3083 3089 3109 3119 3121 3137 3163 3167 3169 3181 \
    3187 3191 3203 3209 3217 3221 3229 3251 3253 3257 \
  --opponents baselines/step_4.py artifacts/step-5-controls/cows.py \
    artifacts/step-5-controls/sheep.py artifacts/step-5-controls/six.py \
  --output artifacts/step-5-reference

uv run python compare_results.py --candidate artifacts/step-5-validation \
  --reference artifacts/step-5-reference --output artifacts/step-5-paired.json
uv run python -m scripts.benchmark_routes --seeds 4001 4021 \
  --output artifacts/step-5-fixed-herd-validation.json
uv run python explain_turn.py --replay artifacts/step-5-validation/replay-0001.json \
  --state 72 --player 0
uv run python prepare_submission.py --output artifacts/submission-step-5
```

Next checkpoint: mixed crop schedules and fertilizer/feed opportunity costs integrated with the shared executor. Keep Step 5 as the reference, use new validation seeds for later decisions, and add independent opponent classes before making stronger competitive claims.
