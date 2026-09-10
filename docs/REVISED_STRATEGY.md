# Revised competitive strategy after the Otter Vibe and SpaTaro replays

Prepared September 10, 2026. Status: implementation proposal, not a new agent or a performance claim. Ryo leads development and can spend about three hours per day. Ryo has $48.39 in AMD Developer Cloud credit expiring today. The account is ready, but a GPU droplet still needs to be created; expiry time and timezone are unconfirmed. Do not assume midnight Eastern. The sustained plan uses the existing Mac, with no assumed out-of-pocket cloud spending. The teammate's contribution is optional to the critical path.

**Implementation checkpoint, September 10:** [Step 5](STEP_5_RESULTS.md) implements shared livestock maintenance routes and protects scheduled production deliveries. An installed-herd experiment isolates scheduling, followed by ordinary full-season evaluation with the investment rule unchanged. This establishes one part of the proposal below. Mixed crops, expanded land, and new opponent-supply forecasts remain future work. No AMD droplet was needed for this checkpoint; the local runner now supports independent CPU processes.

**Subsequent checkpoint, September 10:** Step 5 passed server validation. [The awarse audit](STEP_5_SERVER_ANALYSIS.md) shows that our low wage bill and cash lead did not offset the rival's larger crop/livestock pipeline. [Step 6](STEP_6_RESULTS.md) implements bounded wheat/melon/strawberry commitments, input opportunity costs, supporting hires, and crop deadlines. It won 251 of 300 fresh local games, including all 60 against Step 5, but lost 49 of 60 against the melon-only crop control. Investigate planting dates, waiting, and crop sequences before adding land. The proposal below remains the longer-term direction; land expansion, larger joint routing models, and richer rival forecasts are not yet implemented. Step 6 is locally prepared and has not been uploaded.

## Objective and evidence

Build a self-contained agent that improves its probability of winning against a broad field, including opponents with the strengths observed in Otter Vibe and SpaTaro. Do not optimize for a particular replay's coin total or the current opponent's name.

The competition objective is:

```text
maximize E[1{our terminal bank > opponent terminal bank}
         + 0.5 * 1{terminal banks tie}].
```

Expected cash margin is a useful planning approximation, but maximizing mean margin is not mathematically equivalent to maximizing win probability. Use win/draw/loss for candidate selection; cash flow and margin explain results.

The two supplied episodes were reproduced exactly in the pinned official 1.32.7 engine. Their economic states and cash accounts match at every transition. They contain three team names and no submitted source versions. They establish behavior, not internal algorithms or an unchanged Otter policy across both games.

| Evidence | What we can try to improve |
| --- | --- |
| Otter beats Himanshu 99,728–91,370 in episode 107287104 | Broad production and efficient crop timing can pay for more labor |
| SpaTaro beats Otter 125,668–125,425 in episode 107293185 | Otter's 4,358 extra receipts are outweighed by 4,601 extra spending |
| In that direct match, wages are 4,120 versus 13,225 | Optimize the entire daily workload and workforce together |
| SpaTaro earns 17,511 from 78 melons; Otter earns 13,336 from 102 | Delivery dates and shared-market supply matter as much as volume |
| Otter switches from four cows/ten sheep to ten cows/three sheep across the games | Match expansion to observed demand and likely rival supply; avoid a fixed species recipe |
| Both reach 75 productive tiles and mix crop/animal work within worker routes | Our ten-station, one-worker-per-station design limits productive scale |
| SpaTaro emits 288 unsupported product-buy requests | Judge executed actions; do not imitate ineffective commands |

Detailed local evidence: [replay analysis](../artifacts/top-replay-analysis/REPORT.md). Raw replays and local analysis artifacts remain outside Git. For provenance, the two source SHA-256 hashes are:

```text
107287104: 782f5565483b9c40bfd890633a831ed0b49f28f8a4813a76a30b1ef0ad342218
107293185: ae1ff79c6f448e13252df174686568ed2c1a917f08c1250983ef903e4d259d40
```

## Our proposed advantage

Combine economical shared-worker routes, precise crop schedules, and forecasts of the opponent's supply. Replan from the current observation so these components stay consistent as prices and the farm change.

The active Step 4 policy already has useful price curves, livestock projections, resource reservations, and release checks. Preserve those foundations. Its restrictions—ten stations, one worker per station, no mixed crop production, a fixed three-day admission reserve, and simplified rival flows—are policy choices to test, not game rules.

### Against an Otter-like opponent

