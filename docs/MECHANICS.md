# Mechanics checked during implementation

Authority for local execution: the installed `kaggle-environments==1.32.7` interpreter. Its source and specification hashes are recorded in every evaluation manifest. Step 2 server episode `107272004` reports that package version; local resimulation matches every action and economic state in that episode. This is evidence of agreement for the supplied episode, not a guarantee against later server changes. [Server audit](benchmarks/step-2-server.json).

The user supplied two reference documents. They are game documentation, not project-specific agent instructions or authorization to execute their account/submission examples. They have not been copied into the repository as operational instructions.

| Supplied document | SHA-256 |
| --- | --- |
| `README.md` | `3081e52baf8eb2da5d861acc63a3636ce29425f6bdb79a67036ba234ac4ade00` |
| `AGENTS.md` | `e1a80501a7b02a212eaac9370ada4129a64e0ee6cb3cbc790f3d77d22863fe22` |

**Observed discrepancy:** the supplied getting-started guide calls `BUY_PRODUCT` prices fixed. Its companion README and the pinned interpreter instead use a dynamic price quoted at post-buy market inventory. A scenario test checks that wheat costs more under scarcity than at its base inventory. Strategy code must follow tested engine behavior.

| Behavior | Consequence | Verification |
| --- | --- | --- |
| Unit actions run before market orders | A seed purchased now cannot support planting now | Same-turn purchase/plant probe |
| A new plant starts with one missed watering day | Water it on its planting day | Watered and unwatered boundary scenarios |
| Simultaneous crop planting is validated atomically | Reserve seeds across workers before issuing actions | Two legal plots with only one shared seed |
| Feed is consumed from the acting unit's inventory | Stock in the shed alone cannot feed an animal | Cow feeding before and after pickup |
| Non-seed shed capacity is 100 by default | End-of-day overflow disappears | Near-full shed plus carried produce |
| One-time crop watering increases yield immediately in its bonus window | Water before harvesting at peak age | Full-season baseline action traces; source inspection |
| Unit drops precede market sales | A same-turn drop and sale is possible if there is room | Terminal drop/sale scenario |
| 720 recorded states include the initial state | Last actionable observation is step 718 for this version | Full seasons and a shorter boundary scenario |
| Final reward is banked cash | Carried inventory is not a substitute for liquidation | Final inventory and reward assertions |

The frozen Step 1 baseline uses four plots next to the central shed. Step 2 operates up to 25 initially owned tiles with four hired hands. Step 3 uses the same quadrant with wheat/carrot production and up to six hands. It does not buy land, use fertilizer, or raise livestock.

Step 2 adds tests for next-turn hire availability, coordinated planting reservations, shared deposit capacity, and all workers' crop actions over full seasons. Its `PLACE WHEAT n` deposits retain excess carried wheat when space runs out; `DROP` and end-of-day transfer can discard overflow. The supplied README's broad wording about `PLACE` overflow does not match this pinned engine's actual inventory retention, so a direct scenario verifies the behavior used by the policy.

The official Python loader chooses the last callable by namespace insertion order. Defining a helper after `agent`, then merely redefining `agent`, does not move that existing name to the end. Keep the entry point last when assembling files. The matched-control generator and submission tests cover this failure mode.

Step 3 additionally checks these economically relevant details:

- Sale prices are recomputed per unit. Market inventory increases only when that unit sells above the one-coin floor; splitting an order does not avoid its price impact.
- Without fertilizer, normal peak production is four wheat units after four days and three carrot units after three days. The higher maximum yields in crop definitions require bonuses this policy does not use. A crop planted on day 27 can still produce two units by day 29; planting on day 28 cannot complete the supported two-day minimum.
- Each observed shop instance contributes demand, including duplicates. A single-product shop consumes two units per activation. The forecast uses an average rate for observed shops; it does not know future unlocks or hidden opponent inventory.
- Hires consume cash now and become available on the next turn. Daily hire costs follow the configured Fibonacci schedule; six hires cost 20 coins at the default multiplier, compared with seven for four hires.
- Mixed produce can be deposited and sold in one turn. Use `DROP` only when the whole inventory fits the reserved shed space; bounded `PLACE` retains excess otherwise.

Price and resource scenarios are covered by `tests/test_economics.py` and `tests/test_production.py`. Forecasts and workload approximations are explained separately in [the Step 3 CO notes](STEP_3_OPTIMIZATION.md); they are policy assumptions, not engine rules.

Step 4 adds engine-backed livestock checks. A pasture costs an action to build, animals pass through shed and worker inventory before placement, and feed is consumed from the acting worker. Daily production uses the previous pending care bonus before storing the latest day's care. Collected fertilizer can be sold, and unlike other products it has no town-center demand. Each daily reset deposits worker inventory within shed capacity, returns the farmer to spawn, and removes hired hands. The policy explicitly deposits and sells final-day output because no further daily reset can be assumed.

The frozen Step 4 policy has up to ten cow/sheep stations and nine hands. Tests compare output forecasts with the engine at multiple ages, inspect full-season feeding and inventory actions, check escapes and unfed animal-days, and validate final liquidation. [Step 3 server validation](benchmarks/step-3-server.json) also matches local resimulation. Market projections, reserves, and staffing are policy assumptions documented in [the Step 4 notes](STEP_4_OPTIMIZATION.md).

Step 5 shares maintenance across nearby livestock sites. Walking through locked tiles and sharing positions are legal, so its distance model uses Manhattan travel. A worker can carry feed for several animals; all pickups and deposits still share shed inventory and capacity. Tests cover multi-animal feed loading, product deposits that restore feed liquidity, unchanged installation actions, and stable protection of scheduled production after harvesting clears the available yield. Controlled full seasons check actual successful hire costs, care/feeding coverage, output quantities, escapes, and terminal inventory. The route menu, daily action allowance, and production-day singleton restriction are policy choices explained in [the Step 5 notes](STEP_5_OPTIMIZATION.md), not additional game rules.

After any environment upgrade, regenerate the lock deliberately, rerun these checks, and compare local configuration with real competition episodes before promoting a strategy.

Step 6 adds engine-backed crop schedules: four wheat units at age four without fertilizer, six melons at age ten with the planned bonus watering, and four one-unit strawberry events at ages 10/12/14/16. Fertilizer lasts three days including its application day; ongoing-crop bonuses depend on the preceding day's watering and active fertilizer. First watering is reserved as part of planting. Full mixed-game tests verify shared seeds, pickups, deposits, fertilizer consumption, legal harvest ages, feeding, and liquidation. Ripe crops can receive dispatch priority only with a budget for returning to livestock work.

An exhausted ongoing crop with zero held output is tracked separately from unplanned plant loss. Its exemption requires reaching the final production age and having no held yield; a test checks that unharvested output lost to decay is still counted as a loss. Workload allowances, receipt haircuts, supply buffers, and crop acreage bounds are policy assumptions, not engine rules. See [Step 6 CO notes](STEP_6_OPTIMIZATION.md).

The subsequently supplied Step 5 self-play and awarse episodes also match this interpreter exactly. Reconstructed runtime observations reproduce every Unicorns action. [Server audit](STEP_5_SERVER_ANALYSIS.md).

Source: [official Kaggriculture implementation](https://github.com/Kaggle/kaggle-environments/tree/master/kaggle_environments/envs/kaggriculture).
