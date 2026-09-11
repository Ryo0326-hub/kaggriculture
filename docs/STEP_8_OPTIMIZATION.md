# Step 8: conditional expansion and spatial production economics

The entry point is `main.expansion_turn`. The single-file agent retains the
tested opening and installation routine. Starting on Day 3, it considers batches
of crops on owned land and batches that also purchase the next quadrant. The
maximum is three owned quadrants (75 tiles). This is a search bound, not
a claim that the fourth quadrant is always unprofitable.

## Why this change follows both server games

The [Step 7 server analysis](STEP_7_SERVER_ANALYSIS.md) records a 33,122-coin loss
to MugaBros and a 42,970-coin win over Jaikrishna@007. One opponent made productive
use of extra land; the other spent more and lost inventory. We therefore evaluate
the whole additional production schedule, not a fixed expansion day or cash
threshold. The observations do not reveal either opponent's private source code.

## CO250: a fixed cost and integer activity selection

For land decision `y` and production activities `x_j`, the conceptual model is:

```text
maximize incremental cash received before termination
         - land_cost * y - seeds/animals - feed/fertilizer - extra wages
subject to integer activity counts and binary land decisions,
           activity sites being owned or unlocked by y,
           dated cash and input inventory remaining nonnegative,
           sufficient worker service, travel, and delivery capacity.
```

Land is a fixed cost: buying an extra quadrant to plant one crop can be poor value
while funding it with a productive batch can be worthwhile. The policy enumerates
one animal or 1/4/8/12 crops, with a no-investment alternative. It compares the
next quadrant only when at most six currently owned crop sites are free and the
proposed batch actually needs more space. It pays land and seed costs before
projected receipts and credits no terminal land resale value.

The policy first ranks feasible activity families by marginal value per asset,
then chooses the greatest positive total contribution within that family. This
prevents a large crop count from automatically displacing a much more valuable
individual animal solely because unlike batch sizes were compared. It remains a
heuristic: a global integer optimizer could choose mixed batches that this menu
does not contain. It does not solve an LP or obtain LP dual prices.

For every alternative, `production_projection` reprices the visible portfolio
against observed town demand and rival production. Own supply changes the value
of existing output. Inputs are consumed or sold once, with fertilizer charged its
sale opportunity cost or dated purchase cost. The inherited 80% receipt credit
and 150-coin minimum cash are conservative heuristic allowances, not calibrated
probabilities or a guarantee of future liquidity.

## One source-matched decision

In the [saved expansion example](examples/step-8-expansion.json), on Day 11 the
agent buys the next quadrant and twelve strawberry seeds:

| Forecast quantity | Coins |
| --- | ---: |
| Land purchase | 1,000 |
| Twelve seeds | 1,200 |
| Total paid now | 2,200 |
| Estimated additional terminal contribution | 10,811.60 |
| Minimum projected cash across the whole portfolio | 2,187 |

The positions are the twelve nearest free crop sites in the newly available
region. The dated forecast includes fertilizer, input purchases, wages, and
market impact. These are conditional forecasts, not realized incremental profit.
The recorded action and source hash are checked before the explanation is saved.

## Land capacity has a location

The ten nearby animal installation sites remain reserved. Other cells on owned
land can grow crops. Pending seeds are restricted to the nearest free plots in
the same order used by the investment model. Without this link, a forecast could
price a short trip while the dispatcher planted an expensive distant corner.

`farm_tours` forms a bounded route menu by cheapest insertion. It accounts for
the worst shed-access starting position, movement between sites, per-site
service, and return to the shed. It reserves three operations for feed and
fertilizer/animal pickup and deposit, plus three turns of daily headroom.
`farm_service` varies the allowance by crop age and animal production date.
Infeasible routes or portfolios requiring more than twelve forecast workers are
rejected rather than silently clipping their cost.

This is a capacitated routing heuristic related to graph optimization. It is not
minimum-cost flow: optional visits, multiple service actions, time limits, and
prerequisites add constraints beyond ordinary flow conservation. The insertion
algorithm does not prove globally minimal travel or workforce size.

## Execution and resource reservations

The existing exact bounded livestock route-cover solver continues to assign
animal service even when many workers have already been hired. The old station
fallback used a separate worker per animal whenever a large crew was present;
on a larger mixed farm this consumed valuable early crop capacity. Installation
continues to use its protected station routine and preloaded first feed.

Workers finish their animal commitments before taking discretionary crop work.
Crop tasks are selected among available workers with shared tile and inventory
reservations. Small harvest batches can share a return trip, and workers can
load up to three fertilizer units for nearby applications. The dispatcher retains
storage-space checks, newborn watering, and terminal delivery checks. It can hire
up to thirteen total workers for operational repair; their actual cost is charged
by the game. Forecast and execution crews are related estimates, not identical
fixed tours.

The whole-farm insertion tours are a capacity and wage estimate; the actual
dispatcher uses the tested livestock cover and replans crop tasks. This is not
a proof that every forecast schedule will execute exactly. Full-season tests and
fresh opponent comparisons remain necessary to detect missed work.

The discrepancy is material in the saved example: the Day 11 forecast assigns
ten total workers to the following day, while execution hires twelve hands plus
the farmer, costing 376 coins for that day. The full remaining schedule also
changes with later investments. Consequently, the 476-coin forecast of remaining
wages is not an estimate of the realized cost of every later policy decision.
Spatial tours can underprice the dispatcher's staffing, and the Fibonacci cost
curve magnifies the gap. Matching forecast staffing to execution is a concrete
follow-up; positive projected value alone is not sufficient promotion evidence.

Ripe strawberries at the end of their final production window now receive a
harvest deadline instead of spending time watering a crop with no later output.
This is a deadline correction; broader selective maintenance remains Step 10.

## Evidence and scope

`opponents/expanding_mixed.py` is independently implemented using fixed work
zones, a four-animal opening, and subsequent crop expansion. A cow-heavy variant
changes its market exposure. These are reactive strategy-family controls, not
copies of leaderboard bots. Their limitations and measured outcomes belong in
the results report; adding an independent source does not by itself make the
benchmark strong.

`scripts/make_expansion_control.py --max-land 1` freezes a source-matched
ablation that retains the other Step 8 changes while forbidding land purchases.
This distinguishes expansion from the benefits of revised dispatch and batches.
The previous release is preserved byte-for-byte in `baselines/step_7.py`.

Development variants were rejected for operational failures even when they won
every game. No claim about medal probability follows from the internal pool.
See `STEP_8_RESULTS.md` for the final frozen protocol, actual counts, runtime,
release status, and a source-matched decision example.
