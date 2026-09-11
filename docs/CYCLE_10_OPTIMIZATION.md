# Cycle 10 — early wheat, working capital and land reuse

The incumbent opening buys two cows, two sheep and eight melon seeds for 2,440 coins. The experimental opening selects the same animals, four melon seeds and eight wheat seeds for 2,200. Its additional wheat can feed animals or be sold, and its plots become available sooner. Neither benefit is free: wheat needs seeds, planting, water, harvest, transport and sometimes extra hires.

## CO250 connection: integer production columns

Think of each complete portfolio as a column containing dated cash and resource use. A binary variable `x_j` selects portfolio `j`, with `sum(x_j) = 1`. Reject a column whose projected minimum cash is below 150 or whose simultaneous opening crops exceed the existing crop limit. Maximize projected terminal contribution among the surviving columns. Enumeration solves this small finite menu exactly; it does not solve the complete game optimally.

The old menu has twenty combinations of livestock and melon counts. The new menu retains their exact forecasts and adds thirty wheat-inclusive combinations. Wheat plots carry a possible two-stage sequence: wheat on day 0, harvested on day 4, then melon on day 5. Only the first-stage purchase executes. Subsequent purchases are reevaluated from the actual farm, cash and market by the unchanged investment policy.

This is a concrete way to represent the opportunity value of land becoming free. Pricing wheat once and leaving its plot idle for the entire season would penalize a short crop against a long-lived investment. Conversely, a forecast that credits the second crop without charging its seed, service and later cash requirement would overstate the gain. This experiment dates both costs and receipts. The second stage is an option represented by one feasible template, not guaranteed future behavior or a complete reinvestment plan.

## Economics: one unit cannot serve two uses

Daily wheat conservation is `ending stock = starting stock + harvest + purchases - feed - sales`. Feeding a unit saves a purchase at the applicable marginal buy price; selling it earns its marginal sale price. The forecast consumes held wheat for feed, purchases any deficit, then retains a next-day feed buffer before selling the remainder. It cannot credit the same own unit as both feed savings and sales. The existing approximate rival-feed forecast is unchanged so this remains an opening-only experiment.

The selected column spends 240 fewer coins immediately but includes 640 coins of possible later melon seeds, for 2,840 modeled acquisition costs overall. Cheaper first-stage seeds therefore do not mean lower total investment. The old forecast values its opening at 27,769.6 contribution, versus 30,631.6 for the wheat sequence. These are planning estimates under two existing melon-supply stresses and an existing receipt haircut, not realized returns or a calibrated probability distribution.

Labor is integer and increasingly expensive: an extra crop may fit within an existing crew, or trigger a whole additional hire. Cycle 9 showed that cutting four crop seeds can leave the wage bill unchanged. Actual hiring and dispatch are kept fixed here so any additional labor cost arises from the changed portfolio rather than a simultaneous staffing redesign. The forecast can still miss installation delays and repair hires; compare its dates and wages with actual execution.

## Game theory and evaluation

The two farms interact through the shared market. Wheat production can lower our feed expenditure while also lowering a rival's feed price. Excess supply can reduce sale value. A related wheat-heavy version of the scaled-mixed control tests that competitive exposure. It retains the control's livestock, expansion and work policy and changes its crop supply; it is not a reconstruction of Ace Team.

Winning matters more than increasing our own cash alone. Development therefore requires both higher aggregate match score and no opponent-stratum regression. Matched seeds and both seats control some variance, but the simulator's shop draws depend on earlier farm occupancy. Different opening crops can change the towns themselves. Report town divergence and reactive rival outcomes; do not interpret a cash difference as wheat profit at fixed demand.

The frozen [plan](CYCLE_10_PLAN.md) separates consumed development seeds from untouched evaluation seeds. A failed development screen preserves the incumbent and motivates a new hypothesis rather than repeated parameter tuning on the same matches. See [results](CYCLE_10_RESULTS.md) for the eventual decision and measured limits.
