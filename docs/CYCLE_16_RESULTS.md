# Cycle 16 — unchanged public V36 baseline for the next server test

The [Cycle 15 server analysis](CYCLE_15_SERVER_ANALYSIS.md) finds successful
execution but insufficient productive scale. The next recommendation is to
test the complete public strategy that Ryo previously requested, before
another speculative custom redesign.

This is a **new package path for the exact source already preserved as Cycle
14**, not a new version of V36 or a newly improved custom policy. Its source
and notices remain byte-identical. No new farming, trading or model logic was
implemented for this release. No claim of a 2700 rating or 150,000 final coins.

## Upload artifact

`artifacts/submission-cycle-16-public-baseline/main.py`

SHA-256: `7eb5ab6c48581c82906ab6fa6b2cc5c9607513249ef59b2c45fcd6176e8653dd`.

```bash
/Users/ryokitano/.local/bin/kaggle competitions submit kaggriculture \
  -f /Users/ryokitano/Documents/Projects/kaggriculture/artifacts/submission-cycle-16-public-baseline/main.py \
  -m "Cycle 16 - unchanged public V36 baseline - 7eb5ab6c4858"
```

No automatic upload was made. Kaggle validation and our own results for these
exact bytes are pending. Submitting it alongside the current Cycle 15 provides
the next source-identifiable server comparison, not a randomized paired test.

## Integrity and existing evidence

The exact-copy builder verified the frozen upstream hash and parsed the Python
source while creating the new artifact. Cycle 14 and Cycle 16 files, plus the
vendored source, match byte-for-byte. The [Cycle 14 packaging/interface checks](benchmarks/cycle-14-artifact-check.json) apply to the identical source; they
were not rerun or relabeled as new performance evidence.

The public source embeds thirteen action schedules, shop-dependent route
selection, repairs, production overlays, sales and a bounded terminal planner.
It uses standard-library Python and requires no cloud training, GPU or LLM API.
The local packaging step does not invoke that planner or run a game. Preserve
the [upstream attribution and license](../third_party/kaggriculture_v36/README.md).

To reproduce at a new path:

```bash
uv run --no-sync python -m scripts.make_public_v36 \
  --output artifacts/submission-cycle-16-public-baseline/main.py
```

The builder refuses overwriting. Root `main.py`, custom Cycle 15, public Cycle
14 and all prior frozen sources remain unchanged. Artifacts are ignored by Git;
the committed builder and vendored source reproduce this package.
