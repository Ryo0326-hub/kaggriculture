# Cycle 2 — staffing savings did not earn a release

**Decision: retain the submitted Step 8 file.** Implemented six bounded challengers, a controlled installed-farm harness, and a staffing forecast diagnostic. None improved the matched development match score. Two forecast variants introduced operational regressions. No Kaggle upload was made, and no fresh validation seeds were consumed.

`main.py` remains byte-identical to `baselines/step_8.py`, SHA-256 `63dbf4381d8607cbd681f5296749f4f8af4cc37d0181f97d6b8931f6078d3f72`. Experimental policy sources live under `experiments/`; they are not release candidates. This cycle does not change the previously recorded Steps 8/7 submission pair or establish a new server result.

## What was implemented

The [pre-experiment hypothesis](CYCLE_2_PLAN.md) separated execution from investment. The incumbent crop dispatcher already allowed ordinary-night automatic deposit. The proposed changes therefore tested livestock route bounds, dated crop staffing, and the investment forecast that pays for those workers.

- **Open livestock routes:** omit the return edge and deposit allowance on ordinary days; preserve production-day dedicated livestock workers and explicit final-day delivery.
- **Dated crop staffing:** count actual water/harvest/planting jobs and construct crop tours, then add the separately committed animal crew. Existing execution still replans and can borrow released workers; a tour is not an executable schedule certificate.
- **Staffing forecast:** use the same livestock service dates and route geometry, and charge the actual discrete wage curve through thirteen total workers. Compare the legacy crop hiring budget with a dated crop estimate. Deduct wages already paid today rather than charging them again.
- **Controlled harness:** identical preinstalled assets, starting cash and inputs; capital purchases disabled. Instrument the actual engine to count executed wages, inventory gains, decay, overflow, feeding, and final stock. Reconcile every player's cash as starting cash plus sales minus spending.

The three dispatch-only artifacts come from `experiments/staffing_dispatch.py`; the three forecast artifacts come from `experiments/staffing.py`. All six generated files were reconstructed and matched their recorded SHA-256 hashes exactly. Historical engine/version, source hashes, all match rows, executed fixture accounts, daily wages and compact staffing traces are in [the evidence archive](benchmarks/cycle-2-staffing.json). Detailed routes remain in the ignored raw local fixture artifact, whose hash is recorded there.

## Controlled installed portfolios: useful savings, conditional on layout

Thirty-six games: three policies × three installed portfolios × seeds 17/43 × both seats. Portfolios contain ten alternating cows/sheep and 15/35/55 wheat/melon/strawberry plots on one/two/three quadrants. Both sides receive 30,000 cash, 20 wheat and 20 fertilizer; initial crops are watered. They do not purchase new seeds, animals or land. These are modified-start experiments, not competition scores.

Mean candidate minus reference cash, and reference minus candidate wages, in coins:

| Execution change | Installed assets | Cash gain | Wage saving | Strawberry output change |
| --- | ---: | ---: | ---: | ---: |
| Open routes | 25 | −1,288 | 399 | −2 |
| Open routes | 45 | 815.5 | 242 | 0 |
| Open routes | 65 | 5,611.5 | 77 | −10 |
| Dated staffing, closed routes | 25 | 815 | 819 | 0 |
| Dated staffing, closed routes | 45 | 624 | 298 | 0 |
| Dated staffing, closed routes | 65 | 1,107 | 1,107 | 0 |
| Dated staffing, open routes | 25 | 133.5 | 1,981 | −2 |
| Dated staffing, open routes | 45 | 2,468 | 1,968 | 0 |
| Dated staffing, open routes | 65 | 7,328 | 2,485 | −10 |

Other harvested/collected quantities were unchanged. Both sides finished all fixtures without missed feeding, escapes, decayed units, explicit or overnight overflow, or terminal inventory. All 72 cash accounts reconcile. A preliminary unchanged-versus-unchanged fixture also produced zero cash and wage differences in both seats.

