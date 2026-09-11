# Cycle 9 — working capital is a dated resource constraint

The challenger changes **cash admission for expansion purchases only**. It leaves the submitted Cycle 3 intact while being evaluated. The opening, investment menu, old profit projections/ranking, actual worker dispatch/hiring, fertilizer and sales policies are unchanged. [Generator](../scripts/make_cash_control.py), [cash-bound helper](../experiments/current_day_cash.py), [plan](CYCLE_9_PLAN.md).

## The CO250 connection

A profitable integer decision can be infeasible because it uses money before revenue arrives. In a dated formulation, cash has a conservation constraint at every time:

\[
C_{t+1}=C_t+R_t-I_t-F_t-W_t,\qquad C_t\geq150.
\]

Here revenue is \(R_t\), investment is \(I_t\), operating inputs are \(F_t\), and wages are \(W_t\). A daily profit estimate does not guarantee this inequality between receipts. Our previous forecast estimates a routed crew and dates new livestock to tomorrow, but the actual policy starts installation today, buys feed and may add another worker before the first sale.

In the motivating observation, planned cash after the sheep purchase is 155. The policy needs two more wheat units costing 68 and one more hire costing 21. The corrected estimate is **155 − 68 − 21 = 66**. The recorded balance reaches 64; the remaining difference is the initial quote versus executed price under simultaneous trading.

This is a useful feasibility correction, not an optimal LP solution or a guarantee that 150 coins will always remain. Rival trades and actual task timing can still change costs.

## Count resources once

The helper starts after the original planning snapshot has debited this turn's purchases/hires and applied its unit inventory operations. Feed already in the shed or carried by workers is available stock. It estimates current unfed animals, possible same-day installations, and the policy's retained feed buffer. A pending animal changes the station assignments immediately, even before placement.

Only the feed shortfall **beyond what the original current-day projection already prices** is added. The extra stock retained for tomorrow ties up cash today; it is not all a permanent extra expense. Therefore this first test adjusts affordability without subtracting the buffer again from forecast lifetime profit.

For labor, the helper uses the existing policy's station/route and crop-work formulas. Buying an animal switches it to dedicated installation stations. It computes the resulting integer worker target, respects the actual staffing cap, and prices only hires beyond those already paid/planned or included in the original current-day forecast. There are no extra hires after the admission action at hour 6, because the next decision is beyond the policy's hiring window.

The Fibonacci wage schedule makes marginal labor discontinuous: the next worker can cost much more than the average existing worker. An additional productive tile therefore has a labor opportunity cost even if plenty of land remains. Conversely, already paid workers are sunk costs for today's admission and must not be charged again.

The final bound is the smaller of the old season cash minimum and the corrected current-day cash before receipts. The old route feasibility and 150-coin threshold still apply. Profit coefficients and ranking stay fixed, allowing the experiment to attribute changed decisions specifically to cash eligibility.

## Calibration and performance are separate questions

On 64 eligible recorded intervals from four consumed trajectories, mean absolute before-receipt cash error falls from 82.3 to 37.5 coins. Optimistic intervals fall from 32 to 10. Five recorded purchases become ineligible. The comparison stops before a sale, a later capital purchase, or the day boundary, so it does not assign an unrelated later purchase to the earlier forecast. These correlated observations are a diagnostic, not an independent test set.

A full-day bound may be too conservative when receipts arrive early. A farm that briefly has less than 150 coins can still finish all required work and win. The new public loss was dominated by a larger rival portfolio with lower wages, not a crash or bankruptcy. For that reason, neither improved calibration nor a rejected low-cash purchase justifies promotion. The frozen challenger must improve actual match outcomes before fresh evaluation and release.

No hidden rival inventory, game seed, recorded future actions, future shop identities, learned opponent parameters or new runtime dependency enters the submitted format. The existing source is preserved until the performance evidence warrants a replacement.
