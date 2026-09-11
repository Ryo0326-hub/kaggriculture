# Cycle 13 — user reports submission; server validation pending

September 11, 2026. The user requested an integrated challenger informed by five Majkel1337 games and then two Gekkotron games, explicitly adapting our existing strategy. Competitive evaluation remains on Kaggle; no local match simulations were run.

## What is ready

The reproducible Cycle 13 builder extends exact Cycle 12 bytes with staged livestock space, four additional opening wheat seeds, shared herd routes, workload-based staffing, marginal production/land choices under demand/supply uncertainty, actual goose purchasing, tomato handling and selected age-three wheat harvests. It keeps the existing carrot fertilizer coordination, strawberry timing, ledger, feed, sale and terminal delivery paths. [Full study](CYCLE_13_SERVER_STUDY.md) · [CO/economic notes](CYCLE_13_OPTIMIZATION.md).

Artifact: `artifacts/submission-cycle-13-throughput/main.py`.

SHA-256: `542547dbe7cd63856b2a6f037e2014790c1410316c3b3872f67ea85c2b628947`.

Its parent Cycle 12 hash is `555c312fc2c09c61c5f0081c4b4148446f5794eddaa1a71427a07b11d4057d34`. Protected `main.py` and `baselines/cycle_3.py` remain byte-identical at `47c281bfb4118a9755f1759930b162de007efdfef3b23144457eccbaac42da0c`.

The new artifact is a server-test candidate, not a promoted incumbent. **On September 11, Ryo reported submitting the latest version.** The submission ID, uploaded-byte identity, server validation and resulting games have not yet been independently confirmed. No submission was uploaded automatically, no fresh rating was fetched, no API key was used and no cloud compute was purchased. The source is standard-library Python; the builder assembles the file locally without a simulator.

The subsequent [V36 public notebook review](V36_NOTEBOOK_REVIEW.md) identifies marginal-impact sale ordering as a potential next bounded challenger. It leaves this artifact unchanged while awaiting its server evidence.

## Checks completed

- Sixteen focused tests pass, without engine imports or game stepping: preserved opening, staged land geometry, wheat harvest/forecast agreement, tomato lifecycle and fertilizer timing, shared herd route coverage, goose feed/output accounting, demand-gated menus, cash/order/pending/terminal admission, terminal sales, market saturation, land cost and added Fibonacci wages.
- Fifty-six isolated calls on recorded observations pass serialization, hand-count, order-count, observation-immutability and sampled timeout checks. The maximum sampled time is **0.0397 seconds**. [Artifact check](benchmarks/cycle-13-artifact-check.json).
- Repository lint, formatting and Python compilation pass.
- All seven supplied focal-player episodes were analyzed through JSON state differences. The analyzer never invokes the game engine or a bot.

The recorded-observation calls are interface/performance probes, not new episodes and not evidence that our policy would have created those farms. Sampled timing is not a worst-case runtime proof. We have not measured this candidate's win rate, 30-day own trajectory, server runtime or rating. Forecasted staffing feasibility remains approximate, particularly on crowded farms.

## Build and upload

The commands below remain for reproducibility. Ryo has reported uploading the latest version; no repeat upload is needed for this documentation-only review.

To reproduce after cloning, from the repository root:

```bash
uv run --no-sync python -m scripts.make_throughput_agent \
  --output artifacts/submission-cycle-13-throughput/main.py
```

The builder verifies its parent source hash and refuses to overwrite an existing output file. The packaged file already exists on Ryo's current machine. **Upload the candidate path below, not the repository-root protected `main.py`.** The installed Kaggle CLI takes the competition as a positional argument:

```bash
/Users/ryokitano/.local/bin/kaggle competitions submit kaggriculture \
  -f /Users/ryokitano/Documents/Projects/kaggriculture/artifacts/submission-cycle-13-throughput/main.py \
  -m "Cycle 13 - throughput - 542547dbe7cd"
```

The user will return Kaggle validation/gameplay logs. First verify artifact identity and server success. Then inspect productive footprint and its timing, feed/water failures, idle reserved land, input queues, wages, delivery/overflow, product mix, shared prices and terminal stock. Keep outcome, absolute coins, efficiency and rating separate. If the larger portfolio misses maintenance, fix scheduling/admission before increasing scale further. If output is clean but margins remain weak, investigate sale timing and cannibalization.

The original numbered engineering checkpoints are complete; this is evidence-driven **Cycle 13**, not another prerequisite before a first end-to-end agent. A 3000 rating remains an unverified competitive objective. No cloud training or Featherless access is needed for this release.
