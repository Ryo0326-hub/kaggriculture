# Cycle 10 — opening experiment rejected

**Implemented and tested; no promotion or upload.** The wheat-inclusive opening scored 50.0% versus 79.2% for Cycle 3 on the preregistered 24-game development grid per policy. All games completed with clean own operational checks and no terminal inventory. The incumbent `main.py` remains byte-identical to `baselines/cycle_3.py` (`47c281bfb411…`). Reserved seeds 9401–9420 remain unused.

The original Steps 1–8 already delivered a functioning, server-validated agent. Cycle 10 is a competitive improvement experiment under the revised plan, not the tenth incomplete component of an eleven-step agent. [Frozen plan](CYCLE_10_PLAN.md), [economic/CO notes](CYCLE_10_OPTIMIZATION.md), [complete machine-readable evidence](benchmarks/cycle-10-opening.json).

## What changed

Only the opening portfolio menu and its first-stage purchase orders change. Thirty wheat-to-melon sequences extend the original twenty portfolios; original option forecasts are preserved exactly. The chosen opening is two cows, two sheep, four melons and eight wheat, versus the incumbent's same animals and eight melons. The candidate spends 2,200 immediately versus 2,440 and forecasts another 640 in possible later melon seeds. Subsequent purchases, actual hiring/dispatch, fertilizer and sales retain the incumbent code.

Candidate SHA-256: `8238417035610248ca48a7a497e480ed66eab970f4c9ef7ae79f9b6597216b72`.

A related wheat-heavy scaled-mixed variant plants wheat throughout the season, with fifteen opening wheat seeds in place of six melons and nine wheat. Its animal, land and work policy is unchanged; initial cost is corrected from 2,370 to 1,950. This is a supply stress variant in the same control family, not an independent reconstruction of a top player. SHA-256: `0a1e10f047db34da9a8199f6880f399b521589fb7da03bb5d0a1161a2f9e2e62`.

Both generated sources reproduce byte-for-byte. Seven new tests cover original-option preservation, dated land/cost constraints, first-stage orders, own feed conservation, source isolation, control loading, actual opening service and the stricter development gate. The complete suite passed **221 tests**; lint and formatting passed.

## Complete development comparison

Consumed seeds 17/43/9310, both seats, four controls, two CPU processes. These are 48 complete games on three seed blocks, not 48 independent observations. All eighteen regenerated reference games on the old three-control grid exactly match their previously recorded economics and outcomes. Regeneration provides the new complete comparison grid without making those seeds fresh.

| Measure | Wheat opening | Cycle 3 |
| --- | ---: | ---: |
| Wins / draws / losses | 12 / 0 / 12 | 17 / 4 / 3 |
| Match score | 50.0% | 79.2% |
| Mean own terminal cash | 86,454.5 | 93,406.5 |
| Mean cash margin | +10,261.4 | +16,909.5 |
| Mean wages | 7,353.8 | 6,955.3 |
| Mean peak productive tiles | 35.1 | 35.6 |
| Mean harvested wheat | 105.8 | 32.4 |
| Maximum observed decision time | 0.272393 s | 0.378734 s |

| Opponent | Wheat opening score | Cycle 3 score |
| --- | ---: | ---: |
| Cycle 3 | 16.7% | 50.0% |
| Step 8 | 83.3% | 100.0% |
| Scaled mixed | 0.0% | 66.7% |
| Wheat-heavy scaled variant | 100.0% | 100.0% |

The development gate fails both aggregate improvement and opponent-stratum preservation. A descriptive paired whole-seed bootstrap interval is −50 to 0 percentage points; with three consumed blocks it is not a fresh confidence claim about the leaderboard. More wheat production did not make the bot stronger on this grid. No candidate tuning followed these results.

## What worked and what failed

The new opening physically works: eight wheat plots are planted and watered on day 0, and the audited branches harvest 32 wheat on day 4. Cash arrives sooner, and the ordinary spending rules can reinvest it. In both audited branches the opening needs eight hired hands costing 54 on day 0, versus five costing 12 for the incumbent. Cheap seeds do not imply cheap service.

The sequence used to justify the purchase is not what the later policy necessarily executes. In both selected candidate branches it buys a cow during day 4 and another on day 5, instead of buying the forecast eight day-5 melons. This is allowed adaptive behavior, but it limits the opening projection's ability to rank actual full-season policies. Neither forecast contribution nor early liquidity can substitute for reactive match results.

