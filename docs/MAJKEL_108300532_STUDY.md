# Majkel1337 versus SpaTaro — repeatable structure, different product mix

Reviewed September 12, 2026. Episode **108300532**, Majkel seat 1, ends
**90,293–81,479**, a win by **8,814** banked coins. Both finish DONE. The user's
current-rank description is not independently verified by this replay.

This analysis reads recorded observations/actions; it does not run a game.
[Evidence](benchmarks/majkel-108300532-study.json) includes input hash, confirmed
acquisitions, passive cash accounting, maintenance and boundary-adjusted harvests.
The earlier [178,462-coin win](MAJKEL_108305451_STUDY.md) provides the comparison.

## The common structure and important differences

| Majkel metric | Versus SpaTaro, 108300532 | Versus M & M & P & Q, 108305451 |
|---|---:|---:|
| Final coins | 90,293 | 178,462 |
| Peak productive tiles | 74 | 74 |
| Final owned quadrants | 3 | 3 |
| First land purchase | Day 7 Turn 6 | Day 7 Turn 6 |
| Second land purchase | Day 10 Turn 6 | Day 10 Turn 12 |
| Cow/sheep/goose acquisitions | 7 / 3 / 4 | 14 / 3 / 0 |
| Strawberry seeds actually acquired/planted | 25 | 41 |
| Tomato / carrot seeds actually acquired | 14 / 30 | 0 / 0 |
| Wheat / melon seeds actually acquired | 224 / 12 | 153 / 12 |
| Wages | 4,929 | 5,018 |
| Adjacent reversal pairs | 39 | 31 |

Both openings buy one cow plus five wheat, followed by a second cow, three sheep
and four hires. Ten wheat plants and twelve staggered melons bridge the opening
into animal and longer-maturity crop receipts. Cash is only 34 at the start of
Day 3 in the SpaTaro game. The second quadrant again arrives immediately after
first sheep production. Staffing reaches eleven hands for Days 11–28 here,
versus Days 10–28 in the previous game, then ten on the last two days.

The first two shops are **BAKERY and PET_CAFE**, rather than two ice-cream shops.
Majkel installs **four geese and two additional cows on Day 7** in its new central
livestock area. It begins tomatoes before the pizza shop appears on Day 10;
this might reflect an opening prior, not observation of future shops. We must
not turn the recorded future town into information available to our bot.

Later shops are pizza, brunch, two ice-cream shops, another brunch and another
pet cafe. This supports a broader mix of eggs, wheat, tomatoes, milk, berries
and carrots. Majkel still retains its original three sheep without a yarn shop.
That is not proof every opening investment is optimal for this town.

By Day 8 it has four cows, three sheep, four geese, sixteen berries, twelve
melons, one tomato and five wheat plants. By Day 11 it has six cows and twenty-one
wheat plants. Its seventh cow is installed on Day 19. At the start of Day 25,
there are forty-two wheat plants, nine tomatoes and eight berries alongside the
herd. Crop turnover continues as early berries retire.

## Why Majkel wins this particular game

| Reconciled cash account | Majkel | SpaTaro |
|---|---:|---:|
| Starting cash | 3,000 | 3,000 |
| Net product receipts after product purchases | 107,722 | 97,649 |
| Seed purchases | −7,000 | −7,160 |
| Animal purchases | −5,500 | −5,600 |
| Land | −3,000 | −3,000 |
| Wages | −4,929 | −3,410 |
| Final cash | **90,293** | **81,479** |

The product row is the residual after confirmed fixed-price acquisitions and
wages, not separately reconstructed gross receipts. Majkel spends **1,259 more**
outside product trading, produces **10,073 more net product receipts**, and wins
by **8,814**. In the prior win, its advantage was lower cost despite slightly
lower net product receipts. The objective is profit, not always spending less.

Harvested output, including identifiable night-boundary collections:

| Product | Majkel | SpaTaro |
|---|---:|---:|
| Wheat | 729 | 614 |
| Milk | 178 | 202 |
| Eggs | 163 | 0 |
| Wool | 55 | 73 |
| Strawberries | 161 | 162 |
| Tomatoes | 94 | 0 |
| Carrots | 66 | 323 |
| Melons | 72 | 66 |

Majkel is not simply better on every product. It directs resources toward a
broader portfolio including eggs and tomatoes while producing more wheat.
SpaTaro requests many product purchases/resales; request totals cannot establish
fills or a trading loss. The net cash account already includes their combined
contribution. Nor can the replay isolate how much of Majkel's advantage comes
from portfolio mix versus sale timing and service.

## Service and selling

The same compact installation structure repeats: opening animals beside shed
access, northeast additions within a few moves, then southwest cows extending
from the center. Thirty-nine reversal pairs are far below our reviewed Cycle
18 losses (357 and 507). This supports committing to useful work rather than
continually changing routes. It does not prove optimal tours; SpaTaro has zero
reversals and still loses.

Majkel uses 127 fertilizer commands versus SpaTaro's 78. Its 729 harvested wheat
units support both feed and sales. In this game it has 88 strawberry production
events, only 73 with a fertilizer bonus, and five animal production events without
feeding/usable care bonus. It is less reliable than in the prior example. Its
25 berry plants do not all reach four production events: later additions have
shorter remaining horizons. Those are reasons to preserve our working input and
maturity checks, not copy all of the winner's decisions.

Sales also differ by commodity. There are sixteen egg sale decisions; the first
is Day 13 Turn 23 for 27 requested units, followed mostly by late-day batches.
Tomato sales begin on Day 17, frequently near the start of a day. Strawberry
sales begin on Day 14, while carrots sell in an earlier cluster around Days
18–19 and again late in the season. This is not a universal fixed four-turn
selling rule. Sale request quantities are not assumed to be fully executed.

Majkel enters Day 30 with 77,733 coins and gains another 12,560. Its terminal
shed and seed inventories are empty. The selected game supplies a useful target
for prompt liquidation, not evidence of a universal 150K production requirement.

## Implications for our implementation

The replicable design is an aggressive but funded opening, compact installations,
sustained eleven-hand-scale service, prompt planting, finite-horizon crop turnover,
visible-demand adaptation and storage-aware sales. The 178K portfolio should not
be hardcoded into a bakery/pet-cafe economy. Our new candidate follows those
principles with its own reactive rules; it is not a reconstruction of Majkel's
private source or a playback of the supplied future actions.

[Cycle 19 implementation and CO notes](CYCLE_19_OPTIMIZATION.md) describe the
actual code, its deliberately bounded forecasts, differences from Majkel, and
remaining validation limits. No trained model, API key or paid compute is needed.