The output reductions are real: open-route policies made zero successful fertilizer applications versus one on the small farm, and three versus eight on the large farm. This is consistent with the missing strawberries; it is not a claim that every cash difference is caused by fertilizer. On the small farm, open routes reduced gross sales by 1,682.5 while saving only 394.5 in total expenses. On the large farm, open routes increased gross sales by 5,533 despite fewer strawberries. Sale timing, shared prices, and input purchase timing matter alongside physical output. The constant sale policy does not imply constant sale times.

## Standard starts: the improvement did not transfer

Fifty-six games: Step 8 plus six candidates, each on seeds 17/43 in both seats against frozen Step 8 and `scaled_mixed.py`. Same environment, opponent files and evaluator; two local CPU processes. Match score is `(wins + 0.5 × draws) / games`, not Kaggle's displayed rating.

| Policy | W / D / L | Match score | Mean cash change versus matched Step 8 runs | Mean wages | Mean peak productive tiles |
| --- | --- | ---: | ---: | ---: | ---: |
| Step 8 reference | 3 / 2 / 3 | 50% | 0 | 6,986.4 | 35.4 |
| Open routes | 1 / 0 / 7 | 12.5% | +99.9 | 6,956.3 | 35.3 |
| Dated staffing, closed routes | 4 / 0 / 4 | 50% | −826.1 | 8,123.5 | 35.8 |
| Dated staffing, open routes | 3 / 0 / 5 | 37.5% | +4,724.8 | 4,029.6 | 35.5 |
| Forecast only | 3 / 0 / 5 | 37.5% | −1,449.0 | 8,309.9 | 53.1 |
| Open routes + forecast | 2 / 0 / 6 | 25% | −2,595.6 | 8,140.3 | 49.6 |
| Open routes + dated staffing + forecast | 2 / 0 / 6 | 25% | −986.4 | 5,213.8 | 41.5 |

Step 8's self-play produced two draws and one win/loss pair, reflecting seat-sensitive game dynamics. The dated/closed candidate tied Step 8's score against each opponent; its average cash and margin were lower. The combined candidate lost all four games against the larger mixed control. The dated/open candidate earned more cash and spent less on labor, but its opponents also benefited from the changed market and production path; it won fewer matches. It is not enough to maximize our cash in isolation.

All games completed without agent errors. The slowest observed candidate decision was 0.562 seconds under this local load, not a server guarantee. No candidate had missed feeding or escaped animals. Dispatch-only controls had no detected unplanned crop losses or terminal stock. Forecast-only lost one crop in seed 43, seat 1 against Step 8; open/forecast left four and three unused seeds in the two seed-43 Step 8 games. Those are additional reasons to reject release, even though the affected forecast-only game won.

These are two development seeds, six attempted variants and related opponent families. They do not establish that a policy is universally inferior or estimate a ladder win rate. They do establish insufficient evidence to displace a validated submission. No parameters were repeatedly tuned to these outcomes, and no claimed holdout was reused.

## The forecast diagnosis

At the initial installed-farm state, the old routed investment forecast rejected all three portfolios, although the actual dispatcher serviced them without the measured losses above. Conservative round trips from the worst shed start can reject a distant corner; combining animal and crop work in hypothetical tours also differs from actual dedicated livestock crews. A rejected heuristic schedule is not proof that the farm is infeasible.

The new legacy-budget forecast predicted season wages of 3,555 / 5,508 / 6,783 coins for the three installed portfolios, matching the executed reference wages in this experiment. Its open-route counterpart predicted 3,156 / 5,266 / 6,706, also matching the executed open-route policy. That is a useful calibration result, restricted to these fixtures.

