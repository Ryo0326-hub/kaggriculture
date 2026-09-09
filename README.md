# Kaggriculture

An optimization-based agent for Kaggle's farming simulation, developed in explicit, testable steps.

**Step 1: implemented.** A reproducible simulator, a four-plot wheat baseline, an exact small routing solver, mechanics tests, and a match runner. This is a development baseline; its local results do not establish leaderboard or medal strength.

## Run locally

Install [uv](https://docs.astral.sh/uv/getting-started/installation/), then:

```bash
uv sync --locked
uv run pytest -q
uv run ruff check .
uv run ruff format --check .
uv run python evaluate.py --seeds 11 29 47 --opponents starter main.py --output artifacts/baseline
```

Python 3.12 and `kaggle-environments==1.32.7` are pinned. `uv.lock` fixes transitive dependencies. The official simulator brings dependencies for other games; the actual submitted `main.py` uses only the standard library and makes no network calls.

The match runner loads the actual Python artifact through Kaggle's agent loader, plays every seed in both player positions, and writes:

- `manifest.json`: agent hashes, environment/version/source hashes, resolved configuration, seeds, and runner hash.
- `matches.csv` / `matches.jsonl`: individual outcomes, cash, statuses, runtime, and remaining stock.
- `summary.json`: overall and per-opponent results. Errors are reported separately and are never counted as economic wins.
- `replay-0001.json` / `logs-0001.json`: the first replay and logs. Use `--replays all` to save every game; error games are always saved.

Choose a new output directory for each experiment; existing directories are not overwritten. The built-in `random` agent is deliberately excluded because its own unseeded RNG prevents deterministic comparisons. A file can be passed as an opponent instead. Run only trusted agent files: the simulator executes their Python code.

## What the baseline does

One farmer tends four wheat plots next to the shed. It waters crops, harvests at age four, clears weeds, purchases only enough seeds for the active plots, and deposits/sells stock. It stops new production conservatively near the season end and explicitly returns carried produce before termination.

Within a watering, harvesting, planting, or weed-clearing batch, it examines all visit orders for at most four tiles and chooses the shortest route using Manhattan distances. This is an exact combinatorial solution to that **restricted movement problem**. Crop choice, task priorities, and investment decisions remain heuristics.

## Learning and implementation checkpoints

The starting mathematical background is CO250: linear programming, duality, and integer programming. Network flow and graph theory will be introduced as needed.

1. **Foundation — complete:** game model, small exact routing example, feasible baseline, reproducible comparisons.
2. **Worker assignment — next:** formulate a binary assignment model; compare coordinated workers with the baseline before adding complexity.
3. **Production and investment:** incorporate labor/capital constraints, marginal values, and market impact; use LP bounds and integer decisions where appropriate.
4. **Uncertainty and competition:** replan as shops and rival production change; validate against diverse opponents and unseen seeds.

See [the CO250-to-implementation explanation](docs/OPTIMIZATION.md), [engine findings](docs/MECHANICS.md), [Step 1 evidence](docs/STEP_1_RESULTS.md), and [the competition plan](COMPETITION_PLAN.md).

## Files

| File | Role |
| --- | --- |
| `main.py` | Complete baseline artifact; `agent(obs, configuration=None)` is the entry point |
| `evaluate.py` | Official-simulator matches, provenance, and result files |
| `tests/test_routing.py` | Independent grid-search verification of route optimality |
| `tests/test_mechanics.py` | Engine behavior that can silently destroy economic value |
| `tests/test_baseline.py` | Full seasons, both seats, reproducibility, liquidation, and failure classification |
| `.github/workflows/checks.yml` | Linux installation, lint, format, and tests on pushes and pull requests |

## Sources

- [Competition](https://www.kaggle.com/competitions/kaggriculture)
- [Official environment and documentation](https://github.com/Kaggle/kaggle-environments/tree/master/kaggle_environments/envs/kaggriculture)
- [Pinned simulator release](https://pypi.org/project/kaggle-environments/1.32.7/)

The supplied `README.md` and `AGENTS.md` were read as game references. Their CLI examples do not automatically authorize Kaggle uploads, account actions, or rule acceptance. This repository currently performs local evaluation and GitHub CI only.