1. Match its crop timing before trying to outproduce it.
2. Service several neighboring assets with each worker; avoid expensive daily hires unless the whole plan pays for them.
3. Anticipate large premium-product deliveries from visible mature crops and herd output. Compare selling before the batch with waiting for demand to recover.
4. Stagger our plantings and select an alternative product when overlapping harvests would destroy our portfolio's margin.

Do not assume every Otter version always sells at hour 23. Its observed sales occur throughout the day, with about 36% of receipts at hour 23 in the direct match. Delivery timing belongs in a forecast with uncertainty, not a hard-coded opponent identifier.

### Against a SpaTaro-like opponent

1. Improve crop output per seed, tile-day, and action through timed fertilizer and watering.
2. Treat its frequent early selling as the difficult delivery scenario; a strategy that only front-runs an end-of-day seller is insufficient.
3. Avoid automatically adding cows and strawberries just because current prices are high. Evaluate the future shared market with its visible committed production included.
4. Use the best available alternative: sheep, eggs, carrots, wheat, premium crops, or retaining cash. An alternative is selected for positive incremental value, not merely because the opponent does not produce it.

Both sets of responses are hypotheses. A proxy with similar behavior is not the actual competitor, and winning these two historical trajectories is not an evaluation target.

## 1. Shared-worker scheduling comes first

Initially hold the herd, investment decisions, and daily maintenance requirements fixed. Change only the scheduler and hiring rule. This isolates whether moving beyond station ownership saves money without losing output.

Create task bundles with locations, prerequisites, inventories, durations, deadlines, and estimated contributions to terminal cash. Examples:

- Carry wheat to a group of animals, feed/care where worthwhile, harvest available products, and collect fertilizer.
- Plant a reserved seed and complete its required first-day watering before the boundary.
- Water a crop before a bonus/production transition, fertilizing first when appropriate.
- Harvest, travel to an accessible shed tile, deposit within capacity, and sell before a useful price window closes.

Plan routes over the remaining day, execute one action per worker, and repair from the next observation. Keep nearby tasks together and penalize repeated target switching. The board allows walking through locked land and sharing a tile, so ordinary Manhattan distance is appropriate here; do not invent obstacles or exclusive tile occupancy. Reserve tasks and resources, rather than prohibiting legal worker overlap.

Enumerate a small set of feasible daily worker counts. For each, estimate the value of a complete schedule and subtract actual new hire costs. This handles tasks that become worthwhile only with multiple additional workers; repeatedly rejecting the next single worker can miss such complementarities.

The marginal hire prices for hands 10–15 are 55, 89, 144, 233, 377, and 610. Twelve hands cost 376 in total; fifteen cost 1,596. Do not install an arbitrary permanent workforce target of either number. Workers already hired today are a sunk cost, and hires late in the day provide fewer remaining actions for the same wage.

Start with greedy insertion of feasible bundles, a small worker/task assignment, and local route repair. Use an LP/MIP offline as a benchmark on small states if needed. A full-season exact routing-and-production optimization is not the first implementation.

**CO250 connection:** assignment and knapsack decisions with resource constraints. **Future course connection:** shortest paths, time-expanded networks, and routing with deadlines. The complete problem has integer task activation and shared resources, so it is not automatically a pure min-cost flow problem.

## 2. Mixed production with explicit operating schedules

Start with wheat, strawberries, and melons alongside cows/sheep. Keep carrots, tomatoes, and geese as later alternatives or controls; add them only after the common executor handles their tasks and economic comparison supports them.

| Activity | Initial scheduling template | Economic test |
| --- | --- | --- |
| Wheat | Water on planting day; target bonus ages 2–4, optionally fertilize at age 2; compare earlier harvest with age-4 yield | Feed replacement value versus sale value, cash timing, land reuse, labor |
| Strawberry | Water to survive; fertilize around ages 9 and 13; schedule harvests at 10/12/14/16 | Cover setup and ten-day wait; include four finite production events and the terminal cutoff |
| Melon | Water at ages 0/2/4, then 6–10; target age-10 six-unit harvest without fertilizer | First sale must repay seed, land occupancy, watering, and delivery despite aggregate supply |
| Cows/sheep | Select production or reduced-maintenance mode; schedule care against actual output dates | Joint product/fertilizer receipts less feed, actions, and installation |

These are seed templates, not unconditional instructions. Adjust to observed age, flags, remaining season, labor availability, prices, and feasibility. An ongoing crop's four production events are finite; an animal's holding cap is not a lifetime production cap.

The pinned engine initializes a new plant with `consecutive_unwatered = 1`. First-day watering is therefore mandatory if the plant must survive that boundary. Later, one unwatered day can be tolerated, but two consecutive missed refreshes cannot. Do not generalize alternate-day maintenance to the planting boundary.