The fully dated forecast remained unreliable: it predicted 1,150 for the small farm versus 1,574 executed, and rejected both larger farms despite successful execution. It over-reserves separate crews on some dates while missing repair and assignment costs on others. Standard-start forecast-only expanded the mean peak footprint from 35.4 to 53.1, but higher wages and a crop loss accompanied a lower match score. More permissive admission does not prove additional capacity is profitable or serviceable.

## CO250 and economic interpretation

Let binary `z_r` select a candidate worker route, and `a_jr` indicate whether it serves job `j`. A basic route-cover model has `sum_r a_jr z_r >= 1` for each required job, with route travel, service and input-handling time bounded by the available day. Ordinary-night deposit removes a terminal travel edge; the final day retains that edge and enough time to sell. The bounded livestock solver enumerates small routes; crop insertion is a heuristic. Neither is a global integer-programming optimum for the whole farm.

Labor is discrete. With `m` total workers, only `m−1` are hired: `W(m) = sum_{i=0}^{m−2} F_i` using the engine's `1, 1, 2, 3, …` wage sequence. Twelve total workers cost 232 per day; thirteen cost 376. Removing one route has no wage value unless it actually removes a paid worker, and the marginal saving depends on which worker disappears. Already-paid wages are sunk for today's next decision.

In duality language, scarce worker time has an opportunity value: spending an action walking or saving a deposit may prevent a fertilizer application or an earlier sale. We did not solve an LP or compute exact dual prices. The useful next estimate is **incremental realized receipt per scarce action**, accounting for inputs, maturity, remaining service and market impact. Optional work must compete on that value rather than a blanket wage-minimization rule.

The strategic objective is winning the match. A changed sale path changes the rival's prices and subsequent decisions. Here +4,724.8 average own cash accompanied a lower match score. This is why matched reactive opponents and separate cash/output accounts are necessary; it is not a Nash-equilibrium calculation.

## Next hypothesis and verification

Cycle 3 should test **marginal fertilizer and harvest timing**, keeping Step 8's investment and hiring policy fixed initially. Measure whether prioritizing an extra fertilizer application or earlier harvest pays for its input and worker actions before the relevant sale deadline. Use the small-farm fertilizer regression as a development case. Only a clean, repeatable improvement should advance to frozen fresh-seed evaluation. The broad staffing/forecast redesign is parked.

Verification covers exact route travel against enumeration, animal staffing parity on normal/production/final dates, the thirteenth worker's marginal wage, exclusion of paid wages, unknown asset locations, disabled-forecast execution parity, preserved Step 8 actions and bytes, and the existing isolated full-season submission check. No new server validation was requested because no challenger qualified for upload.

Final local checks: **140 tests passed**, Ruff lint and formatting passed. After moving the policies into the archive, a full-season fixture reproduced its cash, wages, physical outputs, daily accounts and operational metrics exactly. The six standard-start candidate files also regenerated byte-for-byte from the archived sources.

## Reproduction

Use fresh output directories. The archived source files intentionally retain their original bytes; changing an import in the harness to the archived policy changes the runner hash, not the policy being tested.

```bash
uv run python -m scripts.benchmark_staffing --seeds 17 43 --quadrants 1 2 3 \
  --modes open_routes dated_closed dated_open --workers 2 --output artifacts/cycle-2-repeat

uv run python -m scripts.make_staffing_control --source experiments/staffing_dispatch.py \
  --mode dated_open --output artifacts/cycle-2-repeat-controls/dated-open.py
uv run python -m scripts.make_staffing_control --source experiments/staffing.py \
  --mode combined --output artifacts/cycle-2-repeat-controls/combined.py

uv run python evaluate.py --agent artifacts/cycle-2-repeat-controls/combined.py \
  --opponents baselines/step_8.py opponents/scaled_mixed.py --seeds 17 43 \
  --workers 2 --output artifacts/cycle-2-repeat-combined
```

The report generator `scripts/report_staffing.py` validates the complete original run grid and common environment before archiving it. The raw initial forecast probe is preserved in the evidence archive; it is a diagnostic, not another match.
