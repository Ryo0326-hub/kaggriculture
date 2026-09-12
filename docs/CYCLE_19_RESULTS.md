# Cycle 19 — ready for user-run server validation

The final standalone artifact is:

`artifacts/submission-cycle-19-final/main.py`

SHA-256: `eb151fe1e088e598edfdcd6b10c5c108bdb91783bfbbac9758211b5df29bd17d`.

This is our implementation of observed strategic principles, not Majkel's private
source and not an exact copy of either replay. [Second game review](MAJKEL_108300532_STUDY.md),
[first game review](MAJKEL_108305451_STUDY.md), [implementation/CO notes](CYCLE_19_OPTIMIZATION.md).

## Upload this exact file

```bash
/Users/ryokitano/.local/bin/kaggle competitions submit kaggriculture \
  -f /Users/ryokitano/Documents/Projects/kaggriculture/artifacts/submission-cycle-19-final/main.py \
  -m "Cycle 19 - compact service and adaptive growth - eb151fe1e088"
```

The installed CLI's help confirms the positional competition argument. The
command does not upload root `main.py`, which remains protected Cycle 3. Earlier
Cycle 19 development artifacts, including `submission-cycle-19-compact`, are
superseded. We performed no automatic upload. Kaggle validation and ladder
performance remain pending.

## Checks completed on the final source

- 73 bounded tests pass: 33 new Cycle 19 cases plus 40 protected Cycle 18 checks.
  These include authored multi-callback continuity fixtures, without advancing
  a game, in addition to input/stock/deadline cases.
- 5,752 independent recorded-observation checks pass across both players in
  episodes 108300532, 108305451, 108239790 and 108195100. Input observations are
  unmodified. Checks validate legal actions, unique tile assignments, seed
  counts, shared shed accounting, order count and sampled runtime.
- Maximum callback in that pass: approximately 0.0194 seconds against the
  configured one-second action limit. This is local timing, not a server guarantee.
- Ruff lint/format checks pass; the builder compiles the standalone code and
  reproduces identical bytes. Final source uses only standard-library imports.
- Final artifact hash matches the checked source and the committed builder.
  The protected Cycle 18 artifact remains `65e0e1f6f12e…` unchanged.
- Local games, counterfactual matches, parameter sweeps, training, paid compute
  and automatic submissions: **zero**.

[Observation evidence](benchmarks/cycle-19-checks.json) ·
[Release manifest](benchmarks/cycle-19-release.json).

The draft audit caught shared-stock processing order, optional fertilizer
admission, stale installation, field reuse, storage admission, and a poor-cash
hiring-before-feed risk. The final regressions cover those conditions. Passing
these checks does not prove all possible states safe or establish win rate.

## Reproduction

The builder refuses an existing output path:

```bash
.venv/bin/python -m scripts.make_majkel_agent --output NEW_DIRECTORY/main.py
.venv/bin/pytest -q tests/test_majkel.py tests/test_cycle18.py
.venv/bin/ruff check .
.venv/bin/ruff format --check .
```

To repeat the isolated observation audit, use `scripts.check_majkel_agent` with
`--source`, `--replays` and `--output`. It does not import the simulator or execute
an episode. Do not treat its outputs as outcomes that the new bot would have
achieved in the original games.

## What to inspect in returned server games

First confirm DONE and clean agent logs. Then compare deployment timing, active
footprint, ownership/route continuity, missed water/feed/care, seed backlog, actual
versus expected product flow, warehouse losses, and final inventory. Track net
receipts minus costs; do not infer strength solely from gross output, one early
rating, one loss, or an absolute 150K cash target in every town. Preserve the
existing bots while judging this one from its own server evidence.
