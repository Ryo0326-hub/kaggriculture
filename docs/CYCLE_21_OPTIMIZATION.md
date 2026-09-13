# Cycle 21 — production calendars and deadline-aware service

Cycle 21 is a complete standalone descendant of the preserved Cycle 20 agent.
It implements the crop scheduling priority identified in the
[Baen review](SERVER_REVIEW_108335136.md) and
[Majkel/THIRD FARM CLUB comparison](MAJKEL_108290604_STUDY.md).
The opening investment targets, animal care, staffing, land expansion, supply
forecasts and market-sale rules remain inherited. Crop labor valuation changes
to reflect the new watering calendar, so later crop purchases can differ.

Source: `experiments/majkel_calendar.py`. Builder:
`scripts/make_calendar_agent.py`. [Release and upload](CYCLE_21_RESULTS.md).

## 1. Spend water actions when they matter

The previous agent requested daily watering for living crops. That spent turns
on safe nonproduction days while some distant crops missed essential service.
The new rule combines the observed drought counter with production dates:

- Always preserve necessary survival water. A skipped day is allowed only when
  the current counter permits it; a missed earlier visit overrides the calendar.
- Keep planting-day water. New plants start with a drought counter of one.
- For strawberries, water before production at ages 10, 12, 14 and 16, meaning
  the relevant preceding nights are ages 9, 11, 13 and 15. Safely skip intervening
  nights and alternate immature watering where possible.
- For tomatoes, retain water before their daily production events. Their calendar
  cannot use the same alternating mature-phase rule as strawberries.
- For wheat, carrots and melons, preserve watering that increases one-time yield,
  as well as survival water. Stop unproductive water after a repeater's final output.

Fertilizer's inherited marginal-value and coverage checks remain active. On a
survival deadline, WATER comes before optional fertilizer. Once the recorded
water flag is satisfied, fertilizer can still be applied before the production
boundary. Already-watered crops do not receive duplicate water commands.

This follows a useful component of THIRD FARM CLUB's losing policy without
copying its weak livestock care or replacing our entire production portfolio.

## 2. Route continuity must allow deadline intervention

Static angular sectors remain the normal ownership map. Cycle 21 adds a small
deadline assignment pass before the existing command/resource ledger:

1. Identify necessary water/feed, production-night input work, harvests and the
   next observed crop-decay boundary. Record a deadline and a value proxy.
2. Estimate each sector's remaining travel and service work. This is a workload
   indicator, not an exact optimal tour or a proof that every job fits.
3. For deadline work, compute worker-specific feasibility using current position,
   carried inputs, available shed stock, pickup actions and service actions.
4. Intervene when even the cheapest feasible visit has at most four spare turns,
   or when the sector workload exceeds the available time minus a small buffer.
5. Retain feasible existing deadline commitments to avoid route reversals. Permit
   preemption when a more urgent deadline cannot absorb the current job's delay.
6. Greedily assign remaining work by deadline, survival/production priority and
   output-value proxy, then choose a cheap feasible worker. Reserve each target
   once; workers outside the original sector can help.

Useful carried animals keep installation precedence. The existing ledger still
processes units in engine order, so actual shared input availability determines
the command. A hypothetical match does not authorize unavailable wheat or fertilizer.
Final-day delivery retains its existing precedence; the new matching pass is
disabled on the final day.

The four-turn slack threshold is a conservative service buffer, not a four-turn
market-sale timer or a tuned performance optimum. This is greedy matching with
continuity, not an exact minimum-cost flow or integer-programming solver.

## 3. Do not rescue a crop after its output has decayed

For a ripe crop with an observed lifespan boundary, the agent computes the next
two-turn decay event. Unit actions happen before decay, so HARVEST on that event's
action is still timely. Spending the action on WATER instead is not equivalent.
The job therefore gets its own shorter deadline and an immediate harvest plan.

Ordinary survival visits also drop a fertilizer detour when it would consume the
remaining slack. During the audit, a further conflict was found: depositing
valuable carried goods at shed access could replace the pickup needed for a
last-feasible fertilizer-and-water sequence. Deposits now yield when a reserved
service visit has at most one spare action, including its actual pickup cost.
Normal sales, capacity protection and terminal deposits remain in place.

