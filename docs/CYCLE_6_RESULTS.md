# Cycle 6 — waiting and supply stress rejected

**Retain Cycle 3; no upload.** The corrected, cached waiting challenger scored **38.9%** versus **72.2%** for the incumbent and exceeded the one-second decision target. It failed the preregistered development gate. No fresh seeds or release package were used. [Plan](CYCLE_6_PLAN.md), [CO/economics notes](CYCLE_6_OPTIMIZATION.md), [checked full archive](benchmarks/cycle-6-information.json).

The generated source hash is `6365a19af351075e5942654a52a4b2fd6f75678547adc4d429eaafc9dee56724`. It is reproducible with `uv run python -m scripts.make_information_control --output NEW_DIRECTORY/main.py`. The submitted `main.py` remains `47c281bfb4118a9755f1759930b162de007efdfef3b23144457eccbaac42da0c`.

Combined repository verification after Cycles 6/7: **201 tests passed**, lint and formatting checks passed, and both final challenger hashes reproduce from their generators. No additional packages or paid compute were used.

## Completed development comparison

Consumed seeds **17, 43, 9310**, both seats, the same three frozen opponents, two CPU processes per policy. Candidate and reference each completed 18 games. Two superseded engineering runs contain four completed games each: the first inherited a wheat-accounting error; the second was replaced by an equivalent labor-cache implementation. Neither partial run enters the comparison or increases its sample size. The archive retains their manifests and records separately.

| Measure | Waiting challenger | Cycle 3 |
| --- | ---: | ---: |
| Win / draw / loss | 7 / 0 / 11 | 11 / 4 / 3 |
| Match score | **38.9%** | **72.2%** |
| Versus Cycle 3 | 0 wins / 6 | 1 win, 4 draws, 1 loss |
| Versus Step 8 | 5 wins / 6 | 6 wins / 6 |
| Versus scaled mixed | 2 wins / 6 | 4 wins / 6 |
| Mean own cash | 91,865.9 | 90,226.6 |
| Mean cash margin | −2,976.4 | +5,377.3 |
| Mean wages | 5,761.3 | 7,055.2 |
| Mean productive footprint | 31.89 | 35.83 |
| Mean strawberries produced | 112.00 | 163.78 |
| Maximum observed decision | **1.636 s** | **0.301 s** |

The policy saved wages and produced on fewer plots. Its slightly higher average own cash did not translate into wins. Optimizing own forecast cash is an imperfect surrogate in a shared market, where changed production can benefit the opponent too.

Both full runs completed without agent errors, detected unplanned crop losses, missed feeds, escapes, seed conflicts, duplicate crop jobs or terminal goods/seeds. The local engine completed the challenger games despite individual decisions over one second; that does not establish sufficient server runtime headroom. No attempt was made to promote or upload this slow policy.

## What the actual decisions show

In seed 17, seat 0 versus Cycle 3, the first changed action follows observation 48 (displayed Day 3, hour 0). The model estimates an immediate purchase at **914.4** marginal coins, versus a branch-dependent delayed purchase at **3,874.1**. It waits. Its hypothetical next-day choices include four strawberries under several shops, a cow under dairy buyers, or a sheep under a yarn store. After the actual yarn store appears, it buys a sheep. Both first divergent decisions reproduce exactly from identical recorded observations.

The final challenger farm makes more wool but less milk, melon and strawberry output. It loses **80,878–94,466**; the matched reference self-play ties **86,066–86,066**. Own expenses fall by 1,486, but receipts fall by 6,674. The town paths diverge at observation 72, so this is a whole-policy comparison, not an isolated fixed-demand effect of the first skipped purchase.

The strongest-control diagnostic is especially instructive. In seed 9310, seat 0, own cash rises from **97,230** to **105,906**, but rival cash rises from **94,544** to **108,361**. A win by 2,686 becomes a loss by 2,455. The challenger produces 228 milk versus 192 and 95 strawberries versus 158. Towns diverge at observation 144. Higher own income alone therefore does not establish improved competitive performance.

All four selected replays resimulate exactly and all eight cash accounts reconcile. The four own accounts have no ineffective non-pass operations, decayed crop units, missed feed, escapes, overflow or terminal stock. The first candidate audit reaches 118 actual cash, below the forecast's 150-coin reserve: the reserve is a model constraint, not a realized-cash guarantee.

## Decision and follow-up

The waiting comparison forecasts one immediate purchase and no later investment, but allows a delayed purchase after intervening receipts. It mixes information value with timing and liquidity and omits buying now **and** investing later. Together with approximate routes, future rival behavior and later shop demand, this limits its economic interpretation. We did not tune the scenario tree after its failure.

The implementation review also found a separate conservation error: rival wheat was used to reduce estimated feed purchases and then all sold again. [Cycle 7](CYCLE_7_RESULTS.md) tests only that correction, separately from this unsuccessful waiting policy. Its reference reuses the same 18 incumbent games, which remain one body of evidence. Fresh seeds 9401–9420 remain unused by Cycle 6.

The full archive can be regenerated from the retained local artifacts with:

```bash
uv run python -m scripts.report_information \
  --source artifacts/cycle-6-information-final/main.py --output NEW_REPORT.json
```
