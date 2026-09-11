# Cycle 6 — the option to wait, with supply risk

This is an isolated research implementation built from frozen Cycle 3. [Pre-experiment plan](CYCLE_6_PLAN.md). The results report determines release status; this explanation alone does not qualify the code for upload.

## A small decision tree

An investment uses money and service capacity now for goods sold later. Waiting can reveal a new buyer, accumulate cash or change when a crop matures. It can also lose productive days. The challenger compares these effects explicitly.

It retains the existing menu: one cow/sheep, or crop batches of 1/4/8/12 plots, sometimes with a land purchase. It compares buying immediately with buying on the next shop-opening day and installing the following day. Only the first real action is executed; the agent recalculates on the next actual observation.

There are eight equally weighted next-shop branches, following the engine's uniform draw with replacement. Existing shops are retained. The eight-instance cap and configured unlock interval determine whether another opening remains. Within each branch, the model holds the resulting demand fixed for the remaining season. This is a deliberately short information horizon: later shops are omitted, not asserted impossible.

Each branch contains two supply cases when feasible: the rival's visible portfolio alone, and a small addition to it. The stress adds up to four plots of its most common supported visible crop, followed by one of its most common animals. Acquisition is capped by public cash less 150 and available unlocked vacant/weed cells. Unsupported species, new rival land and hidden inventory are not guessed. These checks bound acquisition; they do not certify the rival's future staffing, care or working capital. This is a sensitivity case, not a learned prediction or probability estimate of rival behavior.

## CO250: integer columns, resource constraints and nonanticipativity

For purchase `j`, observed-shop branch `s`, and unobserved supply case `r`, calculate:

```text
Delta[j,s,r] = terminal cash with the purchase - terminal cash without it
downside[j,s] = min over r of Delta[j,s,r]
buy-now score[j] = average over s of downside[j,s]
```

The subtraction uses the same market scenario for the purchased and existing portfolio. It includes acquisition costs, feed/fertilizer purchases, discrete wages and the purchase's effect on prices for existing output. This is marginal profit, not gross sales.

An immediate investment must satisfy the current affordability test and preserve the forecast's 150-coin cash reserve before receipts in every branch/supply case. Routes must remain feasible under the existing twelve-worker forecast. The original 20% receipt haircut is retained. The heuristic still chooses a family by marginal value per column, then the highest total-value batch in that family; it is not a global integer-program solver.

A waiting policy may select a different investment after observing the next shop. It must choose one investment that works across that branch's *unobserved* supply cases. This is **nonanticipativity**: decisions at the same information state must agree. Taking the best purchase separately in each hidden supply case would give the bot information it never receives.

A regression test makes that error visible. Under one shop, project A pays `[100, -100]` across the two supply cases and project B pays `[-100, 100]`. The bot cannot select A in the first hidden world and B in the second and claim a guaranteed 100. Both have a worst marginal value of −100, so the waiting policy chooses no purchase in that branch. Under another observed shop, A pays `[80, 80]`, so it can choose A there. The two equally weighted shop branches give a waiting value of 40, not the clairvoyant 90.

This connects integer decisions from CO250 to a small stochastic decision tree. There are no computed LP dual multipliers. The relevant economic idea is opportunity cost: waiting preserves capital and scarce service capacity but gives up earlier production.

## Timing and cash are moved together

A deferred crop has its seed purchase on the next opening day and its planting one day later. Land cost moves to that purchase day too. Growth, fertilizer, harvest, animal feeding and service requirements follow the shifted installation dates. Delayed options can use intervening forecast receipts only when the complete cash path covers spending before that day's receipts.

Tests verify this accounting directly. They also verify horizon rejection, unchanged default projections, rival acquisition costs excluded from our accounts, and current-observation purity. The 150-coin reserve remains a model constraint, not a guarantee about realized cash under future opponent trades and dispatch repairs.

## A conservation correction

The inherited forecast estimated rival wheat purchases as `max(herd - crop output, 0)` but then also sold all of the rival crop output. That credits the same wheat as both feed and market supply.

The experimental continuation now uses:

```text
market wheat bought for rival feed = max(herd - wheat output, 0)
rival wheat sold = max(wheat output - herd, 0)
```

For six wheat and three animals, three units feed the herd and three are sold. For two wheat and three animals, one is purchased and none is sold. The final day requires no feed under the existing model, so all output can be sold. Tests check actual price/receipt implications for surplus, shortage and zero wheat.

The correction is opt-in for the new continuation. Default projection behavior, opening decisions and the submitted source are preserved so the challenger remains isolated. A correct conservation equation does not prove that the combined investment policy wins more games.

## Runtime and reproducibility

`scripts/make_information_control.py` requires the frozen Cycle 3 hash and builds a standalone file using `experiments/information_value.py`. Only the original expansion and projection functions change; the actual dispatcher, hiring rules, fertilizer/harvest rules, opening and sale policy remain fixed.

Price quotes are memoized within one decision and one parameter set. A purchase's deterministic labor/wage schedule is shared across its shop and supply scenarios, with a separate cache for each purchase continuation. It is never reused across different actions or observations. Tests compare cached and independent forecasts, including infeasible routes. Ten complete replay decisions and explanations also matched the uncached implementation exactly; measured calculation time fell from 6.03 to 4.02 seconds over those observations.

Two partial engineering runs were superseded before selection: one for the wheat correction, one for the labor cache. Their records are archived separately and are not additional independent competitive evidence.

## What this model still cannot conclude

The reported waiting advantage combines information, timing and liquidity. It is not a clean estimate of the value of information alone. More seriously, the immediate alternative forecasts one purchase and then holds the portfolio fixed, while waiting can access a larger purchase after projected receipts. It omits buying something useful now **and** investing again later. That can bias the comparison toward waiting or misallocate the resulting capacity.

Expected own coins are still a surrogate for winning. The rival's future expansion and later shops are not fully modeled. Its staffing is not optimized. Mean or conservative marginal profit does not establish a Nash equilibrium or a medal-level strategy.

Finally, matched initial seeds do not fix the town trajectory: the engine's weed and shop draws share a day-specific RNG, so changed occupancy can change subsequent shops. Exact replay audits establish executed cash and production, not a fixed-market causal effect of waiting. Promotion must depend on the complete matched game screen and a separate fresh evaluation.
