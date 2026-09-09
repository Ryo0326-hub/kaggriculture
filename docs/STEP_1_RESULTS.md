# Step 1: verified baseline

Completed locally on September 9, 2026. The scope is a reliable experimentation foundation and a small exact optimization example. No Kaggle submission or server validation has been performed in this step.

Historical checkpoint: commit `dc401062aadf4b6705d80859e247918c7fb0af3a`. Its artifact is now preserved in `baselines/step_1.py`; the current `main.py` is Step 2. To repeat the command below from the current checkout, add `--agent baselines/step_1.py` and replace the self-play opponent `main.py` with `baselines/step_1.py`.

## Validation

- `uv run ruff check .`: passed.
- `uv run ruff format --check .`: passed.
- `uv run pytest -q`: **18 passed**.
- Full benchmark: **20 completed games**, each containing 720 recorded states, with the final actionable observation at step 718.
- All 20 benchmark games ended with zero unsold shed units, zero carried produce, and zero unused seeds for the candidate.

The tests include an independent exact route oracle, engine boundary scenarios, both player seats, a repeated-seed trajectory comparison, self-play, and a deliberately crashing opponent to verify failure reporting.

## Development benchmark

```bash
uv run python evaluate.py --seeds 11 29 47 71 97 --opponents starter main.py --output artifacts/step-1
```

| Opponent | Games | Wins | Draws | Losses | Errors | Mean candidate cash | Mean cash margin |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| Official starter | 10 | 10 | 0 | 0 | 0 | 6,624.8 | +3,068.6 |
| Identical baseline | 10 | 0 | 10 | 0 | 0 | 6,387.2 | 0.0 |

Starting cash was 3,000. The largest recorded candidate decision duration was approximately **46.6 ms** on the local machine, including file-loading overhead where recorded by the framework. This is a local measurement, not a Kaggle sandbox timing guarantee.

These are five development seeds with paired player positions. They are not 20 independent samples, and self-play draws are expected for this deterministic policy. Starter wins establish basic functionality, not medal-level strength. A competitive opponent pool and held-out selection remain future work.

The committed [benchmark evidence](benchmarks/step-1.json) includes all match records, source hashes, configuration, and summaries. Raw replay/log artifacts stay local under the ignored `artifacts/step-1/` directory.

## Reproduction identifiers

- Python: `3.12.12` locally; project requires Python 3.12.
- Simulator: `kaggle-environments==1.32.7`.
- Agent SHA-256: `b4ed623e87af218daaeca5d1a9578dc5e0f7db45a35cd095aae6eb90851c77f9`.
- Interpreter SHA-256: `bc8a54879ef02c7ea64b8b333d6a976f0ea65c4949149d01f463f23bccee653e`.

Use a new output directory when reproducing a run. Compare actions, outcomes, cash, and fingerprints; wall-clock timing naturally varies. Linux CI is recorded separately in the repository's Actions tab.

## Next checkpoint

Implement coordinated hired-worker assignment from an explicit binary decision model. Explain the assignment LP and its network-flow connection, then compare the resulting policy against this frozen Git version and additional opponents. Production mix, land expansion, and uncertain-demand optimization remain later steps.
