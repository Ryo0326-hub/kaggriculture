# Cycle 4 — spatial admission did not qualify for promotion

**Decision: retain the submitted Cycle 3 agent.** The spatial challenger improved fresh matched score by only **0.83 percentage points**, with a whole-seed 95% interval of **−5.83 to +6.67 points**, and regressed against the strongest control. Both failures violate the [protocol frozen before evaluation](benchmarks/cycle-4-protocol.json). `main.py` remains byte-identical to `baselines/cycle_3.py`, SHA-256 `47c281bfb4118a9755f1759930b162de007efdfef3b23144457eccbaac42da0c`. No Kaggle upload or new release package was created.

The implementation is preserved in `scripts/make_spatial_control.py`; its generated standalone hash is `a9adaa81f622c8ea23d1a6c6b83bec95da66462bc33aa08a35637f55e6df7d5a`. Read the [CO and economics notes](CYCLE_4_OPTIMIZATION.md) and [complete checked experiment archive](benchmarks/cycle-4-spatial.json). Local CPU only, $0 new spending.

## Server evidence and hypothesis

The [three-game Cycle 3 audit](CYCLE_3_SERVER_ANALYSIS.md) confirmed one win and two losses, all 2,157 own decisions matching source, clean own execution and actual use of post-water fertilizer. In the two losses, rivals produced on 68/74 peak tiles versus our 37 while paying lower wages. Our late lead against Yendrew reversed when its remaining output became cash on Day 30; our own inventory was fully sold.

The old investment menu refused a new quadrant while more than six owned crop sites were vacant, and rejected batches no larger than the number of vacant owned sites. That treats locations as interchangeable despite travel costs. The single challenger removes those restrictions, requiring instead that a paid-land batch actually use a currently locked tile. All existing forecast, cash reserve, land cost, route, profitability ranking, fertilizer, harvest and hiring rules remain unchanged. The [plan](CYCLE_4_PLAN.md) records the hypothesis before development.

This repairs a real search restriction, but does not prove that more land is profitable. In the motivating public observation, newly enumerated one-crop land batches remained unprofitable and larger batches still failed the unchanged route forecast. The test was designed to establish whether a broader menu improves actual match outcomes.

## Development screen

Seeds 17/43, both seats, Cycle 3 / Step 8 / scaled mixed controls; 12 games per policy, two CPU processes, frozen sources and all replays retained.

| Policy | W / D / L | Match score | Mean cash | Mean wages | Mean peak productive tiles |
| --- | --- | ---: | ---: | ---: | ---: |
| Spatial challenger | 10 / 0 / 2 | 83.3% | 83,525.8 | 7,129.3 | 37.58 |
| Cycle 3 reference | 7 / 2 / 3 | 66.7% | 87,434.2 | 7,001.6 | 35.25 |

The challenger won all four direct games against Cycle 3; both policies won 4/4 against Step 8 and 2/4 against scaled mixed. The two development seeds cannot establish an improvement. Mean cash fell by 3,908.3 despite the increased match score, so this was not a simple efficiency gain. Every candidate game still bought exactly one extra quadrant.

Four development replays (candidate and reference, seed 17 seat 0, against Cycle 3 and scaled mixed) were resimulated exactly; all eight cash accounts reconcile and own decay, feeding, overflow and terminal-stock checks are clean. In the direct Cycle 3 case the candidate bought land at state 264 versus state 289 for the matched reference. It won 77,177–76,017 while the reference self-play finished 86,066–86,066. In the scaled case the candidate and reference outcomes were identical at 44,472–31,043. These audits establish execution and timing, not a fixed-demand causal cash effect.

## Fresh matched evaluation

The unchanged challenger and Cycle 3 reference each played seeds **9301–9320**, both seats, the same three frozen opponents and four CPU processes: **240 games**. All protocol fields, sources and result completeness are checked by `scripts/report_spatial.py`.

| Opponent | Spatial challenger | Cycle 3 reference |
| --- | ---: | ---: |
| Cycle 3 | 19 wins, 10 draws, 11 losses / 40 | 14 wins, 12 draws, 14 losses / 40 |
| Step 8 | 40 wins / 40 | 40 wins / 40 |
| Scaled mixed | **25 wins / 40** | **28 wins / 40** |
| Total | 84 wins, 10 draws, 26 losses | 82 wins, 12 draws, 26 losses |
| Match score, draws worth half | **74.17%** | **73.33%** |

