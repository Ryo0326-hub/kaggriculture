# Cycle 19 — compact service and prompt capital deployment

This is a new reactive Unicorns candidate, informed by Majkel1337's supplied
wins [108300532](MAJKEL_108300532_STUDY.md) and
[108305451](MAJKEL_108305451_STUDY.md). It does not contain those players' source,
replay action schedules, seeds, episode identifiers or future shops. The builder
extracts the hash-checked existing Cycle 3 market/mechanics helpers and combines
them with `experiments/majkel.py`. Cycle 15 and Cycle 18 remain unchanged.

## Why a new dispatcher

Cycle 18 repeatedly rebuilt route assignments and abandoned work. It also allowed
unplanted seeds to veto unrelated growth. The reviewed failures include 357–507
adjacent movement reversals, seeds waiting almost twelve days, and realized animal
output well below a full-care forecast. Additional investment features did not
repair those dependencies.

The new policy retains our known crop, animal, feed, fertilizer, warehouse and
terminal mechanics. It replaces the expensive route/forecast orchestration with
smaller, inspectable rules. This is a substantial challenger rather than a claim
that a narrow change alone explains any future score difference.

## Implemented decisions

### Layout, job completion and labor

- Reserve five compact livestock pads in NW, six in NE and six in SW. Existing
  off-layout assets are still serviced. From internal day 14, unused pads may
  receive crops. At most three quadrants are purchased by this policy.
- Split owned tiles into deterministic angular sectors weighted for livestock
  service. Completion flags cannot move sector boundaries. Workers finish
  current-site work and their committed target before choosing another job;
  idle workers can help beyond their sector. Every target is reserved once per
  decision, eliminating duplicate same-tile operations.
- Remember active targets only while callbacks are sequential within one day.
  Missing/reset memory falls back to deterministic sector ordering. This memory
  accelerates continuity; legality never depends on an unseen previous action
  having succeeded. Every operation is regenerated from the current flags and
  inventories. Episode/day discontinuities clear commitments.
- Feed/fertilizer pickups are batched for nearby work. Animal carriers select
  compatible installations. The shared shed ledger is processed in engine unit
  order, so a later worker's deposit cannot fund an earlier worker's pickup.
- Use observed staffing targets: four paid hands on UI Days 1–2; six on Days
  3–6; eight on Day 7; nine on Days 8–9; eleven on Days 10–28; ten on Days 29–30.
  Actual hires depend on cash and order slots and occur near dawn. The final
  audit makes feed an operating obligation before expensive hires, while keeping
  enough cash for the first four inexpensive hands when possible.
- Route admission charges movement, missing-input pickups and current service
  operations. A pending plant must have time for first watering. A pending animal
  must have time for its setup/feed/care bundle. If an established site's whole
  bundle cannot fit, the policy can salvage a feasible essential operation.

The staffing numbers and sector weights are heuristics derived from repeated
behavior, not solutions of a global routing optimization. Matching a headcount
does not by itself guarantee completion of every daily job.

### Opening and investment

The opening aims for two cows, three sheep, five initial feed units, ten wheat
seeds and twelve staggered melon seeds. Purchases precede physical availability:
no worker relies on goods being bought later in the same turn. Successful stock
and installations, rather than historical purchase requests, determine subsequent
orders. Affordability can delay or reduce a target.

The second quadrant is considered from UI Day 7, the third from Day 10, while
there are at least fifteen installed productive assets and enough capital for
land, running reserves and initial development. Neither purchase is automatic.

Subsequent crop queues are normally limited to four pending/newborn commitments,
with purchases of at most two seeds per decision. The special opening can queue
more. A seed that cannot reach first maturity is not planted. An uninstalled
animal that cannot produce before termination is not installed, and carrying it
does not prevent its worker from completing useful tasks. Seed backlog no longer
vetoes land or animal evaluation.

Later livestock is considered only with visible product-shop demand, a positive
estimated margin, central space and a seventeen-animal ceiling. Species also
have a demand-based capacity cap; for example, one bakery supports a four-goose
cap under this rule rather than unlimited goose purchases. This differs from
Majkel's occasional additional cows before milk shops appear. We deliberately
avoid treating its observed future demand as available information.

Crop alternatives include wheat, carrots, tomatoes and strawberries. Carrots and
tomatoes require visible corresponding demand. Both plain and fertilizer-assisted
production are valued: expensive optional fertilizer cannot make an otherwise
viable plain crop inadmissible. Repeated crops lose value when fewer harvests can
fit, and stale seeds cannot block a new feasible investment of another type.

