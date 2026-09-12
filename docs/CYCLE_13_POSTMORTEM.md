# Cycle 13 — growth blocked before investment valuation

**Follow-up:** this initial land diagnosis was not exhaustive. The [broader
logic audit](CYCLE_13_LOGIC_AUDIT.md) documents two additional dispatch defects,
two forecast inconsistencies and a profit-selection weakness, distinguishing
recorded evidence from constructed cases. No legacy agent fixes are claimed.

September 11, 2026. Episode **107984963**, Unicorns versus onepunch999. Source
`542547dbe7cd63856b2a6f037e2014790c1410316c3b3872f67ea85c2b628947` reproduces **all
719 recorded own decisions** when given the recorded observations. No game
engine was imported and no state was advanced. The diagnostic wrapper recorded
investment inputs/results and returned the original decisions unchanged.

The user screenshot shows a successful Cycle 13 submission with a displayed
rating of 435.7. That is a screenshot observation, not a newly fetched rating.
The replay ends at **66,319 versus 106,333 coins**, a loss of **40,014**. The
image showing 65,066 versus 103,666 is an earlier frame on Day 30. These amounts
are bank balances, not gross sales revenue.

[Passive replay accounting](benchmarks/cycle-13-server-107984963.json) ·
[Source-matched investment diagnosis](benchmarks/cycle-13-failure-diagnosis.json).

## What failed

| Recorded measure | Unicorns / Cycle 13 | onepunch999 |
| --- | ---: | ---: |
| Final bank balance | 66,319 | 106,333 |
| Final owned quadrants | 1 | 3 |
| Land purchases | 0 | 2, at decision steps 169 and 241 |
| Peak simultaneously productive tiles | 23 | 68 |
| Confirmed total wages | 734 | 7,641 |
| Cows purchased and installed | 2 | 10 |
| Confirmed strawberry plantings | 2 | 38 |
| Confirmed daytime milk harvest units | 72 | 242 |
| Confirmed daytime strawberry harvest units | 16 | 129 |

Harvest totals are verified within-day inventory increases and therefore lower
bounds. Simultaneous productive tiles count crops and animals, not weeds or
empty structures. The broad duplicate-coordinate metric in the passive report
includes harmless shared moves/PASS and is not a count of execution failures.

Cycle 13 did not crash. Both players finish `DONE`; all 719 supplied own log
records have empty stderr. The largest recorded callback duration is 0.180613
seconds, including startup. Own shed, carried products and seeds are empty at
the end. Our animals do not disappear in the supplied observations. New geese,
tomatoes and carrots were actually used, but on too small a productive base.

The opponent spent 6,907 more on wages and still finished 40,014 ahead. Saving
labor expense did not compensate for foregone output. On UI Day 12 our bank
already held 21,693 coins. The problem was not a lack of expansion capital.

## Exact reason no land was purchased

The frozen code's `throughput_investment` was called 718 times. It exits if the
hour is after six, seeds or animals are awaiting installation, orders are full,
or the final day has arrived. Only **39 calls** passed these initial rules.
Pending seeds appear on 381 calls and the late-hour condition on 509; these
counts overlap and must not be added as disjoint causes.

At **38 of the 39** eligible calls, this rule removed land from consideration:

```python
if extra_land and (owned >= max_land or len(vacant(fields)) > 4):
    continue
```

It requires at most four vacant existing crop spaces before expansion can even
be valued. Harvesting frees spaces, small new purchases refill them slowly,
and pending seeds then block further purchases. This combination repeatedly
closed the investment window. The headline three-quadrant limit did not make
three quadrants reachable under the actual admission rules.

The only call that passed the vacancy test was **step 360, UI Day 16**, with
28,107 coins and two vacant crop spaces. Its existing order list already had
nine entries: two sales, a wheat purchase, and six hires. Every land project
required two more entries—`BUY_LAND` and `BUY_SEED`—but the cap is ten. All ten
generated land/crop bundles were consequently rejected before valuation.

**Not a single land bundle reached the profitability calculation in this game.**
An empty recorded land-alternatives list means the candidates were filtered
out, not that their evaluated profits were negative. The source therefore
cannot support the explanation that the opponent made land unprofitable.

The livestock layout compounds this: only five animal sites are available
before the northeast quadrant is owned. Once two cows, two sheep and one goose
occupied those sites, land admission also blocked further herd growth.

## The optimization lesson and our implementation mistake

The selection model maximizes value over its generated feasible set. If the
admission rules remove every land investment, better price forecasts cannot
recover the missing option. A heuristic vacancy test is not a real physical
constraint, while the market-order cap is real and needs scheduling across
turns. The controller failed to coordinate these two restrictions.

A related economic issue is interpreting unspent cash and cheap labor as
success during the growth phase. The opponent invested that cash into later
output. Final banked profit is the objective; conserving intermediate cash is
useful only to the extent that it supports that objective.

This was an implementation/design failure on our side. The earlier tests
checked individual features, accounting and interface behavior; they did not
establish that the complete admission rules could produce the intended land
growth. Adding more features was not evidence of stronger play. The supplied
server game now provides the missing integrated evidence. A targeted fix to
Cycle 13 is possible, but has not been made or presented as a verified solution.

## Decision after this result

Following Ryo's request, **Cycle 14 uses the complete public V36 agent unchanged**
as a separate candidate. No Cycle 13 dispatcher, investment filters or sale
rules are grafted onto it. Its source and attribution are preserved, and the
existing agents remain available for comparison.

This supersedes the earlier plan to make sale ordering the next narrow change:
production admission failed, so trading alone would address the wrong primary
problem. First obtain a server result for the unchanged public baseline. Then
choose improvements from its actual failures or missed opportunities.

[Cycle 14 artifact and upload command](CYCLE_14_RESULTS.md). No local matches,
counterfactual games, sweeps, cloud compute or training were run for this work.