The difference is one match point over 120 games. The 10,000-resample percentile interval resamples whole seeds, preserving seats and opponents: **−5.83 to +6.67 percentage points**. Five seed blocks improved, two regressed, thirteen tied. The strongest-control regression fails the separate opponent-class gate even without the uncertainty failure.

Mean cash fell from 84,776.2 to 84,409.7 (−366.6). Mean wages rose slightly from 7,078.0 to 7,083.8; mean productive footprint increased only from 36.26 to 37.09. The candidate bought a third quadrant in 25/120 games, versus none for Cycle 3. More land did not translate into the rivals' 68–74 productive tiles or a reliable win-rate gain.

Both policies completed all games without agent errors, detected unplanned crop losses, unfed animal-days, escapes, seed overrequests, duplicate service targets, or terminal goods/seeds. Maximum observed decision time was 0.479 seconds for the candidate and 0.253 for the reference. These are local measurements. Full executed overflow/decay accounting was performed in the selected audits, not inferred for every fresh game from attempted harvests.

This internal pool contains related policy families. Its score and interval do not estimate a ladder rating or medal probability. Seeds 9301–9320 are consumed evidence and cannot be reused as an untouched holdout after this review.

## Largest regression and policy-dependent town demand

Seed 9310 against scaled mixed changed from a win by **2,686** in each seat to a loss by **491** in each seat. Four diagnostic reruns exactly reproduced the fresh cash outcomes and all recorded economic diagnostics. The eight player accounts and all economic states reconcile. These are reproductions of consumed games, not extra independent evidence. [Executed regression profiles and engine mechanism](benchmarks/cycle-4-regression.json).

| Own result, each seat | Spatial challenger | Cycle 3 |
| --- | ---: | ---: |
| Final cash | 81,394 | 97,230 |
| Gross sales | 106,981 | 121,808 |
| Expenses | 28,587 | 27,578 |
| Peak cows | 4 | 8 |
| Milk harvested and sold | 129 | 192 |
| Strawberries harvested and sold | 202 | 158 |
| Extra quadrants purchased | 2 | 1 |
| Wages | 7,253 | 7,033 |

The larger crop allocation accompanied lower dairy output and lower overall receipts. But the whole 15,836 cash decline must **not** be described as an isolated crop-versus-cow effect at fixed market demand. The pinned engine's `_end_of_day` uses one seed/day RNG for weed generation on both farms and then town shop selection. Empty-cell counts affect how many draws precede the shop selection. Different occupancy therefore can produce different future shops even with the same seed.

The two towns first diverged at **state 288, Day 13**. The reference later received a yarn store and two smoothie shops; the candidate received additional farmers markets and a pizza shop instead. Both farms' production, investment and prices can respond. For example, both policies sold 68 wool, but received 5,403 versus 9,323 coins. Matched seeds compare complete policies under common initial randomness; they do not hold the entire future demand path fixed.

The next investment experiment should therefore calibrate dated marginal cash and service estimates under plausible future-shop scenarios, using current observations only. Keep current dispatch and hiring initially fixed. Do not keep relaxing acreage constraints until a desired farm size appears, or credit one crop with the whole effect of a changed town trajectory.

## Verification and reproduction

**165 tests passed**, including ten new admission, provenance and release-gate cases; Ruff lint and formatting passed. Tests confirm unchanged non-investment functions, frozen Cycle 3 identity, location-linked land use, real land cost, quadrant/cash/horizon limits and rejection of uncertain or regressing candidates. The unchanged current artifact already has exact public server evidence, so there is no reason to spend a submission slot or label this rejected challenger a new validated release.

```bash
uv run python -m scripts.make_spatial_control --output artifacts/spatial-repeat/main.py
uv run python evaluate.py --agent artifacts/spatial-repeat/main.py \
  --opponents baselines/cycle_3.py baselines/step_8.py opponents/scaled_mixed.py \
  --seeds 17 43 --workers 2 --replays all --output artifacts/spatial-repeat-eval
```

Use new output directories. The archive generator validates the complete development and fresh grids against the frozen protocol; the regression report records separate rerun manifests and replay/engine/audit hashes. The current Kaggle pair remains **Cycle 3 / Step 8** at the recorded snapshot. No new upload is recommended from this cycle.