The two diagnostic cases were selected by largest negative and positive change in cash margin, as preregistered. Both players' economic state is reproduced at every step, and all **eight cash accounts reconcile**:

- **Largest regression, seed 17, seat 1 versus scaled mixed:** the incumbent wins 77,898–49,141. The candidate loses 108,955–115,493. Own cash rises 31,057, but the rival gains 66,352. The first shop already changes at observation 72: PET_CAFE becomes ICE_CREAM_SHOP, followed by another PET_CAFE versus SMOOTHIE_SHOP. Our candidate produces 210 milk versus 99, with average milk price 223.48 versus 131.80, but the rival benefits more. Wheat opening does not yield a sustained wheat advantage here: eventual own wheat is 54 versus 152, and wheat purchases cost 10,020 versus 8,657.
- **Largest improvement, seed 17, seat 1 versus wheat-heavy supply:** both policies win. Cash moves from 75,019–31,824 to 116,957–62,078; the margin improves by 11,684 without changing the outcome. Towns also diverge at observation 72. Feed expenditure is higher, 6,712 versus 4,830, despite the opening harvest; the later herd/production mix and prices have changed. This is not evidence of a pure wheat-feed saving at fixed demand.

The simulator couples later shop randomness to farm occupancy, so paired seeds do not preserve identical demand after different opening plantings. These comparisons evaluate actual reactive policies under the pinned engine; they do not identify a causal crop return holding the market constant. The wheat-heavy rival remains a useful supply test, but both agents beating it six times means it is not an adequate performance target alone.

## Next priority

**Add a bounded, demand-responsive carrot production option after the unchanged opening.** The current investment crop set contains only wheat, melon and strawberry, while the engine's PET_CAFE buys carrots exclusively. The audited reference branch receives two such shops; the supplied Ace Team game also demonstrates carrot production. This is an identifiable missing production choice, whereas more opening-forecast complexity has not improved matches.

Before that experiment, verify carrot watering, fertilizer, yield and harvest deadlines against the pinned engine; price its seeds, labor, land occupancy and actual observed demand alongside current options. Preserve actual hiring and the incumbent opening. Include a related carrot-supply stress case and retain a fresh holdout after development. Tomatoes have a different ongoing harvest schedule and should be a separate hypothesis. Do not blend this rejected wheat opening into the next candidate or treat one favorable town as proof of general carrot superiority.

## Reproduction

Run from the repository root with the locked environment. Output directories must be new. The report below expects the documented artifact names; raw replays remain local and ignored by Git.

```bash
uv run python -m scripts.make_opening_control --output artifacts/cycle-10-opening-dev/main.py
uv run python -m scripts.make_opening_control --wheat-opponent --output artifacts/cycle-10-wheat-pressure/main.py
uv run python - <<'PY'
import json
from pathlib import Path
recorded = json.loads(Path("docs/benchmarks/cycle-10-opening.json").read_text())
with Path("artifacts/cycle-10-opening-freeze.json").open("x") as file:
    json.dump(recorded["freeze"], file, indent=2)
PY
uv run python evaluate.py --agent artifacts/cycle-10-opening-dev/main.py --opponents baselines/cycle_3.py baselines/step_8.py opponents/scaled_mixed.py artifacts/cycle-10-wheat-pressure/main.py --seeds 17 43 9310 --workers 2 --replays all --output artifacts/cycle-10-opening-development
uv run python evaluate.py --agent baselines/cycle_3.py --opponents baselines/cycle_3.py baselines/step_8.py opponents/scaled_mixed.py artifacts/cycle-10-wheat-pressure/main.py --seeds 17 43 9310 --workers 2 --replays all --output artifacts/cycle-10-reference-development
uv run python -m scripts.audit_replay artifacts/cycle-10-opening-development/replay-0014.json artifacts/cycle-10-opening-development/replay-0020.json --output artifacts/cycle-10-candidate-audit
uv run python -m scripts.audit_replay artifacts/cycle-10-reference-development/replay-0014.json artifacts/cycle-10-reference-development/replay-0020.json --output artifacts/cycle-10-reference-audit
uv run python -m scripts.report_opening --output artifacts/cycle-10-reproduced-report.json
```

The Python block restores the recorded freeze metadata from the committed evidence; it does not select a new candidate. `scripts.report_opening` verifies those plan/source hashes before joining the results. This report is provenance documentation, not a submission. No server rating/latest-two query or Kaggle upload was performed in this cycle.
