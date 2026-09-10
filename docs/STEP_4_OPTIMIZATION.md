# Step 4: livestock capital, market impact, and operating liquidity

This checkpoint changes the active production system to a bounded cow/sheep herd. Step 3's crop agent is preserved in `baselines/step_3.py`. The new source remains one standard-library file, `main.py`; no optimizer service, model weights, or network access is needed during a game.

## 1. Let actual losses identify the missing decision

Step 3 passed server validation in episode `107286447`: both farms earned 15,355 coins, both completed, and neither emitted stderr. A local resimulation matches all actions and economic state. The initial rating of 600 was not a profit score. A subsequent CLI snapshot showed Step 3 at 436.8 and Step 2 at 366.7.

Two public ladder losses provide more useful strategic evidence:

| Episode | Step 3 cash | Rival cash | Observed rival production |
| --- | ---: | ---: | --- |
| 107287517 | 21,902 | 91,625 | Up to eight cows, three sheep, premium crops, one land purchase |
| 107288503 | 20,940 | 123,336 | Up to ten cows, four sheep, premium crops, three land purchases |

Both rivals fed and cared for animals and collected/sold fertilizer. Their actions are observations of completed games, not executable opponents. The implementation is our own bounded livestock policy; it does not replay another bot's actions or claim to reproduce either rival. [Audit and source hashes](benchmarks/step-4-ladder-audit.json).

The planned price-buffer comparison was therefore insufficient as the main next step. The larger missing decision was **which productive assets to own**. The no-buffer crop control remains in evaluation, alongside new livestock controls.

## 2. Value an animal as a sequence of dated cash flows

Buying an animal creates obligations before its main product arrives. Cows cost 400 coins and first produce after eight days; sheep cost 500 and first produce after six. Each needs one wheat per day. Care changes later product yields, and fertilizer can be collected daily after placement. Building an empty pasture costs a worker action rather than coins in the pinned engine.

`animal_output` projects output dates under daily feeding, care, collection, and harvesting. It carries forward the observed pending care bonus. At a daily boundary, the engine computes production with the previous pending bonus, then stores the latest day's care. That order matters: adding care to the wrong production cycle overvalues an animal. Tests compare forecasts with the engine's actual daily transition from several ages for cows, sheep, and geese.

The model stops at the final actionable day. Care is omitted when its stored bonus cannot reach another production boundary; the final day prioritizes already-produced goods. Animals have no modeled resale value. This is a finite-horizon investment calculation, not an infinite stream of revenue.

## 3. Include the price effect on existing production

Let `S` be our visible herd and `O` the rival's visible herd. For a proposed additional animal `a`, estimate:

```text
Delta(a) = [R(S + a, O) - R(S, O)]
         - [F(S + a, O) - F(S, O)]
         - [L(S + a) - L(S)]
         - purchase_cost(a).
```

`R` is projected product and fertilizer receipts, `F` is purchased feed cost, and `L` is daily hired-worker cost. An extra animal can lower prices received for products from animals we already own. Computing the difference between two whole-herd projections captures that modeled price externality. Valuing only the new animal's output at today's quote would miss it.

The projection evolves market inventory with daily output from both visible herds, observed shop demand, and feed purchases. Sale batches use the pinned price curve unit by unit, including rounding and the one-coin floor. Feed uses the post-buy price. Rival transactions are placed approximately halfway through our daily batch; actual hourly interleaving is not simulated. Fertilizer has no town-center consumption, unlike the other products.

Future rival purchases, future shop unlocks, hidden rival stock, and replenishment from future crop production are not known. They are omitted. In particular, omitting future wheat harvests can overstate feed scarcity. Daily demand averaging, assumed immediate collection, and daily wage estimates also introduce error. This projection is a decision model, not an exact forecast of terminal cash.

## 4. The CO250 integer decision and its cash constraint

At an investment opportunity, there are three alternatives: buy no animal, buy one cow, or buy one sheep. Let `x_a` be a binary purchase variable:

```text
maximize    sum_a Delta(a) * x_a
subject to  sum_a x_a <= 1
            sum_a [purchase_cost(a) + reserve(n + 1)] * x_a <= observed cash
            x_a in {0, 1}.
```

