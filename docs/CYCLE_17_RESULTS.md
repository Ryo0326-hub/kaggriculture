# Cycle 17 — custom shared growth candidate

Implemented at the user's request to complete the custom policy's known growth
repairs, incorporating the new loss to Sergey Panasenko. This candidate extends
Cycle 15; it is separate from the unchanged public V36 packaged as Cycle 16.

## Upload

Artifact: `artifacts/submission-cycle-17-shared-growth/main.py`.

SHA-256: `96297a3e899d77bbb5f0ec0299da34418bbdf9c62d999738df39da7a4237c6ea`.

```bash
/Users/ryokitano/.local/bin/kaggle competitions submit kaggriculture \
  -f /Users/ryokitano/Documents/Projects/kaggriculture/artifacts/submission-cycle-17-shared-growth/main.py \
  -m "Cycle 17 - shared routes and funded growth - 96297a3e899d"
```

The user performs this upload. Server validation and competitive performance
are pending; there is no claimed rating or 150K-coin result. Root `main.py` is
still protected Cycle 3, so use the full artifact path above.

## Implemented

- One shared route constructor for crops, animals and installations, used in
  economic admission, staffing and dispatch. Ordinary days use automatic night
  deposits; the final day reserves a complete delivery chain.
- Known demand remains a floor in both future scenarios. Candidate values charge
  own market impact, land, inputs, Fibonacci wages and early installation costs.
- Compact preferred livestock sites plus overflow onto vacant fields remove the
  former twelve-animal layout ceiling. All four land quadrants are eligible.
- Positive estimated value and dated cash feasibility govern larger batches;
  additional workers are priced up to a 17-total-worker search bound.
- Shared input/seed/site reservations, mandatory maintenance, correct care bonus
  timing, inventory pressure relief and same-turn deposit/sale accounting.

Read [the game analysis and CO implementation notes](CYCLE_17_OPTIMIZATION.md).

## Verification

- **67 bounded tests pass:** 22 new growth checks and 45 frozen parent/public
  packaging checks. These files do not import the simulator.
- **78 independent recorded-observation checks pass:** both seats at thirteen
  fixed decisions in each of episodes 107999948, 108000970 and 108005959.
  Checks cover action preconditions, shared inputs, seed counts, duplicate tile
  assignments, deposit capacity, sales, action counts, serialization and unchanged
  observations. Route caches are cleared before each call.
- Largest sampled callback: **0.312214 seconds** against the recorded one-second
  action limit. Startup: 0.022862 seconds. This is local sampled timing, not a
  cloud worst-case guarantee.
- Ruff, formatting, compilation and parent artifact integrity checks pass.
- All 719 own actions in the newly supplied Sergey game match Cycle 15 exactly;
  this identity check is separate from checks on the new candidate.

[Recorded check report](benchmarks/cycle-17-checks.json) ·
[Sergey evidence](benchmarks/cycle-17-sergey-analysis.json).

No local matches, engine imports, game advances, counterfactual episodes,
training, API model calls or paid compute were used. Independent decisions on
another player's recorded observations are interface checks, not matches.

## Reproduction

```bash
uv run --no-sync python -m scripts.make_growth_agent \
  --output artifacts/submission-cycle-17-shared-growth/main.py
```

The builder refuses to overwrite existing files. It reproduces and checks the
frozen Cycle 15 hash before adding the new helpers. The committed builder and
source reproduce the ignored upload artifact on another checkout.

## Preserved sources

Cycle 15: `ce4444126f5ef7e0ee01a22f395ae87ee442ec2f329c4feb6aedf0687af45f1a`.
Cycle 13: `542547dbe7cd63856b2a6f037e2014790c1410316c3b3872f67ea85c2b628947`.
Public V36 / Cycles 14 and 16:
`7eb5ab6c48581c82906ab6fa6b2cc5c9607513249ef59b2c45fcd6176e8653dd`.

The existing submissions keep running. The new upload replaces the older active
slot under Kaggle's latest-two rule; it does not alter the running Cycle 15.
