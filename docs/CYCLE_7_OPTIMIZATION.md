# Cycle 7 — conserve rival wheat before comparing investments

[Plan recorded before evaluation](CYCLE_7_PLAN.md). This isolated challenger tests a forecast-accounting correction discovered during Cycle 6. It contains no waiting policy, demand scenarios or hypothetical rival growth. The results report determines whether it qualifies for release.

## The economic inconsistency

Let `Y` be the rival's projected wheat output on a feeding day and `H` its visible herd. The inherited forecast estimates `max(H - Y, 0)` wheat purchased for feed, then also places all `Y` units on the market as sales. That treats some wheat as both consumed and sold.

For example, with six wheat and three animals, it assumes no feed purchase and six units sold. If the rival uses its crop as feed, only three can be sold. If it buys all three feed units and sells all six harvested units, the net effect is still three added market units. The old forecast incorrectly adds six.

The correction uses:

```text
rival feed purchases = max(H - Y, 0)
rival market sales   = max(Y - H, 0)
```

Surplus and shortage cannot occur at the same time. On the final day the forecast has no feed requirement, so all projected wheat is available for sale. This does not claim knowledge of hidden rival stocks or exact intraday order timing; the existing daily aggregation and half-rival-sale pricing approximation remain.

## CO250 connection: conservation constraints

The underlying resource equation is familiar from linear programming:

```text
available wheat + purchased wheat = consumed wheat + sold wheat + ending wheat
```

A feasible economic plan cannot put the same unit on both outgoing uses. The rival has no modeled private starting inventory here, and the existing forecast aggregates its net daily flow. The fix enforces that simplified balance before valuing our purchase.

Less phantom wheat supply can increase projected feed costs and the value of our own wheat. It can therefore change the preferred cow, sheep or crop batch even though the actual hiring and production rules are fixed. The direction of the final policy effect is not guaranteed: a model correction can still interact poorly with approximate routes, missing future investments and price timing.

This is accounting inside an integer investment heuristic, not a new optimizer. The original candidate menu, marginal-value subtraction, per-column family ranking, 150-coin forecast reserve and discrete wage estimates remain unchanged.

## Implementation boundary

`scripts/make_wheat_conservation_control.py` checks the frozen Cycle 3 source hash and builds a standalone file. It adds an opt-in `net_rival_wheat` argument to `production_projection` and enables it only at the two expansion-forecast calls: the no-purchase baseline and each purchase alternative.

Opening forecasts retain their existing behavior. No other original functions change. Without rival wheat output or without a rival herd, the projection and decisions remain identical; the final day also retains its existing treatment. Tests check those boundaries, the surplus/shortage/zero-output equations and their exact forecast receipt consequences.

This corrected accounting is necessary for a trustworthy model of rival feed and sales. Whether it earns a new submission is a separate empirical question, answered by the matched development and, if warranted, fresh evaluation gates.