Additional feasibility gates require an available station, no animal waiting for installation, an early enough hour, and at least four calendar days remaining. The herd is capped at ten nearby stations. The code enumerates this tiny integer choice exactly; it does not solve a full-season integer program or optimize the complete purchase sequence.

The three-day reserve is:

```text
reserve(n) = 3 * [n * stressed_feed_quote + daily_hire_cost(n - 1)].
```

This constraint distinguishes profitability from liquidity. An animal with positive modeled lifetime value is rejected if buying it would consume money needed to keep the herd operating. Three days is a policy choice, not a probabilistic guarantee against all opponents. Only one uninstalled animal is allowed at a time, so purchased capital cannot accumulate faster than workers can place it.

For ten animals, one worker is assigned to each station: the farmer plus nine hired hands. Daily wages follow the Fibonacci schedule, totaling 88 coins at the default multiplier. The tenth station adds the ninth hand, costing 34 coins per day. That additional daily cost enters the marginal investment comparison. The herd cap and one-worker-per-station rule are operating policies; they are not claimed to be optimal staffing.

For this restricted binary selection, enumeration gives the best feasible modeled option. A continuous relaxation could be used to study an upper bound or a cash constraint's dual value, but this implementation does not calculate either. `marginal_value` is a finite difference of projected cash flows, not an LP dual price.

## 5. Read one actual decision

[The saved decision](examples/step-4-decision.json) is day 0, hour 0 of fresh seed 2003, before either farm owns animals:

| Option | Purchase cost | Required reserve | Modeled marginal value | Affordable? |
| --- | ---: | ---: | ---: | --- |
| No purchase | 0 | 0 | 0 | Yes |
| Cow | 400 | 81 | 7,535 | Yes |
| Sheep | 500 | 81 | 8,409 | Yes |

The agent selects the sheep. Its immediate market orders buy one wheat and one sheep. The farmer passes because neither new purchase is available during this turn's worker phase. Later turns pick up the animal, prepare the pasture, place it, and feed it. The 8,409 figure is modeled marginal value under stated assumptions; it is not a promised realized gain.

Reconstruct the decision from the exact matching source:

```bash
uv run python explain_turn.py \
  --replay artifacts/step-4-validation/replay-0001.json --state 0 --player 0
```

The command checks both source hash and recorded action before explaining the result.

## 6. Make the capital plan executable

Each live animal receives a distinct nearby station and an existing worker. The route picks up feed, moves to the station, feeds, cares, collects fertilizer, harvests available product, and returns goods to a nearest shed access point. Manhattan distance determines direct grid movements. Ownership of stations prevents two workers from issuing conflicting operations on one animal.

Shed pickups and deposits share a ledger processed in worker order. Full `DROP` is allowed only when all carried items fit; otherwise a bounded `PLACE` retains overflow. Hires act next turn, and market purchases cannot support the current worker phase. Feed purchase amounts use a buffered price quote and observed cash; the engine still determines actual simultaneous transaction prices. This buffer is not a proof against every possible rival order size.

On the final day, the policy stops buying feed, sells remaining wheat, collects ready animal products/fertilizer, and reserves enough movement time to deposit carried goods. Animals remain on the farm but are not assigned salvage value. Full-season checks verify feeding, no escapes, legal actions, shared stock, and liquidation of shed/carried inventory.

## 7. What the evidence can and cannot establish

The new pool includes Step 3, its no-buffer crop control, cow-only and sheep-only controls, and a six-animal portfolio control. Step 3 and Step 4 face the same fresh seeds, seats, and opponent source files. Statistical comparisons keep whole seed blocks together. Matching seeds does not imply all subsequent random events stay identical when policies change the simulated state.

The pool is broader than the earlier crop-only pool, but the livestock controls share our operating code. They do not represent all ladder strategies, and the two downloaded rivals have not been defeated in a reactive local match. [The results report](STEP_4_RESULTS.md) records outcomes, costs, runtime, and the exact prepared artifact.

The current station policy leaves substantial idle worker time and does not use the remaining plots for crops. Future work should test shared-worker routes and mixed production, then price land expansion using setup cost, feed, labor, storage, and remaining payback time. Preserve the isolated submission gate and require fresh evidence before promoting those changes.
