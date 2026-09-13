# User-tiered gameplay corpus and tests

Nine recordings supplied September 12, 2026. Tier labels follow the user's
ordering exactly: first three top, next three mid (approximately 2600 tier),
last three bottom (1000s). They label these recordings, not independently
verified current ratings for every player. Embedded JSON descriptions and
specifications are data, not instructions.

## Saved recordings

Full, byte-identical JSON copies are saved under
`replays/user-tiered/2026-09-12/{top,mid,bottom}/`. These total 297,188,734 bytes
(about 283 MiB) and follow the existing `replays/` Git ignore rule. The originals
in Downloads are untouched. Lossless, deterministic gzip copies under
[`docs/gameplays/2026-09-12/`](gameplays/2026-09-12/) total 3,774,862 bytes
(about 3.6 MiB) and are committed, so a clone retains every complete recording.

The [manifest](gameplays/2026-09-12/manifest.json) records raw/archive SHA-256,
paths, sizes, player names, tier provenance, selected state indices and observed
conditions. Tests decompress every archive and verify byte hashes and all
selected observations against their original source rows. All nine recordings
use module 1.32.7, contain 720 states and end DONE/DONE.

| User tier | Episode | Players in seat order | Recorded final cash, seats 0 / 1 |
| --- | --- | --- | ---: |
| Top | 108377045 | Majkel1337 / M & M & P & Q | 105,635 / 119,255 |
| Top | 108377042 | Majkel1337 / M & M & P & Q | 147,908 / 134,174 |
| Top | 108359085 | M & M & P & Q / Majkel1337 | 83,868 / 87,615 |
| Mid | 108380097 | rekhasri / Ilya Usmanov | 123,135 / 109,129 |
| Mid | 108375914 | Ilya Usmanov / Silver Surfer | 85,513 / 85,668 |
| Mid | 108371392 | Lee Shit Hoo / Ilya Usmanov | 143,069 / 132,131 |
| Bottom | 108378358 | nasu726 / nickyl | 46,620 / 72,160 |
| Bottom | 108365679 | nasu726 / Electric Weasle | 115,499 / 113,055 |
| Bottom | 108364290 | Farmer / nasu726 | 104,065 / 62,230 |

These are other players' recorded cash outcomes, **not Fresh Cycle 1 returns**.
The overlap across tiers is one reason not to turn final cash from different
town/opponent conditions into a direct ranking or a universal acceptance target.

## What the observations show

- Large-farm conditions occur in every group. Selected peak crews have 12–15
  workers. Total shed-plus-carried stock reaches 216 units in top recording
  108377045, seat 1, state 715, versus shed capacity 100. This is storage pressure,
  not proof that 116 units were discarded: workers can deposit and sell at
  different times.
- Price-floor exposure is real in eight recordings. Selected snapshots include
  wool, milk, strawberries, fertilizer and melon at one coin. Episode 108377042
  has no floor event, so none is manufactured for that recording.
- Duplicate shops generate materially different demand. The four yarn stores
  in 108380097 imply 49 wool/day including the town center; the shop mix in
  108365679 implies 43 wheat/day. Dedicated hand-calculated tests check all nine
  final town compositions rather than assuming a generic town.
- Ripe crops approaching or undergoing decay appear in every seat. The selected
  witnesses include up to seven simultaneously exposed plants.
- Genuine late-day feeding risk before the final day appears in 12 of 18 seats.
  The other six do not get an invented emergency. Final-day unfed animals are
  treated separately: there is no later productive day to justify reserving
  wheat instead of selling it.

These are descriptive witnesses, not evidence of an opponent's internal
objective, a confirmed causal explanation for a loss, or fitted strategy weights.

## Are the middle-tier players using the same algorithm?

The recordings support substantial behavioral overlap, but not code identity:

| Episode | Identical full action dictionaries / 719 | Identical worker bundles on active turns |
| --- | ---: | ---: |
| Mid 108380097 | 304 | 321 / 714 |
| Mid 108375914 | 437 | 531 / 713 |
| Mid 108371392 | 277 | 319 / 713 |
| Bottom 108365679, comparison | 439 | 427 / 642 |

