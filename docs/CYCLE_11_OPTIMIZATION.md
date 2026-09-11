# Cycle 11 — carrots, product choice and marginal value

The candidate adds carrots to the investment menu when PET_CAFE or FARMERS_MARKET is visible. The existing opening, three older crops, hiring rules and route assignment remain unchanged. This is a finite production-menu extension; it is not a claim that carrots are always the best crop. [Experiment plan](CYCLE_11_PLAN.md), [unit-action reference](ACTIONS.md).

## CO250: adding a missing production variable

In a production LP, omitting a product variable can prevent the solver from using a profitable market even when demand and capacity exist. Here the old investment menu represented wheat, melon and strawberry, but no carrot choice. A carrot-only shop could push up prices while our agent lacked a corresponding production option.

We add integer carrot batches of 1, 4, 8 or 12 plots. Each batch has an unfertilized and a fertilized schedule. The current portfolio is the baseline; an option's marginal value is its projected terminal contribution minus the baseline projection. Cash, available land, the remaining season and feasible labor routes constrain admission. Existing heuristics rank feasible options; this is not an exact LP/IP solution of the whole game. Neither a forecast difference nor a hand-chosen work allowance is a solver-derived dual price.

The public-shop gate deliberately bounds the experiment. It prevents speculative carrot purchases before a carrot-buying shop appears, but it may exclude opportunities due to center demand alone. Already purchased carrots still receive service regardless of the buying gate.

## Exact yield before economic valuation

A carrot seed costs 20. A new plant starts with one unit of yield and needs planting-day water to survive. Water raises yield at ages 2 and 3, giving **three units without fertilizer**. The maximum is four; that maximum is not the ordinary yield. Harvest is legal from age 2, and the policy plans age 3 after its final beneficial watering. Delayed harvest starts losing one unit every two turns from the next day boundary until the plant becomes a weed.

One timely fertilizer can add one net unit over the ordinary schedule. The actual action decision compares the expected value of that extra carrot against the fertilizer's sale value and the existing eight-coin work allowance. It skips fertilizer after today's water, while fertilizer remains active, or when future ordinary watering already reaches the cap. The projection also considers the unfertilized template, so it can admit a crop without pretending the extra unit is free.

The same-turn planning ledger uses the real four-unit cap and removes a harvested carrot plot. Otherwise the planner could count impossible output or keep charging an already harvested crop. Terminal-day salvage uses only remaining legal growth; a new investment still needs time to complete its planned cycle. Forecasts of late existing crops use observed remaining yield; travel-time spoilage is still a modeling limitation, and dispatch prioritizes the maturity deadline.

## Resource costs and competition

Short growth occupies land for fewer days, but still needs planting, watering, harvesting, travel and delivery. Integer Fibonacci wages can make the extra batch expensive even when its seed cost is small. Both planting cash and later service/input costs must fit the existing budget rule. The route planner receives carrot-specific service counts; its algorithm and the actual hiring rules are not redesigned.

The forecast uses observed town demand and visible rival carrot crops. Selling our carrots pushes down their shared price. A related scaled-mixed control reserves every third field for carrots to test that supply competition; its remaining fields and livestock keep their previous rules. Beating this related variant alone would not establish general strength.

Evaluation keeps win/draw/loss separate from own profit and from leaderboard rating. Matched seeds and seats reduce some variance, but different occupancy can change subsequent shop draws in this engine. Exact replay accounting and source-matched decisions explain what happened; they do not hold future demand fixed. Development must pass before reserved fresh seeds are consumed. [Results](CYCLE_11_RESULTS.md) record the eventual release decision.

## Measured integration limit

The full-agent audit exposes a gap that the isolated growth tests cannot resolve: the existing urgent watering branch permits fertilizer substitution only for strawberries. Carrot bonus days are usually urgent because of dehydration or maturity. A theoretical carrot fertilizer gain therefore does not imply that the worker will load and apply it. In the largest-profit diagnostic, 37 carrot plots yield 111 units, with zero carrot fertilizer applications.

Procurement also changes its own price. At observation 481 a small positive fertilizer value prompts an eight-unit purchase costing 583; at 482 the recomputed value becomes nonpositive and all eight units are sold back for 583. That pair has zero direct net cash, but it does not fertilize any crop. Treating gross sales as production profit would be misleading.

The next correction must connect a funded, timed input-delivery action sequence to the production column, or value the executable unfertilized schedule instead. Buying and selling at the correct quotes, loading before watering, preserving critical watering/harvest service, and avoiding duplicate reservation are part of the same resource-feasibility problem. The frozen Cycle 11 candidate retains this diagnosed limitation and is not a release.
