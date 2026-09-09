# Kaggriculture

An optimization-based agent for Kaggle's farming simulation, developed in explicit, testable steps.

**Step 2: implemented.** Up to four hired hands coordinate work across the starting quadrant through an exact small worker-task assignment solver. Shared seeds, storage, hire timing, and terminal liquidation have explicit checks. Local results establish a working development candidate, not leaderboard or medal strength.

## Run locally

Install [uv](https://docs.astral.sh/uv/getting-started/installation/), then:

```bash
uv sync --locked
uv run pytest -q
uv run ruff check .
uv run ruff format --check .
uv run python evaluate.py --seeds 11 29 47 --opponents baselines/step_1.py main.py --output artifacts/local-check
```

Python 3.12 and `kaggle-environments==1.32.7` are pinned. `uv.lock` fixes transitive dependencies. The official simulator brings dependencies for other games; the actual submitted `main.py` uses only the standard library and makes no network calls.

The match runner loads the actual Python artifact through Kaggle's agent loader, plays every seed in both player positions, and writes:

- `manifest.json`: agent hashes, environment/version/source hashes, resolved configuration, seeds, and runner hash.
- `matches.csv` / `matches.jsonl`: individual outcomes, cash, statuses, runtime, and remaining stock.
- `summary.json`: overall and per-opponent results. Errors are reported separately and are never counted as economic wins.
- `replay-0001.json` / `logs-0001.json`: the first replay and logs. Use `--replays all` to save every game; error games are always saved.

Choose a new output directory for each experiment; existing directories are not overwritten. The built-in `random` agent is deliberately excluded because its own unseeded RNG prevents deterministic comparisons. A file can be passed as an opponent instead. Run only trusted agent files: the simulator executes their Python code.

## What the current agent does

The farmer and up to four hands tend wheat on the 25 initially owned tiles. Each turn, the policy creates watering, harvesting, planting, weed-clearing, and deposit tasks. It jointly assigns existing workers to feasible tasks while reserving seeds, then issues movement or work commands and an ordered market queue. It stops new production conservatively near the season end and returns carried produce before termination.

The assignment solver exactly maximizes the supplied task scores under worker/task uniqueness and a seed quota. The task scores, crop choice, workforce cap, and investment rules remain heuristics. Read [the Step 2 CO implementation notes](docs/STEP_2_OPTIMIZATION.md) for the integer model, algorithm, proof scope, limitations, and an actual explained decision.

Step 1's four-plot, single-farmer routing policy is preserved byte-for-byte in `baselines/step_1.py`, along with its tests and historical results.

## Prepare the submission file

```bash
uv run python prepare_submission.py --output artifacts/submission-step-2
```

This creates `main.py`, `validation.json`, and `validation.log` in a new directory. It checks the **copied file** in full-season self-play using the official loader, in a separate Python process with the repository removed from the import path. The report records its hash, environment, statuses, inventory, and maximum observed decision time. Existing release directories are never overwritten.

**Only the generated `main.py` is the submission artifact.** It needs no supporting repository files. The command does not upload to Kaggle. Next, upload that exact file when ready, inspect Kaggle's validation status and logs, and record its submission ID and hash. Local validation cannot certify the server environment or competitive rating. Remember that a new upload changes the latest-two submission window.

## Reproduce and understand Step 2

```bash
uv run python scripts/make_greedy_ablation.py --output artifacts/controls/greedy.py
uv run python evaluate.py --seeds 11 29 47 71 97 \
  --opponents baselines/step_1.py artifacts/controls/greedy.py \
  --output artifacts/assignment-comparison
uv run python explain_turn.py \
  --replay artifacts/assignment-comparison/replay-0001.json --state 30 --player 0
```

The greedy control changes only the assignment algorithm, so its comparison tests coordination at the same workforce and farm scale. The replay command checks the source hash and recorded action before reporting worker targets and scores. See [the saved example](docs/examples/step-2-decision.json) and [Step 2 evidence](docs/STEP_2_RESULTS.md).

## Learning and implementation checkpoints

The starting mathematical background is CO250: linear programming, duality, and integer programming. Network flow and graph theory will be introduced as needed.

1. **Foundation — complete:** game model, small exact routing example, feasible baseline, reproducible comparisons.
2. **Worker assignment — complete:** binary assignment model, exact bounded solver, resource checks, matched greedy comparison, and isolated artifact validation.
3. **Production and investment — next:** incorporate labor/capital constraints, marginal values, and market impact; use LP bounds and integer decisions where appropriate.
4. **Uncertainty and competition:** replan as shops and rival production change; validate against diverse opponents and unseen seeds.

See [the CO250-to-implementation explanation](docs/OPTIMIZATION.md), [engine findings](docs/MECHANICS.md), [Step 1 evidence](docs/STEP_1_RESULTS.md), and [the competition plan](COMPETITION_PLAN.md).

## Files

| File | Role |
| --- | --- |
| `main.py` | Complete current artifact; `agent(obs, configuration=None)` is the final callable entry point |
| `baselines/step_1.py` | Frozen four-plot reference agent |
| `evaluate.py` | Official-simulator matches, provenance, and result files |
| `prepare_submission.py` | Copy and validate an isolated, self-contained release |
| `explain_turn.py` | Reconstruct and explain a decision from a matching replay |
| `scripts/make_greedy_ablation.py` | Generate the controlled greedy comparison |
| `tests/test_assignment.py` | Independent exhaustive verification of assignment optimality |
| `tests/test_workers.py` | Joint resources, worker actions, full seasons, and endgame |
| `tests/test_submission.py` | Isolated release and actual loader entry-point checks |
| `tests/test_routing.py` | Independent grid-search verification of route optimality |
| `tests/test_mechanics.py` | Engine behavior that can silently destroy economic value |
| `tests/test_baseline.py` | Full seasons, both seats, reproducibility, liquidation, and failure classification |
| `.github/workflows/checks.yml` | Linux installation, lint, format, and tests on pushes and pull requests |

## Sources

- [Competition](https://www.kaggle.com/competitions/kaggriculture)
- [Official environment and documentation](https://github.com/Kaggle/kaggle-environments/tree/master/kaggle_environments/envs/kaggriculture)
- [Pinned simulator release](https://pypi.org/project/kaggle-environments/1.32.7/)

The supplied `README.md` and `AGENTS.md` were read as game references. Their CLI examples do not automatically authorize Kaggle uploads, account actions, or rule acceptance. This repository performs local evaluation, release preparation, and GitHub CI. Kaggle server submission remains a separate action.
