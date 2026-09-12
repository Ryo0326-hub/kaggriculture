# Cycle 18 — second pre-submission audit

The extra audit found defects that the first 27 checks did not cover. They were
reproduced against the exact earlier release (`6d3cbf383297…`) and repaired in
the final candidate (`65e0e1f6f12e…`). The earlier upload command is superseded;
use [the final release command](CYCLE_18_RESULTS.md).

## Reproduced failures and corrections

| Fixed observation | Earlier release | Corrected release |
|---|---|---|
| Unwatered ongoing tomato, one move away, two ordinary actions left | PASS because travel + water + harvest would take three actions | Move toward the plant; water-only service fits the deadline |
| Unfed cow, two moves away, three ordinary actions left, feed carried | DROP feed because feed + care + collection + travel would not fit | Move toward the cow; feeding alone fits |
| Final day, nearest worker occupied carrying an animal; another worker can reach, harvest and deposit | Other worker PASS because water + harvest + delivery would be late | Assign harvest-only work to the available worker, preserving delivery time |
| Observation omits optional `step` | `KeyError: 'step'` | Derive the action budget from day and hour; preserve the input observation |
| Full carried animal load, only one depot slot, worker on empty matching pasture | `PLACE COW 1` booked as a deposit, although the engine installs an animal there | Skip that ambiguous partial deposit; market sales can still clear space |
| Inventory contains zero MILK plus two COW; one depot slot, no matching pen | PASS after selecting zero MILK as the highest-value product | Ignore zero quantities and deposit one cow safely |

These are fixed synthetic counterexamples, not claims that each defect occurred
in a supplied server episode. In particular, the missing-step crash is an input
robustness failure; it does not establish that Kaggle omitted the field during
live callbacks. The final-day deposit examples exercise leftover animal inventory
and do not claim animals can be sold for endgame revenue.

[Machine-readable before/after actions and observations](benchmarks/cycle-18-audit-regressions.json).

## Scope of the code review

The live `production_turn` call path was traced through jobs, route assignments,
carried stock, depot reservations, sale/purchase ordering, hiring and investment.
Checks used the pinned 1.32.7 game source for unit-before-market ordering, the
719-action horizon, ordinary night deposits, explicit final delivery, feeding,
watering and the overloaded animal `PLACE` operation. No engine was imported.

The fix retains feasible complete service bundles, shared stock reservations,
plant/install first-maintenance requirements, final delivery and the existing
investment objective. The route constructor's 36 equivalence cases still pass.
The Soumic decision-340 investment diagnostic is unchanged: two cows are admitted
and additional melon cohorts are rejected. That remains a forecast, not profit.

The independent command checker was also corrected to distinguish animal
installation from legal animal deposits on ordinary or locked shed-access tiles.
It now checks board boundaries for movement. This prevents validation from
misclassifying a legal partial deposit or overlooking a move off the board.

## Release evidence and limits

- 40 bounded regression tests pass, including all newly reproduced failures.
- 140 independent recorded-observation checks pass on the final source: both
  seats at fourteen fixed states from each of the five reviewed games.
- Largest sampled callback is 0.413041 seconds against the one-second configured
  action limit; startup is 0.038634 seconds. These are local samples.
- Lint, formatting, syntax, standard-library packaging, final `agent` discovery,
  deterministic rebuild and frozen-parent integrity checks pass.
- Default CI now includes the bounded tests; full gameplay tests remain manual
  opt-in. No local match, replay advancement, training or paid compute was used.

All defects reproduced in this audit are repaired. These checks cannot establish
that every reachable game state is bug-free or that the candidate beats Cycle 15.
Kaggle validation and the candidate's own games remain the next evidence source.
