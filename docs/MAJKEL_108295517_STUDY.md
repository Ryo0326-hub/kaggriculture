# Majkel loses to M & M & P & Q: portfolio risk and the last deliveries

Episode **108295517**, supplied by the user, ends **108,315–105,196**. M & M & P & Q
is seat 0; Majkel1337 is seat 1. Both finish DONE. This is a **3,119-coin** loss,
not a crash, missed land expansion or overwhelming defeat. All 720 recorded
states and 719 joint decisions were inspected passively. No local game or
counterfactual was run. UI dates below are one-based.

[Machine-readable evidence](benchmarks/majkel-108295517-study.json) records the
input hash, observed purchases, production, cash, exceptions and final orders.
Mechanics were checked against the pinned 1.32.7 source, without importing it.
Recorded private inventories can be inspected for both players in this report;
the submitted agent sees only its own private inventory.

## The accounting explanation

| Account | Majkel | M & M & P & Q |
|---|---:|---:|
| Starting cash | 3,000 | 3,000 |
| Net product receipts after product purchases | 124,244 | 130,808 |
| Seeds | −5,840 | −7,040 |
| Animals | −8,300 | −11,100 |
| Land | −3,000 | −3,000 |
| Wages | −4,908 | −4,353 |
| Final coins | **105,196** | **108,315** |

The receipt row is the cash residual after reconciling confirmed fixed purchases
and accepted wages, not independently reconstructed gross sales. Majkel saves
**3,445** on these costs but earns **6,564** fewer net product receipts:
6,564 − 3,445 = **3,119**, exactly the loss. The rival pays 555 less in wages while
buying more animals and seeds. More spending alone is not the explanation.

Both buy two additional quadrants. Majkel buys them on Day 7 Turn 6 and Day 11
Turn 3; the rival on Day 7 Turn 1 and Day 11 Turn 1. Peak productive tiles are
70 versus 75. Buying a fourth quadrant is not the lesson of this replay.

## The town favored a different output mix

The town reveals yarn, pizza, bakery, pet cafe, bakery, yarn, bakery and pet cafe,
on Days 4, 7, 10, 13, 16, 19, 22 and 25. There is **no strawberry shop**, only one
milk shop, and eventually three egg/wheat bakeries, two carrot cafes and two yarn
stores. Neither player could know these unrevealed shops in advance.

| Confirmed harvested units | Majkel | Rival |
|---|---:|---:|
| Wheat | 680 | 711 |
| Milk | 158 | 96 |
| Wool | 295 | 233 |
| Eggs | 0 | 174 |
| Carrots | 60 | 241 |
| Tomatoes | 75 | 137 |
| Strawberries | 69 | 32 |
| Melons | 72 | 96 |

These totals include attributable boundary harvests. One immediate newborn wheat
weed event remains unresolved; it does not affect the milk/berry conclusions.
Harvest is not sale: goods still need delivery, storage and an executed order.

Majkel buys seven cows and eleven sheep, with no geese. The rival buys seven
cows, thirteen sheep and six geese over the season; these are purchase totals,
not simultaneous herd sizes. Its first goose is installed on Day 3 and the second
on Day 4, before a bakery appears. That early egg investment may be a generic
opening or a forecast; the replay cannot identify its reasoning. Later egg
capacity has visible buyer support.

Majkel plants 17 strawberries by Day 8, while demand remains only the town-center
baseline. The rival plants 85 carrots over the season versus Majkel's 24, and
19 tomatoes versus 12. Majkel starts carrots only on Day 22, nine days after
the first pet cafe opens. The rival is better positioned for that market.

At the start of Day 13, milk is quoted at 181 and strawberries at 149. By Day 22
the quotes are 30 and 20; by Day 29 they are 19 and 1. Meanwhile eggs remain
around 50–59 and carrots around 39–42 late in the season. These are observed
market quotes, not average realized sale prices. Both farms' supply and town
consumption drive them; the log does not prove intentional price manipulation.

Majkel's heavier milk/berry exposure is less suitable here than in
[its 178,462-coin win against the same opponent](MAJKEL_108305451_STUDY.md), where
multiple ice-cream shops and a smoothie shop supported those products. A cash
target like 150K is consequently not a universal threshold for a good policy.

## Execution imperfections compound the exposure

