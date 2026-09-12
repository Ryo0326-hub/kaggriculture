# Cycle 20 — submission candidate

Prepared September 12, 2026. **Not uploaded by the assistant; server validation
and competitive results are pending.** The user reports submitting Cycle 19;
its source and artifact are preserved unchanged.

- Artifact: `artifacts/submission-cycle-20-final/main.py`
- SHA-256: `79a8fb9661cd6fbb0c2cb9abc5a591b7daee1496b292ba8eca889f4fe6b16280`
- Size: 41,553 bytes; standalone standard-library Python.
- Frozen parent: Cycle 19, `eb151fe1e088e598edfdcd6b10c5c108bdb91783bfbbac9758211b5df29bd17d`.
- Changes: committed-output price forecasts, feed opportunity cost, uncushioned
  price downside and late-day survival priority. [Implementation and CO notes](CYCLE_20_OPTIMIZATION.md).
- Evidence: [Majkel loss review](MAJKEL_108295517_STUDY.md),
  [release manifest](benchmarks/cycle-20-release.json),
  [recorded-observation checks](benchmarks/cycle-20-checks.json).

## Checks actually performed

**117 bounded tests pass**, covering protected Cycle 18 and shared Cycle 19/20
decision/accounting cases plus the new forecast and rescue tests. Repository
lint, formatting, syntax and diff checks pass. Isolated `python -I` artifact
loading and one opening decision pass without importing `kaggle_environments`.

**7,190 independent recorded observations pass** resource/legality and
input-immutability checks across both seats of five supplied games: 108295517,
108300532, 108305451, 108239790 and 108195100. Each call starts with cleared policy
memory; the candidate's action is never applied to an environment. Maximum
observed callback time on this machine is **0.024393 seconds**. This is not a
Kaggle runtime guarantee, season simulation or performance measurement.

No local games, training, cloud jobs, tuning sweeps or automatic Kaggle uploads
were run. Server play is still required to evaluate integrated performance.

## Upload this exact artifact

The installed Kaggle CLI uses a positional competition name:

```bash
/Users/ryokitano/.local/bin/kaggle competitions submit kaggriculture \
  -f /Users/ryokitano/Documents/Projects/kaggriculture/artifacts/submission-cycle-20-final/main.py \
  -m "Cycle 20 - supply risk and survival - 79a8fb9661cd"
```

Do not upload the repository-root `main.py`, which remains a protected older bot.
The review artifact is superseded by this final file. To rebuild the final source
into a new, nonexistent path, use:

```bash
cd /Users/ryokitano/Documents/Projects/kaggriculture
.venv/bin/python -m scripts.make_resilience_agent --output /tmp/kaggriculture-cycle20/main.py
```

The builder refuses overwrite and fails if its parent source changes. The hash
must match the final artifact above. Bounded checks can be rerun with:

```bash
.venv/bin/pytest -q tests/test_cycle18.py tests/test_majkel.py tests/test_resilience.py
```

On the next server logs, inspect whether this candidate avoids buying into milk
or berry gluts, still deploys capital in favorable towns, services threatened
plots before night and delivers terminal output. A valid action check cannot
establish any of those season-level competitive outcomes on its own.
