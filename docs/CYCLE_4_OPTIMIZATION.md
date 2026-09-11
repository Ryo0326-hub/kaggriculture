# Cycle 4 — spatial alternatives, fixed costs and shared-market outcomes

This experiment changes only **candidate generation inside `expansion_investment`**. The preserved Cycle 3 dispatcher, fertilizer and harvest rules, opening, projections, prices, working-capital reserve, profitability ranking and discrete hiring rule remain unchanged. `scripts/make_spatial_control.py` builds a standalone candidate from the frozen baseline and rejects an unexpected source layout.

## CO250 connection: columns are not interchangeable

Think of each candidate batch as a column in a restricted integer optimization model. A column specifies a crop, count, planting date and concrete tile locations. Its coefficients consume capital, dated inputs and travel/service capacity; its estimated payoff is added final cash. The current bot enumerates a small menu and applies heuristics. It does not solve the full integer program or certify global optimality.

The old menu excluded a land purchase whenever more than six owned crop sites were vacant. It also required a new batch to contain more crops than the total number of vacant owned sites. Both rules implicitly treat tiles as interchangeable. With travel, that implication fails: a near-shed site in a new quadrant may require fewer scarce worker turns than an empty distant corner.

The new rule considers both owned-land and next-quadrant alternatives whenever the quadrant cap permits. It admits a paid-land batch only if at least one of its actual proposed sites is currently locked. That prevents paying for land that the batch does not use. Existing route, profitability and cash checks then decide whether the new option is worthwhile. Ordinary vacant-land batches remain available.

In an integer model, let binary `y` buy a quadrant and binary `x_j` select a crop batch. A batch that uses a locked site requires `x_j <= y`. The full fixed land cost is charged once; an empty plot is not free if reaching and maintaining it needs additional labor. The heuristic still searches only batches of 1, 4, 8 and 12 and sorts candidate sites by distance. Enlarging its menu is not an exact knapsack or network-flow solution.

In duality terms, unused distant land does not establish that the marginal value of a near-shed site is zero: locations consume different amounts of worker time. We do not compute exact dual prices here. Also distinguish a model theorem from an empirical result: enlarging an exact optimization problem's feasible set cannot lower its optimal modeled objective, but this bot uses approximate forecasts and a heuristic ranking. More choices therefore do not guarantee better realized cash or a higher probability of winning.

## Economic interpretation

The relevant increment remains forecast final cash with the batch minus forecast final cash without it, after land, seeds, feed, fertilizer and discrete wages. A candidate needs positive marginal value and at least 150 coins of forecast working capital. Expected future receipts do not excuse an unaffordable purchase now. No asset has terminal salvage value.

A same-observation example from development state 264 shows the distinction. Cycle 3 proposes eight strawberry seeds on owned land. The spatial candidate proposes the next quadrant plus twelve seeds, spending 2,200 coins on land and seeds. Its forecast marginal value is 10,678.4 and its forecast minimum cash is 14,811. Those figures are predictions, not realized extra profit. [Exact decision example](examples/cycle-4-spatial-admission.json).

On the public ntumlnoob state that motivated the restriction audit, merely adding these columns does **not** produce a purchase: the few feasible new-land alternatives are unprofitable, and the larger ones fail the unchanged route bound. This separates a verified search restriction from the much stronger, unproved claim that removing it solves the observed loss.

## Game theory and evidence limits

Sales enter a shared market. Altering planting dates and product mix changes the opponent's sale prices and possibly its later investments. More own cash and more wins are different objectives. In development, the spatial candidate won all four direct games against Cycle 3 but earned less mean cash than the matched reference. Its strongest-control result remained 2/4. This supports a fresh reactive comparison, not a claim of strategic dominance or a computed Nash equilibrium.

The regression audit found another channel: **a common seed does not fix future town demand across policies**. The pinned engine creates one RNG from seed and day, consumes weed draws for each empty tile on both farms, and then draws a new town shop. Different land/occupancy can change the number of draws before the shop selection. In seed 9310, candidate and reference towns first diverged at state 288 (Day 13); the reference later had a yarn store and two smoothie shops absent from the candidate's town. [Exact trajectories and engine functions](benchmarks/cycle-4-regression.json).

The paired-seed experiment still compares complete policies under the same initial seed distribution. It does **not** identify a pure investment effect at fixed future prices, fixed demand or fixed opponent actions. The agent cannot read the hidden evaluation seed or future shops. A better investment estimate must account for plausible future demand scenarios using currently visible information; observed bad outcomes alone do not prove a specific new crop was intrinsically unprofitable.

The development candidate still bought only one additional quadrant in every game. The observed mechanism is a changed investment menu and timing, not demonstrated three-quadrant production. Staffing forecasts remain imperfect and can reject schedules the actual dispatcher could execute; changing those forecasts is a separate experiment. Avoid enlarging the scope just to make the original scale hypothesis come true.

The release decision follows the frozen protocol: matched new seeds and seats, whole-seed uncertainty, opponent-specific results and operational checks. Public replays diagnose causes; their recorded actions cannot serve as a reactive counterfactual opponent.
