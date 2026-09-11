# Episode 107928511 — clean execution, weaker production economics

Unicorns lost **73,860–122,954** to Ace Team, a 49,094-coin gap. All 719 own decisions match the submitted Cycle 3 source (`47c281bfb411…`). Both agents finish DONE, our runtime log has no stderr, and its maximum decision duration is 0.302481 seconds. Recorded-action resimulation reproduces every economic state and reconciles both cash accounts. [Full evidence](benchmarks/cycle-9-server.json).

This identifies the policy's behavior in this game. The supplied replay does not identify a submission ID, provide Ace Team's source, or establish the current ladder rating. The opponent's actions are observations of one trajectory, not code we can replay as a reactive counterfactual.

## What worked and what lost the game

| Measure | Unicorns / Cycle 3 | Ace Team |
| --- | ---: | ---: |
| Gross sales | 97,503 | 148,539 |
| Total expenses | 26,643 | 28,585 |
| Wages | 6,929 | 3,630 |
| Peak productive tiles | 36 | 75 |
| Peak hired hands | 12 | 11 |
| Physical wheat harvested | 48 | 517 |
| Strawberries harvested | 185 | 249 |
| Milk collected | 99 | 245 |
| Wool collected | 152 | 161 |
| Fertilizer collected | 211 | 369 |

Our routine was reliable: no ineffective non-pass operations, missed feeding, escapes, crop decay, overflow, or unsold terminal inventory/seeds. Fertilized strawberries and wool contributed 29,710 and 35,295 coins in gross receipts. Execution reliability remains useful, but it did not close a much larger production gap.

Ace Team earned 51,036 more sales while spending only 1,942 more overall. It acquired two extra quadrants, versus our one, and produced wheat, carrots and eggs in addition to the shared crops/livestock. The peak asset counts are not necessarily simultaneous. It spent 3,299 fewer coins on labor despite the larger productive footprint. Its recorded behavior therefore supports investigating production per labor coin and feed self-supply; it does not prove that copying its purchase sequence will work under different demand.

Our wheat purchases cost 8,927 and wheat sales brought 2,622, a net product cash flow of −6,305. Ace Team's wheat purchases cost 5,935 and sales brought 13,367, net +7,432. The 13,737 difference combines feed sourcing, sales, inventory timing and volumes. It is **not isolated wheat profit**: seeds, crop labor, and the value of wheat consumed by animals require separate allocation. Ace Team also bought and sold wheat; gross wheat sales alone do not measure its crop output.

The shared market matters. Both farms sold some milk at the one-coin floor: 19 units for us and 39 for Ace Team. Our average milk sale price was 71.2; its was 58.6. Greater production can depress both players' prices. Wool demand was better supported by three YARN_STORE openings, and our mean wool price stayed near 232 coins. These facts favor evaluating additional output against demand and rival supply, rather than maximizing physical yield alone.

This was not simply a last-turn liquidation failure. Our largest cash lead was only 1,166 at observation 163; our last positive lead was observation 249. We entered the final day already behind by 40,543. Final-day net receipts added 1,471 for us and 10,022 for Ace Team, including its late carrots and strawberries. Both emptied final inventories.

Ace Team had some ineffective work and 29 audited unfed animal-days, with no escapes or crop decay. Some late-season maintenance omissions may be intentional. These events do not justify imitating missed feeding; they show that zero operational waste alone is not the competition objective. Timing of extra production and its net revenue still dominate this result.

## Implication for the current implementation

Continue the already identified remaining-day cash correction as one bounded test. Our minimum cash in this game was 78, and a source-matched calibration finds underpriced current-day obligations at some purchases. Do not assume a stricter admission rule will improve this loss: declining a productive expansion could make the scale gap worse. Require the local head-to-head performance gate before changing the submitted agent.

Record the larger issue separately: benchmark more productive wheat/feed portfolios and labor allocation when choosing the next economic hypothesis. Current controls do not cover every behavior in Ace Team's changing wheat/carrot/goose portfolio. One replay cannot determine its optimizer, private forecasts, or exact objective weights.

The replay auditor initially failed while counting the rival's empty market orders (`[]`). The interpreter accepts and ignores these orders. The audit now skips them in requested-order statistics, with a focused regression test; agent behavior and executed transaction accounting are unchanged.
