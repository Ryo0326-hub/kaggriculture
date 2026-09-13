# Fresh Cycle 1 — submission package

**Historical pre-fix report.** The original artifact and benchmark below remain preserved. The [Fresh Cycle 1 fixes release](FRESH_CYCLE_1_FIXES.md) supersedes its policy, results and upload command: all nine formerly expected failures now pass as mandatory regressions; the full bounded selection passes 871 tests.

Prepared September 12, 2026, Toronto. **Implemented and packaged for user-run
Kaggle submission. Not uploaded, server-validated or competitively evaluated.**

The user requested a fresh Cycle 1 without a reference. This supersedes the
Cycle 19 derivation instructions in `HANDOFF_CYCLE_22.md`. Policy code is newly
written from game mechanics; no prior agent/helper is used by the source or
builder. Archived releases retain their existing names.

## Release identity

| Item | Value |
| --- | --- |
| Branch / starting commit | `codex/fresh-cycle-1` / `d6dc250` |
| Source, exact submission bytes | `experiments/fresh_cycle1.py` |
| Builder | `scripts/make_fresh_cycle1.py` |
| Final local artifact | `artifacts/submission-fresh-cycle-1-final/main.py` |
| SHA-256 | `c5d31b86d1120028114f058d0560f73036c7ae940fe5186cb8dc7e2a59ef585e` |
| Size / runtime imports | 38,438 bytes / standard-library `math` only |
| Entry point | `agent(observation, configuration=None)`, last callable |
| Mechanics | Pinned `kaggle-environments==1.32.7`, source read without engine import |

Worktree: `/Users/ryokitano/Documents/Projects/kaggriculture2`, on a separate
branch from the clean neighboring `kaggriculture` checkout. The local upload
file is gitignored by existing convention; committed policy source contains
its exact bytes. The builder recreates it without any reference and refuses
to overwrite existing destinations.

## Verification

- **210 bounded tests pass:** 34 new focused checks and 176 existing historical
  regression checks. No simulation tests were invoked.
- **175 original observations in eight histories**, 16–24 states each, from
  three completed server games. Two identical warm passes and one cold pass
  make **525 callback checks** on the final artifact.
- Per-callback one-second alarms, action preconditions, shared seed/input and
  capacity checks, unique ownership, immutable inputs and warm-run determinism.
  The recorded maximum was **0.067234 seconds** in a run concurrent with the
  bounded test suite; this is local timing, not Kaggle runtime evidence.
- Standalone isolated Python (`-I`) load, exact source/artifact bytes, deterministic
  builder, imports, compilation and last-callable entrypoint all pass.
- Repository lint, format and syntax checks pass. CI now includes the new
  bounded tests; simulation tests remain behind explicit manual opt-in.

[Machine-readable checks](benchmarks/fresh-cycle1-checks.json) preserve input and
action hashes, timing and route diagnostics. The fixture is losslessly encoded
as gzip/base64 JSON to compact repeated boards. The helper
`scripts.check_fresh_cycle1.read_histories()` verifies its expanded hash and
returns original observations and source provenance. It contains no prior
policy memory and does not execute recorded or candidate actions.

| Server recording | Seat and observation windows (end exclusive) |
| --- | --- |
| 108351109 validation | Seat 0: 0–16, 240–264, 288–306; seat 1: 696–719 |
| 108360391 versus mogura | Seat 1: 480–504, 696–719 |
| 108359367 versus Nawaf | Seat 0: 432–456, 696–719 |

At route-witness steps 492/493/494, Cycle 1 requests WEST/WEST/WEST for worker 3
and retains animal-service target `(3,3)`. It uses its own memory. The recording
still moves according to the historical actions; these are off-policy
diagnostics, not a completed replacement route or a production-gain claim.

## Preservation and limits

The original checkout stays clean. Root `main.py`, `baselines/cycle_3.py`, the
three prior experimental policy sources, public V36 and final Cycle 19/20/21
artifacts were hash-checked before and after work and are unchanged. The
[preservation manifest](benchmarks/fresh-cycle1-preserved.json) records them.
No old artifact, recording, notebook or benchmark was overwritten.

No local game, full-season simulation, counterfactual season, tuning sweep,
cloud service or paid compute ran. No automatic Kaggle upload occurred. Existing
historical tests protect archived files and are not a performance reference.
Price/work estimates and portfolio bounds are heuristics; server execution,
delivered production, profitability and competitive strength remain unverified.

[Economics and CO notes](FRESH_CYCLE_1_OPTIMIZATION.md) explain cash, marginal
value, greedy matching, input constraints and deadline budgets. Next evidence
should separate Kaggle validation from rated games and inspect service,
installation lag, output delivery, wages and final cash.

## Reproduce without a game

From this worktree, using the existing development interpreter:

```bash
/Users/ryokitano/Documents/Projects/kaggriculture/.venv/bin/python -m scripts.make_fresh_cycle1 \
  --output /tmp/kaggriculture-fresh-cycle1-new-check/main.py
/Users/ryokitano/Documents/Projects/kaggriculture/.venv/bin/python -m scripts.check_fresh_cycle1 \
  --agent /tmp/kaggriculture-fresh-cycle1-new-check/main.py
/Users/ryokitano/Documents/Projects/kaggriculture/.venv/bin/pytest -q tests/test_fresh_cycle1.py
```

Choose another nonexistent destination if needed. A new clone can use
`uv sync --locked --only-group dev` and `uv run --no-sync` instead. No engine
installation is needed for these checks.

## User-run upload

Verified against the installed `kaggle competitions submit --help` and
[official CLI documentation](https://github.com/Kaggle/kaggle-cli/blob/main/docs/competitions.md#kaggle-competitions-submit).
The competition name is positional. This is the verified new artifact:

```bash
/Users/ryokitano/.local/bin/kaggle competitions submit kaggriculture \
  -f /Users/ryokitano/Documents/Projects/kaggriculture2/artifacts/submission-fresh-cycle-1-final/main.py \
  -m "Fresh Cycle 1 - reserved visits and cash discipline - c5d31b86d112"
```

Ryo executes the command. Push/CI success is not a Kaggle upload or validation.