Five Majkel strawberry plants die before first maturity: one on Day 11 and two
each on Days 13 and 15. Of 45 observed strawberry production events, only 24
receive the fertilizer bonus; six occur without watering. In its earlier win,
all 41 strawberries reached four production dates and 146/164 events received
the bonus. Here, more planted capital does not consistently become output.

Majkel also issues **87 duplicate WATER commands**, 27 duplicate CARE commands,
22 FEED, 22 COLLECT_FERTILIZER, 19 HARVEST, 15 PLANT and one FERTILIZE command on
the same tile in the same decision. These are extra requests, not successful
additional work. Movement reversals remain fairly low at 31, so this loss is not
the severe route oscillation previously seen in our Cycle 18 failures.

The rival is not mechanically flawless: eight strawberries die before maturity;
111 of 477 animal-night records are unfed, and 49 production events have no care
bonus. Majkel has only 20/413 unfed records and seven zero-bonus events. The rival
nevertheless wins through delivered output and its economics. This is evidence
against blindly copying neglect or using perfect maintenance as the sole metric.
Some late animal disappearances follow the last useful production date; not all
are economically harmful escapes. Intentional retirement versus failed service
cannot be inferred from an absent FEED command alone.

## The apparent cash lead hid the rival's inventory

Majkel leads by 6,891 at the start of Day 24. At that moment the rival holds
70 melons in its shed; subsequent sales contribute to the reversal. Its melon
sales are concentrated in only six decisions, including 40 units on Day 25
Turn 1. Majkel sold its earlier melon cohort by Day 16. Delayed sales are one
reason cash balances alone misrepresent who is ahead. Holding was risky too:
the melon quote drops from 202 at the start of Day 24 to 62 on Day 26.

Both sides gain almost the same cash on the final day: **11,804 Majkel** versus
**11,845 rival**. Their delivery schedules create another temporary reversal:

| After final-day action | Majkel cash | Rival cash | Majkel lead |
|---|---:|---:|---:|
| Turn 17 | 100,912 | 98,817 | +2,095 |
| Turn 21 | 104,683 | 100,536 | +4,147 |
| Turn 22 | 104,688 | 105,198 | −510 |
| Turn 23, final action | 105,196 | 108,315 | **−3,119** |

In the last two actions the rival deposits and sells, among other output,
105 wheat, 40 carrots, 16 eggs and 16 wool. Its cash increases **7,779**, versus
Majkel's **513**. Majkel's final 22-milk sale faces a weak market. It ends with
only one milk and three fertilizer in the shed and no carried stock. The rival
ends with an empty shed and carries. This is not a loss explained by thousands
of forgotten terminal goods, nor proof that selling later is always better.

## What changes in our agent

Cycle 19 already reserves each tile once, budgets feed before expensive hiring,
supports geese/carrots/tomatoes, and requires final harvest delivery. Those rules
address several observed failures. The user reports submitting Cycle 19; no own
Cycle 19 server replay has yet been supplied, so this report cannot diagnose its
actual performance.

The audit found two related weaknesses worth correcting in a bounded challenger:

1. **Investment price risk.** Cycle 19 uses a lifetime-average supply rate and
   blends 35% of today's quote into every forecast. Even if the projected future
   price reaches one coin, today's expensive quote keeps the investment looking
   partially attractive. It also ignores stored field output/own inventory in
   that forecast and treats gross wheat production as supply without feed use.
2. **Survival scheduling.** Route commitments and geographic order can outrank
   a different plant's second unwatered night. Urgency was mostly a tie-break
   in outside-sector work, not an explicit rescue priority.

[Cycle 20](CYCLE_20_OPTIMIZATION.md) prices the visible production commitments on
their actual maturity/remaining-production dates, includes known unsold output,
subtracts estimated wheat feeding and stops cushioning projected price falls
with today's quote. In the last six ordinary-day actions it prioritizes feasible
at-risk feeding/watering over routine tasks, retaining resource checks and target
reservations. It preserves the Cycle 19 opening, land and hiring rules.

For example, on Majkel's recorded Day 10 observation, the internal extra-cow
score changes from approximately +3.90 to −12.36 and the strawberry score from
+0.58 to −8.09. These are heuristic ranking scores from **independent decisions
on someone else's observation**, not coins earned or a counterfactual result.
They demonstrate a response to crowding, not a verified competitive improvement.
