# Cycle 18 — submission candidate

**Ready for the user's Kaggle upload.** This is the custom Cycle 15 descendant
with shared growth routes, deadline-aware feed/fertilizer, ongoing-crop watering
repairs, carried-stock capacity reservations and faster equivalent route costs.

Artifact: `artifacts/submission-cycle-18-ready/main.py`.

SHA-256: `6d3cbf383297aab89a278606026f38b35a1e6f00167314e8916cd23a0a78054e`.

```bash
/Users/ryokitano/.local/bin/kaggle competitions submit kaggriculture \
  -f /Users/ryokitano/Documents/Projects/kaggriculture/artifacts/submission-cycle-18-ready/main.py \
  -m "Cycle 18 - funded growth and deadline inputs - 6d3cbf383297"
```

The positional competition syntax is verified against the installed CLI's
`competitions submit --help`. No upload was performed. Server validation and
competitive results are pending. Root `main.py` is still protected Cycle 3;
use the artifact path above. Earlier Cycle 18 development artifacts are not the
release and are not referenced by the upload command.

## Checks

- **27 bounded regression tests:** route-specific resource credit, profitable
  fertilizer staging, scarce-input assignment, pickup ordering, crop/animal
  survival, terminal harvest/delivery, partial deposits, capacity reservations,
  paid-land admission, deterministic packaging and observation immutability.
  The route-equivalence test includes 36 direct comparisons with the frozen
  insertion constructor. These are task/ledger fixtures, not gameplay episodes.
- **140 independent recorded-observation checks:** both seats at fourteen fixed
  states from each of the five reviewed games, including the larger rival
  farms. Action preconditions, shared stocks, seed counts, unique tile
  assignments, deposits, sales, command counts and JSON serialization pass.
  Each check starts with a cold route cache and leaves its observation unchanged.
- Largest sampled callback **0.298192 seconds**; standalone import/startup
  **0.049849 seconds**. Local sampled timing is not a server worst-case guarantee.
- Standard-library imports only; the final callable is `agent`.
- Source compilation, Ruff and frozen-parent hash checks pass.

[Check evidence](benchmarks/cycle-18-checks.json) ·
[Soumic investment decision](benchmarks/cycle-18-decision-evidence.json) ·
[Strategy and CO notes](CYCLE_18_OPTIMIZATION.md).

No local match, simulated season, applied replay action, counterfactual episode,
training, paid compute or model API was used. Fixed-observation decisions test
the interface and expose forecasts; they do not measure win rate or revenue.

## Reproduce on another checkout

```bash
uv run --no-sync python -m scripts.make_production_agent \
  --output artifacts/submission-cycle-18-ready/main.py
```

The builder refuses to overwrite an existing file. It rebuilds and checks Cycle
17, whose builder checks Cycle 15, before adding the new module. To verify a
second build locally, choose a fresh output path and compare the SHA-256 above.
The ignored artifact is reproducible from committed source and builder files.

Frozen parents remain unchanged:

- Cycle 15: `ce4444126f5ef7e0ee01a22f395ae87ee442ec2f329c4feb6aedf0687af45f1a`.
- Cycle 17: `96297a3e899d77bbb5f0ec0299da34418bbdf9c62d999738df39da7a4237c6ea`.

Cycle 18 supersedes Cycle 17 as the candidate to upload; Cycle 17 has no claimed
server result. The existing validated submissions are unaffected until the user
uploads. Retain their logs for comparison with this candidate's own games.
