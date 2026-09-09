# Step 2: coordinated-worker candidate

Completed locally on September 9, 2026. The current `main.py` coordinates the farmer and up to four hands on the starting quadrant, with a bounded exact assignment solver inside a heuristic wheat policy. It has been prepared and validated as a self-contained Python file. No Kaggle upload or server validation has been performed.

## Decision and evidence

Promote Step 2 as the local development candidate. It beat the frozen Step 1 agent and a matched greedy assignment control on the tested development and fresh-validation seeds. [The CO implementation notes](STEP_2_OPTIMIZATION.md) explain exactly what the solver optimizes and what remains heuristic.

| Set | Opponent | Games | W / D / L / errors | Mean candidate cash | Mean cash margin |
| --- | --- | ---: | --- | ---: | ---: |
| Development | Frozen Step 1 | 10 | 10 / 0 / 0 / 0 | 13,957.10 | +8,831.50 |
| Development | Matched greedy assignment | 10 | 10 / 0 / 0 / 0 | 13,384.70 | +653.50 |
| Fresh validation | Frozen Step 1 | 20 | 20 / 0 / 0 / 0 | 13,843.30 | +8,735.40 |
| Fresh validation | Matched greedy assignment | 20 | 20 / 0 / 0 / 0 | 13,421.60 | +650.35 |

Development seeds: `11, 29, 47, 71, 97`. Fresh validation seeds, chosen before that run: `101, 137, 173, 211, 257, 293, 337, 379, 419, 463`. Every seed runs in both player positions. The candidate was frozen before validation and was not tuned on its results. These seeds have now been used; future final selection needs a new untouched set.

The 40 validation games represent ten seed blocks, not 40 independent samples. Both opponents are internal wheat policies. This is useful evidence for the implementation checkpoint, not an estimate of leaderboard win rate or medal probability. The large improvement over Step 1 combines additional labor, more land in use, and changed scheduling. The matched control isolates the assignment algorithm at the same scale, and supports retaining it in this policy. It does not prove exact assignment dominates greedy for every task-scoring policy.

All 60 reported benchmark games completed 720 recorded states, with the final action based on step 718. The candidate ended every one with zero carried produce and zero shed stock. Three development games retained seeds (at most two); four validation games retained seeds (at most three). Seed lot sizing therefore remains an economic improvement for Step 3. The minimum candidate margin was +84 on development and +373 on validation.

Maximum recorded candidate decision time was 120.4 ms in development and 87.7 ms in validation, including framework-reported loading overhead and local machine contention. The configured action limit is one second. These local timings are not a guarantee for Kaggle's server hardware.

## Validity checks

- `uv run pytest -q`: **33 passed**.
- `uv run ruff check .` and `uv run ruff format --check .`: passed.
- Assignment solutions agree with independent exhaustive enumeration on small random matrices.
- Joint-action scenarios cover shared seeds, hire availability, limited market order capacity, retained deposit overflow, and final-turn deposit/sale.
- Full seasons check both seats, deterministic repeated trajectories, actual hand use, non-conflicting crop actions, crop maintenance, and produce liquidation.
- The isolated artifact test excludes repository imports; a deliberately dependent artifact is rejected.
- The matched control is tested with Kaggle's actual loader, including its last-callable entry-point behavior.

During development, an overly aggressive final-day staffing reduction left distant crops unharvested. The candidate now retains sufficient capped labor while standing crops remain. An initial greedy control also exposed its helper as the loader entry point; its ten error games were excluded, the generator was corrected, and the entire comparison was rerun. Neither failure is counted as a competitive win in the reported sets.

## Exact submission artifact

```bash
uv run python prepare_submission.py --output artifacts/submission-step-2
```

The prepared artifact is `artifacts/submission-step-2/main.py`, **10,049 bytes**, with SHA-256:

```text
fc50a8154b898f95e6baae8a0f2918fadb77a8cf933753b53ae8df921a9303a3
```

The copied file completed isolated official-loader self-play at seed 505: both players `DONE`, 720 states, no error statuses or agent stderr, no unsold produce, no leftover seeds, and terminal cash of 13,406 each. Maximum recorded decision time was 7.77 ms. The release uses no external imports, network calls, model files, or repository helpers.

Submit only that `main.py` when ready; the validation JSON and log are local evidence. After an upload, record the submission ID and hash, verify Kaggle's validation outcome, inspect its episode/logs, and compare the server environment with the pinned local one. Preparing and testing a file does not perform that server step or consume a daily submission slot.

## Reproduce the experiment

```bash
uv run python scripts/make_greedy_ablation.py --output artifacts/step-2-controls/greedy-v2.py
uv run python evaluate.py --seeds 11 29 47 71 97 \
  --opponents baselines/step_1.py artifacts/step-2-controls/greedy-v2.py \
  --output artifacts/step-2-development-v2
uv run python evaluate.py --seeds 101 137 173 211 257 293 337 379 419 463 \
  --opponents baselines/step_1.py artifacts/step-2-controls/greedy-v2.py \
  --output artifacts/step-2-validation
```

Choose unused output paths when rerunning. [Committed evidence](benchmarks/step-2.json) contains every reported match, source and environment hashes, resolved configuration, summaries, and the isolated release report. Raw replays/logs remain under ignored `artifacts/` directories. The source-matched [decision example](examples/step-2-decision.json) can be reconstructed with `explain_turn.py`.

The environment remains `kaggle-environments==1.32.7`, with engine SHA-256 `bc8a54879ef02c7ea64b8b333d6a976f0ea65c4949149d01f463f23bccee653e`. The Step 1 reference retains its original SHA-256 `b4ed623e87af218daaeca5d1a9578dc5e0f7db45a35cd095aae6eb90851c77f9`. Linux CI is recorded separately in GitHub Actions.

## Next checkpoint

Step 3 will model production and workforce economics: observed sale prices, seed and labor costs, productive time, and resource constraints. Keep the current valid artifact as the benchmark, test one economic change at a time, and write a new CO explanation with each implementation checkpoint. Diversify the opponent pool before making any medal-strength claim.
