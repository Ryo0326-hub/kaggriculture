# Kaggriculture

An optimization-based agent for Kaggle's farming simulation, developed in explicit, testable steps.

**Step 3: implemented.** A small integer production model chooses wheat/carrot lots and up to six hired hands using seed costs, estimated labor, price impact, observed demand, and remaining growing time. The coordinated execution layer checks shared resources and terminal liquidation. Step 2 passed Kaggle server validation; Step 3 has a separately prepared local release.

## Run locally

Install [uv](https://docs.astral.sh/uv/getting-started/installation/), then:

```bash
uv sync --locked
uv run pytest -q
uv run ruff check .
uv run ruff format --check .
uv run python evaluate.py --seeds 11 29 47 --opponents baselines/step_2.py main.py --output artifacts/local-check
```

Python 3.12 and `kaggle-environments==1.32.7` are pinned. `uv.lock` fixes transitive dependencies. The official simulator brings dependencies for other games; the actual submitted `main.py` uses only the standard library and makes no network calls.

The match runner loads the actual Python artifact through Kaggle's agent loader, plays every seed in both player positions, and writes:

- `manifest.json`: agent hashes, environment/version/source hashes, resolved configuration, seeds, and runner hash.
- `matches.csv` / `matches.jsonl`: outcomes, cash, statuses, runtime, and remaining stock. JSONL also includes crop production, hire/seed order costs, idle work, and resource-conflict diagnostics for both agents.
- `summary.json`: overall and per-opponent results. Errors are reported separately and are never counted as economic wins.
- `replay-0001.json` / `logs-0001.json`: the first replay and logs. Use `--replays all` to save every game; error games are always saved.

Choose a new output directory for each experiment; existing directories are not overwritten. The built-in `random` agent is deliberately excluded because its own unseeded RNG prevents deterministic comparisons. A file can be passed as an opponent instead. Run only trusted agent files: the simulator executes their Python code.

## What the current agent does

The farmer and up to six hands tend wheat and carrots on the 25 initially owned tiles. The economic model compares affordable crop quantities and workforce sizes. It values sale batches along the price curve, accounts for observed supply/demand and a supply stress case, and permits shorter profitable crops near season end. The execution layer creates maintenance, harvest, planting, clearing, and deposit tasks; it jointly assigns existing workers while reserving seeds and storage, then emits unit commands and market orders.

The lot enumeration and worker assignment solve their stated small models exactly. Forecasts, workload estimates, service priorities, and the combined hiring score are approximations; this does not solve the full game's profit or win-probability objective. Read [the Step 3 CO notes](docs/STEP_3_OPTIMIZATION.md) for the equations, marginal values, LP connections, proof limits, and an actual decision.

Historical agents are preserved byte-for-byte in `baselines/step_1.py` and `baselines/step_2.py`, along with their notes and tests. Step 2's server episode and logs were also checked against a local resimulation; see [the audit](docs/benchmarks/step-2-server.json).

## Prepare the submission file

```bash
uv run python prepare_submission.py --output artifacts/submission-step-3
```

This creates `main.py`, `validation.json`, and `validation.log` in a new directory. It checks the **copied file** in full-season self-play using the official loader, in a separate Python process with the repository removed from the import path. The report records its hash, environment, statuses, inventory, and maximum observed decision time. Existing release directories are never overwritten.

**Only the generated `main.py` is the submission artifact.** It needs no supporting repository files. The command does not upload to Kaggle. Next, upload that exact file when ready, inspect Kaggle's validation status and logs, and record its submission ID and hash. Local validation cannot certify the server environment or competitive rating. Remember that a new upload changes the latest-two submission window.

## Reproduce and understand Step 3

```bash
uv run python scripts/make_economics_control.py --fixed-hands --output artifacts/controls/fixed-four.py
uv run python scripts/make_economics_control.py --wheat-only --output artifacts/controls/wheat-only.py
uv run python scripts/make_economics_control.py --optimistic-prices --output artifacts/controls/no-buffer.py
uv run python evaluate.py --seeds 11 29 47 71 97 \
  --opponents baselines/step_2.py artifacts/controls/fixed-four.py \
    artifacts/controls/wheat-only.py artifacts/controls/no-buffer.py \
  --output artifacts/economics-comparison
uv run python explain_turn.py \
  --replay artifacts/economics-comparison/replay-0001.json --state 96 --player 0
```

The controls respectively fix staffing at four, restrict production to wheat, or remove the supply buffer. The replay command checks source and action consistency, then reports worker targets, crop lots, spending, alternative workforce scores, and marginal hiring values. See [the saved example](docs/examples/step-3-decision.json) and [Step 3 evidence](docs/STEP_3_RESULTS.md). The earlier greedy-assignment experiment remains documented in [Step 2](docs/STEP_2_RESULTS.md).

## Learning and implementation checkpoints

The starting mathematical background is CO250: linear programming, duality, and integer programming. Network flow and graph theory will be introduced as needed.

1. **Foundation — complete:** game model, small exact routing example, feasible baseline, reproducible comparisons.
2. **Worker assignment — complete:** binary assignment model, exact bounded solver, resource checks, matched greedy comparison, and isolated artifact validation.
3. **Production and hiring — complete:** integer lot/workforce enumeration, cash and estimated labor constraints, price-impact valuation, supply stress case, and finite-horizon crop value. Land investment remains future work.
4. **Competition and model refinement — next:** broaden the opponent pool, test forecast/workload assumptions, and evaluate further logistics or capital investments against the frozen Step 3 release.

See [the CO250-to-implementation explanation](docs/OPTIMIZATION.md), [engine findings](docs/MECHANICS.md), [Step 1 evidence](docs/STEP_1_RESULTS.md), and [the competition plan](COMPETITION_PLAN.md).

## Files

| File | Role |
| --- | --- |
| `main.py` | Complete current artifact; `agent(obs, configuration=None)` is the final callable entry point |
| `baselines/` | Frozen Step 1 and server-validated Step 2 agents |
| `evaluate.py` | Official-simulator matches, provenance, and result files |
| `prepare_submission.py` | Copy and validate an isolated, self-contained release |
| `explain_turn.py` | Reconstruct and explain a decision from a matching replay |
| `scripts/make_greedy_ablation.py` | Generate the controlled greedy comparison |
| `scripts/make_economics_control.py` | Generate matched staffing, crop, and forecast controls |
| `tests/test_assignment.py` | Independent exhaustive verification of assignment optimality |
| `tests/test_workers.py` | Joint resources, worker actions, full seasons, and endgame |
| `tests/test_economics.py` | Real sale pricing, integer budgets, workload/cost sensitivity, and endgame value |
| `tests/test_production.py` | Current multi-crop policy's full-season action and resource contract |
| `tests/test_submission.py` | Isolated release and actual loader entry-point checks |
| `tests/test_routing.py` | Independent grid-search verification of route optimality |
| `tests/test_mechanics.py` | Engine behavior that can silently destroy economic value |
| `tests/test_baseline.py` | Full seasons, both seats, reproducibility, liquidation, and failure classification |
| `.github/workflows/checks.yml` | Linux installation, lint, format, and tests on pushes and pull requests |

## Sources

- [Competition](https://www.kaggle.com/competitions/kaggriculture)
- [Official environment and documentation](https://github.com/Kaggle/kaggle-environments/tree/master/kaggle_environments/envs/kaggriculture)
- [Pinned simulator release](https://pypi.org/project/kaggle-environments/1.32.7/)

The supplied `README.md` and `AGENTS.md` were read as game references. Their CLI examples do not authorize account actions. Step 2 was uploaded following the user's explicit request and passed server validation. Each new artifact still has its own local and server validation status; see [the submission registry](docs/SUBMISSIONS.md).
