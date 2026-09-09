# Step 3: production, hiring, and marginal value

Implemented September 9, 2026. This checkpoint connects CO250's integer variables, resource constraints, opportunity cost, and LP relaxations to a working agent. The artifact remains one standard-library Python file. It considers wheat and carrots on the 25 starting tiles and up to six hired hands. Land, livestock, and fertilizer remain future work.

## What the server episode established

Submission `56132050` passed validation in episode `107272004`. The supplied replay contains 720 states, both players `DONE`, and 13,297 coins per farm. Both logs contain 719 decisions and no stderr; the largest decision time was 17.554 ms. **600 is the initial skill rating**, not farm profit or evidence of medal strength.

The frozen Step 2 artifact, run locally with the server configuration and seed 0, reproduced every action and economic state. [The audit](benchmarks/step-2-server.json) records the input hashes and comparison. This establishes agreement for this episode; the replay does not expose the server interpreter's source hash.

The replay also showed idle labor: days 1–3 each had four hires and 42 `PASS` commands. Initial wage-saving policies nevertheless reduced terminal cash: their work estimates understated the value of completing production promptly. The final policy can hire more on busy days. Spending on labor is useful when the resulting work creates more banked cash than it costs.

## 1. Price the whole sale

The engine's price `p_c(I)` depends on market inventory, is rounded to an integer, and has a one-coin floor. An isolated sale of `u` units earns:

```text
R_c(I, u) = sum_(k=0 to u-1) p_c(I_k)
I_(k+1)   = I_k + 1[p_c(I_k) > 1].
```

Inventory stops increasing for floor-price sales. `price_at` and `batch_revenue` reproduce the pinned engine's formulas and sparse configuration overrides. Tests compare both prices and complete transactions with the official interpreter.

Multiplying the first price by the whole quantity misses market impact. Wheat's glut curve is relatively shallow; carrot prices fall more steeply as supply grows. A higher advertised price does not automatically imply a better crop investment. The sale calculation is exact for the supplied inventory in isolation; forecasting that inventory is a separate approximation.

## 2. Use observed supply and demand, plus a stress case

The base harvest-inventory estimate is:

```text
current market inventory
+ our carried and shed units
+ estimated harvests from both farms' visible standing crops
- consumption by currently observed shops and the town center during growth.
```

No rival private inventory, future shop unlock, or evaluation seed enters the policy. Duplicate shop instances count separately. Under default intervals, each pet cafe consumes 12 carrots per day, a farmers market six, and the town center one. This average-rate forecast abstracts away within-day consumption timing.

A second case adds one extra 25-tile field's unfertilized peak harvest before ours: 100 wheat units or 75 carrot units. Production uses the lower revenue across the base and stressed cases. Because prices decrease with inventory, the stressed case is always the lower one.

This is a finite supply stress test, not a learned probability distribution or a guarantee against every opponent. It can be too cautious. A matched no-buffer control measures that tradeoff separately in [the results](STEP_3_RESULTS.md).

## 3. Charge new seed costs and value the remaining season

| Crop | Seed cost | Normal harvest age | Unfertilized units with timely watering |
| --- | ---: | ---: | ---: |
| Wheat | 10 | 4 days | 4 |
| Carrot | 20 | 3 days | 3 |

These are reachable unfertilized yields, not the engine's fertilized maximums. Both crops first become harvestable at age two. For a new crop:

```text
d_c = min(normal harvest age, final day - current day)
y_c = d_c                       for these two crops when d_c >= 2.
```

Fewer than two days cannot produce a harvest. With two days left, watered wheat can still yield two units. The agent values that smaller harvest instead of requiring every crop to reach its normal peak. The command layer also reserves time to water, harvest, return, deposit, and sell before the final actionable observation, step 718.

For `q_c` proposed plants and `S_c` owned seeds, new expenditure is:

```text
K_c(q_c) = seed_price_c * max(0, q_c - S_c)
v_c(q_c) = [R_c(stressed_inventory, q_c * y_c) - K_c(q_c)] / d_c.
```

Owned seeds are a sunk cash cost for the current decision, so they are not charged twice. Their future option value is not explicitly modeled. Dividing the margin by growing days represents the opportunity cost of occupying a plot longer. `v_c` is an average cycle-return proxy, not total season profit: it omits exact replanting delays and future labor expense.

## 4. Couple integer crop lots to hiring

Let `H` be hands already present and `h` the proposed total, from `H` through six. New hands cost successive Fibonacci amounts: `1, 1, 2, 3, 5, 8`. Existing wages are sunk; `C_h` includes only additional hires. With `t` actions left today:

```text
B_h = (H + 1) * t + (h - H) * max(0, t - 1).
```

New hands lose the current action because they arrive after the worker phase. Cash and available market-order slots further restrict hiring.

