# Cycle 17 — shared service routes and funded production growth

Cycle 17 is a custom descendant of frozen Cycle 15. It replaces the separate
livestock/crop dispatch layers with one current-observation route planner, and
replaces their investment labor/demand estimates. It retains Cycle 15's price
curves, animal/crop production columns, fertilizer marginal-value functions,
and joint livestock/melon/wheat opening. The public V36 source is untouched.

This is an implemented end-to-end policy, not a proof of optimal play, a promise
of 150,000 coins, or an exhaustive claim that all useful strategies are covered.
The next evidence is its own Kaggle validation and competitive games.

## Evidence: the loss to Sergey Panasenko

Replay `108005959.json` contains 720 recorded states and 719 decision transitions.
Our seat is 0; Sergey Panasenko is seat 1. Each action at state k+1 was submitted
against the observation at k. The shared `step` field is omitted on seat 1, so
isolated checks supply the recorded state index there. Both seats' recorded
private inventories are available for post-game analysis; the live policy only
receives its own private inventory. Opponent source code and internal reasoning
cannot be recovered from a replay.

All 719 own decisions match frozen Cycle 15 exactly. Every own stderr entry is
empty, the largest logged callback including startup is 0.241104 seconds, and
both players finish DONE. This was an economic loss, not a runtime failure.

| Recorded metric | Cycle 15 | Sergey |
| --- | ---: | ---: |
| Final banked coins | 76,678 | 122,718 |
| Peak productive tiles | 30 | 75 |
| Final purchased quadrants | 2 | 3 |
| Daytime milk harvested | 72 | 318 |
| Daytime wool harvested | 68 | 174 |
| Daytime tomato harvest | 0 | 208 |
| Daytime strawberry harvest | 142 | 32 |
| Confirmed wages | 3,865 | 15,687 |
| Recorded worker commands | 6,947 | 7,002 |
| PASS share | 41.8% | 15.2% |
| Animal disappearances | 0 | 0 |

Harvest quantities are lower bounds from within-day carry changes, excluding
night-boundary harvests. The companion JSON labels sale requests separately;
they must not be described as independently reconciled fills. Wages reconcile
accepted daytime hires; no overnight hire requests are unresolved here.

Sergey's sequence was:

1. Establish an early melon and staple-crop farm with a small herd. At the start
   of UI Day 4: 15 melons, 6 wheat, one carrot, two sheep, and one cow.
2. Buy two quadrants together at decision 179, UI Day 8 turn 12. We bought one
   quadrant on that same decision. He requests 43 wheat seeds during Day 9;
   the observed Day 11 farm contains 43 wheat plots.
3. Reinvest into livestock and tomatoes as the early crops finish. By the
   start of UI Day 21 he has 19 cows, 10 sheep, nine geese, 26 tomatoes,
   seven strawberries and four melons. These 75 assets coexist in that state.
4. Monetize the herd late. Several smoothie shops, a pizza shop and an ice
   cream shop support milk consumption. The recorded milk quote rises from
   160 initially to 266 near the end despite both players' sales.

We lead 20,082 to 3,013 at the start of UI Day 13, but those bank balances omit
the value of his growing production assets. At the start of UI Day 25, the
balances are 60,132 to 62,246, and his lead then widens. He also spends much more
on late crews: the count of hired hands is similar across the season, but
concentrating them into larger daily crews incurs the convex Fibonacci costs.

He issues only 37 DROP commands versus our 114. This is consistent with using
the automatic night deposit and keeping workers on their routes; it is not
proof that every avoided return caused a profit increase. His ending carries
still contain 12 milk, 14 strawberries, 16 carrots, eight tomatoes and 64 wheat,
plus two wheat in the shed. We retain explicit final delivery instead of copying
that weakness. Neither a trained model nor an LLM can be inferred from these
actions; no training or model API is needed for this implementation.

[Machine-readable evidence](benchmarks/cycle-17-sergey-analysis.json).

## The CO model and the executable decisions

For route r let x_r indicate hiring/using a worker on that route. Each route
contains dated jobs on real tiles. A set-cover formulation would minimize
staffing cost subject to every required job being covered and every route's
action budget fitting the day. Because staffing cost depends on total hires,
the objective uses the cumulative Fibonacci bill, rather than a constant cost
per worker. This connects to CO250 integer programming. Routes themselves
connect to network routing and scheduling topics in later CO courses.

