# Step 6 results: bounded mixed production

Implemented and locally validated September 10, 2026. **Subsequently uploaded as submission 56149269 and server validated in episode 107547593.** [The server audit](STEP_6_SERVER_AND_LEADER_ANALYSIS.md) records that later evidence and the resulting strategy revision. The local candidate won 251 of 300 fresh validation games. Against the same five-opponent pool, frozen Step 5 won 60, drew 60, and lost 180. The new policy still lost 49 of 60 games against the melon specialist, so crop sequencing remains a substantial weakness.

[CO and economics implementation notes](STEP_6_OPTIMIZATION.md) · [awarse replay analysis](STEP_5_SERVER_ANALYSIS.md) · [Machine-readable evidence](benchmarks/step-6.json) · [Frozen protocol](benchmarks/step-6-protocol.json).

## Change and hypothesis

Step 5's awarse loss exposed productive capacity left unused and dependence on a shared livestock market. Step 6 adds at most eight nearby crop plots alongside the existing herd. It evaluates wheat, melon, and strawberry commitments using dated receipts, seed prices, estimated extra wages, and a work allowance. It protects watering and harvest deadlines, supports the crop workload with early hires, values fertilizer against selling it, and accounts for homegrown feed in the shared inventory balance.

The hypothesis is that a bounded crop portfolio improves the probability of winning without sacrificing reliable livestock service or terminal liquidation. No new land purchase or learned policy is included. The livestock core is preserved in `baselines/step_5.py`, and remains callable as `main.plan_turn`; the submitted entry point now calls `mixed_turn`.

## Frozen common-pool comparison

Each policy played **30 fresh seeds × two seats × five opponents = 300 games**. The comparison therefore contains 600 games, grouped into 30 seed blocks. Both runs used four CPU processes, the same opponents and configuration, and `kaggle-environments==1.32.7`. The source and control hashes were frozen before these seeds were run. No policy tuning followed inspection of their results.

Match score is `(wins + 0.5 × draws) / games`. These percentages are local pool results, not Kaggle skill ratings.

| Opponent | Step 6 W–D–L | Step 6 score | Step 5 reference score | Step 6 mean cash margin |
| --- | ---: | ---: | ---: | ---: |
| Frozen Step 5 | 60–0–0 | 100% | 50% | +17,575.40 |
| Frozen Step 3 | 60–0–0 | 100% | 100% | +74,721.62 |
| Strawberry crop control | 60–0–0 | 100% | 0% | +8,904.70 |
| Melon crop control | 11–0–49 | 18.33% | 0% | −1,241.23 |
| Wheat crop control | 60–0–0 | 100% | 0% | +13,191.08 |
| **Overall** | **251–0–49** | **83.67%** | **30%** | **+22,630.31** |

The paired match-score improvement is **53.67 percentage points**. Resampling whole seed blocks 10,000 times gives a 95% percentile interval of **[51.33, 56.67] percentage points**. Every opponent score improved or stayed unchanged relative to Step 5. The interval describes this particular pool; it does not account for unseen rival classes or establish medal strength.

The three crop controls retain the same livestock core, crop dispatcher, and eight-plot bound, while restricting the crop menu. They react to the simulation and are more informative than replaying a rival's fixed commands. They are also related policies, so this is not a broad independent sample of competition strategies. None is the actual code of awarse, Otter Vibe, or SpaTaro.

## Reliability and release gates

Across all 300 candidate validation games:

- All episodes completed with 720 recorded states and no execution errors.
- Zero recorded crop losses, including zero exhausted-plant expirations; 6,615 `PLANT` actions were recorded.
- Zero missed animal feeding, escaped animals, seed overrequests, or duplicate crop targets.
- Zero final saleable shed stock, carried stock, or unused seeds.
- Maximum observed candidate decision time: **0.140064 seconds** under concurrent local evaluation.

These checks satisfy the frozen operational gates, positive paired-score interval, and per-opponent regression gate. They are empirical checks on the evaluated games, not guarantees for every possible state. Detailed action preconditions and shared inventory balances are checked in the full-season tests.

**90 tests passed** on the final frozen source. The tests include independent official-engine crop schedules, dated staffing cost, input opportunity costs, source purity, newborn watering reservations, late fertilizer/water regressions, crop-expiration accounting, and two complete mixed-farm resource-contract games. Ruff lint, formatting, and `git diff --check` passed. Existing livestock-only episode tests use the frozen Step 5 file; the mixed policy has its own full-season checks.

The isolated release checks the copied file through Kaggle's official agent loader, in a fresh process without repository imports:

| Release property | Result |
| --- | --- |
| File | `artifacts/submission-step-6/main.py` |
| SHA-256 | `d545236b1045fa522676931380ba68517eb2d359252783ea997156bb0f6f13ac` |
| Size | 57,438 bytes |
| Self-play seed | 505 |
| Statuses | `DONE`, `DONE` |
| Recorded states | 720 |
| Final cash | 43,994 each |
| Errors / stderr | None |
| Final stock / unused seeds | Zero for both seats |
| Maximum observed decision time | 0.062506 seconds |

