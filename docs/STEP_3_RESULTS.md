# Step 3: production and hiring economics

Completed locally on September 9, 2026. The agent now chooses wheat/carrot production lots and up to six hired hands using seed costs, cash, estimated labor, observed demand, sale price impact, and remaining growing time. [The CO implementation notes](STEP_3_OPTIMIZATION.md) explain its integer model, marginal hiring comparisons, LP relaxation, and approximation limits.

Historical checkpoint: this source is now frozen in `baselines/step_3.py`; active `main.py` is Step 4. Step 3 subsequently passed server validation as submission `56132659`, episode `107286447`, with 15,355 coins per farm and no stderr. [Server audit](benchmarks/step-3-server.json). The decisions below describe the original local checkpoint, before that upload.

**Decision:** retain this as the implemented research checkpoint and a locally valid candidate that improves on Step 2 in the tested matches. The supply buffer is not established as an improvement: the matched control without it wins most fresh head-to-head games. Compare both forecast variants against the same broader opponent pool before selecting the next ladder candidate. No Step 3 file has been uploaded to Kaggle.

## Results and controlled comparisons

| Set | Opponent | Games | W / D / L / errors | Mean candidate cash | Mean cash margin |
| --- | --- | ---: | --- | ---: | ---: |
| Development | Frozen Step 2 | 10 | 10 / 0 / 0 / 0 | 15,771.60 | +2,534.20 |
| Development | Matched four-hand control | 10 | 10 / 0 / 0 / 0 | 16,080.20 | +1,566.00 |
| Development | Matched wheat-only control | 10 | 10 / 0 / 0 / 0 | 16,199.60 | +2,548.00 |
| Development | Matched no-buffer control | 10 | 6 / 0 / 4 / 0 | 14,090.80 | −75.80 |
| Fresh validation | Frozen Step 2 | 20 | 20 / 0 / 0 / 0 | 18,258.70 | +4,876.70 |
| Fresh validation | Matched four-hand control | 20 | 20 / 0 / 0 / 0 | 16,131.90 | +1,227.15 |
| Fresh validation | Matched wheat-only control | 20 | 20 / 0 / 0 / 0 | 18,423.85 | +4,769.35 |
| Fresh validation | Matched no-buffer control | 20 | 4 / 0 / 16 / 0 | 14,274.45 | −617.65 |

Development used seeds `11, 29, 47, 71, 97`. Fresh validation used `1009, 1031, 1061, 1091, 1151, 1201, 1237, 1277, 1301, 1361`. Every seed was played in both positions against all four opponents. The candidate and controls were frozen before the fresh run; neither was adjusted after seeing these results. These validation seeds are now used and cannot serve as an untouched final selection set.

The fresh set contains **ten seed blocks**, not 80 independent observations. Its 64/80 wins describe this equally weighted internal pool, not leaderboard win probability or medal strength. None of the opponents raises livestock, buys land, or uses a substantially different production system. The planned final evaluation should be larger and more varied.

The controls are generated from the exact candidate source, changing only their entry-point flags:

- **Four-hand:** staffing stays at the affordable four-hand cap on productive days; the rest of the production and execution policy is shared. This isolates that staffing policy choice within this model, not the benefit of every possible labor optimizer.
- **Wheat-only:** excludes carrot production while retaining economic hiring, the supply buffer, and endgame handling.
- **No-buffer:** retains observed inventory, standing crops, average shop demand, and per-unit price impact, but removes the extra hypothetical field of supply. It is called `optimistic-v5.py` in the recorded manifests; it does not simply use today's quoted price.

The Step 2 comparison bundles crop diversification, staffing, economic planning, endgame production, and mixed-inventory execution changes. It cannot attribute the total gain to any one component.

## What the cost and production audit explains

Against the four-hand control, the candidate spends an average **359.35 coins on hire orders**, compared with 210.00. It also spends 205.00 more on seed orders. Despite those added costs, it finishes **1,227.15 coins ahead** on average. Recorded wheat/carrot harvest units average 397.50/210.30 versus 364.15/195.90, and the mean share of worker commands that are `PASS` falls from 18.91% to 15.09%. This supports additional labor under the tested workloads; it does not imply every farm should always hire six hands.

Against the no-buffer control, the candidate's recorded production shifts to about **578 wheat and 35 carrot units**, while the control produces about **230 wheat and 357 carrot units**. The conservative candidate spends less on both hiring and seeds but still loses most matches. A plausible interpretation is that the extra supply assumption suppresses valuable carrot production in this matchup. That is a diagnosis to test with realized price and forecast errors, not proof of an optimal replacement forecast.

`evaluate.py` records costs of requested hire/seed orders and units attached to harvest commands. These are diagnostics, not an independent accounting ledger: the official engine's final cash remains authoritative. Full-season action tests separately verify that this agent's spending and resource requests are feasible.