The estimated existing workload `W` charges three actions per crop needing water, two per mature crop to harvest, and a return/deposit cost for carried goods. Return cost uses distance to the northwest shed-access tile plus one deposit. These are workload proxies, not exact routes or guaranteed upper bounds. Empty plots, weeds to clear, and plots expected to be harvested today supply planting slots `L`. Each new lot receives a four-action setup budget.

For each workforce, `optimize_lots` exactly enumerates:

```text
maximize    v_wheat(q_wheat) + v_carrot(q_carrot)
subject to  q_wheat + q_carrot <= L
            4 * (q_wheat + q_carrot) <= max(0, B_h - W)
            K_wheat(q_wheat) + K_carrot(q_carrot) + C_h <= observed cash
            q_wheat, q_carrot are nonnegative integers.
```

There are at most 351 quantity pairs and seven workforce totals. This is a small integer resource-allocation problem, so enumeration avoids an external solver dependency. A hand-worked test demonstrates the shared budget: with quantity-table values `8, 15` for one/two wheat lots and `10, 17` for carrots, a 30-coin budget at seed costs 10/20 buys one of each for value 18, exceeding two wheat lots at 15.

The outer comparison also values servicing standing crops. Let `G` estimate the value needing protection or collection today and `s_h = min(1, B_h / W)` when work remains. It selects:

```text
model_score(h) = G * s_h + best_production_value(h) - C_h.
```

The service fraction is a proportional-workload approximation. It neither identifies which crops will be serviced nor guarantees every plant will be maintained. `G` values existing goods while production uses normalized cycle returns, so this blended score is a heuristic for today's decision, not an exact common-horizon cash objective. Full games test whether these approximations are useful.

## 5. Interpret a marginal hire

For adjacent workforce alternatives:

```text
delta_value = operating_value(h) - operating_value(h - 1)
delta_cost  = C_h - C_(h - 1)
delta_net   = delta_value - delta_cost.
```

The algorithm enumerates all alternatives rather than stopping at the first unattractive hire. Indivisible lots can make two hires together valuable even if the first adds little by itself: an integer-programming complementarity effect.

[The saved decision](examples/step-3-decision.json) reconstructs development seed 11 at day 4, hour 0. Existing work is estimated at 114 actions:

| Total hands | Capacity | New hire cost | Production score | Overall model score |
| --- | ---: | ---: | ---: | ---: |
| 4 | 116 | 7 | 0.00 | 2,009.00 |
| 5 | 139 | 12 | 105.83 | 2,109.83 |
| 6 | 162 | 20 | 210.83 | 2,206.83 |

The sixth hand costs eight more coins and adds 105 units of estimated operating value: a marginal model gain of 97. The selected plan anticipates eleven wheat lots and one carrot lot. Its immediate action waters with the existing farmer, hires six hands, and buys seven wheat seeds. The twelve planned lots have not yet been planted; later observations trigger new plans.

## 6. Connect to LP relaxation and duality

For fixed `h`, represent each quantity table with binary prefix variables: `z_c,k = 1` includes the kth lot, with `z_c,k+1 <= z_c,k`. Its objective coefficient is that lot's marginal value. Its cash coefficient is zero for an owned seed or the seed price for a new purchase. Plot, estimated labor, and cash constraints are linear in these variables.

Relaxing the variables to `[0,1]` gives an upper bound on **this fixed-workforce model's** integer optimum. Its dual variables could price another unit of model cash, labor, or land. This implementation does not solve that LP or calculate its duals. Reported marginal hire values are finite differences between discrete alternatives, not LP shadow prices. Neither exact enumeration nor a model LP bound establishes a bound on real season profit when forecasts and work estimates are imperfect.

## 7. Execute safe immediate actions

The Step 2 assignment solver remains, now bounded at seven workers and 32 tasks. It jointly assigns existing workers to feasible targets. The economic model may propose both crops, but the executor chooses one planting crop for the current turn, preferring usable owned seeds. Planting assignments are capped by both the selected lot count and seed stock. Purchased seeds become usable later.

Deposits reserve shared space in worker order. `DROP` is used only when the entire inventory fits; otherwise `PLACE` transfers a bounded amount and retains the excess. Mixed wheat/carrot inventory can therefore be banked in one action when space allows. Sales include actual planned deposits. Hires and purchases are funded from observed cash without requiring a particular same-turn sale price.

Model optimality does not extend to this complete execution process. Travel, changing targets, work estimates, and one-crop-per-turn execution may prevent a proposed plan from being completed. Full-season tests inspect all workers' seed quotas, crop targets, storage, spending, maintenance, and terminal produce.

Reconstruct the example with matching source:

```bash
uv run python explain_turn.py \
  --replay artifacts/step-3-development/replay-0001.json --state 96 --player 0
```

The command verifies the source hash and recorded action before explaining the decision. [Step 3 results](STEP_3_RESULTS.md) report controlled comparisons, failed hypotheses, limitations, and the exact prepared artifact.