For an available fertilizer unit, compare:

```text
additional crop receipts enabled by timely application
minus forgone fertilizer sale proceeds
minus extra delivery/application work and other displaced production.
```

Similarly, homegrown wheat is not free feed: feeding it forgoes selling it. Account for harvested and purchased wheat in one inventory balance so resale revenue is not counted as farming profit.

**CO250 connection:** fertilizer applications form a small interval-covering/selection problem. Binary watering decisions have survival constraints, production-day requirements, and an initial-condition constraint. Whole-farm choices combine these schedules with cash, inventory, labor, and land constraints.

## 3. Opening and expansion should preserve useful choices

Do not commit to a single supposedly optimal opening from two replays. Screen a small fixed menu before tuning many parameters. For example:

| Candidate, before any expansion | Productive starting tiles | Fixed animal and seed cost |
| --- | ---: | ---: |
| Two cows, one sheep, six melons, twelve wheat | 21 | 1,900 |
| One cow, one sheep, eight melons, fourteen wheat | 24 | 1,680 |
| One cow, one sheep, two geese, four melons, ten wheat | 18 | 1,920 |

Those costs exclude hired labor, purchased feed/fertilizer, and later operating needs. They are untested candidates, not safe executable plans or proven recommendations. Five initial hands would add 12 coins, but the scheduler must demonstrate that all installation/planting/watering jobs fit and that subsequent cash balances remain feasible. The goose candidate waits until geese are supported.

Place frequently serviced assets near the shed and distribute lower-frequency work farther away. Evaluate complete routes; distance alone does not determine the layout. Fill unused land only with activities whose incremental contribution is positive.

Replace the fixed three-day admission reserve only after a dated cash-flow model exists. Require money for committed work through the next plausible sale under conservative delivery/price scenarios, with explicit contingency. Do not imitate a two-coin minimum bank merely because a top player survived it.

Buy land when a feasible production-and-labor plan for it improves expected terminal outcome after its purchase/setup/maintenance/logistics cost. Reaching 75 tiles is an observed benchmark, not an objective. The last quadrant costs 4,000 and should face the same test. Reevaluate after new shops and major harvests rather than using Otter's observed purchase dates as rules.

**CO250 connection:** fixed-charge integer investment, working-capital constraints, and resource opportunity cost. Empty capacity can retain option value when future demand is uncertain.

## 4. Model the opponent through visible commitments

The UI is a debugging view of the same grid operations. The submitted agent reads structured observations; it does not need image recognition or UI automation.

Public observations expose both farms' crops, ages, animal states, workers, land, and cash, plus market inventory and unlocked shops. Rival carried goods, shed stock, and future actions are not directly available. Use visible commitments to create plausible supply-and-delivery scenarios:

1. Immediate or frequent selling after harvest.
2. Sale near the daily boundary.
3. Delayed selling or reduced maintenance after a price collapse.

Project a rival's visible asset output conservatively and update with actual subsequent observations. Do not infer exact hidden inventories or individual rival fills when multiple transaction histories fit the same observed change.

Forecast market inventory using both sides' plausible sales and permitted purchases, plus known town consumption. Preserve the price-floor rule: units sold for one coin do not add market inventory. Compute sale batches unit by unit. Split orders do not remove impact unless timing or intervening transactions/demand actually change.

Long-term investment uses low/base/high supply and future-demand scenarios, including the possibility of unfavorable shop draws. Never read the replay seed or future shops inside the acting policy. Use the remaining-season forecast to value long-growth investments, and a more detailed near-term forecast for dispatch and sales. Replan after observable changes.

**Game theory connection:** this is a dynamic game with a shared market and partially observed inventory. Quantity competition resembles Cournot competition, but the timed production, integer investments, logistics, and terminal objective make a static Cournot solution insufficient. Use an approximate best response to an ensemble of plausible rival behaviors, rather than claiming to solve a Nash equilibrium.

## 5. Make sale timing and relative advantage explicit

At an eligible decision, compare a small menu: sell available surplus now, deliver a valuable batch now, wait for the next demand event, or keep enough stock for committed internal use. Include worker opportunity cost, shed pressure, and liquidity.

The comparison should change both our and the rival's expected future prices. Selling before a rival may increase our receipts and reduce theirs. It can also damage our own later receipts. Buying wheat to affect its price ties up cash and shed space and affects our own feed costs; the engine does not require nonnegative market inventory, so this cannot be treated as literal denial of all rival feed supply. Such tactics must earn their full modeled cost, not be rewarded for price movement itself.