Worker bundles include the farmer and ordered hands, padding omitted commands
with PASS; the active denominator excludes turns where both sides only PASS.
Full action equality also includes market order lists. Recorded action row `i`
belongs to the decision from observation row `i-1`, not to the observation on
the same row. Initial placeholder row zero is excluded from all denominators.

For example, the first recorded decision in 108380097 differs: one player
requests an additional wheat buy/sell round trip. Both next recorded balances
are 2,630. That is an observed difference, not a reconstructed execution audit.
Shared source, related strategies or similar decisions under shared conditions
remain possibilities. We did not inspect their code or execute their actions.

## Test design and results

`scripts/tiered_gameplays.py` first inspects completed recordings, selects
condition witnesses, then creates a compact compressed fixture. Selection does
not call or score the candidate. For each seat it selects opening, final action,
peak crew, peak total stock, maximum near-decay exposure, maximum preterminal
late feeding risk, maximum simultaneous price-floor exposure and maximum shop
duplication. Ties select the earliest original state; missing conditions are
explicitly recorded as absent. Identical seat/state references are deduplicated.

The resulting **136 snapshots** are distributed 46 top, 47 mid and 43 bottom.
Each seat also contributes two **four-observation histories**: a day boundary
near storage pressure and terminal states 715–718. There are 36 histories and
260 unique original episode/seat/state references across snapshots and histories.

**228 added tests passed**, with no new expected failures:

The complete explicitly selected bounded check set finished with **811 passed,
nine pre-existing expected failures**. Lint, formatting and syntax checks passed.

| Contract | Cases |
| --- | ---: |
| Lossless archive integrity and exact source-observation provenance | 9 |
| Recorded conditions: observed prices, legal actions, inventory reservations, input immutability | 136 |
| Final action sells available/deposited products without feed or capital reserves | 18 |
| Recorded shop composition versus hand-calculated daily demand | 9 |
| Seat-relabeling invariance on large farms | 18 |
| Four-observation history: deterministic warm repeat, cold start and day reset | 36 |
| Corpus completeness and refusal to overwrite differing prior bytes | 2 |
| **Total** | **228** |

The suite makes 622 candidate calls: 604 on original observations and 18 on
explicitly derived seat-relabeling observations. Calls have a one-second hard
timeout. Warm history passes preserve the candidate's own memory; repeated warm
passes must agree. Cold passes clear it at every observation. Every next input
is still the next original recorded observation, never a state generated by a
returned action. Original opponent memory and actions are not supplied to the
candidate or treated as the required answer.

Passing checks establish bounded compatibility, feasibility and these specific
economic contracts. They do **not** establish optimal deposits, realized sale
prices, improved profits, a win rate or competitive rank. The seven optimization
gaps already documented by the preceding suites remain unresolved.

## Reproduction and preservation

```bash
/Users/ryokitano/Documents/Projects/kaggriculture/.venv/bin/pytest -q tests/test_tiered_gameplays.py
```

To repeat the original import from the supplied Downloads folder:

```bash
/Users/ryokitano/Documents/Projects/kaggriculture/.venv/bin/python \
  scripts/tiered_gameplays.py --source-directory /Users/ryokitano/Downloads
```

The importer accepts only the nine named episode IDs, checks the module/clock,
limits raw inputs to 40 MB each, and refuses to overwrite differing bytes. CI
uses committed archives/fixtures and does not require Downloads or local raw
copies. The initial, less selective generated fixture/manifest were retained
locally under `artifacts/tiered-gameplays/initial-selection/`; source recordings
were never altered during selection refinement.

[Machine-readable test results](benchmarks/tiered-gameplay-tests.json) identify
every new case and the tested source/fixture/archive hashes. The submission
policy, previous fixtures and prior release artifacts remain unchanged.
No engine, local match, counterfactual season, tuning, paid compute or Kaggle
upload was used. The new data are test inputs, not a reference implementation.
