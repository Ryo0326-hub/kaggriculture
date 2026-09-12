# Cycle 15 — growth stalls before the 150,000-coin target

The agent underproduces. Fixing the six audited contracts made the policy more
consistent, but preserved an overly restrictive production and labor model.
The source-matched server evidence now exposes that limitation. More code and
passing isolated correctness tests did not establish a competitive strategy.

[Recorded evidence and admission diagnostics](benchmarks/cycle-15-growth-gap.json)
includes both supplied replays, source/log hashes and the illustrative target
budget. Analysis used passive recorded states, 1,438 independent decisions on
those recorded observations, and bounded investment-accounting probes. No
engine imports, game advances, local matches, counterfactual episodes or training.

## Results and identity

| Episode | Opponent | Our final coins | Opponent final coins | Gap |
| --- | --- | ---: | ---: | ---: |
| 107999948 | JoshJML | 81,939 | 123,182 | -41,243 |
| 108000970 | Dhanyashree1028 | 86,193 | 98,981 | -12,788 |

All 719 Unicorns decisions in each game match the frozen Cycle 15 source
`ce4444126f5ef7e0ee01a22f395ae87ee442ec2f329c4feb6aedf0687af45f1a`.
Both games finish DONE. Agent stderr is empty throughout; the maximum logged
callback durations are 0.218576 and 0.280298 seconds, including startup.
Own animals never disappear, no own crop-to-weed transition is observed, and
own final shed, carries and seeds are empty.

The screenshots show approximately comparable pre-update ratings: JoshJML
678 versus our 684; Dhanyashree1028 622 versus our 573. Their farming was
stronger in these games, but the displayed ratings do not support attributing
the losses to being matched against the top of the ladder. These are historical
screenshot ratings, not a live leaderboard lookup.

## Growth and labor evidence

| Metric | Us vs JoshJML | JoshJML | Us vs Dhanyashree1028 | Dhanyashree1028 |
| --- | ---: | ---: | ---: | ---: |
| Peak productive tiles | 29 | 50 | 29 | 71 |
| Final owned quadrants | 2 | 2 | 2 | 3 |
| Confirmed milk harvested during daytime | 72 | 201 | 72 | 79 |
| Confirmed wool harvested during daytime | 68 | 158 | 98 | 181 |
| Confirmed strawberries harvested during daytime | 72 | 190 | 120 | 144 |
| Confirmed wages | 3,800 | 6,670 | 3,363 | 6,215 |
| PASS / recorded unit commands | 43.8% | 18.1% | 40.6% | 0.2% |

Harvest counts here are **lower bounds** confirmed by within-day carry changes;
night-boundary harvests are excluded. Market request totals in the JSON are
separately labeled as requests, not independently reconstructed fills. This
report does not claim a complete transaction-by-transaction gross-revenue audit.

Our herd reaches five animals in both games and never grows further. Expansion
does execute, at steps 162 and 217, so the old failure to request land is no
longer the whole explanation. JoshJML beats us on the same two quadrants by
using much more of the available area. Buying land without staffing and filling
it would not close the gap.

PASS is diagnostic, not an objective: some waiting is useful when crops have
no due work. Dhanyashree1028 also loses six animals and has many crop-to-weed
transitions, including exhausted crops; nearly zero PASS is not proof of good
execution. The issue is rejecting profitable production while a large fraction
of the workforce's observed day is unused.

## Why the custom model rejects growth

### 1. Installation and maintenance bounds are too restrictive

`repaired_workforce` assumes two daily service actions for every living crop,
plus route travel and pickup/deposit allowances. While an animal is being
installed, it temporarily reserves one worker for **every** animal, then adds
separate crop-route crews. It rejects a purchase if this model exceeds twelve
workers on any modeled day, even if installation could be staged or another
feasible service allocation exists.

At step 211 against JoshJML, adding one cow produces a fourteen-worker next-day
estimate. At step 241 it produces thirteen. Both purchases are rejected.
Against Dhanyashree1028 at step 241, one extra sheep has **+2,468.5 coins of
estimated value after the existing discounts and wages**, but the installation
capacity flag rejects it. The next-day estimate fits twelve; the modeled
immediate installation phase does not. These are bounded probes on the real
state, not executed alternate investments or proven profitable continuations.

The prior repair aligned forecast and hiring arithmetic, but aligned both to
an overly expensive service model. Consistency is necessary, not sufficient.

The custom geometry also provides at most twelve animal sites. The supplied
near-150K reference reaches thirteen cows and four sheep simultaneously. That
particular production mix cannot fit our existing geometry even if its earlier
five-animal stall is resolved.

### 2. The downside demand scenario contradicts a known demand floor

`throughput_value` still uses `(1.0 demand, 1.0 rival supply)` and
`(0.5 demand, 1.5 rival supply)`, then retains 75% of the worse marginal receipts.
Unlocked shops persist. Halving already-visible shop consumption is not an
uncertain future-shop scenario consistent with the game's rules.

