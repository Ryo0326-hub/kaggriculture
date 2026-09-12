# Cycle 20 — price risk from committed supply and survival deadlines

This bounded descendant of Cycle 19 responds to
[Majkel's loss in episode 108295517](MAJKEL_108295517_STUDY.md). The prior submitted
source and artifact remain byte-identical. The builder verifies Cycle 19's full
SHA-256 before applying the replacements in `experiments/majkel_resilience.py`.
There is no LLM, trained model, hidden opponent inventory or replay-specific
opening schedule in this candidate.

## 1. Forecast the portfolio already committed

For product c and a finite horizon h, estimate:

`future market stock = current market stock + committed output − observed demand × h`.

Committed output includes both visible farms' currently held yields and future
production dates, our actual shed/carries and our purchased seeds/animals. Pending
assets are assumed installed tomorrow for the supply-risk estimate. It does not
invent rival private inventory, rival future purchases, future shops or repeated
replanting of a single crop. The horizon ends at the last playable day.

Animal output uses the next production date, present care bank and interval;
subsequent yields assume full care/feeding and timely harvesting. Repeat crops
contribute 1.7 units per remaining event, an inherited heuristic, not an exact
yield forecast. One-time crops contribute one harvest: 4.2 units for wheat and
the crop cap otherwise. Known held output is never counted again as another
completed production event. These are approximate supply commitments assuming
execution, not promises of realized output.

Wheat feeding is subtracted from gross supply for both visible herds, through
their last useful production date. Already-fed animals are not charged again
for today's grain. Negative net wheat supply means potential market purchases;
ignoring that use previously understated future feed cost.

This is **closed-form arithmetic**, not an engine rollout, agent simulation or
optimization sweep. It replaces the lifetime-rate extrapolation used in purchase
and limited-holding quotes. The old `production_rates` helper remains available
for compatibility, but no longer determines those price forecasts.

## 2. Do not subsidize future sales with today's high price

The forecast quote is now:

`min(future_quote, 0.35 × current_quote + 0.65 × future_quote)`.

Thus a forecast fall is taken at face value, while an increase retains the prior
discount. When a crowded milk or strawberry market is projected to reach one
coin, its future output is valued at one coin, rather than at 35% of today's
much higher quote plus the floor. Existing seed/animal value functions, fixed
costs, work allowances, demand gates, small purchase queues and cash reserves
then determine which alternatives remain attractive. The same quote prevents
holding small stocks merely because the old forecast missed standing supply.

**CO/economics connection:** the crop or animal purchase is an integer capital
decision. Its marginal revenue must use the price at realization, including our
additional supply and the rival's visible output. Wheat has an opportunity cost
as both feed and saleable grain. The work allowance remains a heuristic shadow
price; no LP dual optimum or Nash equilibrium is claimed.

## 3. Rescue threatened assets before night

During the last six actions of an ordinary day, sites with an imminent second
unwatered/unfed night precede routine route targets. Their job is reduced to the
necessary WATER/FEED action so optional fertilizer, care or collection does not
use up rescue time. Travel, actual inputs, exclusive target reservations and
carried-animal installation constraints still apply. Infeasible rescue work is
skipped. Once service flags show success, it stops being urgent.

Earlier in the day, geographic routing and commitments remain unchanged. Final
day delivery continues to outrank this rescue mechanism because there is no
further useful overnight growth. This rule reduces a concrete failure mode; it
does not solve the complete routing problem or guarantee every plant survives.

**CO connection:** this is a deadline-constrained scheduling heuristic. Saving a
productive asset before a hard deadline can dominate starting a new investment
or collecting optional fertilizer. Preserving sunk capital is useful only when
future output remains; the inherited final-day logic handles that boundary.

## Scope and verification

The opening portfolio, three-quadrant policy, seventeen-animal cap, fixed staffing
targets, regular fertilizer rules and terminal storage/accounting are unchanged.
No speculative animal killing, fourth-quadrant purchase or large final sale delay
was added based on one opponent loss. These may need separate evidence later.

Both Cycle 19 and Cycle 20 run the same bounded mechanics/continuity tests.
Additional tests cover remaining production dates, exhausted crops, one-time
harvests, care banks, feed opportunity cost, pending-asset delay, terminal cutoffs,
price collapse, actual buyer demand, survival preemption and unique assignments.
[Release evidence](CYCLE_20_RESULTS.md) identifies the exact artifact and checks.

The largest strategic risk is conservatism: rivals may neglect animals, defer
sales or plant less than their observed capacity suggests, and new shops may
increase demand. Full-care supply estimates can reject an investment that would
have paid off. Delivery timing and private rival stock remain uncertain. The
next server logs should compare actual acquisitions, maintenance losses, prices
and net receipts with this hypothesis. No simulated profit or rating improvement
has been established.
