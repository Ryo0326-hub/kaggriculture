# Cycle 15 loss to JulianHahn28 — episode 108009995

Reviewed September 11, 2026. Unicorns is seat 1. Final banked coins are
**69,799 versus 75,016**, a **5,217-coin loss**. These are final cash balances,
not gross revenue. Both players finish `DONE`.

All 719 own decisions reproduce frozen Cycle 15 behavior on the recorded
observations. Its source SHA-256 is
`ce4444126f5ef7e0ee01a22f395ae87ee442ec2f329c4feb6aedf0687af45f1a`.
This is behavioral identification; the uploaded Python file is not attached.
It is not performance evidence for the newer Cycle 17 candidate.

The own runtime log has 719 entries, no nonempty stderr, and a largest recorded
duration of 0.230659 seconds. The replay is interpretable: it supplies public
farms and market state, each seat's inventories, actions and terminal results.
Actions in `steps[k+1]` correspond to observations in `steps[k]`. Seat 1 omits
the shared `step` field; the record index supplies it for source checks.

## Why we lost

The strongest explanation is insufficient recurring production after a good
early melon harvest. This is an economic interpretation of the recorded
trajectory, not a counterfactual proof of how a different purchase would perform.

| Recorded metric | Unicorns | JulianHahn28 |
|---|---:|---:|
| Final banked coins | 69,799 | 75,016 |
| Peak herd | 5 | 16 |
| Herd composition | 2 cows, 2 sheep, 1 goose | 3 cows, 13 sheep |
| Peak productive tiles | 28 | 44 |
| Final owned quadrants | 2 | 4 |
| Confirmed daytime wool units | 68 | 273 |
| Confirmed daytime milk units | 72 | 108 |
| Confirmed daytime melon units | 138 | 67 |
| Accepted daily hires, summed across season | 268 | 273 |
| Confirmed wages | 3,224 | 4,072 |
| PASS share of recorded unit commands | 42.3% | 18.3% |

Harvest counts above are **lower bounds** from within-day carry increases.
Harvests crossing a night reset are excluded. There are no unresolved
night-boundary hire requests, so the wage comparison does not have that gap.
PASS includes deliberate waiting; its percentage alone is not lost profit.

Julian served a much larger herd for only 848 more coins in wages. The total
recorded unit-command budgets were nearly equal: 6,796 for us and 6,772 for
Julian. Lower wages did not compensate for our smaller recurring output.

We led by as much as **22,881 coins**, at the recorded state on UI Day 14,
Turn 19. At the start of Day 21 we had 44,667 against 28,413. From there to
termination, our cash increased by 25,132 while Julian's increased by 46,603.
That 21,471 difference erased our 16,254 lead. After an earlier temporary
overtake on Day 27, Julian moved ahead permanently on Day 29, Turn 2.

## Julian's strategy fits this particular town

The first yarn store appeared on UI Day 7. Julian opened with three sheep,
bought six more on Day 8 and four more on Day 13. Our sheep count remained two.
A second yarn store appeared on Day 22. Wool's opening-of-day quotes at the
three-day snapshots from Day 10 through Day 28 stayed between 209 and 233.
Milk, in contrast, was quoted at 91 on Days 13 and 16.

This differs from the [Sergey loss](CYCLE_17_OPTIMIZATION.md), where much greater
milk production served a different town. The transferable idea is to expand
the product with durable demand and feasible service costs. A fixed instruction
to buy cows, or to copy thirteen sheep in every game, misses that distinction.

Julian also collected much more fertilizer: 359 collection commands versus
140, with 356 versus 119 units requested for sale. Those are command/order
counts, not a separately reconciled proceeds account. Selling fertilizer
provided another recurring income stream, but it became less valuable as
the shared quote fell from 100 initially to 6 at the end. Forecasts must price
that supply pressure rather than give every future fertilizer unit today's price.

Julian used selective `PLACE` deposits for fertilizer, wool and milk, alongside
animal placement. Its lack of `DROP` commands does **not** mean goods were left
undelivered. Selective deposits preserve other carried goods, such as feed.
The replay alone does not establish that this deposit method outperformed ours.

## What our bot did well

- All **23 melons produced six harvested units each**, at crop age ten: 138
  units in total. Our melon sale requests finished on UI Day 20. Julian's
  requests came on Days 21 and 23, at pre-order quotes of 113 and 73. Our
  earliest quote was 272, and the last was 125. These quotes are not realized
  batch-average prices: each batch can move the market.
- All four carrots yielded four units each, consistent with the intended
  fertilizer benefit. The six strawberry plants delivered 46 confirmed units.
  Fertilizer scheduling is producing useful output and should be preserved
  where its extra yield repays its inputs and labor.
- No own animal disappeared and no own crop changed into a weed. The final
  shed, carried inventories and seed inventory were empty. No unharvested
  crops remained. This loss was not caused by a crash or a terminal stockpile.
- We bought the second quadrant on Day 7, earlier than Julian's first land
  purchase on Day 9. The issue is subsequent investment and utilization,
  rather than an inability to buy land at all.

Julian was not flawless: 18 wheat and nine carrot plants became weeds, with
positive yield still recorded immediately before the transition. It ended
with eleven unused carrot seeds, eight wheat seeds and three fertilizer units
across shed and carries. Four quadrants did not translate into full productive
occupancy; peak productive tiles were 44. These observations do not prove that
avoiding every loss, or skipping its fourth quadrant, would improve cash after
charging the alternative labor and land value.

## CO and economic interpretation

For CO250, think of crop/livestock batches as integer decisions with dated
cash, feed, tile and worker constraints. Their contribution is expected sale
proceeds less inputs, setup, land and incremental wages. The objective is
terminal banked cash, so an early cash lead is not a measure of the value of
the whole remaining production system.

Worker capacity has a marginal value, analogous to an LP shadow price. Here,
large amounts of paid waiting coexist with a small herd and cash accumulating
after the melon harvest. That supports investigating conservative investment
admission and how work is shared. It does not prove that every idle worker can
service another sheep: movement, feed availability and daily deadlines are
discrete constraints. The integer hiring schedule also means one extra batch
may need no extra hire, while the next batch crosses an expensive wage step.

The shared market creates a game-theoretic interaction. Expanding wool both
earns revenue and changes the price available to the rival. This replay shows
that substantial combined melon supply met much weaker demand later in the
season; our earlier realization was valuable. Future production must use
visible rival supply and current shop demand without knowing future shop draws.

## Decision for the next review

**No agent change or new submission from this review.** Cycle 15 and the
[Cycle 17 candidate](CYCLE_17_RESULTS.md) remain unchanged. Cycle 17 already
targets shared service costs and growth admission; this older replay reinforces
the motivation, but cannot validate the repair.

Compare the upcoming wins on the same dimensions: source version, shop sequence,
recurring herd/output, investment dates, cash before and after the melon harvest,
wages, quoted sale timing, losses and terminal delivery. Check whether a win
comes from a strong repeatable income stream, better early sales, or an opponent
that underproduces. Do not select a new policy based only on a loss or a win.

[Machine-readable evidence](benchmarks/server-review-108009995.json).
Raw files remain in Downloads and are identified by hashes in that report.
The base passive counters can be reproduced with
`scripts.study_recorded_games.study(path, name)` for each player. Supplemental
tables are direct filters of recorded observations/actions, not engine output.
No local match, state advance, training, paid compute or model API was used.
