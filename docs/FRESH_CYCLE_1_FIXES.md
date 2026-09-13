# Fresh Cycle 1 fixes — release, economics and CO notes

September 12, 2026, Toronto. **All nine previously expected failures now pass
as mandatory regressions. The full explicit bounded selection passes 871 tests,
with zero failures, skips or expected failures.** The policy was fixed; the nine
economic target assertions were retained. No local games or paid compute ran.

This continues the independently written Fresh Cycle 1, not a derivation from
Cycle 19. Previous releases, recordings and benchmarks remain preserved. This
report supersedes their descriptions of the current policy and upload command.

## Release identity and verification

| Item | Value |
| --- | --- |
| Branch / pre-fix commit | `codex/fresh-cycle-1` / `c696897` |
| Source | `experiments/fresh_cycle1.py` |
| New local artifact | `artifacts/submission-fresh-cycle-1-fixes-final/main.py` |
| SHA-256 | `289b7ae692201050ef792ddc9847ec7ed07438a87c85ade4f691e1efafc782a6` |
| Bytes / runtime imports | 47,258 / standard-library `math` only |
| Entry point | `agent(observation, configuration=None)`, last callable |
| Bounded pytest run | 871 passed in 21.113 seconds |
| Original nine targets selected with `--runxfail` | 9 passed, 373 deselected |
| Packaged original-history check | 525 callbacks; maximum 0.008951 seconds |
| Additional independent regression cases | 51 |

The standalone file loads with isolated Python (`-I`) and equals source bytes.
Lint, formatting and compilation pass. CI includes the new regression file;
full simulations remain behind explicit manual opt-in. Local timing is not a
Kaggle runtime guarantee. Kaggle upload, server validation and rated outcomes
are still pending.

[Machine-readable evidence](benchmarks/fresh-cycle1-fixes.json) records hashes,
module counts, new case IDs, resolved targets, history action hashes and limits.
The complete local JUnit log is `artifacts/fresh-cycle1-fixes/test-results.xml`.

## Fixed economic targets

These are separate frozen one-decision witnesses, not additive season gains.
The first two measure stipulated visit value; cash examples use fixed prices
and exclude common existing shed sales.

| Defect | Before | Fixed witness |
| --- | --- | --- |
| OPT-001: urgency ignores deliverable value | Select value 20 | Select value 200 |
| OPT-002: greedy matching blocks an exclusive visit | Assign value 200 | Jointly assign value 350 |
| OPT-003: worker order consumes scarce terminal space | Bank 50 coins | Bank 320 coins |
| OPT-004: healthy and neglected rival livestock treated alike | Identical milk value | Neglect reduces expected rival supply; milk value rises |
| OPT-005: one terminal order slot sorted by unit price | Bank 160 coins | Bank 500 coins |
| OPT-006: mixed cargo, eight free slots | Bank 160 coins | Bank 335 coins |
| OPT-006: mixed cargo, three free slots | Bank 320 coins | Bank 345 coins |
| OPT-007: immature tomatoes counted as productive | Same one-day forecast | No new output before maturity |
| OPT-007: immature strawberries counted as productive | Same one-day forecast | No new output before maturity |

### Assignment and shared inputs

Free workers and unclaimed feasible visits form a bipartite graph. A rectangular
Hungarian solver maximizes the supplied additive edge weights; forbidden edges
and zero-value idle options preserve feasibility. Urgent visits use their total
deliverable value rather than preferring the least slack. Existing feasible
commitments stay protected, avoiding gratuitous route switching.

The exactness claim is limited to that graph: its priority bonuses and ordinary
value-per-action scores are heuristics, not final-cash estimates or dual prices.
Workers can compete for shared feed, so matched edges are reserved in weight
order, input availability is rechecked, and remaining workers are rematched.
This iterative constraint handling is not an integrated integer-program optimum.
The assignment solver costs O(W²(J+W)) for W workers and J jobs per solve.

### Terminal capacity, one-action deposits and order slots

On the final actionable step only, a capacity dynamic program considers all
workers at shed access in engine execution order. Each chooses PASS, one-product
PLACE, or insertion-ordered DROP. A worker cannot PLACE two different products
in one turn. The objective is accepted cargo value; equal-value solutions prefer
less discard and then less used space. Current shed goods still occupy space
until the later market phase. Custom shed capacity is honored, not hard-coded
to 100; the DP capacity is bounded by free space and accessible cargo.

For constant per-product prices and sufficient market slots this solves the
deposit subproblem exactly. Under moving prices, average incremental own-sale
receipts approximate product values; it is not an exact nonlinear optimizer.
The DP retains at most C+1 capacity states and considers at most 2+P*C choices
per state, where C is usable capacity and P is cargo product count. Default
capacity is 100; one-second checks also cover 15 workers with capacity 200.