The self-play cash is a packaging observation. It is not directly comparable to Step 5 playing a different policy, because both agents affect market prices and can encounter different shop draws. Local timing also cannot certify Kaggle's server runtime. The subsequent server validation passed at **63,524 per farm**, with no stderr and every action matching this source; see the linked server audit. The benchmark JSON preserves the original pre-upload local release status as historical evidence.

## What the remaining losses teach us

Against the melon control, our mean harvest includes **71.88 melons and 50.80 wheat**, versus **87.40 melons** for the control. We pay **1,415.73** in average hire orders versus **1,218.93**. Our mean deficit is 1,241.23; the worst deficit is 6,336. These differences identify an allocation and timing hypothesis, not proof that wheat is always inferior.

The [saved source-matched decision](examples/step-6-decision.json) makes the gap concrete. With 455 cash and a 405 reserve, a ten-coin wheat seed is feasible; an 80-coin melon seed is not. The wheat forecast has 57 marginal coins after modeled costs. The agent buys wheat without comparing that action against waiting to afford the much more valuable melon alternative. Its per-tile-day ranking also does not optimize a sequence of crops through the remaining season.

The next checkpoint should compare **plant now, wait, and short crop sequences** with dated cash and worker constraints. A small finite-horizon integer model or enumerated schedule can evaluate those alternatives. Investigate the melon loss class on development seeds, then use an entirely new validation set. Larger land purchases should follow evidence that additional productive schedules repay the land, setup, staffing, and logistics costs.

## Fertilizer ablation and development history

A separate six-game check on seeds 6007, 6011, and 6029, in both seats, compares the final candidate with the same policy's fertilizer application disabled. It finishes **4 wins, 2 draws, 0 losses**, with a mean margin of **109.67 coins**. Margins by seed are 0, 104, and 225 in both seats. This is modest, small-sample support for the feature; it does not establish fertilizer as the primary reason for the pool improvement.

Development versions initially won against Step 5 while still losing crops. Those versions were rejected as releases. Diagnostics led to planting-day watering reservations, nearby-worker priority, bounded routes, early supporting hires, and ripe-crop scheduling that preserves time for livestock duties. The v9 development source had no crop losses in 16 direct games; the final source additionally preserves the original livestock command if an urgent crop reservation fails. Earlier hashes, summaries, raw crop-loss counts, and the smaller development pool remain in the evidence JSON. Missing diagnostics from older runner versions are marked null. These results guided implementation and are not independent validation.

## Reproduction

Run these commands from the repository at the Step 6 source hash above. Use new output directories when repeating an experiment; the tools deliberately refuse to overwrite prior runs. The controls below retain livestock and only restrict the crop menu.

```bash
uv sync --locked
uv run python scripts/make_mixed_control.py --crops STRAWBERRY --output artifacts/step-6-controls/strawberries.py
uv run python scripts/make_mixed_control.py --crops MELON --output artifacts/step-6-controls/melons.py
uv run python scripts/make_mixed_control.py --crops WHEAT --output artifacts/step-6-controls/wheat.py

STEP6_SEEDS=(5003 5009 5011 5021 5023 5039 5051 5059 5077 5081 5087 5099 5101 5107 5113 5119 5147 5153 5167 5171 5179 5189 5197 5209 5227 5231 5233 5237 5261 5273)
STEP6_OPPONENTS=(baselines/step_5.py baselines/step_3.py artifacts/step-6-controls/strawberries.py artifacts/step-6-controls/melons.py artifacts/step-6-controls/wheat.py)

uv run python evaluate.py --candidate main.py --seeds "${STEP6_SEEDS[@]}" \
  --opponents "${STEP6_OPPONENTS[@]}" --workers 4 --replays first \
  --output artifacts/step-6-validation
uv run python evaluate.py --candidate baselines/step_5.py --seeds "${STEP6_SEEDS[@]}" \
  --opponents "${STEP6_OPPONENTS[@]}" --workers 4 --replays first \
  --output artifacts/step-6-reference
uv run python compare_results.py --candidate artifacts/step-6-validation \
  --reference artifacts/step-6-reference --output artifacts/step-6-paired.json

uv run python scripts/make_mixed_control.py --no-fertilizer --output artifacts/step-6-controls/no-fertilizer.py
uv run python evaluate.py --candidate main.py --seeds 6007 6011 6029 \
  --opponents artifacts/step-6-controls/no-fertilizer.py --workers 2 --replays first \
  --output artifacts/step-6-fertilizer-validation
uv run python explain_turn.py --replay artifacts/step-6-validation/replay-0001.json \
  --state 52 --player 0
uv run pytest -q
uv run ruff check .
uv run ruff format --check .
uv run python prepare_submission.py --output artifacts/submission-step-6
```

Array syntax above works in Bash and Zsh. Artifacts and raw replays remain local; committed benchmark evidence contains manifests, hashes, per-game metrics, the paired comparison, development summaries, and the isolated release result.
