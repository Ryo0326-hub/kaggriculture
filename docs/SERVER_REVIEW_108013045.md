# Cycle 15 loss to Chloe — episode 108013045

Reviewed September 11, 2026. Unicorns is seat 0. Final banked coins are
**90,928 versus 92,597**, a **1,669-coin loss**. Both players finish `DONE`.
All 719 own decisions match frozen Cycle 15 on the recorded observations.
The own runtime log has no nonempty stderr; its largest recorded duration is
0.204720 seconds. This does not evaluate the newer Cycle 17 candidate.

Source identification is behavioral: the uploaded Python file is not attached.
The matching frozen source hash is
`ce4444126f5ef7e0ee01a22f395ae87ee442ec2f329c4feb6aedf0687af45f1a`.

## The late reversal

Our maximum cash lead was **37,413**, at the start of UI Day 21. We still led
89,211 to 81,590 at the start of the final day. During that day, our bank grew
by 1,717 and Chloe's grew by 11,007. The 9,290 difference erased the 7,621 lead.
Chloe first passed us at the recorded state on Day 30, Turn 20; after a brief
cash reversal during its wheat transactions, it led permanently from Turn 22.

We reached our final 90,928 at recorded state 709, Day 30, Turn 14. Our terminal
shed, carries and seed inventory are empty, and every remaining crop/animal
has zero held yield. There is no observed uncollected own terminal harvest to
explain the loss. The remaining tomato plant is exhausted, with zero output.

As in the Julian and Sergey losses, current bank balance understated the
opponent's remaining production and unsold inventory. That is the useful
strategic pattern; the profitable product mix differs between towns.

## Chloe's strategy

| Recorded metric | Unicorns | Chloe |
|---|---:|---:|
| Peak productive tiles | 29 | 56 |
| Final owned quadrants | 2 | 3 |
| Peak cows | 3 | 10 |
| Peak sheep | 3 | 0 |
| Strawberry plants established | 19 | 42 |
| Confirmed strawberry units harvested | 141 | 168 |
| Confirmed milk units harvested | 102 | 160 |
| Confirmed melon units harvested | 72 | 136 |
| Total wages | 3,916 | 3,080 |
| Recorded unit commands | 7,070 | 6,697 |
| PASS share of those commands | 41.0% | 28.6% |

The passive base report counts within-day harvests. Two additional harvests
crossing nights were resolved directly from the recorded tiles: two of our
strawberries at decision 431 and two of Chloe's milk units at decision 671.
Thus this table includes them rather than mixing lower bounds with totals.
Harvested output still differs from delivered or sold output.

Chloe initially buys 23 melon seeds and two strawberry seeds, then uses seven
hired hands per day through Day 11. Its first large cash receipt finances ten
cows and two land purchases on **Day 12**, followed by a large strawberry
planting wave. At the start of Day 14 it already has 41 strawberry plants and
ten cows; the strawberry count eventually reaches 42. From Day 12 onward it
hires ten hands per day. It does not use fertilizer.

That portfolio fits the observed economy. An ice cream shop opens on Day 4,
farmers markets on Days 7 and 10, then smoothie shops and another ice cream
shop later. By Day 25, seven of the eight shops consume strawberries and five
consume milk. At the start of Day 30, the quotes are **284 per strawberry and
274 per milk** despite both players' sales. Wool has just one yarn store.
These are displayed quotes, not batch-average realized sale prices.

We react in the right direction, including an additional cow on Day 5 and
nineteen strawberry plants. But the cow count remains three, and our additional
sheep arrives only on Day 22. Our productive footprint is much smaller while
the market continues to absorb the opponent's larger berry/milk supply.

## Cash accounting: the margin is fully explained

Observed seed-stock changes plus successful planting reconcile every seed
purchase. Changes in installed/carried/stored animals identify animal purchases.
Land transitions and accepted daily hires determine their fixed costs. Product
net receipts below are then the residual in the bank account:

`final cash = starting cash + product sales - wheat/fertilizer purchases`
`             - seed costs - animal costs - land costs - wages`.

| Cash component | Unicorns | Chloe |
|---|---:|---:|
| Starting cash | 3,000 | 3,000 |
| Product sales minus wheat/fertilizer purchases | 98,744 | 107,857 |
| Seed costs | −3,200 | −8,180 |
| Animal costs | −2,700 | −4,000 |
| Land costs | −1,000 | −3,000 |
| Wages | −3,916 | −3,080 |
| Final banked cash | **90,928** | **92,597** |

Chloe generates **9,113 more net product receipts** while spending **7,444 more
on the four cost categories**, leaving precisely 1,669. This reconciles the
total cash gap without claiming to have reconciled every product's sale price
or gross sales separately. It does not isolate the causal value of a purchase.

Our higher wage bill is a second optimization target. Chloe's larger farm
coexists with 836 less wage spending. PASS includes necessary waiting, and
geography and timing differ; we cannot simply delete 836 of our wages while
assuming all output survives. The evidence favors charging shared route costs
and discrete crew sizes rather than treating each additional asset as requiring
its own worker.

