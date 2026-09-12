# Cycle 13 — broader logic audit

September 11, 2026. The land-admission failure was not an exhaustive diagnosis.
This review finds **two further dispatch defects, two forecast inconsistencies,
and an additional objective-selection weakness** in the custom Cycle 13 agent.
The exact public V36 / Cycle 14 candidate was not changed or certified by this
audit. These findings must not be attributed to that separate source.

Sources examined: the frozen Cycle 13 artifact, its builder, the inherited
crop/livestock dispatcher and shared ledgers, `experiments/throughput.py`, and
the pinned engine's unit, market and overnight-refresh definitions. Engine
source was read, not executed. No matches, engine stepping, counterfactual
episodes, training or cloud compute were used.

[Reproducible audit](../scripts/audit_cycle13_logic.py) ·
[Evidence, cases and hashes](benchmarks/cycle-13-logic-audit.json) ·
[Earlier land diagnosis](CYCLE_13_POSTMORTEM.md).

All **719 own recorded decisions** in episode 107984963 still match the frozen
artifact. The additional probes call policy/accounting functions on recorded
or constructed observations; they never apply returned actions to a game.
Constructed cases demonstrate decision failures under the specified inputs,
not that those failures occurred in the supplied match or explain a quantified
part of its 40,014-coin loss.

## Findings and evidence strength

| Finding | Evidence | Consequence |
| --- | --- | --- |
| Land candidates blocked before valuation | Previously traced in the actual game | No expansion despite sufficient cash |
| Final-day urgent watering overrides cargo delivery | Constructed single-decision case | Carried goods can become impossible to bank |
| Tomato harvesting overrides fatal watering deadline | Constructed single-decision case | A still-productive tomato plant can die overnight |
| Investment labor model disagrees with dispatcher | Recorded-state comparisons plus a constructed marginal case | Costs and feasibility estimates do not consistently price the executing policy |
| Existing tomato fertilizer is ignored in forecasts | Fifteen checks against recorded overnight transitions | Known next production is understated |
| Profit-per-work selection favors small commitments | Twenty actual source-matched investment selections | Higher total predicted profit can be rejected without a globally enforced labor allocation |

## 1. Final-day cargo can lose its last delivery opportunity

At decision step **715**, four actions remain through step 718. In the bounded
case, the farmer is at `[1,4]`, carries ten carrots and stands on mature,
unwatered wheat. Reaching a shed access tile takes three moves and depositing
takes one action. Leaving immediately can therefore bank the carrots.

Cycle 13 returns **WATER**. The urgent crop branch runs before the ordinary
cargo-return guard. Its terminal return allowance is added only when the
selected crop job is HARVEST; a WATER job reserves no return time. After
watering, only three actions remain for a four-action delivery. The carrots
can no longer be deposited before termination.

This is a deadline/resource invariant violation, not a price-forecast dispute.
Reference: frozen artifact `mixed_turn`, lines 1488–1496 and 1568–1603. The
fixture and returned action are included in `constructed_terminal_case`.

The supplied game ends with empty own shed and carries, so it does **not**
demonstrate this particular loss. A robust implementation must apply terminal
delivery feasibility before every discretionary branch, including urgent
watering, fertilizer work and input errands—not just ordinary harvesting.

## 2. Tomato harvesting can bypass necessary watering

`throughput_crop_job` returns HARVEST immediately when a tomato holds at least
three units, before considering whether it needs water. In the constructed
case, the plant is age ten, holds three units, has not been watered and already
has an unwatered counter of one. It is hour 23 and the only worker is on it.
The policy returns **HARVEST**.

The pinned `_daily_refresh_plants` increments an unwatered counter before
production and replaces the plant with a weed at two. There is no remaining
action to water it. Its last age-eleven production is thus lost. The controller
does not explicitly value retiring the plant against preserving that output;
the high-yield branch simply bypasses the maintenance deadline.

Reference: [throughput.py](../experiments/throughput.py), lines 44–55;
`constructed_tomato_case` in the evidence. This was not observed as a tomato
death in the supplied game. The needed correction is deadline-aware harvest
selection or an explicit, economically valued retirement decision.

## 3. Forecasted labor is not the labor the dispatcher requests