### Crop and animal service

- Daily feeding and care use the actual animal production clock. Care is banked
  after production; only care that can affect a later production is requested.
  Feeding can stop after the last production possible before the terminal date.
- Water protects living crops and enables production bonuses. Repeaters still
  need watering between collections. Empty exhausted crops can be removed.
- Fertilizer is optional and its estimated additional crop value must exceed
  current fertilizer sale value plus an action allowance. Berry/tomato fertilizer
  can be applied after watering because their bonus resolves overnight. Wheat
  and carrot applications must precede beneficial watering. No fertilizer is
  purchased by this candidate; animal output supplies it.
- Wheat can be harvested at age three, especially after reaching five units;
  melons can be harvested at age ten after their watering-supported growth.
  Waiting for maximum crop yield is not the universal objective.

### Sales, working capital and storage

Sales use stock projected after the chosen unit commands. They precede purchases
and hiring in the order list. Expected proceeds are discounted and stressed for
rival sales for budgeting; the next callback still uses actual money and stock.
Partial fills do not create imaginary resources.

The default sells surplus promptly. A bounded holding rule can retain up to ten
units per product when cash is ample, total shed-plus-carried stock is below
70% of capacity, and the visible-demand one-day price estimate improves by over
5%. The last two days disable holding. It does not reproduce Majkel's multi-day
40-melon holding or claim those delays would help our different production path.

Sale ordering prioritizes exposure to rival price impact. The price formula,
quantity and a rival-supply stress estimate matter; nominal unit price alone is
insufficient. No rival hidden inventory or future action is read.

Feed carried on a worker can offset depot demand only for hungry animals in
that worker's sector or assigned task; arbitrary remote grain cannot cancel
another worker's pickup. Space is reserved for all carried stock before buys.
Selective PLACE deposits retain other inputs. The policy does not request an
oversized DROP into full storage. It also refuses new collection/harvest that
would make even total sellable-stock clearance insufficient for night capacity.

Ordinary overnight transfers allow outward routes to finish away from the shed.
On the terminal day, candidate work must include physical return and deposit.
A loaded worker begins returning before that becomes impossible; final deposits
can be sold in the same action. Unreachable terminal harvests and optional terminal
watering without a deliverable harvest are rejected.

## Economics and CO250 connections

The objective is final banked coins:

`3,000 + product sales − product purchases − seeds − animals − land − wages`.

- **Working-capital constraints:** a profitable asset is useless if installation
  or feed cannot be funded before its output arrives. Sales can fund later orders
  in the same action; they cannot fund earlier worker pickups.
- **Integer costs:** an extra quadrant is a fixed charge. Fibonacci hiring makes
  an extra worker discontinuously expensive: eleven hands cost 232/day and the
  twelfth alone costs 144. The candidate caps routine staffing below that jump.
- **Opportunity cost:** fertilizer can be sold, land can grow a different crop,
  and worker actions can service other assets. The crop/animal value functions
  explicitly subtract inputs and a four-coin work allowance. That allowance is
  a heuristic shadow price, not an exact LP dual solution.
- **Finite horizon:** planting/install dates determine achievable production
  events. First maturity and repeated harvest count must use execution time,
  not only purchase time. Crop payoffs are discounted if only one event remains.
- **Facility layout and routing:** recurring service earns compact central
  livestock space. Stable assignments prevent reoptimization from endlessly
  deferring the actual work.
- **Shared-market game:** both farms contribute supply. Quotes extrapolate only
  visible production and currently revealed demand, without invented future
  shops. They are approximate capacity/price estimates, not a Nash equilibrium,
  trained value function, or proof of optimal sales.

## Verification scope and limits

[Results and upload command](CYCLE_19_RESULTS.md) identify the final artifact.
Bounded tests cover resource accounting, exact timing boundaries, no duplicate
operations, seed conflicts, survival priorities, stale investment, task continuity
across authored observations, cold starts and final delivery. The recorded-state
checker invokes the candidate independently on existing observations and never
advances a game. It is **not** a counterfactual season or a performance benchmark.

The two supplied Majkel wins demonstrate repeatable strategies across different
towns; they do not identify its full algorithm. Only new Kaggle validation and
matches can establish whether this candidate's integrated behavior is reliable
and stronger than our preserved bots. No error-free or rating guarantee is made.
