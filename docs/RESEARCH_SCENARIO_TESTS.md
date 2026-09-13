# Research-led scenario tests

**Historical pre-fix report.** The original artifact and benchmark below remain preserved. The [Fresh Cycle 1 fixes release](FRESH_CYCLE_1_FIXES.md) supersedes its policy, results and upload command: all nine formerly expected failures now pass as mandatory regressions; the full bounded selection passes 871 tests.

Research and scenario selection completed before test implementation, September
12, 2026 Toronto (02:02 UTC September 13). This extends, rather than replaces,
the 245 cases in [OPTIMIZATION_TESTS.md](OPTIMIZATION_TESTS.md).

## External research and rule verification

1. [Kaggle's official rules](https://github.com/Kaggle/kaggle-environments/blob/master/kaggle_environments/envs/kaggriculture/README.md)
   describe hidden rival inventories, random shop draws with replacement,
   finite recurring-crop production, nonlinear scarcity prices, and cash-only
   terminal scoring. These motivate uncertainty, lifecycle and liquidation
   tests; public farm capacity is not a promised rival sale.
2. [Official engine source, pinned to its last-change commit](https://github.com/Kaggle/kaggle-environments/blob/28b6d8af3ce73926b3d0fda1410c1ddd8384ab8c/kaggle_environments/envs/kaggriculture/kaggriculture.py)
   was fetched read-only and compared with the pinned 1.32.7 source. Both SHA-256
   hashes are `bc8a54879ef02c7ea64b8b333d6a976f0ea65c4949149d01f463f23bccee653e`.
   Unit actions precede market orders; town consumption follows them. Market
   queues have a configurable limit. Floor-price sales do not increase public
   inventory. CARE earned today is banked **after** today's scheduled animal
   production; it cannot augment that same payout. Source ordering resolves
   ambiguity in the prose. No engine was imported or executed.
3. [NEOS Guide: Stochastic Programming](https://neos-guide.org/guide/types/stochastic/)
   explains nonanticipativity: today's choice is common across unresolved
   future scenarios, while later recourse may depend on revealed information.
   A scenario-by-scenario best choice is a perfect-information upper bound,
   not an achievable pre-revelation policy.
4. [Bertsimas and Sim, The Price of Robustness (2004)](https://pubsonline.informs.org/doi/10.1287/opre.1030.0065)
   motivates making the cost of conservatism explicit. Expected profit and
   worst-case protection answer different questions. Our small discrete stress
   sets do not implement their robust LP reformulation or its probability bounds.

The README link is mutable; the engine link and hash identify the mechanics
reviewed. No opponent implementation or previous-cycle policy was used as a
reference. Scenario payoffs below are declared assumptions, not fitted returns
or claims about a particular competitor.

## Scenario analysis, specified before creating tests

| Scenario and plausible cause | Economic failure to detect | Bounded check |
| --- | --- | --- |
| Several demand-focused shops exhaust ordinary supply | Extrapolating a mild scarcity slope beyond its knee | Independent closed-form hinge values before, at and beyond the knee |
| Different consumption cadence or observation-provided market parameters | Valuing assets against the wrong demand or price specification | Exact rates and authoritative observed-parameter checks |
| Rival plants are newly planted, productive or exhausted | Counting output before it can mature or after its last production | Fixed lifecycle snapshots and near-term forecast comparisons |
| Livestock need survival feed while holding valuable output | Taking cash now destroys future productive capital; CARE displaces collection | On-site last-hour action priorities and held-output checks |
| One terminal order slot remains for a small premium lot or large staple lot | Sorting by unit price instead of total bankable receipts | Exact subset selection under an order cap; neutral controls |
| A worker carries mixed products into a nearly full terminal shed | Highest unit price is not highest feasible deposit value | Enumerate DROP or a single-product PLACE, never multiple actions |
| Final day has a different clock or ends part-way through a day | Reserving feed or buying capital after its remaining value disappears | Final actionable snapshots across explicit configurations |
| Rival holds, sells in parallel or has already sold first | Ignoring queue timing and price impact | Closed-form one-order receipt comparisons; no market replay |
| Public inventory stays flat during an unseen dumping episode at the floor | Treating unchanged public inventory as proof of no trade | Liquidation remains valuable across alternative hidden sale quantities |
| Future shop favors berries or dairy, but has not been revealed | Selecting a different investment using tomorrow's answer | Expected-profit decision versus perfect-information upper bound |
| Feed scarcity and output-price collapse occur together, separately or independently | Mistaking equal marginal risks for equal portfolio downside | Same-marginal payoff tables with different joint distributions |
| One extra crew slot, tile or cash block becomes available | Assuming a fixed work penalty equals the value of scarce resources | Exact finite-difference integer resource values at binding thresholds |

A policy test must use only its supplied observation. An economic oracle must
not ask the policy for the expected answer. Exact optimum claims apply only to
the explicitly bounded decision model; comparative statics are weaker checks.
New unmet policy targets will be reported separately, not accepted by relaxing
assertions. The policy and submission bytes remain protected.

## Results

Added **137 individually named cases: 132 passed, five strict expected
failures**. Of these, 101 exercise the candidate or its components; 36 check
independent economic models and oracle bounds. Combined with the original 245
optimization cases, there are **382 economic cases: 373 pass, nine expected
failures**. Those nine cases identify seven distinct gaps, not nine distinct
bugs. Including the original 34 Fresh Cycle 1 tests gives 407 passed and nine
expected failures, with 525 callbacks on original recorded observations.
The full explicitly selected bounded set, including 176 historical regression
checks, finished with **583 passed, nine expected failures**. Lint, formatting
and syntax checks also passed.

| Coverage family | New cases |
| --- | ---: |
| Nonlinear scarcity knee and authoritative observed price parameters | 21 |
| Eight duplicate shops with alternative demand clocks | 16 |
| Crop production windows, retired rivals and immature-rival targets | 20 |
| Survival feeding and collection before optional CARE | 12 |
| Final-action liquidation on four season/day clocks | 12 |
| Market-slot and mixed-deposit policy contracts | 16 |
| Rival queue position and liquidation at the price floor | 10 |
| Nonanticipativity, information value and correlated shocks | 8 |
| Integer resource thresholds and resource complementarity | 7 |
| Hand-calculated oracle witnesses and hard input bounds | 15 |
| **Total** | **137** |

## New unmet targets

| ID | Cases | Actual versus independently feasible value | Scope |
| --- | ---: | --- | --- |
| OPT-005 | 1 | 160 versus 500 coins | One configured terminal market slot; one milk versus 20 wheat |
| OPT-006 | 2 | 160 versus 335; 320 versus 345 coins | One worker, mixed cargo, nearly full shed |
| OPT-007 | 2 | Tomato forecast 54.0 in both states; strawberry 111.6 in both | One-day forecast ignores newly planted versus next-day productive rival crops |

OPT-005 uses constant native-base prices and `maxMarketOrdersPerTurn=1`.
This is an allowed configuration stress, **not** evidence of that exact loss
under the default ten-order cap. Selling the larger wheat lot yields 340 more
coins than selling one milk. Separate equal-lot controls pass with one, two
and three slots.

OPT-006 uses default shed capacity, fixed native-base prices and the default
order allowance. The first state has 92 fertilizer in the shed and a worker
carrying one milk followed by eight wheat. The policy places only milk for 160;
DROP can bank milk plus seven wheat for 335, discarding one wheat that has no
terminal value. Even a non-overflowing PLACE of eight wheat banks 200. The
second state has 97 fertilizer, two milk and two wheat; DROP banks 345 versus
the policy's 320. Existing shed fertilizer sales are common to both choices
and excluded from the comparison. These differences are not additive across
states or proof of season profit improvement.

The existing action validator deliberately rejects overflowing DROP. The
candidate still obeys it. The independent terminal oracle includes the
engine-legal overflow choice using insertion-order prefix sums; it neither
executes DROP nor constructs a next observation. A future fix allowing
intentional terminal overflow would also need an explicitly scoped validator
update. No such policy/validator change was made here.

OPT-007 requires only a defensible directional forecast, not an exact future
price. Twelve newly planted repeaters cannot produce within the next day;
otherwise comparable crops just before first production can. Unknown rival
private stores remain unknown in both states. No hidden stock or future shop
draw is supplied to the agent.

## Economics and CO interpretation

The terminal order problem is a tiny subset selection: choose product orders
to maximize **quantity times constant price**, subject to available order
slots. The oracle enumerates at most 512 subsets of nine products. The deposit
problem differs: one worker has one action, so independent quantities of many
products cannot be selected as if each had its own worker. The alternatives
are PASS, a single-product PLACE, or the engine's insertion-ordered DROP.

The information test has declared profits of `(140, 0)` for berries, `(0, 140)`
for dairy, and `(60, 60)` for a flexible plan. With equally likely unresolved
shop scenarios, either specialist earns expected profit 70; perfect information
would earn 140. Crediting the latter to today's choice would leak the future.
These are toy profit assumptions, not fitted crop returns. They implement the
distinction motivated by NEOS, not a multi-stage farm solver.

The correlation checks hold each shock's marginal probability at one half.
A risky portfolio earns `100 - 70*feed_shock - 70*output_shock`, so expected
profit is always 30. Its worst outcome is -40 when both shocks can coincide,
but 30 when they are mutually exclusive. A fixed reserve earns 20. Expected
profit selects the risky portfolio in all three cases; maximin selects the
reserve only when both shocks are possible. That sacrifice is explicit, not
automatically called profit optimization or a Nash equilibrium.

Integer resource tests compare exact feasible selections before and after a
small capacity change. Extra cash may have zero value until enough labor is
also available. In one example, relaxing either cash or labor alone adds zero,
but relaxing both adds 50. Such finite differences are not LP dual prices and
do not justify a constant per-action penalty in all farm states.

## Reproduction and boundaries

```bash
/Users/ryokitano/Documents/Projects/kaggriculture/.venv/bin/pytest -q -rx tests/test_research_scenarios.py
```

To expose the five targets as ordinary failures:

```bash
/Users/ryokitano/Documents/Projects/kaggriculture/.venv/bin/pytest -q \
  tests/test_research_scenarios.py -m optimization_gap --runxfail
```

The latter command intentionally exits nonzero. New markers use
`xfail(strict=True, raises=OptimizationTargetGap)`: only the final unmet target
raises this dedicated assertion subclass. Failed oracle checks, invalid actions
and unexpected exceptions are **not** swallowed as expected economic gaps.
A future fix produces strict XPASS until its marker is removed.

The [machine-readable report](benchmarks/research-scenario-tests.json) records
every new case, outcome, source hashes and the combined bounded result. CI
explicitly selects the new file. Full simulation remains manual opt-in.
No local game, engine step, training, tuning sweep, paid compute or Kaggle upload
was performed. Original histories and prior benchmark artifacts are unchanged.
Candidate and existing submission SHA-256 both remain
`c5d31b86d1120028114f058d0560f73036c7ae940fe5186cb8dc7e2a59ef585e`.

This is broader diagnostic coverage, **not a stronger submitted agent**.