`throughput_value` and the operating reserve use `throughput_workers`: total
service allowances divided by nineteen usable turns. Actual execution uses
`throughput_staff`, which also adds separate livestock workers, crop tours and
pending-seed work. These are different cost/feasibility models.

On the recorded farm at step **384**, the aggregate estimate is **five total
workers**, whereas the dispatcher requests **nine**. At default Fibonacci
prices those targets imply seven versus fifty-four coins for a fresh day's
paid crew. These are model/target comparisons, not a reconstruction that every
requested hire was filled.

A bounded marginal case on that farm adds one mature wheat plot at `[4,1]`.
The aggregate estimate stays at five; the dispatcher target rises from nine
to ten. The forecast therefore assigns **zero additional daily wages**, while
the dispatch rule requires another **thirty-four coins**. This case compares
workload rules; it is not a new episode or evidence that the extra plot would
actually have been purchased.

References: `throughput_workers`, `throughput_staff`, `throughput_value`, and
the reserve in `throughput_investment`; `constructed_marginal_labor_case`.

Approximate labor forecasting was disclosed previously, but this concrete
contradiction limits what `capacity_estimate_fits` can establish. Using actual
Fibonacci prices is insufficient if they are applied to the wrong worker
count. A corrected design needs one service/route model shared by investment
admission, reserves and execution, including the effect on existing tasks.

## 4. Tomato forecasts ignore fertilizer already applied

`throughput_column` assigns one unit to every future tomato production date,
even for an existing plant whose current watering and active fertilizer are
visible. At an imminent night transition those inputs are already supplied;
crediting their bonus does not assume free future fertilizer.

In **fifteen recorded night-boundary checks**, the helper predicts one unit for
the next day while the next recorded state contains two. For example, step
551's plant at `[2,3]` has zero held output, is watered, and has fertilizer
active through internal day 24. The next observation has two tomatoes.

These are checks of the forecast function against observed transitions. The
investment selector does not run its valuation at hour 23, so they are **not
fifteen proven bad live investment decisions**. The component inconsistency
still matters: forecasts of existing own and rival output affect saturation,
marginal revenue and investment comparisons.

Reference: `throughput_column`, lines 99–103; `known_fertilized_tomato_nights`.
Keep conservative base yields for uncommitted future inputs, while crediting
already-known productive state and respecting plant capacity.

## 5. A separate strategy weakness: ratio versus total profit

The selector maximizes `value / work` across affordable candidates that pass
its estimated capacity test. In **twenty recorded investment decisions**, an
alternative has greater total forecast value, but the ratio favors a smaller
or different commitment. At step 72 it chooses one melon with forecast value
150 instead of four tomatoes valued at 546. These are the policy's forecasts,
not verified realized profits.

Profit per unit of scarce labor can be useful. However, this controller does
not allocate the remaining labor/cash across a full collection of projects;
it chooses one purchase and pending seeds then block subsequent investments.
Consequently, the ratio can leave capacity and cash unused and delay growth.
The land-vacancy gate amplifies that effect.

This is a design weakness rather than a malformed action or proof that choosing
the higher-value alternative wins. In CO terms, a ratio is not equivalent to
maximizing total season profit under joint resource constraints. A consistent
alternative would compare complete feasible bundles and charge the marginal
value of scarce labor and order slots, rather than treating all work as equally
scarce at every point in the season.

## Scope, remaining uncertainty and next action

The observed small farm is still most directly explained by the traced land
admission failure and restricted investment selection. This audit does not
assign the entire cash gap to any one cause. It also does not establish an
exhaustive absence of further bugs: route feasibility, forecast uncertainty,
partial market fills and installation interactions remain broader audit areas.

No agent bytes were changed. Cycle 13 remains preserved with these defects;
it is not a newly repaired submission. The planned Cycle 14 public baseline
remains byte-identical and has separate, limited packaging/interface checks.
Do not import legacy components into that baseline without resolving these
invariants and checking the resulting complete policy.

To reproduce this bounded audit from the repository root, use a new output
path (the script refuses overwriting evidence):

```bash
uv run --no-sync python -m scripts.audit_cycle13_logic \
  --source artifacts/submission-cycle-13-throughput/main.py \
  --replay /Users/ryokitano/Downloads/107984963.json \
  --output /tmp/cycle-13-logic-audit.json
```

It verifies both input hashes before executing the known custom policy. All
source-state comparisons use the supplied record, not a simulated successor.
