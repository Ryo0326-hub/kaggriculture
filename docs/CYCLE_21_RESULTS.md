# Cycle 21 — submission candidate

Prepared September 12, 2026. Ready for user upload; **Kaggle validation and
competitive performance remain pending**.

- Final artifact: `artifacts/submission-cycle-21-final/main.py`
- SHA-256: `f56a3f597528265c8a7ecaeaaf1f08ad03035a5b1ce56809b2baa9c7c5fd2156`
- Size: 50,589 bytes; standalone Python using only `math` and `collections.Counter`.
- Frozen parent: Cycle 20, `79a8fb9661cd6fbb0c2cb9abc5a591b7daee1496b292ba8eca889f4fe6b16280`.
- Changes: safe watering calendar, production/decay deadlines, worker assistance
  across overloaded sectors, input/deposit timing protection and matching crop labor costs.
- [Implementation and CO notes](CYCLE_21_OPTIMIZATION.md) ·
  [Release manifest](benchmarks/cycle-21-release.json) ·
  [Recorded-observation checks](benchmarks/cycle-21-checks.json).

## Verification performed

**176 bounded tests pass.** Repository lint, formatting, syntax and diff checks
pass. The final artifact matches the tested audit source byte for byte and is
reproducible from the committed builder. The builder refuses overwrite and fails
if the frozen parent changes. Cycle 19 and Cycle 20 sources/artifacts are unchanged.

**5,752 independent recorded observations pass** action/resource validation,
input-immutability and runtime checks across both seats of episodes 108335136,
108290604, 108305451 and 108295517. Maximum local callback time is **0.028855 seconds**.
Isolated `python -I` loading and a recorded-observation call pass with no engine
import; isolated source loading takes approximately 0.010454 seconds locally.

These checks do not run a match or prove a higher score. No local games, training,
cloud spending or automatic upload occurred. The final artifact supersedes the
review/audit files; upload the final file below.

## Upload command

The installed CLI's help confirms the positional competition syntax:

```bash
/Users/ryokitano/.local/bin/kaggle competitions submit kaggriculture \
  -f /Users/ryokitano/Documents/Projects/kaggriculture/artifacts/submission-cycle-21-final/main.py \
  -m "Cycle 21 - production calendars and deadlines - f56a3f597528"
```

Do not use the repository-root `main.py`, which is a protected older bot.

To rebuild into a new, nonexistent location:

```bash
cd /Users/ryokitano/Documents/Projects/kaggriculture
.venv/bin/python -m scripts.make_calendar_agent --output /tmp/kaggriculture-cycle21/main.py
```

The output hash must match the full SHA-256 above. Bounded checks are:

```bash
.venv/bin/pytest -q tests/test_cycle18.py tests/test_majkel.py tests/test_resilience.py tests/test_calendar.py
```

The default GitHub workflow runs these bounded tests. Full game tests remain
disabled unless explicitly requested through the separate manual workflow input.
