# Step 5: shared livestock routes with production-day delivery protection

Implemented September 10, 2026. This checkpoint changes staffing and execution; mixed crops, land expansion, and new opponent forecasts remain future work. [Validation and release status](STEP_5_RESULTS.md).

## What changed, and what stayed fixed

Step 4 is preserved byte-for-byte in `baselines/step_4.py`, SHA-256 `0024dc48be607636775eba055eea8bde54d3c0679e5e851439791b5d6cb741f9`. The investment functions `animal_output`, `livestock_value`, and `investment_plan` remain textually identical. Their ten-animal cap, cow/sheep choices, market projection, and three-day admission reserve remain in place. Tests verify that identity.

Step 5 groups nearby animals into worker routes on lighter days, picks up feed for the entire route, and hires enough workers for the selected route cover. On scheduled production days, producing animals receive individual routes. When installing an animal, or when a full station crew is already paid for, it uses the unchanged Step 4 station executor. A route-budget failure also falls back to that executor.

Holding the investment *rule* fixed does not hold purchases fixed in normal games. Wage savings and different transaction timing change cash and market observations, which can change the rule's later choices. The controlled installed-herd benchmark removes new investment to isolate scheduling; ordinary full-season matches measure the complete resulting policy.

## Why minimizing wages alone was insufficient

An initial minimum-workforce version preserved quantities in the installed-herd experiment and cut wages from 2,640 to 200. It nevertheless lost cash head-to-head: batching delayed sales until after the rival's deliveries. This is the same economic issue exposed by the Otter/SpaTaro melon comparison.

The final design constrains the route menu to protect scheduled main-product deliveries. This spends more than the rejected minimum-wage version when output is ready, while retaining labor savings on maintenance days. It is a conservative delivery safeguard rather than an exact solution to market timing. It protects scheduled production even when the current quote is low; future work can replace this rule with a tested marginal delay-value model.

The installation fallback addresses a separate opportunity cost: delaying placement by one calendar day can lose an entire production event before termination. A lower wage bill does not justify that loss automatically.

## The CO250 model: a bounded set-partitioning problem

Let the current installed animal sites be `V`. Enumerate candidate routes `r` containing at most four sites. For each subset, enumerate visit orders and choose the order minimizing a conservative travel estimate:

```text
travel(r) = max over shed-access starts a of distance(a, first(r))
          + sum of distances between consecutive sites
          + min over shed-access returns a of distance(last(r), a).

duration(r) = travel(r) + 2 + sum over i in r of service_steps(i).
```

The two extra actions reserve feed pickup and deposit. Ordinary service reserves four actions per site: feed, care, fertilizer collection, and harvest. The penultimate day reserves three because the existing policy omits care that cannot pay back. The final day reserves two for collection/harvest. Actual work can be smaller than these bounds.

Walking through locked quadrants is legal, and workers can share a tile. Manhattan distance is therefore appropriate for this board. There is no need to invent an obstacle-avoidance or collision constraint. These distances and production rules come from the pinned interpreter, not merely the UI.

Keep only routes whose estimated duration fits the daily budget, reserving three turns for hire availability and repair. Under the default season, the normal budget is 21 actions; the shorter final actionable day has a smaller budget. A scheduled production site is allowed only in a singleton route.

Introduce a binary variable `z_r` for selecting each candidate route:

```text
minimize lexicographically:
    (sum_r z_r, sum_r duration(r) * z_r)

subject to:
    sum_{r containing i} z_r = 1       for every animal site i
    z_r in {0, 1}.
```

This is set partitioning: every site receives exactly one route. One route is operated by the main farmer and each additional route needs a hand. With positive Fibonacci hire costs, fewer required routes imply a lower daily wage bill within this model.

The implementation solves this small integer model through subset dynamic programming. For uncovered set `S`, choose its first site `i`, try each feasible route containing `i`, and solve the smaller set `S \ r`. There are at most `2^10 = 1,024` site subsets. An independent test enumerates all small partitions and visit permutations and verifies the chosen route count and total modeled duration.

**Exactness boundary:** this is exact over the enumerated route menu and its conservative timing bounds. It is not the globally optimal worker schedule, delivery plan, herd investment, or full-season policy. The full game has timing, liquidity, shared-market feedback, and uncertainty absent from this small model.

## Timing stability and resource constraints

Routes depend on full-day workload bounds and scheduled production dates, rather than disappearing tasks alone. Harvesting a producing animal does not immediately remove its production-day protection and reshuffle every worker. All cache keys contain explicit geometry, work bounds, budget, and protected sites; clearing caches changes runtime but not decisions. No hidden future seed or persistent state is required for correctness.

Workers visit their route's unfinished sites in order. They load all outstanding route feed when possible, service animals, and deposit output. Shared shed stock and deposit capacity are reserved in worker execution order. Partial `PLACE` deposits avoid discarding goods when a full `DROP` would overflow. A worker at the shed with saleable produce and no available feed deposits the produce to restore liquidity rather than waiting indefinitely for feed it cannot fund.

The separate market queue preserves the existing conservative feed-buy budget and order limit. Unit operations occur before market orders, so newly purchased feed and newly hired hands are not used in that turn's unit phase. Terminal delivery respects the actual last actionable observation, step 718 in the pinned 720-state season.

The three-turn allowance is a planning margin, not a proof that every unexpected mid-day state can complete all work. Installation fallback, same-day paid crews, state-based repair, and full-season tests address practical cases. The infeasible-cover fallback emits valid station actions; it does not claim to recover an impossible deadline.

## Economic interpretation and duality

The objective here minimizes the cash cost of providing a required service level. Production-day singleton constraints express a conservative restriction on delivery delay. Removing them releases labor capacity but can reduce sales revenue enough to hurt final cash, as the rejected experiment demonstrated.

In an LP relaxation, the site-cover constraints have dual values representing the marginal value of relaxing coverage requirements within that relaxation. The implementation does not compute those dual prices. We should not label route-duration coefficients or cash forecasts as exact shadow prices.

The practical shadow-price question is: how much final cash is one more worker or one earlier delivery worth? This checkpoint handles it through a small minimum-cost cover plus a tested protection rule. A future extension should compare the change in whole-portfolio receipts with the actual extra wage, using a forecast of both players' deliveries.

## Evidence layers and limits

1. Exact small-instance partition/permutation oracle and unchanged investment/executor checks.
2. Engine scenarios for multi-animal feed pickup, liquidity recovery, production protection, installation fallback, and terminal behavior.
3. Controlled ten-animal herds with identical starting assets and new investment disabled. They begin with 15,000 cash and 20 wheat to isolate operations; their cash totals are not normal competition scores.
4. Normal-start complete games against the frozen Step 4 and existing species/herd-size controls, using paired seats and fresh seed blocks.
5. Exact copied artifact tested through Kaggle's official Python loader in an isolated process.

Local evaluation can use independent CPU processes through `evaluate.py --workers 4`. The simulator is not GPU accelerated. Results retain deterministic job ordering and record concurrency in the manifest; comparisons reject differing concurrency settings. Parallel/serial consistency is tested on the actual engine. Runtime comparisons under load remain machine-dependent.

The current pool contains related local policies, not Otter's or SpaTaro's reactive source code. Local improvement is evidence for this checkpoint, not proof of leaderboard or medal strength.

For a source-matched decision, `explain_turn.py` now reports route mode, protected sites, modeled route lengths, workforce target, and actual actions alongside the unchanged investment alternatives. [Saved shared-route example](examples/step-5-decision.json).