## Our execution advantage, and a concrete timing opportunity

Our nineteen strawberry plants produced **141 units**, versus Chloe's 168
from 42 plants: about **7.42 versus 4 units per plant**. All twelve of our
melons yielded six units. No own animal disappeared and no own crop became a
weed. These are useful behaviors to retain when increasing the productive area.

The recorded strawberry refreshes expose a narrower opportunity:

- Nineteen plants have 76 production events. Sixty-five events add two units;
  **eleven add only one**, giving 141 instead of the 152-unit fertilized maximum.
- None of those eleven events has active fertilizer. All eleven were watered
  at the refresh: one receives its water on the day's final recorded action.
  The night actions do not supply a missing fertilizer application. This is a
  confirmed fertilizer bonus gap, not eleven lost plants or missed watering.
- At ten of the eleven events, some fertilizer is being carried elsewhere on
  the farm, while the shed has none. Cash is ample. This points to input
  positioning and deadline scheduling, but does not prove the carried stock
  was unreserved or could reach those plants in time.

At the quotes immediately preceding those refreshes, eleven extra berries total
**2,742 coins**. Charging one fertilizer unit per event at those same quotes
costs 815, leaving **1,927 before extra labor, delivery and price effects**.
This is screening arithmetic, not a predicted or guaranteed improvement.
Fertilizer lasts three days, so applications can sometimes cover two production
events; conversely, travel, alternative input uses and market impact can reduce
value. The 1,669 match margin makes this a concrete scheduling issue worth
checking, but there is only a 258-coin buffer in that simple arithmetic.

Use a dated fertilizer job: reserve a real unit, get it to the plant, water and
apply before the production refresh, and include the delivery/sale of the added
yield. Compare its marginal cash against other jobs competing for the same
worker. Merely raising a fertilizer preference score would not establish that
the job is executable. No policy change is made in this review.

## Behaviors we should not copy without examination

**Storage overflow.** At recorded state 263, Chloe holds 132 melons and two
strawberries across its inventories, with an empty shed. Every worker then
passes and there are no market orders. The next day's shed contains 98 melons
and two strawberries, exactly its 100-unit capacity: **34 harvested melons
were discarded** during the overnight transfer. Those are physical lost units;
multiplying them by one quote would overstate a guaranteed cash improvement.
The existing night-deposit strategy still needs a storage-capacity constraint.

**Seed purchasing and feeding.** Chloe ends with eighteen unused strawberry
seeds and one tomato seed, costing 1,850 in total. One cow escapes during the
Day 25-to-26 refresh after two unfed days. Its final inventory contains seven
wheat and four milk units. A larger herd also needs reliable feed delivery and
a final sale route; volume alone is insufficient.

**Normal crop retirement.** All 43 Chloe crop-to-weed transitions involve
exhausted crops with zero held output: 41 strawberries at age 17 and two
tomatoes at age 12. They are not 43 crop failures or lost harvests. Keeping
this distinction prevents us from diagnosing legal crop retirement as a bug.

**Wheat turnover.** Chloe requests 5,862 wheat purchases and 5,976 wheat sales,
but harvests only twelve wheat units. Requested turnover is neither production
nor profit. The pinned market code quotes buys at post-buy inventory so an
unchanged-market round trip nets zero. In this replay, three isolated equal-size
sell/buy pairs leave both the full private state and cash unchanged. This does
not establish the profitability of all its trades; cross-turn demand and rival
orders can move prices. There is no evidence here for adopting the repeated
turnover as a free-money mechanism.

## CO implications and next priorities

The investment problem resembles an integer program with production batches,
dated cash balances, finite land, daily labor and finite storage. Fertilizer is
another decision sharing those constraints. A cash lead is not a reason to
stop investing while a feasible asset still has positive remaining contribution.
Crew wages are discrete and convex, so batch costs must reflect the additional
workers actually required rather than a fixed per-asset labor charge.

The loss evidence now supports two complementary priorities:

1. **Demand-responsive production growth.** Julian's early yarn store favored
   sheep; this town favors berries and milk; Sergey expanded milk in another
   favorable town. Retain our efficient yields while expanding funded batches
   that fit actual service routes and sell before the season ends.
2. **Deadline and capacity discipline.** Investigate the eleven own berry bonus
   gaps, preserve clean terminal delivery, and prevent a larger farm from
   overflowing its shed. Do not import Chloe's oversized seed queue or feed
   failures along with its productive scale.

[Cycle 17](CYCLE_17_RESULTS.md) already targets shared routes and investment
admission; it remains unchanged and needs its own server evidence. This replay
does not establish that it has fixed these issues. Continue reviewing the
losses the user supplies; wins would broaden the evidence but are not a
prerequisite for identifying a concrete repair. No new upload is proposed here.

[Machine-readable evidence](benchmarks/server-review-108013045.json) ·
[Julian comparison](SERVER_REVIEW_108009995.md).
The base counters come from `scripts.study_recorded_games.study(path, name)`;
the supplemental evidence uses recorded state differences and fixed-cost
accounting. No local match, simulator import, state advance, training, model API
or paid compute was used.