For example, a cow at step 241 against JoshJML has marginal scenario receipts
of **3,680 versus -167**, before its purchase and additional wages. The second
scenario and labor cost turn it into a strong rejection. This does not prove
the cow would earn 3,680 in an actual continuation; it identifies what the
model is using to reject it.

A custom rebuild should retain all known recurring town demand in every
scenario, vary future additions and rival supply, and distinguish forecast
uncertainty from physical infeasibility. A discount cannot repair an impossible
demand trajectory.

### 3. Early cash is being accumulated before productive capacity is ready

At the start of UI Day 16 we hold 30,547 and 24,693 coins. The opponents hold
10,321 and 700, respectively, with larger producing farms. Banked cash looks
like a lead while earlier investments are still maturing.

Our Day-16 herd is still five animals. In the supplied 147,606-coin Majkel game,
UI Day 11 already has twelve cows, three sheep and thirty strawberry plots;
UI Day 16 has thirteen cows, four sheep and forty strawberries. Its Day-16 cash
is only 20,070. Physical capacity, installation dates and future sale dates
explain the later receipts better than current cash alone.

## Work backward from 150,000 banked coins

This is an **illustrative milk/strawberry-rich economy budget**, not a prediction
for either supplied game. Average prices are explicit assumptions; they are
not immutable base prices or averages reconstructed from these losses.

| Product | Target units sold | Assumed average realized price | Gross receipts |
| --- | ---: | ---: | ---: |
| Milk | 330 | 190 | 62,700 |
| Strawberries | 300 | 220 | 66,000 |
| Wool | 120 | 150 | 18,000 |
| Melons | 72 | 150 | 10,800 |
| Wheat | 350 | 40 | 14,000 |
| Fertilizer | 200 | 50 | 10,000 |
| **Total** | | | **181,500** |

Budget 3,000 for two land purchases, 7,200 for livestock, 7,300 for seeds,
5,000 for labor and 12,000 for feed/additional inputs: **34,500 total costs**.
Then `3,000 starting cash + 181,500 sales - 34,500 costs = 150,000 final cash`.
Wheat here is gross sales; the input budget must include bought feed and any
buy/resell quantities. Gross receipts alone are not the objective.

The volumes are grounded in the supplied Majkel episode 107964504: it confirms
at least 343 milk and 299 strawberries harvested during daytime and finishes
at 147,606 coins. Its market requests include 341 milk, 302 strawberries,
118 wool, 72 melons, 358 wheat and 200 fertilizer sold. Those request totals
are not claimed as a separate exact fill reconciliation.

If milk and strawberry average prices are each fifty coins lower, the target
volumes earn **31,500 less**. Existing reference games also include Gekkotron
winning with 66,698 and Majkel winning with 89,087. Thus 150K is a useful rich-
economy production target, not a universal floor or a substitute for win rate.

### Physical milestones for a custom rebuild

These are provisional planning targets informed by observed successful farms,
not hard-coded orders or assertions that every market supports this mix.

1. **UI Days 1–6:** install and service the initial herd, harvest early wheat,
   and fund the first melon cohort. Reserve actual near-term feed and wages.
2. **Around UI Day 7:** open the second quadrant when a financed installation
   and production schedule uses it. Expand shared livestock service capacity.
3. **Around UI Days 10–11:** aim for a third quadrant, roughly 12–17 animals in
   demand-supported types, and 25–35 strawberry plots in milk/berry economies.
   Installation and daily service must fit before making these commitments.
4. **UI Days 12–20:** maintain roughly 60–75 productive plots, harvest and
   replant short-cycle wheat, and keep high-value recurring production supplied
   with feed, care and fertilizer. Target approximately twelve total workers
   through coordinated routes, not one permanent worker per animal.
5. **UI Days 21–30:** accept only projects with time to produce and deposit;
   sell physical output, maintain profitable continuing assets, and liquidate
   by the final action. Assess cash plus scheduled net receipts, not cash alone.

The CO connection is a time-expanded resource allocation problem: installation,
watering, harvest, travel and sale jobs consume dated worker actions and cash.
A full-day aggregate or a conservative route count is not a proof that no
feasible schedule exists. Growth requires a constructive schedule or bounded
service reservation, with opportunity costs applied to the actual bottleneck.

## Next decision: establish the public schedule baseline

The previously requested public V36 source was packaged as Cycle 14, but the
submissions page checked earlier showed custom Cycles 15 and 13 as the active
pair. These two new files also match custom Cycle 15 exactly. We have no supplied
server evidence of running our unchanged public V36 artifact.

The recommended next server candidate is therefore **the complete public V36
source unchanged**, packaged explicitly as [Cycle 16](CYCLE_16_RESULTS.md).
Its schedule family already appears in the supplied Gekkotron games and reaches
much higher physical utilization. This is attributed third-party code, not a
new custom scheduler or a promised 150K agent.

Keep Cycle 15 and all previous artifacts intact. Once the public candidate's
actual server games arrive, compare area utilization, installations, product
output, wages and realized prices before modifying its production schedule.
If rebuilding custom logic instead, the priorities are executable shared
service/installation scheduling, expanded herd geometry and valid demand
scenarios; another cosmetic sale-order tweak will not solve this scale gap.