Reject unprofitable production justified only as an attempt to flood a market unless a complete relative-outcome evaluation supports it. Against a strong frequent seller, profitable product substitution or a different harvest date may dominate racing to the shed.

Near the end, evaluate projected final margin including visible rival unharvested output and uncertainty in hidden inventory. A current cash lead alone is not a safe lead. Preserve likely wins when credible scenarios agree; when trailing, consider higher-upside feasible alternatives only if they improve estimated win probability. Randomness or larger expenditure alone is not useful risk-taking.

## 6. Operating modes and endgame

Installed animals have sunk acquisition costs. Compare future feed, care, collection, and harvest choices, rather than insisting on recovering the original purchase price in every later decision.

- Product mode: feed and care when the resulting production is valuable before termination.
- Fertilizer-oriented mode: consider alternate-day feeding, collection, and only worthwhile main-product work.
- Exit mode: stop maintenance when future recoverable output cannot cover its incremental costs, with planned asset loss explicitly recorded.

Fertilizer availability on surviving unfed animals makes the second mode possible in this engine. Care bonuses, holding capacity, existing yield, next production date, consecutive-unfed state, and feed already carried must all enter the comparison. Terminal work should not spend money on output that arrives after the final actionable transition.

Keep existing Step 4 daily-maintenance tests for its frozen policy. For the new policy, distinguish intentional modes from unplanned missed feeding or escapes. Do not remove safety assertions simply to make failures disappear.

Every harvest requiring banked proceeds needs a feasible remaining harvest/deposit/sale path. Endgame inventory should be evaluated by achievable net sale value; retrieving two one-coin items is not worthwhile if it requires a new expensive worker. Check the actual final step, not an assumed final overnight drop.

## 7. Architecture and runtime

Use four compact components with explicit interfaces:

1. **Economic state and forecast:** observed resources, future output scenarios, batch prices, cash schedules, and rival uncertainty.
2. **Investment planner:** selected asset/land alternatives, spending limits, and internal-use stock reservations.
3. **Task scheduler:** task bundles, remaining worker capacity, routes, and candidate workforce counts.
4. **Executor and reconciler:** feasible unit commands, ordered market commands, shared reservations, and next-observation repair.

Detailed operational planning covers the remaining day; investment valuation covers the remaining season. Avoid a short horizon that systematically rejects strawberries before their first yield. Recompute expensive forecasts on changed state or daily boundaries; keep ordinary turns cheap.

Continue with standard-library submitted code and lightweight enumeration/heuristics. External LP/MIP tools, if used, belong first in offline small-instance benchmarks. End-to-end RL, a live LLM policy, and a new GPU training system are deferred unless the simpler system reaches a demonstrated bottleneck early enough to justify them.

The current specification gives a one-second action timeout. Start with an engineering target below 100 ms p99 and 250 ms worst case on representative local states, then verify the exact packaged agent on the server. These are local targets, not guarantees about server hardware. Prefer a bounded feasible schedule to running an optimizer until timeout; maintain a valid fallback.

## 8. Evidence required before promotion

Freeze Step 4 and the submitted Steps 2/3. Build reactive controls from our own components: a precise mixed producer, a dairy/strawberry frequent seller, a wool specialist, a premium oversupplier, and a conservative low-labor operator. Perturb their opening, maintenance, and sale timing so success does not depend on one brittle proxy.

Use a sequential evaluation budget:

1. Full-season smoke games, both seats, resource-conflict and terminal scenarios.
2. Development screening: ten fresh seeds in both seats against four relevant controls, about 80 games. Inspect failures and retain only promising candidates.
3. Freeze candidate and hypothesis; compare candidate and champion on a separate set of 30–50 seed blocks, both seats, against the same pool. Four opponents imply 240–400 games per candidate or reference. Scale to measured CPU throughput and the available budget.
4. Report pool-weighted match score and uncertainty in the paired improvement, resampling whole seed blocks. Predeclare a material regression threshold per opponent class; initially flag a drop exceeding five match-score percentage points for investigation. Use fresh batches if uncertainty prevents a promotion decision.
5. Repeat exact-artifact isolated validation, then inspect server validation and actual ladder episodes.

After inspecting a holdout for tuning, retire it into development data. Log artifact/environment hashes, seeds, seat, latency, errors, no-ops, wages, price-floor sales, losses, and forecast error. Store summaries for every game and only selected compressed diagnostic replays; local disk space is limited.

Beating our own proxies cannot establish that we beat Otter or SpaTaro. That claim requires actual head-to-head episodes or legitimately available current executable policies tested reactively. Broader ladder performance also matters: overfitting to two opponents can reduce medal chances.