All 120 final development/validation games completed 720 recorded states without agent errors. The candidate had zero unsold shed or carried produce in every game. Unused seeds remained in 31/40 development games, at most five, and 49/80 validation games, at most eight. This metric does not count standing plants; it does not establish that every seed investment paid back.

Across the 80 fresh games, the candidate's audit found zero seed overrequests, duplicate crop targets, or crops turning into weeds. The maximum decision time was **79.687 ms**, and the largest per-game p99 was **21.588 ms**, versus the configured one-second action limit. Local hardware timings do not guarantee server timings.

## Experiments that shaped this checkpoint

Earlier screens tried production models with a four-hand cap and stricter crop completion cutoffs. Saving labor and delaying production lost to Step 2. Raising the cap to six made those development comparisons favorable, but an early price forecast still lost to its wheat-only control. The final candidate combines a supply stress scenario with shorter, reduced-yield endgame crops. It beats the matched wheat-only control, while its loss to the no-buffer control remains unresolved.

Those exploratory screens reused development seeds; they are not additional independent confirmation. Their manifests and summaries are retained in [the evidence package](benchmarks/step-3.json). Reproducible raw replays from discarded screens were removed when local storage filled; final benchmark summaries, records, diagnostic replay, and release files were retained.

The fresh run also encountered a local disk-space failure after 30 complete records. After freeing generated scratch data, the remaining 50 planned games ran with verified identical candidate, control, runner, lock, and environment hashes. The final set has exactly 80 unique `(seed, seat, opponent)` records. This interruption was an output-storage failure, not an agent failure or a reason to replace an unfavorable result.

## Validity and artifact

- `uv run pytest -q`: **50 passed**.
- `uv run ruff check .` and `uv run ruff format --check .`: passed.
- Scenario tests check exact engine sale pricing, a hand-computed constrained integer allocation, observed shop demand, labor/cost sensitivity, cash constraints, and finite-horizon crop yields.
- Full-season tests check both player positions, self-play, shared seeds, legal crop operations, deposit capacity, funded market orders, maintenance, and final produce liquidation.
- The frozen Step 2 tests remain against `baselines/step_2.py`; they do not silently change their historical assumptions to fit the new policy.

The exact prepared release is `artifacts/submission-step-3/main.py`, **18,585 bytes**, SHA-256:

```text
ddd775729432e51be0ecf4462866ca4c75673fb1b55a0b12c0395c40d0a5114a
```

It passed isolated official-loader self-play at seed 505 with the repository excluded from imports: both players `DONE`, 720 states, no error statuses or agent stderr, no unsold produce, and one unused seed per player. Terminal cash was 15,268 and 15,403; maximum decision time was 36.854 ms. The submitted policy uses only the standard library and makes no network calls.

Step 2 separately passed Kaggle server validation in episode `107272004`; its initial displayed rating of **600 is a skill rating, not farm profit**. The supplied logs contain no agent stderr, and the replay matches a local resimulation for every action and economic state. [Server audit](benchmarks/step-2-server.json) and [submission registry](SUBMISSIONS.md).

## Reproduce and continue

The economics generator now defaults to `baselines/step_3.py`. Generate `fixed-four.py`, `wheat-only.py`, and `no-buffer.py` with `--fixed-hands`, `--wheat-only`, and `--optimistic-prices` respectively. To rerun the fresh comparison using new output paths:

```bash
uv run python evaluate.py --agent baselines/step_3.py --seeds 1009 1031 1061 1091 1151 1201 1237 1277 1301 1361 \
  --opponents baselines/step_2.py artifacts/controls/fixed-four.py \
    artifacts/controls/wheat-only.py artifacts/controls/no-buffer.py \
  --output artifacts/economics-validation-rerun
uv run python prepare_submission.py --source baselines/step_3.py --output artifacts/submission-step-3-rerun
```

Renaming a control changes its display ID, but its source hash must match the corresponding recorded control. Repeated deterministic games do not add independent evidence. The evidence package contains full match records, source/environment hashes, configuration, summaries, cost metrics, and the isolated release report. Raw replays and local releases remain under ignored `artifacts/` directories. [The saved decision](examples/step-3-decision.json) illustrates the actual marginal hire calculation.

Next, compare forecast variants against the same broader opponent pool, inspect prediction errors and unused seeds, and test workload estimates. Keep the current source frozen while screening a new hypothesis. The six-hand limit, fixed extra-field supply assumption, average shop demand, and blended service/production objective are modeling choices to improve through experiments; none is a proven optimum for the full game.

Subsequent implementation: [Step 4](STEP_4_RESULTS.md) used actual ladder losses to prioritize livestock capital economics. For historical replay explanations, use a separate checkout of commit `3637b04`; the command deliberately rejects a replay whose hash differs from current source.
