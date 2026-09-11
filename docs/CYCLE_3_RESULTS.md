# Cycle 3 — strawberry fertilizer timing

Subsequent server update: submission **56158876** is COMPLETE, and three supplied public games match all 2,157 own decisions with clean execution (one win, two losses). [Server analysis](CYCLE_3_SERVER_ANALYSIS.md). Upload-pending language below records the original implementation checkpoint.

**Decision: advance fertilizer timing as the current local agent.** The fresh matched evaluation improved match score from 60.8% to 86.7%, including an improvement against the stronger mixed control. Investment and hiring rules remain unchanged; the old harvest rule is retained. `main.py` and the isolated release file have the exact frozen hash `47c281bfb4118a9755f1759930b162de007efdfef3b23144457eccbaac42da0c`. Step 8 remains preserved in `baselines/step_8.py`. Kaggle upload and server validation are pending.

Read the [implementation and CO notes](CYCLE_3_OPTIMIZATION.md) for crop-specific precedence, input opportunity cost and why the separate harvest experiment is not selected. [Complete development and fresh-game evidence](benchmarks/cycle-3-timing.json).

## Development screen

The [plan](CYCLE_3_PLAN.md) was written before the experiments. Three policies were tested: fertilizer timing, early wheat harvest, and both. The exact Step 8 artifact remained unchanged during development. All computation used local CPUs with no new spending.

Thirty-six installed-portfolio games used seeds 17/43, both seats, and 25/45/65 preinstalled assets. Ten animals and the remaining wheat/melon/strawberry crops received identical starting inputs; no new capital purchases were allowed. All 72 player cash accounts reconciled. Both sides completed without missed feeding, escapes, decayed units, overflow or final inventory. These are modified-start experiments, not competition scores.

| Policy | Assets | Mean cash difference | Mean extra strawberries | Mean wheat difference | Wage difference |
| --- | ---: | ---: | ---: | ---: | ---: |
| Fertilizer timing | 25 | +2,749 | +18 | 0 | 0 |
| Fertilizer timing | 45 | +2,236.5 | +35 | 0 | 0 |
| Fertilizer timing | 65 | −33 | +30.5 | 0 | 0 |
| Harvest timing | 25 | 0 | 0 | 0 | 0 |
| Harvest timing | 45 | −321 | 0 | −12 | 0 |
| Harvest timing | 65 | −171 | 0 | −19 | 0 |
| Both | 25 | +2,749 | +18 | 0 | 0 |
| Both | 45 | +1,928.5 | +35 | −12 | 0 |
| Both | 65 | −204 | +30.5 | −19 | 0 |

The fertilizer result is economically conditional: on the largest installed portfolio, seed 17 lost 350 coins while seed 43 gained 284. Extra berries do not guarantee extra profit when fertilizer could be sold and the additional supply changes market prices. No claim of uniformly better cash is made. Early harvest gave up wheat without reducing executed wages; its assumed value for saved actions did not materialize in these fixtures.

Twenty-four normal-start games tested the three candidates on the same two seeds and seats against Step 8 and the frozen larger mixed control. Eight matching Step 8 reference games were reused from Cycle 2 after verifying identical environment, runner, opponent hashes, seeds, seats and concurrency.

| Policy | W / D / L | Match score | Mean cash | Mean wages | Mean strawberry harvest |
| --- | --- | ---: | ---: | ---: | ---: |
| Step 8 reference | 3 / 2 / 3 | 50% | 82,552.9 | 6,986.4 | 91.5 |
| Fertilizer timing | 6 / 0 / 2 | 75% | 88,130.3 | 6,971.4 | 136.8 |
| Harvest timing | 3 / 2 / 3 | 50% | 82,552.9 | 6,986.4 | 91.5 |
| Both | 6 / 0 / 2 | 75% | 88,130.3 | 6,971.4 | 136.8 |

Fertilizer-only won all four Step 8 games and split the larger-control games 2–2. All normal-start games completed without agent errors or detected unplanned crop losses, missed feeding, escapes or terminal stock. These two development seeds cannot establish ladder strength.

The harvest-only agent emitted exactly the same actions as the reference across all eight games. The combined agent emitted exactly the same actions as fertilizer-only across all eight games. Fertilizer-only was therefore selected before the fresh evaluation, preserving the old harvest rule.

## Reconciled execution evidence

Two normal-start replays were resimulated through the actual engine with transaction and unit-action hooks. Their complete economic state matched; all four cash accounts reconciled. [Audit evidence](benchmarks/cycle-3-dev-audit.json).

