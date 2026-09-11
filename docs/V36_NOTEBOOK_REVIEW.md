# V36 public notebook — strategy and lessons for our agent

September 11, 2026. Ryo reports submitting our latest candidate and finding a notebook scored 2705.7. The submission ID, exact uploaded bytes, server validation and rating have not been independently checked this turn. Cycle 13 gameplay evidence remains pending.

Reviewed the supplied `kaggriculture-v36-guarded-four-turn-sales.ipynb`, attributed to Ahmed Berat Özer. [Public notebook](https://www.kaggle.com/code/ahmedberatozer/kaggriculture-v36-guarded-four-turn-sales). This was **static analysis only**: read notebook JSON, parsed Python syntax, decoded compressed JSON schedules, and compared existing replay actions. No notebook cells, foreign agent code, engine, match, training job or external API were executed. The notebook's instructions to run cells were treated as document content.

Notebook SHA-256: `5cefaf9299049e0ee61c83f22869d0916647fe9f495d68b1b20e22c0093b6224`. Extracted cell-4 agent SHA-256: `7eb5ab6c48581c82906ab6fa6b2cc5c9607513249ef59b2c45fcd6176e8653dd`, matching the notebook's expected hash. [Static findings and replay hashes](benchmarks/v36-notebook-static-review.json). Source line numbers below refer to the extracted agent without the `%%writefile` line.

## Architecture: prepared schedules with reactive corrections

Thirteen compressed schedules each contain 719 action dictionaries. At step 144 the router selects a schedule using the ordered first two shops; at step 648 it switches to a common closing schedule. Weed repairs and worker alignment adapt scheduled work to observed state. Later layers handle market execution, conditional production projects and final delivery.

The raw base schedule requests twelve melon, 163 wheat, thirty-three strawberry and thirty-one carrot seeds, and land at steps 150 and 265. These are requested quantities, not confirmed production or executed purchases. Animal purchases vary between routes; the raw schedules request at most eleven or twelve hires per day. Full-route totals are descriptive: the active agent switches routes and applies overlays.

Enabled settings matter. The generic chassis advertises several guards, but its initial budget, room, clamping, dead-stock, terminal-liquidation and opponent-plan front-running switches are **off**. Later wrappers implement specific storage, investment, liquidation and sale protections. Reading the feature list alone would overstate which generic controls run. Sources: lines 939–962 and subsequent `agent` wrappers.

No model weights, neural inference, LLM client or network-dependent decision path appear in the reviewed source. The compressed payload is action data; runtime imports are standard-library modules. Source inspection cannot establish whether upstream authors used LLMs, mathematical optimization or learning to create those schedules.

## Direct connection to the Gekkotron evidence

We compared recorded decisions with raw public schedules, choosing the middle route from shops already visible at step 144 and the closing route from step 648. We did not execute the router or its overlays.

| Gekkotron episode | Middle route | Identical farmer/hand decisions | Identical non-sale order sequences |
| --- | ---: | ---: | ---: |
| 107970619 | 0 | 710 / 719 | 719 / 719 |
| 107974608 | 8 | 712 / 719 | 718 / 719 |

In the second game, **every worker decision before the last seven turns matches**. Its sole non-sale difference is a one-unit wheat purchase at step 362. This strongly supports a shared schedule family; it does not prove identical private source or identify the author of the original schedules. Similar farming by differently named bots can therefore reflect shared schedules, with different trading and repair layers.

Our earlier [Gekkotron versus kyy666 study](CYCLE_13_SERVER_STUDY.md) found identical worker and non-sale actions between those players but a 2,822-coin final gap. V36 supplies a concrete source-level example of trading overlays distinguishing agents with the same production schedules. These observations do not establish that Majkel uses this code.

## Four economic mechanisms

### Advance physical surplus sales

Despite its name, V36 does **not** hold products for four turns. During steps 288–695 it looks up to four turns ahead in its own schedule and sells already available goods earlier. It records deductions against future scheduled sales to avoid counting the same stock twice.

Reservations use stock projected after current worker actions. They exclude wheat and fertilizer, protect pickups/purchases, avoid ambiguous animal placement, respect the order limit, and stop at the next 72-turn shop boundary or the final-day boundary. Older similarity/probe logic remains in the source, but the final V36 override fixes this window at four regardless of those signals. Sources: `_r36_reserve`, `_r36_suppress`, lines 1636–1694 and 1866–1876.

**Our overlap:** Cycle 13 already sells available surplus each turn after preserving feed/fertilizer needs. It has no future action tape from which sales need to be advanced. Copying the debt ledger would add machinery without establishing a new benefit. Earlier physical delivery might help, but costs worker time and is a separate scheduling decision.

### Order sales by revenue exposed to rival supply

The pinned engine processes orders by list index, then per unit. At a shared index, both players' next units are quoted before either commits. There is no universal seat advantage at that index; **product order can still change exposure to earlier rival orders**. Checked in `_process_market`, lines 544–626, without executing the engine.

V36 ranks distinct products within contiguous sale blocks using:

\[
D_c(q,b)=R_c(I_c,q)-R_c(I_c+b,q),\qquad
R_c(I,q)=\sum_{j=0}^{q-1}p_c(I+j).
\]

Here `q` is physically available sale quantity, `I` is current market supply, and `b` is a hypothetical rival batch. A larger `D` means more own revenue would be lost if the rival supplied that product first. V36 uses eight to twenty-four rival units, increasing with visible ripe output. Eight units is a scenario, **not recovered hidden stock**. Sources: `_r37_quote_priority`, `_r37_reorder_sales`, lines 1757–1802.

The CO connection is a scheduling heuristic based on marginal delay cost. It is not an exact optimal sequence or Nash equilibrium: it does not predict the opponent's complete order list. Nominal price alone is insufficient; sale quantity and the price curve's slope matter.

**Our gap:** the existing surplus loop uses fixed `MARKET` product order. A narrow challenger could keep workers, quantities, reserves and purchases unchanged while ranking the initial sale block by exposure. Preserve purchase barriers and same-turn deposit accounting. Evaluate actual receipts and relative cash in returned server logs; do not assume V36's batch parameters are optimal for our farm.

### Opening market sequences affect relative wealth

V36 replaces its raw opening with `BUY_PRODUCT WHEAT 13`, `BUY_PRODUCT WHEAT 30`, `SELL WHEAT 30`. The raw opening buys thirteen, sells thirteen, then buys thirteen.

This exact contrast already appears in supplied episode **107970619**. After the first action, Gekkotron's old sequence leaves **2,604 coins and thirteen wheat**; Subin An's revised sequence leaves **2,656 coins and thirteen wheat**. Both started with 3,000 coins: a **52-coin advantage in this recorded interaction**, before subsequent farming.

The engine quotes buys at post-buy supply: a fully filled ordinary buy/sell round trip above the price floor has zero isolated gain if nobody changes that market. The other player's intervening trades matter here. This is an opponent-dependent execution tactic, not unlimited arbitrage. Temporary funding, capacity and partial fills must be considered.

**Our decision:** keep this as a separate hypothesis. Our opening has different feed and investment obligations. Adopting it would require funding/stock checks and evidence that relevant opponents expose the opportunity. It should not be bundled into the first recurring-sale-order experiment.

### Fund complete production projects

The notebook's reactive overlays go beyond choosing the highest current price:

- **Cattle substitution:** in steps 216–227, sufficient milk-shop demand and no yarn shop can replace selected scheduled sheep purchases with cows. The controller confirms actual purchases, redirects pickup/placement and accounts for extra milk.
- **Tomato expansion:** at internal day 18, qualifying tomato demand, price at least seventy and cash at least 12,000 can trigger the fourth quadrant, ten tomato seeds and dedicated labor. Land plus seeds cost 4,500 before optional fertilizer, wages and working capital. The controller serves the remaining production window and sales.
- **Sheep expansion:** at internal day 12, two yarn shops, wool at least 220 and wheat at most forty-five can trigger the fourth quadrant plus six sheep. Land and sheep cost 7,000 before feed/labor. Two additional workers serve the project, installation resources are confirmed, and extra wool/fertilizer are tracked. Initial financing preserves a 3,000-coin buffer.

Days here are zero-based: internal day 12 is UI Day 13 and internal day 18 is UI Day 19. Sources: `_v231_*`, `_v219_*`, `_v233_*`, lines 1216–1422, 1500–1608 and 1913–2069.

The CO connection is a **fixed-charge integer investment with resource constraints**. Land produces nothing alone: fund seeds/animals, installation, recurring labor, feed and cash reserves together. Cycle 13 already evaluates marginal bundles under demand/supply stress and charges cannibalization of existing output. A remaining restriction is our three-quadrant cap, which excludes these fourth-quadrant projects. Revisit it after our larger farm demonstrates reliable maintenance; additional land is not automatically profitable.

## Final delivery is a separate optimization problem

At step 712 the notebook can examine seven remaining actions through step 718. Its planner caps candidate evaluations at sixty-four, with additional baseline/recheck calls. It considers short worker collection/delivery alternatives and requires physical delivery gains while protecting baseline obligations. Observation guards can abandon a plan. This uses a limited physical model and current prices, not a full forecast of rival market decisions.

Tomato/sheep commitments disable this planner because its baseline model does not contain those added obligations. The general lesson is to optimize **cashable output before the deadline**, with consistent investment and terminal models. We already have terminal delivery/sale safeguards. Further changes should target actual stranded cargo in our logs, beginning with latest-departure and route feasibility calculations. No new local rollout or planner was run or added in this review.

## What the reported benchmarks establish

The notebook reports these V36-versus-V35 comparisons; their underlying experiment files were not supplied or reproduced here:

- **512 recorded-opponent games:** 53.13% versus 48.63% wins, a reported +4.49 percentage-point improvement. Opponents replay recorded actions rather than executing private reactive policies. Its eight wins against Majkel records are not eight live wins against Majkel's current bot.
- **1,856 reactive games:** 96.12% versus 90.68% strict wins. Many entries share one schedule family. Equal-family outcome improvement is +1.32 percentage points. Its overall +3.93-point outcome improvement counts ties as half, so differs from the strict-win-rate change.
- The evaluation text identifies comparator V35 as user-reported near 2700 and explicitly does not independently establish a V36 live rating. Ryo's 2705.7 observation is useful context, but has not been verified against these exact downloaded bytes.

These results support hypotheses, not a promise that adaptation gives us 2700 or 3000. Many opponents are related public schedules. Production capacity and accumulated earlier improvements also contribute: the title does not establish four-turn sales as the cause of the entire score.

## Next priorities

1. **Read Cycle 13 server validation and games.** Confirm identity; inspect maintenance, throughput, wages, prices, inventory and terminal delivery. Fix execution failures before pursuing small trading gains.
2. **If production is sound, isolate marginal-impact sale ordering.** Keep production, hiring, quantities and input reservations fixed. Use static/bounded accounting checks, then a user-run Kaggle submission and returned logs. This is the strongest directly transferable new mechanism from this review.
3. **Keep opening wheat sequencing separate.** It is an opponent-dependent cash-flow hypothesis.
4. **Consider funded fourth-quadrant projects or better terminal collection when our logs show the opportunity.** Adapt our existing strategy instead of replacing it wholesale with these schedules.

No agent implementation or submission bytes changed. No GPU, training or Featherless access is needed for the identified next candidate. Credit this notebook and its upstream authors if an idea is implemented; preserve applicable notices if code is reused.
