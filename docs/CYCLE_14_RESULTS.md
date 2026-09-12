# Cycle 14 — unchanged public V36, ready for user upload

September 11, 2026. After the [Cycle 13 growth failure](CYCLE_13_POSTMORTEM.md),
Ryo requested adopting the entire public strategy reported at 2705.7. This
release packages **the exact V36 notebook agent**, without gameplay changes.
Its thirteen schedules, opening, shop router, production overlays, sales and
terminal planner are all retained. It is attributed upstream work, not claimed
as a newly developed Unicorns strategy.

## Exact artifact

- Preserved source: `third_party/kaggriculture_v36/main.py`.
- Upload: `artifacts/submission-cycle-14-v36/main.py`.
- Both SHA-256: `7eb5ab6c48581c82906ab6fa6b2cc5c9607513249ef59b2c45fcd6176e8653dd`.
- Notebook SHA-256: `5cefaf9299049e0ee61c83f22869d0916647fe9f495d68b1b20e22c0093b6224`.
- The newly attached `(1).ipynb` is byte-identical to the notebook reviewed
  previously. Extraction removes only its cell-4 `%%writefile main.py` line.
- Complete in-source Apache-2.0 license/notices, separate license, attribution
  cell and [provenance](../third_party/kaggriculture_v36/provenance.json) are retained.

The frozen third-party source is excluded from Ruff formatting/lint so it stays
byte-identical. Our builder and tests remain covered. Root `main.py` remains
the protected Cycle 3 source. Cycle 12 and Cycle 13 artifacts are unchanged.
**Upload the Cycle 14 path below, not root `main.py`.**

## What was checked

- Three bounded packaging tests pass: exact copy/hash, refusal to overwrite an
  existing output, and refusal to package altered upstream bytes.
- Eighteen calls on recorded observations pass action serialization, worker
  count, order limit and observation-immutability checks in Python `-I`
  isolation, using the official loader's last-callable selection rule.
- The selected entry point is `agent`; both seats return the exact expected
  revised wheat opening. Sampled startup was at most 0.0333 seconds and sampled
  callback time at most 0.000189 seconds. No exception counters were triggered.
- No engine imports, game advances, matches or local terminal-planner calls
  occurred. [Artifact check](benchmarks/cycle-14-artifact-check.json).
- Repository lint, formatting and Python syntax checks pass. Default CI now
  includes the frozen third-party source in compilation without executing it.

These are integrity/interface checks, not evidence of full-season economic
performance or worst-case runtime. The policy's original bounded physical
planner may run on Kaggle at step 712; it was retained but not invoked locally.
The same frozen source always packs to the same hash. No LLM, GPU, training,
Featherless key or external runtime API is required.

## Build and upload

The artifact already exists on Ryo's machine. To reproduce in a fresh checkout:

```bash
uv run --no-sync python -m scripts.make_public_v36 \
  --output artifacts/submission-cycle-14-v36/main.py
```

The builder refuses an existing output and does not upload. The installed CLI
takes the competition as a positional argument:

```bash
/Users/ryokitano/.local/bin/kaggle competitions submit kaggriculture \
  -f /Users/ryokitano/Documents/Projects/kaggriculture/artifacts/submission-cycle-14-v36/main.py \
  -m "Cycle 14 - unchanged public V36 - 7eb5ab6c4858"
```

No automatic upload was made. Server validation, submission ID and competitive
rating remain pending. Copying the source does not guarantee matching its
reported rating: the exact upstream score/version association was not verified,
and opponent pool and played episodes matter.

## Strategy and next evidence

The [V36 strategy/CO review](V36_NOTEBOOK_REVIEW.md) explains the schedules,
conditional investments, market sequencing, sales and terminal delivery.
Its raw schedules request two land purchases at steps 150 and 265; a request
still needs cash and successful execution. Conditional overlays can buy a
fourth quadrant in certain demand configurations.

After upload, check validation and return the games. Inspect actual expansion,
productive footprint, output, wages, stock, repairs, final delivery and final
cash. Establish this unchanged baseline's behavior before altering it. Keep
public-baseline evidence separate from our earlier agent's results and from
upstream benchmark claims. No local match simulations are planned.
