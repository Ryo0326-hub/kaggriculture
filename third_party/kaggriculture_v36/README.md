# Unchanged public V36 candidate

This directory preserves the exact agent supplied in Ahmed Berat Özer's public
`kaggriculture-v36-guarded-four-turn-sales` notebook. It is upstream work, not a
newly authored Unicorns policy. Ryo requested using the complete strategy after
the Cycle 13 server loss. Local strategy modifications: **none**.

- `main.py`: complete, standalone upstream agent with its full license and notices.
- `LICENSE`: Apache-2.0 text extracted from the retained source comments.
- `ATTRIBUTION.md`: unchanged attribution cell from the supplied notebook.
- `provenance.json`: source URL, extraction method and integrity hashes.

The submitted file needs only `main.py`; all schedules and runtime helpers are
embedded. Do not format this file: byte identity is checked by the builder.
Its exclusion from Ruff applies only to this frozen third-party source.
Do not execute notebook setup or full-game evaluation cells to build it.

Build from the repository root:

```bash
uv run --no-sync python -m scripts.make_public_v36 \
  --output artifacts/submission-cycle-14-v36/main.py
```

The builder refuses changed upstream bytes and existing output files. It does
not import the policy, start a game, use a network API or upload to Kaggle.
The earlier protected `main.py`, Cycle 12 and Cycle 13 remain separate.

The policy itself includes a bounded final-seven-turn physical planner. An
actual Kaggle game may invoke that planner at step 712. Local artifact checks
avoid this step; no local matches are required to package the source.

The user reports a public score of 2705.7. That is not a rating guarantee for
this artifact or our account. The next evidence is Kaggle validation and games.
See [Cycle 14 release notes](../../docs/CYCLE_14_RESULTS.md) and the
[strategy/CO review](../../docs/V36_NOTEBOOK_REVIEW.md).
