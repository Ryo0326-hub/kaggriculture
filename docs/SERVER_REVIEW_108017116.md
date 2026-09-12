# Cycle 15 versus soumic 1088 — episode 108017116

Reviewed September 11, 2026. Unicorns is seat 0; soumic 1088 is seat 1.
Final banked coins are **85,532 versus 94,176**, an **8,644-coin loss**.
All 719 own decisions match frozen Cycle 15 on the recorded observations.
Both players finish `DONE`; our 719 runtime entries have empty stderr and the
largest duration is 0.251969 seconds. Source matching is behavioral because the
uploaded source is not attached. This game does not evaluate Cycle 17.

The main finding is another productive-scale disadvantage, with a useful
qualification: Soumic reaches almost the entire board but wastes much of that
capacity. We should combine stronger investment with our better maintenance,
rather than copy every expansion or trading action.

## The late reversal

| Recorded metric | Unicorns | soumic 1088 |
|---|---:|---:|
| Final banked coins | 85,532 | 94,176 |
| Land quadrants purchased/owned at end | 1 / 2 | 3 / 4 |
| Peak productive tiles | 30 | 96 |
| Peak installed animals | 5 | 14 |
| Peak strawberry plants | 19 | 51 |
| Strawberries harvested | 138 | 197 |
| Melons harvested | 60 | 138 |
| Wool harvested | 68 | 119 |
| Milk harvested | 102 | 94 |
| Wheat harvested | 84 | 271 |
| Wages over the season | 2,947 | 6,932 |

Harvest totals include six manually resolved night-boundary events; the JSON
preserves the daytime lower bounds and the separate adjustments. Harvesting
does not by itself establish delivery or sale. Different asset peaks need not
coincide, and a planted tile can still be immature.

Our largest cash lead is **37,500**, on UI Day 21, Turn 17. From the start of
Day 21, our bank grows by 39,793 while Soumic's grows by 83,916.
We enter Day 30 ahead **84,843–80,634**. The final day's net cash gains are
only **689 for us versus 13,542 for Soumic**. They take the permanent lead on
Day 30, Turn 2, after temporarily leading on Day 29.

This is not our failure to empty final inventories: our terminal shed, carries
and seeds are empty, with no unharvested animal output or remaining crops. Much
of our crop programme has simply finished. At the start of Day 30, we have one
carrot plant and five animals; Soumic has ten strawberry plants, seventeen
wheat plants, a carrot plant and eight animals, as well as goods ready to sell.
Future income and inventory matter alongside the visible bank balance.

## Soumic's strategy, viewed from their side

**Start with cheap labor, then reinvest heavily.** Soumic hires only three hands
per day on Days 1–9, compared with our eight to eleven. An early melon crop and
two sheep establish the opening; cows are added later. They move to six hands
on Days 10–11, nine on Day 12 and twelve every day from Day 13 onward.

**Use successive land purchases to plant large cohorts.** Their second, third
and fourth quadrants arrive on Days 10, 11 and 13. Strawberry purchases ramp
up around Days 11–14; visible strawberry plants rise from four at the start of
Day 11 to 43 at the start of Day 14. They also plant another melon cohort and
keep sowing wheat. By Day 18, Turn 21, their peak footprint contains 48
strawberries, 22 wheat plants, twelve melons, eight cows and six sheep: 96
productive tiles. Our peak is 30.

**Accept a weak-looking bank while assets mature.** Soumic starts Day 11 with
nine coins and Day 14 with 64, while we start Day 14 with 23,323. That cash
gap is partly a difference in investment timing. However, the tiny balance
also creates real constraints: they request nineteen cows and thirteen sheep
over the game, but stock changes confirm only nine cows and seven sheep were
bought. They request 58 strawberry seeds and receive 56. Requested orders
must not be treated as completed acquisitions.

**Collect a larger later stream in a supportive town.** Pizza, ice cream and
farmers market appear first; yarn shops appear on Days 13 and 16, followed by
smoothie, another farmers market and pet cafe. There are eventually four
strawberry buyers, three milk buyers and two wool buyers. Final quotes are
200 for berries, 287 for milk and 247 for wool. These support the economic
interpretation of the portfolio, but future shops were not knowable when the
early investments were made. We cannot infer the opponent's exact algorithm,
training method or intention from its actions alone.

## Where their strategy breaks down

**The farm exceeds what the dispatcher reliably services.** Eight animals
escape: six cows and two sheep, with combined original purchase costs of
3,400. The recorded pre-night tiles show an existing missed-feed streak and
no feed that day. Some escapes occur as early as Days 4 and 12. Although their
herd peaks far above ours, they harvest less milk: 94 versus 102. Later
installation and maintenance losses both matter; herd size alone is a poor
measure of useful production. There are no observed losses of uninstalled
animal inventory in this game.

Of 85 visible crop-to-weed transitions, **25 are normal exhausted strawberry
retirements**. The other 60 comprise 38 crops with positive held yield lost
and 22 premature zero-yield deaths. None of those transitions coincides with
a harvest or dig command on the tile. There are also twelve separate
last-turn plantings that become weeds immediately that night: nine wheat,
two strawberries and one melon. They consume seeds but never survive into
the next recorded day. The planting-day watering deadline matters.

Unlike Ahmed's game, neither side issues duplicate exclusive operations to
the same tile in one turn. Soumic's losses therefore cannot be explained by
that particular coordination defect. Their lower PASS fraction also does not
prove better economic utilization: travel, repeated replacement and failed
maintenance still consume actions.