## 9. Approximately 60 hours of work, with a final buffer

### Today's expiring AMD credit

Use the credit only if an existing or quickly available environment makes a useful bounded job possible. Our current simulator and policy are Python CPU workloads. Access to a large GPU does not make them GPU accelerated, and rewriting the engine or starting RL to consume expiring credit would displace higher-value work.

If access is ready, use the VM's CPU capacity to run a fresh diagnostic league for frozen Step 4 against existing controls, measure throughput, and save summaries plus selected loss replays locally before expiry. This can identify fragile demand regimes and feed/labor forecast errors. It cannot evaluate the proposed mixed strategy before that strategy exists. Limit setup effort to approximately 30 minutes; otherwise continue the local implementation plan.

Before launching a paid resource, resolve the exact account expiry, applicable hourly rate, credit eligibility, and access. Bound runtime by both time-to-expiry and remaining applicable credit, leaving time to export results and remove any newly created disposable resource. This strategy document does not provision or delete an instance. AMD's current FAQ says promotional credit applies to MI300X instances, not standalone CPU services; powered-off VMs continue to be billed until destroyed, and a payment method can be charged after credit runs out. Follow the account's actual terms rather than assuming expiry stops billing. [AMD Developer Cloud FAQ](https://www.amd.com/en/developer/resources/cloud-access/amd-developer-cloud.html).

### Main implementation calendar

| Dates | Ryo's budget | Deliverable and gate |
| --- | ---: | --- |
| Sep 10–13 | 12 h | Shared-worker scheduler with fixed existing herd/economics; preserve required output and show savings on a matched comparison |
| Sep 14–17 | 12 h | Mixed crop templates and fertilizer/feed opportunity costs; feasible opening/cash schedule; compare with scheduler-only control |
| Sep 18–21 | 12 h | Rival supply scenarios, delivery timing, and conditional land expansion; test frequent and late sellers |
| Sep 22–24 | 9 h | Fresh-seed league, narrow parameter tuning, and selective-maintenance/endgame ablations; freeze the strongest candidate |
| Sep 25–27 | 9 h | Untouched final comparison, runtime/packaging verification, and actual ladder loss analysis; no new major subsystem |
| Sep 28–29 | 6 h | Verify intended final artifacts and latest-two submission positions; preserve rollback package |
| Sep 30 | Up to 3 h buffer | Confirm statuses or repair a verified defect before 23:59 UTC; avoid speculative changes |

Total planned work before the buffer: 60 hours. If a stage fails its gate, spend the next block fixing or simplifying it and drop a later optional feature. Do not count on the teammate, ongoing cloud compute, or a specific number of simulations until availability and throughput are confirmed. Any cloud setup today comes out of the first block's budget.

A useful three-hour session is 30 minutes reviewing evidence, two hours implementing one hypothesis, and 30 minutes recording results and preparing the next comparison. If the teammate contributes, prioritize independent replay labeling, evaluation runs, and loss analysis using the same interfaces rather than a second evolving full agent.

Keep CO notes per implementation: variables, objective, constraints, connection to LP/IP/duality, approximation, observed decision example, and validation result. Do not label heuristic marginal values as exact dual prices.

## Release state when this proposal was written, and sources

The proposal's original CLI check listed only Step 2 (`56132050`) and Step 3 (`56132659`), both complete. Step 4 was locally validated and absent from that submission list. Its frozen artifact SHA-256 is `0024dc48be607636775eba055eea8bde54d3c0679e5e851439791b5d6cb741f9`. This is historical context; the [submission registry](SUBMISSIONS.md) records the later Step 5 upload and Step 6 local release. No upload is performed by this document.

The live competition listing confirms the final deadline as September 30, 2026, 23:59 UTC (19:59 Toronto). Official page content retrieved through the Kaggle CLI confirms five daily submissions, the latest two used for final evaluation, and no external ingress/egress during an episode. Do not consume upload slots for an unvalidated experimental change. Each upload moves the latest-two window.

Sources: [official timeline and evaluation](https://www.kaggle.com/competitions/kaggriculture/overview), [competition rules](https://www.kaggle.com/competitions/kaggriculture/rules), [official environment specification](https://github.com/Kaggle/kaggle-environments/blob/master/kaggle_environments/envs/kaggriculture/kaggriculture.json), [mechanics notes](MECHANICS.md), [Step 4 model](STEP_4_OPTIMIZATION.md), [Step 4 evidence and limitations](STEP_4_RESULTS.md).
