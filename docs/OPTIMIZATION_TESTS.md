# Economic optimization tests

Follow-up: [137 research-led scenarios](RESEARCH_SCENARIO_TESTS.md) extend this
original suite without changing its cases, results or recorded benchmark.

September 12, 2026, Toronto. Added **245 individually named pytest cases**:
**241 pass and four expose unmet optimization targets**. Of these, 223 exercise
the current policy or its economic/scheduling components; 22 verify independent
economic oracles. The 34 original Fresh Cycle 1 tests also pass, including their
525 original-observation callbacks. Combined local run: 275 passed, 4 xfailed.

Source under test remains SHA-256
`c5d31b86d1120028114f058d0560f73036c7ae940fe5186cb8dc7e2a59ef585e`.
Neither the policy nor its packaged submission was changed. This work adds
tests and evidence; it does not establish higher profits or fix the four gaps.
No game engine, local match, counterfactual season, parameter tuning, training
or paid compute was used. Opponent profiles are static observations and payoff
assumptions, not executable opposing bots.

## Coverage

| Economic question | Cases |
| --- | ---: |
| Scarcity, neutral and glut price anchors across nine products | 27 |
| Rival supply, complementary feed demand, revealed shops, full decisions and displayed cash | 84 |
| Terminal best responses to rival holding/selling/dumping and per-unit sale impact | 36 |
| Post-buy feed pricing, feed shocks and operating liquidity before expansion | 21 |
| Maturity and remaining production windows | 16 |
| Fibonacci marginal wages and avoiding unproductive hires | 16 |
| Fertilizer opportunity cost across five crop calendars | 10 |
| Expected-profit best response, maximin, minimax regret and dominance | 10 |
| Exact integer capital/labor/land allocation and abstaining from losses | 11 |
| Terminal collection, travel and deposit deadlines | 9 |
| Documented unmet optimization targets | 4 |
| Explicit size limits on exhaustive oracles | 1 |
| **Total** | **245** |

Eight named rival farm profiles cover passive play, dairy specialization, wool,
eggs, berries, melon supply, wheat supply and a diversified farm. Tests also
contrast a well-serviced dairy farm with visibly neglected livestock. Three
separate sale assumptions cover a rival holding inventory, making a matched
sale or dumping a larger quantity. These are controlled stress conditions, not
claims about the private strategy or future actions of a real competitor.

Each parameter row changes a product, economic regime, binding resource,
observable rival exposure or strategic belief. Tests do not change policy
coefficients, search seeds or use full-game returns for selection.

## Independent optimization oracles

`scripts/optimization_oracles.py` contains only static arithmetic:

- Per-unit simultaneous sale receipts for an explicitly linear test market.
  Both players share each pre-commit quote; a rival's later sales cannot alter
  receipts already booked. This is not quote times quantity.
- Pure best responses for a supplied probability distribution over opponent
  states, maximin profit and minimax regret. These are different objectives:
  maximin is appropriate only if worst-case protection is the intended choice.
  Neither a pure best response nor minimax regret establishes Nash equilibrium.
- Exact binary portfolios with capital, action and land limits. At most eight
  offers means at most 256 combinations. Payoffs are stipulated net values,
  already including recurring costs, not inferred season returns.
- Maximum-value immediate visit assignment, at most four workers and six jobs
  (2,401 combinations). It assigns at most one visit per worker and checks
  travel, service deadlines and optional terminal delivery. It does not solve
  multi-stop daily routes or simulate movement.
- Constant-price final-turn deposit allocation for at most four workers with
  six units each. It enumerates capacity choices, not future farm states.

The oracles never call the candidate to produce the expected answer. Hand-worked
payoff matrices and binding-resource examples check the oracles themselves.
Some policy tests assert comparative statics rather than an exact optimum:
more competing supply should reduce the same asset's value, while a rival herd
can strengthen wheat demand. Passing those conditions is necessary evidence
of sensible economics, not proof of profit maximization.

## Four current gaps

| ID | Observed choice | Independent target | Interpretation |
| --- | --- | --- | --- |
| OPT-001 | 20 visit-value units | 200 | Slack-first priority selects a lower-value job when either competing visit can be completed, but not both. |
| OPT-002 | 200 visit-value units | 350 | Greedy matching uses the only worker able to cover a second job on a shared job; the joint assignment covers both. |
| OPT-003 | 50 incremental coins | 320 | Final-turn deposits fill two free shed slots with wheat before another worker's more valuable milk. |
| OPT-004 | Milk value estimate 86.8 in both states | Distinguish service deterioration | The supply estimate ignores visible feeding/care history and crew loss. This is a forecasting blind spot, not a measured cash loss. |

OPT-001 and OPT-002 use explicitly supplied visit values to isolate the
scheduler; their gaps are not reconstructed match profits. Both counterexamples
have deadlines that prevent a later second visit from recovering the omission.

OPT-003 is a full agent decision on the final actionable observation. The shed
contains 98 fertilizer units, worker 0 holds two wheat and worker 1 holds two
milk. Both stand at shed access, and capacity is 100. Configured constant prices
are wheat 25 and milk 160. Today's sales occur after worker actions, so selling
the existing fertilizer cannot free space before those deposits. Both choices
sell the same existing fertilizer. PASS for worker 0 and DROP for worker 1 is
feasible and improves incremental banked receipts by **270 coins**. This is
an exact difference for this fixed configured market, not a season-profit claim.

OPT-004 contrasts identical asset counts with different visible service and
staffing. The desired inequality is a model-quality target; the test does not
assume the neglected farm's future harvest or future hiring is known exactly.

Suggested implementation order is final-turn capacity allocation, joint worker
assignment, value-aware deadline triage, then calibrated rival supply. The
first three have small, exact decision witnesses; supply calibration needs
additional recorded evidence and assumptions about service reliability.

## Running and interpreting the suite

From the worktree:

```bash
/Users/ryokitano/Documents/Projects/kaggriculture/.venv/bin/pytest -q -rx tests/test_optimization.py
```

Four named contracts use `xfail(strict=True, raises=AssertionError)` with their
OPT identifiers. They execute in CI and remain visible as expected failures;
unexpected exceptions fail normally. A future fix that passes an unmet target
produces a strict XPASS failure so the marker and evidence must be updated.
No assertion was loosened to accept the current suboptimal answer.

To expose just the four gaps as ordinary failures:

```bash
/Users/ryokitano/Documents/Projects/kaggriculture/.venv/bin/pytest -q \
  tests/test_optimization.py -m optimization_gap --runxfail
```

That command is expected to exit nonzero for the preserved Cycle 1 policy.
CI reports the gaps and runs the other bounded checks. The full simulation suite
remains manual opt-in and was not run. [Machine-readable results](benchmarks/optimization-tests.json)
include every case ID, outcome, reason and source/test/oracle hashes.

Server validation and competitive strength remain separate. The existing upload
artifact is byte-identical, and its previously supplied upload command is still
for that preserved policy, not a policy incorporating fixes for these findings.