- Seed 17, seat 0 versus Step 8: 88,897–79,976. Our farm harvested 175 strawberries versus 116. It made 44 successful strawberry fertilizer applications; 35 were requested after watering. Step 8 made 14, all before watering.
- Seed 43, seat 1 versus the larger mixed control: 119,074–119,927, a loss by 853. Our farm harvested 166 strawberries versus 249. It made 42 strawberry applications, including 28 after watering. This remains a useful production-scale stress case, not a victory to include in the record.

These audits distinguish actual inventory gains and cash from estimated future receipts. They support the intended timing mechanism, while the larger-control loss shows that the correction does not solve the whole farm-allocation problem.

## Frozen comparison and release checks

The [frozen protocol](benchmarks/cycle-3-protocol.json) specifies seeds 9201–9220, both seats, Step 8 plus the larger and original expanding mixed controls, and four CPU processes for both policies: 120 games per policy. The selected file differs from its development artifact only in the default argument used by `expansion_turn`, so direct explanations select fertilizer mode as well. Both agent entry points explicitly pass the same fertilizer mode. No strategy change is permitted during evaluation.

| Frozen opponent | Fertilizer candidate | Step 8 reference |
| --- | ---: | ---: |
| Step 8 | 40 wins / 40 | 11 wins, 18 draws, 11 losses / 40 |
| Larger mixed control | 24 wins / 40 | 13 wins / 40 |
| Original expanding control | 40 wins / 40 | 40 wins / 40 |
| **Overall match score** | **86.7%** | **60.8%** |

The candidate recorded 104 wins and 16 losses; the reference recorded 64 wins, 18 draws and 38 losses. Count draws as half a point. The paired score improvement is **25.83 percentage points**, with a whole-seed 95% percentile bootstrap interval of **+20.0 to +32.5 points** across 10,000 resamples. All twenty seed blocks had positive score differences. No opponent class regressed in aggregate.

Mean candidate cash was 90,106.6 versus 81,348.3, an increase of 8,758.4. Mean strawberry harvest was 144.3 versus 91.2 units. Mean wages were almost unchanged: 7,021.3 versus 7,032.6. These standard-game output/cost counters are evaluator diagnostics; the earlier replay audits establish executed accounting in two representative games. The result primarily supports improved production timing, not a labor-policy redesign.

Both policies completed all 120 games without agent errors, detected unplanned crop losses, unfed animal days, escapes, duplicate crop targets, seed overrequests or terminal inventory/seeds. Maximum observed candidate decision time was 0.519 seconds with four local simulation processes; the reference maximum was 0.468 seconds. These are local measurements, not server guarantees.

The two mixed controls share lineage and do not represent two independent algorithm families. The interval describes this internal pool and excludes untested opponent classes; it does not certify a medal or predict a live Kaggle rating. The candidate still lost 16/40 against the strongest control, and the largest installed-farm fixture had mixed cash results.

The exact copied file passed isolated official-loader self-play at seed 505: 720 recorded states, both agents DONE, no failures or stderr, no final inventory or unused seeds, cash 59,398 / 59,300, maximum decision time 0.235 seconds. [Validation record](benchmarks/cycle-3-local-validation.json). The ready file is `artifacts/submission-cycle-3-fertilizer/main.py`; it requires no other repository files. Final local verification passed **155 tests**, Ruff lint and formatting. No Kaggle upload was performed during this implementation. The last recorded latest-two pair remains Steps 8 and 7; a new upload would displace Step 7 if that pair is unchanged.

Next checkpoint: review the intended latest-two pair, upload the exact qualified file, reconcile its server validation and collect actual ladder evidence before another strategy change. Source control, local qualification and server validation are distinct stages.

## Reproduce

Use fresh output directories:

```bash
uv run python -m scripts.benchmark_timing --workers 2 --output artifacts/timing-fixtures
uv run python -m scripts.make_timing_control --mode fertilizer --bake-default \
  --output artifacts/timing-candidate/main.py
uv run python evaluate.py --agent artifacts/timing-candidate/main.py \
  --opponents baselines/step_8.py opponents/scaled_mixed.py --seeds 17 43 \
  --workers 2 --output artifacts/timing-development
```

The fixture harness records executed crop work and sales by date, source hashes, cash reconciliation and operational diagnostics. `scripts/report_timing.py` checks completeness and matched environments before archiving the development and fresh comparison results. The prototype's investment and hiring rules are checked against frozen Step 8 source; engine tests cover ordering, capacity, expiry, final-night boundaries and shared tile reservations.
