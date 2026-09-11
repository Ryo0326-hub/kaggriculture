# Cycle 13 — production throughput and opportunity cost

This is an adaptation of our Cycle 12 agent, with protected Cycle 3 unchanged. It combines the supplied server evidence with code-confirmed constraints. See [the seven-game study](CYCLE_13_SERVER_STUDY.md) and [release status](CYCLE_13_RESULTS.md).

## Decision flow

1. Read the current public market, shops and farms, and our private inputs/carries.
2. Assign our existing feeding, care, collection, crop and delivery tasks; reserve shared inputs in worker order.
3. Keep the Cycle 12 carrot fertilizer bundles and Cycle 3 strawberry timing. Apply the same ongoing-crop timing principle to tomatoes.
4. Issue surplus sales and operating input orders, then size hires from herd routes, independent crop work and pending planting.
5. With remaining funds and order slots, compare new animal, crop and land batches. Purchase only an affordable positive-value option with estimated capacity available. Pending seeds or unplaced animals stop further investment orders until handled.
6. Replan next turn. Full games and future shop draws are not simulated inside the policy.

## LP concepts, integer decisions and marginal value

An idealized model would choose integer production quantities x_j to maximize final banked cash subject to money, worker time, land, seed, feed and fertilizer constraints. This implementation enumerates a small menu rather than solving a global integer program. It evaluates one animal, one/four crops on owned land, or a land purchase paired with four/eight actual crop plantings.

Each alternative is assessed by a finite difference:

`V(j) = 0.75 × min_s[revenue_s(existing + j) − revenue_s(existing)] − upfront_cost(j) − extra_wages(j)`.

The two scenarios use the visible town's demand rate and, separately, half that rate with 1.5 times visible rival future positive output beyond two days. The factors are conservative design assumptions, not fitted probabilities or calibrated confidence bounds. No future shop identities or replay RNG are consulted.

Revenue here is net of feed purchases. Own crops and animals generate dated physical output, and our current shed/carries are included once. Wheat retained/produced for feed displaces a purchase; it is not simultaneously counted as both a sale and free feed. Animal fertilizer is an output with a market opportunity cost. Crop admission generally promises unfertilized output; optional future fertilizer is not treated as free guaranteed yield.

Prices are recomputed after adding a candidate's supply. Consequently, the candidate's marginal revenue includes any reduction in receipts from our existing output. This addresses **cannibalization**: another cow can lower the selling price of milk produced by cows we already own. Rival supply is likewise part of the shared-price calculation. This is an opponent-aware estimate, not a Nash-equilibrium computation or a model of the rival's full future policy.

Fertilizer decisions compare extra crop revenue against its forgone sale and application/pickup work. Our retained Cycle 12 carrot path also tests the post-purchase quote and assigns actual workers/inputs. Tomato fertilizer can work after watering because ongoing-crop bonuses are applied at the nightly refresh. The local accounting snapshot correctly leaves tomato yield unchanged by WATER itself.

## Labor is an integer resource

Hiring prices follow 1, 1, 2, 3, 5, 8, 13, 21, 34, 55, 89, 144, ... for successive hands each day. Eleven paid hands cost 232 total; twelve cost 376. A small workload increase can therefore have no wage effect, or cross a costly threshold.

Admission estimates dated workload, converts it to a worker count, and charges the difference in complete Fibonacci wage sums. It ranks positive investments by net estimated value per added service action. That denominator is an approximate way to price scarce labor; **it is not an LP dual variable obtained from an optimal solve**. The cash reserve also includes anticipated next-day wages, missing feed and a 150-coin buffer, after already-issued orders have been booked.

Actual dispatch retains our coordinated-task implementation. Herds now use the Step 8 cheapest-insertion tour routine rather than requiring a separate worker for every producing animal. Feasible tours account for travel, service and input/deposit overhead; the algorithm is a routing heuristic, not a shortest-tour proof. Crop staffing is considered separately so investment cannot simply assume every livestock worker is free at sunrise.

The practical ceiling is twelve total workers, including the farmer. Aggregate future workload is only an estimate: it can disagree with the actual dispatcher's route order and deadlines. The prior small-farm experiments showed that lowering wages alone can lose. Server diagnostics must check whether this ceiling causes late water, feed or collection before describing it as an improvement.

## Land and fixed costs

The old geometry reserved ten nearby starting tiles for livestock. Staged geometry reserves five northwest animal sites initially, leaving twenty crop sites. It reserves seven more animal sites in the northeast, available after that quadrant is purchased. The resulting limits are twelve animals and sixty-three crop sites across three quadrants. They are limits, not a promise that all are profitable or that the candidate reaches them.

The second/third quadrants cost 1,000/2,000. A land option must actually use at least one newly unlocked crop tile and pays the whole land cost. Pairing land with four/eight purchased seeds spreads the fixed cost across real planned production. No unpaid future continuation is credited as if it already existed. Land waiting for future animals is not independently valued yet; that is an acknowledged limitation.

## Harvesting maximizes season value, not a single yield

A normal watered wheat crop has two units at age two, three at age three and four at age four. Fertilizer can bring it to five at age three and six at age four. Waiting gains one unit but ties up the plot and requires another service visit. The new branch harvests an already-five-unit wheat crop at age three when another full wheat cycle can still fit. Ordinary three-unit wheat and late-season completion retain the prior rules. This is a bounded renewal/turnover heuristic, not a solved optimal-stopping policy.

The opening remains our joint eight-melon/two-cow/two-sheep portfolio with four additional wheat seeds when cash/space permit. It does not replace melons with wheat as the rejected Cycle 10 opening did. New owned-land batches remain small, limiting queues and spreading planting dates naturally.

## What remains uncertain

The candidate combines related changes in layout, labor, investment, species and harvest timing. That is appropriate to the user's request for an integrated challenger, but a win/loss will not identify each change's causal contribution. Prior sources are preserved for later diagnosis; no local simulation ablations were run.

The market scenarios aggregate dated supply and do not resolve every unknown simultaneous order. Future rival investment, input logistics and optional fertilization remain uncertain. Worker workload estimates do not certify every future route. Our previous cash-survival and current-turn ledger safeguards are preserved, but larger portfolios still require server verification. We do not selectively starve animals or speculate on buy/sell round trips based only on opponent traces.

Implementation: [policy extension](../experiments/throughput.py), [deterministic standalone builder](../scripts/make_throughput_agent.py), [bounded tests](../tests/test_throughput.py). The final artifact uses only Python's standard library; no LLM, training job, API key or GPU is required.
