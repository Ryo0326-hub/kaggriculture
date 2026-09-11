# Cycle 3 — three public games and the next bottleneck

The supplied games contain **one win and two losses**. This is a three-game user-supplied sample, not a live leaderboard snapshot or an estimated win rate. Every economic state reproduces under the pinned engine; all six cash accounts reconcile. All **2,157 own decisions** match the frozen Cycle 3 source, `47c281bfb411…`. The three own logs contain no stderr; maximum server decision time is **0.254936 seconds**. [Reconciled evidence and provenance](benchmarks/cycle-3-public-three.json).

| Episode / opponent | Our cash | Opponent cash | Our margin | Productive tiles, ours / rival | Wages, ours / rival |
| --- | ---: | ---: | ---: | ---: | ---: |
| 107790825 / Yendrew Y | 85,591 | 97,127 | −11,536 | 37 / 68 | 7,795 / 4,673 |
| 107763520 / 李秉叡（ntumlnoob） | 81,229 | 93,210 | −11,981 | 37 / 74 | 7,318 / 4,502 |
| 107763714 / op_star_platinum | 85,023 | 64,596 | +20,427 | 36 / 65 | 6,355 / 8,207 |

Our farms had no ineffective non-pass commands, unfed animal-days, escaped animals, decayed crop units, explicit or overnight overflow, or unsold goods/seeds. These matches establish execution on Kaggle and public-game source correspondence. A separate official CLI check at September 11, 11:28 UTC confirms submission **56158876**, uploaded at 05:02:52 UTC, COMPLETE at a time-specific rating of 734.6. The latest-two pair is Cycle 3 / Step 8. The separate validation replay was not supplied. [Submission snapshot](benchmarks/cycle-4-submissions-snapshot.json).

The separate [transition diagnostics](benchmarks/cycle-3-public-operational.json) also show zero unintended crop-to-weed losses, seed overrequests or duplicate service targets on our side. They supplement the exact inventory/transaction audit rather than replacing its physical-production counts.

The Yendrew game illustrates why bank balance before termination can mislead. We began Day 30 ahead by **3,225**, but earned only **1,886 net cash** that day against **16,647** for the rival, producing the final 11,536 deficit. Its final-day strawberry receipts were 13,352 coins. Our inventory was fully sold: the reversal reflects the rival's remaining production/inventory becoming cash, not a failed terminal delivery on our farm. Intermediate bank balance excludes unsold assets and future output; it is not a mark-to-market estimate of who will win.

## What worked

**The fertilizer correction reached production.** Our farms made 48, 53 and 18 successful strawberry applications, including 37, 47 and 12 after watering: **96 of 119** applications used the newly available ordering. They harvested and sold 186, 210 and 72 strawberries. These are executed gains and sales, not summed harvest requests. We cannot infer the exact extra profit relative to the old bot from these games alone, because changing the policy changes both farms' future observations and prices.

**The economic portfolio responded to the market.** Against op_star_platinum, our eight-sheep peak herd sold 212 wool for 51,541 coins. The rival peaked at eight cows but sold 201 milk for only 7,126 coins in that market. Our two-cow peak herd avoided that degree of dairy exposure. These are gross product receipts; feed, purchases and labor still have to be paid. Our win decomposes into 13,814 more gross sales plus 6,613 lower expenses, totaling 20,427.

**Inventory discipline preserved output.** Our winning farm sold every harvested unit, while op_star_platinum harvested 246 strawberries but sold only 160 and suffered eight overnight overflow events across its products. It also ended with eight goods and 19 unused seeds. Bigger physical production can lose when storage or sale execution fails. The exact overflow events are in the audit; the difference between harvest and sales is not by itself a count of overflow.

## What did not work

**The two losses were production/expense allocation gaps.** Yendrew Y generated 14,576 more gross sales while paying only 3,040 more total expenses. Its 199 strawberry sales and 162 milk sales exceeded our 186 and 135; carrots added 10,350 gross receipts, although seed, labor and losses must be charged against them. It reached a third quadrant and paid 3,122 less in wages despite nearly twice our peak productive footprint.

ntumlnoob earned 18,080 more gross sales for 6,099 more expenses. Our strawberry output was stronger (210 versus 123 harvested), but the rival produced 182 milk, 298 fertilizer and 378 wheat versus our 102, 140 and 52. Its milk sales alone exceeded ours by 18,425 coins. It still won with 62 unfed animal-days, 15 escapes, crop decay and overflow. Copying those losses would not be a sound strategy; the evidence supports investigating profitable productive capacity.

**Available land is not equivalent to serviceable land.** In the ntumlnoob replay at state 313 (Day 14, hour 1), we hold 16,230 coins and 32 crops. All eleven investment alternatives fail the route forecast. Eight empty owned crop sites also trigger a rule excluding the next quadrant entirely. This is not proof that a larger portfolio fits: when the new admission rule is applied to this same observation, feasible one-crop land batches have negative marginal value, and larger batches still fail the existing forecast.

There is nevertheless an unjustified dominance assumption in the old candidate menu: an empty distant tile is treated as a substitute for a near-shed tile across the quadrant boundary. The next bounded implementation removes that assumption while retaining location-specific travel, full land cost, marginal wages, input cost, remaining-season payback and cash reserves. [Cycle 4 pre-experiment plan](CYCLE_4_PLAN.md).

**Wage savings alone remain an inadequate target.** PASS counts are high on our farms, but the prior Cycle 2 staffing experiments failed to improve match score. Paid idle time is a diagnostic, not automatically recoverable profit. The new test changes which spatial investment alternatives are considered, not the worker-count or dispatch rule. Conditional investment and hiring counts may still differ later because production and cash change.

## Reproduce the audit

Run `scripts/audit_replay.py` on the three downloaded replays into a new directory, then run `python -m scripts.report_server` with `--replays`, matching `--logs` in the same order, `--source baselines/cycle_3.py`, `--audit-directory` and a fresh `--output`. The reporter rejects mismatched source decisions, incomplete logs and mismatched episode/log filenames, and requires the reconciled replay hashes. Raw replays remain in ignored local storage; compact checked evidence is committed.
