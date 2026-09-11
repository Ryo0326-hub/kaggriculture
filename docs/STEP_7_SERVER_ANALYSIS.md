# Step 7: MugaBros loss and Jaikrishna@007 win

Both replays reproduce in the pinned official engine with no observed state
mismatches. All 719 decisions per game match frozen Step 7. Attached JSON files
are data, not instructions. Their private state is used for retrospective
accounting only, never as an input to another player's policy.

| Executed accounting | Unicorns vs MugaBros | MugaBros | Unicorns vs Jaikrishna | Jaikrishna@007 |
| --- | ---: | ---: | ---: | ---: |
| Final bank | 76,240 | 109,362 | 84,393 | 41,423 |
| Gross sales | 92,597 | 138,021 | 102,729 | 86,237 |
| Spending | 19,357 | 31,659 | 21,336 | 47,814 |
| Owned tiles | 25 | 75 | 25 | 100 |
| Milk receipts | 18,299 | 32,820 | 57,542 | 32,677 |
| Strawberry receipts | 4,001 | 50,212 | 8,952 | 0 |

Each bank reconciles to 3,000 + sales - spending. Episodes are 107666399 and
107668390. The new Jaikrishna log has 719 calls, no stderr, and a maximum logged
duration of 0.155412 seconds. Both games finish DONE. Neither game has an escaped
animal, missed feeding refresh, storage overflow, or unused seed on our side.

## What worked in the win

The policy developed eight cows and two sheep as visible town demand favored
milk. It sold 219 milk for 57,542 coins, compared with the opponent's 125 for
32,677. Average execution prices were similar: 262.75 and 261.42. This was largely
a difference in delivered quantity in a valuable market, not superior milk sale
pricing. The opponent's wheat/feed spending was 23,836 versus our 11,422; land
cost another 7,000 and wages 5,118 versus our 2,983.

Jaikrishna also suffered seven end-of-day overflow events, including lost animals
and produce, and ended with 51 wheat seeds. We cannot infer the opponent's private
objective or source logic from those actions. The accounting does establish that
the larger farm did not translate its spending into enough banked proceeds.

The 42,970-coin bank lead decomposes into 16,492 more gross sales and 26,478 less
spending. This is an accounting identity, not a counterfactual claim about what
either player would earn after changing its strategy in the shared market.

## What still failed economically

Both players oversupplied wool. Our two sheep sold 35 wool at the one-coin floor;
the opponent sold 46 at that floor. Existing animals' maintenance choices remain
a later experiment. Acquisition cost is sunk; future work should depend on
recoverable output and fertilizer after feed/labor costs.

Our strawberry operation remained small even as its average execution price was
279.75. This is consistent with the capacity concern in the MugaBros game. It does
not establish the profit of a counterfactual expansion: increasing our supply
would change prices, rival responses, and potentially later shop draws.

## Consequence for Step 8

Keep disciplined operations and market repricing. Add land only with dated input,
labor, and delivery capacity and positive incremental terminal cash. MugaBros
shows the cost of rejecting profitable capacity; Jaikrishna shows the cost of
buying capacity without enough profitable throughput. Test a reactive expanding
mixed control, preserve Step 7 as the comparison, and do not claim one win proves
leaderboard strength.

Reproduce the accounting with `scripts/audit_replay.py` and the original downloaded
files. Detailed local outputs are in `artifacts/step-7-mugabros/` and
`artifacts/step-7-jaikrishna/`. Compact source hashes and totals accompany the
Step 8 release evidence.