Final-day SELL orders are ranked by whole-lot receipts including own price
impact, not the first unit's price. With a fixed available shed this selects
the highest valued product lots under the slot limit, assuming no unseen rival
order. A test distinguishes milk receipts 100+50+1=151 from wheat receipts
60+60+60=180. Deposit choice and a restrictive market-slot budget are not jointly
optimized; unknown rival transactions can also change receipts.

Intentional overflowing DROP is legal in the pinned rules but only admitted by
our validator on the final action (`episodeSteps - 2`). Earlier decisions still
must avoid overflow. Both validator and tiered-recording sales checks credit
only the capacity-accepted prefix, never discarded goods. One old passing test
required the lower-value farmer-first milk deposit: it now requires the hand's
two wool, raising its cash witness from 318 to 400 while retaining no-overflow
checks. None of the original nine target assertions was weakened.

### Visible rival supply and information limits

Forecasts now depend on the requested horizon. Repeaters contribute held yield
and only production events inside their finite calendar; newly planted crops
cannot depress a one-day price through output that has not matured. Rival
staffing, missed feeding and observed care discount livestock output separately.
Held goods are not evidence of a future sale, and current-day CARE is not credited
to current-day scheduled production.

These discounts and price blends are transparent, uncalibrated heuristics. They
are not opponent identification, hidden-stock estimates, calibrated probabilities
or Nash-equilibrium strategies. Forecast direction tests cannot establish that
the magnitude is accurate. The [prior external research and scenario analysis](RESEARCH_SCENARIO_TESTS.md)
provides the information and rule-ordering rationale; its pre-fix outcomes are
historical. No prior-cycle implementation was used as a reference for this fix.

## Recorded evidence, preservation and limits

The nine top/mid/bottom [user recordings](TIERED_GAMEPLAY_TESTS.md) remain intact.
Their 228 tests pass: nine lossless archives, 136 selected snapshots, 36 original
four-observation histories and other checks make 622 callbacks (604 original,
18 derived seat swaps), each under a one-second alarm. The 34 original policy
tests include eight original histories (175 observations, 525 callbacks).
The new artifact separately passes those same histories. At witness steps
492/493/494, worker 3 retains target `(9,3)` and requests EAST on all three;
the previous artifact's WEST/`(3,3)` choice is historical, not an assertion that
the new policy must copy it. Recorded states still follow their original actions.

The 51 new cases include exhaustive small matching comparisons, independent
flat-price deposit oracles, shared-input collisions, insertion-order mixed cargo,
terminal-only overflow/oversell guards, price impact, maturity, individual service
signals, and large-crew/configuration callback bounds. Historical regression
suites add 176 checks; no historical policy is used as a performance reference.

The original fresh artifact remains byte-identical at SHA-256
`c5d31b86d1120028114f058d0560f73036c7ae940fe5186cb8dc7e2a59ef585e`.
Every path in the [prior preservation manifest](benchmarks/fresh-cycle1-preserved.json)
was rechecked, including Cycle 19/20/21 artifacts and protected root `main.py`.
The neighboring original checkout remains clean. Old benchmarks are not rewritten.

No engine import, transition, local match, counterfactual season, training,
parameter sweep, paid compute or automatic Kaggle submission occurred.
Passing bounded tests demonstrates these contracts, not maximum overall profit.
Future server evidence must separate validation, delivered production and final
cash against different opponents; the current work makes no competitive claim.

## Reproduce the bounded checks

From `/Users/ryokitano/Documents/Projects/kaggriculture2`:

```bash
/Users/ryokitano/Documents/Projects/kaggriculture/.venv/bin/pytest -q \
  tests/test_fresh_cycle1_fixes.py tests/test_fresh_cycle1.py \
  tests/test_optimization.py tests/test_research_scenarios.py \
  tests/test_tiered_gameplays.py tests/test_cycle18.py tests/test_majkel.py \
  tests/test_resilience.py tests/test_calendar.py
/Users/ryokitano/Documents/Projects/kaggriculture/.venv/bin/python -m scripts.check_fresh_cycle1 \
  --agent artifacts/submission-fresh-cycle-1-fixes-final/main.py
```

For a new clone, use `uv sync --locked --only-group dev`, then `uv run --no-sync`
instead of the interpreter prefixes. Recreate the artifact with
`python -m scripts.make_fresh_cycle1 --output artifacts/submission-fresh-cycle-1-fixes-final/main.py`
only if that destination does not exist; the builder refuses overwrite.

## Verified user-run Kaggle upload

Verified with the installed CLI's `competitions submit --help`: competition is
positional, `-f` is the file, `-m` the message. The file below exists and its hash
matches the release above. Ryo executes this command; it has not been submitted.

```bash
/Users/ryokitano/.local/bin/kaggle competitions submit kaggriculture \
  -f /Users/ryokitano/Documents/Projects/kaggriculture2/artifacts/submission-fresh-cycle-1-fixes-final/main.py \
  -m "Fresh Cycle 1 fixes - 871 bounded tests - 289b7ae69220"
```