The implementation uses deterministic insertion and worker assignment heuristics,
not an integer solver or an optimality certificate. The same route constructor
supports admission, daily workforce estimation and actual dispatch. Its cost
includes tile operations, movement and distinct input pickup types. Only the
new animal incurs installation operations; installing one cow no longer creates
one station worker for every existing animal.

During ordinary days the engine automatically transfers carried inventory to
the shed at night. Routes can end in the field. Inventory pressure triggers
earlier deposits; on the final day, route costs explicitly include return and
deposit before the last market action. Thus the terminal constraint differs
from ordinary daily maintenance.

Actual jobs include installation, planting with first-day watering, feeding,
care, collection, fertilizer application, harvesting and clearance. Current
completion flags avoid repeating finished jobs. Shared reservations prevent
duplicate tile assignments, seed oversubscription and unavailable pickups.
Short urgent jobs can be served when a full route no longer fits. Optional
fertilizer cannot prevent last-turn survival maintenance. CARE follows the
engine's production-before-bonus-banking order and stops when no remaining
production can use its bonus.

Preferred animal locations grow with land ownership. Once those locations are
full, vacant crop plots can also house animals. Every existing asset remains
serviced even outside the preferred layout. Pending animals and seeds reserve
different sites. There is no twelve-animal geometry ceiling.

## Marginal investment and working capital

Each candidate is a funded crop/animal batch, optionally bundled with the next
quadrant. Candidate sizes include 1/2 animals on existing land, 2/4 with land,
1/4/8 crop plots on existing land, and 8/12 with land. All five crops and all
three livestock types are eligible. All four quadrants can be considered.

The marginal objective is:

`0.75 * change_in_receipts_known_demand + 0.25 * change_in_receipts_expected_shops`
`- purchase_and_land_cost - added_wages - early_setup_reserve`.

Both branches preserve all currently observed shop consumption. The first
assumes no additional shops and larger future rival supply; the second adds
expected consumption from uniformly drawn future shops and a smaller rival
supply multiplier. Neither reads future shops, the replay seed, opponent
private inventories or opponent future actions. These are explicit scenario
approximations, not calibrated probabilities or a game-theoretic equilibrium.

Both branches price our whole affected production stream with and without the
addition. This charges the effect of our extra supply on our existing sales,
not just the new units. Every candidate pays its full land price. Estimated
feed purchases and daily wages come before that date's projected receipts, and
the modeled bank balance must remain at least 150. Earlier installation reserves
extra feeding and any same-day hires. Uncertain same-turn sale proceeds are not
used to fund speculative purchases.

The runtime considers at most 17 total workers and charges the full wage curve;
17 is a bounded search limit, not a target staffing level. Unlike the former
12-worker cutoff, economically justified additional crews can be admitted.
The dispatcher asks for the estimated crew during the morning and retains any
already hired workers. Purchases are reconsidered every four turns through
hour 20 when the prior installation queue has cleared.

The opening remains the existing joint economic choice (two cows, two sheep,
eight melons and four wheat in the supplied starting state). Later choices
respond to the actual economy. Milk and strawberry volumes in the earlier
150K budget are targets in favorable markets, not fixed instructions.

## What the checks establish, and what they do not

The repaired policy passes bounded route, demand-floor, resource, installation,
care-timing and terminal-chain checks. For example, on the recorded Sergey-game
observation at decision 244, it admits two cows and prices setup and recurring
wages. This demonstrates a changed decision at the known growth bottleneck;
the associated value is a forecast, not money actually earned in a continuation.

Replanning can change worker routes as jobs finish. Forecasts approximate harvest
and sale dates, future supply and delivery detours; they do not certify a whole
season's realized schedule. Finite shed space, shop draws and opponent sales can
change outcomes. There are no local matches, counterfactual episodes, parameter
sweeps, cloud costs or training in this release. Its own server performance is
unmeasured until the user uploads it.

Next supplied games should show whether installations clear promptly, daily
output grows before the final week, animals and crops remain maintained, wages
are repaid, inventory does not overflow, and final delivery succeeds. Compare
wins and losses across markets; a short rating swing is not proof of improvement.