## 4. Charge crops for the new calendar

The inherited crop score approximates:

`net = forecast output value − seed cost − fertilizer opportunity cost − 4 × work`.

It then scales the result by crop lifetime and work. Previously, the work term
charged daily watering even on dates when the new policy would safely skip it.
`crop_work` now counts the planned calendar visits, harvests, setup terms and
fertilizer allowance. A full strawberry lifetime has nine planned water visits;
the resulting work term is 17 rather than the old 25. Tomato and one-time crop
calendars are counted separately.

This changes crop rankings consistently with the execution change. It does not
increase seed queue limits, force extra strawberry purchases, copy an opponent's
asset totals or remove feed/cash reserves. Real missed visits can make work exceed
the calendar estimate; saved actions and competitive profit are not measured yet.

**CO250 connection:** purchases are integer decisions, while cash, land, input
inventory and worker time are scarce resources. A crop's marginal value depends
on when its output arrives and whether its service fits. The four-coin work charge
is a heuristic shadow price, not an optimal LP dual variable. Survival and decay
deadlines introduce scheduling constraints that a seed-ROI ranking alone misses.

**Economics/game theory:** Cycle 20's dated output forecast for both visible farms
is retained. It accounts for feed use and does not cushion a predicted price
collapse with today's quote. Cycle 21 does not assume future shops, inspect rival
private inventories, introduce an LLM or learn a secret opponent model. Larger
speculative inventory holding and revised rival-service forecasts are separate
research hypotheses; they are not silently bundled into this release.

## 5. Complete observation-to-action flow

The single file exposes `agent(observation, configuration)` and returns farmer,
hand and market commands. The flow is:

`observation → calendar jobs → deadline matching / stable routes → shared resource ledger → market and investment decisions → action`.

| Capability | Cycle 21 status |
|---|---|
| Plant, water, fertilize, harvest and clear plots | Integrated; calendar/deadline changes included |
| Animal installation, feed, care, fertilizer collection and product harvest | Integrated; inherited service and accounting |
| Daily hiring and land purchases | Integrated; existing targets and affordability checks |
| Demand/supply-dependent investment and selling | Integrated; Cycle 20 forecasts plus revised crop work cost |
| Storage protection and terminal delivery/sales | Integrated; shared checks retained |
| Standalone packaging and deterministic rebuild | Implemented; frozen parent hash and overwrite refusal |
| Kaggle validation and competitive outcome | Pending user upload/server play |

“Complete” here means the policy and submission path are implemented. It does
not mean that all future optimization opportunities have been exhausted or that
this revision has already demonstrated stronger server results.

## 6. Evidence and limits

All **176 bounded tests pass**, including shared Cycle 19–21 checks and the new
watering, fertilizer, decay, matching, continuity and deposit-deadline regressions.
Two original Baen observations are committed as small fixtures. On Day 14 Turn 19,
Cycle 21 targets both endangered melons with nearby workers. On Day 17 Turn 18,
it targets all three endangered northern strawberries.

[Decision evidence](benchmarks/cycle-21-deadline-decisions.json) compares independent
callbacks from the preserved candidates. These are decisions on the old recorded
positions, not a continued Cycle 21 season; actual survival or additional coins
cannot be inferred from target assignments alone. At the original final watering
turn, some distant jobs are already physically unreachable, which is why earlier
assignment matters.

The final source also passes **5,752 independent recorded-observation checks**
across both seats of four supplied games. Input immutability, JSON output, action
preconditions, exclusive tile operations, input use and storage arithmetic are
checked without advancing any environment. Maximum observed callback time is
0.028855 seconds locally; this is not a Kaggle runtime guarantee.

On the next server logs, inspect crop deaths, production-date water/fertilizer,
actual crop purchases, preserved animal bonuses, route reversals and final cash.
Keep both wins and losses: the matching/work estimates are approximate, and more
deadline preemption could change travel or optional-care coverage. No local
simulation, training, paid compute or automated Kaggle submission was used.