**The second melon cohort oversupplies a weak market.** Our initial melon
sales mostly occur on Day 11. Soumic sells a 42-melon batch on Day 13, then
starts selling the next cohort on Day 22. The displayed pre-order quote falls
from 129 on that sale to 28 on Day 25; later that day, a six-melon sale realizes
just **six coins**. The latter receipt is independently reconciled: selling
six melons and buying one ten-coin wheat seed changes cash by −4. Displayed
quotes for the other batches are not their average execution prices.

Both players' supply affects this shared price. There is no evidence of a
deliberate market attack. The lesson is to value additional output against
existing supply and town consumption, including the crop cohort we can see
on the rival farm. Melons have no specialized shop buyer under these rules;
their replenishing demand is much thinner than berries in this town.

**Terminal scheduling still leaves money on the board.** Soumic ends with
seven wheat in the shed, and harvestable held output of four strawberries,
22 wheat and two carrots on the farm. There are also four unused wheat seeds
and one carrot seed. These are opportunities to investigate, not guaranteed
recoverable coins: travel, delivery and sale slots must fit before termination.

Finally, their repeated wheat BUY/SELL orders are not evidence of a free-money
strategy. At decisions 716 and 717, cash moves +384 then −384, and shed wheat
returns to its starting twelve units. That pair creates zero net cash.
Other trades would need their own accounting before attributing profit.

## What our agent does well, and the recurring input gap

Our animals all survive, no own crop becomes a weed, and all ten melon plants
are harvested for six units each at age ten. Final delivery is clean. This
supports preserving those protections while fixing growth admission.

Our nineteen strawberry plants complete all 76 production events. Of those,
62 produce two berries and fourteen produce one, for **138 rather than the
physical maximum of 152**. Every event is watered, including one tile watered
on the last action before the night. All fourteen single-yield events lack
active fertilizer. At those deadlines, fertilizer exists in worker inventories
but none is in the shed. On one night, five affected plants face only four
carried units in total.

This repeats Chloe's fertilizer finding. The relevant resource is a unit of
fertilizer available at the correct location before the production deadline,
not the farm's undated total inventory. A repair should reserve production
inputs, arrange pickup/delivery early enough, and choose the highest-value
applications when supply or time is scarce. The recorded berry quotes at the
fourteen deadlines sum to 2,946; one fertilizer quote per event sums to 1,015.
These are reference arithmetic, not a counterfactual profit estimate: route
costs, fertilizer coverage over multiple events and price impact are unresolved.
The input shortfall does not by itself explain the full 8,644-coin loss.

## The cash gap reconciles

| Cash component | Unicorns | soumic 1088 |
|---|---:|---:|
| Starting cash | 3,000 | 3,000 |
| Product sales minus wheat/fertilizer purchases | 91,759 | 121,098 |
| Seeds | −3,080 | −8,890 |
| Animals | −2,200 | −7,100 |
| Land | −1,000 | −7,000 |
| Wages | −2,947 | −6,932 |
| Final banked coins | **85,532** | **94,176** |

Fixed-price purchases are reconciled against stock changes, including seeds
consumed by immediate crop deaths; wages use accepted hires, with no unresolved
night-boundary hiring requests. The product row is the residual in this cash
account, not independently reconstructed gross sales by product.

Soumic generates **29,339 more net product receipts** and spends **20,695 more
on seeds, animals, land and wages**. The difference is exactly the 8,644 margin.
This is an accounting explanation, not proof that each additional investment
was profitable or that removing a cost would leave revenues unchanged.

## Strategy implications and CO connection

1. **Fund feasible production with time to pay back.** The recurring priority
   across Sergey, Julian, Chloe, Ahmed and this game is productive growth.
   Cycle 15's installation staffing discontinuity and overly discounted known
   demand were directly traced in the Ahmed review. Cycle 17 already changes
   those mechanisms; this older replay provides no performance validation for
   that candidate. More land is useful only when its funded crop/animal plan
   can be serviced and sold.
2. **Reserve tasks and inputs through their deadlines.** Feed prevents the loss
   of an entire asset and its remaining income; fertilization adds marginal
   yield. Allocate labor and inputs across the complete workday, with delivery
   before the final sale deadline. This is a resource-constrained scheduling
   problem. Input value depends on both location and time.
3. **Price marginal supply, not just today's quote.** Additional melons in this
   replay eventually face the one-coin floor. Existing shops and rival maturing
   cohorts should inform the next investment. This is an endogenous-price
   optimization problem: our own planned supply also changes realized prices.
4. **Treat cash, land, workers and storage as separate constraints.** In CO250
   terms, each binding constraint has an opportunity cost. Fibonacci hiring
   makes capacity discrete: compare whole feasible service plans and their
   actual extra wage bill, rather than average cost per worker. These are
   useful duality and integer-programming interpretations; the replay does not
   show that either bot actually solves an LP or IP.

From our side, the opportunity is better use of affordable service capacity
while retaining clean execution. From Soumic's side, the opportunity is to
protect the productive assets already bought, avoid weak-demand melon waves,
and finish collection earlier. The target is more bankable net output, not a
96-tile footprint or a large early cash lead.

Only this report, its [machine-readable evidence](benchmarks/server-review-108017116.json)
and the performance-plan note change. Cycle 15 and Cycle 17 remain unchanged.
No local game, counterfactual episode, training or Kaggle upload was run.
